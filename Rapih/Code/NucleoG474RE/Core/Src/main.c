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

typedef struct {
    uint8_t estop;
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
    uint8_t motorIndividualId;
    int8_t  motorIndividualArah;
    uint8_t kalibrasi;
    uint8_t mode; /* 0=manual, 1=auto - placeholder, belum ada tombolnya di GCS */
} GcsCommand_t;

typedef struct {
    int8_t  speed;
    int8_t  act[8];
    uint8_t fLamp;
    uint8_t bLamp;
    uint8_t bLampMode;
    int8_t  pantiltHorizontal;
    int8_t  pantiltVertical;
    int8_t  kameraZoom;
    uint8_t slipRing;
    uint8_t lrfTrigger;
    uint8_t gcsReplyStm32Status;
    uint8_t gcsReplyLrfStatus;
    uint8_t gcsReplyLrfLsb;
    uint8_t gcsReplyLrfMsb;
    uint8_t gcsReplyBoxTerdeteksi;
    int8_t  gcsReplyBoxPusatX;
    int8_t  gcsReplyBoxPusatY;
    uint8_t gcsReplyBoxLebar;
    uint8_t gcsReplyBoxTinggi;
} JetsonCommand_t;
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define JUMLAH_MOTOR        4U
#define JUMLAH_ACTUATOR     8U

#define FREQ_PER_RPM        50U
#define TIMER_CLOCK_HZ      170000000UL
#define LAMP_PWM_ARR        3399U

#define BLINK_INTERVAL_MS   250U
#define LAMPU_MATI          0U
#define LAMPU_NYALA         1U
#define LAMPU_KEDIP         2U

/* Bridge LRF butuh sampai 2000ms internal (LRF_TIMEOUT_MS di firmware
 * bridge-nya, sekarang pakai mode SMM biasa - ~1.3 detik nominal, tapi
 * datasheet resmi bilang bisa ~300ms lebih lama di cuaca buruk, jadi
 * worst-case ~1.6 detik + margin) sebelum dia sempat balas ke bus - timeout
 * di sini HARUS lebih panjang dari itu + overhead transmisi, kalau enggak
 * G474RE bakal nyerah duluan walau bridge-nya sebenarnya bakal jawab.
 * JANGAN diturunin manual - itu udah 2 kali kejadian bikin baca jarak
 * SELALU timeout gara-gara nilainya balik ke yang lama. */
#define RS485_TIMEOUT_MS    2300U

/* Batas waktu "anggap link mati total" - dipakai LED status link dan
 * failsafe (paksa stop motor/actuator kalau kelewat). DIPISAH per link,
 * BUKAN 1 angka buat semua - Jetson lewat kabel langsung (USART3), harus
 * tetap ketat. GCS lewat radio RF, yang menurut serial_workers.py
 * (AMBANG_MISS_BERTURUT) NORMALNYA miss ~75-80% per percobaan dan app-nya
 * sendiri baru declare disconnect setelah ~1 detik miss beruntun - kalau
 * STM32 pakai angka seketat Jetson (500ms), motor bisa keburu di-failsafe
 * padahal dari sudut pandang GCS app link itu masih dianggap sehat. */
#define JETSON_LINK_TIMEOUT_MS 500U
#define GCS_LINK_TIMEOUT_MS    1500U

#define ALAMAT_KAMERA       1U
#define ALAMAT_BRIDGE_LRF   2U
#define CMD2_BACA_JARAK     0x01U
#define CMD2_POINTER        0x02U

/* Nilai lrfStatusTerakhir yang di-relay transparan lewat Jetson ke GCS
 * (byte gcsReplyLrfStatus) - Jetson gak pernah interpretasi isinya, cuma
 * nge-passing mentah, jadi aman diperluas dari cuma 0/1 tanpa nyentuh kode
 * Jetson sama sekali. 2/3 dipetakan dari kode hasil LRF_HASIL_* bridge. */
#define LRF_STATUS_GAGAL_KOMUNIKASI  0U   /* timeout/checksum salah - gak ada jawaban sama sekali */
#define LRF_STATUS_OK                1U   /* ada target valid */
#define LRF_STATUS_NO_TARGET         2U   /* bridge jawab, tapi LRF gak nemu target (NT) */
#define LRF_STATUS_ERROR             3U   /* bridge jawab, tapi LRF lapor ERR/TTE */

#define GCS_FRAME_LEN       15U

#define GCS_REPLY_MARKER    0xA5U
#define GCS_REPLY_LEN       11U

#define JETSON_DOWN_LEN     27U   /* 26 data + 1 checksum */
#define JETSON_UP_LEN       20U   /* 19 data + 1 checksum */

/* Resync frame Jetson (USART3) kalau lagi nampung SEBAGIAN frame (index>0)
 * tapi udah sekian ms gak ada byte baru masuk - anggap byte-nya beneran
 * hilang (bukan cuma jeda kecil biasa), buang sisa frame yang gantung,
 * mulai dari 0 lagi. 26 byte @115200 baud cuma butuh ~2.3ms buat kirim
 * SEMUA kalau lancar - 30ms udah kasih margin besar buat jeda pengiriman
 * yang wajar, tapi masih jauh lebih pendek dari jarak antar siklus
 * Jetson (~100ms) jadi gak bakal ketuker sama "nunggu frame BERIKUTNYA". */
