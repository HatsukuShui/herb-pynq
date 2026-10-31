"""On PYNQ 3.1.1: sh run_on_pynq.sh (sets the venv and XRT environment)."""
import argparse
import json
import time
from pathlib import Path


def signed(value):
    return value - 2**32 if value & 0x80000000 else value


def infer(ip, offsets, inputs, outputs, timeout=2.0):
    # Clear stale ap_done before starting this invocation.
    control = ip.read(offsets['control'])
    if not control & 4:
        raise RuntimeError('IP is not idle; reload overlay before retrying')
    for i, value in enumerate(inputs):
        ip.write(offsets['input'] + 4*i, value & 0xffffffff)
    ip.write(offsets['control'], 1)
    deadline = time.monotonic() + timeout
    while not ip.read(offsets['control']) & 2:
        if time.monotonic() >= deadline:
            raise TimeoutError('Classifier timeout; reload overlay before retrying')
        time.sleep(0.00001)
    return signed(ip.read(offsets['return'])), [signed(ip.read(offsets['output'] + 4*i)) for i in range(outputs)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=Path('.'))
    args = parser.parse_args()
    from pynq import Overlay
    overlay = Overlay(str(args.directory / 'herb_models.bit'))
    for model in ('small_lr', 'fusion_q32'):
        data = json.loads((args.directory / f'{model}_replay.json').read_text())
        ip = getattr(overlay, data['instance'])
        start = time.monotonic()
        for index, case in enumerate(data['cases']):
            cls, scores = infer(ip, data['offsets'], case['input'], len(case['logits']))
            if cls != case['class'] or scores != case['logits']:
                raise RuntimeError(f'{model} vector {index}: class={cls}, logits={scores}')
        print(f"PASS {model}: {len(data['cases'])} vectors; host replay {time.monotonic()-start:.3f}s")
    print('Integer replay passed. This is not a measurement of recognition accuracy.')


if __name__ == '__main__':
    main()
