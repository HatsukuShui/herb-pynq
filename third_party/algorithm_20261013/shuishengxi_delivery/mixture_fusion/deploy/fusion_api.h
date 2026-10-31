#pragma once
#include <stdint.h>
#if defined(_WIN32) && defined(FUSION_NATIVE_DLL)
#define FUSION_API __declspec(dllexport)
#else
#define FUSION_API
#endif
#ifdef __cplusplus
extern "C" {
#endif
// Raw row order: MOS1..MOS6, SGP5..SGP8. Times and onset use the same seconds origin.
FUSION_API int fusion_extract(const double *time_s,const double *raw10,int n,double onset_s,double features[100]);
// Return 0 on success. Nonfinite or out-of-range inputs return a negative error.
FUSION_API int fusion_prepare(const double features[100],int32_t input_q[100]);
// Floating reference and PL integer kernel return class IDs 1..10.
FUSION_API int fusion_float(const double features[100],double logits[10]);
FUSION_API int fusion_q(const int32_t input_q[100],int32_t logits_q[10]);
#ifdef __cplusplus
}
#endif
