/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/

/* Private variables----------------------------------------------------------*/
static void LED_ON(LED_Num_t); 
static void LED_OFF(LED_Num_t);
static void LED_Flip(LED_Num_t);

/* Public variables-----------------------------------------------------------*/
LED_t LED = 
{
	LED_ON,
	LED_OFF,
	LED_Flip
};

/* Private function prototypes------------------------------------------------*/      

/*
	* @name   LED_ON
	* @brief  打开LED
	* @param  Num -> 编号
	* @retval None      
*/
static void LED_ON(LED_Num_t LED_Num)
{
	//条件选择语句
	switch(LED_Num)
	{
		case LED_Run: HAL_GPIO_WritePin(LED_GPIO_Port,LED_Pin,GPIO_PIN_SET); break;
//		case LED_Warn: HAL_GPIO_WritePin(LED_Warn_GPIO_Port,LED_Warn_Pin,GPIO_PIN_SET); break;
		default: System.Assert_Failed();
	}
}

/*
	* @name   LED_OFF
	* @brief  关闭LED
	* @param  Num -> 编号
	* @retval None      
*/
static void LED_OFF(LED_Num_t LED_Num)
{
	//条件选择语句
	switch(LED_Num)
	{
		case LED_Run: HAL_GPIO_WritePin(LED_GPIO_Port,LED_Pin,GPIO_PIN_RESET); break;
//		case LED_Warn: HAL_GPIO_WritePin(LED_Warn_GPIO_Port,LED_Warn_Pin,GPIO_PIN_RESET); break;
		default: System.Assert_Failed();
	}
}

/*
	* @name   LED_Flip
	* @brief  取反LED
	* @param  Num -> 编号
	* @retval None      
*/
static void LED_Flip(LED_Num_t LED_Num)
{
	//条件选择语句
	switch(LED_Num)
	{
		case LED_Run: HAL_GPIO_TogglePin(LED_GPIO_Port,LED_Pin); break;
//		case LED_Warn: HAL_GPIO_TogglePin(LED_Warn_GPIO_Port,LED_Warn_Pin); break;
		default: System.Assert_Failed();
	}
}
/********************************************************
  End Of File
********************************************************/
