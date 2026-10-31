"""按记录唯一编号比较整数分类器的完整输出，缺记录不能算通过。"""
import argparse
import json
from pathlib import Path


def index_records(records):
    """验证记录结构和整数类型，拒绝重复编号及空数据。"""
    if not isinstance(records, list) or not records:
        raise ValueError('Expected a nonempty record list')
    record_index = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Record must be an object')
        record_id = record.get('record_id')
        if not isinstance(record_id, str) or not record_id or record_id in record_index:
            raise ValueError('Missing or duplicate record_id')
        if type(record.get('class_id')) is not int:
            raise ValueError('class_id must be an integer')
        scores = record.get('scores')
        if not isinstance(scores, list) or not scores or any(type(score) is not int for score in scores):
            raise ValueError('scores must be a nonempty integer list')
        record_index[record_id] = record
    return record_index


def compare_records(expected_records, actual_records):
    """类别和每个整数得分必须精确一致，不对不同长度输出截断比较。"""
    expected_index = index_records(expected_records)
    actual_index = index_records(actual_records)
    if expected_index.keys() != actual_index.keys():
        raise ValueError('Record ID sets differ')
    mismatches = []
    for record_id, expected_record in expected_index.items():
        actual_record = actual_index[record_id]
        if (expected_record['class_id'] != actual_record['class_id']
                or expected_record['scores'] != actual_record['scores']):
            mismatches.append(record_id)
    if mismatches:
        raise ValueError('Output mismatch: ' + ', '.join(mismatches[:10]))
    return {'records': len(expected_index), 'matches': len(expected_index)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('expected', type=Path)
    parser.add_argument('actual', type=Path)
    arguments = parser.parse_args()
    print(compare_records(json.loads(arguments.expected.read_text(encoding='utf-8')),
                          json.loads(arguments.actual.read_text(encoding='utf-8'))))
