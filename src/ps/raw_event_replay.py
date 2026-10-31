"""Replay recorded sensor events through ARM preprocessing and the actual FPGA.

The labels are used only for reporting, never for inference. These are existing
delivery records, not a new blind test or live sensor acquisition.
"""
import argparse
import csv
import ctypes as ct
import json
import subprocess
from pathlib import Path

import numpy as np
from replay_models import infer

HERE = Path(__file__).resolve().parent
SMALL_LABELS = ['干姜', '肉桂', '川芎', '熟地黄', '柴胡', '当归', '甘草', '苍术']
FUSION_LABELS = ['当归+甘草', '当归+川芎', '当归+肉桂', '当归+熟地黄', '甘草+川芎',
                 '甘草+肉桂', '甘草+熟地黄', '川芎+肉桂', '川芎+熟地黄', '肉桂+熟地黄']
DP = ct.POINTER(ct.c_double)
IP = ct.POINTER(ct.c_int32)


def build_libraries():
    out = HERE / 'native'
    out.mkdir(exist_ok=True)
    for model, prefix in [('small', 'small'), ('fusion', 'fusion')]:
        src = HERE / 'raw_support' / model
        subprocess.run(['g++', '-std=c++11', '-O2', '-shared', '-fPIC',
                        '-Wno-unknown-pragmas', '-I' + str(src),
                        str(src / (prefix + '_ps.cpp')), str(src / (prefix + '_hls.cpp')),
                        '-o', str(out / ('lib' + model + '.so'))], check=True)
    return out


def libraries():
    out = build_libraries()
    small, fusion = [ct.CDLL(str(out / ('lib' + m + '.so'))) for m in ('small', 'fusion')]
    for lib, name, types in [(small, 'small_extract', [DP, DP, DP]),
                             (small, 'small_prepare', [DP, IP]),
                             (small, 'small_lr_q', [IP, IP]),
                             (fusion, 'fusion_extract', [DP, DP, ct.c_int, ct.c_double, DP]),
                             (fusion, 'fusion_prepare', [DP, IP]),
                             (fusion, 'fusion_q', [IP, IP])]:
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = types, ct.c_int
    return small, fusion


def dp(a):
    return a.ctypes.data_as(DP)


def ip(a):
    return a.ctypes.data_as(IP)


def check_status(status, stage):
    if status != 0:
        raise ValueError(f'{stage} rejected input: {status}')


def extract_small(lib, baseline, response):
    b, r = [np.ascontiguousarray(a, dtype=np.float64) for a in (baseline, response)]
    if b.shape != (10, 5) or r.shape != (20, 5):
        raise ValueError('Small model needs baseline 10x5 and response 20x5')
    features, q = np.zeros(50), np.zeros(50, dtype=np.int32)
    check_status(lib.small_extract(dp(b), dp(r), dp(features)), 'small_extract')
    check_status(lib.small_prepare(dp(features), ip(q)), 'small_prepare')
    return features, q


