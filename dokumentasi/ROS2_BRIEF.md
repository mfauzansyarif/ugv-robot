# Brief: Pengembangan ROS2 - UGV Lidikzi v2

Dokumen ini rangkuman lengkap buat lanjutin development ROS2 di mesin/sesi
lain (Ubuntu, Claude terpisah dari yang di VSCode Windows ini). Tujuannya
supaya Claude di sisi Ubuntu punya konteks penuh tanpa perlu baca ulang
seluruh histori chat. **Semua path file di bawah relatif ke root repo
`ugv-robot` ini** - kalau repo yang sama di-clone/di-pull di Ubuntu, semua
file ini seharusnya ada.

**PENTING: dokumen ini adalah RINGKASAN. Kalau ada detail byte-level protokol
yang perlu presisi (checksum, urutan field, dll), BACA LANGSUNG file kode
yang direferensikan - jangan percaya rangkuman di sini 100% kalau ada
keraguan, karena rangkuman bisa saja typo/kelewat detail dibanding kode
aslinya.**

## 1. Konteks proyek

UGV "Lidikzi 2" - kendaraan darat tanpa awak buat TNI Zeni AD (Engineering
Corps). User (mahasiswa KP/magang) sedang rebuild total sistem kontrolnya.
Robot ini funsinya: recon/pengintaian medan, dilengkapi pan-tilt kamera +
laser rangefinder (LRF) di atas slip ring yang berputar, serta kemampuan
gerak/steering yang kompleks (bukan diferensial biasa - ada motor linear
buat ubah lebar & tinggi chassis).

## 2. Arsitektur hardware keseluruhan

```
GCS (2 joystick + tombol) --RF--> Jetson Orin Nano --???--> STM32(s) --> aktuator
                                        |
                                        +--RS485 bus bersama--> Pantilt + Kamera + [STM32 Bridge LRF]
```

### 2.1. Aktuator & subsistem fisik
- **4 motor AC servo** (roda utama, gerak maju-mundur) - lewat AC servo
  driver HK Series, kontrol PULS+SIGN (position-control mode disalahgunakan
  jadi continuous-speed control, PULS=frekuensi menentukan kecepatan, SIGN=arah)
- **12 motor linear**: 4 buat belok kanan-kiri, 4 buat melebarkan chassis,
  4 buat naik-turun tinggi chassis
- **Pan-tilt** (4 arah) + **kamera** (zoom, focus HARDWARE-LIMITED ke
  auto-only, gak bisa manual) + **LRF** (laser rangefinder, ukur jarak +
  pointer laser on/off) - ketiganya di atas slip ring yang berputar,
  konek ke sisa sistem lewat **1 bus RS485 bersama**
- **Lampu depan** (PWM brightness, 0-100%) + **lampu belakang** (3-state:
  mati/nyala steady/kedip - indikator mundur)

### 2.2. Kenapa ada STM32 "bridge" khusus buat LRF
LRF (Noptel LRF127) protokol native-nya BUKAN Pelco-D (byte pertama gak
selalu `0xFF` seperti Pelco-D/pantilt), sehingga secara struktural aman
digabung 1 bus RS485 bareng pantilt+kamera (gak akan collision sync byte).//
TAPI mentor project khawatir soal byte mentah respons LRF (yang mengandung
float, bisa aja kebetulan berisi `0xFF` di tengah data) numpang di bus
Pelco-D. Solusinya: **STM32 (NUCLEO-G431KB) jadi bridge** - nempel di bus
RS485 bersama sebagai device address=2, TERIMA command ala-Pelco-D,
translate ke protokol native LRF lewat link TTL terpisah (USART2, TANPA
modul RS485, karena ini point-to-point pendek), lalu BUNGKUS ULANG hasilnya
jadi frame Pelco-D 7-byte sebelum balik ke bus. Byte mentah LRF gak pernah
nyentuh bus bersama. **Ini sudah CONFIRMED WORKING end-to-end** (lihat
bagian 4.3).

## 3. Status tiap subsistem (per hari ini)

### 3.1. Pantilt - SEHAT, protokol reverse-engineered
- Protokol custom (bukan Pelco-D asli walau bentuk frame mirip: 7 byte,
  sync `0xFF`), checksum = jumlah byte KECUALI yang nilainya `0xFF`.
- Address selalu `0x00` (byte kedua frame), device ini VALIDASI address-nya
  (gak akan gerak kalau byte address bukan 0x00) - CONFIRMED aman digabung
  bus bareng device Pelco-D lain.
- Kode: `Testcode/test_bus_pantilt_kamera_lrf.py` (fungsi `pantilt_*`),
  referensi awal `Testcode/test_rs485.py`.

