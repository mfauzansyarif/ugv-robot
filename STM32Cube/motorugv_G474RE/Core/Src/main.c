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
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
typedef enum {
    PANTILT_KIRI = 0,
    PANTILT_KANAN,
    PANTILT_ATAS,
    PANTILT_BAWAH,
    PANTILT_STOP
} PantiltArah_t;

typedef struct {
    uint8_t estop;
    uint8_t mode;
    int8_t  xJoy1;
    int8_t  yJoy1;
    int8_t  xJoy2;
    int8_t  yJoy2;
    int8_t  zoom;
    uint8_t lrf;
    uint8_t fLamp;
    uint8_t bLamp;
    uint8_t slipRing;
    int8_t  bodyUpDown;
    int8_t  armWidenNarrow;
    uint8_t motorIndividualId;
    int8_t  motorIndividualArah;
    uint8_t kalibrasi;
} GcsCommand_t;

/* Command final dari Jetson (Core Node udah mutusin) - lihat brief Fase 4 */
typedef struct {
    int8_t  speed;
    int8_t  act[8];
    uint8_t fLamp;
    uint8_t bLamp;
    uint8_t bLampMode;
    uint8_t pantiltArah;
    int8_t  kameraZoom;
    uint8_t slipRing;
    uint8_t lrfTrigger;
    uint8_t gcsReplyStm32Status;
    uint8_t gcsReplyLrfStatus;
    uint8_t gcsReplyLrfLsb;
    uint8_t gcsReplyLrfMsb;
} JetsonCommand_t;
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define JUMLAH_MOTOR        4U
#define JUMLAH_ACTUATOR     8U

#define FREQ_PER_RPM        50U
#define TIMER_CLOCK_HZ      170000000UL   /* HSI 16MHz -> PLL -> 170MHz, SAMA buat semua timer (APB1/APB2 prescaler 1) */

#define LAMP_PWM_ARR        3399U   /* 170MHz / (3400*50) = 1kHz, prescaler 49 (di-set manual di USER CODE 2) */

#define BLINK_INTERVAL_MS   250U
#define LAMPU_MATI          0U
#define LAMPU_NYALA         1U
#define LAMPU_KEDIP         2U

#define RS485_TIMEOUT_MS    100U
#define ALAMAT_KAMERA       1U
#define ALAMAT_BRIDGE_LRF   2U
#define CMD2_BACA_JARAK     0x01U
#define CMD2_POINTER        0x02U

#define GCS_FRAME_LEN       16U

#define JETSON_DOWN_LEN     20U  /* Jetson -> STM32: speed+8act+flamp+blamp+blampmode+pantilt+zoom+slipring+lrftrigger+4 gcsreply */
#define JETSON_UP_LEN       20U  /* STM32 -> Jetson: 16 byte relay GCS + lrf_lsb+lrf_msb+lrf_status+stm32_status */

#define LRF_TRIGGER_IDLE       0U
#define LRF_TRIGGER_BACA_JARAK 1U
#define LRF_TRIGGER_POINTER_ON 2U
#define LRF_TRIGGER_POINTER_OFF 3U

#define LINK_TIMEOUT_MS      500U  /* LED mati + failsafe stop kalau gak ada frame Jetson valid selama ini */
#define HEARTBEAT_INTERVAL_MS 500U

#define UART_TX_TIMEOUT_MS   50U   /* batas HAL_UART_Transmit - jangan HAL_MAX_DELAY, biar main loop gak bisa hang selamanya */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef hlpuart1;
UART_HandleTypeDef huart1;
UART_HandleTypeDef huart2;
UART_HandleTypeDef huart3;

TIM_HandleTypeDef htim1;
TIM_HandleTypeDef htim3;
TIM_HandleTypeDef htim4;
TIM_HandleTypeDef htim8;
TIM_HandleTypeDef htim15;

PCD_HandleTypeDef hpcd_USB_FS;

/* USER CODE BEGIN PV */
typedef struct {
    GPIO_TypeDef *portRPWM;
    uint16_t      pinRPWM;
    GPIO_TypeDef *portLPWM;
    uint16_t      pinLPWM;
} ActuatorPin_t;

static const ActuatorPin_t actuatorTable[JUMLAH_ACTUATOR] = {
    /* 0  */ { LinearR_0_GPIO_Port,  LinearR_0_Pin,  LinearL_0_GPIO_Port,  LinearL_0_Pin  },
    /* 1  */ { LinearR_1_GPIO_Port,  LinearR_1_Pin,  LinearL_1_GPIO_Port,  LinearL_1_Pin  },
    /* 2  */ { LinearR_2_GPIO_Port,  LinearR_2_Pin,  LinearL_2_GPIO_Port,  LinearL_2_Pin  },
    /* 3  */ { LinearR_3_GPIO_Port,  LinearR_3_Pin,  LinearL_3_GPIO_Port,  LinearL_3_Pin  },
    /* 4  */ { LinearR_4_GPIO_Port,  LinearR_4_Pin,  LinearL_4_GPIO_Port,  LinearL_4_Pin  },
    /* 5  */ { LinearR_5_GPIO_Port,  LinearR_5_Pin,  LinearL_5_GPIO_Port,  LinearL_5_Pin  },
    /* 6  */ { LinearR_6_GPIO_Port,  LinearR_6_Pin,  LinearL_6_GPIO_Port,  LinearL_6_Pin  },
    /* 7  */ { LinearR_7_GPIO_Port,  LinearR_7_Pin,  LinearL_7_GPIO_Port,  LinearL_7_Pin  },
};

