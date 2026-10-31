// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef __linux__

#include "xstatus.h"
#ifdef SDT
#include "xparameters.h"
#endif
#include "xsmall_lr_q.h"

extern XSmall_lr_q_Config XSmall_lr_q_ConfigTable[];

#ifdef SDT
XSmall_lr_q_Config *XSmall_lr_q_LookupConfig(UINTPTR BaseAddress) {
	XSmall_lr_q_Config *ConfigPtr = NULL;

	int Index;

	for (Index = (u32)0x0; XSmall_lr_q_ConfigTable[Index].Name != NULL; Index++) {
		if (!BaseAddress || XSmall_lr_q_ConfigTable[Index].Ctrl_BaseAddress == BaseAddress) {
			ConfigPtr = &XSmall_lr_q_ConfigTable[Index];
			break;
		}
	}

	return ConfigPtr;
}

int XSmall_lr_q_Initialize(XSmall_lr_q *InstancePtr, UINTPTR BaseAddress) {
	XSmall_lr_q_Config *ConfigPtr;

	Xil_AssertNonvoid(InstancePtr != NULL);

	ConfigPtr = XSmall_lr_q_LookupConfig(BaseAddress);
	if (ConfigPtr == NULL) {
		InstancePtr->IsReady = 0;
		return (XST_DEVICE_NOT_FOUND);
	}

	return XSmall_lr_q_CfgInitialize(InstancePtr, ConfigPtr);
}
#else
XSmall_lr_q_Config *XSmall_lr_q_LookupConfig(u16 DeviceId) {
	XSmall_lr_q_Config *ConfigPtr = NULL;

	int Index;

	for (Index = 0; Index < XPAR_XSMALL_LR_Q_NUM_INSTANCES; Index++) {
		if (XSmall_lr_q_ConfigTable[Index].DeviceId == DeviceId) {
			ConfigPtr = &XSmall_lr_q_ConfigTable[Index];
			break;
		}
	}

	return ConfigPtr;
}

int XSmall_lr_q_Initialize(XSmall_lr_q *InstancePtr, u16 DeviceId) {
	XSmall_lr_q_Config *ConfigPtr;

	Xil_AssertNonvoid(InstancePtr != NULL);

	ConfigPtr = XSmall_lr_q_LookupConfig(DeviceId);
	if (ConfigPtr == NULL) {
		InstancePtr->IsReady = 0;
		return (XST_DEVICE_NOT_FOUND);
	}

	return XSmall_lr_q_CfgInitialize(InstancePtr, ConfigPtr);
}
#endif

#endif

