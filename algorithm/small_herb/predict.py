"""Predict one annotated event. Start rows are one-based and inclusive."""
import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np

from features import LABELS, from_record


def predict_event(bundle, record, start_row, format_name="float"):
    if bundle.get("format") != "small-herb-v1" or bundle["labels"] != LABELS:
        raise ValueError("Incompatible model or class mapping")
    view = bundle["candidate"]["view"]
    feature = from_record(record, start_row)[view][None, :]
    model = bundle["pipeline"]
    extra = {}
    if format_name == "float":
        class_id = int(model.predict(feature)[0])
    elif format_name == "q16":
        from quantization import export, inference, prepare
        family = bundle["candidate"]["family"]
        arrays, _ = export(model, family)
        logits, saturations = inference(prepare(model.steps[0][1].transform(feature)), arrays, family)
        class_id = int(logits[0].argmax())
        extra["hidden_saturated_elements"] = saturations
    else:
        raise ValueError("format_name must be float or q16")
    return {"class_id": class_id, "herb": LABELS[class_id],
            "start_row_1based": int(start_row),
            "last_used_row_1based": int(start_row) + 19,
            "candidate": bundle["candidate"]["id"],
            "format": format_name, **extra,
            "scope": "one known herb exposure; no air/unknown detection"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--txt", type=Path, required=True)
    parser.add_argument("--start-row", type=int, required=True)
    parser.add_argument("--model", type=Path,
                        default=Path(__file__).resolve().parent / "herb_model.joblib")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("float", "q16"), default="float")
    args = parser.parse_args()
    # Load only the locally trained bundle or another trusted joblib file.
    bundle = joblib.load(args.model)
    result = predict_event(bundle, np.loadtxt(args.txt), args.start_row, args.format)
    content = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(content + "\n", encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
