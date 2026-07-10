/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
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
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <string.h>
#include <stdlib.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define LAMP_PWM_ARR   3999U   /* 4MHz / (0+1) / (3999+1) = 1000 Hz PWM freq */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

TIM_HandleTypeDef htim15;

UART_HandleTypeDef huart3;

/* USER CODE BEGIN PV */
uint8_t rxByte;
char rxBuffer[32];
volatile uint8_t rxIndex = 0;
volatile uint8_t frameSiap = 0;
char frameKerja[32];

#define BLINK_INTERVAL_MS   250
#define LAMPU_MATI    0
#define LAMPU_NYALA   1
#define LAMPU_KEDIP   2

volatile uint8_t statusLampuBelakang = LAMPU_NYALA;  // default nyala pas boot
uint32_t waktuBlinkTerakhir = 0;
uint8_t statusBlinkSekarang = 0;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
#define BLINK_INTERVAL_MS   250   // 250ms toggle = 2Hz kedip penuh
volatile uint8_t sedangMundur = 0;
uint32_t waktuBlinkTerakhir = 0;
uint8_t statusBlinkSekarang = 0;

void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_TIM15_Init(void);
static void MX_USART3_UART_Init(void);
/* USER CODE BEGIN PFP */
static void Lamp_SetBrightness(uint8_t percent);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/**
  * @brief Atur brightness lampu (0-100%) via duty cycle TIM15 CH1
  * @param percent: 0 = mati total, 100 = full bright
  */
static void Lamp_SetBrightness(uint8_t percent)
{
    if (percent > 100U) percent = 100U;   /* clamp, jaga-jaga input di luar batas */

    /* CCR = persen dari ARR. +1 di ARR karena period dihitung dari 0 s.d ARR
     * inklusif (ARR+1 total step) */
    uint32_t ccr = ((uint32_t)percent * (LAMP_PWM_ARR + 1U)) / 100U;

    __HAL_TIM_SET_COMPARE(&htim15, TIM_CHANNEL_1, ccr);
}

static void setLampuBelakang(uint8_t mundur) {
	static void setLampuBelakang(uint8_t state) {
	    if (state > LAMPU_KEDIP) state = LAMPU_KEDIP;  // clamp, jaga-jaga input aneh
	    statusLampuBelakang = state;

	    if (state == LAMPU_MATI) {
	        HAL_GPIO_WritePin(GPIOF, GPIO_PIN_8, GPIO_PIN_RESET);
	    } else if (state == LAMPU_NYALA) {
	        HAL_GPIO_WritePin(GPIOF, GPIO_PIN_8, GPIO_PIN_SET);
	    }
	    // kalau LAMPU_KEDIP: gak set pin di sini, biar while(1) yang toggle terus
	}
    }
    // kalau mundur=1, biarin while(1) yang urus kedipnya
}

static void prosesFrame(char *baris) {
    char *token[2];
    uint8_t jumlahToken = 0;
    char *tok = strtok(baris, " ");
    while (tok != NULL && jumlahToken < 2) {
        token[jumlahToken++] = tok;
        tok = strtok(NULL, " ");
    }
    if (jumlahToken != 2) return;
    if (tok != NULL) return;

    char *endptr;
    long val = strtol(token[1], &endptr, 10);
    if (endptr == token[1] || *endptr != '\0') return;

    if (strcmp(token[0], "L") == 0) {
        if (val < 0) val = 0;
        if (val > 100) val = 100;
        Lamp_SetBrightness((uint8_t)val);
        printf("Lamp OK: %ld%%\r\n", val);
    } else if (strcmp(token[0], "R") == 0) {
        setLampuBelakang((uint8_t)val);
        printf("Lampu belakang: %ld\r\n", val);
    }

}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance != USART3) return;
    char c = (char)rxByte;
    if (c == '\n') {
        rxBuffer[rxIndex] = '\0';
        if (frameSiap == 0) {
            strncpy(frameKerja, rxBuffer, sizeof(frameKerja) - 1);
            frameKerja[sizeof(frameKerja) - 1] = '\0';
            frameSiap = 1;
        }
        rxIndex = 0;
    } else if (c != '\r') {
        if (rxIndex < sizeof(rxBuffer) - 1) {
            rxBuffer[rxIndex++] = c;
        } else {
            rxIndex = 0;
        }
    }
    HAL_UART_Receive_IT(&huart3, &rxByte, 1);
}

