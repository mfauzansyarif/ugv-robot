/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32g4xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define MotorS_1_Pin GPIO_PIN_13
#define MotorS_1_GPIO_Port GPIOC
#define LinearL_3_Pin GPIO_PIN_15
#define LinearL_3_GPIO_Port GPIOC
#define LinearR_3_Pin GPIO_PIN_0
#define LinearR_3_GPIO_Port GPIOF
#define LinearL_5_Pin GPIO_PIN_1
#define LinearL_5_GPIO_Port GPIOF
#define Lamp_F_Pin GPIO_PIN_0
#define Lamp_F_GPIO_Port GPIOC
#define Lamp_B_Pin GPIO_PIN_1
#define Lamp_B_GPIO_Port GPIOC
#define LinearR_5_Pin GPIO_PIN_2
#define LinearR_5_GPIO_Port GPIOC
#define MotorS_3_Pin GPIO_PIN_3
#define MotorS_3_GPIO_Port GPIOC
#define LinearR_2_Pin GPIO_PIN_0
#define LinearR_2_GPIO_Port GPIOA
#define LinearL_2_Pin GPIO_PIN_1
#define LinearL_2_GPIO_Port GPIOA
#define Debug_TX_Pin GPIO_PIN_2
#define Debug_TX_GPIO_Port GPIOA
#define Debug_RX_Pin GPIO_PIN_3
#define Debug_RX_GPIO_Port GPIOA
#define LinearR_11_Pin GPIO_PIN_4
#define LinearR_11_GPIO_Port GPIOA
#define MotorS_0_Pin GPIO_PIN_5
#define MotorS_0_GPIO_Port GPIOA
#define MotorP_0_Pin GPIO_PIN_6
#define MotorP_0_GPIO_Port GPIOA
#define LinearL_1_Pin GPIO_PIN_7
#define LinearL_1_GPIO_Port GPIOA
#define RS485_TX_Pin GPIO_PIN_4
#define RS485_TX_GPIO_Port GPIOC
#define RS485_RX_Pin GPIO_PIN_5
#define RS485_RX_GPIO_Port GPIOC
#define LED_Jetson_Pin GPIO_PIN_0
#define LED_Jetson_GPIO_Port GPIOB
#define LED_RF_Pin GPIO_PIN_1
#define LED_RF_GPIO_Port GPIOB
#define LED_Heartbeat_Pin GPIO_PIN_2
#define LED_Heartbeat_GPIO_Port GPIOB
#define Jetson_TX_Pin GPIO_PIN_10
#define Jetson_TX_GPIO_Port GPIOB
#define Jetson_RX_Pin GPIO_PIN_11
#define Jetson_RX_GPIO_Port GPIOB
#define LinearR_8_Pin GPIO_PIN_12
#define LinearR_8_GPIO_Port GPIOB
#define LinearL_8_Pin GPIO_PIN_13
#define LinearL_8_GPIO_Port GPIOB
#define MotorP_3_Pin GPIO_PIN_14
#define MotorP_3_GPIO_Port GPIOB
#define LinearR_9_Pin GPIO_PIN_15
#define LinearR_9_GPIO_Port GPIOB
#define MotorP_2_Pin GPIO_PIN_6
#define MotorP_2_GPIO_Port GPIOC
#define LinearR_7_Pin GPIO_PIN_7
#define LinearR_7_GPIO_Port GPIOC
#define MotorS_2_Pin GPIO_PIN_8
#define MotorS_2_GPIO_Port GPIOC
#define LinearR_1_Pin GPIO_PIN_9
#define LinearR_1_GPIO_Port GPIOC
#define LinearL_6_Pin GPIO_PIN_8
#define LinearL_6_GPIO_Port GPIOA
#define LinearL_7_Pin GPIO_PIN_9
#define LinearL_7_GPIO_Port GPIOA
#define LinearR_6_Pin GPIO_PIN_10
#define LinearR_6_GPIO_Port GPIOA
#define T_SWDIO_Pin GPIO_PIN_13
#define T_SWDIO_GPIO_Port GPIOA
#define T_SWCLK_Pin GPIO_PIN_14
#define T_SWCLK_GPIO_Port GPIOA
#define RF_RX_Pin GPIO_PIN_15
#define RF_RX_GPIO_Port GPIOA
#define LinearL_4_Pin GPIO_PIN_10
#define LinearL_4_GPIO_Port GPIOC
#define LinearR_0_Pin GPIO_PIN_11
#define LinearR_0_GPIO_Port GPIOC
#define LinearR_4_Pin GPIO_PIN_12
#define LinearR_4_GPIO_Port GPIOC
#define LinearL_0_Pin GPIO_PIN_2
#define LinearL_0_GPIO_Port GPIOD
#define RF_TX_Pin GPIO_PIN_3
#define RF_TX_GPIO_Port GPIOB
#define LinearL_9_Pin GPIO_PIN_4
#define LinearL_9_GPIO_Port GPIOB
#define LinearR_10_Pin GPIO_PIN_5
#define LinearR_10_GPIO_Port GPIOB
#define LinearL_10_Pin GPIO_PIN_6
#define LinearL_10_GPIO_Port GPIOB
#define MotorP_1_Pin GPIO_PIN_7
#define MotorP_1_GPIO_Port GPIOB
#define LinearL_11_Pin GPIO_PIN_9
#define LinearL_11_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
