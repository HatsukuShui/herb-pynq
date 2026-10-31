"""Small MOS/SGP two-branch network with explicit NumPy forward and gradients.

No pretrained architecture or weights are loaded. SciPy supplies L-BFGS only.
Input: 60 standardized MOS summaries followed by 40 standardized SGP summaries.
"""
import warnings
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPClassifier

SEED = 20261012

def rank_vote(scores):
    order = np.argsort(-scores,axis=1,kind='stable')
    rank = np.empty_like(order)
    np.put_along_axis(rank,order,np.arange(10)[None,:],axis=1)
    values = 2.**(-rank)
    return values / values.sum(axis=1,keepdims=True)

class DualBranchClassifier(ClassifierMixin, BaseEstimator):
    def __init__(self, hidden=8, alpha=1., max_iter=8000, seed=SEED):
        self.hidden=hidden; self.alpha=alpha; self.max_iter=max_iter; self.seed=seed

    def shapes(self):
        h=self.hidden
        return [(60,h),(h,),(40,h),(h,),(2*h,10),(10,)]

    def unpack(self,theta):
        arrays=[]; offset=0
        for shape in self.shapes():
            count=int(np.prod(shape)); arrays.append(theta[offset:offset+count].reshape(shape)); offset+=count
        return arrays

    def initial(self):
        rng=np.random.default_rng(self.seed); arrays=[]
        for shape in self.shapes():
            if len(shape)==2:
                limit=np.sqrt(6./sum(shape)); arrays.append(rng.uniform(-limit,limit,shape))
            else: arrays.append(np.zeros(shape))
        return np.concatenate([a.ravel() for a in arrays])

    def objective(self,theta,x,y):
        wm,bm,ws,bs,wo,bo=self.unpack(theta)
        hm=np.tanh(x[:,:60]@wm+bm); hs=np.tanh(x[:,60:]@ws+bs)
        hidden=np.column_stack([hm,hs]); logits=hidden@wo+bo; n=len(y)
        loss=np.mean(logsumexp(logits,axis=1)-logits[np.arange(n),y])
        loss+=self.alpha*(np.sum(wm*wm)+np.sum(ws*ws)+np.sum(wo*wo))/(2*n)
        delta=softmax(logits,axis=1); delta[np.arange(n),y]-=1; delta/=n
        dwo=hidden.T@delta+self.alpha/n*wo; dbo=delta.sum(0)
        dh=delta@wo.T; dm=dh[:,:self.hidden]*(1-hm*hm); ds=dh[:,self.hidden:]*(1-hs*hs)
        grad=[x[:,:60].T@dm+self.alpha/n*wm,dm.sum(0),x[:,60:].T@ds+self.alpha/n*ws,ds.sum(0),dwo,dbo]
        return float(loss),np.concatenate([g.ravel() for g in grad])

    def fit(self,x,y):
        x=np.asarray(x,dtype=float); y=np.asarray(y,dtype=int)
        if x.ndim!=2 or x.shape[1]!=100 or not np.isfinite(x).all(): raise ValueError('Expected finite N x 100 input')
        self.classes_=np.unique(y); self.n_features_in_=100
        if not np.array_equal(self.classes_,np.arange(10)): raise ValueError('Training fold must include all ten classes')
        result=minimize(self.objective,self.initial(),args=(x,y),method='L-BFGS-B',jac=True,
                        options=dict(maxiter=self.max_iter,maxfun=25000,gtol=1e-6,ftol=1e-10,maxls=40))
        self.theta_=result.x; self.n_iter_=result.nit; self.loss_=float(result.fun)
        self.optimization_success_=bool(result.success); self.optimization_message_=str(result.message)
        if not result.success: warnings.warn(self.optimization_message_,ConvergenceWarning)
        return self

    def decision_function(self,x):
        wm,bm,ws,bs,wo,bo=self.unpack(self.theta_); x=np.asarray(x)
        return np.column_stack([np.tanh(x[:,:60]@wm+bm),np.tanh(x[:,60:]@ws+bs)])@wo+bo

    def predict_proba(self,x): return softmax(self.decision_function(x),axis=1)
    def predict(self,x): return self.decision_function(x).argmax(axis=1)

class LateFusionClassifier(ClassifierMixin, BaseEstimator):
    """Weighted rank decision fusion. Output scores are not calibrated probabilities."""
    def __init__(self, mos_weight=.5, hidden=16, seed=SEED):
        self.mos_weight=mos_weight; self.hidden=hidden; self.seed=seed

    def fit(self,x,y):
        self.classes_=np.unique(y); self.n_features_in_=100; self.branches_=[]
        for part in [x[:,:60],x[:,60:]]:
            m=MLPClassifier(hidden_layer_sizes=(self.hidden,),activation='tanh',alpha=1.,
                            solver='lbfgs',max_iter=8000,random_state=self.seed)
            self.branches_.append(m.fit(part,y))
        return self

    def decision_function(self,x):
        a=rank_vote(self.branches_[0].predict_proba(x[:,:60]))
        b=rank_vote(self.branches_[1].predict_proba(x[:,60:]))
        return self.mos_weight*a+(1-self.mos_weight)*b

    def predict(self,x): return self.decision_function(x).argmax(axis=1)

def check_gradient():
    rng=np.random.default_rng(1719); x=rng.normal(size=(13,100)); y=np.arange(13)%10
    model=DualBranchClassifier(hidden=3); theta=model.initial(); _,analytic=model.objective(theta,x,y)
    errors=[]
    for i in rng.choice(len(theta),40,replace=False):
        plus=theta.copy(); minus=theta.copy(); plus[i]+=1e-6; minus[i]-=1e-6
        numeric=(model.objective(plus,x,y)[0]-model.objective(minus,x,y)[0])/2e-6
        errors.append(abs(numeric-analytic[i]))
    maximum=max(errors)
    if maximum>1e-7: raise AssertionError(f'Gradient check failed: {maximum}')
    return dict(parameters_checked=40,max_absolute_error=maximum)