#define JETSON_RESYNC_TIMEOUT_MS 30U

#define LRF_TRIGGER_IDLE       0U
#define LRF_TRIGGER_BACA_JARAK 1U
#define LRF_TRIGGER_POINTER_ON 2U
#define LRF_TRIGGER_POINTER_OFF 3U

#define HEARTBEAT_INTERVAL_MS 500U

#define UART_TX_TIMEOUT_MS   50U
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
    { LinearR_0_GPIO_Port,  LinearR_0_Pin,  LinearL_0_GPIO_Port,  LinearL_0_Pin  },
    { LinearR_1_GPIO_Port,  LinearR_1_Pin,  LinearL_1_GPIO_Port,  LinearL_1_Pin  },
    { LinearR_2_GPIO_Port,  LinearR_2_Pin,  LinearL_2_GPIO_Port,  LinearL_2_Pin  },
    { LinearR_3_GPIO_Port,  LinearR_3_Pin,  LinearL_3_GPIO_Port,  LinearL_3_Pin  },
    { LinearR_4_GPIO_Port,  LinearR_4_Pin,  LinearL_4_GPIO_Port,  LinearL_4_Pin  },
    { LinearR_5_GPIO_Port,  LinearR_5_Pin,  LinearL_5_GPIO_Port,  LinearL_5_Pin  },
    { LinearR_6_GPIO_Port,  LinearR_6_Pin,  LinearL_6_GPIO_Port,  LinearL_6_Pin  },
    { LinearR_7_GPIO_Port,  LinearR_7_Pin,  LinearL_7_GPIO_Port,  LinearL_7_Pin  },
};

/* TODO: proteksi stall actuator - durasi maks HIGH per index belum
 * ditentukan, isi kalau udah ada angka pasti dari tes fisik. */
static uint32_t waktuMulaiAktif[JUMLAH_ACTUATOR];
static int8_t   arahTerakhir[JUMLAH_ACTUATOR];
static const int8_t ARAH_FISIK_MOTOR[JUMLAH_MOTOR] = {1, -1, 1, -1};

volatile uint8_t statusLampuBelakang = LAMPU_MATI;
uint8_t lampuBelakangBrightness = 0;
uint32_t waktuBlinkTerakhir = 0;
uint8_t statusBlinkSekarang = 0;

/* ---- Komunikasi GCS/RF (USART2, 15 byte request / 11 byte reply) ---- */
static uint8_t gcsRxBuf[GCS_FRAME_LEN];
static uint8_t gcsFrameKerja[GCS_FRAME_LEN];
volatile uint8_t gcsFrameSiap = 0;
static uint8_t gcsFrameTerakhir[GCS_FRAME_LEN];
static uint8_t gcsBalasanCache[9] = {1U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U};

/* ---- Komunikasi Jetson (USART3, 26 byte down / 19 byte up) ----
 * SENGAJA hitung-byte-manual (bukan ReceiveToIdle kayak USART2) - link
 * Jetson ini lewat kabel langsung (bukan radio), dan ReceiveToIdle
 * ternyata KETERLALU sensitif ke jeda kecil antar byte (misal dari
 * buffering OS/USB di sisi Jetson) - jeda sekecil itu udah dianggap
 * "akhir frame", motong 1 frame 26-byte yang UTUH jadi 2 potongan yang
 * dua-duanya BUKAN 26 byte, akhirnya DIBUANG DUA-DUANYA walau data
 * aslinya gak rusak sama sekali. Ini yang bikin motor "mati sesaat"
 * berkala walau input dari Jetson udah stabil. Hitung-byte-manual gak
 * peduli jeda waktu antar byte SAMA SEKALI - byte boleh nyicil pelan,
 * tetap ke-anggap 1 frame yang sama selama TOTAL 26 byte akhirnya
 * lengkap. waktuByteJetsonTerakhir dipakai buat resync kalau BENERAN ada
 * byte hilang (lihat CekResyncJetson di main loop). */
static uint8_t jetsonRxByte;
static uint8_t jetsonRxBuf[JETSON_DOWN_LEN];
static volatile uint8_t jetsonRxIndex = 0;
static uint8_t jetsonFrameKerja[JETSON_DOWN_LEN];
volatile uint8_t jetsonFrameSiap = 0;
static volatile uint32_t waktuByteJetsonTerakhir = 0;
static uint16_t lrfJarakTerakhir = 0;
static uint8_t  lrfStatusTerakhir = 0;

/* ---- LED indikator (heartbeat + status link) ---- */
static uint32_t waktuFrameJetsonTerakhir = 0;
static uint32_t waktuFrameGcsTerakhir = 0;
/* Flag "sudah lapor" biar DebugPrint failsafe cuma sekali pas BARU
 * masuk kondisi timeout, bukan tiap iterasi while(1) (~ratusan Hz) -
 * kalau tiap loop, log-nya banjir dan malah gak kebaca. */
static uint8_t failsafeJetsonSudahLapor = 0U;
static uint8_t failsafeGcsSudahLapor = 0U;
static uint32_t waktuHeartbeatTerakhir = 0;
static uint8_t  statusHeartbeat = 0;

