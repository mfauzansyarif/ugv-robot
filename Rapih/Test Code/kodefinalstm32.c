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
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define JUMLAH_MOTOR        4U
#define FREQ_PER_RPM        50U
#define TIMER_CLOCK_HZ      4000000UL
#define WATCHDOG_MS         300U

#define JUMLAH_ACTUATOR     12U

#define LAMP_PWM_ARR        3999U   /* 4MHz/4000 = 1kHz */

#define BLINK_INTERVAL_MS   250U
#define LAMPU_MATI          0U
#define LAMPU_NYALA         1U
#define LAMPU_KEDIP         2U
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

UART_HandleTypeDef hlpuart1;
UART_HandleTypeDef huart3;

TIM_HandleTypeDef htim1;
TIM_HandleTypeDef htim8;
TIM_HandleTypeDef htim15;
TIM_HandleTypeDef htim16;
TIM_HandleTypeDef htim17;

/* USER CODE BEGIN PV */
/* ---- Motor BLAC ---- */
static const int8_t ARAH_FISIK_MOTOR[JUMLAH_MOTOR] = {1, -1, 1, -1};

/* ---- Komunikasi USART3 (dari Jetson) ---- */
uint8_t rxByte;
char rxBuffer[80];
volatile uint8_t rxIndex = 0;
volatile uint8_t frameSiap = 0;
char frameKerja[80];
volatile uint32_t waktuFrameValidTerakhir = 0;

/* ---- Lampu belakang (nyala/mati/kedip) ---- */
volatile uint8_t statusLampuBelakang = LAMPU_NYALA;
uint32_t waktuBlinkTerakhir = 0;
uint8_t statusBlinkSekarang = 0;

/* ---- 12 Actuator BTS7960 ----
 * PERBAIKAN dari desain awal: RPWM dan LPWM bisa beda PORT (index 5:
 * RPWM di GPIOG, LPWM di GPIOD, karena PG11 gak ada fisik di package
 * LQFP144 ini) - jadi struct butuh 2 field port terpisah, bukan 1. */
typedef struct {
    GPIO_TypeDef *portRPWM;
    uint16_t      pinRPWM;
    GPIO_TypeDef *portLPWM;
    uint16_t      pinLPWM;
} ActuatorPin_t;

static const ActuatorPin_t actuatorTable[JUMLAH_ACTUATOR] = {
    /* 0: Steer Depan Kiri     */ { GPIOG, GPIO_PIN_0,  GPIOG, GPIO_PIN_1  },
    /* 1: Steer Depan Kanan    */ { GPIOG, GPIO_PIN_2,  GPIOG, GPIO_PIN_3  }, /* PG2=LD3 onboard */
    /* 2: Steer Belakang Kiri  */ { GPIOG, GPIO_PIN_4,  GPIOG, GPIO_PIN_5  },
    /* 3: Steer Belakang Kanan */ { GPIOG, GPIO_PIN_6,  GPIOG, GPIO_PIN_7  },
    /* 4: FBody Kiri           */ { GPIOG, GPIO_PIN_8,  GPIOG, GPIO_PIN_9  },
    /* 5: FBody Kanan          */ { GPIOG, GPIO_PIN_10, GPIOD, GPIO_PIN_8  }, /* LPWM di port beda! */
    /* 6: BBody Kiri           */ { GPIOG, GPIO_PIN_12, GPIOG, GPIO_PIN_13 },
    /* 7: BBody Kanan          */ { GPIOG, GPIO_PIN_14, GPIOG, GPIO_PIN_15 },
    /* 8: RArm Depan           */ { GPIOD, GPIO_PIN_0,  GPIOD, GPIO_PIN_1  },
    /* 9: RArm Belakang        */ { GPIOD, GPIO_PIN_2,  GPIOD, GPIO_PIN_3  },
    /*10: LArm Depan           */ { GPIOD, GPIO_PIN_4,  GPIOD, GPIO_PIN_5  },
    /*11: LArm Belakang        */ { GPIOD, GPIO_PIN_6,  GPIOD, GPIO_PIN_7  },
};

enum {
    ACT_STEER_FD = 0, ACT_STEER_FK = 1, ACT_STEER_BD = 2, ACT_STEER_BK = 3,
    ACT_FBODY_KI = 4, ACT_FBODY_KA = 5,
    ACT_BBODY_KI = 6, ACT_BBODY_KA = 7,
    ACT_RARM_DEPAN = 8, ACT_RARM_BELAKANG = 9,
    ACT_LARM_DEPAN = 10, ACT_LARM_BELAKANG = 11,
};

