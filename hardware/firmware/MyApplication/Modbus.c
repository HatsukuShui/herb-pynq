/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/
#define FunctionCode_Read_Register 		(uint8_t)0x03
#define FunctionCode_Write_Register 	(uint8_t)0x06
#define Modbus_Order_LENGTH           (uint8_t)8

/* Private variables----------------------------------------------------------*/
static void Protocol_Analysis(UART_t*);
static void Modbus_Read_Register(UART_t*);
static void Modbus_Wrtie_Register(UART_t*);
static void Handle_Read_Analog_Output(uint16_t, uint16_t *);
static void Handle_Write_Analog_Output(uint16_t, uint16_t *);

/* Public variables-----------------------------------------------------------*/
Modbus_t Modbus = 
{
	1,   // ????
	Protocol_Analysis
};

/* -------------------------------------------------------------------------- */
static void Protocol_Analysis(UART_t* UART) 
{
	UART_t* const  COM = UART;
	uint8_t i = 0, Index = 0;

	switch(COM->UART_Number)
	{
		case COM1:  HAL_UART_DMAStop(&huart1); break;
		default: System.Error_Handler();
	}
	
	// ??????,??????
	for(i=0; i<COM->Rec_LENGTH; i++)
	{
		if(Index == 0)
		{
			if(*(COM->pucRec_Buffer+i) != Modbus.Addr)
				continue;
		}
		*(COM->pucRec_Buffer+Index) = *(COM->pucRec_Buffer+i);
		if(Index == Modbus_Order_LENGTH)
			break;
		Index++;
	}
	
	// CRC??
	CRC_16.CRC_Value = CRC_16.CRC_Check(COM->pucRec_Buffer, 6);
	CRC_16.CRC_H = (uint8_t)(CRC_16.CRC_Value >> 8);
	CRC_16.CRC_L = (uint8_t)CRC_16.CRC_Value;
	
	if(((*(COM->pucRec_Buffer+6) == CRC_16.CRC_L) && (*(COM->pucRec_Buffer+7) == CRC_16.CRC_H))
		|| ((*(COM->pucRec_Buffer+6) == CRC_16.CRC_H) && (*(COM->pucRec_Buffer+7) == CRC_16.CRC_L)))
	{
		if(*(COM->pucRec_Buffer) == Modbus.Addr)
		{
			if(*(COM->pucRec_Buffer+1) == FunctionCode_Read_Register)
				Modbus_Read_Register(COM);
			else if(*(COM->pucRec_Buffer+1) == FunctionCode_Write_Register)
				Modbus_Wrtie_Register(COM);
		}
	}
	
	Public.Memory_Clr(COM->pucRec_Buffer, COM->Rec_LENGTH);
}

/* -------------------------------------------------------------------------- */
static void Modbus_Read_Register(UART_t* UART)
{
	UART_t* const  COM = UART;
	uint16_t Start_Address, Keep_Address, Register_Count, Byte_Count, Register_Data;
	uint8_t i;
	
	Start_Address = ((*(COM->pucRec_Buffer+2))<<8) + *(COM->pucRec_Buffer+3);
	Keep_Address = Start_Address;
	Register_Count = ((*(COM->pucRec_Buffer+4))<<8) + *(COM->pucRec_Buffer+5);
	Byte_Count = Register_Count * 2;
	
	for(i=0; i<(uint8_t)Byte_Count; i+=2, Keep_Address++)
	{
		Handle_Read_Analog_Output(Keep_Address, &Register_Data);
		*(COM->pucSend_Buffer+i+3) = Register_Data >> 8;
		*(COM->pucSend_Buffer+i+4) = Register_Data & 0xff;
	}
	
	*(COM->pucSend_Buffer+0) = *(COM->pucRec_Buffer+0);
	*(COM->pucSend_Buffer+1) = FunctionCode_Read_Register;
	*(COM->pucSend_Buffer+2) = Byte_Count;
	
	CRC_16.CRC_Value = CRC_16.CRC_Check(COM->pucSend_Buffer, (uint8_t)(Byte_Count+3));
	CRC_16.CRC_H = (uint8_t)(CRC_16.CRC_Value >> 8);
	CRC_16.CRC_L = (uint8_t)CRC_16.CRC_Value;
	*(COM->pucSend_Buffer+(uint8_t)(Byte_Count+3)) = CRC_16.CRC_H;
	*(COM->pucSend_Buffer+(uint8_t)(Byte_Count+4)) = CRC_16.CRC_L;
	
	COM->SendArray(COM->pucSend_Buffer, Byte_Count+5);
}

/* -------------------------------------------------------------------------- */
static void Modbus_Wrtie_Register(UART_t* UART)
{
	UART_t* const  COM = UART;
	uint16_t Start_Address, Register_Data;
	uint8_t i;
	
	Start_Address = ((*(COM->pucRec_Buffer+2))<<8) + *(COM->pucRec_Buffer+3);
	Register_Data = ((*(COM->pucRec_Buffer+4))<<8) + *(COM->pucRec_Buffer+5);
	
	// ???????
	Public.pM_M[Start_Address] = Register_Data;
	
	// ????????????
	switch(Start_Address)
	{
		case HEAT1_M_addr:
			Heat.Set(HEAT_CH1, Register_Data);
			break;
		case HEAT2_M_addr:
			Heat.Set(HEAT_CH2, Register_Data);
			break;
		case HEAT3_M_addr:
			Heat.Set(HEAT_CH3, Register_Data);
			break;
		case PUMP_M_addr:
			Pump.Set_DutyCycle(Register_Data);
			break;
		default:
			// ??????????,?????
			break;
	}
	
	// ????
	for(i=0; i<8; i++)
		*(COM->pucSend_Buffer+i) = *(COM->pucRec_Buffer+i);
	COM->SendArray(COM->pucSend_Buffer, 8);
}

/* -------------------------------------------------------------------------- */
static void Handle_Read_Analog_Output(uint16_t Register_Address, uint16_t *Register_Data)
{
	if(Register_Address < M_LENGTH)
		*Register_Data = Public.pM_M[Register_Address];
}

static void Handle_Write_Analog_Output(uint16_t Register_Address, uint16_t *Register_Data)
{
	if(Register_Address < M_LENGTH)
		Public.pM_M[Register_Address] = *Register_Data;
}