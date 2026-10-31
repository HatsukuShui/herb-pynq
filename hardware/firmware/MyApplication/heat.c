/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/
#define HEAT_MAX_VALUE   100   // ???????
#define HEAT_CCR_MAX     1000  // CCR??? (??100%)

/* Private variables----------------------------------------------------------*/
static void Init(void);
static void Heat_Set(uint8_t channel, uint16_t value);

/* Public variables-----------------------------------------------------------*/
Heat_t Heat = 
{
	Init,
	Heat_Set
};

/* -------------------------------------------------------------------------- */
static void Init(void)
{
	// ????PWM??
	HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
	HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_2);
	HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_3);
	
	// ??????80
	Heat_Set(HEAT_CH1, 80);
	Heat_Set(HEAT_CH2, 80);
	Heat_Set(HEAT_CH3, 80);
	
	// ??????(Modbus????????80)
	Public.pM_M[HEAT1_M_addr] = 80;
	Public.pM_M[HEAT2_M_addr] = 80;
	Public.pM_M[HEAT3_M_addr] = 80;
}

static void Heat_Set(uint8_t channel, uint16_t value)
{
	uint32_t ccr;
	
	if (value > HEAT_MAX_VALUE)
		value = HEAT_MAX_VALUE;
	
	// ?? 0-100 -> 0-1000
	ccr = (uint32_t)value * 10;
	if (ccr > HEAT_CCR_MAX)
		ccr = HEAT_CCR_MAX;
	
	switch(channel)
	{
		case HEAT_CH1:
			TIM1->CCR1 = ccr;
			break;
		case HEAT_CH2:
			TIM1->CCR2 = ccr;
			break;
		case HEAT_CH3:
			TIM1->CCR3 = ccr;
			break;
		default:
			System.Error_Handler();
			break;
	}
}