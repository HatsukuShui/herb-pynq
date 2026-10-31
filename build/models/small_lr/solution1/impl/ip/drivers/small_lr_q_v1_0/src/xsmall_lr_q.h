// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef XSMALL_LR_Q_H
#define XSMALL_LR_Q_H

#ifdef __cplusplus
extern "C" {
#endif

/***************************** Include Files *********************************/
#ifndef __linux__
#include "xil_types.h"
#include "xil_assert.h"
#include "xstatus.h"
#include "xil_io.h"
#else
#include <stdint.h>
#include <assert.h>
#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stddef.h>
#endif
#include "xsmall_lr_q_hw.h"

/**************************** Type Definitions ******************************/
#ifdef __linux__
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
#else
typedef struct {
#ifdef SDT
    char *Name;
#else
    u16 DeviceId;
#endif
    u64 Ctrl_BaseAddress;
} XSmall_lr_q_Config;
#endif

typedef struct {
    u64 Ctrl_BaseAddress;
    u32 IsReady;
} XSmall_lr_q;

typedef u32 word_type;

/***************** Macros (Inline Functions) Definitions *********************/
#ifndef __linux__
#define XSmall_lr_q_WriteReg(BaseAddress, RegOffset, Data) \
    Xil_Out32((BaseAddress) + (RegOffset), (u32)(Data))
#define XSmall_lr_q_ReadReg(BaseAddress, RegOffset) \
    Xil_In32((BaseAddress) + (RegOffset))
#else
#define XSmall_lr_q_WriteReg(BaseAddress, RegOffset, Data) \
    *(volatile u32*)((BaseAddress) + (RegOffset)) = (u32)(Data)
#define XSmall_lr_q_ReadReg(BaseAddress, RegOffset) \
    *(volatile u32*)((BaseAddress) + (RegOffset))

#define Xil_AssertVoid(expr)    assert(expr)
#define Xil_AssertNonvoid(expr) assert(expr)

#define XST_SUCCESS             0
#define XST_DEVICE_NOT_FOUND    2
#define XST_OPEN_DEVICE_FAILED  3
#define XIL_COMPONENT_IS_READY  1
#endif

/************************** Function Prototypes *****************************/
#ifndef __linux__
#ifdef SDT
int XSmall_lr_q_Initialize(XSmall_lr_q *InstancePtr, UINTPTR BaseAddress);
XSmall_lr_q_Config* XSmall_lr_q_LookupConfig(UINTPTR BaseAddress);
#else
int XSmall_lr_q_Initialize(XSmall_lr_q *InstancePtr, u16 DeviceId);
XSmall_lr_q_Config* XSmall_lr_q_LookupConfig(u16 DeviceId);
#endif
int XSmall_lr_q_CfgInitialize(XSmall_lr_q *InstancePtr, XSmall_lr_q_Config *ConfigPtr);
#else
int XSmall_lr_q_Initialize(XSmall_lr_q *InstancePtr, const char* InstanceName);
int XSmall_lr_q_Release(XSmall_lr_q *InstancePtr);
#endif

void XSmall_lr_q_Start(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_IsDone(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_IsIdle(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_IsReady(XSmall_lr_q *InstancePtr);
void XSmall_lr_q_EnableAutoRestart(XSmall_lr_q *InstancePtr);
void XSmall_lr_q_DisableAutoRestart(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Get_return(XSmall_lr_q *InstancePtr);

u32 XSmall_lr_q_Get_logits_q_BaseAddress(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Get_logits_q_HighAddress(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Get_logits_q_TotalBytes(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Get_logits_q_BitWidth(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Get_logits_q_Depth(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Write_logits_q_Words(XSmall_lr_q *InstancePtr, int offset, word_type *data, int length);
u32 XSmall_lr_q_Read_logits_q_Words(XSmall_lr_q *InstancePtr, int offset, word_type *data, int length);
u32 XSmall_lr_q_Write_logits_q_Bytes(XSmall_lr_q *InstancePtr, int offset, char *data, int length);
u32 XSmall_lr_q_Read_logits_q_Bytes(XSmall_lr_q *InstancePtr, int offset, char *data, int length);
u32 XSmall_lr_q_Get_input_q_BaseAddress(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Get_input_q_HighAddress(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Get_input_q_TotalBytes(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Get_input_q_BitWidth(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Get_input_q_Depth(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_Write_input_q_Words(XSmall_lr_q *InstancePtr, int offset, word_type *data, int length);
u32 XSmall_lr_q_Read_input_q_Words(XSmall_lr_q *InstancePtr, int offset, word_type *data, int length);
u32 XSmall_lr_q_Write_input_q_Bytes(XSmall_lr_q *InstancePtr, int offset, char *data, int length);
u32 XSmall_lr_q_Read_input_q_Bytes(XSmall_lr_q *InstancePtr, int offset, char *data, int length);

void XSmall_lr_q_InterruptGlobalEnable(XSmall_lr_q *InstancePtr);
void XSmall_lr_q_InterruptGlobalDisable(XSmall_lr_q *InstancePtr);
void XSmall_lr_q_InterruptEnable(XSmall_lr_q *InstancePtr, u32 Mask);
void XSmall_lr_q_InterruptDisable(XSmall_lr_q *InstancePtr, u32 Mask);
void XSmall_lr_q_InterruptClear(XSmall_lr_q *InstancePtr, u32 Mask);
u32 XSmall_lr_q_InterruptGetEnabled(XSmall_lr_q *InstancePtr);
u32 XSmall_lr_q_InterruptGetStatus(XSmall_lr_q *InstancePtr);

#ifdef __cplusplus
}
#endif

#endif
