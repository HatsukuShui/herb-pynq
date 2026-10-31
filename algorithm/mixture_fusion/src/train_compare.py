"""Predeclared, shared date splits for family comparison and sensor fusion ablation."""
from pathlib import Path
import itertools,json,time,warnings,platform
import numpy as np
import pandas as pd
import joblib
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.svm import SVC
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score,confusion_matrix
from threadpoolctl import threadpool_limits
from fusion_model import DualBranchClassifier,LateFusionClassifier,SEED,check_gradient
from features import LABELS

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; REPORT=ROOT/'report'; MODELS=ROOT/'models'
VIEWS=['mos6_stats','sgp4_fixed_stats','sgp8_stats','stable10_stats','all14_stats','sgp4_signature','stable10_signature']

def factory(c):
    kind=c['kind']
    if kind=='lda': m=LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto')
    elif kind=='svm': m=SVC(C=c['c'],gamma='scale',decision_function_shape='ovr')
    elif kind=='trees': m=ExtraTreesClassifier(n_estimators=240,min_samples_leaf=2,max_features=.8,random_state=SEED,n_jobs=1)
    elif kind=='mlp': m=MLPClassifier(hidden_layer_sizes=(c['hidden'],),activation='tanh',alpha=1.,solver='lbfgs',max_iter=8000,random_state=SEED)
    elif kind=='dual': m=DualBranchClassifier(hidden=c['hidden'],alpha=c['alpha'])
    elif kind=='late': m=LateFusionClassifier(mos_weight=c['mos_weight'])
    else: raise ValueError(kind)
    return make_pipeline(StandardScaler(),m)

def get_scores(model,x):
    return model.decision_function(x) if hasattr(model,'decision_function') else model.predict_proba(x)

def metrics(y,p):
    return dict(correct=int(np.sum(y==p)),total=len(y),accuracy=float(np.mean(y==p)),
                macro_f1=float(f1_score(y,p,labels=np.arange(10),average='macro',zero_division=0)))

def candidates():
    result=[]
    for v in VIEWS:
        for suffix,params in [('lda',dict(kind='lda')),('svm_03',dict(kind='svm',c=.3)),
                              ('svm_3',dict(kind='svm',c=3.)),('trees',dict(kind='trees')),
                              ('mlp16',dict(kind='mlp',hidden=16)),('mlp32',dict(kind='mlp',hidden=32))]:
            result.append(dict(id=v+'__'+suffix,view=v,family='flat_neural' if params['kind']=='mlp' else 'traditional',**params))
    for h in [8,16]:
        for alpha in [.1,1.,10.]:
            result.append(dict(id=f'dual_h{h}_a{str(alpha).replace(".","p")}',view='stable10_stats',family='dual_neural',kind='dual',hidden=h,alpha=alpha))
    for w in [.25,.5,.75]:
        result.append(dict(id=f'late_mos{int(w*100)}',view='stable10_stats',family='late_fusion',kind='late',mos_weight=w))
    return result

