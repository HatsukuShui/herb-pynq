"""Verify repository payloads, deployment dependencies, and IP references."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'source_manifest.json').read_text(encoding='utf-8'))
    for name, entry in manifest.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f'Missing or unsafe payload: {name}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError(f'Payload changed: {name}')
    for relative in ['build/deploy/manifest.json', 'build/deploy/raw_manifest.json']:
        source = ROOT / relative
        for name, expected in json.loads(source.read_text(encoding='utf-8')).items():
            path = (source.parent / name).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                raise ValueError(f'Missing deployment file: {name}')
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f'Deployment hash mismatch: {name}')
    ip_files = 0
    for model in ['small_lr', 'fusion_q32']:
        base = ROOT / f'build/models/{model}/solution1/impl/ip'
        tree = ET.parse(base / 'component.xml')
        namespace = {'s': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}
        for node in tree.findall('.//s:file/s:name', namespace):
            if not (base / node.text).is_file():
                raise ValueError(f'Missing IP dependency: {model}/{node.text}')
            ip_files += 1
    if not ip_files:
        raise ValueError('No IP file references found')
    deploy = ROOT / 'build/deploy'
    for name in ['herb_models.bit', 'herb_models.hwh', 'hardware_export/herb_models.xsa']:
        if not (deploy / name).is_file():
            raise ValueError(f'Missing deployment artifact: {name}')
    if (deploy / 'herb_models.xsa').exists():
        raise ValueError('Keep XSA in hardware_export, away from bit/HWH')
    print(f'PASS: {len(manifest)} original payloads; {ip_files} IP references; deployment hashes and layout')


if __name__ == '__main__':
    main()
