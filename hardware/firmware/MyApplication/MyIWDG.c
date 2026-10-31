/* Includes ------------------------------------------------------------------*/
#include "MyApplication.h"

/* Private define-------------------------------------------------------------*/

/* Private variables----------------------------------------------------------*/

/* Private function prototypes------------------------------------------------*/  
static void FeedDog(void);

/* Public variables-----------------------------------------------------------*/
MyIWDG_t MyIWDG = 
{
	TRUE,
	
	FeedDog
};    

/*
	* @name   FeedDog
	* @brief  Î¹¹·
	* @param  None
	* @retval None      
*/
static void FeedDog(void)
{
	HAL_IWDG_Refresh(&hiwdg);
}
/********************************************************
  End Of File
********************************************************/