/* ---- Anti-spam RS485 ---- */
static int8_t  pantiltHorizontalTerakhir = 127;
static int8_t  pantiltVerticalTerakhir = 127;
static int8_t  kameraZoomTerakhir = 127;
static uint8_t slipRingTerakhir = 0xFFU;
static uint8_t lrfPointerTerakhir = 0xFFU;

/* ---- Anti-glitch motor: setPulseFreq() nulis ulang prescaler/ARR timer +
 * HAL_TIM_OC_Start() tiap dipanggil - kalau dipanggil tiap frame Jetson
 * (~20Hz) walau nilainya SAMA PERSIS, ini bikin gangguan sesaat di sinyal
 * PWM (kelihatan di oscilloscope). Sama prinsipnya kayak anti-spam RS485 di
 * atas, cuma buat motor. */
static int8_t  speedMotorTerakhir = 127;
static uint8_t speedTransisiKeNolPending = 0U;

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
static void Pantilt_Gerak(int8_t horizontal, int8_t vertical);
static void Pantilt_PowerSlipRing(uint8_t nyala);

static uint8_t Pelco_Checksum(uint8_t alamat, uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2);
static void Pelco_Kirim(uint8_t alamat, uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2);
static void Kamera_ZoomIn(void);
static void Kamera_ZoomOut(void);
static void Kamera_ZoomStop(void);

static void BridgeLrf_Kirim(uint8_t cmd2, uint8_t data1, uint8_t data2);
static uint8_t BridgeLrf_BacaRespons(uint8_t *cmd1Out, uint8_t *cmd2Out, uint8_t *data1Out, uint8_t *data2Out);
static uint8_t BridgeLrf_BacaJarak(uint16_t *jarakDesimeterOut, uint8_t *hasilLrfOut);
static uint8_t BridgeLrf_Pointer(uint8_t nyala);

static void GcsParseFrame(const uint8_t *frame14, GcsCommand_t *out);
static uint8_t JetsonChecksum(const uint8_t *data, uint8_t panjang);
static void JetsonParseFrame(const uint8_t *frame24, JetsonCommand_t *out);
static void JetsonApplyCommand(const JetsonCommand_t *cmd);
static void JetsonBangunUpFrame(uint8_t *frameOut18);
static void CekResyncJetson(void);

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/* ==== LAYER 1 ==== */

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

/* ==== LAYER 2 ====*/

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
}

/* ==== DEBUG ==== */

static void DebugPrint(const char *format, ...)
{
    char buffer[128];
    va_list args;
    va_start(args, format);
    int panjang = vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    HAL_UART_Transmit(&hlpuart1, (uint8_t *)buffer, (uint16_t)panjang, UART_TX_TIMEOUT_MS);
}

/* ==== RS485 ==== */

static void RS485_KirimFrame(const uint8_t *frame, uint8_t panjang) {
    HAL_UART_Transmit(&huart1, (uint8_t *)frame, panjang, UART_TX_TIMEOUT_MS);
}

/* ---- Pantilt (protokol custom) ---- */

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

/* cmd2 = bitmask arah (kiri=0x04, kanan=0x02, atas=0x08, bawah=0x10) -
 * horizontal & vertical di-OR bareng buat gerak diagonal. data1/data2 =
 * kecepatan horizontal/vertical, bisa aktif bareng. */
static void Pantilt_Gerak(int8_t horizontal, int8_t vertical) {
    uint8_t cmd2 = 0x00;
    uint8_t data1 = 0x00;
    uint8_t data2 = 0x00;

    if (horizontal > 0) {
        cmd2 |= 0x02U; /* kanan */
        data1 = 0x3FU;
    } else if (horizontal < 0) {
        cmd2 |= 0x04U; /* kiri */
        data1 = 0x3FU;
    }

    if (vertical > 0) {
        cmd2 |= 0x08U; /* atas */
        data2 = 0x3FU;
    } else if (vertical < 0) {
        cmd2 |= 0x10U; /* bawah */
        data2 = 0x3FU;
    }

    uint8_t payload5[5] = { 0x00, 0x00, cmd2, data1, data2 };
    Pantilt_Kirim(payload5);
}

static void Pantilt_PowerSlipRing(uint8_t nyala) {
    uint8_t payload5[5] = { 0x00, 0x00, (uint8_t)(nyala ? 0x09U : 0x0BU), 0x00, 0x02 };
    Pantilt_Kirim(payload5);
}

/* BELUM DIIMPLEMENTASI - pantilt BISA dibaca sudutnya, beda dari command
 * gerak/slip ring yang gak pernah balas. Referensi:
 * Testcode/test_bus_pantilt_kamera_lrf.py -> pantilt_baca_sudut().
 * Kirim payload5 = {0x00,0x00,cmd2,0x00,0x00}, cmd2: 0x51=azimuth, 0x53=elevasi.
 * Respons 7 byte (pola sama Pantilt_Kirim, checksum pakai Pantilt_Checksum),
 * payload[3] & payload[4] = data encoder mentah, lalu:
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
    DebugPrint("[RS485] kirim ke bridge LRF (addr=0x%02X) cmd2=0x%02X data1=%02X data2=%02X\r\n",
               ALAMAT_BRIDGE_LRF, cmd2, data1, data2);
    Pelco_Kirim(ALAMAT_BRIDGE_LRF, 0x00, cmd2, data1, data2);
}

/* cmd1Out dititipin bridge buat kode hasil LRF: 0=OK (ada target valid),
 * 1=NT (No Targets), 2=ERR/TTE - lihat LRF_HASIL_* di firmware bridge-nya
 * (Rapih/Code/NucleoG431KB). Byte ini SEBELUMNYA selalu 0x00/gak dipakai. */