/* TODO: proteksi stall - durasi maks HIGH per actuator belum ditentukan.
 * Isi array ini nanti kalau sudah ada angka pasti dari tes fisik, lalu
 * tambah pengecekan di main loop mirip CekWatchdog(). */
static uint32_t waktuMulaiAktif[JUMLAH_ACTUATOR];
static int8_t   arahTerakhir[JUMLAH_ACTUATOR];
static const int8_t ARAH_FISIK_MOTOR[JUMLAH_MOTOR] = {1, -1, 1, -1};

volatile uint8_t statusLampuBelakang = LAMPU_MATI;
uint8_t lampuBelakangBrightness = 0;
uint32_t waktuBlinkTerakhir = 0;
uint8_t statusBlinkSekarang = 0;

/* ---- Komunikasi GCS/RF (USART2, 16 byte request / 4 byte reply) ---- */
static uint8_t gcsRxBuf[GCS_FRAME_LEN];
static uint8_t gcsFrameKerja[GCS_FRAME_LEN];
volatile uint8_t gcsFrameSiap = 0;
static uint8_t gcsFrameTerakhir[GCS_FRAME_LEN];      /* buat di-relay ke Jetson */
static uint8_t gcsBalasanCache[4] = {1U, 0U, 0U, 0U}; /* diisi Jetson lewat down-frame, default aman */

/* ---- Komunikasi Jetson (USART3, 24 byte down / 20 byte up) ---- */
static uint8_t jetsonRxBuf[JETSON_DOWN_LEN];
static uint8_t jetsonFrameKerja[JETSON_DOWN_LEN];
volatile uint8_t jetsonFrameSiap = 0;
static uint16_t lrfJarakTerakhir = 0;
static uint8_t  lrfStatusTerakhir = 0;

/* ---- LED indikator (heartbeat + status link) ---- */
static uint32_t waktuFrameJetsonTerakhir = 0;
static uint32_t waktuFrameGcsTerakhir = 0;
static uint32_t waktuHeartbeatTerakhir = 0;
static uint8_t  statusHeartbeat = 0;

/* ---- Anti-spam RS485 (cuma kirim pas berubah) - file-scope biar bisa
 * dipicu paksa ke STOP dari failsafe di main loop juga, gak cuma dari
 * JetsonApplyCommand. Sentinel awal DILUAR rentang valid biar frame
 * pertama pasti dianggap "berubah". */
static uint8_t pantiltArahTerakhir = 0xFFU;
static int8_t  kameraZoomTerakhir = 127;
static uint8_t slipRingTerakhir = 0xFFU;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_TIM1_Init(void);
static void MX_TIM3_Init(void);
static void MX_TIM4_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_USART3_UART_Init(void);
static void MX_TIM8_Init(void);
static void MX_TIM15_Init(void);
static void MX_USB_PCD_Init(void);
static void MX_LPUART1_UART_Init(void);
/* USER CODE BEGIN PFP */
static void SetActuator(uint8_t index, int8_t dir);
static void StopSemuaActuator(void);
static void setPulseFreq(TIM_HandleTypeDef *htim, uint32_t channel, int32_t speed);
static void setMotor(uint8_t index, int32_t speedWheelSpace);
static void stopSemuaMotor(void);
static void Lamp_SetBrightness(TIM_HandleTypeDef *htim, uint32_t channel, uint8_t percent);
static void setLampuBelakang(uint8_t brightness, uint8_t state);
static void DebugPrint(const char *format, ...);

static void RS485_KirimFrame(const uint8_t *frame, uint8_t panjang);

static uint8_t Pantilt_Checksum(const uint8_t *payload5);
static void Pantilt_Kirim(const uint8_t *payload5);
static void Pantilt_Gerak(PantiltArah_t arah);
static void Pantilt_PowerSlipRing(uint8_t nyala);

static uint8_t Pelco_Checksum(uint8_t alamat, uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2);
static void Pelco_Kirim(uint8_t alamat, uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2);
static void Kamera_ZoomIn(void);
static void Kamera_ZoomOut(void);
static void Kamera_ZoomStop(void);

static void BridgeLrf_Kirim(uint8_t cmd2, uint8_t data1, uint8_t data2);
static uint8_t BridgeLrf_BacaRespons(uint8_t *cmd2Out, uint8_t *data1Out, uint8_t *data2Out);
static uint8_t BridgeLrf_BacaJarak(uint16_t *jarakDesimeterOut);
static uint8_t BridgeLrf_Pointer(uint8_t nyala);