def extract_fusion(lib, times, samples, onset=0.):
    t, raw = [np.ascontiguousarray(a, dtype=np.float64) for a in (times, samples)]
    if t.ndim != 1 or raw.shape != (len(t), 10):
        raise ValueError('Fusion model needs n times and n x 10 samples')
    features, q = np.zeros(100), np.zeros(100, dtype=np.int32)
    check_status(lib.fusion_extract(dp(t), dp(raw), len(t), onset, dp(features)), 'fusion_extract')
    check_status(lib.fusion_prepare(dp(features), ip(q)), 'fusion_prepare')
    return features, q


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--all', action='store_true', help='All 160 + 410 delivery events')
    mode.add_argument('--examples', action='store_true', help='First small event and official reverse example')
    args = parser.parse_args()
    small, fusion = libraries()
    from pynq import Overlay
    overlay = Overlay(str(HERE / 'herb_models.bit'))
    data = HERE / 'raw_data'
    small_data = np.load(data / 'small_dataset.npz', allow_pickle=False)
    fusion_data = np.load(data / 'fusion_features.npz', allow_pickle=False)
    windows = np.load(data / 'fusion_raw_windows.npz', allow_pickle=False)
    small_meta = list(csv.DictReader((data / 'small_events.csv').open(encoding='utf-8-sig')))
    fusion_meta = list(csv.DictReader((data / 'fusion_events.csv').open(encoding='utf-8-sig')))
    configs = {m: json.loads((HERE / (m + '_replay.json')).read_text()) for m in ('small_lr', 'fusion_q32')}
    rows, maximum_feature_error = [], {'small_lr': 0., 'fusion_q32': 0.}
    for model, meta in [('small_lr', small_meta), ('fusion_q32', fusion_meta)]:
        cfg = configs[model]
        device_ip = getattr(overlay, cfg['instance'])
        for i, event in enumerate(meta):
            if not args.all and not (model == 'small_lr' and i == 0 or model == 'fusion_q32' and event['event_id'] == 'r002_e01'):
                continue
            if model == 'small_lr':
                f, q = extract_small(small, small_data['baseline'][i], small_data['response'][i])
                expected_features = small_data['shape50'][i]
                labels, base, nout, reference = SMALL_LABELS, 0, 8, small.small_lr_q
                subset = 'existing_training_records'
            else:
                w = windows[event['event_id']]
                f, q = extract_fusion(fusion, w[:, 0], w[:, [1, 2, 3, 4, 5, 6, 11, 12, 13, 14]])
                expected_features = fusion_data['stable10_stats'][i]
                labels, base, nout, reference = FUSION_LABELS, 1, 10, fusion.fusion_q
                subset = 'reverse_diagnostic' if event['reverse'].lower() == 'true' else 'existing_training_records'
            error = float(np.max(np.abs(f - expected_features)))
            maximum_feature_error[model] = max(maximum_feature_error[model], error)
            if not np.allclose(f, expected_features, atol=1e-10, rtol=1e-10):
                raise RuntimeError(f'{event["event_id"]}: ARM feature extraction mismatch, max error {error}')
            golden = cfg['cases'][i]
            if q.tolist() != golden['input']:
                raise RuntimeError(f'{event["event_id"]}: quantized input differs from delivery reference')
            arm_scores = np.zeros(nout, dtype=np.int32)
            arm_class = reference(ip(q), ip(arm_scores))
            cls, scores = infer(device_ip, cfg['offsets'], q.tolist(), nout)
            if cls != arm_class or scores != arm_scores.tolist() or cls != golden['class'] or scores != golden['logits']:
                raise RuntimeError(f'{event["event_id"]}: FPGA/ARM/delivery integer result mismatch')
            truth = int(event['class_id'])
            row = dict(model=model, event_id=event['event_id'], subset=subset,
                       true_class=truth, true_label=labels[truth-base],
                       predicted_class=cls, predicted_label=labels[cls-base],
                       recognition_correct=cls == truth, hardware_match=True,
                       feature_max_error=error, logits=scores)
            rows.append(row)
            if not args.all:
                print(f"{row['event_id']}: 实际标签={row['true_label']}；FPGA识别={row['predicted_label']}；"
                      f"识别{'正确' if row['recognition_correct'] else '错误'}；ARM/FPGA/交付参考一致", flush=True)
    # Invalid samples must be rejected before the FPGA is invoked.
    rejected = []
    for name, fn in [('small_nan', lambda: extract_small(small, np.full((10, 5), np.nan), np.ones((20, 5)))),
                     ('small_short', lambda: extract_small(small, np.ones((9, 5)), np.ones((20, 5)))),
                     ('fusion_short', lambda: extract_fusion(fusion, np.array([0., .2]), np.ones((2, 10))))]:
        try:
            fn()
        except ValueError:
            rejected.append(name)
        else:
            raise RuntimeError(f'Invalid input accepted: {name}')
    summaries = []
    for model in ('small_lr', 'fusion_q32'):
        for subset in sorted({r['subset'] for r in rows if r['model'] == model}):
            selected = [r for r in rows if r['model'] == model and r['subset'] == subset]
            summaries.append(dict(model=model, subset=subset, count=len(selected),
                                  hardware_matches=sum(r['hardware_match'] for r in selected),
                                  correct_labels=sum(r['recognition_correct'] for r in selected)))
    result = dict(mode='all' if args.all else 'examples', events=len(rows),
                  hardware_matches=len(rows), summaries=summaries,
                  maximum_feature_error=maximum_feature_error, invalid_inputs_rejected=rejected,
                  scope='Recorded events; known onset. Existing training records are not a blind accuracy test.',
                  rows=rows)
    out = HERE / 'raw_results'
    out.mkdir(exist_ok=True)
    stem = 'all_events' if args.all else 'examples'
    (out / (stem + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    with (out / (stem + '.csv')).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, ensure_ascii=False, indent=2))
    print('PASS: raw samples -> ARM preprocessing -> actual FPGA; reference agreement verified.', flush=True)


if __name__ == '__main__':
    main()