static uint8_t BridgeLrf_BacaRespons(uint8_t *cmd1Out, uint8_t *cmd2Out, uint8_t *data1Out, uint8_t *data2Out) {
    uint8_t frame[7];
    HAL_StatusTypeDef status = HAL_UART_Receive(&huart1, frame, 7U, RS485_TIMEOUT_MS);
    if (status != HAL_OK) {
        DebugPrint("[RS485] TIMEOUT nunggu respons bridge LRF (status HAL=%d)\r\n", (int)status);
        return 0U;
    }
    if (Pelco_Checksum(frame[1], frame[2], frame[3], frame[4], frame[5]) != frame[6]) {
        DebugPrint("[RS485] checksum salah dari bridge: %02X %02X %02X %02X %02X %02X %02X\r\n",
                   frame[0], frame[1], frame[2], frame[3], frame[4], frame[5], frame[6]);
        return 0U;
    }
    *cmd1Out  = frame[2];
    *cmd2Out  = frame[3];
    *data1Out = frame[4];
    *data2Out = frame[5];
    DebugPrint("[RS485] respons OK dari addr=0x%02X cmd1=0x%02X cmd2=0x%02X data1=%02X data2=%02X\r\n",
               frame[1], frame[2], frame[3], frame[4], frame[5]);
    return 1U;
}

/* hasilLrfOut diisi cmd1 dari bridge (0=OK/1=NT/2=ERR) kalau return 1 -
 * INDEPENDEN dari return value (return 1 cuma berarti komunikasi sukses,
 * belum tentu LRF nemu target). */
static uint8_t BridgeLrf_BacaJarak(uint16_t *jarakDesimeterOut, uint8_t *hasilLrfOut) {
    uint8_t cmd1, cmd2, data1, data2;
    BridgeLrf_Kirim(CMD2_BACA_JARAK, 0x00, 0x00);
    if (!BridgeLrf_BacaRespons(&cmd1, &cmd2, &data1, &data2)) return 0U;
    *jarakDesimeterOut = (uint16_t)data1 | ((uint16_t)data2 << 8);
    *hasilLrfOut = cmd1;
    return 1U;
}

static uint8_t BridgeLrf_Pointer(uint8_t nyala) {
    uint8_t cmd1, cmd2, data1, data2;
    BridgeLrf_Kirim(CMD2_POINTER, (uint8_t)(nyala ? 1U : 0U), 0x00);
    return BridgeLrf_BacaRespons(&cmd1, &cmd2, &data1, &data2);
}

/* ============================================================================
 * GCS/RF - USART2, 57600. Balas 11 byte ber-marker+checksum tiap 15 byte
 * request diterima - link ini lewat RF beneran, byte bisa geser/rusak di
 * udara, checksum biar gcs_app bisa buang balasan yang gak valid. Status
 * diambil dari gcsBalasanCache (diisi Jetson - lihat JetsonApplyCommand).
 * ==========================================================================*/

static void GcsParseFrame(const uint8_t *frame14, GcsCommand_t *out) {
    out->estop               = frame14[0];
    out->xJoy1                = (int8_t)frame14[1];
    out->yJoy1                = (int8_t)frame14[2];
    out->xJoy2                = (int8_t)frame14[3];
    out->yJoy2                = (int8_t)frame14[4];
    out->zoom                 = (int8_t)frame14[5];
    out->lrf                  = frame14[6];
    out->fLamp                = frame14[7];
    out->bLamp                = frame14[8];
    out->slipRing             = frame14[9];
    out->bodyUpDown           = (int8_t)frame14[10];
    out->motorIndividualId    = frame14[11];
    out->motorIndividualArah  = (int8_t)frame14[12];
    out->kalibrasi            = frame14[13];
    out->mode                 = frame14[14];
}

/* ============================================================================
 * Jetson - USART3, 115200. Jetson yang inisiatif (heartbeat ~20Hz), STM32
 * APPLY command yang diterima LANGSUNG (motor/actuator/lampu/RS485), lalu
 * balas 18 byte (relay GCS terakhir + status LRF real-time).
 * ==========================================================================*/

/* XOR semua byte data (BELUM termasuk byte checksum itu sendiri) - pola
 * sama kayak checksum balasan GCS, dipakai DUA ARAH di link Jetson (down
 * dan up frame) buat nutup celah "byte kegeser/kena noise tapi kebetulan
 * masih diproses seolah valid" yang sebelumnya gak ketahuan sama sekali
 * (link ini SEBELUMNYA gak ada validasi integritas data sama sekali). */
static uint8_t JetsonChecksum(const uint8_t *data, uint8_t panjang) {
    uint8_t checksum = 0U;
    for (uint8_t i = 0; i < panjang; i++) {
        checksum ^= data[i];
    }
    return checksum;
}

