#ifndef __MyIWDG_H__
#define __MyIWDG_H__

#include "MyApplication.h"

//定义枚举类型

//定义结构体类型
typedef struct
{
	uint8_t FeedDog_Flag;  //喂狗标志位
	
	void (*FeedDog)(void); //喂狗
} MyIWDG_t;

/* extern variables-----------------------------------------------------------*/
extern  MyIWDG_t  MyIWDG;
/* extern function prototypes-------------------------------------------------*/

#endif
/********************************************************
  End Of File
********************************************************/
