"""用正例和错误注入检查技能脚本；测试文件只生成在本技能目录内。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

skill_root = Path(__file__).resolve().parent


def load_module(module_name, relative_path):
    """按显式路径加载技能，避免依赖环境中的同名模块。"""
    module_spec = importlib.util.spec_from_file_location(module_name, skill_root / relative_path)
    loaded_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(loaded_module)
    return loaded_module


overlay_module = load_module('overlay_check', 'overlay_check/check_overlay.py')
golden_module = load_module('golden_check', 'golden_check/compare_results.py')


class SkillTests(unittest.TestCase):
    """验证文件冲突和不完整结果都不会被误判为通过。"""
    def test_overlay_files_and_xsa_conflict(self):
        with tempfile.TemporaryDirectory(dir=skill_root) as temporary_directory:
            bitstream_path = Path(temporary_directory) / 'example.bit'
            bitstream_path.write_bytes(b'test-fixture-not-a-real-bitstream')
            with self.assertRaises(ValueError):
                overlay_module.check_overlay(bitstream_path)
            bitstream_path.with_suffix('.hwh').write_text('<test/>', encoding='utf-8')
            self.assertEqual(overlay_module.check_overlay(bitstream_path)['status'], 'file_check_passed')
            bitstream_path.with_suffix('.xsa').write_bytes(b'fixture')
            with self.assertRaises(ValueError):
                overlay_module.check_overlay(bitstream_path)

    def test_golden_full_scores_and_membership(self):
        expected_records = [{'record_id': 'sample_a', 'class_id': 1, 'scores': [-2, 3]}]
        self.assertEqual(golden_module.compare_records(expected_records, expected_records)['matches'], 1)
        invalid_cases = [
            [{'record_id': 'sample_a', 'class_id': 1, 'scores': [-2, 4]}],
            expected_records * 2,
            [],
            [{'record_id': 'sample_b', 'class_id': 1, 'scores': [-2, 3]}],
            [{'record_id': 'sample_a', 'class_id': True, 'scores': [-2, 3]}],
        ]
        for actual_records in invalid_cases:
            with self.assertRaises(ValueError):
                golden_module.compare_records(expected_records, actual_records)


if __name__ == '__main__':
    unittest.main()
