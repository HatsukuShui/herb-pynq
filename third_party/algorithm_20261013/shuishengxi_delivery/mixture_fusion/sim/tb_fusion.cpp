#include "fusion_api.h"
#include "test_vectors.h"
#include <cstdio>
int main(){
    int failures=0;
    for(int n=0;n<TEST_COUNT;++n){
        int32_t logits[10];int cls=fusion_q(TEST_INPUT+n*100,logits);
        if(cls!=TEST_CLASS[n])++failures;
        for(int k=0;k<10;++k)if(logits[k]!=TEST_LOGITS[n*10+k])++failures;
    }
    std::printf("%d vectors; %d integer mismatches\n",TEST_COUNT,failures);
    return failures?1:0;
}
