"""Export both integer formats, compile C++ and validate raw and outer-fold predictions."""
from pathlib import Path
import argparse,ctypes,hashlib,json,os,shutil,subprocess
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
from fusion_model import DualBranchClassifier
from quantization import FORMATS,quantize,inputs,inference
from train_compare import metrics

ROOT=Path(__file__).resolve().parents[1]

def c_array(name,values,ctype='double'):
    flat=np.asarray(values).ravel()
    values=[format(float(v),'.17g') if ctype=='double' else str(int(v))+('LL' if ctype=='int64_t' else '') for v in flat]
    return f'static const {ctype} {name}[{len(flat)}] = {{\n'+',\n'.join(', '.join(values[i:i+8]) for i in range(0,len(values),8))+'\n};\n'

def parameter_header(fmt,arrays):
    integer_type=f'int{fmt["weight_bits"]}_t'; hidden_type=f'int{fmt["hidden_bits"]}_t'
    text='#pragma once\n#include <stdint.h>\n'
    text+=f'typedef int{fmt["input_bits"]}_t input_t;\ntypedef {hidden_type} hidden_t;\n'
    constants={'BRANCH_H':fmt['hidden'],'INPUT_BITS':fmt['input_bits'],'INPUT_FRAC':fmt['input_frac'],
               'ACC_FRAC':fmt['acc_frac'],'OUT_ACC_FRAC':fmt['out_acc_frac'],'OUTPUT_FRAC':fmt['output_frac']}
    for k,v in constants.items(): text+=f'static const int {k}={v};\n'
    for k,a in arrays.items():
        ctype='int64_t' if k in ['bm','bs','bo'] else hidden_type if k=='lut' else integer_type
        text+=c_array('TANH_LUT' if k=='lut' else 'Q_'+k.upper(),a,ctype)
    return text

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--compiler',default=shutil.which('g++') or 'D:/msys64/ucrt64/bin/g++.exe'); args=parser.parse_args()
    compiler=Path(shutil.which(args.compiler) or args.compiler).resolve()
    if not compiler.is_file(): raise FileNotFoundError('Specify --compiler with a working C++ compiler')
    native=ROOT/'build/native'; native.mkdir(exist_ok=True)
    bundle=joblib.load(ROOT/'models/dual_neural.joblib'); pipe=bundle['pipeline']; scale,model=pipe[0],pipe[-1]
    z=np.load(ROOT/'data/features.npz'); x=z['stable10_stats']; y=z['y']; meta=pd.read_csv(ROOT/'data/events.csv')
    normal=~meta.reverse.to_numpy(bool); xr=scale.transform(x); floating=model.decision_function(xr); float_class=floating.argmax(1)
    weights=dict(zip(['wm','bm','ws','bs','wo','bo'],model.unpack(model.theta_)))
    np.savez_compressed(ROOT/'models/dual_weights.npz',**weights,mean=scale.mean_,scale=scale.scale_)
    text='#pragma once\n'+f'static const int FLOAT_BRANCH_H={model.hidden};\n'
    for name,a in [('FEATURE_MEAN',scale.mean_),('FEATURE_SCALE',scale.scale_)]+[('FLOAT_'+k.upper(),v) for k,v in weights.items()]: text+=c_array(name,a)
    (ROOT/'deploy/float_parameters.h').write_text(text,encoding='utf-8')
    outer=joblib.load(ROOT/'models/dual_outer_folds.joblib'); raw=np.load(ROOT/'data/raw_event_windows.npz')
    dp=ctypes.POINTER(ctypes.c_double); ip=ctypes.POINTER(ctypes.c_int32)
    ptr=lambda a:a.ctypes.data_as(dp); iptr=lambda a:a.ctypes.data_as(ip)
    directory_handle=os.add_dll_directory(str(compiler.parent)) if os.name=='nt' else None
    report={}; quant_predictions=meta[['event_id','class_id','reverse']].copy(); quant_predictions['float_final']=float_class+1
    for name in FORMATS:
        fmt,arrays=quantize(model,name); q=inputs(xr,fmt); expected=inference(q,fmt,arrays); qclass=expected.argmax(1)
        deploy=ROOT/'deploy'/name; sim=ROOT/'sim'/name; deploy.mkdir(exist_ok=True);sim.mkdir(exist_ok=True)
        (deploy/'quant_parameters.h').write_text(parameter_header(fmt,arrays),encoding='utf-8')
        np.savez_compressed(deploy/'parameters.npz',**arrays)
        (deploy/'format.json').write_text(json.dumps(fmt,indent=2),encoding='utf-8')
        # Add deterministic zero/range-boundary vectors to ordinary recorded events.
        maximum=(1<<(fmt['input_bits']-1))-1; minimum=-(1<<(fmt['input_bits']-1))
        boundary=np.array([np.zeros(100),np.full(100,maximum),np.full(100,minimum),np.tile([minimum,maximum],50)],dtype=np.int64)
        test_input=np.vstack([q,boundary]); test_output=inference(test_input,fmt,arrays)
        vectors='#pragma once\n#include <stdint.h>\n'+f'static const int TEST_COUNT={len(test_input)};\n'
        vectors+=c_array('TEST_INPUT',test_input,'int32_t')+c_array('TEST_LOGITS',test_output,'int32_t')+c_array('TEST_CLASS',test_output.argmax(1)+1,'int')
        (sim/'test_vectors.h').write_text(vectors,encoding='utf-8')
        np.savez_compressed(sim/'test_vectors.npz',input_q=test_input.astype(np.int32),logits_q=test_output.astype(np.int32),class_id=test_output.argmax(1)+1)
        dll=native/(name+('.dll' if os.name=='nt' else '.so'))
        command=[str(compiler),'-std=c++11','-O2','-shared','-DFUSION_NATIVE_DLL','-Wno-unknown-pragmas',
                 '-I'+str(ROOT/'deploy'),'-I'+str(deploy),str(ROOT/'deploy/fusion_ps.cpp'),str(ROOT/'deploy/fusion_hls.cpp'),'-o',str(dll)]
        if os.name!='nt': command.insert(1,'-fPIC')
        subprocess.run(command,check=True,capture_output=True,text=True)
        lib=ctypes.CDLL(str(dll))
        lib.fusion_extract.argtypes=[dp,dp,ctypes.c_int,ctypes.c_double,dp];lib.fusion_extract.restype=ctypes.c_int
        lib.fusion_prepare.argtypes=[dp,ip];lib.fusion_prepare.restype=ctypes.c_int
        lib.fusion_float.argtypes=[dp,dp];lib.fusion_float.restype=ctypes.c_int
        lib.fusion_q.argtypes=[ip,ip];lib.fusion_q.restype=ctypes.c_int
        error=0.;float_error=0.;raw_matches=0; host_integer_matches=0
        for i,row in meta.iterrows():
            window=raw[row.event_id]; times=np.ascontiguousarray(window[:,0]); samples=np.ascontiguousarray(window[:,[1,2,3,4,5,6,11,12,13,14]])
            feature=np.zeros(100); assert lib.fusion_extract(ptr(times),ptr(samples),len(times),0.,ptr(feature))==0
            error=max(error,float(np.max(np.abs(feature-x[i])))); assert np.allclose(feature,x[i],atol=1e-10,rtol=1e-10)
            logits=np.zeros(10); assert lib.fusion_float(ptr(feature),ptr(logits))==float_class[i]+1
            float_error=max(float_error,float(np.max(np.abs(logits-floating[i]))))
            qq=np.zeros(100,np.int32); oo=np.zeros(10,np.int32)
            assert lib.fusion_prepare(ptr(feature),iptr(qq))==0
            assert np.array_equal(qq,q[i]),'PS quantized inputs differ'
            assert lib.fusion_q(iptr(qq),iptr(oo))==qclass[i]+1
            assert np.array_equal(oo,expected[i]),'C++ integer arithmetic differs from Python reference'
            raw_matches+=1;host_integer_matches+=1
        for a in boundary:
            qq=a.astype(np.int32); oo=np.zeros(10,np.int32);lib.fusion_q(iptr(qq),iptr(oo))
            assert np.array_equal(oo,inference(a[None,:],fmt,arrays)[0]);host_integer_matches+=1
        # Meaningful failure and invariance checks for public input contracts.
        bad=samples.copy();bad[20,2]=np.nan
        assert lib.fusion_extract(ptr(times),ptr(bad),len(times),0.,ptr(feature))<0
        assert lib.fusion_extract(ptr(times),ptr(samples),10,0.,ptr(feature))<0
        shifted=times+12345.; original=np.zeros(100); moved=np.zeros(100)
        assert lib.fusion_extract(ptr(times),ptr(samples),len(times),0.,ptr(original))==0
        assert lib.fusion_extract(ptr(shifted),ptr(samples),len(times),12345.,ptr(moved))==0
        assert np.allclose(original,moved,atol=1e-10,rtol=1e-10)
        extreme=np.full(100,1e100); assert lib.fusion_prepare(ptr(extreme),iptr(qq))<0
        invalid=np.full(100,np.nan); assert lib.fusion_prepare(ptr(invalid),iptr(qq))<0
        exe=native/('tb_'+name+('.exe' if os.name=='nt' else ''))
        subprocess.run([str(compiler),'-std=c++11','-O2','-Wno-unknown-pragmas','-I'+str(ROOT/'deploy'),'-I'+str(deploy),'-I'+str(sim),
                        str(ROOT/'deploy/fusion_hls.cpp'),str(ROOT/'sim/tb_fusion.cpp'),'-o',str(exe)],check=True,capture_output=True,text=True)
        testbench=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
        fold_rows=[]; held_y=[]; held_float=[]; held_q=[]; max_oof_error=0.;fold_agreement=0
        for held,fold in outer.items():
            pp=fold['pipeline']; idx=fold['test_ids']; xx=pp[0].transform(x[idx]); fm,qa=quantize(pp[-1],name)
            integer=inference(inputs(xx,fm),fm,qa); fp=pp[-1].decision_function(xx); pf=fp.argmax(1); pq=integer.argmax(1)
            diff=float(np.max(np.abs(integer/2.**fm['output_frac']-fp)));max_oof_error=max(max_oof_error,diff)
            fold_rows.append(dict(date=held,candidate=fold['candidate']['id'],float=metrics(y[idx],pf),quantized=metrics(y[idx],pq),
                                  class_agreement=int(np.sum(pf==pq)),max_logit_abs_error=diff))
            held_y.extend(y[idx]);held_float.extend(pf);held_q.extend(pq);fold_agreement+=int(np.sum(pf==pq))
        fmetrics=metrics(np.array(held_y),np.array(held_float)); qmetrics=metrics(np.array(held_y),np.array(held_q))
        report[name]=dict(format=fmt,parameter_count=len(model.theta_),weight_bias_bytes=sum(a.size*(8 if k in ['bm','bs','bo'] else fmt['weight_bits']//8) for k,a in arrays.items() if k!='lut'),
                           tanh_lut_bytes=arrays['lut'].size*fmt['hidden_bits']//8,
                           stored_scaler_float64_bytes=scale.mean_.nbytes+scale.scale_.nbytes,
                           training_final_float=metrics(y[normal],float_class[normal]),training_final_quantized=metrics(y[normal],qclass[normal]),
                           reverse_float=metrics(y[~normal],float_class[~normal]),reverse_quantized=metrics(y[~normal],qclass[~normal]),
                           all410_float_quant_class_agreement=int(np.sum(float_class==qclass)),
                           max_final_logit_error=float(np.max(np.abs(expected/2.**fmt['output_frac']-floating))),
                           nested_outer_float=fmetrics,nested_outer_quantized=qmetrics,outer400_class_agreement=fold_agreement,
                           nested_accuracy_change_percentage_points=100*(qmetrics['accuracy']-fmetrics['accuracy']),
                           outer_folds=fold_rows,max_outer_logit_error=max_oof_error,
                           host_cpp_integer_vectors_matched=host_integer_matches,raw_event_end_to_end_matched=raw_matches,
                           max_cpp_feature_error=error,max_cpp_float_logit_error=float_error,
                           invalid_inputs_rejected=True,time_origin_invariant=True,testbench_stdout=testbench.stdout.strip())
        quant_predictions[name+'_final']=qclass+1
        print(name,json.dumps(report[name],ensure_ascii=False),flush=True)
    quant_predictions.to_csv(ROOT/'report/quantization_predictions.csv',index=False,encoding='utf-8-sig')
    result=dict(model_sha256=hashlib.sha256((ROOT/'models/dual_neural.joblib').read_bytes()).hexdigest(),selected=bundle['candidate'],
                formats=report,deployment_default='q32 (preselected precision-first reference); q16 supplied for resource experiments',
                hardware_status=dict(host_cpp_tested=True,hls_csim=False,hls_synthesis=False,rtl_cosimulation=False,bitstream=False,board=False),
                caveat='Agreement is numerical preservation, not independent recognition accuracy; outer-fold quantization uses fold-specific fitted models.')
    (ROOT/'report/quantization.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    if directory_handle: directory_handle.close()

if __name__=='__main__':
    with threadpool_limits(limits=2):main()
