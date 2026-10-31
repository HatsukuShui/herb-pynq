#include "small_api.h"
#include "small_parameters.h"

static int64_t rounded_shift(int64_t value, int bits) {
    const int64_t half=int64_t(1)<<(bits-1);
    return value>=0 ? (value+half)>>bits : -(((-value)+half)>>bits);
}

int small_lr_q(const int32_t input_q[50], int32_t logits_q[8]) {
#pragma HLS INTERFACE s_axilite port=input_q bundle=CTRL
#pragma HLS INTERFACE s_axilite port=logits_q bundle=CTRL
#pragma HLS INTERFACE s_axilite port=return bundle=CTRL
    for (int i=0; i<50; ++i) if (input_q[i] < -32768 || input_q[i] > 32767) return -3;
    int best=0;
    for (int k=0; k<8; ++k) {
        int64_t sum=Q_LR_B[k];
        for (int i=0; i<50; ++i) {
#pragma HLS PIPELINE II=1
            sum += int64_t(int16_t(input_q[i])) * Q_LR_W[i*8+k];
        }
        logits_q[k]=int32_t(rounded_shift(sum,10));
        if (k && logits_q[k]>logits_q[best]) best=k;
    }
    return best;
}

int small_mlp_q(const int32_t input_q[50], int32_t logits_q[8]) {
#pragma HLS INTERFACE s_axilite port=input_q bundle=CTRL
#pragma HLS INTERFACE s_axilite port=logits_q bundle=CTRL
#pragma HLS INTERFACE s_axilite port=return bundle=CTRL
    for (int i=0; i<50; ++i) if (input_q[i] < -32768 || input_q[i] > 32767) return -3;
    int16_t hidden[32];
    for (int j=0; j<32; ++j) {
        int64_t sum=Q_MLP_B1[j];
        for (int i=0; i<50; ++i) {
#pragma HLS PIPELINE II=1
            sum += int64_t(int16_t(input_q[i])) * Q_MLP_W1[i*32+j];
        }
        const int64_t value=rounded_shift(sum,12);
        hidden[j]=int16_t(value<0 ? 0 : (value>32767 ? 32767 : value));
    }
    int best=0;
    for (int k=0; k<8; ++k) {
        int64_t sum=Q_MLP_B2[k];
        for (int j=0; j<32; ++j) {
#pragma HLS PIPELINE II=1
            sum += int64_t(hidden[j])*Q_MLP_W2[j*8+k];
        }
        logits_q[k]=int32_t(rounded_shift(sum,10));
        if (k && logits_q[k]>logits_q[best]) best=k;
    }
    return best;
}
