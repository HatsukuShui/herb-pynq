#ifndef __Timer14_H__
#define __Timer14_H__

#include "MyApplication.h"

//定义枚举类型
typedef enum
{
	TIMER14_10mS  	= (uint16_t)2,
	TIMER14_50mS  	= (uint16_t)10,
	TIMER14_100mS	= (uint16_t)20,
	TIMER14_200mS	= (uint16_t)40,
	TIMER14_500mS	= (uint16_t)100,
	TIMER14_1S     = (uint16_t)200,
	TIMER14_2S     = (uint16_t)400,
	TIMER14_3S     = (uint16_t)600,
	TIMER14_5S     = (uint16_t)1000,
	TIMER14_10S    = (uint16_t)2000,
	TIMER14_3min   = (uint16_t)36000,
}Timer14_Value_t;

//定义结构体类型
typedef struct
{
  uint16_t volatile usMCU_Run_Timer;  //系统运行定时器
	uint16_t volatile usDelay_Timer;    //延时定时器
	uint16_t volatile usMCU_Run_Timer500mS;    //500ms定时器
	
	void (*Timer14_Start_IT)(void);      //定时器6以中断模式启动
	void (*Delay_5mS)(uint16_t );           //延时程序	
} Timer14_t;

/* extern variables-----------------------------------------------------------*/
extern Timer14_t  Timer14;

#endif
/********************************************************
  End Of File
********************************************************/
