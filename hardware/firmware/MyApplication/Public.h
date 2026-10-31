#ifndef __PUBLIC_H_
#define __PUBLIC_H_

#include "MyApplication.h"

/* ???? */
#define SoftWare_Version 	(float)0.10
#define	huart_debug		huart1

/* ?????:6????(???2????,?12?) + 3??? + 1??? = 16 */
#define M_LENGTH  16

/* Modbus??????? */
#define MOS1_M_addr      0   // float,2????,??1
#define MOS2_M_addr      2   // float,??2
#define MOS3_M_addr      4   // float,??3
#define MOS4_M_addr      6   // float,??4
#define MOS5_M_addr      8   // float,??5
#define MOS6_M_addr      10  // float,??6
#define HEAT1_M_addr     12  // uint16_t, 0-100
#define HEAT2_M_addr     13
#define HEAT3_M_addr     14
#define PUMP_M_addr      15  // uint16_t, 0-100

/* ????? */
typedef enum
{
	BIT0 = (uint8_t)(0x01 << 0),  
	BIT1 = (uint8_t)(0x01 << 1),  
	BIT2 = (uint8_t)(0x01 << 2),  
	BIT3 = (uint8_t)(0x01 << 3),  
	BIT4 = (uint8_t)(0x01 << 4),
	BIT5 = (uint8_t)(0x01 << 5),
	BIT6 = (uint8_t)(0x01 << 6),
	BIT7 = (uint8_t)(0x01 << 7),
} BIT_t;

typedef enum 
{
  FALSE = 0U, 
  TRUE = !FALSE
} FlagStatus_t;

typedef enum 
{
  FAILED = 0U, 
  PASSED = !FAILED
} TestStatus_t;

/* ???????????? */
typedef union                                         
{
   float ul_Temp;
   uint8_t  uc_Buf[4];
   uint16_t us_Buf[2];
} un_DtformConver;

/* ??????? */
typedef struct
{
	uint16_t* volatile  pM_M;     // ???????
	void (*Memory_Clr)(uint8_t*, uint16_t);
	void (*Float_To_U32)(float, uint16_t);
} Public_t;

extern Public_t Public;

#endif