static void JetsonParseFrame(const uint8_t *frame24, JetsonCommand_t *out) {
    out->speed = (int8_t)frame24[0];
    for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
        out->act[i] = (int8_t)frame24[1U + i];
    }
    out->fLamp               = frame24[9];
    out->bLamp                = frame24[10];
    out->bLampMode             = frame24[11];
    out->pantiltHorizontal     = (int8_t)frame24[12];
    out->pantiltVertical       = (int8_t)frame24[13];
    out->kameraZoom            = (int8_t)frame24[14];
    out->slipRing              = frame24[15];
    out->lrfTrigger            = frame24[16];
    out->gcsReplyStm32Status   = frame24[17];
    out->gcsReplyLrfStatus     = frame24[18];
    out->gcsReplyLrfLsb        = frame24[19];
    out->gcsReplyLrfMsb        = frame24[20];
    out->gcsReplyBoxTerdeteksi = frame24[21];
    out->gcsReplyBoxPusatX     = (int8_t)frame24[22];
    out->gcsReplyBoxPusatY     = (int8_t)frame24[23];
    out->gcsReplyBoxLebar      = frame24[24];
    out->gcsReplyBoxTinggi     = frame24[25];
}

static void JetsonApplyCommand(const JetsonCommand_t *cmd) {
    /* Anti-glitch: cuma re-apply PWM kalau speed BERUBAH - lihat komentar
     * speedMotorTerakhir di atas.
     *
     * Debounce KHUSUS transisi ke 0: kalau speed tiba-tiba 0 padahal
     * sebelumnya jalan, JANGAN langsung diterapin - tunda 1 frame (~50ms)
     * buat konfirmasi. Kalau beneran mau stop (joystick dilepas beneran),
     * frame BERIKUTNYA juga bakal 0 lagi dan baru diterapin di situ. Ini
     * jaga-jaga kalau ada 1 frame Jetson yang kelewat/rusak/telat bikin
     * speed kebaca 0 sesaat doang (dicurigai penyebab motor "ngedip mati
     * sebentar" di oscilloscope pas speed harusnya konstan tinggi).
     * ESTOP/failsafe TETAP langsung motong tanpa nunggu ini - jalur
     * terpisah, gak lewat sini sama sekali. */
    if (cmd->speed == 0 && speedMotorTerakhir != 0) {
        if (!speedTransisiKeNolPending) {
            speedTransisiKeNolPending = 1U;
        } else {
            for (uint8_t i = 0; i < JUMLAH_MOTOR; i++) {
                setMotor(i, 0);
            }
            speedMotorTerakhir = 0;
            speedTransisiKeNolPending = 0U;
        }
    } else {
        speedTransisiKeNolPending = 0U;
        if (cmd->speed != speedMotorTerakhir) {
            for (uint8_t i = 0; i < JUMLAH_MOTOR; i++) {
                setMotor(i, cmd->speed);
            }
            speedMotorTerakhir = cmd->speed;
        }
    }
    for (uint8_t i = 0; i < JUMLAH_ACTUATOR; i++) {
        SetActuator(i, cmd->act[i]);
    }
    Lamp_SetBrightness(&htim1, TIM_CHANNEL_1, cmd->fLamp);
    setLampuBelakang(cmd->bLamp, cmd->bLampMode);

    /* RS485 cuma dikirim kalau nilainya BERUBAH, bukan tiap frame Jetson
     * masuk (~10-20Hz) - tanpa ini bus digempur command identik terus. */
    if (cmd->pantiltHorizontal != pantiltHorizontalTerakhir
            || cmd->pantiltVertical != pantiltVerticalTerakhir) {
        Pantilt_Gerak(cmd->pantiltHorizontal, cmd->pantiltVertical);
        pantiltHorizontalTerakhir = cmd->pantiltHorizontal;
        pantiltVerticalTerakhir = cmd->pantiltVertical;
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
        /* Query, SENGAJA gak di-anti-spam - boleh di-request berkali-kali
         * (misal Core Node kirim ini 1 frame doang pas tombol LRF dilepas). */
        uint16_t jarak;
        uint8_t hasilLrf;
        if (BridgeLrf_BacaJarak(&jarak, &hasilLrf)) {
            lrfJarakTerakhir = jarak;
            /* hasilLrf dari bridge: 0=OK/1=NT/2=ERR -> lrfStatusTerakhir:
             * 1=OK/2=NO_TARGET/3=ERROR (0 direservasi buat gagal komunikasi
             * total, gak pernah dikirim balik dari fungsi ini). */
            lrfStatusTerakhir = (uint8_t)(LRF_STATUS_OK + hasilLrf);
        } else {
            lrfStatusTerakhir = LRF_STATUS_GAGAL_KOMUNIKASI;
        }
    } else if (cmd->lrfTrigger == LRF_TRIGGER_POINTER_ON) {
        /* State (laser nyala sampai dimatiin) - DI-ANTI-SPAM beda dari baca
         * jarak, biar RS485 gak digempur "nyalain laser" tiap frame. */
        if (lrfPointerTerakhir != 1U) {
            BridgeLrf_Pointer(1U);
            lrfPointerTerakhir = 1U;
        }
    } else if (cmd->lrfTrigger == LRF_TRIGGER_POINTER_OFF) {
        if (lrfPointerTerakhir != 0U) {
            BridgeLrf_Pointer(0U);
            lrfPointerTerakhir = 0U;
        }
    }

    /* Simpan buat balasan ke GCS BERIKUTNYA - Jetson yang mutusin isinya,
     * STM32 cuma relay apa adanya (prinsip dumb driver). */
    gcsBalasanCache[0] = cmd->gcsReplyStm32Status;
    gcsBalasanCache[1] = cmd->gcsReplyLrfStatus;
    gcsBalasanCache[2] = cmd->gcsReplyLrfLsb;
    gcsBalasanCache[3] = cmd->gcsReplyLrfMsb;
    gcsBalasanCache[4] = cmd->gcsReplyBoxTerdeteksi;
    gcsBalasanCache[5] = (uint8_t)cmd->gcsReplyBoxPusatX;
    gcsBalasanCache[6] = (uint8_t)cmd->gcsReplyBoxPusatY;
    gcsBalasanCache[7] = cmd->gcsReplyBoxLebar;
    gcsBalasanCache[8] = cmd->gcsReplyBoxTinggi;
}

