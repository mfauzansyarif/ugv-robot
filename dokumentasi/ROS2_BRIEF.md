# Brief: ROS2 di Jetson - UGV Lidikzi v2

Robot darat remote-control (TNI Zeni AD). Operator pakai GCS (aplikasi
touchscreen di NUC, `gcs_app/`) yang kirim command lewat radio RF ke
Jetson Orin Nano. Jetson yang jalanin ROS2, nerjemahin command itu jadi
perintah ke STM32 (motor+lampu+linear, lewat SPI) dan ke bus RS485
(pantilt+kamera+LRF, lewat modul RS485-to-TTL).

Dokumen ini brief SINGKAT buat mulai development - bukan referensi
lengkap byte-per-byte (itu ada di file kode masing-masing, ditunjuk di
bagian akhir). Ditulis buat orang yang baru belajar ROS2 dari nol.

## Arsitektur: 4 node

Semua panah **2 arah** (bidirectional) - tiap interface node kirim
command KE hardware-nya, dan terima status/feedback DARI hardware-nya
balik ke Core Node.

| Node | Tanggung jawab | Prinsip |
|---|---|---|
| **Core Node** | Terima command mentah dari GCS Interface, TERJEMAHIN jadi command spesifik buat STM32 & RS485, terima feedback dari keduanya, kirim balik status ke GCS Interface | **SATU-SATUNYA tempat ada logic/keputusan** |
| **GCS Interface** | Baca/tulis serial ke radio RF, publish command mentah dari GCS, subscribe status dari Core Node buat dikirim balik | Cuma translator byte↔topic, GAK ADA logic |
| **RS485 Interface** | Baca/tulis bus RS485 (pantilt + kamera + LRF bridge, 3 device 1 bus) | Cuma translator byte↔topic, GAK ADA logic |
| **STM32 Interface** | Baca/tulis SPI ke STM32 (motor AC+linear, lampu) | Cuma translator byte↔topic, GAK ADA logic |