### 3.2. Kamera - SEHAT, Pelco-D, address=1
- Chip kamera aslinya VISCA (Sony FCB-EV7520), TAPI modul joystick+RS485
  yang nempel di kamera nerima **Pelco-D** di sisi RS485 dan translate ke
  VISCA secara internal. CONFIRMED jalan: baudrate 9600, address 1
  (hasil scan manual).
- Focus (near/far) TERBUKTI gak bisa dikontrol manual sama sekali (hardware
  limit modul ini, bukan bug kode) - cuma zoom in/out yang jalan.
- Kode: `Testcode/test_bus_pantilt_kamera_lrf.py` (fungsi `kamera_*`,
  `pelco_checksum`, `pelco_frame`), riwayat scan di
  `Testcode/test_camera_zoom_focus.py`.

### 3.3. LRF via STM32 Bridge - CONFIRMED WORKING (baru selesai hari ini)
- Firmware: `Testcode/lrfinterface.c` (project asli STM32CubeIDE-nya ada
  di komputer user, file ini cuma REFERENSI/COPY manual - user paste
  balik ke sini tiap update). Board: NUCLEO-G431KB.
  - USART1 (PB6=TX, PB7=RX) → modul RS485-to-TTL → bus RS485 bersama.
    Address Pelco-D-style device ini = `0x02`. Baudrate 9600.
  - USART2 (PB3=TX, PB4=RX) → LANGSUNG TTL (tanpa modul RS485) → LRF127.
    Baudrate WAJIB 9600 (LRF harus sudah di-set permanen ke 9600 duluan,
    default pabrik LRF itu 115200).
  - LPUART1 (PA2=TX, PA3=RX) → DEBUG ONLY, lewat ST-LINK Virtual COM Port
    (USB yang sama buat flashing). Baca pakai `Testcode/baca_debug_stm32.py`.
  - Custom command (dibungkus frame Pelco-D 7-byte tapi cmd1/cmd2 BUKAN
    Pelco-D asli, opcode custom): `CMD2_BACA_JARAK=0x01` (request jarak,
    respons data1=LSB/data2=MSB jarak dalam desimeter), `CMD2_POINTER=0x02`
    (nyala/matiin pointer laser, data1=0/1).
  - Kalau bridge gagal baca LRF (timeout dsb), SENGAJA gak kirim respons
    apa-apa ke bus (biar master/Jetson yang timeout & retry sendiri).
  - **PENTING**: Jetson/bus HANYA PERNAH terima respons 7-byte Pelco-D-style
    dari bridge ini (sama kayak pantilt/kamera) - TIDAK PERNAH terima
    22-byte mentah native LRF. Kalau ada dokumen/spec lain yang bilang
    "Jetson terima max 22 byte dari LRF", itu SALAH/OUTDATED (sisa dari
    sebelum bridge ini dibikin) - abaikan, itu bertentangan sama seluruh
    alasan bridge ini dibuat (isolasi byte mentah LRF dari bus bersama).
- Test tool: `Testcode/test_bridge_lrf_stm32.py` (test 2-port, bisa emulasi
  LRF palsu tanpa hardware asli - berguna buat validasi logic doang), dan
  `Testcode/test_bus_pantilt_kamera_lrf.py` (kontrol gabungan pantilt+
  kamera+LRF, menu `3` = LRF lewat bridge).
- **Pelajaran penting dari debugging hari ini**: sempat ketemu BANYAK
  masalah "kadang jalan kadang nggak" yang SEMUANYA ternyata soal
  KONEKSI FISIK LONGGAR (pin PB7 & PB3 di board Nucleo-32 ada 2 opsi
  posisi header dan salah satunya gak beneran connect, plus soal
  stabilitas power supply LRF), BUKAN soal logic/protokol - logic-nya
  sendiri sudah dites berkali-kali dan selalu benar begitu koneksi fisik
  fix. **Kalau nanti integrasi ke Jetson dan ketemu gejala serupa
  ("kadang bisa kadang nggak", partial byte count di log), curigai
  hardware/wiring dulu, BUKAN langsung ubah kode.**

### 3.4. Motor AC + Linear + Lampu - PROTOKOL SUDAH FINAL (2026-07-16), firmware BELUM ditulis ulang
**Ini supersede semua yang ada di `dokumentasi/STM32_BRIEF.md` (dokumen lama,
scope-nya cuma 4 motor AC dengan tag "M") dan `Testcode/kodestm32tes.c` versi
sekarang (masih pakai format lama).** Firmware perlu ditulis ulang buat
match spec final di bawah - JANGAN asumsikan `kodestm32tes.c` sekarang
sudah sesuai.

