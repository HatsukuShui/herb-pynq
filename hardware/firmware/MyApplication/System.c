/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

static void Run(void);
static void Run_500mS(void);
static void Run_1S(void);
static void Run_3M(void);
static void Error_Handler(void);
static void Assert_Failed(void);

System_t System = 
{
	Run,
	Run_500mS,
	Run_1S,
	Run_3M,
	Error_Handler,
	Assert_Failed
};

static void Run()
{
	SPI_AD.ADS114_Read_AD();   // ???????
	HAL_Delay(50);
}

static void Run_500mS() {}
static void Run_1S() {}
static void Run_3M() {}
static void Error_Handler() {}
static void Assert_Failed() {}