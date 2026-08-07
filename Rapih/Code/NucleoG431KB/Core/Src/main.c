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
#include <stdarg.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* =====================================================================
 * BRIDGE LRF - RS485 Pelco-D <-> LRF native, NUCLEO-G431KB (STM32G431KBTx)
 * =====================================================================
 * USART1 (PB6=TX, PB7=RX) --TTL-- [modul RS485-to-TTL] --RS485-- bus bersama
 *   (Pantilt address=0, Kamera address=1, Bridge LRF ini address=2)
 *
 * USART2 (PB3=TX, PB4=RX) --TTL langsung (TANPA modul)-- LRF127
 *
 * LPUART1 (PA2=TX, PA3=RX) -- DEBUG ONLY, sudah di-setup CubeMX lewat
 *   BSP_COM_Init(COM1, ...) di main() -- jalan lewat ST-LINK VCP (USB
 *   yang sama buat flashing). Semua log lewat DebugPrint() ke
 *   hcom_uart[COM1], TIDAK PERNAH nyentuh USART1/USART2 supaya gak
 *   ganggu protokol asli.
 *
 * PENTING soal timing debug: JANGAN print / JANGAN transmit blocking di
 * dalam HAL_UART_RxCpltCallback (ISR) - bus jalan di 9600 baud (~1ms per
 * byte). Kalau ISR sibuk >1ms, byte berikutnya bisa KELEWAT atau malah
 * bikin OVERRUN ERROR - fix-nya ada di HAL_UART_ErrorCallback di bawah.
 * Makanya ISR di sini CUMA nyusun frame buffer (murah & cepat), semua
 * print & proses berat dilakuin di main loop.
 * ===================================================================== */
#define ALAMAT_BRIDGE_LRF     0x02U   /* address Pelco-D milik bridge ini di bus bersama */
#define CMD2_BACA_JARAK       0x01U
#define CMD2_POINTER          0x02U

/* Kode hasil baca LRF, dititipkan di byte cmd1 punya frame balasan Pelco-D
 * (byte itu sebelumnya SIA-SIA, selalu 0x00, gak dipakai custom command
 * bridge ini) - biar G474RE & main app bisa bedain "sukses dapet jarak
 * valid" vs "sukses eksekusi tapi LRF gak nemu target" vs "ada error LRF",
 * tanpa nambah ukuran frame Pelco-D sama sekali. */
#define LRF_HASIL_OK          0x00U   /* ada target valid */
#define LRF_HASIL_NT          0x01U   /* No Targets - LRF eksekusi normal, gak ketemu target */
#define LRF_HASIL_ERR         0x02U   /* ERR/TTE dilaporkan LRF */

/* SMM biasa (bukan Quick SMM1) butuh ~1.3 detik nominal buat ngukur (vs Quick
 * SMM1 yang jauh lebih cepat tapi jarak efektifnya lebih pendek/kurang
 * sensitif) - TAPI datasheet resmi (Table 8, ICD O50052CE v3.3) bilang "at
 * bad weather conditions measurement time can be about 300ms longer", jadi
 * worst-case beneran ~1.6 detik. Timeout ini WAJIB lebih panjang dari itu. */
#define LRF_TIMEOUT_MS         2000U
#define DEBUG_STATUS_INTERVAL_MS  1000U  /* heartbeat status di main loop, tiap 1 detik */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

COM_InitTypeDef BspCOMInit;

UART_HandleTypeDef huart1;
UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */
/* ---- penerima frame Pelco-D dari bus bersama (USART1, PB6/PB7), fixed 7 byte ----
 * Pakai ReceiveToIdle (bukan hitung byte manual) - auto "sinkron ulang" tiap
 * ada jeda hening di UART. Kalau ukuran frame gak pas 7 byte atau gak diawali
 * 0xFF, DIBUANG total - bukan dipaksa diproses (cegah frame kegeser permanen
 * kalau ada 1 byte hilang/rusak gara-gara noise/goyangan kabel). */
static uint8_t frameRxBufBus[7];
static uint8_t frameKerjaBus[7];
static volatile uint8_t frameSiapBus = 0;

