"""Rebuild and train only the original small dataset; group all splits by file."""
import argparse
import hashlib
import io
import json
import platform
import re
import time
import warnings
import zipfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits

from features import LABELS, VIEWS, extract_views

ROOT = Path(__file__).resolve().parent
SEED = 20261013
CANDIDATES = [{"id": f"{view}_{family}", "view": view, "family": family}
              for view in VIEWS for family in ("logistic", "svm", "mlp32")]


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def decode(blob):
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return blob.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Cannot decode text file")


def read_archive(archive):
    events, inventory, references, responses, matrices = [], [], [], [], {v: [] for v in VIEWS}
    with zipfile.ZipFile(archive) as source:
        text_files = [n for n in source.namelist() if n.lower().endswith(".txt")]
        annotations = [n for n in text_files if not Path(n).stem.isdigit()]
        if len(annotations) != 1:
            raise ValueError("Expected exactly one start/end annotation file")
        annotation_blob = source.read(annotations[0])
        ranges, current = {}, None
        for line in decode(annotation_blob).splitlines():
            line = line.strip()
            if not line:
                continue
            if re.fullmatch(r"\d+", line):
                current = int(line)
                if current in ranges:
                    raise ValueError("Duplicate annotation file ID")
                ranges[current] = []
            elif current is not None and re.fullmatch(r"\d+\s*-\s*\d+", line):
                ranges[current].append(tuple(map(int, line.split("-"))))
            else:
                raise ValueError(f"Invalid annotation line: {line!r}")
        numeric_files = [n for n in text_files if Path(n).stem.isdigit()]
        file_map = {int(Path(n).stem): n for n in numeric_files}
        if len(file_map) != len(numeric_files) or set(file_map) != set(ranges):
            raise ValueError("Data files and annotation IDs do not match")
        if set(file_map) != set(range(1, 21)):
            raise ValueError("Expected the twenty original small-dataset files")
        seen = set()
        for file_id, name in sorted(file_map.items()):
            blob = source.read(name)
            record = np.loadtxt(io.StringIO(decode(blob)))
            if record.ndim != 2 or record.shape[1] != 5 or not np.isfinite(record).all():
                raise ValueError(f"Invalid five-channel input: {name}")
            numeric_hash = hashlib.sha256(np.asarray(record, dtype="<f8").tobytes()).hexdigest()
            if numeric_hash in seen:
                raise ValueError("Duplicate numeric recordings require common grouping")
            seen.add(numeric_hash)
            inventory.append({"file_id": file_id, "source": name, "rows": len(record),
                              "sha256": hashlib.sha256(blob).hexdigest(),
                              "numeric_sha256": numeric_hash,
                              "adjacent_duplicate_rows": int(np.all(np.diff(record, axis=0) == 0, axis=1).sum())})
            if len(ranges[file_id]) != len(LABELS):
                raise ValueError("Expected eight annotated single-herb events per file")
            previous_end = 0
            for label_id, (start, end) in enumerate(ranges[file_id]):
                if not (start > previous_end and start >= 11 and start + 19 <= end <= len(record)):
                    raise ValueError("Invalid, overlapping or too-short annotated interval")
                previous_end = end
                baseline = record[start - 11:start - 1]
                response = record[start - 1:start + 19]
                views = extract_views(baseline, response)
                for key, value in views.items():
                    matrices[key].append(value)
                references.append(baseline)
                responses.append(response)
                events.append({"event_id": f"S{file_id:02d}_E{label_id + 1:02d}",
                               "file_id": file_id, "class_id": label_id, "herb": LABELS[label_id],
                               "start_row": start, "end_row": end,
                               "baseline_start_row": start - 10, "feature_end_row": start + 19})
    return (pd.DataFrame(events), pd.DataFrame(inventory),
            {k: np.asarray(v) for k, v in matrices.items()},
            np.asarray(references), np.asarray(responses),
            hashlib.sha256(annotation_blob).hexdigest())


def make_model(candidate):
    family = candidate["family"]
    if family == "logistic":
        classifier = LogisticRegression(C=1.0, max_iter=3000, random_state=SEED)
    elif family == "svm":
        classifier = SVC(C=3.0, gamma="scale", kernel="rbf")
    elif family == "mlp32":
        classifier = MLPClassifier(hidden_layer_sizes=(32,), activation="relu", solver="lbfgs",
                                   alpha=1.0, max_iter=2000, max_fun=30000,
                                   tol=1e-6, random_state=SEED)
    else:
        raise ValueError(f"Unknown classifier: {family}")
    return make_pipeline(StandardScaler(), classifier)


