/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

static void Peripheral_Set(void);

MyInit_t MyInit = 
{
	Peripheral_Set
};

static void Peripheral_Set()
{
	printf("Initialization completed, system startup!\r\n");
	printf("Software version is V%.1f\r\n\r\n", SoftWare_Version);
	
	Timer14.Timer14_Start_IT();
	__HAL_UART_ENABLE_IT(&huart1, UART_IT_IDLE);
	HAL_UART_Receive_DMA(&huart1, UART1.pucRec_Buffer, UART1_Rec_LENGTH);
	UART1.RS485_Set_RecMode();
	
	Heat.Init();        // ???????(PWM??,???80)
	Pump.Init();        // ?????(PWM??,??80)
	SPI_AD.Init();      // ADC???
	
	// LED??7???????
	for(int i=0; i<7; i++)
	{
		LED.LED_Flip(LED_Run);
		HAL_Delay(100);
	}
}