static void GcsParseFrame(const uint8_t *frame16, GcsCommand_t *out);
static void JetsonParseFrame(const uint8_t *frame24, JetsonCommand_t *out);
static void JetsonApplyCommand(const JetsonCommand_t *cmd);
static void JetsonBangunUpFrame(uint8_t *frameOut20);

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

static void Lamp_SetBrightness(TIM_HandleTypeDef *htim, uint32_t channel, uint8_t percent) {
    if (percent > 100U) percent = 100U;
    uint32_t ccr = ((uint32_t)percent * (LAMP_PWM_ARR + 1U)) / 100U;
    __HAL_TIM_SET_COMPARE(htim, channel, ccr);
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
            HAL_GPIO_WritePin(MotorS_0_GPIO_Port, MotorS_0_Pin, levelSign);
            setPulseFreq(&htim3, TIM_CHANNEL_1, speedWheelSpace);
            break;
        case 1:
            HAL_GPIO_WritePin(MotorS_1_GPIO_Port, MotorS_1_Pin, levelSign);
            setPulseFreq(&htim4, TIM_CHANNEL_2, speedWheelSpace);
            break;
        case 2:
            HAL_GPIO_WritePin(MotorS_2_GPIO_Port, MotorS_2_Pin, levelSign);
            setPulseFreq(&htim8, TIM_CHANNEL_1, speedWheelSpace);
            break;
        case 3:
            HAL_GPIO_WritePin(MotorS_3_GPIO_Port, MotorS_3_Pin, levelSign);
            setPulseFreq(&htim15, TIM_CHANNEL_1, speedWheelSpace);
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

static void setLampuBelakang(uint8_t brightness, uint8_t state) {
    if (state > LAMPU_KEDIP) state = LAMPU_KEDIP;
    if (brightness > 100U) brightness = 100U;

    statusLampuBelakang = state;
    lampuBelakangBrightness = brightness;

    if (state == LAMPU_MATI) {
        Lamp_SetBrightness(&htim1, TIM_CHANNEL_2, 0);
    } else if (state == LAMPU_NYALA) {
        Lamp_SetBrightness(&htim1, TIM_CHANNEL_2, brightness);
    }
    /* LAMPU_KEDIP: gak di-set di sini - main loop yang toggle brightness<->0 */
}

/* ============================================================================
 * DEBUG - print lewat LPUART1 (ST-LINK VCP)
 * ==========================================================================*/

static void DebugPrint(const char *format, ...)
{
    char buffer[128];
    va_list args;
    va_start(args, format);
    int panjang = vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    HAL_UART_Transmit(&hlpuart1, (uint8_t *)buffer, (uint16_t)panjang, UART_TX_TIMEOUT_MS);
}

/* ============================================================================
 * RS485 - pantilt + kamera + LRF-bridge, 1 bus fisik bareng (USART1, 9600)
 * ==========================================================================*/

static void RS485_KirimFrame(const uint8_t *frame, uint8_t panjang) {
    HAL_UART_Transmit(&huart1, (uint8_t *)frame, panjang, UART_TX_TIMEOUT_MS);
}

/* ---- Pantilt (protokol custom, hasil reverse-engineer - lihat
 * test_bus_pantilt_kamera_lrf.py) ---- */

static uint8_t Pantilt_Checksum(const uint8_t *payload5) {
    uint8_t sum = 0;
    for (uint8_t i = 0; i < 5U; i++) {
        if (payload5[i] != 0xFFU) sum += payload5[i];
    }
    return sum;
}

static void Pantilt_Kirim(const uint8_t *payload5) {
    uint8_t frame[7];
    frame[0] = 0xFF;
    for (uint8_t i = 0; i < 5U; i++) frame[1U + i] = payload5[i];
    frame[6] = Pantilt_Checksum(payload5);
    RS485_KirimFrame(frame, 7U);
}

static const uint8_t PANTILT_GERAK_TABLE[5][5] = {
    {0x00, 0x00, 0x04, 0x3F, 0x00}, /* kiri */
    {0x00, 0x00, 0x02, 0x3F, 0x00}, /* kanan */
    {0x00, 0x00, 0x08, 0x00, 0x3F}, /* atas */
    {0x00, 0x00, 0x10, 0x00, 0x3F}, /* bawah */
    {0x00, 0x00, 0x00, 0x00, 0x00}, /* stop */
};

static void Pantilt_Gerak(PantiltArah_t arah) {
    Pantilt_Kirim(PANTILT_GERAK_TABLE[arah]);
}

static void Pantilt_PowerSlipRing(uint8_t nyala) {
    uint8_t payload5[5] = { 0x00, 0x00, (uint8_t)(nyala ? 0x09U : 0x0BU), 0x00, 0x02 };
    Pantilt_Kirim(payload5);
}

/* BELUM DIIMPLEMENTASI (sengaja) - pantilt sebenernya BISA dibaca sudutnya,
 * beda dari command gerak/slip ring yang emang gak pernah balas. Referensi:
 * Testcode/test_bus_pantilt_kamera_lrf.py -> pantilt_baca_sudut().
 * Kirim payload5 = {0x00,0x00,cmd2,0x00,0x00}, cmd2: 0x51=azimuth, 0x53=elevasi.
 * Baca respons 7 byte (pola sama kayak Pantilt_Kirim, checksum pakai
 * Pantilt_Checksum), payload[3] & payload[4] = data encoder mentah, lalu:
 *   elevasi = 2.694879023302476*data[3] + 1.1455831934909497*data[4]/100 - 73.36566910656754
 *   azimuth = 2.447221740538158*data[3] + (-2.2315937758949502)*data[4]/100 - 69.7511885011599
 * Kalau nanti mau diimplementasi: butuh field trigger baru di down-frame
 * Jetson (mirip lrfTrigger) + field balik di up-frame buat hasil sudutnya. */

/* ---- Kamera + LRF-bridge, sama-sama bungkus Pelco-D (lihat
 * test_bus_pantilt_kamera_lrf.py) ---- */

static uint8_t Pelco_Checksum(uint8_t alamat, uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2) {
    return (uint8_t)(alamat + cmd1 + cmd2 + data1 + data2);
}

static void Pelco_Kirim(uint8_t alamat, uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2) {
    uint8_t frame[7];
    frame[0] = 0xFF;
    frame[1] = alamat;
    frame[2] = cmd1;
    frame[3] = cmd2;
    frame[4] = data1;
    frame[5] = data2;
    frame[6] = Pelco_Checksum(alamat, cmd1, cmd2, data1, data2);
    RS485_KirimFrame(frame, 7U);
}

static void Kamera_ZoomIn(void)   { Pelco_Kirim(ALAMAT_KAMERA, 0x00, 0x20, 0x00, 0x00); }
static void Kamera_ZoomOut(void)  { Pelco_Kirim(ALAMAT_KAMERA, 0x00, 0x40, 0x00, 0x00); }
static void Kamera_ZoomStop(void) { Pelco_Kirim(ALAMAT_KAMERA, 0x00, 0x00, 0x00, 0x00); }

static void BridgeLrf_Kirim(uint8_t cmd2, uint8_t data1, uint8_t data2) {
    Pelco_Kirim(ALAMAT_BRIDGE_LRF, 0x00, cmd2, data1, data2);
}

static uint8_t BridgeLrf_BacaRespons(uint8_t *cmd2Out, uint8_t *data1Out, uint8_t *data2Out) {
    uint8_t frame[7];
    if (HAL_UART_Receive(&huart1, frame, 7U, RS485_TIMEOUT_MS) != HAL_OK) return 0U;
    if (Pelco_Checksum(frame[1], frame[2], frame[3], frame[4], frame[5]) != frame[6]) return 0U;
    *cmd2Out  = frame[3];
    *data1Out = frame[4];
    *data2Out = frame[5];
    return 1U;
}

static uint8_t BridgeLrf_BacaJarak(uint16_t *jarakDesimeterOut) {
    uint8_t cmd2, data1, data2;
    BridgeLrf_Kirim(CMD2_BACA_JARAK, 0x00, 0x00);
    if (!BridgeLrf_BacaRespons(&cmd2, &data1, &data2)) return 0U;
    *jarakDesimeterOut = (uint16_t)data1 | ((uint16_t)data2 << 8);
    return 1U;
}

static uint8_t BridgeLrf_Pointer(uint8_t nyala) {
    uint8_t cmd2, data1, data2;
    BridgeLrf_Kirim(CMD2_POINTER, (uint8_t)(nyala ? 1U : 0U), 0x00);
    return BridgeLrf_BacaRespons(&cmd2, &data1, &data2);
}

/* ============================================================================
 * GCS/RF - USART2, 57600. STM32 DIDIAMKAN dengerin (interrupt), balas begitu
 * 16 byte lengkap diterima. Status yang dibalas diambil dari gcsBalasanCache
 * (diisi Jetson lewat down-frame - lihat JetsonApplyCommand).
 * ==========================================================================*/

static void GcsParseFrame(const uint8_t *frame16, GcsCommand_t *out) {
    out->estop               = frame16[0];
    out->mode                = frame16[1];
    out->xJoy1                = (int8_t)frame16[2];
    out->yJoy1                = (int8_t)frame16[3];
    out->xJoy2                = (int8_t)frame16[4];
    out->yJoy2                = (int8_t)frame16[5];
    out->zoom                 = (int8_t)frame16[6];
    out->lrf                  = frame16[7];
    out->fLamp                = frame16[8];
    out->bLamp                = frame16[9];
    out->slipRing             = frame16[10];
    out->bodyUpDown           = (int8_t)frame16[11];
    out->armWidenNarrow       = (int8_t)frame16[12];
    out->motorIndividualId    = frame16[13];
    out->motorIndividualArah  = (int8_t)frame16[14];
    out->kalibrasi            = frame16[15];
}

/* ============================================================================
 * Jetson - USART3, 115200. Jetson yang inisiatif (heartbeat ~20Hz), STM32
 * APPLY command yang diterima LANGSUNG (motor/actuator/lampu/RS485), lalu
 * balas 20 byte (relay GCS terakhir + status LRF real-time).
 * ==========================================================================*/

static void JetsonParseFrame(const uint8_t *frame24, JetsonCommand_t *out) {
    out->speed = (int8_t)frame24[0];
    for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
        out->act[i] = (int8_t)frame24[1U + i];
    }
    out->fLamp               = frame24[9];
    out->bLamp                = frame24[10];
    out->bLampMode             = frame24[11];
    out->pantiltArah           = frame24[12];
    out->kameraZoom            = (int8_t)frame24[13];
    out->slipRing              = frame24[14];
    out->lrfTrigger            = frame24[15];
    out->gcsReplyStm32Status   = frame24[16];
    out->gcsReplyLrfStatus     = frame24[17];
    out->gcsReplyLrfLsb        = frame24[18];
    out->gcsReplyLrfMsb        = frame24[19];
}

