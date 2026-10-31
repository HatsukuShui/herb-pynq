"""Open numerical parameter exports for comparison baselines, no additional fitting."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
from fusion_model import DualBranchClassifier, LateFusionClassifier

ROOT=Path(__file__).resolve().parents[1]

def main():
    index={}
    for name in ['traditional','lda','svm','extra_trees','flat_neural']:
        bundle=joblib.load(ROOT/'models'/(name+'.joblib')); p=bundle['pipeline']; s,m=p[0],p[-1]
        arrays=dict(mean=s.mean_,scale=s.scale_); description=dict(candidate=bundle['candidate'],labels=bundle['labels'],class_encoding='arrays 0..9; external IDs 1..10')
        kind=bundle['candidate']['kind']
        if kind=='mlp':
            arrays.update(w1=m.coefs_[0],b1=m.intercepts_[0],w2=m.coefs_[1],b2=m.intercepts_[1]); description.update(activation='tanh',output='linear logits; optional softmax',parameter_count=sum(v.size for k,v in arrays.items() if k not in ['mean','scale']))
        elif kind=='svm':
            arrays.update(support_vectors=m.support_vectors_,dual_coef=m.dual_coef_,intercept=m.intercept_,n_support=m.n_support_,gamma=np.array(m._gamma))
            description.update(kernel='RBF',prediction='scikit-learn SVC multiclass pairwise scores -> OVR decision_function; argmax matches experiment rank selection',support_vectors=len(m.support_))
        elif kind=='lda': arrays.update(coef=m.coef_,intercept=m.intercept_)
        elif kind=='trees':
            roots=[];left=[];right=[];features=[];threshold=[];values=[];offset=0
            for est in m.estimators_:
                t=est.tree_;roots.append(offset);left.extend(np.where(t.children_left<0,-1,t.children_left+offset));right.extend(np.where(t.children_right<0,-1,t.children_right+offset));features.extend(t.feature);threshold.extend(t.threshold)
                v=t.value[:,0,:];values.extend(v/v.sum(1,keepdims=True));offset+=t.node_count
            arrays.update(roots=np.array(roots),left=np.array(left),right=np.array(right),feature=np.array(features),threshold=np.array(threshold),values=np.array(values))
            description.update(tree_count=len(roots),node_count=offset,tree_input_cast='float32 after standardization',output='average leaf class proportions')
        np.savez_compressed(ROOT/'models'/(name+'_parameters.npz'),**arrays)
        description['arrays']={k:list(v.shape) for k,v in arrays.items()}
        (ROOT/'models'/(name+'_parameters.json')).write_text(json.dumps(description,ensure_ascii=False,indent=2),encoding='utf-8')
        index[name]=description
    (ROOT/'report/baseline_exports.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
    z=np.load(ROOT/'data/features.npz');meta=pd.read_csv(ROOT/'data/events.csv');mask=meta.reverse.to_numpy(bool)
    reverse=meta.loc[mask,['event_id','source','class_id','label']].copy()
    for name in ['traditional','lda','svm','extra_trees','flat_neural','dual_neural','late_fusion']:
        bundle=joblib.load(ROOT/'models'/(name+'.joblib'));model=bundle['pipeline'];xx=z[bundle['candidate']['view']][mask]
        score=model.decision_function(xx) if hasattr(model,'decision_function') else model.predict_proba(xx)
        reverse[name+'_pred']=score.argmax(1)+1
    reverse.to_csv(ROOT/'report/reverse_predictions.csv',index=False,encoding='utf-8-sig')
    print('Exported five baseline bundles; no model retrained.')

if __name__=='__main__':main()
