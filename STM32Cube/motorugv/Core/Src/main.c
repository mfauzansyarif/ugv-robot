/* USER CODE BEGIN Header */
/**testes
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
#include <stdarg.h>

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

#define SPI_FRAME_LEN       (1U + JUMLAH_ACTUATOR + 2U)  /* speed + 12 actuator + flamp + blamp = 15 byte, SAMA persis field UART */

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

I2C_HandleTypeDef hi2c1;

UART_HandleTypeDef hlpuart1;
UART_HandleTypeDef huart3;

SPI_HandleTypeDef hspi1;

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

/* ---- Komunikasi I2C1 (dari Jetson, SLAVE - pengganti rencana SPI) ---- */
uint8_t i2cFrameKerja[SPI_FRAME_LEN];
uint8_t i2cTxBuf[SPI_FRAME_LEN];
uint8_t i2cRxBuf[SPI_FRAME_LEN];
volatile uint8_t i2cFrameSiap = 0;
volatile uint32_t waktuFrameI2cValidTerakhir = 0;



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
static void MX_SPI1_Init(void);
static void MX_I2C1_Init(void);
/* USER CODE BEGIN PFP */

static void SetActuator(uint8_t index, int8_t dir);
static void StopSemuaActuator(void);

static void setPulseFreq(TIM_HandleTypeDef *htim, uint32_t channel, int32_t speed);
static void setPulseFreqN(TIM_HandleTypeDef *htim, uint32_t channel, int32_t speed);
static void setMotor(uint8_t index, int32_t speedWheelSpace);
static void stopSemuaMotor(void);

static void Lamp_SetBrightness(uint8_t percent);
static void setLampuBelakang(uint8_t state);

static uint8_t ParseLong(const char *token, long *hasil);
static uint8_t ProsesFrame8(char *baris);
static uint8_t ProsesFrameI2c(const uint8_t *frame);
static void CekWatchdog(void);

static void DebugPrint(const char *format, ...);


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

