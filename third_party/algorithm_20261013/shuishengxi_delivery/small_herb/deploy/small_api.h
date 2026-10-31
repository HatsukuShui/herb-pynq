#pragma once
#include <stdint.h>
#if defined(_WIN32) && defined(SMALL_NATIVE_DLL)
#define SMALL_API __declspec(dllexport)
#else
#define SMALL_API
#endif
#ifdef __cplusplus
extern "C" {
#endif
// Exactly 10x5 baseline and 20x5 response, row-major. Returns 0 or negative error.
SMALL_API int small_extract(const double baseline[50], const double response[100], double feature[50]);
SMALL_API int small_prepare(const double feature[50], int32_t input_q[50]);
// model_id: 0=logistic, 1=MLP. Class IDs are 0..7; errors are negative.
SMALL_API int small_float(const double feature[50], int model_id, double logits[8]);
SMALL_API int small_lr_q(const int32_t input_q[50], int32_t logits_q[8]);
SMALL_API int small_mlp_q(const int32_t input_q[50], int32_t logits_q[8]);
#ifdef __cplusplus
}
#endif
