#ifndef __System_H__
#define __System_H__

//定义结构体类型
typedef struct
{
	void (*Run)(void);
	void (*Run_500mS)(void);
	void (*Run_1S)(void);
	void (*Run_3M)(void);
	void (*Error_Handler)(void);
	void (*Assert_Failed)(void);
} System_t;

/* extern variables-----------------------------------------------------------*/
extern System_t  System;
/* extern function prototypes-------------------------------------------------*/

#endif
/********************************************************
  End Of File
********************************************************/
