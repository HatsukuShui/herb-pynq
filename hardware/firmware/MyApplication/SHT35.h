#ifndef __SHT35__
#define __SHT35__

#include "MyApplication.h"

//宏定义


//定义枚举类型

//定义结构体类型

typedef struct
{
	float   fTemperature;  //温度 -40至125℃    精度0.1℃ 
	float   fHumidity;     //湿度 0%RH至100%RH  精度1%RH           
	
	void (*SHT35_read_result)(void);  //周期测量模式
}SHT35_t;

/* extern variables-----------------------------------------------------------*/
extern SHT35_t  SHT35;
#endif
/********************************************************
  End Of File
********************************************************/