int _write(int file, char *ptr, int len) {
    for (int i = 0; i < len; i++) {
        ITM_SendChar(*ptr++);
    }
    return len;
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_TIM15_Init();
  MX_USART3_UART_Init();
  /* USER CODE BEGIN 2 */

  /* Mulai PWM di channel 1 (PF9) - WAJIB dipanggil manual, CubeMX cuma
   * generate init-nya doang, gak auto-start */
  HAL_TIM_PWM_Start(&htim15, TIM_CHANNEL_1);

  /* Default aman saat boot: lampu OFF dulu, jangan langsung nyala full
   * sebelum ada command eksplisit dari GCS */
  Lamp_SetBrightness(0);
  setLampuBelakang(LAMPU_NYALA);   // <- tambahin ini: default nyala (mundur=0)
  HAL_UART_Receive_IT(&huart3, &rxByte, 1);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)

  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */

	  if (frameSiap) {
	      char salinanLokal[32];
	      strncpy(salinanLokal, frameKerja, sizeof(salinanLokal) - 1);
	      salinanLokal[sizeof(salinanLokal) - 1] = '\0';
	      frameSiap = 0;
	      prosesFrame(salinanLokal);
	  }

	  if (statusLampuBelakang == LAMPU_KEDIP) {
	      if (HAL_GetTick() - waktuBlinkTerakhir >= BLINK_INTERVAL_MS) {
	          statusBlinkSekarang = !statusBlinkSekarang;
	          HAL_GPIO_WritePin(GPIOF, GPIO_PIN_8,
	              statusBlinkSekarang ? GPIO_PIN_SET : GPIO_PIN_RESET);
	          waktuBlinkTerakhir = HAL_GetTick();
	      }
	  }
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  if (HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE4) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_MSI;
  RCC_OscInitStruct.MSIState = RCC_MSI_ON;
  RCC_OscInitStruct.MSICalibrationValue = RCC_MSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.MSIClockRange = RCC_MSIRANGE_4;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2
                              |RCC_CLOCKTYPE_PCLK3;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_MSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB3CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief TIM15 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM15_Init(void)
{

  /* USER CODE BEGIN TIM15_Init 0 */

  /* USER CODE END TIM15_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};

  /* USER CODE BEGIN TIM15_Init 1 */

  /* USER CODE END TIM15_Init 1 */
  htim15.Instance = TIM15;
  htim15.Init.Prescaler = 0;
  htim15.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim15.Init.Period = 65535;
  htim15.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim15.Init.RepetitionCounter = 0;
  htim15.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_PWM_Init(&htim15) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim15, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_PWM_ConfigChannel(&htim15, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  sBreakDeadTimeConfig.OffStateRunMode = TIM_OSSR_DISABLE;
  sBreakDeadTimeConfig.OffStateIDLEMode = TIM_OSSI_DISABLE;
  sBreakDeadTimeConfig.LockLevel = TIM_LOCKLEVEL_OFF;
  sBreakDeadTimeConfig.DeadTime = 0;
  sBreakDeadTimeConfig.BreakState = TIM_BREAK_DISABLE;
  sBreakDeadTimeConfig.BreakPolarity = TIM_BREAKPOLARITY_HIGH;
  sBreakDeadTimeConfig.BreakFilter = 0;
  sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim15, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM15_Init 2 */

  /* USER CODE END TIM15_Init 2 */
  HAL_TIM_MspPostInit(&htim15);

}

/**
  * @brief USART3 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART3_UART_Init(void)
{

  /* USER CODE BEGIN USART3_Init 0 */

  /* USER CODE END USART3_Init 0 */

  /* USER CODE BEGIN USART3_Init 1 */

  /* USER CODE END USART3_Init 1 */
  huart3.Instance = USART3;
  huart3.Init.BaudRate = 57600;
  huart3.Init.WordLength = UART_WORDLENGTH_8B;
  huart3.Init.StopBits = UART_STOPBITS_1;
  huart3.Init.Parity = UART_PARITY_NONE;
  huart3.Init.Mode = UART_MODE_TX_RX;
  huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart3.Init.OverSampling = UART_OVERSAMPLING_16;
  huart3.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart3.Init.ClockPrescaler = UART_PRESCALER_DIV1;
  huart3.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart3) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetTxFifoThreshold(&huart3, UART_TXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetRxFifoThreshold(&huart3, UART_RXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_DisableFifoMode(&huart3) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART3_Init 2 */

  /* USER CODE END USART3_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOF_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOF, GPIO_PIN_8, GPIO_PIN_RESET);

  /*Configure GPIO pin : PF8 */
  GPIO_InitStruct.Pin = GPIO_PIN_8;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOF, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
