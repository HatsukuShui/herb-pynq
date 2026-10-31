/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/

/* Private variables----------------------------------------------------------*/

/* Private function prototypes------------------------------------------------*/      
static void Timer3_Start_IT(void);  //定时器6以中断模式启动
static void Delay_5mS(uint16_t );       //延时程序	
/* Public variables-----------------------------------------------------------*/
Timer3_t  Timer3 = 
{
	0,
	0,
	0,
	
	Timer3_Start_IT,
  Delay_5mS	
};

/*
	* @name   Timer3_Start_IT
	* @brief  定时器3以中断模式启动
	* @param  None
	* @retval None      
*/
static void Timer3_Start_IT(void)
{
	HAL_TIM_Base_Start_IT(&htim3); //启动定时器3
}

/*
	* @name   Delay
	* @brief  5mS延时程序
	* @param  延时n 5ms
	* @retval None      
*/
static void Delay_5mS(uint16_t n)
{
	Timer3.usDelay_Timer=0;
	while(1)
	{
		if(Timer3.usDelay_Timer>=n)
			break;
	}
	
}

/********************************************************
  End Of File
********************************************************/