**Kenapa dipisah gini**: kalau ada logic (misal "gimana caranya Raise
jadi gerakin 2 motor sekaligus") tersebar di banyak node, gampang lupa
update salah satu pas ada perubahan. Simpen SEMUA keputusan di 1 tempat
(Core Node), node lain tinggal "nurut" command yang udah jadi.

## Topic antar node (saran, bebas disesuaikan)

| Topic | Dari → Ke | Isi |
|---|---|---|
| `/gcs/command_mentah` | GCS Interface → Core Node | Semua field frame 16-byte dari GCS (lihat protokol di bawah) |
| `/gcs/status_balik` | Core Node → GCS Interface | Status buat dikirim balik ke GCS (4-byte reply) |
| `/rs485/command` | Core Node → RS485 Interface | Command pantilt/kamera/LRF yang UDAH diterjemahin |
| `/rs485/status` | RS485 Interface → Core Node | Hasil baca (jarak LRF, dll) |
| `/stm32/command` | Core Node → STM32 Interface | 15 field (speed + 12 motor individual + 2 lampu) UDAH final |
| `/stm32/status` | STM32 Interface → Core Node | Status dari STM32 (lihat catatan SPI di bawah) |

## Protokol GCS ↔ Jetson (lewat GCS Interface)

Request-response bergantian, ~20Hz, GCS selalu mulai duluan.

**GCS → Jetson, 16 byte:**
```
[Estop][Mode][XJoystick1][YJoystick1][XJoystick2][YJoystick2][Zoom][LRF][FLamp][BLamp][SlipRing][BodyUpDown][ArmWidenNarrow][MotorIndividualID][MotorIndividualArah][Kalibrasi]
```
Semua `uint8`/`int8` (1 byte per field). Struct Python: `"=BBbbbbbBBBBbbBbB"`.
Range tiap field ada di `gcs_app/main_window.py` (`_bangun_frame_gcs`).

**Jetson → GCS, 4 byte (WAJIB dibalas TIAP kali terima 16-byte valid):**
```
[stm32_status][lrf_status][lrf_jarak_LSB][lrf_jarak_MSB]
```
- `lrf_jarak` dipecah 2 byte (LSB+MSB, uint16) karena 1 byte max cuma
  255 desimeter (25.5m) - LRF ini jangkauannya sampai ~4500m, jadi butuh
  16-bit (`jarak_desimeter = LSB | (MSB << 8)`, lalu `/10` buat meter).
- **TIDAK ADA field ack terpisah buat command individual/kalibrasi**
  (sempat didesain, lalu DIHAPUS 2026-07-16 - dengan frame yang udah
  disatuin, gak ada momen "sukses/gagal" khusus buat sebagian field,
  semua field diterapkan/diabaikan BARENGAN sebagai 1 frame. `stm32_status`
  yang ada udah cukup buat tau apa command nyampe ke STM32 atau nggak).
- Pakai status YANG SUDAH DI-CACHE (jangan query fresh STM32/LRF secara
  blocking pas mau balas - bisa telat sampai 500ms dan macetin siklus RF).

## Protokol Jetson ↔ STM32 (lewat STM32 Interface)

**Status saat ini (firmware `STM32Cube/motorugv/`, SUDAH JALAN & dicompile)**:
UART (USART3 @ 57600), ASCII `\n`-terminated, **15 field**:
```
"<speed> <act0> <act1> ... <act11> <flamp> <blamp>\n"
```
- `speed`: -100..100 (kontinu) - 4 motor AC
- **12 field individual** (urutan PERSIS sama `actuatorTable`/enum di
  `STM32Cube/motorugv/Core/Src/main.c`: `ACT_STEER_FD..ACT_LARM_BELAKANG`),
  masing-masing **-1/0/1** (extend/stop/retract) - **1 field = 1 motor**,
  bukan grup. Semua logic "mana yang gerak bareng pas operasi normal"
  ada di `vehicle_control_node` (isi field berpasangan dengan nilai
  SAMA); kalibrasi/individual juga lewat field yang sama, gak ada
  command terpisah.
- `flamp`: 0..100, `blamp`: 0/1/2

**RENCANA BERIKUTNYA (belum diimplementasi): pindah ke SPI + tambah
balikan.** Alasan pindah dari UART: rencana awal emang SPI (Jetson pegang
lebih banyak jalur SPI daripada UART di header 40-pin). Desain yang
disepakati (2026-07-16):

**Jetson → STM32 (MOSI), 15 byte biner** (field SAMA PERSIS kayak versi
ASCII di atas, cuma dikodekan biner - gak perlu `\n` lagi karena SPI
transaksi ukuran tetap):
```
[speed(int8)][act0..act11(int8 x12)][flamp(uint8)][blamp(uint8)]
```

**STM32 → Jetson (MISO), 15 byte biner, DIKIRIM BARENGAN** (SPI
full-duplex - byte balasan clock keluar DI SAAT YANG SAMA byte command
clock masuk):
```
[status(uint8)][reserved x14, isi 0 dulu]
```
`status`: minimal 1 bit "frame terakhir valid", sisanya reserved buat
telemetry lain nanti.

**PENTING soal SPI slave**: STM32 (sebagai SLAVE, Jetson pegang clock)
**GAK BISA "mikir dulu baru balas"** di tengah transaksi - byte balasan
harus UDAH SIAP sebelum Jetson mulai clocking. Makanya balasannya
otomatis **status dari SIKLUS SEBELUMNYA** (telat 1 siklus), bukan fresh
dari command yang baru aja diterima di transaksi yang sama.

**Belum ditentukan**: peripheral SPI mana yang dipakai di STM32U575ZI,
konfigurasi CPOL/CPHA (harus SAMA persis sisi Jetson & STM32), dan
implementasi HAL_SPI slave (biasanya `HAL_SPI_TransmitReceive_IT`,
di-arm ulang tiap selesai 1 transaksi, mirip pola `HAL_UART_Receive_IT`
yang udah dipakai di firmware lain project ini).

## Protokol Jetson ↔ RS485 (lewat RS485 Interface)

3 device beda protokol di 1 bus fisik (9600 baud):
- **Pantilt**: custom, `[0xFF][0x00][cmd1][cmd2][data1][data2][checksum]`
- **Kamera**: Pelco-D standar, address=1
- **LRF**: lewat STM32 bridge terpisah (NUCLEO-G431KB), address=2,
  Pelco-D-style tapi cmd2 custom (`0x01`=baca jarak, `0x02`=pointer)

Detail checksum/byte persis: lihat `Testcode/test_bus_pantilt_kamera_lrf.py`
(referensi Python yang SUDAH JALAN, tinggal port logic-nya ke rclpy).

## Saran buat yang baru mulai ROS2

1. **Bahasa: Python (`rclpy`)**, biar konsisten sama seluruh stack
   (RS485/RF protokol semua udah ada reference implementation-nya di
   Python, di `Testcode/*.py` dan `gcs_app/`) - tinggal bungkus jadi
   Node class, bukan nulis ulang dari nol. STM32 Interface (SPI) mungkin
   perlu library SPI Python di Jetson (misal `spidev`) - belum ada
   reference implementation Python-nya, ini bagian yang beneran baru.
2. **Test tiap node SENDIRI-SENDIRI dulu** sebelum digabung - misal
   RS485 Interface dites pakai `ros2 topic pub` manual, amati hasil baca
   sensor, BARU sambungin ke Core Node.
3. **Package ROS2**: 1 package (misal `ugv_robot`), 4 node di
   `ugv_robot/ugv_robot/*.py`, daftarin tiap node jadi executable di
   `setup.py` (`entry_points`).

## Referensi kode (baca ini buat detail persis, bukan cuma percaya brief ini)

| File | Isi |
|---|---|
| `gcs_app/serial_workers.py`, `main_window.py` | Protokol RF GCS↔Jetson persis |
| `STM32Cube/motorugv/Core/Src/main.c` | Firmware STM32 motor+linear+lampu SAAT INI (UART, SUDAH JALAN & dicompile) - `actuatorTable`/enum buat urutan 12 motor |
| `Testcode/test_bus_pantilt_kamera_lrf.py` | Referensi RS485 pantilt+kamera+LRF, SUDAH TERBUKTI JALAN |
| `Testcode/lrfinterface.c` | Firmware bridge LRF (NUCLEO-G431KB), SUDAH TERBUKTI JALAN |
| `dokumentasi/ARDUINO_GCS_BRIEF.md` | Protokol panel Arduino → GCS (buat konteks asal data GCS) |