static void JetsonApplyCommand(const JetsonCommand_t *cmd) {
    for (uint8_t i = 0; i < JUMLAH_MOTOR; i++) {
        setMotor(i, cmd->speed);
    }
    for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
        SetActuator(i, cmd->act[i]);
    }
    Lamp_SetBrightness(&htim1, TIM_CHANNEL_1, cmd->fLamp);
    setLampuBelakang(cmd->bLamp, cmd->bLampMode);

    /* RS485 (pantilt/kamera/slip ring) CUMA dikirim kalau nilainya BERUBAH
     * dari siklus sebelumnya - bukan tiap ada frame Jetson masuk (~10-20Hz).
     * Tanpa ini, bus RS485 digempur command identik terus-menerus. */
    if (cmd->pantiltArah <= (uint8_t)PANTILT_STOP && cmd->pantiltArah != pantiltArahTerakhir) {
        Pantilt_Gerak((PantiltArah_t)cmd->pantiltArah);
        pantiltArahTerakhir = cmd->pantiltArah;
    }

    if (cmd->kameraZoom != kameraZoomTerakhir) {
        if (cmd->kameraZoom > 0) {
            Kamera_ZoomIn();
        } else if (cmd->kameraZoom < 0) {
            Kamera_ZoomOut();
        } else {
            Kamera_ZoomStop();
        }
        kameraZoomTerakhir = cmd->kameraZoom;
    }

    if (cmd->slipRing != slipRingTerakhir) {
        Pantilt_PowerSlipRing(cmd->slipRing);
        slipRingTerakhir = cmd->slipRing;
    }

    if (cmd->lrfTrigger == LRF_TRIGGER_BACA_JARAK) {
        uint16_t jarak;
        if (BridgeLrf_BacaJarak(&jarak)) {
            lrfJarakTerakhir = jarak;
            lrfStatusTerakhir = 1U;
        } else {
            lrfStatusTerakhir = 0U;
        }
    } else if (cmd->lrfTrigger == LRF_TRIGGER_POINTER_ON) {
        BridgeLrf_Pointer(1U);
    } else if (cmd->lrfTrigger == LRF_TRIGGER_POINTER_OFF) {
        BridgeLrf_Pointer(0U);
    }

    /* Simpan buat balasan ke GCS BERIKUTNYA - Jetson yang mutusin isinya,
     * STM32 cuma relay apa adanya (prinsip dumb driver). */
    gcsBalasanCache[0] = cmd->gcsReplyStm32Status;
    gcsBalasanCache[1] = cmd->gcsReplyLrfStatus;
    gcsBalasanCache[2] = cmd->gcsReplyLrfLsb;
    gcsBalasanCache[3] = cmd->gcsReplyLrfMsb;
}

