#include "fusion_api.h"
#include "float_parameters.h"
#include "quant_parameters.h"
#include <algorithm>
#include <cmath>
#include <vector>

static double median(std::vector<double>& v) {
    std::sort(v.begin(),v.end()); const size_t n=v.size();
    return n%2?v[n/2]:(v[n/2-1]+v[n/2])*.5;
}
static void summarize(const double curve[71][10],int c,double *f) {
    double sum=0,variance=0,early=0,late=0,mid=0,hi=curve[0][c],lo=hi;
    for(int i=0;i<71;++i){double a=curve[i][c];sum+=a;hi=std::max(hi,a);lo=std::min(lo,a);
        if(i>=4&&i<=20)early+=a;if(i>=20&&i<=40)mid+=a;if(i>=50)late+=a;}
    double mean=sum/71.;for(int i=0;i<71;++i){double a=curve[i][c]-mean;variance+=a*a;}
    f[0]=hi;f[1]=lo;f[2]=mean;f[3]=std::sqrt(variance/71.);f[4]=early/17.;f[5]=late/21.;
    f[6]=f[5]-f[4];f[7]=mid/21.;f[8]=(curve[10][c]-curve[2][c])/4.;f[9]=(curve[70][c]-curve[50][c])/10.;
}
int fusion_extract(const double *t,const double *x,int n,double onset,double *f) {
    if(!t||!x||!f||n<2||!std::isfinite(onset))return -1;
    if(onset-8<t[0]||onset+35.25>t[n-1])return -2;
    int previous=-1;
    for(int i=0;i<n;++i){
        if(!std::isfinite(t[i])||(i&&t[i]<=t[i-1]))return -3;
        if(t[i]>=onset-8.25&&t[i]<=onset+35.25){
            if(previous>=0&&t[i]-t[previous]>.8)return -4;previous=i;
            for(int c=0;c<10;++c)if(!std::isfinite(x[i*10+c])||x[i*10+c]<=0)return -5;
        }
    }
    double curve[71][10];
    for(int c=0;c<10;++c){
        std::vector<double> v;
        for(int i=0;i<n;++i)if(t[i]>=onset-8&&t[i]<=onset-3)v.push_back(x[i*10+c]);
        if(v.empty())return -6;double base=median(v);
        for(int k=0;k<71;++k){
            v.clear();double centre=onset+k*.5;
            for(int i=0;i<n;++i)if(t[i]>=centre-.25&&t[i]<centre+.25)v.push_back(x[i*10+c]);
            if(v.empty())return -7;double raw=median(v);
            curve[k][c]=c<6?std::log(raw/base):(raw-base)/base;
        }
        summarize(curve,c,f+c*10);
    }
    return 0;
}
int fusion_prepare(const double *f,int32_t *q) {
    if(!f||!q)return -1;
    const int64_t bound=int64_t(1)<<(INPUT_BITS-1);
    for(int i=0;i<100;++i){
        const double v=(f[i]-FEATURE_MEAN[i])/FEATURE_SCALE[i]*double(int64_t(1)<<INPUT_FRAC);
        if(!std::isfinite(v)||v<=-double(bound)-.5||v>=double(bound)-.5)return -2;
        q[i]=int32_t(std::llround(v));
    }
    return 0;
}
int fusion_float(const double *f,double *out) {
    if(!f||!out)return -1;
    double z[100],h[2*BRANCH_H];
    for(int i=0;i<100;++i){z[i]=(f[i]-FEATURE_MEAN[i])/FEATURE_SCALE[i];if(!std::isfinite(z[i]))return -2;}
    for(int j=0;j<BRANCH_H;++j){
        double a=FLOAT_BM[j],b=FLOAT_BS[j];
        for(int i=0;i<60;++i)a+=z[i]*FLOAT_WM[i*BRANCH_H+j];
        for(int i=0;i<40;++i)b+=z[60+i]*FLOAT_WS[i*BRANCH_H+j];
        h[j]=std::tanh(a);h[BRANCH_H+j]=std::tanh(b);
    }
    int best=0;
    for(int k=0;k<10;++k){double a=FLOAT_BO[k];for(int j=0;j<2*BRANCH_H;++j)a+=h[j]*FLOAT_WO[j*10+k];
        out[k]=a;if(k&&out[k]>out[best])best=k;}
    return best+1;
}
