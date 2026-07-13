/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body - LRF Bridge (RS485 Pelco-D <-> LRF native)
  *                    VERSI DEBUG - nambah log ASCII lewat LPUART1 (PA2=TX/PA3=RX)
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
#include <stdio.h>
#include <stdarg.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* =====================================================================
 * KONSEP BRIDGE INI (lihat diskusi lengkap di chat):
 * =====================================================================
 * USART1 (PB6=TX, PB7=RX) --TTL-- [modul RS485-to-TTL] --RS485-- bus bersama
 *   (Pantilt address=0, Kamera address=1, Bridge LRF ini address=2)
 *
 * USART2 (PB3=TX, PB4=RX) --TTL langsung (TANPA modul)-- LRF127
 *
 * LPUART1 (PA2=TX, PA3=RX) -- DEBUG ONLY, lewat ST-LINK VCP (USB yang sama
 *   buat flashing). Semua log dikirim ke sini, TIDAK PERNAH nyentuh USART1
 *   atau USART2 supaya gak ganggu protokol asli.
 *
 * PENTING soal timing debug: JANGAN print di dalam HAL_UART_RxCpltCallback
 * (ISR) per-byte - bus jalan di 9600 baud, jarak antar byte cuma ~1ms,
 * sedangkan kirim 1 baris debug text di 115200 baud bisa >2ms -> bisa bikin
 * byte berikutnya di bus KELEWAT (bug baru muncul gara-gara debug-nya
 * sendiri). Makanya ISR cuma NGITUNG (counter), print teksnya dilakuin di
 * main loop (BUKAN interrupt) secara periodik + tiap kali 1 frame lengkap
 * selesai diproses.
 * ===================================================================== */
#define ALAMAT_BRIDGE_LRF     0x02U   /* address Pelco-D milik bridge ini di bus bersama */
#define CMD2_BACA_JARAK       0x01U
#define CMD2_POINTER          0x02U

#define LRF_TIMEOUT_MS         500U   /* timeout tunggu respons LRF - LRF butuh waktu buat lasering */
#define DEBUG_STATUS_INTERVAL_MS  1000U  /* heartbeat status di main loop, tiap 1 detik */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart1;
UART_HandleTypeDef huart2;
/* NOTE: hlpuart1 (LPUART1) HARUS sudah otomatis ke-declare di sini oleh
 * CubeMX setelah kamu enable LPUART1 (PA2/PA3) & generate code. JANGAN
 * tulis ulang manual "UART_HandleTypeDef hlpuart1;" di sini - kalau CubeMX
 * sudah nulis baris itu duluan, bikin kamu punya dobel deklarasi. */

/* USER CODE BEGIN PV */
/* ---- penerima frame Pelco-D dari bus bersama (USART1), fixed 7 byte ---- */
static uint8_t rxByteBus;
static uint8_t frameBufferBus[7];
static volatile uint8_t frameIndexBus = 0;
static volatile uint8_t frameSiapBus = 0;
static uint8_t frameKerjaBus[7];

/* ---- counter buat debug, cuma di-increment di ISR, dibaca di main loop ---- */
static volatile uint32_t totalByteMasukBus = 0;
static volatile uint32_t totalFrameLengkapBus = 0;
static uint32_t waktuDebugTerakhir = 0;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_USART2_UART_Init(void);
/* USER CODE BEGIN PFP */
static void DebugPrint(const char *format, ...);
static uint8_t PelcoD_Checksum(uint8_t alamat, uint8_t cmd1, uint8_t cmd2, uint8_t data1, uint8_t data2);
static void KirimResponsPelcoD(uint8_t cmd2, uint8_t data1, uint8_t data2);
static uint8_t LRF_Checksum(const uint8_t *payload, uint8_t panjang);
static uint8_t LRF_BacaJarak(float *jarakKeluar);
static uint8_t LRF_Pointer(uint8_t nyala);
static void ProsesFramePelcoD(const uint8_t *frame);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* ============================= DEBUG (lewat LPUART1, PA2/PA3) ============================= */