/* TODO: proteksi stall - durasi maks HIGH per actuator belum ditentukan.
 * Isi array ini nanti kalau sudah ada angka pasti dari tes fisik, lalu
 * tambah pengecekan di main loop mirip CekWatchdog(). */
static uint32_t waktuMulaiAktif[JUMLAH_ACTUATOR];
static int8_t   arahTerakhir[JUMLAH_ACTUATOR];


/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_TIM8_Init(void);
static void MX_USART3_UART_Init(void);
static void MX_TIM1_Init(void);
static void MX_TIM16_Init(void);
static void MX_TIM17_Init(void);
static void MX_LPUART1_UART_Init(void);
static void MX_TIM15_Init(void);
/* USER CODE BEGIN PFP */

static void SetActuator(uint8_t index, int8_t dir);
static void SetSteer(int8_t dir);
static void SetFBody(int8_t dir);
static void SetBBody(int8_t dir);
static void SetRArm(int8_t dir);
static void SetLArm(int8_t dir);
static void StopSemuaActuator(void);

static void setPulseFreq(TIM_HandleTypeDef *htim, uint32_t channel, int32_t speed);
static void setPulseFreqN(TIM_HandleTypeDef *htim, uint32_t channel, int32_t speed);
static void setMotor(uint8_t index, int32_t speedWheelSpace);
static void stopSemuaMotor(void);

static void Lamp_SetBrightness(uint8_t percent);
static void setLampuBelakang(uint8_t state);

static uint8_t ParseLong(const char *token, long *hasil);
static uint8_t ProsesFrame8(char *baris);
static void CekWatchdog(void);


/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/* ============================================================================
 * LAYER 1 - nyentuh hardware langsung
 * ==========================================================================*/

