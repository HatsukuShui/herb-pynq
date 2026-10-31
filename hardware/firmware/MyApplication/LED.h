#ifndef __LED_H__
#define __LED_H__

#include "MyApplication.h"

//定义枚举类型
typedef enum
{
	LED_Run = (uint8_t)0x01,
	LED_Warn = (uint8_t)0x02,
}LED_Num_t;

//定义结构体类型
typedef struct
{
	void (*LED_ON)(LED_Num_t);     //打开
	void (*LED_OFF)(LED_Num_t);    //关闭
	void (*LED_Flip)(LED_Num_t);   //翻转
} LED_t;

/* extern variables-----------------------------------------------------------*/
extern LED_t  LED;
/* extern function prototypes-------------------------------------------------*/

#endif
/********************************************************
  End Of File
********************************************************/