static void JetsonBangunUpFrame(uint8_t *frameOut18) {
    memcpy(frameOut18, gcsFrameTerakhir, GCS_FRAME_LEN); /* relay 15 byte GCS APA ADANYA */
    frameOut18[GCS_FRAME_LEN + 0] = (uint8_t)(lrfJarakTerakhir & 0xFFU);
    frameOut18[GCS_FRAME_LEN + 1] = (uint8_t)((lrfJarakTerakhir >> 8) & 0xFFU);
    frameOut18[GCS_FRAME_LEN + 2] = lrfStatusTerakhir;
    frameOut18[GCS_FRAME_LEN + 3] = 1U; /* stm32Status: sehat */
    /* Byte terakhir (index 19) = checksum XOR 19 byte sebelumnya. */
    frameOut18[JETSON_UP_LEN - 1U] = JetsonChecksum(frameOut18, JETSON_UP_LEN - 1U);
}

/* ============================================================================
 * LAYER 4 - komunikasi & housekeeping
 * ==========================================================================*/

/* USART2 (GCS/RF) - Pakai ReceiveToIdle: auto "sinkron ulang" tiap ada
 * jeda hening di UART. Kalau jumlah byte gak pas, frame DIBUANG, bukan
 * dipaksa diproses (cegah frame kegeser permanen). Ini link RADIO,
 * genuinely butuh proteksi dari noise/byte hilang di udara. */
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
    }
}

/* USART3 (Jetson) - hitung-byte-manual, lihat komentar panjang di
 * deklarasi jetsonRxBuf soal kenapa BUKAN ReceiveToIdle di link ini. */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART3) {
        waktuByteJetsonTerakhir = HAL_GetTick();
        jetsonRxBuf[jetsonRxIndex++] = jetsonRxByte;
        if (jetsonRxIndex >= JETSON_DOWN_LEN) {
            waktuFrameJetsonTerakhir = HAL_GetTick();
            if (jetsonFrameSiap == 0) {
                memcpy(jetsonFrameKerja, jetsonRxBuf, JETSON_DOWN_LEN);
                jetsonFrameSiap = 1;
            }
            jetsonRxIndex = 0;
        }
        HAL_UART_Receive_IT(&huart3, &jetsonRxByte, 1U);
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART2) {
        HAL_UARTEx_ReceiveToIdle_IT(&huart2, gcsRxBuf, GCS_FRAME_LEN);
    } else if (huart->Instance == USART3) {
        __HAL_UART_CLEAR_OREFLAG(huart);
        jetsonRxIndex = 0U; /* buang akumulasi frame yang mungkin lagi setengah jalan */
        HAL_UART_Receive_IT(&huart3, &jetsonRxByte, 1U);
    }
}

/* Dipanggil tiap loop utama - kalau lagi nampung SEBAGIAN frame Jetson
 * (jetsonRxIndex > 0) tapi udah JETSON_RESYNC_TIMEOUT_MS gak ada byte
 * baru, anggap ada byte yang beneran hilang - buang sisa yang gantung,
 * biar byte BERIKUTNYA yang masuk mulai ngitung dari 0 lagi (gak
 * ke-geser permanen). */
