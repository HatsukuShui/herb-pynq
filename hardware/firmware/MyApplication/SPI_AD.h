#ifndef __SPI_AD_H__
#define __SPI_AD_H__

//头文件
#include "MyApplication.h"

////宏定义
//ADS114S08有关定义
//设置ads114S08寄存器00h-ID     01h-STATUS    02h-INPMUX    03h-PGA     04h-DATARATE
//                   05h-REF    06h-IDACMAG   07h-IDACMUS   08h-VBIAS   09h-SYS
//                   0Ah-保留   0Bh-OFCAL0    0Ch-OFCAL1    0Dh-保留    0Eh-FSCAL0 
//                   0Fh-FSCAL1 10h-GPIODAT   11h-GPIOCON   写+40h   读+20h 
//ADS114S08命令码列表 
#define ADC_CMD_NOP         0x00            /*!< 空操作   */ 
#define ADC_CMD_WAKEUP      0x02            /*!< 退出睡眠模式   */
#define ADC_CMD_POWERDN     0x04            /*掉电*/
#define ADC_CMD_RESET       0x06            /*!< 芯片复位   */  
#define ADC_CMD_START       0x08            /*开始转换*/
#define ADC_CMD_STOP        0x0A            /*停止转换*/
//校准命令
#define ADC_CMD_SYSOCAL     0x16            /*!< 系统偏移校准   */  
#define ADC_CMD_SYSGCAL     0x17            /*!< 系统增益校准   */  
#define ADC_CMD_SELFOCAL    0x19            /*!< 系统自校准   */ 
//数据读命令
#define ADC_CMD_RDATA       0x12            /*!< 单次读取数据   */  
//寄存器读写命令  
#define ADC_CMD_RREG        0x20            /*!< 读寄存器   */  
#define ADC_CMD_WREG        0x40            /*!< 写寄存器   */  
 

	 
//ADS114S08寄存器列表
#define ADC_REG_ICID        0x00
#define ADC_REG_STATUS      0x01
#define ADC_REG_INPMUX      0x02
#define ADC_REG_PGA         0x03
#define ADC_REG_DATARATE    0x04
#define ADC_REG_REF         0x05
#define ADC_REG_IDACMAG     0x06    
#define ADC_REG_IDACMUX     0x07  
#define ADC_REG_VBIAS       0x08  
#define ADC_REG_SYS         0x09  
#define ADC_REG_OFC0        0x0A
#define ADC_REG_OFC1        0x0B
#define ADC_REG_OFC2        0x0C
#define ADC_REG_FSC0        0x0D  
#define ADC_REG_FSC1        0x0E  
#define ADC_REG_FSC2        0x0F 
#define ADC_REG_GPIODAT     0x10
#define ADC_REG_GPIOCON     0x11



//ADS114S08支持的增益列表  
#define ADC_GAIN_1          0x00  
#define ADC_GAIN_2          0x01  
#define ADC_GAIN_4          0x02  
#define ADC_GAIN_8          0x03  
#define ADC_GAIN_16         0x04  
#define ADC_GAIN_32         0x05  
#define ADC_GAIN_64         0x06  
#define ADC_GAIN_128        0x07 
#define ADC_GAIN_EN         0x08

//ADS114S08支持的转换速率列表  
#define ADC_SPS_5           0x01  
#define ADC_SPS_10          0x02  
#define ADC_SPS_16_6        0x03 
#define ADC_SPS_20          0x04
#define ADC_SPS_50          0x05 
#define ADC_SPS_60          0x06 
#define ADC_SPS_100         0x07 
#define ADC_SPS_100         0x07  
#define ADC_SPS_400         0x09  
#define ADC_SPS_1000        0x0b  
#define ADC_SPS_2000        0x0c  
#define ADC_SPS_4000        0x0d 

#define POSI_AIN(x)    (x<<4)
#define NEGA_AIN(x)    (x)

//ADS114S08转换模式
#define ADC_MODE_SINGLECOV      0x00        //单次转换  
#define ADC_MODE_CONTINUOUS     0x01        //连续转换 

#define AD_DRDY_STATE   HAL_GPIO_ReadPin( AD_DRDY_GPIO_Port,AD_DRDY_Pin ) 

#define  	Dummy_Byte           		0xFF  //假数据

//定义枚举类型

//定义结构体类型
typedef struct
{
	float    Flow_Voltage;                        //流量电压值
  uint8_t  ID;	                                //设备标识符 
	
	void (*Init)(void);                           //初始化
	void (*ReadID)(void);                          //读取ID
	void (*ADS114_Read_AD)(void); 
} SPI_AD_t;


/* extern variables-----------------------------------------------------------*/
extern SPI_AD_t  SPI_AD ;

/* extern function prototypes-------------------------------------------------*/

#endif
/********************************************************
  End Of File
********************************************************/