def fit_model(candidate, x, y, context, warning_log):
    model = make_model(candidate)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.fit(x, y)
    warning_log.extend({"context": context, "candidate": candidate["id"],
                        "category": w.category.__name__, "message": str(w.message)} for w in caught)
    return model


def metrics(y, predicted):
    return {"events": len(y), "correct": int(np.sum(y == predicted)),
            "accuracy": float(accuracy_score(y, predicted)),
            "macro_f1": float(f1_score(y, predicted, labels=range(8), average="macro", zero_division=0)),
            "confusion_matrix": confusion_matrix(y, predicted, labels=range(8)).tolist(),
            "classification_report": classification_report(y, predicted, labels=range(8),
                                                            target_names=LABELS, output_dict=True, zero_division=0)}


def grouped_splits(y, groups, folds, seed):
    splits = list(GroupKFold(n_splits=folds, shuffle=True, random_state=seed).split(y, y, groups))
    for train, test in splits:
        assert not set(groups[train]) & set(groups[test])
        assert set(y[train]) == set(range(8))
    return splits


def select_model(matrices, y, groups, splits, context, warning_log):
    rows, all_predictions = [], {}
    for candidate in CANDIDATES:
        x = matrices[candidate["view"]]
        predictions = np.full(len(y), -1)
        fold_scores = []
        for fold, (train, test) in enumerate(splits, 1):
            assert not set(groups[train]) & set(groups[test])
            model = fit_model(candidate, x[train], y[train], f"{context}/fold{fold}", warning_log)
            predictions[test] = model.predict(x[test])
            fold_scores.append(float(accuracy_score(y[test], predictions[test])))
        assert (predictions >= 0).all()
        result = metrics(y, predictions)
        rows.append({**candidate, "dimension": x.shape[1], "accuracy": result["accuracy"],
                     "macro_f1": result["macro_f1"], "correct": result["correct"],
                     "fold_accuracy": fold_scores})
        all_predictions[candidate["id"]] = predictions
    # Fixed tie-break: accuracy, macro F1, lower dimension, then candidate declaration order.
    ranked = sorted(rows, key=lambda r: (-r["accuracy"], -r["macro_f1"], r["dimension"]))
    best = next(c for c in CANDIDATES if c["id"] == ranked[0]["id"])
    return best, ranked, all_predictions


