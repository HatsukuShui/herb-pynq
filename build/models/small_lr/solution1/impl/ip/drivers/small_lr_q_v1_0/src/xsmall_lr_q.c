// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
/***************************** Include Files *********************************/
#include "xsmall_lr_q.h"

/************************** Function Implementation *************************/
#ifndef __linux__
int XSmall_lr_q_CfgInitialize(XSmall_lr_q *InstancePtr, XSmall_lr_q_Config *ConfigPtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(ConfigPtr != NULL);

    InstancePtr->Ctrl_BaseAddress = ConfigPtr->Ctrl_BaseAddress;
    InstancePtr->IsReady = XIL_COMPONENT_IS_READY;

    return XST_SUCCESS;
}
#endif

void XSmall_lr_q_Start(XSmall_lr_q *InstancePtr) {
    u32 Data;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSmall_lr_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_AP_CTRL) & 0x80;
    XSmall_lr_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_AP_CTRL, Data | 0x01);
}

u32 XSmall_lr_q_IsDone(XSmall_lr_q *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSmall_lr_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_AP_CTRL);
    return (Data >> 1) & 0x1;
}

u32 XSmall_lr_q_IsIdle(XSmall_lr_q *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSmall_lr_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_AP_CTRL);
    return (Data >> 2) & 0x1;
}

u32 XSmall_lr_q_IsReady(XSmall_lr_q *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSmall_lr_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_AP_CTRL);
    // check ap_start to see if the pcore is ready for next input
    return !(Data & 0x1);
}

void XSmall_lr_q_EnableAutoRestart(XSmall_lr_q *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSmall_lr_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_AP_CTRL, 0x80);
}

void XSmall_lr_q_DisableAutoRestart(XSmall_lr_q *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSmall_lr_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_AP_CTRL, 0);
}

u32 XSmall_lr_q_Get_return(XSmall_lr_q *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XSmall_lr_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_AP_RETURN);
    return Data;
}
u32 XSmall_lr_q_Get_logits_q_BaseAddress(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE);
}

u32 XSmall_lr_q_Get_logits_q_HighAddress(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_HIGH);
}

u32 XSmall_lr_q_Get_logits_q_TotalBytes(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_HIGH - XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE + 1);
}

u32 XSmall_lr_q_Get_logits_q_BitWidth(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XSMALL_LR_Q_CTRL_WIDTH_LOGITS_Q;
}

u32 XSmall_lr_q_Get_logits_q_Depth(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XSMALL_LR_Q_CTRL_DEPTH_LOGITS_Q;
}

u32 XSmall_lr_q_Write_logits_q_Words(XSmall_lr_q *InstancePtr, int offset, word_type *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length)*4 > (XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_HIGH - XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(int *)(InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE + (offset + i)*4) = *(data + i);
    }
    return length;
}

u32 XSmall_lr_q_Read_logits_q_Words(XSmall_lr_q *InstancePtr, int offset, word_type *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length)*4 > (XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_HIGH - XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(data + i) = *(int *)(InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE + (offset + i)*4);
    }
    return length;
}

u32 XSmall_lr_q_Write_logits_q_Bytes(XSmall_lr_q *InstancePtr, int offset, char *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length) > (XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_HIGH - XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(char *)(InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE + offset + i) = *(data + i);
    }
    return length;
}

u32 XSmall_lr_q_Read_logits_q_Bytes(XSmall_lr_q *InstancePtr, int offset, char *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length) > (XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_HIGH - XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(data + i) = *(char *)(InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE + offset + i);
    }
    return length;
}

u32 XSmall_lr_q_Get_input_q_BaseAddress(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE);
}

u32 XSmall_lr_q_Get_input_q_HighAddress(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_HIGH);
}

u32 XSmall_lr_q_Get_input_q_TotalBytes(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_HIGH - XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE + 1);
}

u32 XSmall_lr_q_Get_input_q_BitWidth(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XSMALL_LR_Q_CTRL_WIDTH_INPUT_Q;
}

u32 XSmall_lr_q_Get_input_q_Depth(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XSMALL_LR_Q_CTRL_DEPTH_INPUT_Q;
}

u32 XSmall_lr_q_Write_input_q_Words(XSmall_lr_q *InstancePtr, int offset, word_type *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length)*4 > (XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_HIGH - XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(int *)(InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE + (offset + i)*4) = *(data + i);
    }
    return length;
}

u32 XSmall_lr_q_Read_input_q_Words(XSmall_lr_q *InstancePtr, int offset, word_type *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length)*4 > (XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_HIGH - XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(data + i) = *(int *)(InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE + (offset + i)*4);
    }
    return length;
}

u32 XSmall_lr_q_Write_input_q_Bytes(XSmall_lr_q *InstancePtr, int offset, char *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length) > (XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_HIGH - XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(char *)(InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE + offset + i) = *(data + i);
    }
    return length;
}

u32 XSmall_lr_q_Read_input_q_Bytes(XSmall_lr_q *InstancePtr, int offset, char *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length) > (XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_HIGH - XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(data + i) = *(char *)(InstancePtr->Ctrl_BaseAddress + XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE + offset + i);
    }
    return length;
}

void XSmall_lr_q_InterruptGlobalEnable(XSmall_lr_q *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSmall_lr_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_GIE, 1);
}

void XSmall_lr_q_InterruptGlobalDisable(XSmall_lr_q *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSmall_lr_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_GIE, 0);
}

void XSmall_lr_q_InterruptEnable(XSmall_lr_q *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XSmall_lr_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_IER);
    XSmall_lr_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_IER, Register | Mask);
}

void XSmall_lr_q_InterruptDisable(XSmall_lr_q *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XSmall_lr_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_IER);
    XSmall_lr_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_IER, Register & (~Mask));
}

void XSmall_lr_q_InterruptClear(XSmall_lr_q *InstancePtr, u32 Mask) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XSmall_lr_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_ISR, Mask);
}

u32 XSmall_lr_q_InterruptGetEnabled(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XSmall_lr_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_IER);
}

u32 XSmall_lr_q_InterruptGetStatus(XSmall_lr_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XSmall_lr_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XSMALL_LR_Q_CTRL_ADDR_ISR);
}

