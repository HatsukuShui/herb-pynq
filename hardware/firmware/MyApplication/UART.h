#ifndef __UART_H_
#define __UART_H_

#include "MyApplication.h"

//定义枚举类型
typedef enum
{	
	TTL       = (uint8_t)0,
	RS_485	  = (uint8_t)1,
	RS_232	  = (uint8_t)2,
}Interface_Type_t;
typedef enum
{	
	COM1    = (uint8_t)1,
	COM2	  = (uint8_t)2,
	COM3	  = (uint8_t)3,
	COM4	  = (uint8_t)4,
	COM5	  = (uint8_t)5,
}UART_Number_t;
//定义异步串口结构体类型
typedef struct
{
	UART_Number_t   UART_Number;
	uint16_t Send_LENGTH;
	uint16_t Rec_LENGTH;
	
	uint8_t* pucSend_Buffer;           //发送缓存指针 
	uint8_t* pucRec_Buffer;            //接收缓存指针 
		
	void (*SendArray)(uint8_t*,uint16_t);  //串口发送数组
	void (*SendString)(uint8_t*);          //串口发送字符串

	uint8_t	Interface_Type;            //接口类型
	void (*RS485_Set_SendMode)(void);  //RS-485接口设置为发送模式
	void (*RS485_Set_RecMode)(void);   //RS-485接口设置为接收模式
	
} UART_t;

/* extern variables-----------------------------------------------------------*/

/* extern function prototypes-------------------------------------------------*/

#endif
/********************************************************
  End Of File
********************************************************/