def train(archive, output):
    start_time = time.perf_counter()
    output.mkdir(parents=True, exist_ok=True)
    (output / "fold_models").mkdir(exist_ok=True)
    events, inventory, matrices, baseline, response, annotation_hash = read_archive(archive)
    y = events.class_id.to_numpy()
    groups = events.file_id.to_numpy()
    outer = grouped_splits(y, groups, 5, SEED)
    plan = {"seed": SEED, "candidates": CANDIDATES,
            "classifier_parameters": {f: make_model({"family": f}).steps[-1][1].get_params()
                                      for f in ("logistic", "svm", "mlp32")},
            "selection": "accuracy, macro F1, lower dimension, then declaration order",
            "evaluation": "5 outer file-group folds; 4 inner file-group folds; scaler fitted inside each fit",
            "outer_split": [{"fold": i, "train_files": sorted(set(groups[tr].tolist())),
                             "test_files": sorted(set(groups[te].tolist()))}
                            for i, (tr, te) in enumerate(outer, 1)],
            "baseline_points": 10, "response_points": 20,
            "labels": LABELS, "class_id_base": 0,
            "label_source": "existing confirmed eight-herb order in 20261010 label protocol; single-herb intent confirmed 2026-10-13",
            "annotation_index": "one-based inclusive; physical insertion timestamps unverified",
            "file_independence": "unknown, user confirmed uncertainty on 2026-10-13",
            "sample_interval_s": 1, "sample_interval_source": "existing project documentation; TXT has no timestamps",
            "fixed_order": True, "outside_intervals_used_as_air": False,
            "source_archive": archive.name, "source_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "annotation_sha256": annotation_hash,
            "metadata_used_as_model_features": [], "pretrained_models_loaded": False,
            "limits": ["No independent new-date or randomized-order test",
                       "No air, mixture, unknown-herb or automatic onset classification",
                       "Unknown independence between recordings; local references may contain previous-herb residue"]}
    save_json(output / "training_plan.json", plan)
    events.to_csv(output / "events.csv", index=False, encoding="utf-8-sig")
    inventory.to_csv(output / "file_inventory.csv", index=False, encoding="utf-8-sig")
    np.savez_compressed(output / "dataset.npz", **matrices, baseline=baseline, response=response, y=y, groups=groups)
    warning_log, nested_details, prediction_rows = [], [], []
    outer_predictions = np.full(len(y), -1)
    for fold, (train_idx, test_idx) in enumerate(outer, 1):
        print(f"Outer fold {fold}/5: inner selection on {len(train_idx)} events", flush=True)
        inner = grouped_splits(y[train_idx], groups[train_idx], 4, SEED + fold)
        subset = {k: x[train_idx] for k, x in matrices.items()}
        chosen, ranking, _ = select_model(subset, y[train_idx], groups[train_idx], inner,
                                           f"outer{fold}/inner", warning_log)
        x = matrices[chosen["view"]]
        model = fit_model(chosen, x[train_idx], y[train_idx], f"outer{fold}/refit", warning_log)
        predictions = model.predict(x[test_idx])
        outer_predictions[test_idx] = predictions
        bundle = {"format": "small-herb-v1", "labels": LABELS, "candidate": chosen, "pipeline": model,
                  "train_file_ids": sorted(set(groups[train_idx].tolist())), "seed": SEED}
        joblib.dump(bundle, output / "fold_models" / f"fold{fold}.joblib", compress=3)
        nested_details.append({"fold": fold, "chosen": chosen, "ranking": ranking,
                               "train_files": bundle["train_file_ids"],
                               "test_files": sorted(set(groups[test_idx].tolist())),
                               "inner_splits": [{"train_files": sorted(set(groups[train_idx][a].tolist())),
                                                 "test_files": sorted(set(groups[train_idx][b].tolist()))}
                                                for a, b in inner],
                               "metrics": metrics(y[test_idx], predictions)})
        for index, prediction in zip(test_idx, predictions):
            prediction_rows.append({**events.iloc[index].to_dict(), "fold": fold,
                                    "chosen": chosen["id"], "prediction": int(prediction),
                                    "predicted_herb": LABELS[int(prediction)], "correct": bool(prediction == y[index])})
        print(f"  {chosen['id']}: {int(np.sum(predictions == y[test_idx]))}/{len(test_idx)}", flush=True)
    assert (outer_predictions >= 0).all()
    print("Selecting final configuration using grouped CV on all 160 events", flush=True)
    final, ranking, candidate_predictions = select_model(matrices, y, groups, outer, "final_selection", warning_log)
    final_model = fit_model(final, matrices[final["view"]], y, "final_refit", warning_log)
    bundle = {"format": "small-herb-v1", "labels": LABELS, "candidate": final, "pipeline": final_model,
              "train_file_ids": sorted(set(groups.tolist())), "seed": SEED, "protocol": plan}
    joblib.dump(bundle, output / "herb_model.joblib", compress=3)
    predictions_df = pd.DataFrame(prediction_rows).sort_values(["file_id", "class_id"])
    predictions_df.to_csv(output / "validation_predictions.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(ranking).to_csv(output / "candidate_comparison.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"event_id": events.event_id, "truth": y, **candidate_predictions}).to_csv(
        output / "candidate_predictions.csv", index=False, encoding="utf-8-sig")
    save_json(output / "nested_selection.json", nested_details)
    save_json(output / "training_warnings.json", warning_log)
    result = {"nested_grouped_validation": metrics(y, outer_predictions),
              "final_candidate": final, "final_selection_cv_exploratory": ranking[0],
              "warning_count": len(warning_log), "elapsed_seconds": time.perf_counter() - start_time,
              "final_model_bytes": (output / "herb_model.joblib").stat().st_size,
              "versions": {"python": platform.python_version(), "numpy": np.__version__,
                           "pandas": pd.__version__, "scipy": scipy.__version__,
                           "scikit-learn": sklearn.__version__, "joblib": joblib.__version__}}
    save_json(output / "results.json", result)
    np.savetxt(output / "example_event.txt", np.vstack([baseline[0], response[0]]), fmt="%.12g")
    print(json.dumps({k: v for k, v in result.items() if k != "nested_grouped_validation"}, ensure_ascii=False), flush=True)
    print(f"NESTED: {result['nested_grouped_validation']['correct']}/160; "
          f"accuracy={result['nested_grouped_validation']['accuracy']:.4f}; "
          f"macro_f1={result['nested_grouped_validation']['macro_f1']:.4f}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path,
                        default=ROOT.parent / "20260928-原始数据（小数据集）-余正心-v1.zip")
    parser.add_argument("--output", type=Path, default=ROOT)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        train(args.archive, args.output)


if __name__ == "__main__":
    main()
