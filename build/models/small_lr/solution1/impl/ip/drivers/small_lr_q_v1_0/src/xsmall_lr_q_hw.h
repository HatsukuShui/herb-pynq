// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2026.1 (64-bit)
// Tool Version Limit: 2026.06
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
// CTRL
// 0x000 : Control signals
//         bit 0  - ap_start (Read/Write/COH)
//         bit 1  - ap_done (Read/COR)
//         bit 2  - ap_idle (Read)
//         bit 3  - ap_ready (Read/COR)
//         bit 7  - auto_restart (Read/Write)
//         bit 9  - interrupt (Read)
//         others - reserved
// 0x004 : Global Interrupt Enable Register
//         bit 0  - Global Interrupt Enable (Read/Write)
//         others - reserved
// 0x008 : IP Interrupt Enable Register (Read/Write)
//         bit 0 - enable ap_done interrupt (Read/Write)
//         bit 1 - enable ap_ready interrupt (Read/Write)
//         others - reserved
// 0x00c : IP Interrupt Status Register (Read/TOW)
//         bit 0 - ap_done (Read/TOW)
//         bit 1 - ap_ready (Read/TOW)
//         others - reserved
// 0x010 : Data signal of ap_return
//         bit 31~0 - ap_return[31:0] (Read)
// 0x020 ~
// 0x03f : Memory 'logits_q' (8 * 32b)
//         Word n : bit [31:0] - logits_q[n]
// 0x100 ~
// 0x1ff : Memory 'input_q' (50 * 32b)
//         Word n : bit [31:0] - input_q[n]
// (SC = Self Clear, COR = Clear on Read, TOW = Toggle on Write, COH = Clear on Handshake)

#define XSMALL_LR_Q_CTRL_ADDR_AP_CTRL       0x000
#define XSMALL_LR_Q_CTRL_ADDR_GIE           0x004
#define XSMALL_LR_Q_CTRL_ADDR_IER           0x008
#define XSMALL_LR_Q_CTRL_ADDR_ISR           0x00c
#define XSMALL_LR_Q_CTRL_ADDR_AP_RETURN     0x010
#define XSMALL_LR_Q_CTRL_BITS_AP_RETURN     32
#define XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_BASE 0x020
#define XSMALL_LR_Q_CTRL_ADDR_LOGITS_Q_HIGH 0x03f
#define XSMALL_LR_Q_CTRL_WIDTH_LOGITS_Q     32
#define XSMALL_LR_Q_CTRL_DEPTH_LOGITS_Q     8
#define XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_BASE  0x100
#define XSMALL_LR_Q_CTRL_ADDR_INPUT_Q_HIGH  0x1ff
#define XSMALL_LR_Q_CTRL_WIDTH_INPUT_Q      32
#define XSMALL_LR_Q_CTRL_DEPTH_INPUT_Q      50

