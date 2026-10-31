/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/

/* Private variables----------------------------------------------------------*/

static uint8_t  ucSend_Buffer[UART1_Send_LENGTH] = {0x00};
static uint8_t  ucRec_Buffer [UART1_Rec_LENGTH]  = {0x00};

/* Private function prototypes------------------------------------------------*/      
static void SendArray(uint8_t*,uint16_t);  //串口发送数组
static void SendString(uint8_t*);          //串口发送字符串

static void RS485_Set_SendMode(void); //RS-485接口设置为发送模式
static void RS485_Set_RecMode(void);  //RS-485接口设置为接收模式

/* Public variables-----------------------------------------------------------*/
UART_t  UART1 = 
{
	COM1,
	UART1_Send_LENGTH,
	UART1_Rec_LENGTH,
	
	ucSend_Buffer,
	ucRec_Buffer,
	
	SendArray,
	SendString,
	
	RS_485,
	RS485_Set_SendMode,
	RS485_Set_RecMode
};

/*
	* @name   SendArray
	* @brief  串口发送数组
	* @param  p_Arr:数组首地址，LEN:发送长度
	* @retval None      
*/
static void SendArray(uint8_t* p_Arr,uint16_t LEN) 
{
	UART1.RS485_Set_SendMode();	
	HAL_UART_Transmit_DMA(&huart1,p_Arr,LEN);
}


/*
	* @name   SendString
	* @brief  发送字符串
	* @param  p_Str:待发送字符串
	* @retval None      
*/
static void SendString(uint8_t* p_Str) 
{	

}

/*
	* @name   RS485_Set_SendMode
	* @brief  RS-485接口设置为发送模式
	* @param  None
	* @retval None      
*/
static void RS485_Set_SendMode()
{
	HAL_GPIO_WritePin(USART1_485_GPIO_Port,USART1_485_Pin,GPIO_PIN_SET);
	HAL_Delay(1);
}

/*
	* @name   RS485_Set_RecMode
	* @brief  RS-485接口设置为接收模式
	* @param  None
	* @retval None      
*/
static void RS485_Set_RecMode()
{
	HAL_GPIO_WritePin(USART1_485_GPIO_Port,USART1_485_Pin,GPIO_PIN_RESET);
	HAL_Delay(1);	
}
/********************************************************
  End Of File
********************************************************/
