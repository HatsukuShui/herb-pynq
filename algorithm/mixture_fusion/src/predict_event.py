"""Predict one known-onset event with the exported two-branch NumPy model."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
from features import LABELS,GRID,bin_median,describe
from quantization import inputs,inference

ROOT=Path(__file__).resolve().parents[1]
CHANNELS=[f'MOS{i}(k)' for i in range(1,7)]+[f'SGP{i}' for i in range(5,9)]

def extract100(t,raw,onset):
    if len(t)<2 or np.any(~np.isfinite(t)) or np.any(np.diff(t)<=0): raise ValueError('Invalid timestamps')
    if not np.isfinite(onset) or onset-8<t[0] or onset+35.25>t[-1]: raise ValueError('Incomplete window')
    local=(t>=onset-8.25)&(t<=onset+35.25)
    if np.max(np.diff(t[local]))>.8: raise ValueError('Sampling gap exceeds 0.8 seconds')
    if not np.isfinite(raw[local]).all() or (raw[local]<=0).any(): raise ValueError('Invalid sensor values')
    base_mask=(t>=onset-8)&(t<=onset-3)
    if not base_mask.any():raise ValueError('No local baseline')
    base=np.median(raw[base_mask],axis=0); values=bin_median(t,raw,onset+GRID)
    rel=(values-base)/base;rel[:,:6]=np.log(values[:,:6]/base[:6])
    return describe(rel).ravel()

def main():
    p=argparse.ArgumentParser();p.add_argument('--csv',type=Path,required=True);p.add_argument('--onset-seconds',type=float,required=True)
    p.add_argument('--format',choices=['float','q32','q16'],default='q32');p.add_argument('--output',type=Path)
    args=p.parse_args(); df=pd.read_csv(args.csv)
    if 'time_s' in df: t=df.time_s.to_numpy(float)
    else: t=(pd.to_datetime(df.TIME)-pd.to_datetime(df.TIME.iloc[0])).dt.total_seconds().to_numpy()
    f=extract100(t,df[CHANNELS].to_numpy(float),args.onset_seconds);weights=np.load(ROOT/'models/dual_weights.npz'); z=(f-weights['mean'])/weights['scale']
    if args.format=='float':
        h=np.r_[np.tanh(z[:60]@weights['wm']+weights['bm']),np.tanh(z[60:]@weights['ws']+weights['bs'])]
        scores=h@weights['wo']+weights['bo']
    else:
        fmt=json.loads((ROOT/'deploy'/args.format/'format.json').read_text()); params=np.load(ROOT/'deploy'/args.format/'parameters.npz')
        scores=inference(inputs(z[None,:],fmt),fmt,params)[0]/2.**fmt['output_frac']
    order=np.argsort(-scores,kind='stable'); chosen=int(order[0])
    result=dict(class_id=chosen+1,label=LABELS[chosen],format=args.format,
                top3=[dict(class_id=int(i)+1,label=LABELS[i],logit=float(scores[i])) for i in order[:3]],
                note='Logits are not confidence probabilities; this interface requires a known response onset.')
    content=json.dumps(result,ensure_ascii=False,indent=2);print(content)
    if args.output: args.output.write_text(content,encoding='utf-8')

if __name__=='__main__':main()
