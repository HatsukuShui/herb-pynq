"""Compare model families with nested file splits, then export and verify both kernels."""
import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from features import LABELS
from quantization import export, inference, prepare
from train import fit_model, metrics, save_json

ROOT = Path(__file__).resolve().parent


def header_array(name, value, kind):
    values = np.asarray(value).ravel()
    formatted = [format(float(v), ".17g") if kind == "double" else
                 str(int(v)) + ("LL" if kind == "int64_t" else "") for v in values]
    lines = [", ".join(formatted[i:i+8]) for i in range(0, len(formatted), 8)]
    return f"static const {kind} {name}[{len(values)}] = {{\n" + ",\n".join(lines) + "\n};\n"


def plain_logits(model, x, family):
    classifier = model.steps[-1][1]
    z = model.steps[0][1].transform(x)
    if family == "logistic":
        return z @ classifier.coef_.T + classifier.intercept_
    return np.maximum(z @ classifier.coefs_[0] + classifier.intercepts_[0], 0) @ classifier.coefs_[1] + classifier.intercepts_[1]


def complete(compiler):
    dataset = np.load(ROOT / "dataset.npz", allow_pickle=False)
    events = pd.read_csv(ROOT / "events.csv")
    details = json.loads((ROOT / "nested_selection.json").read_text(encoding="utf-8"))
    ranking = pd.read_csv(ROOT / "candidate_comparison.csv")
    y, groups = dataset["y"], dataset["groups"]
    families = ("logistic", "svm", "mlp32")
    summaries, all_predictions, fold_choices, warning_log, final_models = [], [], [], [], {}
    models_dir = ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    print("Evaluating three families; feature view selection stays inside each outer fold", flush=True)
    for family in families:
        predicted = np.full(len(y), -1)
        quantized = np.full(len(y), -1)
        saturations = 0
        for fold in details:
            chosen = next(r for r in fold["ranking"] if r["family"] == family)
            candidate = {k: chosen[k] for k in ("id", "view", "family")}
            tr = np.isin(groups, fold["train_files"])
            te = np.isin(groups, fold["test_files"])
            assert not set(groups[tr]) & set(groups[te])
            x = dataset[candidate["view"]]
            model = fit_model(candidate, x[tr], y[tr], f"family/{family}/outer{fold['fold']}", warning_log)
            predicted[te] = model.predict(x[te])
            # Fixed binary formats use no statistics from the held-out files.
            if family != "svm":
                arrays, _ = export(model, family)
                q_input = prepare(model.steps[0][1].transform(x[te]))
                logits, clipped = inference(q_input, arrays, family)
                quantized[te] = logits.argmax(axis=1)
                saturations += clipped
            fold_choices.append({"family": family, "fold": fold["fold"], "chosen": candidate,
                                 "train_files": fold["train_files"], "test_files": fold["test_files"],
                                 "float_metrics": metrics(y[te], predicted[te])})
            for i in np.flatnonzero(te):
                all_predictions.append({"event_id": events.event_id.iloc[i], "file_id": int(groups[i]),
                                        "family": family, "fold": fold["fold"], "truth": int(y[i]),
                                        "float_prediction": int(predicted[i]),
                                        "q16_prediction": int(quantized[i]) if family != "svm" else None})
        row = {"family": family, "nested_float": metrics(y, predicted)}
        if family != "svm":
            row.update(nested_q16=metrics(y, quantized),
                       float_q16_agreement=int(np.sum(predicted == quantized)),
                       hidden_saturated_elements=saturations)
            winner = ranking[ranking.family == family].iloc[0]
            candidate = {k: winner[k] for k in ("id", "view", "family")}
            if candidate["view"] != "shape50":
                raise ValueError("C feature contract requires shape50; revise exporter for another view")
            pipeline = fit_model(candidate, dataset["shape50"], y, f"family/{family}/final", warning_log)
            bundle = {"format": "small-herb-v1", "labels": LABELS, "candidate": candidate,
                      "pipeline": pipeline, "train_file_ids": list(range(1, 21)), "seed": 20261013}
            joblib.dump(bundle, models_dir / f"{family}.joblib", compress=3)
            reloaded = joblib.load(models_dir / f"{family}.joblib")
            np.testing.assert_array_equal(reloaded["pipeline"].predict(dataset["shape50"]), pipeline.predict(dataset["shape50"]))
            final_models[family] = pipeline
            row["final_candidate"] = candidate
        summaries.append(row)
        print(f"{family}: {row['nested_float']['correct']}/160; Q16 agreement {row.get('float_q16_agreement', 'n/a')}", flush=True)
    # The new exported primary model must equal the already delivered primary prediction.
    primary = joblib.load(ROOT / "herb_model.joblib")
    np.testing.assert_array_equal(primary["pipeline"].predict(dataset["shape50"]),
                                  final_models["logistic"].predict(dataset["shape50"]))
    report = {"selection": "feature view selected by family within each stored inner CV ranking",
              "families": summaries, "warnings": warning_log,
              "input_frac": 10, "weight_frac": 12, "hidden_frac": 10, "output_frac": 12,
              "input_out_of_range": "reject, never wrap", "hidden_activation": "ReLU then saturation at 32767",
              "data_independence": "unknown; file-group nested estimates, no new independent test"}
    save_json(ROOT / "family_comparison.json", report)
    save_json(ROOT / "family_fold_choices.json", fold_choices)
    pd.DataFrame(all_predictions).to_csv(ROOT / "family_validation_predictions.csv", index=False, encoding="utf-8-sig")

    deploy = ROOT / "deploy"
    scaler = final_models["logistic"].steps[0][1]
    np.testing.assert_array_equal(scaler.mean_, final_models["mlp32"].steps[0][1].mean_)
    np.testing.assert_array_equal(scaler.scale_, final_models["mlp32"].steps[0][1].scale_)
    header = ["#pragma once\n#include <stdint.h>\n", header_array("FEATURE_MEAN", scaler.mean_, "double"),
              header_array("FEATURE_SCALE", scaler.scale_, "double")]
    params = {"feature_mean": scaler.mean_, "feature_scale": scaler.scale_, "labels": LABELS}
    quant_params, bounds, model_sizes = {}, {}, {}
    for family, prefix in (("logistic", "LR"), ("mlp32", "MLP")):
        classifier = final_models[family].steps[-1][1]
        floats = ({"w": classifier.coef_.T, "b": classifier.intercept_} if family == "logistic" else
                  {"w1": classifier.coefs_[0], "b1": classifier.intercepts_[0],
                   "w2": classifier.coefs_[1], "b2": classifier.intercepts_[1]})
        arrays, bound = export(final_models[family], family)
        bounds[family] = bound
        quant_params[family] = arrays
        model_sizes[family] = {"parameter_count": sum(a.size for a in floats.values()),
                               "float32_weight_bias_bytes": sum(a.size * 4 for a in floats.values()),
                               "q16_weights_int64_bias_bytes": sum(a.size * (2 if k.startswith('w') else 8) for k, a in arrays.items()),
                               "float64_scaler_bytes": 800}
        for name, value in floats.items():
            params[f"{prefix}_{name}"] = value
            header.append(header_array(f"{prefix}_{name.upper()}", value, "double"))
        for name, value in arrays.items():
            params[f"Q_{prefix}_{name}"] = value.astype(np.int16 if name.startswith("w") else np.int64)
            header.append(header_array(f"Q_{prefix}_{name.upper()}", value, "int16_t" if name.startswith("w") else "int64_t"))
    (deploy / "small_parameters.h").write_text("".join(header), encoding="ascii")
    np.savez_compressed(models_dir / "parameters.npz", **params)
    q_real = prepare(scaler.transform(dataset["shape50"]))
    boundary = np.stack([np.zeros(50, dtype=np.int64), np.full(50, 32767, dtype=np.int64),
                         np.full(50, -32768, dtype=np.int64), np.tile([-32768, 32767], 25)])
    q_test = np.vstack([q_real, boundary])
    reference_q = {family: inference(q_test, a, family)[0] for family, a in quant_params.items()}
    test_header = ["#pragma once\n#include <stdint.h>\n", f"static const int TEST_COUNT={len(q_test)};\n",
                   header_array("TEST_INPUT", q_test, "int32_t"),
                   header_array("TEST_LR", reference_q["logistic"], "int32_t"),
                   header_array("TEST_MLP", reference_q["mlp32"], "int32_t")]
    (deploy / "test_vectors.h").write_text("".join(test_header), encoding="ascii")
    print("Exported parameters. Compiling C++ and checking raw-input and fixed-point outputs", flush=True)
    native = ROOT / "build" / "native"
    native.mkdir(parents=True, exist_ok=True)
    dll = native / "small_native.dll"
    command = [str(compiler), "-std=c++11", "-O2", "-Wno-unknown-pragmas", "-shared", "-DSMALL_NATIVE_DLL",
               str(deploy / "small_ps.cpp"), str(deploy / "small_hls.cpp"), "-o", str(dll)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    dll_directory = os.add_dll_directory(str(compiler.parent)) if os.name == "nt" else None
    lib = ctypes.CDLL(str(dll))
    double_ptr = ctypes.POINTER(ctypes.c_double)
    int_ptr = ctypes.POINTER(ctypes.c_int32)
    lib.small_extract.argtypes = [double_ptr, double_ptr, double_ptr]
    lib.small_prepare.argtypes = [double_ptr, int_ptr]
    lib.small_float.argtypes = [double_ptr, ctypes.c_int, double_ptr]
    lib.small_lr_q.argtypes = [int_ptr, int_ptr]
    lib.small_mlp_q.argtypes = [int_ptr, int_ptr]
    for name in ("small_extract", "small_prepare", "small_float", "small_lr_q", "small_mlp_q"):
        getattr(lib, name).restype = ctypes.c_int
    max_feature_error, max_float_error = 0.0, {f: 0.0 for f in final_models}
    for i in range(len(y)):
        base = np.ascontiguousarray(dataset["baseline"][i], dtype=np.float64)
        response = np.ascontiguousarray(dataset["response"][i], dtype=np.float64)
        feature = np.zeros(50, dtype=np.float64)
        assert lib.small_extract(base.ctypes.data_as(double_ptr), response.ctypes.data_as(double_ptr), feature.ctypes.data_as(double_ptr)) == 0
        max_feature_error = max(max_feature_error, float(np.max(np.abs(feature - dataset["shape50"][i]))))
        np.testing.assert_allclose(feature, dataset["shape50"][i], atol=1e-12, rtol=1e-12)
        qi = np.zeros(50, dtype=np.int32)
        assert lib.small_prepare(feature.ctypes.data_as(double_ptr), qi.ctypes.data_as(int_ptr)) == 0
        np.testing.assert_array_equal(qi, q_real[i])
        for model_id, family in enumerate(("logistic", "mlp32")):
            logits = np.zeros(8, dtype=np.float64)
            got = lib.small_float(feature.ctypes.data_as(double_ptr), model_id, logits.ctypes.data_as(double_ptr))
            expected = plain_logits(final_models[family], dataset["shape50"][[i]], family)[0]
            assert got == int(expected.argmax())
            error = float(np.max(np.abs(logits-expected)))
            max_float_error[family] = max(max_float_error[family], error)
            np.testing.assert_allclose(logits, expected, atol=1e-10, rtol=1e-10)
    integer_errors = 0
    for i, row in enumerate(q_test):
        qi = np.ascontiguousarray(row, dtype=np.int32)
        for function, family in ((lib.small_lr_q, "logistic"), (lib.small_mlp_q, "mlp32")):
            logits = np.zeros(8, dtype=np.int32)
            predicted = function(qi.ctypes.data_as(int_ptr), logits.ctypes.data_as(int_ptr))
            integer_errors += int(np.sum(logits != reference_q[family][i]))
            assert predicted == reference_q[family][i].argmax()
    assert integer_errors == 0
    for bad in (32768, -32769):
        qi = np.zeros(50, dtype=np.int32)
        qi[0] = bad
        logits = np.zeros(8, dtype=np.int32)
        assert lib.small_lr_q(qi.ctypes.data_as(int_ptr), logits.ctypes.data_as(int_ptr)) == -3
        assert lib.small_mlp_q(qi.ctypes.data_as(int_ptr), logits.ctypes.data_as(int_ptr)) == -3
    bad_feature = np.full(50, np.nan)
    qi = np.zeros(50, dtype=np.int32)
    assert lib.small_prepare(bad_feature.ctypes.data_as(double_ptr), qi.ctypes.data_as(int_ptr)) < 0
    assert lib.small_extract(bad_feature.ctypes.data_as(double_ptr), dataset["response"][0].ctypes.data_as(double_ptr),
                            np.zeros(50).ctypes.data_as(double_ptr)) < 0
    tb = native / "tb_small.exe"
    subprocess.run([str(compiler), "-std=c++11", "-O2", "-Wno-unknown-pragmas", str(deploy / "small_hls.cpp"),
                    str(deploy / "tb_small.cpp"), "-o", str(tb)], check=True, capture_output=True, text=True)
    tested = subprocess.run([str(tb)], check=True, capture_output=True, text=True)
    hls_top_native_checks = {}
    for mode in ("LR", "MLP"):
        executable = native / f"tb_{mode.lower()}.exe"
        subprocess.run([str(compiler), "-std=c++11", "-O2", "-Wno-unknown-pragmas", f"-DSMALL_HLS_{mode}",
                        str(deploy / "small_hls.cpp"), str(deploy / "tb_small.cpp"), "-o", str(executable)],
                       check=True, capture_output=True, text=True)
        hls_top_native_checks[mode] = subprocess.run([str(executable)], check=True, capture_output=True, text=True).stdout.strip()
    final_checks = {}
    for family, model in final_models.items():
        fp = model.predict(dataset["shape50"])
        qp = reference_q[family][:len(y)].argmax(axis=1)
        final_checks[family] = {"float_q16_agreement": int((fp == qp).sum()), "events": len(y),
                                "training_accuracy_float": float(np.mean(fp == y)),
                                "training_accuracy_q16": float(np.mean(qp == y)),
                                "hidden_saturated_elements": inference(q_real, quant_params[family], family)[1]}
    verification = {"status": "passed", "raw_feature_checks": 160, "float_model_checks": 320,
                    "max_feature_abs_error": max_feature_error, "max_float_logit_abs_error": max_float_error,
                    "integer_vectors_per_model": len(q_test), "integer_logit_values_checked": len(q_test)*8*2,
                    "integer_logit_mismatches": integer_errors, "native_testbench": tested.stdout.strip(),
                    "individual_top_native_testbenches": hls_top_native_checks,
                    "final_model_conversion": final_checks, "model_sizes": model_sizes,
                    "int64_accumulator_bounds": bounds,
                    "source_primary_sha256": hashlib.sha256((ROOT / "herb_model.joblib").read_bytes()).hexdigest(),
                    "hls_synthesis": "not_run", "rtl_cosimulation": "not_run", "fpga_board_test": "not_run",
                    "native_compiler": str(compiler), "native_compile_command": command}
    save_json(ROOT / "deployment_verification.json", verification)
    if dll_directory:
        dll_directory.close()
    print(json.dumps(verification, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, default=Path("D:/msys64/ucrt64/bin/g++.exe"))
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        complete(args.compiler)
