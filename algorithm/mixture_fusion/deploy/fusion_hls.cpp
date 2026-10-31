#include "fusion_api.h"
#include "quant_parameters.h"

static int64_t rounded_shift(int64_t v,int bits) {
    const int64_t half=int64_t(1)<<(bits-1);
    return v>=0?(v+half)>>bits:-(((-v)+half)>>bits);
}
static hidden_t tanh_fixed(int64_t value) {
    const int64_t limit=int64_t(8)<<ACC_FRAC;
    if(value<=-limit)return TANH_LUT[0];if(value>=limit)return TANH_LUT[1024];
    const int step=ACC_FRAC-6;
    int64_t u=value+limit;int index=int(u>>step);int64_t remainder=u-(int64_t(index)<<step);
    int64_t delta=int64_t(TANH_LUT[index+1])-TANH_LUT[index];
    return hidden_t(TANH_LUT[index]+rounded_shift(delta*remainder,step));
}
int fusion_q(const int32_t input_q[100],int32_t logits_q[10]) {
#pragma HLS INTERFACE s_axilite port=input_q bundle=CTRL
#pragma HLS INTERFACE s_axilite port=logits_q bundle=CTRL
#pragma HLS INTERFACE s_axilite port=return bundle=CTRL
    hidden_t h[2*BRANCH_H];
    mos_branch: for(int j=0;j<BRANCH_H;++j){
        int64_t sum=Q_BM[j];
        mos_mac: for(int i=0;i<60;++i){
#pragma HLS PIPELINE II=1
            sum+=int64_t(input_t(input_q[i]))*Q_WM[i*BRANCH_H+j];
        }
        h[j]=tanh_fixed(sum);
    }
    sgp_branch: for(int j=0;j<BRANCH_H;++j){
        int64_t sum=Q_BS[j];
        sgp_mac: for(int i=0;i<40;++i){
#pragma HLS PIPELINE II=1
            sum+=int64_t(input_t(input_q[60+i]))*Q_WS[i*BRANCH_H+j];
        }
        h[BRANCH_H+j]=tanh_fixed(sum);
    }
    int best=0;
    output_loop: for(int k=0;k<10;++k){
        int64_t sum=Q_BO[k];
        output_mac: for(int j=0;j<2*BRANCH_H;++j){
#pragma HLS PIPELINE II=1
            sum+=int64_t(h[j])*Q_WO[j*10+k];
        }
        logits_q[k]=int32_t(rounded_shift(sum,OUT_ACC_FRAC-OUTPUT_FRAC));
        if(k&&logits_q[k]>logits_q[best])best=k;
    }
    return best+1;
}