/* ---- counter buat debug, cuma di-increment di ISR, dibaca di main loop ---- */
static volatile uint32_t totalFrameLengkapBus = 0;
static volatile uint32_t totalFrameBuangBus = 0;
static uint32_t waktuDebugTerakhir = 0;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_USART2_UART_Init(void);
/* USER CODE BEGIN PFP */
static void DebugPrint(const char *format, ...);
static void DebugPrintFrame(const char *label, const uint8_t *frame, uint8_t panjang);
static uint8_t PelcoD_Checksum(uint8_t alamat, uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2);
static void KirimResponsPelcoD(uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2);
static uint8_t LRF_Checksum(const uint8_t *payload, uint8_t panjang);
static uint8_t LRF_BacaJarak(float *jarakKeluar, uint8_t *hasilLrfOut);
static uint8_t LRF_Pointer(uint8_t nyala);
static void ProsesFramePelcoD(const uint8_t *frame);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* ============================= DEBUG (lewat LPUART1 / ST-LINK VCP) ============================= */

static void DebugPrint(const char *format, ...)
{
    char buffer[128];
    va_list args;
    va_start(args, format);
    int panjang = vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    if (panjang > 0) {
        HAL_UART_Transmit(&hcom_uart[COM1], (uint8_t *)buffer, (uint16_t)panjang, 100U);
    }
}

static void DebugPrintFrame(const char *label, const uint8_t *frame, uint8_t panjang)
{
    char buffer[64];
    int posisi = 0;
    for (uint8_t i = 0; i < panjang && posisi < (int)sizeof(buffer) - 4; i++) {
        posisi += snprintf(&buffer[posisi], sizeof(buffer) - posisi, "%02X ", frame[i]);
    }
    DebugPrint("%s: %s\r\n", label, buffer);
}

/* ============================= PELCO-D (sisi bus bersama, USART1) ============================= */

static uint8_t PelcoD_Checksum(uint8_t alamat, uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2)
{
    return (uint8_t)((alamat + cmd1 + cmd2 + data1 + data2) % 256U);
}

static void KirimResponsPelcoD(uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2)
{
    uint8_t frame[7];
    frame[0] = 0xFFU;
    frame[1] = ALAMAT_BRIDGE_LRF;
    frame[2] = cmd1; /* kode hasil LRF - LRF_HASIL_OK/NT/ERR */
    frame[3] = cmd2;
    frame[4] = data1;
    frame[5] = data2;
    frame[6] = PelcoD_Checksum(ALAMAT_BRIDGE_LRF, cmd1, cmd2, data1, data2);

    DebugPrintFrame("[TX bus] kirim respons", frame, 7U);
    HAL_UART_Transmit(&huart1, frame, sizeof(frame), 100U);
}

/* ============================= LRF NATIVE (sisi LRF, USART2) ============================= */

static uint8_t LRF_Checksum(const uint8_t *payload, uint8_t panjang)
{
    uint16_t jumlah = 0;
    for (uint8_t i = 0; i < panjang; i++) {
        jumlah += payload[i];
    }
    return (uint8_t)((jumlah % 256U) ^ 0x50U);
}

/**
 * @brief Buang byte nyasar yang mungkin masih ngendon di RX USART2 (LRF) +
 *        bersihin error flag, sebelum mulai transaksi baru. WAJIB dipanggil
 *        sebelum tiap kirim command ke LRF - kalau enggak, respons yang
 *        datang TELAT (misal gara-gara LRF_TIMEOUT_MS kelewat sekali) bakal
 *        numpuk di buffer dan bikin transaksi BERIKUTNYA salah baca terus-
 *        terusan (sekali gagal, gagal selamanya - byte nyasar nambah tiap
 *        percobaan). Prinsip yang sama kayak ser.reset_input_buffer() yang
 *        dipakai di Testcode/test_bus_pantilt_kamera_lrf.py.
 */
static void LRF_FlushRx(void)
{
    while (__HAL_UART_GET_FLAG(&huart2, UART_FLAG_RXNE)) {
        (void)huart2.Instance->RDR; /* baca & buang byte nyasar */
    }
    __HAL_UART_CLEAR_OREFLAG(&huart2);
    __HAL_UART_CLEAR_FEFLAG(&huart2);
    __HAL_UART_CLEAR_NEFLAG(&huart2);
}

/**
 * @brief Minta LRF baca jarak (SMM biasa - lebih lambat tapi jarak efektif
 *        lebih jauh & akurat dibanding Quick SMM1), tunggu respons, validasi
 *        checksum.
 * @param jarakKeluar: pointer output, diisi jarak target 1 dalam meter kalau sukses
 * @param hasilLrfOut: pointer output, diisi LRF_HASIL_OK/NT/ERR kalau sukses
 *                      (baca komunikasi berhasil - independen dari apa LRF
 *                      beneran nemu target atau enggak)
 * @retval 1 = sukses & valid (komunikasi OK, cek hasilLrfOut buat detail),
 *         0 = gagal komunikasi (timeout/checksum salah/header salah)
 */
