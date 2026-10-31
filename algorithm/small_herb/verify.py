"""Check saved predictions, fold membership, preprocessing and raw-data inference."""
import argparse
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".mplconfig"))

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from threadpoolctl import threadpool_limits

from features import LABELS, VIEWS, extract_views, from_record
from predict import predict_event
from train import read_archive

ROOT = Path(__file__).resolve().parent


def verify(archive):
    results = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
    details = json.loads((ROOT / "nested_selection.json").read_text(encoding="utf-8"))
    plan = json.loads((ROOT / "training_plan.json").read_text(encoding="utf-8"))
    saved = np.load(ROOT / "dataset.npz", allow_pickle=False)
    events, inventory, matrices, baseline, response, annotation_hash = read_archive(archive)
    pd.testing.assert_frame_equal(events, pd.read_csv(ROOT / "events.csv"))
    pd.testing.assert_frame_equal(inventory, pd.read_csv(ROOT / "file_inventory.csv"))
    assert annotation_hash == plan["annotation_sha256"]
    assert int(inventory.rows.sum()) == 15687
    assert len(set(inventory.numeric_sha256)) == 20
    for view in VIEWS:
        np.testing.assert_array_equal(matrices[view], saved[view])
    np.testing.assert_array_equal(baseline, saved["baseline"])
    np.testing.assert_array_equal(response, saved["response"])
    y, groups = events.class_id.to_numpy(), events.file_id.to_numpy()
    np.testing.assert_array_equal(y, saved["y"])
    np.testing.assert_array_equal(groups, saved["groups"])
    predictions = pd.read_csv(ROOT / "validation_predictions.csv")
    assert len(predictions) == predictions.event_id.nunique() == 160
    predictions = predictions.set_index("event_id").loc[events.event_id].reset_index()
    np.testing.assert_array_equal(predictions.class_id, y)
    np.testing.assert_array_equal(predictions.file_id, groups)
    assert predictions.groupby("file_id").fold.nunique().eq(1).all()
    nested = results["nested_grouped_validation"]
    assert accuracy_score(y, predictions.prediction) == nested["accuracy"]
    assert f1_score(y, predictions.prediction, average="macro") == nested["macro_f1"]
    np.testing.assert_array_equal(confusion_matrix(y, predictions.prediction, labels=range(8)),
                                  nested["confusion_matrix"])
    checked_events = 0
    for fold in details:
        model_path = ROOT / "fold_models" / f"fold{fold['fold']}.joblib"
        bundle = joblib.load(model_path)
        train_files, test_files = set(fold["train_files"]), set(fold["test_files"])
        assert not train_files & test_files
        assert train_files | test_files == set(groups)
        assert bundle["train_file_ids"] == fold["train_files"]
        assert bundle["candidate"] == fold["chosen"]
        inner_test_files = []
        for inner in fold["inner_splits"]:
            a, b = set(inner["train_files"]), set(inner["test_files"])
            assert not a & b
            assert a | b == train_files
            assert not (a | b) & test_files
            inner_test_files.extend(b)
        assert sorted(inner_test_files) == sorted(train_files)
        tr = np.isin(groups, list(train_files))
        te = np.isin(groups, list(test_files))
        view = bundle["candidate"]["view"]
        scaler = bundle["pipeline"].steps[0][1]
        assert scaler.n_samples_seen_ == int(tr.sum())
        np.testing.assert_allclose(scaler.mean_, matrices[view][tr].mean(axis=0), rtol=0, atol=1e-12)
        np.testing.assert_allclose(scaler.var_, matrices[view][tr].var(axis=0), rtol=0, atol=1e-12)
        np.testing.assert_array_equal(bundle["pipeline"].predict(matrices[view][te]), predictions.prediction[te])
        for index in np.flatnonzero(te):
            event = np.vstack([baseline[index], response[index]])
            got = predict_event(bundle, event, 11)
            assert got["class_id"] == predictions.prediction.iloc[index]
            # Earlier/later unrelated points must not enter a known-onset decision.
            padded = np.vstack([np.full((7, 5), 12345.0), event, np.full((6, 5), 99999.0)])
            assert predict_event(bundle, padded, 18)["class_id"] == got["class_id"]
            for key in VIEWS:
                np.testing.assert_array_equal(from_record(padded, 18)[key], matrices[key][index])
            checked_events += 1
    assert checked_events == 160
    final = joblib.load(ROOT / "herb_model.joblib")
    assert final["candidate"] == results["final_candidate"]
    assert final["train_file_ids"] == list(range(1, 21))
    view = final["candidate"]["view"]
    np.testing.assert_allclose(final["pipeline"].steps[0][1].mean_, matrices[view].mean(axis=0), rtol=0, atol=1e-12)
    assert final["pipeline"].steps[0][1].n_samples_seen_ == 160

    reference = np.full((10, 5), 100.0)
    ramp = 100.0 + np.arange(20)[:, None] * np.arange(1, 6)[None, :]
    analytical = extract_views(reference, ramp)
    np.testing.assert_allclose(analytical["mean5"], 9.5 * np.arange(1, 6) / 100.0)
    np.testing.assert_allclose(analytical["shape50"][30:35], np.arange(1, 6) / 100.0)
    np.testing.assert_allclose(analytical["shape50"][:5], 2 * np.arange(1, 6) / 100.0)
    invalid = [np.ones((29, 5)), np.ones((30, 6)), np.full((30, 5), np.nan),
               np.full((30, 5), np.inf), np.zeros((30, 5))]
    for record in invalid:
        try:
            from_record(record, 11)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid input was accepted")
    cli = subprocess.run([sys.executable, str(ROOT / "predict.py"), "--txt", str(ROOT / "example_event.txt"),
                          "--start-row", "11"], capture_output=True, text=True, encoding="utf-8", check=True)
    cli_prediction = json.loads(cli.stdout)
    assert cli_prediction == predict_event(final, np.loadtxt(ROOT / "example_event.txt"), 11)
    verification = {"status": "passed", "raw_rows": int(inventory.rows.sum()), "unique_files": 20,
                    "event_features_rebuilt": 160, "out_of_fold_predictions_replayed": checked_events,
                    "all_outer_and_inner_file_groups_disjoint": True,
                    "fold_scalers_match_training_only": True, "metrics_recomputed": True,
                    "single_event_crop_and_padding_invariant": True,
                    "analytical_feature_checks": "passed", "invalid_input_cases_rejected": len(invalid),
                    "cli_prediction": cli_prediction,
                    "warning_count": results["warning_count"]}
    (ROOT / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    versions = [f"{name}=={importlib.metadata.version(name)}" for name in
                ("numpy", "scipy", "pandas", "scikit-learn", "joblib", "matplotlib", "threadpoolctl")]
    (ROOT / "requirements.txt").write_text("\n".join(versions) + "\n", encoding="ascii")

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    cm = np.asarray(nested["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(8, 6.5), layout="constrained")
    image = ax.imshow(cm, cmap="Blues", vmin=0, vmax=20)
    ax.set_xticks(range(8), LABELS, rotation=35, ha="right")
    ax.set_yticks(range(8), LABELS)
    ax.set_xlabel("预测药材")
    ax.set_ylabel("真实药材")
    ax.set_title(f"小数据集：按文件嵌套验证\n{nested['correct']}/160 正确，准确率 {nested['accuracy']:.2%}", pad=12)
    for i in range(8):
        for j in range(8):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="white" if cm[i, j] > 10 else "black")
    fig.colorbar(image, ax=ax, shrink=.8, label="事件数")
    fig.savefig(ROOT / "confusion_matrix.png", dpi=180)
    plt.close(fig)
    ranking = pd.read_csv(ROOT / "candidate_comparison.csv")
    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    colors = ranking.family.map({"logistic": "#2c7f85", "svm": "#4779b1", "mlp32": "#ab5265"})
    ax.barh(ranking.id, ranking.accuracy * 100, color=colors)
    ax.invert_yaxis()
    ax.set_xlim(0, 108)
    ax.set_xlabel("按文件分组交叉验证准确率 (%)")
    ax.set_title("12 个候选模型比较\n此图用于最终选型；主要效果以嵌套验证为准")
    for index, row in ranking.iterrows():
        ax.text(row.accuracy * 100 + .6, index, f"{row.accuracy:.2%}", va="center", fontsize=9)
    fig.savefig(ROOT / "candidate_comparison.png", dpi=180)
    plt.close(fig)
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path,
                        default=ROOT.parent / "20260928-原始数据（小数据集）-余正心-v1.zip")
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        verify(args.archive)
