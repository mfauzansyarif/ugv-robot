# Brief: Firmware STM32 - Kontrol 4 Motor AC Servo (UGV Lidikzi v2)

Dokumen ini rangkuman kebutuhan buat nulis firmware STM32 (STM32CubeIDE, HAL)
yang mengontrol 4 motor AC servo (roda utama UGV) lewat AC servo driver HK
Series. Sudah dites dulu manual/hardware-nya (bukan asumsi) - lihat bagian
referensi di bawah.

## 1. Konteks & scope

- Board: STM32 Nucleo H743ZI, project dibuat di STM32CubeIDE (bukan Mbed lagi
  seperti firmware v1 lama).
- Yang dikontrol firmware ini: **4 motor AC servo** (roda utama, penggerak
  maju-mundur UGV) lewat 4 unit AC servo driver **HK Series** (1 driver per
  motor).
- **DI LUAR SCOPE firmware ini (jangan diimplementasi dulu)**: 12 motor
  linear (steering + elevasi), pan-tilt/LRF RS485, IMU. Itu subsistem
  terpisah yang belum masuk tahap ini. Protokol serial di bawah sengaja
  didesain supaya nambah itu nanti gak perlu redesign frame yang sudah ada
  (lihat bagian 3).

## 2. Cara kerja motor (sudah settled, jangan didesain ulang)

Motor AC + driver HK Series dikontrol lewat **position control mode**
(bukan speed control analog) dengan sinyal **Pulse + Sign**:

- **PULS**: pulsa kotak, frekuensinya menentukan kecepatan putar motor.
  Dipakai secara "disalahgunakan" sebagai kontrol kecepatan kontinu (motor
  terus berputar selama pulsa terus dikirim) - BUKAN untuk gerak ke 1 titik
  lalu berhenti seperti pemakaian position-control pada umumnya.
- **SIGN**: level digital HIGH/LOW, menentukan arah putar (CW/CCW).
- **SON**: di-force ON secara PERMANEN lewat parameter driver `PA53=0001`
  (servo enable internal, sudah gak perlu wiring/kontrol dari STM32 sama
  sekali).
- **CLE**: sengaja tidak dipakai/wiring dari STM32. Kalau nanti muncul alarm
  Err-4 (position error/deviation counter kebesaran), solusinya power-cycle
  driver (bukan tanggung jawab firmware ini).

Parameter driver yang WAJIB sudah di-set lewat panel keypad driver (bukan
oleh firmware STM32):
| Parameter | Nilai | Keterangan |
|---|---|---|
| PA4 | 0 | Position control mode |
| PA14 | 0 | Pulse+sign mode |
| PA20 | 1 | FSTP/RSTP diabaikan (gak perlu wiring) |
| PA53 | 0001 | SON force ON internal |

Setiap motor butuh 2 sinyal output dari STM32: 1x PULS (perlu hardware
timer, frekuensi variabel) + 1x SIGN (GPIO digital biasa). Total: **4x PULS
+ 4x SIGN** = 8 pin output dari STM32. Karena PULS harus presisi & gak boleh
nge-block CPU, WAJIB pakai hardware timer STM32 (H743ZI banyak timer,
alokasikan 1 channel PWM per motor - bukan bit-banging/delay-based).

Belum ada alokasi pin pasti - itu keputusan yang boleh diambil bebas saat
implementasi (asal pilih timer channel yang mendukung PWM frekuensi
variabel, dan sisakan 1 UART buat komunikasi serial di bagian 3).

## 3. Protokol serial (STM32 menerima dari GCS/Jetson - sisi ini yang perlu diimplementasi)

Sudah ada test tool Python yang JADI REFERENSI RESMI protokolnya:
`Testcode/test_ac_motors_stm32.py` di repo. Firmware harus kompatibel
langsung dengan tool itu (bisa dites end-to-end begitu firmware siap).

**Format**: ASCII, 1 baris per update, dipisah spasi, diakhiri `\n`:

```
M <speed1> <speed2> <speed3> <speed4>\n
```

- `M` = tag jenis frame ("Motor AC"). Nanti kalau ada frame jenis lain
  (misal `L ...` buat 12 motor linear), firmware cukup cek token pertama
  buat nentuin cara parsing - gak perlu redesign frame `M` yang sudah ada.
