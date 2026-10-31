// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
/***************************** Include Files *********************************/
#include "xfusion_q.h"

/************************** Function Implementation *************************/
#ifndef __linux__
int XFusion_q_CfgInitialize(XFusion_q *InstancePtr, XFusion_q_Config *ConfigPtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(ConfigPtr != NULL);

    InstancePtr->Ctrl_BaseAddress = ConfigPtr->Ctrl_BaseAddress;
    InstancePtr->IsReady = XIL_COMPONENT_IS_READY;

    return XST_SUCCESS;
}
#endif

void XFusion_q_Start(XFusion_q *InstancePtr) {
    u32 Data;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XFusion_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_AP_CTRL) & 0x80;
    XFusion_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_AP_CTRL, Data | 0x01);
}

u32 XFusion_q_IsDone(XFusion_q *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XFusion_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_AP_CTRL);
    return (Data >> 1) & 0x1;
}

u32 XFusion_q_IsIdle(XFusion_q *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XFusion_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_AP_CTRL);
    return (Data >> 2) & 0x1;
}

u32 XFusion_q_IsReady(XFusion_q *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XFusion_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_AP_CTRL);
    // check ap_start to see if the pcore is ready for next input
    return !(Data & 0x1);
}

void XFusion_q_EnableAutoRestart(XFusion_q *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XFusion_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_AP_CTRL, 0x80);
}

void XFusion_q_DisableAutoRestart(XFusion_q *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XFusion_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_AP_CTRL, 0);
}

u32 XFusion_q_Get_return(XFusion_q *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XFusion_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_AP_RETURN);
    return Data;
}
u32 XFusion_q_Get_logits_q_BaseAddress(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_LOGITS_Q_BASE);
}

u32 XFusion_q_Get_logits_q_HighAddress(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_LOGITS_Q_HIGH);
}

u32 XFusion_q_Get_logits_q_TotalBytes(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (XFUSION_Q_CTRL_ADDR_LOGITS_Q_HIGH - XFUSION_Q_CTRL_ADDR_LOGITS_Q_BASE + 1);
}

u32 XFusion_q_Get_logits_q_BitWidth(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XFUSION_Q_CTRL_WIDTH_LOGITS_Q;
}

u32 XFusion_q_Get_logits_q_Depth(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XFUSION_Q_CTRL_DEPTH_LOGITS_Q;
}

u32 XFusion_q_Write_logits_q_Words(XFusion_q *InstancePtr, int offset, word_type *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length)*4 > (XFUSION_Q_CTRL_ADDR_LOGITS_Q_HIGH - XFUSION_Q_CTRL_ADDR_LOGITS_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(int *)(InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_LOGITS_Q_BASE + (offset + i)*4) = *(data + i);
    }
    return length;
}

u32 XFusion_q_Read_logits_q_Words(XFusion_q *InstancePtr, int offset, word_type *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length)*4 > (XFUSION_Q_CTRL_ADDR_LOGITS_Q_HIGH - XFUSION_Q_CTRL_ADDR_LOGITS_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(data + i) = *(int *)(InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_LOGITS_Q_BASE + (offset + i)*4);
    }
    return length;
}

u32 XFusion_q_Write_logits_q_Bytes(XFusion_q *InstancePtr, int offset, char *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length) > (XFUSION_Q_CTRL_ADDR_LOGITS_Q_HIGH - XFUSION_Q_CTRL_ADDR_LOGITS_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(char *)(InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_LOGITS_Q_BASE + offset + i) = *(data + i);
    }
    return length;
}

u32 XFusion_q_Read_logits_q_Bytes(XFusion_q *InstancePtr, int offset, char *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length) > (XFUSION_Q_CTRL_ADDR_LOGITS_Q_HIGH - XFUSION_Q_CTRL_ADDR_LOGITS_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(data + i) = *(char *)(InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_LOGITS_Q_BASE + offset + i);
    }
    return length;
}

u32 XFusion_q_Get_input_q_BaseAddress(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_INPUT_Q_BASE);
}

u32 XFusion_q_Get_input_q_HighAddress(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_INPUT_Q_HIGH);
}

u32 XFusion_q_Get_input_q_TotalBytes(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (XFUSION_Q_CTRL_ADDR_INPUT_Q_HIGH - XFUSION_Q_CTRL_ADDR_INPUT_Q_BASE + 1);
}

u32 XFusion_q_Get_input_q_BitWidth(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XFUSION_Q_CTRL_WIDTH_INPUT_Q;
}

u32 XFusion_q_Get_input_q_Depth(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XFUSION_Q_CTRL_DEPTH_INPUT_Q;
}

u32 XFusion_q_Write_input_q_Words(XFusion_q *InstancePtr, int offset, word_type *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length)*4 > (XFUSION_Q_CTRL_ADDR_INPUT_Q_HIGH - XFUSION_Q_CTRL_ADDR_INPUT_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(int *)(InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_INPUT_Q_BASE + (offset + i)*4) = *(data + i);
    }
    return length;
}

u32 XFusion_q_Read_input_q_Words(XFusion_q *InstancePtr, int offset, word_type *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length)*4 > (XFUSION_Q_CTRL_ADDR_INPUT_Q_HIGH - XFUSION_Q_CTRL_ADDR_INPUT_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(data + i) = *(int *)(InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_INPUT_Q_BASE + (offset + i)*4);
    }
    return length;
}

u32 XFusion_q_Write_input_q_Bytes(XFusion_q *InstancePtr, int offset, char *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length) > (XFUSION_Q_CTRL_ADDR_INPUT_Q_HIGH - XFUSION_Q_CTRL_ADDR_INPUT_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(char *)(InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_INPUT_Q_BASE + offset + i) = *(data + i);
    }
    return length;
}

u32 XFusion_q_Read_input_q_Bytes(XFusion_q *InstancePtr, int offset, char *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length) > (XFUSION_Q_CTRL_ADDR_INPUT_Q_HIGH - XFUSION_Q_CTRL_ADDR_INPUT_Q_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(data + i) = *(char *)(InstancePtr->Ctrl_BaseAddress + XFUSION_Q_CTRL_ADDR_INPUT_Q_BASE + offset + i);
    }
    return length;
}

void XFusion_q_InterruptGlobalEnable(XFusion_q *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XFusion_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_GIE, 1);
}

void XFusion_q_InterruptGlobalDisable(XFusion_q *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XFusion_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_GIE, 0);
}

void XFusion_q_InterruptEnable(XFusion_q *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XFusion_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_IER);
    XFusion_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_IER, Register | Mask);
}

void XFusion_q_InterruptDisable(XFusion_q *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XFusion_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_IER);
    XFusion_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_IER, Register & (~Mask));
}

void XFusion_q_InterruptClear(XFusion_q *InstancePtr, u32 Mask) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XFusion_q_WriteReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_ISR, Mask);
}

u32 XFusion_q_InterruptGetEnabled(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XFusion_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_IER);
}

u32 XFusion_q_InterruptGetStatus(XFusion_q *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XFusion_q_ReadReg(InstancePtr->Ctrl_BaseAddress, XFUSION_Q_CTRL_ADDR_ISR);
}