static uint8_t LRF_BacaJarak(float *jarakKeluar, uint8_t *hasilLrfOut)
{
    uint8_t payload[4] = {0xCCU, 0x00U, 0x00U, 0x00U}; /* 0x00 = SMM biasa (bukan Quick SMM1) */
    uint8_t frame[5];
    memcpy(frame, payload, 4);
    frame[4] = LRF_Checksum(payload, 4);

    LRF_FlushRx();
    DebugPrintFrame("[TX LRF] minta jarak", frame, 5U);
    HAL_UART_Transmit(&huart2, frame, sizeof(frame), 100U);

    uint8_t respons[22];
    HAL_StatusTypeDef status = HAL_UART_Receive(&huart2, respons, sizeof(respons), LRF_TIMEOUT_MS);
    if (status != HAL_OK) {
        DebugPrint("[RX LRF] TIMEOUT nunggu jarak (status HAL=%d)\r\n", (int)status);
        return 0U; /* timeout - LRF gak jawab */
    }
    DebugPrintFrame("[RX LRF] jarak mentah", respons, 22U);
    if (respons[0] != 0x59U || respons[1] != 0xCCU) {
        DebugPrint("[RX LRF] header salah (harusnya 59 CC)\r\n");
        return 0U; /* header salah */
    }
    if (LRF_Checksum(respons, 21U) != respons[21]) {
        DebugPrint("[RX LRF] checksum salah (dpt=%02X, harusnya=%02X)\r\n",
                   respons[21], LRF_Checksum(respons, 21U));
        return 0U; /* checksum gak valid */
    }

    memcpy(jarakKeluar, &respons[2], sizeof(float)); /* float32 little-endian, byte 2-5 */

    /* Status byte #3 di respons[20] - SEBELUMNYA gak pernah dibaca sama
     * sekali, padahal ini yang bisa jelasin kenapa jarak keluar 0.0 (misal
     * flag NT = "No Targets", LRF eksekusi normal tapi emang gak ketemu
     * target valid, BUKAN kegagalan komunikasi). Bit position dikonfirmasi
     * dari datasheet resmi (ICD O50052CE v3.3, section 3.4, tabel detail
     * halaman 12 - bukan diagram ringkas halaman 9 yang keliru nulis "NR"
     * di bit 3, padahal NR itu punya status byte 1, bukan byte 3). */
    uint8_t statusByte = respons[20];
    if (statusByte & 0x40U) {
        DebugPrint("[RX LRF] status: MT (Multiple Targets)\r\n");
    }
    if (statusByte & 0x20U) {
        DebugPrint("[RX LRF] status: NT (No Targets) - LRF gak ketemu target valid\r\n");
    }
    if (statusByte & 0x10U) {
        DebugPrint("[RX LRF] status: ERR - ada error dilaporkan LRF (cek status byte 1&2 lewat command 0xC7)\r\n");
    }
    if (statusByte & 0x04U) {
        DebugPrint("[RX LRF] status: TTE (Transmitter Timing Error)\r\n");
    }
    if (statusByte == 0U) {
        DebugPrint("[RX LRF] status: bersih (0x00), gak ada flag aktif\r\n");
    }

    /* NT diprioritaskan (jarak 0.0 emang gak valid), baru ERR/TTE, sisanya
     * (termasuk MT - tetap ada target valid, cuma lebih dari satu) OK. */
    if (statusByte & 0x20U) {
        *hasilLrfOut = LRF_HASIL_NT;
    } else if (statusByte & (0x10U | 0x04U)) {
        *hasilLrfOut = LRF_HASIL_ERR;
    } else {
        *hasilLrfOut = LRF_HASIL_OK;
    }

    DebugPrint("[RX LRF] jarak OK = %d cm (status byte=0x%02X)\r\n", (int)(*jarakKeluar * 100.0f), statusByte);
    return 1U;
}

/**
 * @brief Nyala/matiin pointer alignment LRF, tunggu standard ack.
 * @retval 1 = sukses (ack diterima & valid), 0 = gagal
 */