**Jetson → STM32**, ASCII, 8 field dipisah spasi, `\n`-terminated, TANPA
tag (beda dari versi lama yang pakai tag `"M"`):
```
"<speed> <steer> <fbody> <bbody> <rarm> <larm> <flamp> <blamp>\n"
```
| Field | Range | Arti |
|---|---|---|
| `speed` | -100..100 (signed, kontinu) | 4 motor AC (BLAC/roda utama), + = maju, - = mundur |
| `steer` | -1/0/1 (diskrit) | -1=kiri, 0=stop, 1=kanan (motor linear steering) |
| `fbody` | -1/0/1 (diskrit) | -1=turun, 0=stop, 1=naik (motor linear body depan) |
| `bbody` | -1/0/1 (diskrit) | sama seperti fbody, buat body belakang |
| `rarm` | -1/0/1 (diskrit) | -1=sempit, 0=stop, 1=lebar (motor linear arm kanan) |
| `larm` | -1/0/1 (diskrit) | sama seperti rarm, buat arm kiri |
| `flamp` | 0..100 (unsigned) | brightness lampu depan (PWM) |
| `blamp` | 0/1/2 (unsigned) | 0=mati, 1=nyala steady, 2=kedip (indikator mundur) |

**PENTING**: `speed` itu KONTINU (-100..100, representasi persen kecepatan),
tapi `steer/fbody/bbody/rarm/larm` itu CUMA 3 nilai diskrit (-1/0/1, kayak
tombol jog - bukan proporsional kayak speed). Jangan disamakan rangenya.

- Baudrate STM32: **57600** (CONFIRMED final oleh user, bukan 115200 dari
  `STM32_BRIEF.md` lama - itu sudah outdated).
- Firmware motor (`kodestm32tes.c`, 4 motor AC PULS+SIGN via
  TIM2/3/4/8+UART3, STM32 Nucleo H743ZI) dan firmware lampu
  (`kodelampu.c`, PWM lampu depan TIM15/PF9 + GPIO lampu belakang PF8)
  **AKAN DIGABUNG jadi 1 firmware** (CONFIRMED oleh user) yang menerima
  frame 8-field di atas dan mengontrol ke-4 hal ini (4 motor AC, 12 motor
  linear via logic dari sinyal steer/fbody/bbody/rarm/larm, PWM lampu
  depan, state lampu belakang) sekaligus.
- 12 motor linear: referensi eksplorasi ada di `Testcode/test_linear_motors.py`,
  tapi logic kontrolnya (dari sinyal -1/0/1 di atas ke gerakan fisik 12
  motor) belum ditulis di firmware manapun - ini bagian yang perlu
  diimplementasi baru.
- Firmware LAMA (`kodestm32tes.c` + `kodelampu.c` versi sekarang) TETAP
  berguna sebagai REFERENSI cara pakai timer PWM/GPIO di board yang sama,
  cuma parsing protokol & penggabungannya yang perlu ditulis ulang.

### 3.5. GCS → Jetson (RF) - protokol biner 10 byte, FINAL
```
[Estop][Mode][XJoystick1][YJoystick1][XJoystick2][YJoystick2][Zoom][LRF][FLamp][BLamp]
```
10 byte biner, dikirim GCS lewat RF ke Jetson. Detail per-field (tipe data
exact tiap byte, encoding Estop/Mode/dll) **belum saya konfirmasi di sesi
ini** - cek langsung ke user atau file eksplorasi RF di bawah kalau perlu
presisi lebih.

### 3.6. RF link GCS↔Jetson (implementasi) - status belum jelas, ada beberapa file eksplorasi
- Ada `Testcode/test_rf_link.py`, `test_rf_tx.py`, `test_rf_rx.py`,
  `test_gcs_forwarder.py` - **saya (Claude sisi Windows) belum sempat
  review detail isinya di sesi ini**, cek langsung filenya buat tau
  status implementasi RF yang sebenarnya (apakah sudah match protokol
  10-byte di 3.5 atau masih versi eksplorasi lama).

### 3.7. Desain kontrol GCS (joystick/tombol) - konsep sudah dibahas, DETAIL EXACT BELUM saya rangkum
Ada diskusi panjang soal skema kontrol GCS: 2 joystick, 2 mode ("Drive"
buat gerak+pantilt, mode kedua buat naik-turun chassis+lebar/sempit arm -
namanya masih dicari, "Drive" dipakai user tapi nama mode 2 masih belum
fix - kemungkinan ini yang jadi field `Mode` di protokol 3.5). Detail
lengkap kemungkinan ada di `dokumentasi/GCS/GCS.drawio` atau gambar-gambar
di folder `dokumentasi/` - **cek langsung isinya**.

