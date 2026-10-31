/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/
#define SHT35_ADDR  (uint8_t)(0x44 << 1) //传感器地址
//#define SHT30_ADDR  (unsigned char)(0x45 << 1) //传感器地址

#define	Write_CMD   0xFE
#define	Read_CMD    0x01
/* Private variables----------------------------------------------------------*/
static void SHT35_read_result(void);  //周期测量模式
               //
/* Public variables-----------------------------------------------------------*/
SHT35_t SHT35 = 
{
	0.0,
	0.0,
	
	SHT35_read_result
};

/* Private function prototypes------------------------------------------------*/      
static uint8_t CRC_8(uint8_t *,uint8_t);




/*
	* @name   SHT35_read_result
	* @brief  周期测量模式
	* @param  None
	* @retval None      
*/
static void SHT35_read_result(void)
{
  uint8_t   temp_array[6] = {0};
	uint16_t  temp_uint     = 0;
	float     temp_float    = 0;
	//启动周期性测量
	I2C_Soft.Start();
	I2C_Soft.Write_Byte(SHT35_ADDR & Write_CMD);
	I2C_Soft.Write_Byte(0x2c); //High repeat , mps = 10
	I2C_Soft.Write_Byte(0x06);
	I2C_Soft.Stop(); 
	HAL_Delay(100);
	
	I2C_Soft.Start();
	I2C_Soft.Write_Byte(SHT35_ADDR | Read_CMD);
	temp_array[0] = I2C_Soft.Read_Byte(ACK);
	temp_array[1] = I2C_Soft.Read_Byte(ACK);
	temp_array[2] = I2C_Soft.Read_Byte(ACK);
	temp_array[3] = I2C_Soft.Read_Byte(ACK);
	temp_array[4] = I2C_Soft.Read_Byte(ACK);
	temp_array[5] = I2C_Soft.Read_Byte(NACK);
	I2C_Soft.Stop();
		

			//////计算温度,精度0.1
			if(CRC_8(temp_array,2) == temp_array[2]) //CRC-8 校验
			{
				temp_uint         = temp_array[0]*256+temp_array[1];
				temp_float        = ((float)temp_uint)*0.267032-4500;
				SHT35.fTemperature = temp_float*0.01;
//				printf("温度: %.1f ℃\n", SHT35.fTemperature);
//				temp_uint=(int16_t)(SHT35.fTemperature*10);
//	      Public.pM_M[Temperature]=temp_uint;
				Public.Float_To_U32(SHT35.fTemperature,Temperature);  //赋值到modbus寄存器
				
			}
			
			//////计算湿度，精度1%RH
			if(CRC_8(&temp_array[3],2) == temp_array[5]) //CRC-8 校验
			{
				temp_uint      = temp_array[3]*256+temp_array[4];
				temp_float     = ((float)temp_uint)*0.152590;
				SHT35.fHumidity     = temp_float*0.01;
//				printf("湿度: %.1f %%\n", SHT35.fHumidity);
//				temp_uint=(int16_t)(SHT35.fHumidity*10);
//	      Public.pM_M[Humidity]=temp_uint;
				Public.Float_To_U32(SHT35.fHumidity,Humidity);  //赋值到modbus寄存器
			}
	
}

/*
	* @name   CRC_8
	* @brief  CRC-8校验
	* @param  Crc_ptr -> 校验数据首地址
						LEN     -> 校验数据长度
	* @retval CRC_Value -> 校验值      
*/
static uint8_t CRC_8(uint8_t *Crc_ptr,uint8_t LEN)
{
	uint8_t CRC_Value = 0xFF;
	uint8_t i = 0,j = 0;

	for(i=0;i<LEN;i++)
	{
		CRC_Value ^= *(Crc_ptr+i);
		for(j=0;j<8;j++)
		{
			if(CRC_Value & 0x80)
				CRC_Value = (CRC_Value << 1) ^ 0x31;
			else
				CRC_Value = (CRC_Value << 1);
		}
	}
	return CRC_Value;
}

/********************************************************
  End Of File
********************************************************/
