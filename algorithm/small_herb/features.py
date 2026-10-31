"""Single-herb features from ten reference points and twenty response points."""
import numpy as np

LABELS = ["干姜", "肉桂", "川芎", "熟地黄", "柴胡", "当归", "甘草", "苍术"]
VIEWS = ("raw100", "relative100", "mean5", "shape50")
BASELINE_POINTS = 10
RESPONSE_POINTS = 20


def extract_views(baseline, response):
    baseline = np.asarray(baseline, dtype=np.float64)
    response = np.asarray(response, dtype=np.float64)
    if baseline.shape != (10, 5) or response.shape != (20, 5):
        raise ValueError("Expected baseline (10, 5) and response (20, 5)")
    if not np.isfinite(baseline).all() or not np.isfinite(response).all():
        raise ValueError("Input contains NaN or infinity")
    reference = np.median(baseline, axis=0)
    if np.any(reference <= 0):
        raise ValueError("Reference medians must be positive")
    relative = (response - reference) / reference
    peak = relative.max(axis=0)
    time = np.arange(20, dtype=float) - 9.5
    slope = (time[:, None] * relative).sum(axis=0) / (time @ time)
    shape = np.concatenate([
        relative.reshape(4, 5, 5).mean(axis=1).ravel(),
        peak, relative.mean(axis=0), slope, relative.std(axis=0),
        np.abs(np.diff(relative, axis=0)).mean(axis=0),
        peak / (np.abs(peak).sum() + 1e-6),
    ])
    return {"raw100": response.ravel(), "relative100": relative.ravel(),
            "mean5": relative.mean(axis=0), "shape50": shape}


def from_record(record, start_row):
    record = np.asarray(record, dtype=np.float64)
    if record.ndim != 2 or record.shape[1] != 5:
        raise ValueError("TXT must contain exactly five sensor columns without a header")
    if isinstance(start_row, bool) or int(start_row) != start_row:
        raise ValueError("start_row must be an integer, one-based")
    start = int(start_row) - 1
    if start < BASELINE_POINTS or start + RESPONSE_POINTS > len(record):
        raise ValueError("Need ten points before start_row and twenty points from start_row")
    return extract_views(record[start - 10:start], record[start:start + 20])