## 4. Rencana ROS2

### 4.1. Environment
- **ROS2 Foxy** (CONFIRMED final oleh user, dipilih spesifik biar MATCH
  sama versi ROS2 yang nantinya dipakai di Jetson - bukan Humble).
  Dijalankan lewat Docker di Ubuntu 22.04 (Foxy resminya target Ubuntu
  20.04/Focal, tapi Docker container-nya sendiri isinya Ubuntu 20.04 base
  image biasanya, jadi ini pola yang umum/aman dipakai walau host OS-nya
  22.04).
- Development dilakukan di **laptop dulu** (Windows/WSL atau native Ubuntu
  di laptop - user sebut mau pindah ke Ubuntu 22.04), BARU nanti dites ke
  Jetson kalau sudah stabil.
- Alasan dev di laptop dulu: Jetson pakai Ubuntu 18.04 yang sudah lama,
  VSCode gak bisa diinstall di situ (kemungkinan karena versi glibc/Node.js
  requirement VSCode Remote-SSH server yang gak kompatibel dengan Ubuntu
  18.04 - ini masalah umum, bukan spesifik project ini).

### 4.2. Rencana koneksi fisik Jetson↔hardware (final target, BUKAN buat sekarang)
Jetson Orin Nano 40-pin header:
- **STM32 (motor+lampu)**: lewat **SPI** (SPI0/SPI1 tersedia di header J41)
- **RF (radio GCS)**: lewat **UART1** (pin 8=TX, 10=RX, di header J41 utama)
- **RS485 (pantilt/kamera/LRF-bridge)**: lewat **UART2** (di header
  **J50**, konektor "Automation Header" TERPISAH dari J41 - BUKAN pin
  tambahan di header 40-pin yang sama). **UART2 di J50 itu default-nya
  serial debug console sistem** - sebelum bisa dipakai buat RS485, WAJIB
  disable serial console redirection dulu lewat device tree/boot config
  Jetson (customization yang lumrah/reversible, tapi effeknya kehilangan
  akses debug-via-console ke situ kecuali diaktifkan lagi).
- Sekarang (tahap development) SEMUA masih lewat **USB** dulu (USB-serial
  adapter biasa) - baru migrasi ke SPI/UART1/UART2 pin native kalau logic
  ROS2-nya sudah proven stabil. **Prinsip penting**: semua path/nama port
  di node ROS2 HARUS jadi parameter (launch file/yaml), JANGAN di-hardcode,
  supaya migrasi nanti cuma ganti config bukan ubah kode.

### 4.3. Arsitektur node ROS2 (sudah disepakati konsepnya)
Semua dalam **1 package** ROS2 (misal nama `ugv_robot`). Node-node yang
akan dibuat, prinsip pemisahan "driver" (I/O mentah, gak ada keputusan
logic) vs "brain" (semua logic terpusat):

1. **`stm32_node`** - driver ke STM32 (motor AC + linear + lampu, lewat
   SPI/serial). Terima command target dari topic, translate ke protokol
   serial STM32, kirim. Publish balik status/feedback kalau ada.
2. **`rs485_node`** - driver ke bus RS485 (pantilt+kamera+LRF bridge).
   Terima command (gerak pantilt, zoom kamera, baca jarak LRF dll),
   translate ke protokol masing-masing (custom pantilt / Pelco-D kamera /
   Pelco-D-style bridge LRF), publish balik hasil baca sensor.
3. **`gcs_interface_node`** - terima data mentah dari RF (state joystick,
   tombol, mode switch), publish sebagai topic ROS2. **Node ini TIDAK
   BOLEH ada logic keputusan** - murni translator byte RF → message ROS2.
4. **`vehicle_control_node`** ("otak") - subscribe ke input GCS + feedback
   dari node 1 & 2, SEMUA logic keputusan ada di sini (mode Drive vs mode
   kedua, interlock keselamatan, mapping joystick→target motor, dll),
   publish command yang di-subscribe node 1 & 2.