static void CekResyncJetson(void) {
    if (jetsonRxIndex > 0U &&
        (HAL_GetTick() - waktuByteJetsonTerakhir) > JETSON_RESYNC_TIMEOUT_MS) {
        jetsonRxIndex = 0U;
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
  setLampuBelakang(0, LAMPU_MATI);

  memset(gcsFrameTerakhir, 0, GCS_FRAME_LEN);
  HAL_UARTEx_ReceiveToIdle_IT(&huart2, gcsRxBuf, GCS_FRAME_LEN);
  HAL_UART_Receive_IT(&huart3, &jetsonRxByte, 1U);
  waktuByteJetsonTerakhir = HAL_GetTick();

  DebugPrint("\r\n=== motorugv_G474RE Boot OK ===\r\n");

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    CekResyncJetson();

    if (statusLampuBelakang == LAMPU_KEDIP) {
        if (HAL_GetTick() - waktuBlinkTerakhir >= BLINK_INTERVAL_MS) {
            statusBlinkSekarang = !statusBlinkSekarang;
            Lamp_SetBrightness(&htim1, TIM_CHANNEL_2,
                statusBlinkSekarang ? lampuBelakangBrightness : 0);
            waktuBlinkTerakhir = HAL_GetTick();
        }
    }

    /* LED heartbeat - bukti main loop masih jalan (beda dari LED link
     * yang bisa nyala terus walau loop hang, itu cuma ngecek timestamp). */
    if (HAL_GetTick() - waktuHeartbeatTerakhir >= HEARTBEAT_INTERVAL_MS) {
        statusHeartbeat = !statusHeartbeat;
        HAL_GPIO_WritePin(LED_Heartbeat_GPIO_Port, LED_Heartbeat_Pin,
            statusHeartbeat ? GPIO_PIN_SET : GPIO_PIN_RESET);
        waktuHeartbeatTerakhir = HAL_GetTick();
    }

    /* LED status link - nyala kalau ada frame VALID dalam batas timeout
     * link masing-masing terakhir, mati kalau link putus/timeout. */
    HAL_GPIO_WritePin(LED_Jetson_GPIO_Port, LED_Jetson_Pin,
        (HAL_GetTick() - waktuFrameJetsonTerakhir < JETSON_LINK_TIMEOUT_MS) ? GPIO_PIN_SET : GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LED_RF_GPIO_Port, LED_RF_Pin,
        (HAL_GetTick() - waktuFrameGcsTerakhir < GCS_LINK_TIMEOUT_MS) ? GPIO_PIN_SET : GPIO_PIN_RESET);

    /* FAILSAFE: Jetson gak kirim frame valid selama JETSON_LINK_TIMEOUT_MS -
     * paksa stop, jangan nurut command terakhir tanpa batas waktu.
     * Motor/actuator aman di-stop tiap loop (murah). Pantilt/kamera RS485
     * SENGAJA cuma kirim SEKALI pas transisi, biar gak spam RS485. */
    if (HAL_GetTick() - waktuFrameJetsonTerakhir >= JETSON_LINK_TIMEOUT_MS) {
        if (!failsafeJetsonSudahLapor) {
            DebugPrint("[FAILSAFE] JETSON timeout - udah %lums gak ada frame valid\r\n",
                       HAL_GetTick() - waktuFrameJetsonTerakhir);
            failsafeJetsonSudahLapor = 1U;
        }
        /* gcsBalasanCache[0] (stm32_status) CUMA di-update pas ada frame
         * Jetson BARU (lihat JetsonApplyCommand) - kalau gak di-reset di
         * sini, dia nyangkut "sehat" (1) SELAMANYA walau Jetson-nya udah
         * putus, dan GCS app gak akan pernah tau ("Controller: OK" palsu). */
        gcsBalasanCache[0] = 0U;
        stopSemuaMotor();
        speedMotorTerakhir = 0;
        StopSemuaActuator();
        if (pantiltHorizontalTerakhir != 0 || pantiltVerticalTerakhir != 0) {
            Pantilt_Gerak(0, 0);
            pantiltHorizontalTerakhir = 0;
            pantiltVerticalTerakhir = 0;
        }
        if (kameraZoomTerakhir != 0) {
            Kamera_ZoomStop();
            kameraZoomTerakhir = 0;
        }
        if (slipRingTerakhir != 0) {
            Pantilt_PowerSlipRing(0);
            slipRingTerakhir = 0;
        }
        if (lrfPointerTerakhir != 0U) {
            BridgeLrf_Pointer(0U);
            lrfPointerTerakhir = 0U;
        }
    } else {
        failsafeJetsonSudahLapor = 0U;
    }

    if (jetsonFrameSiap) {
        uint8_t salinanJetson[JETSON_DOWN_LEN];
        memcpy(salinanJetson, jetsonFrameKerja, JETSON_DOWN_LEN);
        jetsonFrameSiap = 0;

        /* Byte terakhir (index 26) = checksum, data aslinya cuma 26 byte
         * pertama (index 0-25). Checksum salah -> frame ini DIBUANG total
         * (gak di-apply, gak dibalas) - command LAMA tetap jalan sampai
         * frame BERIKUTNYA valid atau failsafe Jetson yang ambil alih. */
        if (salinanJetson[JETSON_DOWN_LEN - 1U] != JetsonChecksum(salinanJetson, JETSON_DOWN_LEN - 1U)) {
            DebugPrint("[JETSON] checksum salah, frame dibuang\r\n");
        } else {
            JetsonCommand_t cmd;
            JetsonParseFrame(salinanJetson, &cmd);
            JetsonApplyCommand(&cmd);

            uint8_t upFrame[JETSON_UP_LEN];
            JetsonBangunUpFrame(upFrame);
            HAL_UART_Transmit(&huart3, upFrame, JETSON_UP_LEN, UART_TX_TIMEOUT_MS);

            DebugPrint("Jetson RX: speed=%d flamp=%u blamp=%u pantiltH=%d pantiltV=%d zoom=%d lrfTrig=%u\r\n",
                cmd.speed, cmd.fLamp, cmd.bLamp, cmd.pantiltHorizontal, cmd.pantiltVertical, cmd.kameraZoom, cmd.lrfTrigger);
        }
    }

    if (gcsFrameSiap) {
        uint8_t salinanGcs[GCS_FRAME_LEN];
        memcpy(salinanGcs, gcsFrameKerja, GCS_FRAME_LEN);
        gcsFrameSiap = 0;

        memcpy(gcsFrameTerakhir, salinanGcs, GCS_FRAME_LEN); /* buat di-relay ke Jetson */

        GcsCommand_t cmd;
        GcsParseFrame(salinanGcs, &cmd);

        DebugPrint("GCS RX: estop=%u xj1=%d yj1=%d xj2=%d yj2=%d flamp=%u blamp=%u kalibrasi=%u\r\n",
            cmd.estop, cmd.xJoy1, cmd.yJoy1, cmd.xJoy2, cmd.yJoy2,
            cmd.fLamp, cmd.bLamp, cmd.kalibrasi);

        uint8_t balasanFrame[GCS_REPLY_LEN];
        balasanFrame[0] = GCS_REPLY_MARKER;
        for (uint8_t i = 0; i < 9U; i++) {
            balasanFrame[1U + i] = gcsBalasanCache[i];
        }
        uint8_t checksum = 0U;
        for (uint8_t i = 1; i < GCS_REPLY_LEN - 1U; i++) {
            checksum ^= balasanFrame[i];
        }
        balasanFrame[GCS_REPLY_LEN - 1U] = checksum;
        HAL_UART_Transmit(&huart2, balasanFrame, GCS_REPLY_LEN, UART_TX_TIMEOUT_MS);
    }

    /* FAILSAFE: GCS gak kirim frame valid selama GCS_LINK_TIMEOUT_MS - paksa
     * stop, SAMA PRINSIPNYA kayak failsafe Jetson di atas, tapi ini nutup
     * celah yang failsafe Jetson GAK bisa tangkep: Jetson bisa tetap sehat
     * & terus ngirim command LAMA berulang-ulang walau GCS-nya udah
     * disconnect/mati total (link Jetson<->STM32 gak ikut putus cuma
     * gara-gara GCS mati) - Jetson gak pernah tau GCS-nya udah gak ngirim
     * apa-apa lagi. Makanya ini WAJIB diletakkan SETELAH blok
     * jetsonFrameSiap di atas, biar override apapun yang baru aja di-apply
     * JetsonApplyCommand() di siklus yang sama. */
    if (HAL_GetTick() - waktuFrameGcsTerakhir >= GCS_LINK_TIMEOUT_MS) {
        if (!failsafeGcsSudahLapor) {
            DebugPrint("[FAILSAFE] GCS timeout - udah %lums gak ada frame valid\r\n",
                       HAL_GetTick() - waktuFrameGcsTerakhir);
            failsafeGcsSudahLapor = 1U;
        }
        stopSemuaMotor();
        speedMotorTerakhir = 0;
        StopSemuaActuator();
        if (pantiltHorizontalTerakhir != 0 || pantiltVerticalTerakhir != 0) {
            Pantilt_Gerak(0, 0);
            pantiltHorizontalTerakhir = 0;
            pantiltVerticalTerakhir = 0;
        }
        if (kameraZoomTerakhir != 0) {
            Kamera_ZoomStop();
            kameraZoomTerakhir = 0;
        }
        if (slipRingTerakhir != 0) {
            Pantilt_PowerSlipRing(0);
            slipRingTerakhir = 0;
        }
        if (lrfPointerTerakhir != 0U) {
            BridgeLrf_Pointer(0U);
            lrfPointerTerakhir = 0U;
        }
    } else {
        failsafeGcsSudahLapor = 0U;
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
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, MotorS_1_Pin|LinearR_5_Pin|MotorS_3_Pin|LinearR_7_Pin
                          |MotorS_2_Pin|LinearR_1_Pin|LinearL_4_Pin|LinearR_0_Pin
                          |LinearR_4_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, LinearR_2_Pin|LinearL_2_Pin|LinearL_5_Pin|MotorS_0_Pin
                          |LinearL_1_Pin|LinearL_6_Pin|LinearL_7_Pin|LinearR_6_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, LED_Jetson_Pin|LED_RF_Pin|LED_Heartbeat_Pin|LinearL_3_Pin
                          |LinearR_3_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(LinearL_0_GPIO_Port, LinearL_0_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : MotorS_1_Pin LinearR_5_Pin MotorS_3_Pin LinearR_7_Pin
                           MotorS_2_Pin LinearR_1_Pin LinearL_4_Pin LinearR_0_Pin
                           LinearR_4_Pin */
  GPIO_InitStruct.Pin = MotorS_1_Pin|LinearR_5_Pin|MotorS_3_Pin|LinearR_7_Pin
                          |MotorS_2_Pin|LinearR_1_Pin|LinearL_4_Pin|LinearR_0_Pin
                          |LinearR_4_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : LinearR_2_Pin LinearL_2_Pin LinearL_5_Pin MotorS_0_Pin
                           LinearL_1_Pin LinearL_6_Pin LinearL_7_Pin LinearR_6_Pin */
  GPIO_InitStruct.Pin = LinearR_2_Pin|LinearL_2_Pin|LinearL_5_Pin|MotorS_0_Pin
                          |LinearL_1_Pin|LinearL_6_Pin|LinearL_7_Pin|LinearR_6_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : LED_Jetson_Pin LED_RF_Pin LED_Heartbeat_Pin LinearL_3_Pin
                           LinearR_3_Pin */
  GPIO_InitStruct.Pin = LED_Jetson_Pin|LED_RF_Pin|LED_Heartbeat_Pin|LinearL_3_Pin
                          |LinearR_3_Pin;
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
