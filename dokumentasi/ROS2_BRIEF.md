# Brief: ROS2 di Jetson - UGV Lidikzi v2

Robot darat remote-control (TNI Zeni AD). Operator pakai GCS (aplikasi
touchscreen di NUC, `gcs_app/`) yang kirim command lewat radio RF ke
Jetson Orin Nano. Jetson yang jalanin ROS2, nerjemahin command itu jadi
perintah ke STM32 (motor+lampu, lewat SPI) dan ke bus RS485 (pantilt+
kamera+LRF, lewat modul RS485-to-TTL).

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
| `/gcs/status_balik` | Core Node → GCS Interface | Status buat dikirim balik ke GCS (5-byte reply) |
| `/rs485/command` | Core Node → RS485 Interface | Command pantilt/kamera/LRF yang UDAH diterjemahin |
| `/rs485/status` | RS485 Interface → Core Node | Hasil baca (jarak LRF, dll) |
| `/stm32/command` | Core Node → STM32 Interface | Frame 8-field (speed/steer/fbody/dst) UDAH final |
| `/stm32/status` | STM32 Interface → Core Node | Ack/status dari STM32 (lihat catatan di bawah) |

## Protokol GCS ↔ Jetson (lewat GCS Interface)

Request-response bergantian, ~20Hz, GCS selalu mulai duluan.

**GCS → Jetson, 16 byte:**
```
[Estop][Mode][XJoystick1][YJoystick1][XJoystick2][YJoystick2][Zoom][LRF][FLamp][BLamp][SlipRing][BodyUpDown][ArmWidenNarrow][MotorIndividualID][MotorIndividualArah][Kalibrasi]
```
Semua `uint8`/`int8` (1 byte per field). Struct Python: `"=BBbbbbbBBBBbbBbB"`.
Range tiap field ada di `gcs_app/main_window.py` (`_bangun_frame_gcs`).

**Jetson → GCS, 5 byte (WAJIB dibalas TIAP kali terima 16-byte valid):**
```
[stm32_status][lrf_status][lrf_jarak_LSB][lrf_jarak_MSB][individual_ack]
```
Pakai status YANG SUDAH DI-CACHE (jangan query fresh STM32/LRF secara
blocking pas mau balas - bisa telat sampai 500ms dan macetin siklus RF).

## Protokol Jetson ↔ STM32 (lewat STM32 Interface)

**Jetson → STM32**, ASCII, `\n`-terminated, 20Hz:
```
"<speed> <steer> <fbody> <bbody> <rarm> <larm> <flamp> <blamp>\n"
```
`speed` -100..100 (kontinu), `steer/fbody/bbody/rarm/larm` -1/0/1
(diskrit, tiap field gerakin 1 GRUP motor bareng), `flamp` 0..100,
`blamp` 0/1/2.

Command khusus (dipicu dari `MotorIndividualID`/`Kalibrasi` di frame
GCS): `"I <motor_id 1-12> <arah -1/0/1>\n"` dan `"K\n"`.

**STM32 → Jetson (BARU, harus ditambah - sebelumnya cuma 1 arah)**:
belum ada spesifikasi persis, TAPI harus dibuat supaya `stm32_status`
beneran valid (bukan cuma "port kebuka"). Minimal: STM32 kirim balik 1
baris ack/status tiap kali terima command. **Ini butuh update firmware
STM32 juga, bukan cuma sisi Jetson.**

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
   (STM32/RS485/RF protokol semua udah ada reference implementation-nya
   di Python, di `Testcode/*.py` dan `gcs_app/`) - tinggal bungkus jadi
   Node class, bukan nulis ulang dari nol.
2. **Test tiap node SENDIRI-SENDIRI dulu** sebelum digabung - misal
   STM32 Interface dites pakai `ros2 topic pub` manual ke `/stm32/command`,
   amati serial monitor/motor fisik, BARU sambungin ke Core Node.
3. **Package ROS2**: 1 package (misal `ugv_robot`), 4 node di
   `ugv_robot/ugv_robot/*.py`, daftarin tiap node jadi executable di
   `setup.py` (`entry_points`).

## Referensi kode (baca ini buat detail persis, bukan cuma percaya brief ini)

| File | Isi |
|---|---|
| `gcs_app/serial_workers.py`, `main_window.py` | Protokol RF GCS↔Jetson persis |
| `Testcode/test_ac_motors_stm32.py`, `kodestm32tes.c` | Referensi motor AC (protokol lama, perlu diupdate ke 8-field final) |
| `Testcode/test_bus_pantilt_kamera_lrf.py` | Referensi RS485 pantilt+kamera+LRF, SUDAH TERBUKTI JALAN |
| `Testcode/lrfinterface.c` | Firmware bridge LRF (NUCLEO-G431KB), SUDAH TERBUKTI JALAN |
| `dokumentasi/ARDUINO_GCS_BRIEF.md` | Protokol panel Arduino → GCS (buat konteks asal data GCS) |
