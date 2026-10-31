/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/
// ????ADS114S08??(????,??????)
// ??????????????,?? ADC_CMD_RDATA ?
// ???,???????(????????????)
#define ADC_CMD_RDATA       0x12

/* Private variables----------------------------------------------------------*/
static void ReadID(void);
static void Init(void);
static void ADS114_Read_AD(void);

/* Public variables-----------------------------------------------------------*/
SPI_AD_t  SPI_AD = 
{
	0.0,
	0,
		
	Init,
	ReadID,
	ADS114_Read_AD
};

/* Private function prototypes------------------------------------------------*/
static uint8_t SPI_AD_ReadByte(void);
static void    SPI_AD_WriteByte(uint8_t);
static void SPI_Delay(void);
static float Calc_Voltage(uint16_t);

/* -------------------------------------------------------------------------- */
/*  ?????????,????(?????)                                 */
/* -------------------------------------------------------------------------- */

static uint8_t SPI_AD_ReadByte()
{	
	uint8_t ReceiveByte;
	if(HAL_SPI_Receive(&hspi1, &ReceiveByte, 1, HAL_MAX_DELAY) != HAL_OK)
		ReceiveByte = 0xFF;
	return ReceiveByte;
}

static void SPI_AD_WriteByte(uint8_t Byte)
{	
	HAL_SPI_Transmit(&hspi1, &Byte, 1, HAL_MAX_DELAY);
}

static void SPI_Delay(void)
{
	while(!AD_DRDY_STATE)
		__NOP();
	while(AD_DRDY_STATE)
		__NOP();
}

static void ReadID()
{
	uint8_t Temp;
	SPI_AD_WriteByte(0x20);
	SPI_AD_WriteByte(0x00);
	Temp = SPI_AD_ReadByte();
	Public.pM_M[0] = Temp;  // ??????,?????
}

static void Init()
{
	SPI_AD_WriteByte(0x43);
	SPI_AD_WriteByte(0x00);
	SPI_AD_WriteByte(0x48);
	HAL_Delay(100);
	SPI_AD_WriteByte(0x45);
	SPI_AD_WriteByte(0x00);
	SPI_AD_WriteByte(0x1A);
	HAL_Delay(50);
	SPI_AD_WriteByte(ADC_CMD_START);
	HAL_Delay(100);
}

static float Calc_Voltage(uint16_t dat)
{
	float Temp = 0.0;
	uint16_t i;
	if(dat >= 0x8000)
	{
		i = dat - 0x8000;
		Temp = i * 2.5 / 32767;
	}
	return Temp;
}

/* -------------------------------------------------------------------------- */
/*  ????:ADS114_Read_AD ????????                                  */
/* -------------------------------------------------------------------------- */
static void ADS114_Read_AD(void)
{
	uint8_t Buf[2];
	float Voltage;
	float Resistance;

	// ??1 (0x0C)
	SPI_AD_WriteByte(0x42);
	SPI_AD_WriteByte(0x00);
	SPI_AD_WriteByte(0x0C);
	SPI_Delay();
	SPI_AD_WriteByte(ADC_CMD_RDATA);
	Buf[0] = SPI_AD_ReadByte();
	Buf[1] = SPI_AD_ReadByte();
	Voltage = Calc_Voltage(Buf[0]*256 + Buf[1]);
	Resistance = (Voltage * 100.0) / (2.5 - Voltage);
	Public.Float_To_U32(Resistance, MOS1_M_addr);

	// ??2 (0x1C)
	SPI_AD_WriteByte(0x42);
	SPI_AD_WriteByte(0x00);
	SPI_AD_WriteByte(0x1C);
	SPI_Delay();
	SPI_AD_WriteByte(ADC_CMD_RDATA);
	Buf[0] = SPI_AD_ReadByte();
	Buf[1] = SPI_AD_ReadByte();
	Voltage = Calc_Voltage(Buf[0]*256 + Buf[1]);
	Resistance = (Voltage * 100.0) / (2.5 - Voltage);
	Public.Float_To_U32(Resistance, MOS2_M_addr);

	// ??3 (0x2C)
	SPI_AD_WriteByte(0x42);
	SPI_AD_WriteByte(0x00);
	SPI_AD_WriteByte(0x2C);
	SPI_Delay();
	SPI_AD_WriteByte(ADC_CMD_RDATA);
	Buf[0] = SPI_AD_ReadByte();
	Buf[1] = SPI_AD_ReadByte();
	Voltage = Calc_Voltage(Buf[0]*256 + Buf[1]);
	Resistance = (Voltage * 100.0) / (2.5 - Voltage);
	Public.Float_To_U32(Resistance, MOS3_M_addr);

	// ??4 (0x3C)
	SPI_AD_WriteByte(0x42);
	SPI_AD_WriteByte(0x00);
	SPI_AD_WriteByte(0x3C);
	SPI_Delay();
	SPI_AD_WriteByte(ADC_CMD_RDATA);
	Buf[0] = SPI_AD_ReadByte();
	Buf[1] = SPI_AD_ReadByte();
	Voltage = Calc_Voltage(Buf[0]*256 + Buf[1]);
	Resistance = (Voltage * 100.0) / (2.5 - Voltage);
	Public.Float_To_U32(Resistance, MOS4_M_addr);

	// ??5 (0x4C)
	SPI_AD_WriteByte(0x42);
	SPI_AD_WriteByte(0x00);
	SPI_AD_WriteByte(0x4C);
	SPI_Delay();
	SPI_AD_WriteByte(ADC_CMD_RDATA);
	Buf[0] = SPI_AD_ReadByte();
	Buf[1] = SPI_AD_ReadByte();
	Voltage = Calc_Voltage(Buf[0]*256 + Buf[1]);
	Resistance = (Voltage * 100.0) / (2.5 - Voltage);
	Public.Float_To_U32(Resistance, MOS5_M_addr);

	// ??:??6 (0x5C)
	SPI_AD_WriteByte(0x42);
	SPI_AD_WriteByte(0x00);
	SPI_AD_WriteByte(0x5C);
	SPI_Delay();
	SPI_AD_WriteByte(ADC_CMD_RDATA);
	Buf[0] = SPI_AD_ReadByte();
	Buf[1] = SPI_AD_ReadByte();
	Voltage = Calc_Voltage(Buf[0]*256 + Buf[1]);
	Resistance = (Voltage * 100.0) / (2.5 - Voltage);
	Public.Float_To_U32(Resistance, MOS6_M_addr);
}