def main():
    start=time.time(); REPORT.mkdir(exist_ok=True); MODELS.mkdir(exist_ok=True)
    z=np.load(DATA/'features.npz'); meta=pd.read_csv(DATA/'events.csv')
    ids=np.flatnonzero(~meta.reverse.to_numpy(bool)); reverse=np.flatnonzero(meta.reverse.to_numpy(bool))
    y=z['y'][ids]; days=meta.day.to_numpy()[ids]; dates=sorted(set(days)); cs=candidates(); by_id={c['id']:c for c in cs}
    x={v:z[v][ids] for v in VIEWS}
    families={
        'traditional':[c['id'] for c in cs if c['family']=='traditional'],
        'lda':[c['id'] for c in cs if c['kind']=='lda'],
        'svm':[c['id'] for c in cs if c['kind']=='svm'],
        'extra_trees':[c['id'] for c in cs if c['kind']=='trees'],
        'flat_neural':[c['id'] for c in cs if c['family']=='flat_neural'],
        'dual_neural':[c['id'] for c in cs if c['family']=='dual_neural'],
        'late_fusion':[c['id'] for c in cs if c['family']=='late_fusion'],
    }
    families['all_light_neural']=families['flat_neural']+families['dual_neural']
    for tag,view in [('mos_only','mos6_stats'),('sgp4_only','sgp4_fixed_stats'),('sgp8_only','sgp8_stats'),
                     ('early_fusion','stable10_stats'),('early_all14','all14_stats')]:
        families[tag]=[c['id'] for c in cs if c['kind']=='mlp' and c['view']==view]
    plan=dict(seed=SEED, candidates=cs, families=families, primary='nested leave-date-out family comparison',
              selection='mean inner date accuracy; pooled accuracy; ID',
              ordinary_file_cv='five grouped folds, fixed selected configurations; secondary and post-selection',
              reverse='diagnostic only, previously inspected in this conversation; never fresh blind test',
              no_pretrained_weights=True, historical_data_reused=True,
              preprocessing='StandardScaler fitted within each training fold; metadata never input',
              scopes='MOS + SGP sensors only; no image modality',
              optimizer_max_iter=8000, convergence_change='Raised initial 1600 limit to 8000 after three convergence warnings; no hyperparameter-grid expansion',
              gradient_check=check_gradient())
    (REPORT/'experiment_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    warnlog=[]; cache={}; pipelines={}; audit=[]
    def fit(c,tr,tag):
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always'); model=factory(c).fit(x[c['view']][tr],y[tr])
        for w in captured: warnlog.append(dict(candidate=c['id'],fold=tag,message=str(w.message)))
        return model
    for size in [1,2]:
        for ds in itertools.combinations(dates,size):
            tr=np.isin(days,ds); te=~tr
            assert not set(meta.record_id.iloc[ids[tr]])&set(meta.record_id.iloc[ids[te]])
            assert not set(meta.group.iloc[ids[tr]])&set(meta.group.iloc[ids[te]])
            audit.append(dict(train_dates=list(ds),test_dates=sorted(set(days[te])),train_ids=meta.event_id.iloc[ids[tr]].tolist(),test_ids=meta.event_id.iloc[ids[te]].tolist()))
            for index,c in enumerate(cs):
                model=fit(c,tr,'+'.join(ds)); scores=np.full((len(y),10),np.nan)
                scores[te]=get_scores(model,x[c['view']][te]); cache[(c['id'],ds)]=scores
                if size==2: pipelines[(c['id'],ds)]=model
                if index%15==0: print(f'fit {ds} {index+1}/{len(cs)} {time.time()-start:.0f}s',flush=True)
    def rank(available,choices):
        rows=[]
        for cid in choices:
            pred=np.full(len(y),-1); accuracies=[]
            for held in available:
                tr=tuple(d for d in available if d!=held); te=days==held
                pred[te]=cache[(cid,tr)][te].argmax(1); accuracies.append(float(np.mean(pred[te]==y[te])))
            valid=np.isin(days,available)
            rows.append(dict(candidate=cid,mean_date_accuracy=float(np.mean(accuracies)),pooled_accuracy=float(np.mean(pred[valid]==y[valid]))))
        return sorted(rows,key=lambda r:(-r['mean_date_accuracy'],-r['pooled_accuracy'],r['candidate']))
    pred_table=meta.iloc[ids][['event_id','record_id','day','class_id']].copy(); summary={}; selections={}; exported_folds={}
    all_ranking=rank(tuple(dates),list(by_id))
    pd.DataFrame([{**by_id[r['candidate']],**r} for r in all_ranking]).to_csv(REPORT/'candidate_comparison.csv',index=False,encoding='utf-8-sig')
    for name,choices in families.items():
        prediction=np.empty(len(y),int); rows=[]
        for held in dates:
            ds=tuple(d for d in dates if d!=held); te=days==held; ranking=rank(ds,choices); cid=ranking[0]['candidate']
            prediction[te]=cache[(cid,ds)][te].argmax(1)
            rows.append(dict(held_date=held,selected=cid,inner_ranking=ranking,test=metrics(y[te],prediction[te])))
            if name=='dual_neural': exported_folds[held]=dict(candidate=by_id[cid],pipeline=pipelines[(cid,ds)],test_ids=ids[te])
        final_cid=rank(tuple(dates),choices)[0]['candidate']; c=by_id[final_cid]
        model=fit(c,np.ones(len(y),bool),'all_normal'); final_pred=np.empty(len(y),int)
        for held in dates:
            te=days==held; ds=tuple(d for d in dates if d!=held); final_pred[te]=cache[(final_cid,ds)][te].argmax(1)
        group_pred=np.empty(len(y),int)
        for k,(tr,te) in enumerate(GroupKFold(n_splits=5).split(y,y,meta.group.iloc[ids])):
            assert not set(meta.group.iloc[ids[tr]])&set(meta.group.iloc[ids[te]])
            group_pred[te]=get_scores(fit(c,tr,f'file{k}'),x[c['view']][te]).argmax(1)
        rp=get_scores(model,z[c['view']][reverse]).argmax(1)
        summary[name]=dict(nested=metrics(y,prediction),fixed_selected_date_exploratory=metrics(y,final_pred),
                           grouped_file_exploratory=metrics(y,group_pred),reverse_diagnostic=metrics(z['y'][reverse],rp),
                           selected=c,confusion=confusion_matrix(y,prediction,labels=np.arange(10)).tolist())
        selections[name]=rows
        pred_table[name+'_nested']=prediction+1; pred_table[name+'_fixed']=final_pred+1; pred_table[name+'_file']=group_pred+1
        joblib.dump(dict(candidate=c,pipeline=model,labels=LABELS,training_events=400),MODELS/(name+'.joblib'),compress=3)
        print(name,json.dumps({k:v for k,v in summary[name].items() if k!='confusion'}),flush=True)
    joblib.dump(exported_folds,MODELS/'dual_outer_folds.joblib',compress=3)
    pred_table.to_csv(REPORT/'predictions.csv',index=False,encoding='utf-8-sig')
    comparison=[]
    for name,s in summary.items():
        comparison.append(dict(experiment=name,nested_accuracy=s['nested']['accuracy'],nested_macro_f1=s['nested']['macro_f1'],
                               fixed_date_exploratory=s['fixed_selected_date_exploratory']['accuracy'],
                               grouped_file_exploratory=s['grouped_file_exploratory']['accuracy'],
                               reverse_diagnostic=s['reverse_diagnostic']['accuracy'],selected=s['selected']['id']))
    pd.DataFrame(comparison).to_csv(REPORT/'comparison.csv',index=False,encoding='utf-8-sig')
    for filename,value in [('comparison.json',summary),('nested_selections.json',selections),('split_audit.json',audit),('training_warnings.json',warnlog)]:
        (REPORT/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    (REPORT/'training_run.json').write_text(json.dumps(dict(seconds=time.time()-start,warning_count=len(warnlog),python=platform.python_version(),gradient_check=plan['gradient_check']),indent=2),encoding='utf-8')
    print(f'Completed in {time.time()-start:.1f}s; warnings={len(warnlog)}',flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=2): main()
