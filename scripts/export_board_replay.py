"""Export integer replay data and actual HLS register offsets (no joblib loading)."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / 'third_party/algorithm_20261013/shuishengxi_delivery'


def array(text, name):
    match = re.search(r'\b' + name + r'\[\d+\]\s*=\s*\{([^}]+)\}', text)
    if not match:
        raise ValueError(name)
    return [int(x) for x in re.findall(r'-?\d+', match[1])]


def main():
    output = ROOT / 'build/deploy'
    output.mkdir(parents=True, exist_ok=True)
    specs = [
        ('small_classifier', 'small_lr', 'small_lr_q', DELIVERY / 'small_herb/deploy/test_vectors.h', 50, 8, 'TEST_LR', 0),
        ('fusion_classifier', 'fusion_q32', 'fusion_q', DELIVERY / 'mixture_fusion/sim/q32/test_vectors.h', 100, 10, 'TEST_LOGITS', 1),
    ]
    for instance, model, top, source, n_in, n_out, score_name, base in specs:
        text = source.read_text()
        inputs, scores = array(text, 'TEST_INPUT'), array(text, score_name)
        count = int(re.search(r'TEST_COUNT\s*=\s*(\d+)', text)[1])
        assert len(inputs) == count * n_in and len(scores) == count * n_out
        header = ROOT / f'build/models/{model}/solution1/impl/ip/drivers/{top}_v1_0/src/x{top}_hw.h'
        regs = dict(re.findall(r'#define\s+\w+_CTRL_(\w+)\s+(0x[0-9a-fA-F]+|\d+)', header.read_text()))
        offsets = {k: int(regs[v], 0) for k, v in {
            'control': 'ADDR_AP_CTRL', 'return': 'ADDR_AP_RETURN',
            'input': 'ADDR_INPUT_Q_BASE', 'output': 'ADDR_LOGITS_Q_BASE',
        }.items()}
        assert int(regs['DEPTH_INPUT_Q']) == n_in and int(regs['DEPTH_LOGITS_Q']) == n_out
        cases = []
        classes = array(text, 'TEST_CLASS') if base else None
        for i in range(count):
            logits = scores[i*n_out:(i+1)*n_out]
            cls = max(range(n_out), key=logits.__getitem__) + base
            if classes is not None:
                assert classes[i] == cls
            cases.append({'input': inputs[i*n_in:(i+1)*n_in], 'logits': logits, 'class': cls})
        payload = {'instance': instance, 'model': model, 'offsets': offsets,
                   'header_sha256': hashlib.sha256(header.read_bytes()).hexdigest(), 'cases': cases}
        (output / f'{model}_replay.json').write_text(json.dumps(payload), encoding='utf-8')
        print(f'{model}: exported {count} vectors; offsets={offsets}')


if __name__ == '__main__':
    main()
