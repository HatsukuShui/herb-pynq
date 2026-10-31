/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/
//读SCD30_RDY管脚状态
#define READ_SCD30_RDY	HAL_GPIO_ReadPin(SCD30_RDY_GPIO_Port,SCD30_SDA_Pin)
/* Private variables----------------------------------------------------------*/

/* Public variables-----------------------------------------------------------*/

/* Private function prototypes------------------------------------------------*/      

/*
	* @name   HAL_TIM_PeriodElapsedCallback
	* @brief  定时器中断回调函数
	* @param  *htim -> 处理定时器的结构体指针
	* @retval None      
*/
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
	if(htim->Instance == htim14.Instance)
	{

		Timer14.usMCU_Run_Timer++;
		Timer14.usDelay_Timer++;
		
		if(++Timer14.usMCU_Run_Timer500mS >= TIMER14_500mS)
		{
			Timer14.usMCU_Run_Timer500mS = 0;
			LED.LED_Flip(LED_Run);
			MyIWDG.FeedDog();  //喂狗
		}		
	}
}


/**
  * @name    HAL_UART_TxCpltCallback
  * @brief  Tx 传输完成回调函数.
  * @param  huart  Pointer to a UART_HandleTypeDef structure that contains
  *                the configuration information for the specified UART module.
  * @retval None
  */
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
  if(huart->Instance == huart1.Instance)
	{
		UART1.RS485_Set_RecMode();
	}
}

/*
	* @name   HAL_UART_IdleCallback
	* @brief  串口空闲中断回调函数
	* @param  *htim -> 处理串口的结构体指针
	* @retval None      
*/
void HAL_UART_IdleCallback(UART_HandleTypeDef *huart)
{
	if(huart->Instance == huart1.Instance)
	{
		//解析MODBUS协议
		Modbus.Protocol_Analysis(&UART1);
		//串口1开启DMA接收
		HAL_UART_Receive_DMA(&huart1,UART1.pucRec_Buffer,UART1_Rec_LENGTH); //串口1开启DMA接收
	}
	


}


/********************************************************
  End Of File
********************************************************/