static void StopSemuaActuator(void) {
    for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
        SetActuator(i, 0);
    }
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
    * Frame: "<speed> <steer_fd> <steer_fk> <steer_bd> <steer_bk> <fbody_ki> <fbody_ka> <bbody_ki> <bbody_ka> <rarm_depan> <rarm_belakang> <larm_depan> <larm_belakang> <flamp> <blamp>\n"
    * 15 field: 1 speed + 12 actuator individual (urutan = enum ACT_* di atas) + 2 lampu.
    */
   #define JUMLAH_FIELD_FRAME  (1U + JUMLAH_ACTUATOR + 2U)

   static uint8_t ProsesFrame8(char *baris) {
       char *token[JUMLAH_FIELD_FRAME];
       uint8_t jumlahToken = 0U;

       char *tok = strtok(baris, " ");
       while (tok != NULL && jumlahToken < JUMLAH_FIELD_FRAME) {
           token[jumlahToken++] = tok;
           tok = strtok(NULL, " ");
       }
       if (tok != NULL) return 0U;
       if (jumlahToken != JUMLAH_FIELD_FRAME) return 0U;

       long speed;
       long actuatorNilai[JUMLAH_ACTUATOR];
       long flamp, blamp;

       if (!ParseLong(token[0], &speed)) return 0U;
       for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
           if (!ParseLong(token[1U + i], &actuatorNilai[i])) return 0U;
       }
       if (!ParseLong(token[1U + JUMLAH_ACTUATOR], &flamp)) return 0U;
       if (!ParseLong(token[2U + JUMLAH_ACTUATOR], &blamp)) return 0U;

       if (speed < -100 || speed > 100) return 0U;
       for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
           if (actuatorNilai[i] < -1 || actuatorNilai[i] > 1) return 0U;
       }
       if (flamp < 0 || flamp > 100) return 0U;
       if (blamp < 0 || blamp > 2) return 0U;

       for (uint8_t i = 0; i < JUMLAH_MOTOR; i++) {
           setMotor(i, (int32_t)speed);
       }
       for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
           SetActuator(i, (int8_t)actuatorNilai[i]);
       }
       Lamp_SetBrightness((uint8_t)flamp);
       setLampuBelakang((uint8_t)blamp);

       DebugPrint("Frame OK: spd=%ld act=[%ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld] flamp=%ld blamp=%ld\r\n",
                  speed,
                  actuatorNilai[0], actuatorNilai[1], actuatorNilai[2], actuatorNilai[3],
                  actuatorNilai[4], actuatorNilai[5], actuatorNilai[6], actuatorNilai[7],
                  actuatorNilai[8], actuatorNilai[9], actuatorNilai[10], actuatorNilai[11],
                  flamp, blamp);
       return 1U;
   }

   static uint8_t ProsesFrameI2c(const uint8_t *frame) {
       DebugPrint("I2C RX: %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X\r\n",
                  frame[0], frame[1], frame[2], frame[3], frame[4],
                  frame[5], frame[6], frame[7], frame[8], frame[9],
                  frame[10], frame[11], frame[12], frame[13], frame[14]);

       int8_t speed = (int8_t)frame[0];
       int8_t actuatorNilai[JUMLAH_ACTUATOR];
       for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
           actuatorNilai[i] = (int8_t)frame[1U + i];
       }
       uint8_t flamp = frame[1U + JUMLAH_ACTUATOR];
       uint8_t blamp = frame[2U + JUMLAH_ACTUATOR];

       if (speed < -100 || speed > 100) return 0U;
       for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
           if (actuatorNilai[i] < -1 || actuatorNilai[i] > 1) return 0U;
       }
       if (flamp > 100) return 0U;
       if (blamp > 2) return 0U;

       for (uint8_t i = 0; i < JUMLAH_MOTOR; i++) {
           setMotor(i, (int32_t)speed);
       }
       for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
           SetActuator(i, actuatorNilai[i]);
       }
       Lamp_SetBrightness(flamp);
       setLampuBelakang(blamp);

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

   void HAL_I2C_AddrCallback(I2C_HandleTypeDef *hi2c, uint8_t TransferDirection, uint16_t AddrMatchCode)
   {
       if (hi2c->Instance != I2C1) return;

       if (TransferDirection == I2C_DIRECTION_TRANSMIT) {
           /* Master (Jetson) mau KIRIM data ke kita - fase WRITE, command masuk */
           HAL_I2C_Slave_Seq_Receive_IT(hi2c, i2cRxBuf, SPI_FRAME_LEN, I2C_FIRST_FRAME);
       } else {
           /* Master (Jetson) mau BACA data dari kita - fase READ, balasan keluar */
           HAL_I2C_Slave_Seq_Transmit_IT(hi2c, i2cTxBuf, SPI_FRAME_LEN, I2C_LAST_FRAME);
       }
   }

   void HAL_I2C_SlaveRxCpltCallback(I2C_HandleTypeDef *hi2c)
   {
       if (hi2c->Instance != I2C1) return;

       if (i2cFrameSiap == 0) {
           memcpy(i2cFrameKerja, i2cRxBuf, SPI_FRAME_LEN);
           i2cFrameSiap = 1;
       }
   }

   void HAL_I2C_ListenCpltCallback(I2C_HandleTypeDef *hi2c)
   {
       if (hi2c->Instance != I2C1) return;

       HAL_I2C_EnableListen_IT(hi2c);
   }

   void HAL_I2C_ErrorCallback(I2C_HandleTypeDef *hi2c)
   {
       if (hi2c->Instance != I2C1) return;

       HAL_I2C_EnableListen_IT(hi2c);
   }


   static void CekWatchdog(void) {
       uint8_t uartBasi = (HAL_GetTick() - waktuFrameValidTerakhir) > WATCHDOG_MS;
       uint8_t i2cBasi  = (HAL_GetTick() - waktuFrameI2cValidTerakhir) > WATCHDOG_MS;

       if (uartBasi && i2cBasi) {
           stopSemuaMotor();
           StopSemuaActuator();
       }
   }


   /* _write: debug print (printf) keluar lewat LPUART1 (ST-LINK VCP), bukan
    * lewat SWV/ITM - jadi bisa dipakai walau Run biasa (bukan Debug session) */
   static void DebugPrint(const char *format, ...)
   {
       char buffer[128];
       va_list args;
       va_start(args, format);
       int panjang = vsnprintf(buffer, sizeof(buffer), format, args);
       va_end(args);
       HAL_UART_Transmit(&hlpuart1, (uint8_t *)buffer, (uint16_t)panjang, HAL_MAX_DELAY);
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
  MX_SPI1_Init();
  MX_I2C1_Init();
  /* USER CODE BEGIN 2 */
  stopSemuaMotor();
    StopSemuaActuator();

    HAL_TIM_PWM_Start(&htim15, TIM_CHANNEL_1);
    Lamp_SetBrightness(0);
    setLampuBelakang(LAMPU_NYALA);

    HAL_UART_Receive_IT(&huart3, &rxByte, 1);
    waktuFrameValidTerakhir = HAL_GetTick();
    memset(i2cTxBuf, 0, SPI_FRAME_LEN);
    waktuFrameI2cValidTerakhir = HAL_GetTick();
    HAL_I2C_EnableListen_IT(&hi2c1);

    DebugPrint("\r\n=== Boot OK - motorugv lampuugv actuator ===\r\n");

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

	  if (i2cFrameSiap) {
		  uint8_t salinanI2cLokal[SPI_FRAME_LEN];
		  memcpy(salinanI2cLokal, i2cFrameKerja, SPI_FRAME_LEN);
		  i2cFrameSiap = 0;
		  uint8_t valid = ProsesFrameI2c(salinanI2cLokal);
		  i2cTxBuf[0] = valid;
		  if (valid) {
			  waktuFrameI2cValidTerakhir = HAL_GetTick();
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
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C1_Init(void)
{

  /* USER CODE BEGIN I2C1_Init 0 */

  /* USER CODE END I2C1_Init 0 */

  /* USER CODE BEGIN I2C1_Init 1 */

  /* USER CODE END I2C1_Init 1 */
  hi2c1.Instance = I2C1;
  hi2c1.Init.Timing = 0x00000E14;
  hi2c1.Init.OwnAddress1 = 32;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2 = 0;
  hi2c1.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure Analogue filter
  */
  if (HAL_I2CEx_ConfigAnalogFilter(&hi2c1, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure Digital filter
  */
  if (HAL_I2CEx_ConfigDigitalFilter(&hi2c1, 0) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C1_Init 2 */

  /* USER CODE END I2C1_Init 2 */

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
  hlpuart1.Init.ClockPrescaler = UART_PRESCALER_DIV1;
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
  * @brief SPI1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_SPI1_Init(void)
{

  /* USER CODE BEGIN SPI1_Init 0 */

  /* USER CODE END SPI1_Init 0 */

  SPI_AutonomousModeConfTypeDef HAL_SPI_AutonomousMode_Cfg_Struct = {0};

  /* USER CODE BEGIN SPI1_Init 1 */

  /* USER CODE END SPI1_Init 1 */
  /* SPI1 parameter configuration*/
  hspi1.Instance = SPI1;
  hspi1.Init.Mode = SPI_MODE_SLAVE;
  hspi1.Init.Direction = SPI_DIRECTION_2LINES;
  hspi1.Init.DataSize = SPI_DATASIZE_8BIT;
  hspi1.Init.CLKPolarity = SPI_POLARITY_LOW;
  hspi1.Init.CLKPhase = SPI_PHASE_1EDGE;
  hspi1.Init.NSS = SPI_NSS_HARD_INPUT;
  hspi1.Init.FirstBit = SPI_FIRSTBIT_MSB;
  hspi1.Init.TIMode = SPI_TIMODE_DISABLE;
  hspi1.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
  hspi1.Init.CRCPolynomial = 0x7;
  hspi1.Init.NSSPMode = SPI_NSS_PULSE_DISABLE;
  hspi1.Init.NSSPolarity = SPI_NSS_POLARITY_LOW;
  hspi1.Init.FifoThreshold = SPI_FIFO_THRESHOLD_01DATA;
  hspi1.Init.MasterSSIdleness = SPI_MASTER_SS_IDLENESS_00CYCLE;
  hspi1.Init.MasterInterDataIdleness = SPI_MASTER_INTERDATA_IDLENESS_00CYCLE;
  hspi1.Init.MasterReceiverAutoSusp = SPI_MASTER_RX_AUTOSUSP_DISABLE;
  hspi1.Init.MasterKeepIOState = SPI_MASTER_KEEP_IO_STATE_DISABLE;
  hspi1.Init.IOSwap = SPI_IO_SWAP_DISABLE;
  hspi1.Init.ReadyMasterManagement = SPI_RDY_MASTER_MANAGEMENT_INTERNALLY;
  hspi1.Init.ReadyPolarity = SPI_RDY_POLARITY_HIGH;
  if (HAL_SPI_Init(&hspi1) != HAL_OK)
  {
    Error_Handler();
  }
  HAL_SPI_AutonomousMode_Cfg_Struct.TriggerState = SPI_AUTO_MODE_DISABLE;
  HAL_SPI_AutonomousMode_Cfg_Struct.TriggerSelection = SPI_GRP1_GPDMA_CH0_TCF_TRG;
  HAL_SPI_AutonomousMode_Cfg_Struct.TriggerPolarity = SPI_TRIG_POLARITY_RISING;
  if (HAL_SPIEx_SetConfigAutonomousMode(&hspi1, &HAL_SPI_AutonomousMode_Cfg_Struct) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN SPI1_Init 2 */

  /* USER CODE END SPI1_Init 2 */

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
  * @param None
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