### 4.4. Target HARI INI (paling prioritas, mulai dari sini)
Buktikan **ROS2 bisa ngobrol sama STM32** dulu - cukup **2 node**. Pakai
protokol FINAL 8-field dari 3.4 (bukan format lama "M ..."), meskipun
firmware STM32-nya sendiri belum tentu sudah ditulis ulang match protokol
itu - kalau firmware belum siap, cukup validasi `stm32_node` mengirim
baris ASCII yang benar formatnya (amati lewat serial monitor/debug), gak
harus nunggu firmware final buat buktikan sisi ROS2-nya jalan:
1. `stm32_node` - driver, subscribe topic command, format jadi baris ASCII
   `"<speed> <steer> <fbody> <bbody> <rarm> <larm> <flamp> <blamp>\n"`
   (lihat tabel range/arti tiap field di 3.4), `ser.write()` ke STM32 @
   57600 baud.
2. `vehicle_control_node` versi MINIMAL - sekadar publish command test
   (misal dari CLI `ros2 topic pub` atau node sederhana yang publish
   angka tetap) buat validasi `stm32_node` benar nerima & forward ke
   STM32 - LOGIC LENGKAPNYA BELUM PERLU sekarang, itu development
   lanjutan setelah komunikasi dasar proven.

Cara validasi paling sederhana: `stm32_node` subscribe 1 topic custom
(misal `/cmd_vehicle`, bikin message custom 8-field atau mulai simpel pakai
`std_msgs/Float32MultiArray`/`Int32MultiArray` 8 elemen), tiap terima
message langsung format+kirim baris ASCII di atas. Test dari terminal:
`ros2 topic pub /cmd_vehicle ...` manual, amati di serial monitor/debug
STM32 baris yang diterima persis sesuai format, atau amati motor fisik
kalau firmware STM32 sudah siap.

## 5. File-file penting buat referensi (baca langsung, jangan cuma percaya rangkuman ini)

| File | Isi |
|---|---|
| `Testcode/kodestm32tes.c` | Firmware STM32 motor AC (4 motor, PULS+SIGN, watchdog) |
| `Testcode/test_ac_motors_stm32.py` | Test tool Python buat firmware di atas |
| `Testcode/kodelampu.c` | Firmware STM32 lampu depan+belakang |
| `Testcode/test_lampu_stm32.py` | Test tool Python buat firmware lampu |
| `Testcode/lrfinterface.c` | Firmware STM32 bridge LRF (NUCLEO-G431KB), CONFIRMED WORKING |
| `Testcode/test_bridge_lrf_stm32.py` | Test tool 2-port buat bridge LRF (bisa emulasi LRF palsu) |
| `Testcode/test_bus_pantilt_kamera_lrf.py` | Test tool gabungan pantilt+kamera+LRF di 1 bus RS485 |
| `Testcode/baca_debug_stm32.py` | Baca log debug STM32 (LPUART1/ST-LINK VCP) |
| `Testcode/test_rf_link.py`, `test_rf_tx.py`, `test_rf_rx.py`, `test_gcs_forwarder.py` | Eksplorasi RF link, belum di-review detail |
| `Testcode/test_linear_motors.py` | Test 12 motor linear, status integrasi ke firmware belum jelas |
| `dokumentasi/STM32_BRIEF.md` | Brief lama motor AC - SEBAGIAN SUDAH OUTDATED (baudrate beda dari test tool aktual) |
| `dokumentasi/GCS/GCS.drawio`, folder `dokumentasi/` lainnya | Kemungkinan berisi detail skema kontrol GCS |
| `Datasheet/LRF127.pdf` | Datasheet resmi LRF Noptel |
| `Datasheet/SP-09732-001_v1.1.pdf` | Datasheet carrier board Jetson Orin Nano Dev Kit (pinout J41/J50) |

## 6. Hal yang masih terbuka / perlu dicek lebih lanjut
Semua pertanyaan besar (versi ROS2, baudrate, gabung firmware, protokol
8-field) SUDAH DIJAWAB user per 2026-07-16 dan sudah tercermin di bagian
3 & 4 di atas. Sisa yang masih perlu dicek/diputuskan:
1. **Detail exact tiap byte protokol GCS→Jetson (10-byte, section 3.5)** -
   tipe data persis (misal Estop 1 byte gimana encoding-nya, XJoystick
   range berapa, dll) belum dikonfirmasi presisi di sesi ini.
2. **Status implementasi RF** (`test_rf_link.py` dkk, section 3.6) - apa
   sudah sesuai protokol 10-byte final atau masih versi eksplorasi lama.
3. **Nama mode kedua GCS** (section 3.7) - "Drive" sudah fix buat mode 1,
   mode 2 (naik-turun chassis + lebar/sempit arm) namanya masih dicari.
4. **Logic detail 12 motor linear** di firmware gabungan (section 3.4) -
   gimana persis sinyal -1/0/1 diterjemahkan jadi gerakan fisik tiap motor
   (durasi jalan, limit switch kalau ada, dll) - belum dibahas detail.