static void JetsonBangunUpFrame(uint8_t *frameOut20) {
    memcpy(frameOut20, gcsFrameTerakhir, GCS_FRAME_LEN); /* relay 16 byte GCS APA ADANYA */
    frameOut20[16] = (uint8_t)(lrfJarakTerakhir & 0xFFU);
    frameOut20[17] = (uint8_t)((lrfJarakTerakhir >> 8) & 0xFFU);
    frameOut20[18] = lrfStatusTerakhir;
    frameOut20[19] = 1U; /* stm32Status: sehat */
}

/* ============================================================================
 * LAYER 4 - komunikasi & housekeeping
 * ==========================================================================*/

/* Pakai ReceiveToIdle (bukan HAL_UART_RxCpltCallback biasa) - ini yang
 * bikin STM32 otomatis "sinkron ulang" tiap ada jeda hening di jalur UART
 * (natural ada karena GCS/Jetson kirim per-siklus, gak nonstop). Kalau byte
 * yang ke-nangkep JUMLAHNYA gak pas, frame itu DIBUANG, bukan dipaksa
 * diproses - jadi gak ada lagi kejadian "kegeser permanen" kayak yang
 * ketemu waktu testing GCS. */
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size) {
    if (huart->Instance == USART2) {
        if (Size == GCS_FRAME_LEN) {
            waktuFrameGcsTerakhir = HAL_GetTick();
            if (gcsFrameSiap == 0) {
                memcpy(gcsFrameKerja, gcsRxBuf, GCS_FRAME_LEN);
                gcsFrameSiap = 1;
            }
        }
        HAL_UARTEx_ReceiveToIdle_IT(&huart2, gcsRxBuf, GCS_FRAME_LEN);
    } else if (huart->Instance == USART3) {
        if (Size == JETSON_DOWN_LEN) {
            waktuFrameJetsonTerakhir = HAL_GetTick();
            if (jetsonFrameSiap == 0) {
                memcpy(jetsonFrameKerja, jetsonRxBuf, JETSON_DOWN_LEN);
                jetsonFrameSiap = 1;
            }
        }
        HAL_UARTEx_ReceiveToIdle_IT(&huart3, jetsonRxBuf, JETSON_DOWN_LEN);
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART2) {
        HAL_UARTEx_ReceiveToIdle_IT(&huart2, gcsRxBuf, GCS_FRAME_LEN);
    } else if (huart->Instance == USART3) {
        HAL_UARTEx_ReceiveToIdle_IT(&huart3, jetsonRxBuf, JETSON_DOWN_LEN);
    }
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
  MX_TIM1_Init();
  MX_TIM3_Init();
  MX_TIM4_Init();
  MX_USART1_UART_Init();
  MX_USART2_UART_Init();
  MX_USART3_UART_Init();
  MX_TIM8_Init();
  MX_TIM15_Init();
  MX_USB_PCD_Init();
  MX_LPUART1_UART_Init();
  /* USER CODE BEGIN 2 */
  stopSemuaMotor();
  StopSemuaActuator();

  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_2);
  __HAL_TIM_SET_PRESCALER(&htim1, 49);
  __HAL_TIM_SET_AUTORELOAD(&htim1, LAMP_PWM_ARR);

  Lamp_SetBrightness(&htim1, TIM_CHANNEL_1, 0);
  setLampuBelakang(100, LAMPU_NYALA);

  memset(gcsFrameTerakhir, 0, GCS_FRAME_LEN);
  HAL_UARTEx_ReceiveToIdle_IT(&huart2, gcsRxBuf, GCS_FRAME_LEN);
  HAL_UARTEx_ReceiveToIdle_IT(&huart3, jetsonRxBuf, JETSON_DOWN_LEN);

  DebugPrint("\r\n=== motorugv_G474RE Boot OK ===\r\n");

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    if (statusLampuBelakang == LAMPU_KEDIP) {
        if (HAL_GetTick() - waktuBlinkTerakhir >= BLINK_INTERVAL_MS) {
            statusBlinkSekarang = !statusBlinkSekarang;
            Lamp_SetBrightness(&htim1, TIM_CHANNEL_2,
                statusBlinkSekarang ? lampuBelakangBrightness : 0);
            waktuBlinkTerakhir = HAL_GetTick();
        }
    }

    /* LED heartbeat - blink terus tiap HEARTBEAT_INTERVAL_MS, bukti main loop
     * masih jalan (beda sama LED link yang bisa nyala terus walau loop hang,
     * karena itu cuma ngecek timestamp). */
    if (HAL_GetTick() - waktuHeartbeatTerakhir >= HEARTBEAT_INTERVAL_MS) {
        statusHeartbeat = !statusHeartbeat;
        HAL_GPIO_WritePin(LED_Heartbeat_GPIO_Port, LED_Heartbeat_Pin,
            statusHeartbeat ? GPIO_PIN_SET : GPIO_PIN_RESET);
        waktuHeartbeatTerakhir = HAL_GetTick();
    }

    /* LED status link - nyala kalau ada frame VALID dalam LINK_TIMEOUT_MS
     * terakhir, mati kalau link putus/timeout. */
    HAL_GPIO_WritePin(LED_Jetson_GPIO_Port, LED_Jetson_Pin,
        (HAL_GetTick() - waktuFrameJetsonTerakhir < LINK_TIMEOUT_MS) ? GPIO_PIN_SET : GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LED_RF_GPIO_Port, LED_RF_Pin,
        (HAL_GetTick() - waktuFrameGcsTerakhir < LINK_TIMEOUT_MS) ? GPIO_PIN_SET : GPIO_PIN_RESET);

    /* FAILSAFE: kalau Jetson gak kirim frame valid selama LINK_TIMEOUT_MS,
     * paksa berhenti - jangan terus nurut command terakhir tanpa batas
     * waktu cuma karena link putus (Jetson mati/hang/USB kecabut, dll).
     * Motor/actuator aman di-stop tiap loop (idempoten, murah). Pantilt/
     * kamera RS485 SENGAJA dijaga cuma kirim SEKALI pas transisi ke
     * failsafe (guard pakai tracker anti-spam yang sama) - biar gak balik
     * spam RS485 gara-gara loop ini muter terus selama link masih putus. */
    if (HAL_GetTick() - waktuFrameJetsonTerakhir >= LINK_TIMEOUT_MS) {
        stopSemuaMotor();
        StopSemuaActuator();
        if (pantiltArahTerakhir != (uint8_t)PANTILT_STOP) {
            Pantilt_Gerak(PANTILT_STOP);
            pantiltArahTerakhir = (uint8_t)PANTILT_STOP;
        }
        if (kameraZoomTerakhir != 0) {
            Kamera_ZoomStop();
            kameraZoomTerakhir = 0;
        }
        if (slipRingTerakhir != 0) {
            Pantilt_PowerSlipRing(0);
            slipRingTerakhir = 0;
        }
    }

    if (jetsonFrameSiap) {
        uint8_t salinanJetson[JETSON_DOWN_LEN];
        memcpy(salinanJetson, jetsonFrameKerja, JETSON_DOWN_LEN);
        jetsonFrameSiap = 0;

        JetsonCommand_t cmd;
        JetsonParseFrame(salinanJetson, &cmd);
        JetsonApplyCommand(&cmd);

        uint8_t upFrame[JETSON_UP_LEN];
        JetsonBangunUpFrame(upFrame);
        HAL_UART_Transmit(&huart3, upFrame, JETSON_UP_LEN, UART_TX_TIMEOUT_MS);

        DebugPrint("Jetson RX: speed=%d flamp=%u blamp=%u pantilt=%u zoom=%d lrfTrig=%u\r\n",
            cmd.speed, cmd.fLamp, cmd.bLamp, cmd.pantiltArah, cmd.kameraZoom, cmd.lrfTrigger);
    }

    if (gcsFrameSiap) {
        uint8_t salinanGcs[GCS_FRAME_LEN];
        memcpy(salinanGcs, gcsFrameKerja, GCS_FRAME_LEN);
        gcsFrameSiap = 0;

        memcpy(gcsFrameTerakhir, salinanGcs, GCS_FRAME_LEN); /* buat di-relay ke Jetson */

        GcsCommand_t cmd;
        GcsParseFrame(salinanGcs, &cmd);

        DebugPrint("GCS RX: estop=%u mode=%u xj1=%d yj1=%d xj2=%d yj2=%d flamp=%u blamp=%u kalibrasi=%u\r\n",
            cmd.estop, cmd.mode, cmd.xJoy1, cmd.yJoy1, cmd.xJoy2, cmd.yJoy2,
            cmd.fLamp, cmd.bLamp, cmd.kalibrasi);

        HAL_UART_Transmit(&huart2, gcsBalasanCache, 4U, UART_TX_TIMEOUT_MS);
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
  HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1_BOOST);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = RCC_PLLM_DIV4;
  RCC_OscInitStruct.PLL.PLLN = 85;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_4) != HAL_OK)
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
  hlpuart1.Init.BaudRate = 209700;
  hlpuart1.Init.WordLength = UART_WORDLENGTH_8B;
  hlpuart1.Init.StopBits = UART_STOPBITS_1;
  hlpuart1.Init.Parity = UART_PARITY_NONE;
  hlpuart1.Init.Mode = UART_MODE_TX_RX;
  hlpuart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  hlpuart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  hlpuart1.Init.ClockPrescaler = UART_PRESCALER_DIV1;
  hlpuart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
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
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 9600;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  huart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart1.Init.ClockPrescaler = UART_PRESCALER_DIV1;
  huart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetTxFifoThreshold(&huart1, UART_TXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetRxFifoThreshold(&huart1, UART_RXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_DisableFifoMode(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 57600;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart2.Init.ClockPrescaler = UART_PRESCALER_DIV1;
  huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetTxFifoThreshold(&huart2, UART_TXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetRxFifoThreshold(&huart2, UART_RXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_DisableFifoMode(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

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
  huart3.Init.BaudRate = 115200;
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
  if (HAL_TIM_PWM_Init(&htim1) != HAL_OK)
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
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
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
  * @brief TIM3 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM3_Init(void)
{

  /* USER CODE BEGIN TIM3_Init 0 */

  /* USER CODE END TIM3_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM3_Init 1 */

  /* USER CODE END TIM3_Init 1 */
  htim3.Instance = TIM3;
  htim3.Init.Prescaler = 0;
  htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim3.Init.Period = 65535;
  htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_OC_Init(&htim3) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim3, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_TOGGLE;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_OC_ConfigChannel(&htim3, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM3_Init 2 */

  /* USER CODE END TIM3_Init 2 */
  HAL_TIM_MspPostInit(&htim3);

}

/**
  * @brief TIM4 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM4_Init(void)
{

  /* USER CODE BEGIN TIM4_Init 0 */

  /* USER CODE END TIM4_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM4_Init 1 */

  /* USER CODE END TIM4_Init 1 */
  htim4.Instance = TIM4;
  htim4.Init.Prescaler = 0;
  htim4.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim4.Init.Period = 65535;
  htim4.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_OC_Init(&htim4) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim4, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_TOGGLE;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_OC_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM4_Init 2 */

  /* USER CODE END TIM4_Init 2 */
  HAL_TIM_MspPostInit(&htim4);

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
  if (HAL_TIM_OC_Init(&htim15) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim15, &sMasterConfig) != HAL_OK)
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
  if (HAL_TIM_OC_ConfigChannel(&htim15, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
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
  * @brief USB Initialization Function
  * @param None
  * @retval None
  */
static void MX_USB_PCD_Init(void)
{

  /* USER CODE BEGIN USB_Init 0 */

  /* USER CODE END USB_Init 0 */

  /* USER CODE BEGIN USB_Init 1 */

  /* USER CODE END USB_Init 1 */
  hpcd_USB_FS.Instance = USB;
  hpcd_USB_FS.Init.dev_endpoints = 8;
  hpcd_USB_FS.Init.speed = PCD_SPEED_FULL;
  hpcd_USB_FS.Init.phy_itface = PCD_PHY_EMBEDDED;
  hpcd_USB_FS.Init.Sof_enable = DISABLE;
  hpcd_USB_FS.Init.low_power_enable = DISABLE;
  hpcd_USB_FS.Init.lpm_enable = DISABLE;
  hpcd_USB_FS.Init.battery_charging_enable = DISABLE;
  if (HAL_PCD_Init(&hpcd_USB_FS) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USB_Init 2 */

  /* USER CODE END USB_Init 2 */

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
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOF_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, MotorS_1_Pin|LinearL_3_Pin|LinearR_5_Pin|MotorS_3_Pin
                          |LinearR_7_Pin|MotorS_2_Pin|LinearR_1_Pin|LinearL_4_Pin
                          |LinearR_0_Pin|LinearR_4_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOF, LinearR_3_Pin|LinearL_5_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, LinearR_2_Pin|LinearL_2_Pin|LinearR_11_Pin|MotorS_0_Pin
                          |LinearL_1_Pin|LinearL_6_Pin|LinearL_7_Pin|LinearR_6_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, LED_Jetson_Pin|LED_RF_Pin|LED_Heartbeat_Pin|LinearR_8_Pin
                          |LinearL_8_Pin|LinearR_9_Pin|LinearL_9_Pin|LinearR_10_Pin
                          |LinearL_10_Pin|LinearL_11_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(LinearL_0_GPIO_Port, LinearL_0_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : MotorS_1_Pin LinearL_3_Pin LinearR_5_Pin MotorS_3_Pin
                           LinearR_7_Pin MotorS_2_Pin LinearR_1_Pin LinearL_4_Pin
                           LinearR_0_Pin LinearR_4_Pin */
  GPIO_InitStruct.Pin = MotorS_1_Pin|LinearL_3_Pin|LinearR_5_Pin|MotorS_3_Pin
                          |LinearR_7_Pin|MotorS_2_Pin|LinearR_1_Pin|LinearL_4_Pin
                          |LinearR_0_Pin|LinearR_4_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : LinearR_3_Pin LinearL_5_Pin */
  GPIO_InitStruct.Pin = LinearR_3_Pin|LinearL_5_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOF, &GPIO_InitStruct);

  /*Configure GPIO pins : LinearR_2_Pin LinearL_2_Pin LinearR_11_Pin MotorS_0_Pin
                           LinearL_1_Pin LinearL_6_Pin LinearL_7_Pin LinearR_6_Pin */
  GPIO_InitStruct.Pin = LinearR_2_Pin|LinearL_2_Pin|LinearR_11_Pin|MotorS_0_Pin
                          |LinearL_1_Pin|LinearL_6_Pin|LinearL_7_Pin|LinearR_6_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : LED_Jetson_Pin LED_RF_Pin LED_Heartbeat_Pin LinearR_8_Pin
                           LinearL_8_Pin LinearR_9_Pin LinearL_9_Pin LinearR_10_Pin
                           LinearL_10_Pin LinearL_11_Pin */
  GPIO_InitStruct.Pin = LED_Jetson_Pin|LED_RF_Pin|LED_Heartbeat_Pin|LinearR_8_Pin
                          |LinearL_8_Pin|LinearR_9_Pin|LinearL_9_Pin|LinearR_10_Pin
                          |LinearL_10_Pin|LinearL_11_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pin : LinearL_0_Pin */
  GPIO_InitStruct.Pin = LinearL_0_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LinearL_0_GPIO_Port, &GPIO_InitStruct);

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