- `speed1..speed4` = integer **-100 sampai 100**, representasi ABSTRAK
  "persen dari kecepatan maksimal" DALAM KONVENSI WHEEL-SPACE:
  - Positif = motor itu bikin robot maju
  - Negatif = motor itu bikin robot mundur
  - 0 = motor itu berhenti
  - **PENTING**: nilai ini BUKAN frekuensi mentah, dan BUKAN sign pin
    mentah. Firmware yang wajib translate ke 2 hal:
    1. **Frekuensi PULS** aktual (mapping linear dari 0-100% ke rentang
       frekuensi aman min-max, konstanta ditentukan firmware sendiri
       berdasarkan RPM maksimal motor yang diinginkan)
    2. **Level SIGN aktual**, dengan mengalikan tanda nilai wheel-space
       dengan konstanta arah fisik per motor (karena 2 motor kiri-kanan
       terpasang berhadapan, motor kiri CW = maju tapi motor kanan
       CCW = maju). Contoh konsep (nilai `ARAH_FISIK_MOTOR` sesuaikan
       hasil tes fisik nanti):
       ```c
       const int8_t ARAH_FISIK_MOTOR[4] = {1, -1, 1, -1};
       int8_t arah_pulsa = (nilai_wheel_space >= 0 ? 1 : -1) * ARAH_FISIK_MOTOR[indeks];
       ```
  - Alasan desain "kirim persen abstrak, bukan frekuensi/sign mentah
    langsung dari GCS/Jetson": kalibrasi fisik (gear ratio, RPM maks,
    orientasi mounting motor) itu detail hardware yang harus dipegang
    firmware sebagai satu-satunya sumber kebenaran, supaya kalau nanti
    ada perubahan hardware, gak perlu update logic di banyak tempat
    (Python test tool, nanti Jetson/ROS2, nanti GCS app).

**Baudrate**: 115200 (default test tool, bisa disesuaikan asal 2 sisi sama).

**Frame dikirim TERUS-MENERUS oleh pengirim** (~20Hz / tiap 50ms), bukan
cuma sekali tiap ganti perintah - anggap ini "heartbeat".

## 4. Requirement keamanan/robustness firmware (WAJIB, ini bukan opsional)

Berdasarkan bug yang pernah ditemukan di firmware v1 lama (`main_code_ros.cpp`
- crash `atof(NULL)` karena parsing string gak divalidasi), firmware baru
ini HARUS:

1. **Watchdog serial**: kalau tidak ada baris valid yang diterima dalam
   ~300ms, WAJIB langsung stop ke-4 motor (hentikan semua PULS, apapun
   SIGN-nya) sampai ada baris valid baru masuk.
2. **Validasi parsing ketat sebelum dipakai**:
   - Setelah `strtok()`/`sscanf()`, cek dulu hasil token BUKAN NULL sebelum
     dipanggil `atoi()`.
   - Jumlah token harus PAS 5 (`"M"` + 4 angka). Kalau kurang/lebih, baris
     itu **diabaikan total** (gak diproses sebagian, gak pakai default 0
     diam-diam) - biarkan watchdog di poin 1 yang menangani kalau baris
     rusak terus-terusan.
   - Token pertama harus persis `"M"` sebelum lanjut parsing 4 angka
     berikutnya.
3. **Clamp nilai speed** ke rentang -100..100 di sisi firmware juga (jangan
   cuma percaya pengirim sudah clamp) - defense in depth.
4. **State awal saat boot/reset**: semua motor HARUS dalam keadaan stop
   (PULS tidak jalan) sampai baris valid pertama diterima. Jangan ada
   auto-run/default speed non-zero saat firmware baru nyala.

## 5. Yang HARUS dicoba/divalidasi sebelum dianggap selesai

- Test end-to-end pakai `Testcode/test_ac_motors_stm32.py` langsung dari
  laptop - semua command di menu tool itu (`maju`, `mundur`, `motor <n>
  ...`, `stop`) harus menghasilkan gerakan motor fisik yang sesuai.
- Cabut kabel USB-serial di tengah motor jalan - pastikan motor berhenti
  sendiri dalam ~300ms (validasi watchdog beneran jalan, bukan cuma ada di
  kode).
- Kirim baris sengaja rusak (misal cuma `"M 50\n"`, kurang dari 5 token)
  lewat serial terminal manual - pastikan firmware TIDAK crash/hang, motor
  tetap di state terakhir yang valid sampai watchdog timeout kalau baris
  rusak terus.

## 6. Referensi terkait di repo ini

- `Testcode/test_ac_motors_stm32.py` - test tool Python, protokol resmi
- `Testcode/test_position_control_arduino/test_position_control_arduino.ino`
  - contoh generate PULS+SIGN pakai `tone()` di Arduino (Mega), logic
  konsepnya sama, cuma beda platform (di STM32 pakai timer PWM HAL,
  bukan `tone()`)
- `reference/AC SERVO DRIVER MANUAL.pdf` - manual driver HK Series
  (parameter PA4/PA14/PA20/PA53, spesifikasi timing PULS/SIGN di section
  3.5.3, max frekuensi 500kHz differential/lebih rendah single-ended)
