"""通用 Overlay 加载前文件检查；不导入 PYNQ，不执行硬件操作。"""
import argparse
from pathlib import Path


def check_overlay(bitstream_path):
    """检查位流、同名 HWH 和同名 XSA 冲突；器件匹配仍需上板确认。"""
    bitstream_path = Path(bitstream_path)
    if bitstream_path.suffix.lower() != '.bit':
        raise ValueError('Expected a .bit file')
    metadata_path = bitstream_path.with_suffix('.hwh')
    for required_file in (bitstream_path, metadata_path):
        if not required_file.is_file() or required_file.stat().st_size == 0:
            raise ValueError(f'Missing or empty file: {required_file.name}')
    if bitstream_path.with_suffix('.xsa').exists():
        raise ValueError('Same-name XSA found beside bit/HWH; isolate hardware export first')
    return {'bitstream': str(bitstream_path), 'metadata': str(metadata_path), 'status': 'file_check_passed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bitstream', type=Path)
    print(check_overlay(parser.parse_args().bitstream))