static void SetActuator(uint8_t index, int8_t dir) {
    if (index >= JUMLAH_ACTUATOR) return;
    const ActuatorPin_t *a = &actuatorTable[index];

    if (dir > 0) {
        HAL_GPIO_WritePin(a->portRPWM, a->pinRPWM, GPIO_PIN_SET);
        HAL_GPIO_WritePin(a->portLPWM, a->pinLPWM, GPIO_PIN_RESET);
    } else if (dir < 0) {
        HAL_GPIO_WritePin(a->portRPWM, a->pinRPWM, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(a->portLPWM, a->pinLPWM, GPIO_PIN_SET);
    } else {
        HAL_GPIO_WritePin(a->portRPWM, a->pinRPWM, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(a->portLPWM, a->pinLPWM, GPIO_PIN_RESET);
    }

    if (dir != arahTerakhir[index]) {
           waktuMulaiAktif[index] = HAL_GetTick();
           arahTerakhir[index] = dir;
       }
   }

static void setPulseFreq(TIM_HandleTypeDef *htim, uint32_t channel, int32_t speed) {
    if (speed == 0) {
        HAL_TIM_OC_Stop(htim, channel);
        return;
    }
    uint32_t freqHz = (uint32_t)(abs(speed)) * FREQ_PER_RPM;
    uint32_t maxArr = 65535UL;
    uint32_t prescaler = 1;
    uint32_t arr;
    do {
        arr = (TIMER_CLOCK_HZ / (2UL * prescaler * freqHz));
        if (arr > 0) arr -= 1;
        if (arr <= maxArr) break;
        prescaler *= 2;
    } while (prescaler < 65536UL);
    __HAL_TIM_SET_PRESCALER(htim, prescaler - 1);
    __HAL_TIM_SET_AUTORELOAD(htim, arr);
    HAL_TIM_OC_Start(htim, channel);
}



static void setPulseFreqN(TIM_HandleTypeDef *htim, uint32_t channel, int32_t speed) {
    if (speed == 0) {
        HAL_TIMEx_OCN_Stop(htim, channel);
        return;
    }
    uint32_t freqHz = (uint32_t)(abs(speed)) * FREQ_PER_RPM;
    uint32_t prescaler = 1;
    uint32_t arr;
    do {
        arr = (TIMER_CLOCK_HZ / (2UL * prescaler * freqHz));
        if (arr > 0) arr -= 1;
        if (arr <= 65535UL) break;
        prescaler *= 2;
    } while (prescaler < 65536UL);
    __HAL_TIM_SET_PRESCALER(htim, prescaler - 1);
    __HAL_TIM_SET_AUTORELOAD(htim, arr);
    HAL_TIMEx_OCN_Start(htim, channel);
}

static void Lamp_SetBrightness(uint8_t percent) {
    if (percent > 100U) percent = 100U;
    uint32_t ccr = ((uint32_t)percent * (LAMP_PWM_ARR + 1U)) / 100U;
    __HAL_TIM_SET_COMPARE(&htim15, TIM_CHANNEL_1, ccr);
}

/* ============================================================================
 * LAYER 2 - grouping, manggil Layer 1
 * ==========================================================================*/

static void SetSteer(int8_t dir) {
    /* REVISI: dir=1 (kanan) -> sisi KANAN extend, sisi KIRI retract */
    SetActuator(ACT_STEER_FK, dir);
    SetActuator(ACT_STEER_BK, dir);
    SetActuator(ACT_STEER_FD, (int8_t)(-dir));
    SetActuator(ACT_STEER_BD, (int8_t)(-dir));
}

static void SetFBody(int8_t dir) {
    SetActuator(ACT_FBODY_KI, dir);
    SetActuator(ACT_FBODY_KA, dir);
}

static void SetBBody(int8_t dir) {
    SetActuator(ACT_BBODY_KI, dir);
    SetActuator(ACT_BBODY_KA, dir);
}

static void SetRArm(int8_t dir) {
    SetActuator(ACT_RARM_DEPAN, dir);
    SetActuator(ACT_RARM_BELAKANG, dir);
}

static void SetLArm(int8_t dir) {
    SetActuator(ACT_LARM_DEPAN, dir);
    SetActuator(ACT_LARM_BELAKANG, dir);
}

static void StopSemuaActuator(void) {
    SetSteer(0);
    SetFBody(0);
    SetBBody(0);
    SetRArm(0);
    SetLArm(0);
}

static void setMotor(uint8_t index, int32_t speedWheelSpace) {
    if (speedWheelSpace > 100) speedWheelSpace = 100;
    if (speedWheelSpace < -100) speedWheelSpace = -100;
    int8_t arahPulsa = (speedWheelSpace >= 0 ? 1 : -1) * ARAH_FISIK_MOTOR[index];
    GPIO_PinState levelSign = (arahPulsa >= 0) ? GPIO_PIN_SET : GPIO_PIN_RESET;
    switch (index) {
        case 0:
            HAL_GPIO_WritePin(SING_KIRI_DEPAN_GPIO_Port, SING_KIRI_DEPAN_Pin, levelSign);
            setPulseFreq(&htim16, TIM_CHANNEL_1, speedWheelSpace);
            break;
        case 1:
            HAL_GPIO_WritePin(SIGN_KANAN_DEPAN_GPIO_Port, SIGN_KANAN_DEPAN_Pin, levelSign);
            setPulseFreq(&htim8, TIM_CHANNEL_1, speedWheelSpace);
            break;
        case 2:
            HAL_GPIO_WritePin(SIGN_KIRI_BELAKANG_GPIO_Port, SIGN_KIRI_BELAKANG_Pin, levelSign);
            setPulseFreq(&htim1, TIM_CHANNEL_1, speedWheelSpace);
            break;
        case 3:
            HAL_GPIO_WritePin(SIGN_KANAN_BELAKANG_GPIO_Port, SIGN_KANAN_BELAKANG_Pin, levelSign);
            setPulseFreqN(&htim17, TIM_CHANNEL_1, speedWheelSpace);
            break;
        default:
            break;
    }
}


static void stopSemuaMotor(void) {
    for (uint8_t i = 0; i < JUMLAH_MOTOR; i++) {
        setMotor(i, 0);
    }
}

static void setLampuBelakang(uint8_t state) {
    if (state > LAMPU_KEDIP) state = LAMPU_KEDIP;
    statusLampuBelakang = state;
    if (state == LAMPU_MATI) {
        HAL_GPIO_WritePin(GPIOF, GPIO_PIN_8, GPIO_PIN_RESET);
    } else if (state == LAMPU_NYALA) {
        HAL_GPIO_WritePin(GPIOF, GPIO_PIN_8, GPIO_PIN_SET);
    }
    /* LAMPU_KEDIP: gak set pin di sini, main loop yang toggle */
}
    /* ============================================================================
     * LAYER 3 - parsing & keputusan
     * ==========================================================================*/


   static uint8_t ParseLong(const char *token, long *hasil) {
        char *endptr;
        long val = strtol(token, &endptr, 10);
        if (endptr == token || *endptr != '\0') return 0U;
        *hasil = val;
        return 1U;
    }

   /**
    * Frame: "<speed> <steer> <fbody> <bbody> <rarm> <larm> <flamp> <blamp>\n"
    */
   static uint8_t ProsesFrame8(char *baris) {
       char *token[8];
       uint8_t jumlahToken = 0U;

       char *tok = strtok(baris, " ");
       while (tok != NULL && jumlahToken < 8U) {
           token[jumlahToken++] = tok;
           tok = strtok(NULL, " ");
       }
       if (tok != NULL) return 0U;
       if (jumlahToken != 8U) return 0U;

       long speed, steer, fbody, bbody, rarm, larm, flamp, blamp;
       if (!ParseLong(token[0], &speed)) return 0U;
       if (!ParseLong(token[1], &steer)) return 0U;
       if (!ParseLong(token[2], &fbody)) return 0U;
       if (!ParseLong(token[3], &bbody)) return 0U;
       if (!ParseLong(token[4], &rarm))  return 0U;
       if (!ParseLong(token[5], &larm))  return 0U;
       if (!ParseLong(token[6], &flamp)) return 0U;
       if (!ParseLong(token[7], &blamp)) return 0U;

       if (speed < -100 || speed > 100) return 0U;
       if (steer < -1 || steer > 1) return 0U;
       if (fbody < -1 || fbody > 1) return 0U;
       if (bbody < -1 || bbody > 1) return 0U;
       if (rarm  < -1 || rarm  > 1) return 0U;
       if (larm  < -1 || larm  > 1) return 0U;
       if (flamp < 0 || flamp > 100) return 0U;
       if (blamp < 0 || blamp > 2) return 0U;

       for (uint8_t i = 0; i < JUMLAH_MOTOR; i++) {
           setMotor(i, (int32_t)speed);
       }
       SetSteer((int8_t)steer);
       SetFBody((int8_t)fbody);
       SetBBody((int8_t)bbody);
       SetRArm((int8_t)rarm);
       SetLArm((int8_t)larm);
       Lamp_SetBrightness((uint8_t)flamp);
       setLampuBelakang((uint8_t)blamp);

       printf("Frame OK: spd=%ld steer=%ld fbody=%ld bbody=%ld rarm=%ld larm=%ld flamp=%ld blamp=%ld\r\n",
              speed, steer, fbody, bbody, rarm, larm, flamp, blamp);
       return 1U;
   }



   /* ============================================================================
    * LAYER 4 - komunikasi & housekeeping
    * ==========================================================================*/

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


   static void CekWatchdog(void) {
       if (HAL_GetTick() - waktuFrameValidTerakhir > WATCHDOG_MS) {
           stopSemuaMotor();
           StopSemuaActuator();
           /* Lampu SENGAJA tidak disentuh - tetap di kondisi terakhir */
       }
   }

   /* _write: debug print (printf) keluar lewat LPUART1 (ST-LINK VCP), bukan
    * lewat SWV/ITM - jadi bisa dipakai walau Run biasa (bukan Debug session) */
   int _write(int file, char *ptr, int len) {
       HAL_UART_Transmit(&hlpuart1, (uint8_t *)ptr, (uint16_t)len, 100U);
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
  MX_TIM8_Init();
  MX_USART3_UART_Init();
  MX_TIM1_Init();
  MX_TIM16_Init();
  MX_TIM17_Init();
  MX_LPUART1_UART_Init();
  MX_TIM15_Init();
  /* USER CODE BEGIN 2 */
  stopSemuaMotor();
    StopSemuaActuator();

    HAL_TIM_PWM_Start(&htim15, TIM_CHANNEL_1);
    Lamp_SetBrightness(0);
    setLampuBelakang(LAMPU_NYALA);

    HAL_UART_Receive_IT(&huart3, &rxByte, 1);
    waktuFrameValidTerakhir = HAL_GetTick();

    printf("\r\n=== Boot OK - motorugv lampuugv actuator ===\r\n");
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {


	  if (frameSiap) {
	         char salinanLokal[80];
	         strncpy(salinanLokal, frameKerja, sizeof(salinanLokal) - 1);
	         salinanLokal[sizeof(salinanLokal) - 1] = '\0';
	         frameSiap = 0;
	         if (ProsesFrame8(salinanLokal)) {
	             waktuFrameValidTerakhir = HAL_GetTick();
	         }
	     }

	     CekWatchdog();

	     if (statusLampuBelakang == LAMPU_KEDIP) {
	         if (HAL_GetTick() - waktuBlinkTerakhir >= BLINK_INTERVAL_MS) {
	             statusBlinkSekarang = !statusBlinkSekarang;
	             HAL_GPIO_WritePin(GPIOF, GPIO_PIN_8,
	                 statusBlinkSekarang ? GPIO_PIN_SET : GPIO_PIN_RESET);
	             waktuBlinkTerakhir = HAL_GetTick();
	         }
	     }
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
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
  * @brief LPUART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_LPUART1_UART_Init(void)
{

  /* USER CODE BEGIN LPUART1_Init 0 */

  /* USER CODE END LPUART1_Init 0 */

  /* USER CODE BEGIN LPUART1_Init 1 */

  /* USER CODE END LPUART1_Init 1 */
  hlpuart1.Instance = LPUART1;
  hlpuart1.Init.BaudRate = 115200;
  hlpuart1.Init.WordLength = UART_WORDLENGTH_8B;
  hlpuart1.Init.StopBits = UART_STOPBITS_1;
  hlpuart1.Init.Parity = UART_PARITY_NONE;
  hlpuart1.Init.Mode = UART_MODE_TX_RX;
  hlpuart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  hlpuart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  hlpuart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  hlpuart1.FifoMode = UART_FIFOMODE_DISABLE;
  if (HAL_UART_Init(&hlpuart1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetTxFifoThreshold(&hlpuart1, UART_TXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetRxFifoThreshold(&hlpuart1, UART_RXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_DisableFifoMode(&hlpuart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN LPUART1_Init 2 */

  /* USER CODE END LPUART1_Init 2 */

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
  * @brief TIM1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM1_Init(void)
{

  /* USER CODE BEGIN TIM1_Init 0 */

  /* USER CODE END TIM1_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};

  /* USER CODE BEGIN TIM1_Init 1 */

  /* USER CODE END TIM1_Init 1 */
  htim1.Instance = TIM1;
  htim1.Init.Prescaler = 0;
  htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim1.Init.Period = 65535;
  htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim1.Init.RepetitionCounter = 0;
  htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_OC_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterOutputTrigger2 = TIM_TRGO2_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_TOGGLE;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_OC_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
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
  sBreakDeadTimeConfig.BreakAFMode = TIM_BREAK_AFMODE_INPUT;
  sBreakDeadTimeConfig.Break2State = TIM_BREAK2_DISABLE;
  sBreakDeadTimeConfig.Break2Polarity = TIM_BREAK2POLARITY_HIGH;
  sBreakDeadTimeConfig.Break2Filter = 0;
  sBreakDeadTimeConfig.Break2AFMode = TIM_BREAK_AFMODE_INPUT;
  sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim1, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM1_Init 2 */

  /* USER CODE END TIM1_Init 2 */
  HAL_TIM_MspPostInit(&htim1);

}

/**
  * @brief TIM8 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM8_Init(void)
{

  /* USER CODE BEGIN TIM8_Init 0 */

  /* USER CODE END TIM8_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};

  /* USER CODE BEGIN TIM8_Init 1 */

  /* USER CODE END TIM8_Init 1 */
  htim8.Instance = TIM8;
  htim8.Init.Prescaler = 0;
  htim8.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim8.Init.Period = 65535;
  htim8.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim8.Init.RepetitionCounter = 0;
  htim8.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_OC_Init(&htim8) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterOutputTrigger2 = TIM_TRGO2_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim8, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_TOGGLE;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_OC_ConfigChannel(&htim8, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
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
  sBreakDeadTimeConfig.BreakAFMode = TIM_BREAK_AFMODE_INPUT;
  sBreakDeadTimeConfig.Break2State = TIM_BREAK2_DISABLE;
  sBreakDeadTimeConfig.Break2Polarity = TIM_BREAK2POLARITY_HIGH;
  sBreakDeadTimeConfig.Break2Filter = 0;
  sBreakDeadTimeConfig.Break2AFMode = TIM_BREAK_AFMODE_INPUT;
  sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim8, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM8_Init 2 */

  /* USER CODE END TIM8_Init 2 */
  HAL_TIM_MspPostInit(&htim8);

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
  * @brief TIM16 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM16_Init(void)
{

  /* USER CODE BEGIN TIM16_Init 0 */

  /* USER CODE END TIM16_Init 0 */

  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};

  /* USER CODE BEGIN TIM16_Init 1 */

  /* USER CODE END TIM16_Init 1 */
  htim16.Instance = TIM16;
  htim16.Init.Prescaler = 0;
  htim16.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim16.Init.Period = 65535;
  htim16.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim16.Init.RepetitionCounter = 0;
  htim16.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim16) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_OC_Init(&htim16) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_TOGGLE;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_OC_ConfigChannel(&htim16, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
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
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim16, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM16_Init 2 */

  /* USER CODE END TIM16_Init 2 */
  HAL_TIM_MspPostInit(&htim16);

}

/**
  * @brief TIM17 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM17_Init(void)
{

  /* USER CODE BEGIN TIM17_Init 0 */

  /* USER CODE END TIM17_Init 0 */

  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};

  /* USER CODE BEGIN TIM17_Init 1 */

  /* USER CODE END TIM17_Init 1 */
  htim17.Instance = TIM17;
  htim17.Init.Prescaler = 0;
  htim17.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim17.Init.Period = 65535;
  htim17.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim17.Init.RepetitionCounter = 0;
  htim17.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim17) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_OC_Init(&htim17) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_TOGGLE;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_OC_ConfigChannel(&htim17, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
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
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim17, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM17_Init 2 */

  /* USER CODE END TIM17_Init 2 */
  HAL_TIM_MspPostInit(&htim17);

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
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOG_CLK_ENABLE();
  __HAL_RCC_GPIOE_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOF, GPIO_PIN_8|SING_KIRI_DEPAN_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(SIGN_KANAN_BELAKANG_GPIO_Port, SIGN_KANAN_BELAKANG_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOG, GPIO_PIN_0|GPIO_PIN_1|GPIO_PIN_2|GPIO_PIN_3
                          |GPIO_PIN_4|GPIO_PIN_5|GPIO_PIN_6|GPIO_PIN_7
                          |GPIO_PIN_8|GPIO_PIN_9|GPIO_PIN_10|GPIO_PIN_12
                          |GPIO_PIN_13|GPIO_PIN_14|GPIO_PIN_15, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOD, GPIO_PIN_8|SIGN_KIRI_BELAKANG_Pin|GPIO_PIN_0|GPIO_PIN_1
                          |GPIO_PIN_2|GPIO_PIN_3|GPIO_PIN_4|GPIO_PIN_5
                          |GPIO_PIN_6|GPIO_PIN_7, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(SIGN_KANAN_DEPAN_GPIO_Port, SIGN_KANAN_DEPAN_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : PF8 SING_KIRI_DEPAN_Pin */
  GPIO_InitStruct.Pin = GPIO_PIN_8|SING_KIRI_DEPAN_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOF, &GPIO_InitStruct);

  /*Configure GPIO pin : SIGN_KANAN_BELAKANG_Pin */
  GPIO_InitStruct.Pin = SIGN_KANAN_BELAKANG_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(SIGN_KANAN_BELAKANG_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : PG0 PG1 PG2 PG3
                           PG4 PG5 PG6 PG7
                           PG8 PG9 PG10 PG12
                           PG13 PG14 PG15 */
  GPIO_InitStruct.Pin = GPIO_PIN_0|GPIO_PIN_1|GPIO_PIN_2|GPIO_PIN_3
                          |GPIO_PIN_4|GPIO_PIN_5|GPIO_PIN_6|GPIO_PIN_7
                          |GPIO_PIN_8|GPIO_PIN_9|GPIO_PIN_10|GPIO_PIN_12
                          |GPIO_PIN_13|GPIO_PIN_14|GPIO_PIN_15;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOG, &GPIO_InitStruct);

  /*Configure GPIO pins : PD8 SIGN_KIRI_BELAKANG_Pin PD0 PD1
                           PD2 PD3 PD4 PD5
                           PD6 PD7 */
  GPIO_InitStruct.Pin = GPIO_PIN_8|SIGN_KIRI_BELAKANG_Pin|GPIO_PIN_0|GPIO_PIN_1
                          |GPIO_PIN_2|GPIO_PIN_3|GPIO_PIN_4|GPIO_PIN_5
                          |GPIO_PIN_6|GPIO_PIN_7;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

  /*Configure GPIO pin : SIGN_KANAN_DEPAN_Pin */
  GPIO_InitStruct.Pin = SIGN_KANAN_DEPAN_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(SIGN_KANAN_DEPAN_GPIO_Port, &GPIO_InitStruct);

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
