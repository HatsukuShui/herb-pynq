"""Q16 weights/inputs, Q10 ReLU activations, int64 accumulation."""
import numpy as np

INPUT_FRAC = 10
WEIGHT_FRAC = 12
HIDDEN_FRAC = 10
OUTPUT_FRAC = 12


def rounded(value, frac):
    scaled = np.asarray(value, dtype=float) * (2.0 ** frac)
    if not np.isfinite(scaled).all() or np.max(np.abs(scaled)) >= 2.0 ** 62:
        raise ValueError("Nonfinite or excessive quantization input")
    return (np.sign(scaled) * np.floor(np.abs(scaled) + .5)).astype(np.int64)


def shift(value, bits):
    value = np.asarray(value, dtype=np.int64)
    return np.sign(value) * ((np.abs(value) + (1 << (bits - 1))) >> bits)


def prepare(standardized):
    value = rounded(standardized, INPUT_FRAC)
    if value.min() < -32768 or value.max() > 32767:
        raise ValueError("Standardized input is outside Q10 int16 range")
    return value


def export(pipeline, family):
    classifier = pipeline.steps[-1][1]
    if family == "logistic":
        arrays = {"w": rounded(classifier.coef_.T, WEIGHT_FRAC),
                  "b": rounded(classifier.intercept_, INPUT_FRAC + WEIGHT_FRAC)}
    elif family == "mlp32":
        arrays = {"w1": rounded(classifier.coefs_[0], WEIGHT_FRAC),
                  "w2": rounded(classifier.coefs_[1], WEIGHT_FRAC),
                  "b1": rounded(classifier.intercepts_[0], INPUT_FRAC + WEIGHT_FRAC),
                  "b2": rounded(classifier.intercepts_[1], HIDDEN_FRAC + WEIGHT_FRAC)}
    else:
        raise ValueError("Only linear and ReLU MLP exports are supported")
    bounds = {}
    for name, array in arrays.items():
        if name.startswith("w") and (array.min() < -32768 or array.max() > 32767):
            raise ValueError("Weight outside Q12 int16 range")
    for w, b in (("w", "b"),) if family == "logistic" else (("w1", "b1"), ("w2", "b2")):
        bound = max(sum(abs(int(v)) for v in arrays[w][:, j]) * 32768 + abs(int(arrays[b][j]))
                    for j in range(arrays[w].shape[1]))
        assert bound < 2 ** 63 - 2 ** 22
        bounds[w] = bound
    last = bounds["w" if family == "logistic" else "w2"]
    assert (last + 512) // 1024 < 2 ** 31 - 1
    return arrays, bounds


def inference(inputs, arrays, family):
    inputs = np.asarray(inputs, dtype=np.int64)
    if inputs.min() < -32768 or inputs.max() > 32767:
        raise ValueError("Invalid integer input")
    saturations = 0
    if family == "logistic":
        result = shift(inputs @ arrays["w"] + arrays["b"], 10)
    else:
        hidden = shift(inputs @ arrays["w1"] + arrays["b1"], 12)
        saturations = int((hidden > 32767).sum())
        hidden = np.clip(hidden, 0, 32767)
        result = shift(hidden @ arrays["w2"] + arrays["b2"], 10)
    return result, saturations
