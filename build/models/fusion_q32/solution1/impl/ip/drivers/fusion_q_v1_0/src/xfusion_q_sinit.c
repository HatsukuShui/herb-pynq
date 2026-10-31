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
#include "xfusion_q.h"

extern XFusion_q_Config XFusion_q_ConfigTable[];

#ifdef SDT
XFusion_q_Config *XFusion_q_LookupConfig(UINTPTR BaseAddress) {
	XFusion_q_Config *ConfigPtr = NULL;

	int Index;

	for (Index = (u32)0x0; XFusion_q_ConfigTable[Index].Name != NULL; Index++) {
		if (!BaseAddress || XFusion_q_ConfigTable[Index].Ctrl_BaseAddress == BaseAddress) {
			ConfigPtr = &XFusion_q_ConfigTable[Index];
			break;
		}
	}

	return ConfigPtr;
}

int XFusion_q_Initialize(XFusion_q *InstancePtr, UINTPTR BaseAddress) {
	XFusion_q_Config *ConfigPtr;

	Xil_AssertNonvoid(InstancePtr != NULL);

	ConfigPtr = XFusion_q_LookupConfig(BaseAddress);
	if (ConfigPtr == NULL) {
		InstancePtr->IsReady = 0;
		return (XST_DEVICE_NOT_FOUND);
	}

	return XFusion_q_CfgInitialize(InstancePtr, ConfigPtr);
}
#else
XFusion_q_Config *XFusion_q_LookupConfig(u16 DeviceId) {
	XFusion_q_Config *ConfigPtr = NULL;

	int Index;

	for (Index = 0; Index < XPAR_XFUSION_Q_NUM_INSTANCES; Index++) {
		if (XFusion_q_ConfigTable[Index].DeviceId == DeviceId) {
			ConfigPtr = &XFusion_q_ConfigTable[Index];
			break;
		}
	}

	return ConfigPtr;
}

int XFusion_q_Initialize(XFusion_q *InstancePtr, u16 DeviceId) {
	XFusion_q_Config *ConfigPtr;

	Xil_AssertNonvoid(InstancePtr != NULL);

	ConfigPtr = XFusion_q_LookupConfig(DeviceId);
	if (ConfigPtr == NULL) {
		InstancePtr->IsReady = 0;
		return (XST_DEVICE_NOT_FOUND);
	}

	return XFusion_q_CfgInitialize(InstancePtr, ConfigPtr);
}
#endif

#endif

