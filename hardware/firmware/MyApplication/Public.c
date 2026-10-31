/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/

/* Private variables----------------------------------------------------------*/
static void Memory_Clr(uint8_t*,uint16_t);   //内存清除函数
static uint16_t  AO_Memory[M_LENGTH] = {0x00}; //100个模拟量输出
static void Float_To_U32(float , uint16_t ) ;
/* Public variables-----------------------------------------------------------*/
Public_t  Public = 
{
	AO_Memory,
	
  Memory_Clr,
	Float_To_U32
};
/* Private function prototypes------------------------------------------------*/      
/*
	* @name   Memory_Set
	* @brief  内存清除函数
	* @param  pucBuffer -> 内存首地址
						LEN       -> 内存长度   
	* @retval None      
*/
static void Memory_Clr(uint8_t* pucBuffer,uint16_t LEN)
{
	uint16_t i;
	
	for(i=0;i<LEN;i++)
	{
		*(pucBuffer+i) = (uint8_t)0;
	}
}
/*
	* @name   fputc
	* @brief  fputc映射物理串口
	* @param  ch -> 待发送字符
	* @retval ch -> 已发送字符      
*/
int fputc(int ch,FILE* f)
{
	UART1.RS485_Set_SendMode();
	//通过查询的方式循环发送
	HAL_UART_Transmit(&huart_debug, (uint8_t *)&ch, 1, 0x000A);
	UART1.RS485_Set_RecMode();
	return ch;
}
/* Private function prototypes------------------------------------------------*/      
/*
	* @name   Float_To_U32
	* @brief  浮点数保存到modbus寄存器中
	* @param  value -> 待转换的浮点数
						regaddr   -> modbus地址  
	* @retval None 
*/
static void Float_To_U32(float value, uint16_t regaddr)
{
    un_DtformConver Data;
    Data.ul_Temp = value;//获取小数值
    Public.pM_M[regaddr]= Data.us_Buf[0];//获取低16位
    Public.pM_M[regaddr+1] = Data.us_Buf[1];//获取高16位
}
/********************************************************
  End Of File
********************************************************/
