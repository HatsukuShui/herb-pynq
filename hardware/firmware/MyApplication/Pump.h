#ifndef __PUMP_H__
#define __PUMP_H__

#include "MyApplication.h"

#define PUMP_MAX_VALUE   100   // ???????

typedef struct
{
	void (*Init)(void);
	void (*Set_DutyCycle)(uint16_t value);  // 0-100
	void (*Open)(void);
	void (*Close)(void);
} Pump_t;

extern Pump_t Pump;

#endif