"""Independent checks of single-event inference, metadata separation and saved fold scalers."""
from pathlib import Path
import json,subprocess,sys
import numpy as np
import pandas as pd
import joblib
from fusion_model import DualBranchClassifier
from predict_event import extract100,CHANNELS

ROOT=Path(__file__).resolve().parents[1]

def main():
    meta=pd.read_csv(ROOT/'data/events.csv'); z=np.load(ROOT/'data/features.npz'); windows=np.load(ROOT/'data/raw_event_windows.npz'); normal=~meta.reverse.to_numpy(bool)
    error=0.
    for i,row in meta.iterrows():
        a=windows[row.event_id]; f=extract100(a[:,0],a[:,[1,2,3,4,5,6,11,12,13,14]],0.)
        error=max(error,float(np.max(np.abs(f-z['stable10_stats'][i]))))
        assert np.allclose(f,z['stable10_stats'][i],atol=1e-10,rtol=1e-10)
    final=joblib.load(ROOT/'models/dual_neural.joblib'); p=final['pipeline']; x=z['stable10_stats']
    assert np.allclose(p[0].mean_,x[normal].mean(0)); assert np.all(p[0].n_samples_seen_==400)
    folds=joblib.load(ROOT/'models/dual_outer_folds.joblib'); all_ids=[]
    for day,fold in folds.items():
        tr=normal&(meta.day.to_numpy()!=day);te=normal&(meta.day.to_numpy()==day)
        assert np.array_equal(fold['test_ids'],np.flatnonzero(te))
        assert not set(meta.record_id[tr])&set(meta.record_id[te])
        assert not set(meta.group[tr])&set(meta.group[te])
        assert np.allclose(fold['pipeline'][0].mean_,x[tr].mean(0))
        all_ids.extend(fold['test_ids'])
    assert sorted(all_ids)==np.flatnonzero(normal).tolist()
    # First reverse event is chosen by deterministic order, not correctness.
    idx=int(np.flatnonzero(~normal)[0]); row=meta.iloc[idx]; a=windows[row.event_id]
    sample=pd.DataFrame(a[:,[0,1,2,3,4,5,6,11,12,13,14]],columns=['time_s']+CHANNELS)
    sample.to_csv(ROOT/'data/example_event.csv',index=False)
    outputs={}
    for fmt in ['float','q32','q16']:
        dest=ROOT/'report'/('example_'+fmt+'.json')
        result=subprocess.run([sys.executable,str(ROOT/'src/predict_event.py'),'--csv',str(ROOT/'data/example_event.csv'),'--onset-seconds','0','--format',fmt,'--output',str(dest)],capture_output=True,text=True,encoding='utf-8',check=True)
        outputs[fmt]=json.loads(dest.read_text(encoding='utf-8'))
    assert outputs['float']['class_id']==int(p.predict(x[idx:idx+1])[0])+1
    info=dict(event_id=row.event_id,true_class_id=int(row.class_id),true_label=row.label,selection='first reverse event, no cherry-picking',predictions={k:v['class_id'] for k,v in outputs.items()})
    (ROOT/'data/example_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    summary=dict(raw_events=410,max_independent_python_feature_error=error,outer_fold_train_scalers_checked=3,
                 all_normal_events_held_out_once=True,record_and_group_overlap=False,final_scaler_training_events=400,
                 subprocess_cli_formats=['float','q32','q16'],example=info)
    (ROOT/'report/input_verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
