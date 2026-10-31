// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef XFUSION_Q_H
#define XFUSION_Q_H

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
#include "xfusion_q_hw.h"

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
} XFusion_q_Config;
#endif

typedef struct {
    u64 Ctrl_BaseAddress;
    u32 IsReady;
} XFusion_q;

typedef u32 word_type;

/***************** Macros (Inline Functions) Definitions *********************/
#ifndef __linux__
#define XFusion_q_WriteReg(BaseAddress, RegOffset, Data) \
    Xil_Out32((BaseAddress) + (RegOffset), (u32)(Data))
#define XFusion_q_ReadReg(BaseAddress, RegOffset) \
    Xil_In32((BaseAddress) + (RegOffset))
#else
#define XFusion_q_WriteReg(BaseAddress, RegOffset, Data) \
    *(volatile u32*)((BaseAddress) + (RegOffset)) = (u32)(Data)
#define XFusion_q_ReadReg(BaseAddress, RegOffset) \
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
int XFusion_q_Initialize(XFusion_q *InstancePtr, UINTPTR BaseAddress);
XFusion_q_Config* XFusion_q_LookupConfig(UINTPTR BaseAddress);
#else
int XFusion_q_Initialize(XFusion_q *InstancePtr, u16 DeviceId);
XFusion_q_Config* XFusion_q_LookupConfig(u16 DeviceId);
#endif
int XFusion_q_CfgInitialize(XFusion_q *InstancePtr, XFusion_q_Config *ConfigPtr);
#else
int XFusion_q_Initialize(XFusion_q *InstancePtr, const char* InstanceName);
int XFusion_q_Release(XFusion_q *InstancePtr);
#endif

void XFusion_q_Start(XFusion_q *InstancePtr);
u32 XFusion_q_IsDone(XFusion_q *InstancePtr);
u32 XFusion_q_IsIdle(XFusion_q *InstancePtr);
u32 XFusion_q_IsReady(XFusion_q *InstancePtr);
void XFusion_q_EnableAutoRestart(XFusion_q *InstancePtr);
void XFusion_q_DisableAutoRestart(XFusion_q *InstancePtr);
u32 XFusion_q_Get_return(XFusion_q *InstancePtr);

u32 XFusion_q_Get_logits_q_BaseAddress(XFusion_q *InstancePtr);
u32 XFusion_q_Get_logits_q_HighAddress(XFusion_q *InstancePtr);
u32 XFusion_q_Get_logits_q_TotalBytes(XFusion_q *InstancePtr);
u32 XFusion_q_Get_logits_q_BitWidth(XFusion_q *InstancePtr);
u32 XFusion_q_Get_logits_q_Depth(XFusion_q *InstancePtr);
u32 XFusion_q_Write_logits_q_Words(XFusion_q *InstancePtr, int offset, word_type *data, int length);
u32 XFusion_q_Read_logits_q_Words(XFusion_q *InstancePtr, int offset, word_type *data, int length);
u32 XFusion_q_Write_logits_q_Bytes(XFusion_q *InstancePtr, int offset, char *data, int length);
u32 XFusion_q_Read_logits_q_Bytes(XFusion_q *InstancePtr, int offset, char *data, int length);
u32 XFusion_q_Get_input_q_BaseAddress(XFusion_q *InstancePtr);
u32 XFusion_q_Get_input_q_HighAddress(XFusion_q *InstancePtr);
u32 XFusion_q_Get_input_q_TotalBytes(XFusion_q *InstancePtr);
u32 XFusion_q_Get_input_q_BitWidth(XFusion_q *InstancePtr);
u32 XFusion_q_Get_input_q_Depth(XFusion_q *InstancePtr);
u32 XFusion_q_Write_input_q_Words(XFusion_q *InstancePtr, int offset, word_type *data, int length);
u32 XFusion_q_Read_input_q_Words(XFusion_q *InstancePtr, int offset, word_type *data, int length);
u32 XFusion_q_Write_input_q_Bytes(XFusion_q *InstancePtr, int offset, char *data, int length);
u32 XFusion_q_Read_input_q_Bytes(XFusion_q *InstancePtr, int offset, char *data, int length);

void XFusion_q_InterruptGlobalEnable(XFusion_q *InstancePtr);
void XFusion_q_InterruptGlobalDisable(XFusion_q *InstancePtr);
void XFusion_q_InterruptEnable(XFusion_q *InstancePtr, u32 Mask);
void XFusion_q_InterruptDisable(XFusion_q *InstancePtr, u32 Mask);
void XFusion_q_InterruptClear(XFusion_q *InstancePtr, u32 Mask);
u32 XFusion_q_InterruptGetEnabled(XFusion_q *InstancePtr);
u32 XFusion_q_InterruptGetStatus(XFusion_q *InstancePtr);

#ifdef __cplusplus
}
#endif

#endif
