"""Rebuild audited events directly from the original archive, never from old models."""
from pathlib import Path
import argparse, hashlib, io, json, re, zipfile
import numpy as np
import pandas as pd
from features import LABELS, CHANNELS, locate, extract_event, elapsed

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def decode(info):
    return info.filename if info.flag_bits & 0x800 else info.filename.encode('cp437').decode('gbk')

def records(archive):
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            if entry.filename.lower().endswith('.csv'):
                blob = z.read(entry)
                yield decode(entry).split('/', 1)[1], blob, pd.read_csv(io.BytesIO(blob))

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--archive', type=Path, required=True)
    args = p.parse_args()
    DATA.mkdir(exist_ok=True)
    inventory, events, matrices, curves, nested, raw_windows = [], [], {}, [], [], []
    for number, (name, blob, df) in enumerate(records(args.archive), 1):
        rid = f'r{number:03d}'
        rev = '反序' in name
        peaks = [] if '盖帽' in name else locate(df)
        status = ('excluded_cap' if '盖帽' in name else 'excluded_unlabelled' if '/测试/' in name
                  else 'reverse_diagnostic' if rev else 'normal')
        if status in ['normal', 'reverse_diagnostic'] and len(peaks) != 10:
            raise ValueError(f'{name}: expected labelled ten-event recording, detected {len(peaks)}')
        t = elapsed(df)
        inventory.append(dict(record_id=rid, source=name, status=status, peaks=len(peaks),
                              rows=len(df), sha256=hashlib.sha256(blob).hexdigest(),
                              missing=int(df.isna().sum().sum()), duplicate_t=int(pd.to_datetime(df.TIME).duplicated().sum()),
                              max_gap_s=float(np.max(np.diff(t)))))
        if status.startswith('excluded'):
            continue
        batch = name.split('/')[0]
        file_number = re.findall(r'\d+', name.split('/')[-1].split('.')[0])[-1]
        group = batch + ('/10_11' if file_number in ['10', '11'] else '/' + file_number)
        for i, event in enumerate(peaks):
            if i + 1 < len(peaks) and event['onset'] + 35.25 >= peaks[i + 1]['onset']:
                raise ValueError('Response overlaps following event')
            feature, curve = extract_event(df, event['onset'])
            label = 9 - i if rev else i
            event_id = f'{rid}_e{i+1:02d}'
            events.append(dict(event_id=event_id, record_id=rid, source=name,
                               day=str(pd.to_datetime(df.TIME.iloc[0]).date()), group=group,
                               reverse=rev, event_index=i+1, class_id=label+1, label=LABELS[label], **event))
            for key, value in feature.items():
                matrices.setdefault(key, []).append(value)
            curves.append(curve)
            mask = (t >= event['onset']-8.25) & (t <= event['onset']+35.5)
            # Relative seconds make a single event independently replayable.
            raw_windows.append((event_id, np.column_stack([t[mask]-event['onset'], df.loc[mask, CHANNELS].to_numpy(float)])))
    hashes = {r['sha256'] for r in inventory}
    if len(hashes) != len(inventory):
        raise ValueError('Duplicate top-level files require explicit deduplication')
    with zipfile.ZipFile(args.archive) as z:
        for entry in z.infolist():
            if entry.filename.lower().endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(z.read(entry))) as zz:
                    for inner in zz.infolist():
                        if inner.filename.lower().endswith('.csv'):
                            digest = hashlib.sha256(zz.read(inner)).hexdigest()
                            nested.append(dict(archive=decode(entry), source=decode(inner), sha256=digest,
                                               duplicates_top_level=digest in hashes))
    if not all(r['duplicates_top_level'] for r in nested):
        raise ValueError('Unreviewed distinct nested records')
    meta = pd.DataFrame(events)
    pd.DataFrame(inventory).to_csv(DATA/'file_inventory.csv', index=False, encoding='utf-8-sig')
    meta.to_csv(DATA/'events.csv', index=False, encoding='utf-8-sig')
    np.savez_compressed(DATA/'features.npz', **{k:np.asarray(v) for k,v in matrices.items()},
                        curves=np.asarray(curves), y=meta.class_id.to_numpy()-1)
    np.savez_compressed(DATA/'raw_event_windows.npz', **dict(raw_windows))
    pd.DataFrame([dict(class_id=i+1,label=s) for i,s in enumerate(LABELS)]).to_csv(DATA/'labels.csv',index=False,encoding='utf-8-sig')
    protocol = dict(raw_sha256=hashlib.sha256(args.archive.read_bytes()).hexdigest(), original_name=args.archive.name,
                    status_counts=pd.Series([x['status'] for x in inventory]).value_counts().to_dict(),
                    normal_events=int((~meta.reverse).sum()), reverse_events=int(meta.reverse.sum()),
                    original_channels=CHANNELS, stable_fusion_channels=CHANNELS[:6]+CHANNELS[10:],
                    top_level_unique_hashes=len(hashes), nested_records=len(nested),
                    nested_duplicate_count=sum(x['duplicates_top_level'] for x in nested),
                    normal_class_counts=meta[~meta.reverse].class_id.value_counts().sort_index().to_dict(),
                    label_rule='normal 1..10; reverse 10..1; caps and unlabelled partial tests excluded',
                    baseline_seconds=[-8,-3],response_seconds=[0,35],sample_grid_seconds=.5,
                    input_metadata_excluded=['class_id','event_index','record_id','filename','day','absolute_time'],
                    limitations=['fixed order confounding','offline onset detection','three dates only','local baseline not verified clean air'],
                    no_pretrained_models=True, extraction_source='new feature implementation authored during this conversation')
    (DATA/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf-8')
    (DATA/'nested_duplicate_audit.json').write_text(json.dumps(nested,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(protocol,ensure_ascii=False,indent=2))

if __name__ == '__main__': main()
