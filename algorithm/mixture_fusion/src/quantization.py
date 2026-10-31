"""Integer reference shared by export and independent validation."""
import numpy as np

FORMATS={
    'q32': dict(input_bits=32,input_frac=16,weight_bits=32,weight_frac=20,hidden_bits=32,hidden_frac=20,output_frac=16),
    'q16': dict(input_bits=16,input_frac=10,weight_bits=16,weight_frac=12,hidden_bits=16,hidden_frac=14,output_frac=12),
}

def rounded(values,frac):
    v=np.asarray(values,dtype=np.float64)*2.**frac
    if not np.isfinite(v).all() or np.max(np.abs(v))>=2.**62: raise ValueError('Quantization value out of range')
    return np.where(v>=0,np.floor(v+.5),np.ceil(v-.5)).astype(np.int64)

def shift(v,bits):
    v=np.asarray(v,dtype=np.int64); half=1<<(bits-1)
    return np.where(v>=0,(v+half)>>bits,-(((-v)+half)>>bits))

def quantize(model,format_name):
    f=FORMATS[format_name].copy(); wm,bm,ws,bs,wo,bo=model.unpack(model.theta_)
    f.update(hidden=model.hidden,acc_frac=f['input_frac']+f['weight_frac'],out_acc_frac=f['hidden_frac']+f['weight_frac'])
    arrays={k:rounded(v,f['weight_frac']) for k,v in [('wm',wm),('ws',ws),('wo',wo)]}
    arrays.update(bm=rounded(bm,f['acc_frac']),bs=rounded(bs,f['acc_frac']),bo=rounded(bo,f['out_acc_frac']),
                  lut=rounded(np.tanh(np.linspace(-8,8,1025)),f['hidden_frac']))
    for k in ['wm','ws','wo']:
        if arrays[k].min()<-(1<<(f['weight_bits']-1)) or arrays[k].max()>=(1<<(f['weight_bits']-1)):
            raise ValueError(format_name+' weight overflow; no silent clipping allowed')
    first=[]
    for w,b in [('wm','bm'),('ws','bs')]:
        first.extend(sum(abs(int(v)) for v in arrays[w][:,j])*(1<<(f['input_bits']-1))+abs(int(arrays[b][j])) for j in range(model.hidden))
    second=[sum(abs(int(v)) for v in arrays['wo'][:,j])*(1<<f['hidden_frac'])+abs(int(arrays['bo'][j])) for j in range(10)]
    assert max(first)<2**63-2**40 and max(second)<2**63-2**40
    assert (max(second)+(1<<(f['out_acc_frac']-f['output_frac']-1)))>>(f['out_acc_frac']-f['output_frac']) < 2**31-1
    f.update(first_accumulator_bound=max(first),output_accumulator_bound=max(second))
    return f,arrays

def inputs(x,fmt):
    q=rounded(x,fmt['input_frac']); bound=1<<(fmt['input_bits']-1)
    if q.min() < -bound or q.max() >= bound: raise ValueError('Standardized input outside selected fixed-point range')
    return q

def inference(q,fmt,a):
    def act(v):
        limit=8<<fmt['acc_frac']; pos=np.clip(v,-limit,limit)+limit
        step=fmt['acc_frac']-6; index=np.minimum(pos>>step,1023)
        fraction=pos-(index<<step)
        return a['lut'][index]+shift((a['lut'][index+1]-a['lut'][index])*fraction,step)
    hidden=np.column_stack([act(q[:,:60]@a['wm']+a['bm']),act(q[:,60:]@a['ws']+a['bs'])])
    logits=hidden@a['wo']+a['bo']
    return shift(logits,fmt['out_acc_frac']-fmt['output_frac'])
