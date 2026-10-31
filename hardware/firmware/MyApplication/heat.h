#ifndef __HEAT_H__
#define __HEAT_H__

#include "MyApplication.h"

/* ?????? */
typedef enum
{
	HEAT_CH1 = 1,
	HEAT_CH2 = 2,
	HEAT_CH3 = 3
} Heat_Channel_t;

typedef struct
{
	void (*Init)(void);                         // ?????PWM
	void (*Set)(uint8_t channel, uint16_t value); // ?????????(0-100)
} Heat_t;

extern Heat_t Heat;

#endif