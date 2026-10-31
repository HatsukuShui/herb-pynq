"""New per-event features. No event index, absolute time, file or day is an input."""
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

LABELS=['当归+甘草','当归+川芎','当归+肉桂','当归+熟地黄','甘草+川芎',
        '甘草+肉桂','甘草+熟地黄','川芎+肉桂','川芎+熟地黄','肉桂+熟地黄']
MOS=[f'MOS{i}(k)' for i in range(1,7)]
SGP=[f'SGP{i}' for i in range(1,9)]
CHANNELS=MOS+SGP
STABLE=np.array([0,1,2,3,4,5,10,11,12,13])
GRID=np.arange(0,35.001,.5)

def elapsed(df):
    return (pd.to_datetime(df.TIME)-pd.to_datetime(df.TIME.iloc[0])).dt.total_seconds().to_numpy()

def locate(df,prominence=.08):
    """Offline MOS locator, allowed to return any count (never force ten peaks)."""
    t=elapsed(df); grid=np.arange(0,t[-1],.5)
    x=np.log(df[MOS].to_numpy(float)); q=np.quantile(x,[.1,.9],axis=0)
    z=(x-q[0])/np.maximum(q[1]-q[0],1e-6)
    fusion=np.median(np.column_stack([np.interp(grid,t,z[:,i]) for i in range(6)]),axis=1)
    smooth=gaussian_filter1d(fusion,2)
    ix,props=find_peaks(smooth,distance=60,prominence=prominence)
    events=[]
    for i,p in enumerate(ix):
        left=max(0,p-60,ix[i-1]+12 if i else 0)
        valley=left+np.argmin(smooth[left:p+1])
        threshold=smooth[valley]+.1*(smooth[p]-smooth[valley])
        on=valley+np.flatnonzero(smooth[valley:p+1]>=threshold)[0]
        events.append(dict(peak=float(grid[p]),onset=float(grid[on]),prominence=float(props['prominences'][i])))
    return events

def bin_median(t,x,centres):
    rows=[]
    for c in centres:
        m=(t>=c-.25)&(t<c+.25)
        if not m.any():
            raise ValueError(f'No samples around t={c:.3f}')
        rows.append(np.median(x[m],axis=0))
    return np.array(rows)

def describe(curve):
    """Channel-major, ten summaries with fixed times relative to onset."""
    early=curve[(GRID>=2)&(GRID<=10)].mean(axis=0)
    late=curve[(GRID>=25)&(GRID<=35)].mean(axis=0)
    return np.stack([curve.max(0),curve.min(0),curve.mean(0),curve.std(0),
                     early,late,late-early,
                     curve[(GRID>=10)&(GRID<=20)].mean(0),
                     (curve[10]-curve[2])/4,
                     (curve[-1]-curve[-21])/10],axis=1)

def shape_summary(curve):
    """Eight short time blocks per channel, no PCA or cross-event normalization."""
    edges=np.linspace(0,len(curve),9).astype(int)
    return np.stack([curve[a:b].mean(0) for a,b in zip(edges[:-1],edges[1:])],axis=1)

def extract_event(df,onset):
    t=elapsed(df);x=df[CHANNELS].to_numpy(float)
    if onset-8<t[0] or onset+35.25>t[-1]:raise ValueError('Incomplete baseline/response window')
    local=(t>=onset-8.25)&(t<=onset+35.25)
    if np.max(np.diff(t[local]))>.8:raise ValueError('Sampling gap exceeds 0.8 s within event')
    if not np.isfinite(x[local]).all() or (x[local]<=0).any():raise ValueError('Invalid sensor value')
    baseline_mask=(t>=onset-8)&(t<=onset-3)
    baseline=np.median(x[baseline_mask],axis=0)
    raw=bin_median(t,x,onset+GRID)
    rel=(raw-baseline)/baseline
    rel[:,:6]=np.log(raw[:,:6]/baseline[:6])
    delta=rel.copy();delta[:,6:]=(raw[:,6:]-baseline[6:])/1000.
    # Remove steps at heater switches from one exploratory representation.
    # It is only an approximation: sensor settling may persist after 1.2 s.
    heat=df.Heat_Temp1.to_numpy();changes=np.r_[True,heat[1:]!=heat[:-1]]
    last_change=np.maximum.accumulate(np.where(changes,np.arange(len(t)),0))
    good=(t-t[last_change]>=1.2)&np.r_[False,heat[1:]==heat[:-1]]&np.r_[False,np.diff(t)<.8]
    dx=np.diff(x[:,6:10],axis=0,prepend=x[:1,6:10]);dx[~good]=0
    accumulated=np.cumsum(dx,axis=0)
    hc=bin_median(t,accumulated,onset+GRID)-np.median(accumulated[baseline_mask],axis=0)
    corrected=rel.copy();corrected[:,6:10]=hc/baseline[6:10]
    stats=describe(rel);fixed=describe(delta[:,10:])
    stable=rel[:,STABLE]
    # Per-event group normalization retains ratios between sensor channels.
    norm=stable.copy()
    for sl in [slice(0,6),slice(6,10)]:
        scale=max(float(np.sqrt(np.mean(stable[:,sl]**2))),1e-5)
        norm[:,sl]/=scale
    fixednorm=delta[:,10:]/max(float(np.sqrt(np.mean(delta[:,10:]**2))),.01)
    features={
        'sgp8_stats':stats[6:].ravel(),
        'sgp4_fixed_stats':stats[10:].ravel(),
        'sgp4_fixed_delta':fixed.ravel(),
        'mos6_stats':stats[:6].ravel(),
        'stable10_stats':stats[STABLE].ravel(),
        'all14_stats':stats.ravel(),
        'heater_corrected14':describe(corrected).ravel(),
        'stable10_signature':np.r_[describe(norm).ravel(),stats[STABLE].ravel()],
        'sgp4_signature':np.r_[describe(fixednorm).ravel(),fixed.ravel()],
        'stable10_temporal':shape_summary(stable).ravel(),
        'sgp8_temporal':shape_summary(rel[:,6:]).ravel(),
        'corrected14_temporal':shape_summary(corrected).ravel(),
    }
    assert all(np.isfinite(v).all() for v in features.values())
    return features,rel