static uint8_t LRF_Pointer(uint8_t nyala)
{
    uint8_t payload[2] = {0xC5U, nyala ? 0x02U : 0x00U};
    uint8_t frame[3];
    memcpy(frame, payload, 2);
    frame[2] = LRF_Checksum(payload, 2);

    LRF_FlushRx();
    DebugPrintFrame("[TX LRF] set pointer", frame, 3U);
    HAL_UART_Transmit(&huart2, frame, sizeof(frame), 100U);

    uint8_t respons[4];
    HAL_StatusTypeDef status = HAL_UART_Receive(&huart2, respons, sizeof(respons), LRF_TIMEOUT_MS);
    if (status != HAL_OK) {
        DebugPrint("[RX LRF] TIMEOUT nunggu ack pointer (status HAL=%d)\r\n", (int)status);
        return 0U;
    }
    DebugPrintFrame("[RX LRF] ack pointer", respons, 4U);
    uint8_t checksumHitung = LRF_Checksum(respons, 3U);
    if (respons[0] != 0x59U || respons[1] != 0xC5U ||
        respons[2] != 0x3CU || respons[3] != checksumHitung) {
        DebugPrint("[RX LRF] format ack gak sesuai (dpt echo=%02X chk=%02X, harusnya echo=C5 chk=%02X)\r\n",
                   respons[1], respons[3], checksumHitung);
        return 0U;
    }
    return 1U;
}

/* ============================= LOGIC UTAMA BRIDGE ============================= */

/**
 * @brief Proses 1 frame Pelco-D lengkap (7 byte) yang masuk dari bus bersama.
 *        Kalau address-nya BUKAN buat bridge ini, atau checksum gak valid,
 *        frame DIABAIKAN TOTAL (bukan diproses sebagian) - konsisten sama
 *        prinsip yang sudah dipakai di semua firmware lain di project ini.
 */
static void ProsesFramePelcoD(const uint8_t *frame)
{
    uint8_t alamat = frame[1];
    uint8_t cmd1   = frame[2];
    uint8_t cmd2   = frame[3];
    uint8_t data1  = frame[4];
    uint8_t data2  = frame[5];
    uint8_t checksumDiterima = frame[6];

    if (alamat != ALAMAT_BRIDGE_LRF) {
        DebugPrint("[BUS] frame buat address 0x%02X, bukan bridge ini (0x%02X) - diabaikan\r\n",
                   alamat, ALAMAT_BRIDGE_LRF);
        return; /* bukan buat bridge ini - abaikan, biarkan device lain di bus yang jawab */
    }
    uint8_t checksumHitung = PelcoD_Checksum(alamat, cmd1, cmd2, data1, data2);
    if (checksumHitung != checksumDiterima) {
        DebugPrint("[BUS] checksum salah! dpt=%02X hitung=%02X - frame diabaikan\r\n",
                   checksumDiterima, checksumHitung);
        return; /* checksum gak valid - abaikan total */
    }
    DebugPrint("[BUS] frame VALID buat bridge ini, cmd2=0x%02X data1=%02X data2=%02X\r\n",
               cmd2, data1, data2);

    if (cmd2 == CMD2_BACA_JARAK) {
        float jarak;
        uint8_t hasilLrf = LRF_HASIL_OK;
        if (LRF_BacaJarak(&jarak, &hasilLrf) != 0U) {
            float desimeterF = jarak * 10.0f;
            if (desimeterF < 0.0f) desimeterF = 0.0f;
            if (desimeterF > 65535.0f) desimeterF = 65535.0f; /* clamp, jaga-jaga overflow */
            uint16_t jarakDesimeter = (uint16_t)desimeterF;
            KirimResponsPelcoD(hasilLrf, CMD2_BACA_JARAK,
                                (uint8_t)(jarakDesimeter & 0xFFU),
                                (uint8_t)((jarakDesimeter >> 8) & 0xFFU));
        } else {
            DebugPrint("[BUS] LRF_BacaJarak gagal - SENGAJA gak kirim respons ke bus\r\n");
        }
        /* kalau LRF_BacaJarak gagal KOMUNIKASI (bukan NT/ERR - itu tetap
         * sukses komunikasi), SENGAJA gak kirim respons apa-apa - master di
         * sisi Jetson akan timeout & boleh retry sendiri, bukan tanggung
         * jawab bridge ini buat nebak-nebak nilai default */
    } else if (cmd2 == CMD2_POINTER) {
        uint8_t nyala = (data1 != 0U) ? 1U : 0U;
        if (LRF_Pointer(nyala) != 0U) {
            KirimResponsPelcoD(LRF_HASIL_OK, CMD2_POINTER, nyala, 0U);
        } else {
            DebugPrint("[BUS] LRF_Pointer gagal - SENGAJA gak kirim respons ke bus\r\n");
        }
    } else {
        DebugPrint("[BUS] cmd2=0x%02X gak dikenal, diabaikan\r\n", cmd2);
    }
}

