# Brief: ROS2 di Jetson - UGV Lidikzi v2

Robot darat remote-control (TNI Zeni AD). Operator pakai GCS (aplikasi
touchscreen di NUC, `gcs_app/`) yang kirim command lewat radio RF ke
**STM32** (bukan langsung ke Jetson - lihat arsitektur di bawah). Jetson
Nano 4GB (chip Tegra210, JetPack 4.x - Ubuntu 18.04/Python 3.6, **BUKAN**
Jetson Orin Nano) yang jalanin ROS2 sebagai "otak" pengambil keputusan.

**PENTING soal ROS2 distro**: karena JetPack 4.x = Ubuntu 18.04, ROS2
Humble (butuh Ubuntu 22.04) **TIDAK BISA** dipakai native. Pakai **ROS2
Foxy** (paling umum buat 18.04, dokumentasi/komunitas paling banyak)
atau Eloquent. Jetson Nano 4GB juga jauh lebih lemah dari Orin Nano
(quad-core Cortex-A57 @ 1.43GHz, bukan 6-core A78AE) - perhatikan beban
CPU kalau nanti nambah image processing di ROS2 node.

Dokumen ini brief SINGKAT buat mulai development - bukan referensi
lengkap byte-per-byte (itu ada di file kode masing-masing, ditunjuk di
bagian akhir). Ditulis buat orang yang baru belajar ROS2 dari nol.

## Arsitektur final: STM32 sebagai HUB, Jetson sebagai OTAK

**Ini beda total dari desain awal** (SPI abis di-drop total gara-gara gak
pernah bisa nyala secara elektrik di Jetson - dicoba osiloskop, gak ada
sinyal sama sekali; I2C juga gagal). Setelah diskusi sama mentor: USB
boleh dipakai "sesekali" (flashing doang), TAPI **RF/RS485/link-ke-Jetson
gak boleh lewat USB Jetson**. Solusinya:

- **STM32 pegang LANGSUNG**: radio RF/GCS (USART2), bus RS485
  pantilt+kamera+LRF-bridge (USART1), DAN semua motor/actuator/lampu.
  STM32 yang jadi "hub" fisik.
- **Jetson cuma punya 1 link**: UART biasa ke STM32 (USART3), **BUKAN
  SPI**. Jetson gak pernah nyentuh RS485 atau radio RF sama sekali -
  itu semua sekarang tanggung jawab firmware STM32
  (`STM32Cube/motorugv_G474RE/Core/Src/main.c`, chip STM32G474RE).
- Prinsip **"dumb driver, smart brain"** tetap sama kayak desain awal:
  STM32 gak mikir/mutusin apa-apa, cuma APPLY command final yang
  dikirim Jetson dan RELAY data mentah balik. **SATU-SATUNYA tempat ada
  logic/keputusan tetap di Core Node (Jetson)**.

## Arsitektur node: cuma 2 (bukan 4 lagi)

Karena STM32 udah nelen RS485 Interface & GCS Interface (mereka sekarang
kerjaan firmware C, bukan ROS2 node lagi), sisa node ROS2 yang beneran
dibutuhin di Jetson tinggal:

| Node | Tanggung jawab | Prinsip |
|---|---|---|
| **Core Node** | Terima relay mentah GCS + status LRF dari STM32 Interface, TERJEMAHIN jadi command final (motor/actuator/lampu/pantilt/zoom/slipring/LRF trigger), tentuin juga apa yang mau dibalikin ke GCS | **SATU-SATUNYA tempat ada logic/keputusan** |
| **STM32 Interface** | Baca/tulis UART ke STM32 (USART3, 115200), publish relay GCS + status LRF + kesehatan STM32, subscribe command final dari Core Node | Cuma translator byte↔topic, GAK ADA logic |

## Topic antar node (saran, bebas disesuaikan)

| Topic | Dari → Ke | Isi |
|---|---|---|
| `/stm32/gcs_relay` | STM32 Interface → Core Node | 16 field mentah dari GCS (byte 0-15 up-frame, APA ADANYA, belum diinterpretasi) |
| `/stm32/lrf_status` | STM32 Interface → Core Node | Jarak LRF real-time + status baca (byte 16-18 up-frame) |
| `/stm32/health` | STM32 Interface → Core Node | `stm32Status` (byte 19 up-frame) |
| `/stm32/command` | Core Node → STM32 Interface | Semua 24 field down-frame, UDAH final |

