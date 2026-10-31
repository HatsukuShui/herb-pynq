#ifndef __Modbus_H__
#define __Modbus_H__

#include "MyApplication.h"

//定义枚举类型

//定义结构体类型
typedef struct
{
	uint16_t Addr;                       //地址
	
	void (*Protocol_Analysis)(UART_t*);  //协议分析
} Modbus_t;

/* extern variables-----------------------------------------------------------*/
extern Modbus_t Modbus;

/* extern function prototypes-------------------------------------------------*/

#endif
/********************************************************
  End Of File
********************************************************/