static void DebugPrint(const char *format, ...)
{
    char buffer[128];
    va_list args;
    va_start(args, format);
    int panjang = vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    if (panjang > 0) {
        HAL_UART_Transmit(&hlpuart1, (uint8_t *)buffer, (uint16_t)panjang, 100U);
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

static void KirimResponsPelcoD(uint8_t cmd2, uint8_t data1, uint8_t data2)
{
    uint8_t frame[7];
    frame[0] = 0xFFU;
    frame[1] = ALAMAT_BRIDGE_LRF;
    frame[2] = 0x00U; /* cmd1 gak dipakai buat custom command bridge ini */
    frame[3] = cmd2;
    frame[4] = data1;
    frame[5] = data2;
    frame[6] = PelcoD_Checksum(ALAMAT_BRIDGE_LRF, 0x00U, cmd2, data1, data2);

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
 * @brief Minta LRF baca jarak (Quick SMM1), tunggu respons, validasi checksum.
 * @param jarakKeluar: pointer output, diisi jarak target 1 dalam meter kalau sukses
 * @retval 1 = sukses & valid, 0 = gagal (timeout/checksum salah/header salah)
 */
static uint8_t LRF_BacaJarak(float *jarakKeluar)
{
    uint8_t payload[4] = {0xCCU, 0x10U, 0x00U, 0x00U}; /* 0x10 = Quick SMM1 */
    uint8_t frame[5];
    memcpy(frame, payload, 4);
    frame[4] = LRF_Checksum(payload, 4);

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
    DebugPrint("[RX LRF] jarak OK = %d cm\r\n", (int)(*jarakKeluar * 100.0f));
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

    DebugPrintFrame("[TX LRF] set pointer", frame, 3U);
    HAL_UART_Transmit(&huart2, frame, sizeof(frame), 100U);

    uint8_t respons[4];
    HAL_StatusTypeDef status = HAL_UART_Receive(&huart2, respons, sizeof(respons), LRF_TIMEOUT_MS);
    if (status != HAL_OK) {
        DebugPrint("[RX LRF] TIMEOUT nunggu ack pointer (status HAL=%d)\r\n", (int)status);
        return 0U;
    }
    DebugPrintFrame("[RX LRF] ack pointer", respons, 4U);
    if (respons[0] != 0x59U || respons[2] != 0x3CU) {
        DebugPrint("[RX LRF] format ack gak sesuai\r\n");
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
        if (LRF_BacaJarak(&jarak) != 0U) {
            float desimeterF = jarak * 10.0f;
            if (desimeterF < 0.0f) desimeterF = 0.0f;
            if (desimeterF > 65535.0f) desimeterF = 65535.0f; /* clamp, jaga-jaga overflow */
            uint16_t jarakDesimeter = (uint16_t)desimeterF;
            KirimResponsPelcoD(CMD2_BACA_JARAK,
                                (uint8_t)(jarakDesimeter & 0xFFU),
                                (uint8_t)((jarakDesimeter >> 8) & 0xFFU));
        } else {
            DebugPrint("[BUS] LRF_BacaJarak gagal - SENGAJA gak kirim respons ke bus\r\n");
        }
        /* kalau LRF_BacaJarak gagal, SENGAJA gak kirim respons apa-apa -
         * master di sisi Jetson akan timeout & boleh retry sendiri, bukan
         * tanggung jawab bridge ini buat nebak-nebak nilai default */
    } else if (cmd2 == CMD2_POINTER) {
        uint8_t nyala = (data1 != 0U) ? 1U : 0U;
        if (LRF_Pointer(nyala) != 0U) {
            KirimResponsPelcoD(CMD2_POINTER, nyala, 0U);
        } else {
            DebugPrint("[BUS] LRF_Pointer gagal - SENGAJA gak kirim respons ke bus\r\n");
        }
    } else {
        DebugPrint("[BUS] cmd2=0x%02X gak dikenal, diabaikan\r\n", cmd2);
    }
}

/**
 * @brief Callback interrupt UART - dipanggil tiap 1 byte diterima.
 *        USART1 (bus bersama) : kumpulin 7 byte fixed-length mulai dari
 *        sync 0xFF, baru proses.
 *        SENGAJA GAK ADA DebugPrint/HAL_UART_Transmit APAPUN DI SINI -
 *        ini ISR, dan bus jalan di 9600 baud (~1ms per byte). Kirim debug
 *        text di 115200 baud butuh beberapa ms, cukup buat bikin byte
 *        berikutnya di bus KELEWAT kalau dipanggil di sini. Makanya cuma
 *        counter yang di-increment (murah, aman), print-nya di main loop.
 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1) {
        totalByteMasukBus++;
        if (frameIndexBus == 0U && rxByteBus != 0xFFU) {
            /* belum ketemu sync byte, abaikan byte ini, tetap nunggu 0xFF berikutnya */
        } else {
            frameBufferBus[frameIndexBus++] = rxByteBus;
            if (frameIndexBus >= 7U) {
                if (frameSiapBus == 0U) {
                    memcpy(frameKerjaBus, frameBufferBus, 7U);
                    frameSiapBus = 1U;
                    totalFrameLengkapBus++;
                }
                frameIndexBus = 0U;
            }
        }
        HAL_UART_Receive_IT(&huart1, &rxByteBus, 1U);
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
  /* NOTE: panggilan MX_LPUART1_UART_Init(); HARUS sudah otomatis ada di
   * sini (ditambahin CubeMX di antara init lain di atas) setelah kamu
   * enable LPUART1 & generate code. Kalau belum ada, berarti kamu belum
   * generate ulang dari CubeMX - balik dulu ke CubeMX sebelum lanjut. */
  /* USER CODE BEGIN 2 */
  DebugPrint("\r\n\r\n=== BRIDGE LRF STM32 - BOOT ===\r\n");
  DebugPrint("Alamat bridge di bus = 0x%02X, baudrate USART1/USART2 = 9600\r\n", ALAMAT_BRIDGE_LRF);

  /* Mulai dengerin bus bersama (USART1) via interrupt, 1 byte per callback */
  HAL_UART_Receive_IT(&huart1, &rxByteBus, 1U);
  DebugPrint("USART1 (bus) siap dengerin interrupt.\r\n");

  /* USART2 (ke LRF) SENGAJA gak start receive-IT di sini - LRF_BacaJarak()
   * dan LRF_Pointer() pakai HAL_UART_Receive() blocking dengan timeout,
   * karena pola komunikasinya request-lalu-tunggu-respons (bukan streaming
   * bebas kayak bus bersama), jadi blocking read di sini aman & lebih
   * simpel daripada state machine interrupt kedua. */

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
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

    /* Heartbeat status tiap 1 detik - PALING PENTING buat diagnosa awal:
     * kalau "byte" gak pernah nambah sama sekali, artinya USART1 gak
     * nerima APA-APA dari bus (cek wiring PB6/PB7 & GND & baudrate).
     * Kalau "byte" nambah tapi "frame" gak pernah nambah, artinya ada
     * data masuk tapi gak pernah sinkron ke sync byte 0xFF dengan benar
     * (cek TX/RX kesilang atau kebalik, atau noise). */
    if (HAL_GetTick() - waktuDebugTerakhir >= DEBUG_STATUS_INTERVAL_MS) {
        waktuDebugTerakhir = HAL_GetTick();
        DebugPrint("[STATUS] total byte masuk bus=%lu, total frame lengkap=%lu\r\n",
                   totalByteMasukBus, totalFrameLengkapBus);
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
  * @brief USART1 Initialization Function (ke modul RS485-to-TTL, bus bersama)
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{
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
}

/**
  * @brief USART2 Initialization Function (langsung ke LRF127)
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{
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
}

/* NOTE: MX_LPUART1_UART_Init() SENGAJA GAK saya tulis di sini - biarkan
 * versi yang di-generate CubeMX yang dipakai (dia yang tau kalkulasi
 * clock/prescaler LPUART1 yang benar). Kalau kamu copy-paste file ini,
 * JANGAN timpa fungsi MX_LPUART1_UART_Init() versi CubeMX kamu dengan
 * ketiadaan fungsi ini - biarkan tetap ada punya CubeMX. */

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

  /*Configure GPIO pins : PB3 PB4 (USART2 - ke LRF) */
  GPIO_InitStruct.Pin = GPIO_PIN_3|GPIO_PIN_4;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  GPIO_InitStruct.Alternate = GPIO_AF7_USART2;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pins : PB6 PB7 (USART1 - ke modul RS485-to-TTL) */
  GPIO_InitStruct.Pin = GPIO_PIN_6|GPIO_PIN_7;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  GPIO_InitStruct.Alternate = GPIO_AF7_USART1;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* PA2/PA3 (LPUART1 - debug) dikonfigurasi otomatis oleh
   * MX_LPUART1_UART_Init() versi CubeMX kamu - gak perlu ditambah manual
   * di sini. */

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
