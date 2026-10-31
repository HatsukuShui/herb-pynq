#ifndef __Timer3_H__
#define __Timer3_H__

#include "MyApplication.h"

//定义枚举类型
typedef enum
{
	TIMER3_10mS  	= (uint16_t)2,
	TIMER3_50mS  	= (uint16_t)10,
	TIMER3_100mS	= (uint16_t)20,
	TIMER3_200mS	= (uint16_t)40,
	TIMER3_500mS	= (uint16_t)100,
	TIMER3_1S     = (uint16_t)200,
	TIMER3_2S     = (uint16_t)400,
	TIMER3_3S     = (uint16_t)600,
	TIMER3_5S     = (uint16_t)1000,
	TIMER3_10S    = (uint16_t)2000,
	TIMER3_3min   = (uint16_t)36000,
}TIMER3_Value_t;

//定义结构体类型
typedef struct
{
  uint16_t volatile usMCU_Run_Timer;  //系统运行定时器
	uint16_t volatile usDelay_Timer;    //延时定时器
	uint16_t volatile usMCU_Run_Timer500mS;    //500ms定时器
	
	void (*Timer3_Start_IT)(void);      //定时器6以中断模式启动
	void (*Delay_5mS)(uint16_t );           //延时程序	
} Timer3_t;

/* extern variables-----------------------------------------------------------*/
extern Timer3_t  Timer3;

#endif
/********************************************************
  End Of File
********************************************************/