/**
 * @brief Callback event UART - dipanggil tiap ada jeda hening (idle) di bus
 *        ATAU buffer 7 byte penuh, mana yang duluan. Ini yang bikin auto
 *        "sinkron ulang": kalau ada byte hilang/rusak di tengah jalan
 *        (noise, kabel goyang), Size bakal gak pas 7 - frame itu DIBUANG,
 *        tapi penerimaan BERIKUTNYA tetap mulai bersih dari 0, gak pernah
 *        kegeser permanen kayak versi hitung-byte-manual yang lama.
 */
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
    if (huart->Instance == USART1) {
        if (Size == 7U && frameRxBufBus[0] == 0xFFU) {
            if (frameSiapBus == 0U) {
                memcpy(frameKerjaBus, frameRxBufBus, 7U);
                frameSiapBus = 1U;
                totalFrameLengkapBus++;
            }
        } else {
            totalFrameBuangBus++;
        }
        HAL_UARTEx_ReceiveToIdle_IT(&huart1, frameRxBufBus, 7U);
    }
}

/**
 * @brief Dipanggil kalau ada error UART (overrun/framing/noise/parity) di
 *        USART1. WAJIB re-arm HAL_UARTEx_ReceiveToIdle_IT lagi di sini -
 *        kalau enggak, USART1 bakal diam PERMANEN setelah error pertama.
 */
void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1) {
        totalFrameBuangBus++;
        HAL_UARTEx_ReceiveToIdle_IT(&huart1, frameRxBufBus, 7U);
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
  MX_USART1_UART_Init();
  MX_USART2_UART_Init();
  /* USER CODE BEGIN 2 */

  /* USER CODE END 2 */

  /* Initialize leds */
  BSP_LED_Init(LED_GREEN);

  /* Initialize COM1 port (115200, 8 bits (7-bit data + 1 stop bit), no parity */
  BspCOMInit.BaudRate   = 115200;
  BspCOMInit.WordLength = COM_WORDLENGTH_8B;
  BspCOMInit.StopBits   = COM_STOPBITS_1;
  BspCOMInit.Parity     = COM_PARITY_NONE;
  BspCOMInit.HwFlowCtl  = COM_HWCONTROL_NONE;
  if (BSP_COM_Init(COM1, &BspCOMInit) != BSP_ERROR_NONE)
  {
    Error_Handler();
  }

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  DebugPrint("\r\n\r\n=== BRIDGE LRF NUCLEO-G431KB - BOOT ===\r\n");
  DebugPrint("Alamat bridge di bus = 0x%02X, baudrate USART1/USART2 = 9600\r\n", ALAMAT_BRIDGE_LRF);

  /* Mulai dengerin bus bersama (USART1, PB6/PB7) - ReceiveToIdle, auto
   * sinkron ulang tiap ada jeda hening di bus */
  HAL_UARTEx_ReceiveToIdle_IT(&huart1, frameRxBufBus, 7U);
  DebugPrint("USART1 (bus) siap dengerin (ReceiveToIdle).\r\n");

  /* USART2 (ke LRF) SENGAJA gak start receive-IT di sini - LRF_BacaJarak()
   * dan LRF_Pointer() pakai HAL_UART_Receive() blocking dengan timeout,
   * karena pola komunikasinya request-lalu-tunggu-respons (bukan streaming
   * bebas kayak bus bersama), jadi blocking read di sini aman & lebih
   * simpel daripada state machine interrupt kedua. */
  while (1)
  {

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    if (frameSiapBus) {
        uint8_t salinanLokal[7];
        memcpy(salinanLokal, frameKerjaBus, 7U);
        frameSiapBus = 0U;
        DebugPrintFrame("[RX bus] frame lengkap", salinanLokal, 7U);
        ProsesFramePelcoD(salinanLokal);
    }

    /* Heartbeat status tiap 1 detik. */
    if (HAL_GetTick() - waktuDebugTerakhir >= DEBUG_STATUS_INTERVAL_MS) {
        waktuDebugTerakhir = HAL_GetTick();
        DebugPrint("[STATUS] frame lengkap=%lu frame dibuang=%lu\r\n",
                   totalFrameLengkapBus, totalFrameBuangBus);
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
  huart2.Init.BaudRate = 9600;
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
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pins : PA2 PA3 */
  GPIO_InitStruct.Pin = GPIO_PIN_2|GPIO_PIN_3;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  GPIO_InitStruct.Alternate = GPIO_AF12_LPUART1;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * File Name          :
  * Description        :
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

/**
  * @}
  */

/**
  * @}
  */

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
