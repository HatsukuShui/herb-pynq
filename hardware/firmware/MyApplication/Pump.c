/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/
#define PUMP_CCR_MAX     200   // CCR??? (??100%)

/* Private variables----------------------------------------------------------*/
static void Init(void);
static void Set_DutyCycle(uint16_t value);
static void Open(void);
static void Close(void);

/* Public variables-----------------------------------------------------------*/
Pump_t Pump = 
{
	Init,
	Set_DutyCycle,
	Open,
	Close
};

static void Init(void)
{
	HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
	// ???80
	Set_DutyCycle(80);
	Public.pM_M[PUMP_M_addr] = 80;
}

static void Set_DutyCycle(uint16_t value)
{
    uint32_t ccr;

    // ??,?? value ? 0~100 ??
    if (value > PUMP_MAX_VALUE)
        value = PUMP_MAX_VALUE;

    // ????:0 ? 0%,100 ? 100%
    // ?? CCR ???? 200(?? 100% ???)
    ccr = 200-(uint32_t)value * 2;
    if (ccr > PUMP_CCR_MAX)
        ccr = PUMP_CCR_MAX;

    TIM3->CCR1 = ccr;
}

static void Open(void)
{
	// ???????????
	Set_DutyCycle(Public.pM_M[PUMP_M_addr]);
}

static void Close(void)
{
	TIM3->CCR1 = 0;
}