#include "small_api.h"
#include "test_vectors.h"
#include <cstdio>

int main() {
    int errors=0;
    for (int n=0; n<TEST_COUNT; ++n) {
        int32_t lr[8]={0}, mlp[8]={0};
#ifndef SMALL_HLS_MLP
        int a=small_lr_q(TEST_INPUT+n*50,lr);
#endif
#ifndef SMALL_HLS_LR
        int b=small_mlp_q(TEST_INPUT+n*50,mlp);
#endif
        for (int k=0; k<8; ++k) {
#ifndef SMALL_HLS_MLP
            if (a<0 || lr[k]!=TEST_LR[n*8+k]) ++errors;
#endif
#ifndef SMALL_HLS_LR
            if (b<0 || mlp[k]!=TEST_MLP[n*8+k]) ++errors;
#endif
        }
    }
    int32_t invalid[50]={0}, result[8];
    invalid[0]=32768;
#ifndef SMALL_HLS_MLP
    if (small_lr_q(invalid,result)!=-3) ++errors;
#endif
#ifndef SMALL_HLS_LR
    if (small_mlp_q(invalid,result)!=-3) ++errors;
#endif
    invalid[0]=-32769;
#ifndef SMALL_HLS_MLP
    if (small_lr_q(invalid,result)!=-3) ++errors;
#endif
#ifndef SMALL_HLS_LR
    if (small_mlp_q(invalid,result)!=-3) ++errors;
#endif
    std::printf("vectors=%d, integer_mismatches=%d\n",TEST_COUNT,errors);
    return errors ? 1 : 0;
}
