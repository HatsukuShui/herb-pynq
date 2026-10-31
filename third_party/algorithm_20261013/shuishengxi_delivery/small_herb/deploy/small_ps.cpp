#include "small_api.h"
#include "small_parameters.h"
#include <algorithm>
#include <cmath>

int small_extract(const double baseline[50], const double response[100], double f[50]) {
    if (!baseline || !response || !f) return -1;
    double r[20][5], peak[5], share = 1e-6;
    for (int i=0; i<50; ++i) if (!std::isfinite(baseline[i])) return -2;
    for (int i=0; i<100; ++i) if (!std::isfinite(response[i])) return -2;
    for (int c=0; c<5; ++c) {
        double base[10];
        for (int t=0; t<10; ++t) base[t] = baseline[t*5+c];
        std::sort(base, base+10);
        const double b = (base[4] + base[5]) / 2.0;
        if (!(b>0)) return -3;
        double mean=0, slope=0, delta=0;
        peak[c] = -INFINITY;
        for (int t=0; t<20; ++t) {
            r[t][c] = (response[t*5+c]-b)/b;
            mean += r[t][c]/20.0;
            slope += (t-9.5)*r[t][c]/665.0;
            peak[c] = std::max(peak[c], r[t][c]);
            if (t) delta += std::abs(r[t][c]-r[t-1][c])/19.0;
        }
        for (int block=0; block<4; ++block) {
            double value=0;
            for (int t=0; t<5; ++t) value += r[block*5+t][c]/5.0;
            f[block*5+c] = value;
        }
        double var=0;
        for (int t=0; t<20; ++t) var += (r[t][c]-mean)*(r[t][c]-mean)/20.0;
        f[20+c]=peak[c]; f[25+c]=mean; f[30+c]=slope;
        f[35+c]=std::sqrt(var); f[40+c]=delta;
        share += std::abs(peak[c]);
    }
    for (int c=0; c<5; ++c) f[45+c]=peak[c]/share;
    for (int i=0; i<50; ++i) if (!std::isfinite(f[i])) return -4;
    return 0;
}

int small_prepare(const double feature[50], int32_t input_q[50]) {
    if (!feature || !input_q) return -1;
    for (int i=0; i<50; ++i) {
        double q=(feature[i]-FEATURE_MEAN[i])/FEATURE_SCALE[i]*1024.0;
        if (!std::isfinite(q)) return -2;
        q=std::round(q);
        if (q < -32768 || q > 32767) return -3;
        input_q[i]=int32_t(q);
    }
    return 0;
}

int small_float(const double feature[50], int model_id, double logits[8]) {
    if (!feature || !logits || (model_id!=0 && model_id!=1)) return -1;
    double x[50], hidden[32];
    for (int i=0; i<50; ++i) {
        x[i]=(feature[i]-FEATURE_MEAN[i])/FEATURE_SCALE[i];
        if (!std::isfinite(x[i])) return -2;
    }
    if (model_id==1) {
        for (int j=0; j<32; ++j) {
            double sum=MLP_B1[j];
            for (int i=0; i<50; ++i) sum += x[i]*MLP_W1[i*32+j];
            hidden[j]=std::max(0.0,sum);
        }
    }
    int best=0;
    for (int k=0; k<8; ++k) {
        double sum=model_id==0 ? LR_B[k] : MLP_B2[k];
        if (model_id==0) for (int i=0; i<50; ++i) sum += x[i]*LR_W[i*8+k];
        else for (int j=0; j<32; ++j) sum += hidden[j]*MLP_W2[j*8+k];
        if (!std::isfinite(sum)) return -2;
        logits[k]=sum;
        if (k && sum>logits[best]) best=k;
    }
    return best;
}