## Protokol GCS ↔ STM32 (STM32 yang pegang langsung, Jetson TIDAK terlibat)

Ini **bukan** tanggung jawab ROS2 lagi - dicatat di sini cuma buat
konteks, karena field mentahnya di-relay ke Jetson lewat up-frame.

Request-response, GCS mulai duluan, USART2 @ 57600 baud, framing pakai
`HAL_UARTEx_ReceiveToIdle_IT` (resync otomatis tiap ada jeda hening).

**GCS → STM32, 16 byte** (`"=BBbbbbbBBBBbbBbB"`):

| Offset | Field | Tipe |
|---|---|---|
| 0 | estop | uint8 |
| 1 | mode | uint8 |
| 2 | xJoy1 | int8 |
| 3 | yJoy1 | int8 |
| 4 | xJoy2 | int8 |
| 5 | yJoy2 | int8 |
| 6 | zoom | int8 |
| 7 | lrf | uint8 |
| 8 | fLamp | uint8 |
| 9 | bLamp | uint8 |
| 10 | slipRing | uint8 |
| 11 | bodyUpDown | int8 |
| 12 | armWidenNarrow | int8 |
| 13 | motorIndividualId | uint8 |
| 14 | motorIndividualArah | int8 |
| 15 | kalibrasi | uint8 |

**STM32 → GCS, 4 byte** (`"=BBBB"`): `[stm32_status][lrf_status][lrf_jarak_lsb][lrf_jarak_msb]`
— nilainya diambil STM32 dari cache yang DIISI JETSON lewat down-frame
(field `gcsReply*`, lihat di bawah), **bukan** dihitung ulang tiap ada
request GCS masuk.

## Protokol Jetson ↔ STM32 (INI YANG DIPAKE ROS2)

USART3, **115200 baud**, framing `HAL_UARTEx_ReceiveToIdle_IT` di sisi
STM32 (frame HARUS pas ukurannya, kalau kepotong/lebih dibuang). Jetson
kirim berkala (disaranin **~10-20Hz**, dites di 10Hz/100ms pakai
`Testcode/test_jetson_stm32_g474.py` dan jalan lancar), STM32 balas
LANGSUNG tiap terima 1 down-frame valid.

### Down-frame: Jetson → STM32, 20 byte (`"=b8bBBBBbBBBBBB"`)

**Catatan: actuator linear final CUMA 8** (bukan 12) — bagian "arm" (RArm/LArm depan-belakang, dulu index 8-11) DIBATALKAN. Sisa 8 actuator: Steer (4×, index 0-3) + FBody/BBody (4×, index 4-7).

| Offset | Field | Tipe | Range/arti |
|---|---|---|---|
| 0 | speed | int8 | -100..100, motor AC (semua 4 motor sama, +maju/-mundur) |
| 1-8 | act0..act7 | int8 ×8 | -100..100 tiap actuator linear (0=diam, +/-=dorong/tarik), urutan sesuai `actuatorTable` di `main.c` |
| 9 | fLamp | uint8 | 0..100, brightness lampu depan |
| 10 | bLamp | uint8 | 0..100, brightness lampu belakang |
| 11 | bLampMode | uint8 | 0=mati, 1=nyala, 2=kedip |
| 12 | pantiltArah | uint8 | 0=kiri, 1=kanan, 2=atas, 3=bawah, 4=stop |
| 13 | kameraZoom | int8 | -1=out, 0=stop, 1=in |
| 14 | slipRing | uint8 | 0/1 |
| 15 | lrfTrigger | uint8 | 0=idle, 1=baca jarak, 2=pointer on, 3=pointer off |
| 16 | gcsReplyStm32Status | uint8 | Dipakai STM32 buat balas ke GCS - Jetson yang nentuin isinya |
| 17 | gcsReplyLrfStatus | uint8 | idem |
| 18 | gcsReplyLrfLsb | uint8 | idem |
| 19 | gcsReplyLrfMsb | uint8 | idem |

### Up-frame: STM32 → Jetson, 20 byte

| Offset | Field | Tipe | Arti |
|---|---|---|---|
| 0-15 | (16 byte GCS request TERAKHIR) | — | RAW/APA ADANYA, format SAMA PERSIS kayak tabel GCS→STM32 di atas. Core Node yang parse & mutusin, STM32 gak interpretasi apapun |
| 16 | lrfJarakLsb | uint8 | Jarak LRF REAL-TIME (bukan cache), desimeter LSB |
| 17 | lrfJarakMsb | uint8 | desimeter MSB — `jarak_meter = (lsb \| (msb<<8)) / 10.0` |
| 18 | lrfStatus | uint8 | Hasil baca RS485 LRF barusan (1=berhasil, 0=gagal/timeout) |
| 19 | stm32Status | uint8 | STM32 sehat (selalu 1 kalau sempat balas sama sekali) |

### Dua hal penting buat Core Node

1. **"Stale-by-1-cycle" buat balasan GCS**: field `gcsReply*` yang kamu
   isi di down-frame BARU kepake STM32 buat balas GCS di request
   BERIKUTNYA yang datang (bukan instan). Jadi wajar kalau ada delay
   1-2 siklus antara "Jetson tau status LRF terbaru" dan "GCS lihat
   status itu di layarnya". Ini disengaja (STM32 gak boleh nunggu Jetson
   mikir pas lagi ngebales GCS).
2. **RS485 (pantilt/kamera/LRF) sekarang FULL tanggung jawab STM32** -
   Core Node CUKUP isi `pantiltArah`/`kameraZoom`/`slipRing`/`lrfTrigger`
   di down-frame, STM32 yang urus checksum/protokol RS485-nya. Core Node
   **gak perlu tau** detail Pelco-D/pantilt custom protocol sama sekali
   (beda dari desain lama yang taruh itu di RS485 Interface node
   terpisah - sekarang node itu gak ada lagi).

## Saran buat yang baru mulai ROS2

1. **Bahasa: Python (`rclpy`)**.
2. **STM32 Interface Node dulu yang paling gampang divalidasi** - bisa
   dites standalone pakai `ros2 topic pub` buat kirim command manual ke
   `/stm32/command`, amati balasan di `/stm32/gcs_relay` dkk, BARU
   sambungin ke Core Node.
3. Buat prototyping/debug cepat sebelum nulis node beneran, pakai
   referensi Python yang UDAH TERBUKTI jalan di `Testcode/` (lihat
   tabel di bawah) - tinggal contek pola `struct.pack`/`struct.unpack`
   dan port ke `rclpy` Node class.
4. **Package ROS2**: 1 package (misal `ugv_robot`), 2 node di
   `ugv_robot/ugv_robot/*.py`, daftarin jadi executable di `setup.py`
   (`entry_points`).

## Referensi kode (baca ini buat detail persis, bukan cuma percaya brief ini)

| File | Isi |
|---|---|
| `STM32Cube/motorugv_G474RE/Core/Src/main.c` | Firmware STM32 SAAT INI (chip G474RE) - semua protokol (GCS/RS485/Jetson) SUDAH TERBUKTI JALAN via test manual |
| `Testcode/test_jetson_stm32_g474.py` | Referensi Python paling relevan buat ROS2 - format `struct.pack`/`unpack` down-frame & up-frame PERSIS yang harus dipakai `rclpy` node |
| `Testcode/test_jetson_manual_g474.py` | Sama kayak di atas tapi kontrol manual interaktif, enak buat ngerti efek tiap field satu-satu |
| `Testcode/test_gcs_stm32_g474.py` | Referensi format 16-byte GCS request + 4-byte reply |
| `Testcode/test_rs485_stm32_g474.py` | Referensi protokol RS485 (buat ngerti APA yang STM32 lakuin di baliknya - Core Node gak perlu implementasi ini sendiri) |
| `gcs_app/serial_workers.py`, `main_window.py` | Sisi GCS (NUC) - konteks asal data yang bakal kamu terima di `/stm32/gcs_relay` |
| `~ROS2/STM32 interface/stm32_interface_node.py`~ | **OUTDATED** - masih pakai I2C dari desain sebelum pivot ke UART, perlu ditulis ulang sesuai protokol di atas |
