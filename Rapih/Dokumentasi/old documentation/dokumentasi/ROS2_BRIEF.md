# Brief: ROS2 di Jetson - UGV Lidikzi v2

Robot darat remote-control (TNI Zeni AD). Operator pakai GCS (aplikasi
touchscreen di NUC, `Rapih/Code/Asus NUC/`) yang kirim command lewat radio RF ke
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
  (`Rapih/Code/NucleoG474RE/Core/Src/main.c`, chip STM32G474RE).
- Prinsip **"dumb driver, smart brain"**: STM32 gak mikir/mutusin apa-apa,
  cuma APPLY command final yang dikirim Jetson dan RELAY data mentah
  balik. **SATU-SATUNYA tempat ada logic/keputusan ada di Core Node.**

## 3 Node ROS2 - pembagian tugas TEGAS

| Node | Boleh ada logic/keputusan? | Tugas |
|---|---|---|
| **STM32 Interface Node** | **TIDAK** - translator byte↔topic murni | Baca/tulis serial USART3 ke STM32, publish data mentah apa adanya, subscribe command final dari Core Node dan kirim apa adanya |
| **CV Node** | **TIDAK** - persepsi mentah murni | Baca kamera RTSP, jalanin deteksi YOLO (TensorRT), publish HASIL deteksi (posisi+ukuran box "person" paling confident) - GAK mutusin follow/lock/gerak, itu tetap kerjaan Core Node |
| **Core Node** | **YA - SATU-SATUNYA tempat logic** | Baca data mentah dari STM32 Interface + CV Node, OLAH jadi command final, publish ke STM32 Interface |

Kenapa dipisah tegas gini: kalau logic nyebar ke translator/persepsi juga,
gampang lupa update salah satu pas ada perubahan. STM32 Interface Node
DAN CV Node harus BISA dites sendirian (`ros2 topic pub` manual / `ros2
topic echo`) tanpa perlu Core Node nyala, justru karena keduanya gak
punya keputusan apapun buat digantungin ke node lain.

---

# BAGIAN 1: STM32 Interface Node

## Tanggung jawab
1. Buka serial ke STM32 (USART3 @ **115200 baud**)
2. **Kirim** (subscribe topic dari Core Node, pack jadi 26 byte data + 1 byte
   checksum XOR = 27 byte, tulis serial) - berkala **~10-20Hz**, Jetson yang
   inisiatif
3. **Terima** (baca serial, unpack up-frame 19 byte data + 1 byte checksum =
   20 byte, validasi checksum, publish ke beberapa topic) - STM32 balas
   LANGSUNG tiap kali terima 1 down-frame valid & checksum-nya benar
4. **TIDAK BOLEH** interpretasi/putusin apapun dari isi frame - itu kerjaan Core Node

## Topic yang node ini urus

| Topic | Arah | Isi |
|---|---|---|
| `/stm32/command` | **Subscribe** (dari Core Node) | Semua 26 field down-frame, sudah final, tinggal di-`struct.pack` (checksum XOR-nya ditempel otomatis oleh Interface Node, bukan tanggung jawab Core Node) |
| `/stm32/gcs_relay` | **Publish** (ke Core Node) | 15 field relay GCS mentah dari up-frame offset 0-14 |
| `/stm32/lrf_status` | **Publish** (ke Core Node) | Jarak LRF real-time + status baca, dari up-frame offset 15-17 |
| `/stm32/health` | **Publish** (ke Core Node) | `stm32Status`, dari up-frame offset 18 |

## Down-frame yang HARUS dikirim: Jetson → STM32, 26 byte data (`"=b8bBBBbbbBBBBBBBbbBB"`) + 1 byte checksum = 27 byte total

| Offset | Field | Tipe | Range |
|---|---|---|---|
| 0 | speed | int8 | -100..100 |
| 1-8 | act0..act7 | int8 ×8 | -100..100 |
| 9 | fLamp | uint8 | 0-100 |
| 10 | bLamp | uint8 | 0-100 |
| 11 | bLampMode | uint8 | 0/1/2 |
| 12 | pantiltHorizontal | int8 | -1/0/1 |
| 13 | pantiltVertical | int8 | -1/0/1 |
| 14 | kameraZoom | int8 | -1/0/1 |
| 15 | slipRing | uint8 | 0/1 |
| 16 | lrfTrigger | uint8 | 0-3 |
| 17 | gcsReplyStm32Status | uint8 | 0-255 |
| 18 | gcsReplyLrfStatus | uint8 | 0-255 |
| 19 | gcsReplyLrfLsb | uint8 | 0-255 |
| 20 | gcsReplyLrfMsb | uint8 | 0-255 |
| 21 | gcsReplyBoxTerdeteksi | uint8 | 0/1 |
| 22 | gcsReplyBoxPusatX | int8 | -100..100 |
| 23 | gcsReplyBoxPusatY | int8 | -100..100 |
| 24 | gcsReplyBoxLebar | uint8 | 0-100 |
| 25 | gcsReplyBoxTinggi | uint8 | 0-100 |
| 26 | checksum | uint8 | XOR byte 0-25 (`_checksum_xor()` di Interface Node / `JetsonChecksum()` di firmware) |

**`gcsReplyBox*` (offset 21-25)** numpang mekanisme yang SAMA persis kayak
`gcsReplyLrf*` - Core Node isi dari hasil CV Node (`/vision/deteksi`),
STM32 cache & tempel ke reply GCS (lihat bagian "STM32 → GCS" di bawah),
biar box deteksi bisa di-overlay di video GCS. Cuma buat DITAMPILIN,
BELUM dipakai buat keputusan gerak apapun (lihat catatan `mode` di bawah).

**`pantiltHorizontal`/`pantiltVertical` BISA aktif bareng buat gerak
diagonal** (misal horizontal=1 + vertical=1 = gerak kanan-atas sekaligus) -
STM32 nge-OR bitmask keduanya ke 1 command RS485. Beda dari sebelumnya
(`pantiltArah` 1 field enum 0-4, cuma bisa 1 arah).

(Arti/efek tiap field ada di BAGIAN 2 - Interface Node gak perlu tau
artinya, cuma perlu tau cara pack-nya benar)

## Up-frame yang HARUS diterima & di-publish: STM32 → Jetson, 19 byte data + 1 byte checksum = 20 byte total

| Offset | Field | Tipe | Publish ke topic |
|---|---|---|---|
| 0 | estop | uint8 | `/stm32/gcs_relay` |
| 1 | xJoy1 | int8 | `/stm32/gcs_relay` |
| 2 | yJoy1 | int8 | `/stm32/gcs_relay` |
| 3 | xJoy2 | int8 | `/stm32/gcs_relay` |
| 4 | yJoy2 | int8 | `/stm32/gcs_relay` |
| 5 | zoom | int8 | `/stm32/gcs_relay` |
| 6 | lrf | uint8 | `/stm32/gcs_relay` |
| 7 | fLamp | uint8 | `/stm32/gcs_relay` |
| 8 | bLamp | uint8 | `/stm32/gcs_relay` |
| 9 | slipRing | uint8 | `/stm32/gcs_relay` |
| 10 | bodyUpDown | int8 | `/stm32/gcs_relay` |
| 11 | motorIndividualId | uint8 | `/stm32/gcs_relay` |
| 12 | motorIndividualArah | int8 | `/stm32/gcs_relay` |
| 13 | kalibrasi | uint8 | `/stm32/gcs_relay` |
| 14 | mode | uint8 | `/stm32/gcs_relay` |
| 15 | lrfJarakLsb | uint8 | `/stm32/lrf_status` |
| 16 | lrfJarakMsb | uint8 | `/stm32/lrf_status` |
| 17 | lrfStatus | uint8 | `/stm32/lrf_status` |
| 18 | stm32Status | uint8 | `/stm32/health` |
| 19 | checksum | uint8 | TIDAK dipublish - divalidasi doang (XOR byte 0-18), frame dibuang kalau salah |

**`mode` (offset 14)**: 0=manual, 1=auto. Placeholder protokol - GCS app
BELUM punya tombolnya (selalu kirim 0). CV Node subscribe `/stm32/gcs_relay`
buat baca ini, dipakai buat gerbang: inference YOLO cuma jalan kalau
`mode==1`, biar GPU Jetson gak full-load terus-menerus (risiko thermal
throttle) pas robot lagi dikendalikan manual dan fitur follow gak dipakai.

## Framing
Link Jetson (USART3) di sisi STM32 pakai **hitung-byte-manual**
(`HAL_UART_Receive_IT` per-byte + watchdog resync 30ms kalau ada byte yang
kelamaan gak nyusul), **BUKAN** `HAL_UARTEx_ReceiveToIdle_IT` - link ini
lewat kabel langsung (bukan radio), dan `ReceiveToIdle` ternyata KETERLALU
sensitif ke jeda kecil antar byte (misal dari buffering OS/USB di sisi
Jetson), bisa motong 1 frame utuh jadi 2 potongan yang dua-duanya dibuang
walau data aslinya gak rusak. Beda dari link GCS (USART2, radio RF
beneran) yang masih pakai `ReceiveToIdle` karena genuinely butuh proteksi
dari byte hilang di udara.

Selain itu ukuran frame HARUS pas (27 byte down / 20 byte up) DAN
checksum XOR-nya HARUS cocok (byte terakhir tiap frame) - kalau salah
satu gak sesuai, frame dibuang total (gak diproses, gak dibalas). Gak
perlu sync byte khusus di sisi Python, `pyserial` baca blocking aja cukup
selama ukurannya pas.

---

# BAGIAN 2: Core Node

## Tanggung jawab
**SATU-SATUNYA tempat semua keputusan diambil.** Subscribe data mentah
dari STM32 Interface, OLAH jadi command final, publish balik.

## Topic yang node ini urus

| Topic | Arah |
|---|---|
| `/stm32/gcs_relay` | **Subscribe** (dari Interface Node) |
| `/stm32/lrf_status` | **Subscribe** (dari Interface Node) |
| `/stm32/health` | **Subscribe** (dari Interface Node) |
| `/vision/deteksi` | **Subscribe** (dari CV Node) |
| `/stm32/command` | **Publish** (ke Interface Node) |

## Tabel utama: gimana tiap field up-frame diolah jadi down-frame

Ini inti kerjaan Core Node - per field down-frame, dari mana asalnya dan
cara ngolahnya. Ditandain **[PASTI]** kalau logic-nya udah jelas/simpel,
**[PERLU DIPUTUSIN]** kalau ini masih pertanyaan terbuka yang belum pernah
dibahas/disepakati - JANGAN asal nebak nilainya, konfirmasi dulu.

| Down-frame field | Asal (dari `/stm32/gcs_relay` atau `/stm32/lrf_status`) | Cara olah |
|---|---|---|
| `speed` | `yJoy1` | **[PASTI]** `speed = yJoy1` langsung (sama-sama -100..100), diterapin SAMA ke semua 4 motor AC (gak ada diferensial kiri-kanan - protokol emang cuma punya 1 field `speed` buat semua motor). Belokan murni kerjaan actuator Steer (baris di bawah), bukan beda kecepatan motor - kendaraan ini bukan skid-steer |
| `act0..act3` (Steer) | `xJoy1`, KECUALI `motorIndividualId` override | **[PASTI]** `xJoy1` di-**threshold jadi digital arah** (-1/0/1 - kiri/lurus/kanan, BUKAN dipakai analog penuh). Kalau kanan(+1): `act0`(Depan Kiri)=`-100`(retract), `act1`(Depan Kanan)=`+100`(extend), `act2`(Belakang Kiri)=`-100`(retract), `act3`(Belakang Kanan)=`+100`(extend). Kalau kiri(-1): kebalikan semua tanda. Lurus (dalam threshold): semua `=0` |
| `act4..act7` (FBody/BBody) | `bodyUpDown`, KECUALI `motorIndividualId` override | **[PASTI]** Ke-4 actuator body GERAK BARENG SEMUA (gak beda-beda): `bodyUpDown=1` → `act4=act5=act6=act7=100` (extend semua), `bodyUpDown=-1` → semua `=-100` (retract semua), `bodyUpDown=0` → semua `=0` (diam) |
Override individual (prioritas di atas logic normal) | `motorIndividualId` + `motorIndividualArah` | **[PASTI]** Kalau `motorIndividualId != 0`, abaikan logic normal buat actuator terkait, ganti pakai ini (arti `motorIndividualId` di-REDEFINE dari GCS - lihat `Rapih/Code/Asus NUC/motor_linear_dialog.py`) - 1-8 individual per-actuator, 9-10 steer BERPASANGAN (buat kenyamanan, bukan kalibrasi presisi): <br>**1 = Steering Depan Kiri**: `act0 = motorIndividualArah*100` <br>**2 = Steering Depan Kanan**: `act1 = motorIndividualArah*100` <br>**3 = Steering Belakang Kiri**: `act2 = motorIndividualArah*100` <br>**4 = Steering Belakang Kanan**: `act3 = motorIndividualArah*100` <br>**5 = FBody Kiri**: `act4 = motorIndividualArah*100` <br>**6 = FBody Kanan**: `act5 = motorIndividualArah*100` <br>**7 = BBody Kiri**: `act6 = motorIndividualArah*100` <br>**8 = BBody Kanan**: `act7 = motorIndividualArah*100` <br>**9 = Steer Belakang bersama** (`ID_STEER_BELAKANG_BERSAMA`): `act2 = -motorIndividualArah*100, act3 = motorIndividualArah*100` (sign berlawanan, sama kayak logic normal) <br>**10 = Steer Depan bersama** (`ID_STEER_DEPAN_BERSAMA`): `act0 = -motorIndividualArah*100, act1 = motorIndividualArah*100` <br>`motorIndividualId=0` → semua actuator balik ke logic normal (baris `speed`/Steer/body di atas) |
| `fLamp` | `fLamp` | **[PASTI]** Passthrough langsung, sama-sama 0-100 |
| `bLamp` | `fLamp` (BUKAN `bLamp`!) | **[PASTI]** `bLamp (down) = fLamp (relay)` - COPY nilai fLamp, karena `bLamp` di relay itu MODE bukan brightness (lihat baris di bawah) |
| `bLampMode` | `bLamp` (relay) | **[PASTI]** Passthrough langsung, sama-sama 0/1/2. GCS udah ngitung ini sendiri (`2` kalau `yJoy1<0`/mundur, `1` kalau nyala biasa, `0` kalau mati) |
| `pantiltHorizontal` | `xJoy2` | **[PASTI]** `xJoy2>0`→`1`(kanan), `xJoy2<0`→`-1`(kiri), `xJoy2==0`→`0`(stop). Langsung pakai TANDA `xJoy2` aja (udah -100/0/100 diskrit dari GCS, jadi tanda-nya konsisten) |
| `pantiltVertical` | `yJoy2` | **[PASTI]** `yJoy2>0`→`1`(atas), `yJoy2<0`→`-1`(bawah), `yJoy2==0`→`0`(stop). `pantiltHorizontal` & `pantiltVertical` BISA nonzero bareng (gerak diagonal), gak perlu logic prioritas - dua axis independen |
| `kameraZoom` | `zoom` | **[PASTI]** Passthrough langsung, sama-sama -1/0/1 |
| `slipRing` | `slipRing` | **[PASTI]** Passthrough langsung, sama-sama 0/1 |
| `lrfTrigger` | `lrf` (+ state SEBELUMNYA-nya `lrf`, HARUS diinget Core Node) | **[PASTI]** Perilaku **hold-to-laser, release-to-read**: selama `lrf==1` (tombol DITAHAN) → `lrfTrigger=2` (pointer ON) tiap frame. Pas `lrf` baru aja `1→0` (release, HARUS deteksi edge sendiri di Core Node, bandingin ke nilai `lrf` frame sebelumnya) → `lrfTrigger=1` (baca jarak) SATU frame itu doang. Selain 2 kondisi itu (gak ditahan, bukan momen lepas) → `lrfTrigger=3` (pointer OFF) tiap frame. STM32 udah anti-spam sisi `lrfTrigger=2/3` (pointer), jadi Core Node BEBAS kirim nilai sama terus tanpa mikirin spam RS485 - kecuali `lrfTrigger=1` (baca jarak) yang emang harus PAS 1 frame doang di momen release (STM32 gak nge-dedupe field ini) |
| `gcsReplyStm32Status` | `stm32Status` (dari `/stm32/health`) | **[PASTI]** Passthrough - STM32 sehat, relay balik status kesehatannya sendiri |
| `gcsReplyLrfStatus` | `lrfStatus` (dari `/stm32/lrf_status`) | **[PASTI]** Passthrough - hasil baca LRF terakhir |
| `gcsReplyLrfLsb`/`Msb` | `lrfJarakLsb`/`Msb` (dari `/stm32/lrf_status`) | **[PASTI]** Passthrough - jarak LRF terakhir |
| `gcsReplyBoxTerdeteksi`/`PusatX`/`PusatY`/`Lebar`/`Tinggi` | `PersonDetection` (dari `/vision/deteksi`, topic CV Node) | **[PASTI]** Passthrough - box "person" paling confident, cuma buat DITAMPILIN di GCS (overlay di atas video analog RC832), BELUM dipakai buat keputusan gerak apapun di sini |

**Catatan soal `kalibrasi`** (relay offset 13): SEKARANG SUDAH ACTIONABLE
(beda dari sebelumnya). Kalau `kalibrasi==1`, Core Node override SEMUA
`act[0..7]` ke pola tetap "Fully Extend + Fully Left" (`ACT_KALIBRASI`),
`speed=0`, dan field lain yang gak relevan dinetralin - prioritas di
BAWAH estop, di ATAS override individual/logic normal. Ada safety timeout
(`kalibrasi_maks_durasi_sec`, ROS2 parameter, default 15s) - kalau
`kalibrasi` nyala TERUS lebih lama dari itu, Core Node otomatis
menganggapnya OFF (jatuh ke logic normal) walau GCS masih ngirim `1`,
jaga-jaga toggle GCS lupa dilepas.

**Catatan soal `mode`** (relay offset 14): 0=manual, 1=auto. Cuma dipakai
CV Node buat gerbang inference (lihat BAGIAN 1) - Core Node BELUM punya
logic yang baca field ini (belum ada perilaku "follow" beneran, itu kerja
lanjutan yang belum diimplementasi - lihat TODO di `PersonDetection.msg`
soal posisi box yang relatif ke ARAH KAMERA, bukan ke badan robot, karena
firmware STM32 belum bisa baca sudut pantilt).

## 3 aturan penting lain

1. **"Stale-by-1-cycle" buat balasan GCS**: `gcsReply*` yang kamu isi di
   down-frame BARU kepake STM32 buat balas GCS di request BERIKUTNYA
   (bukan instan). Wajar ada delay 1-2 siklus antara "Jetson tau status
   LRF terbaru" dan "GCS lihat status itu di layarnya" - disengaja, STM32
   gak boleh nunggu Jetson mikir pas lagi ngebales GCS.
2. **RS485 (pantilt/kamera/LRF) FULL tanggung jawab STM32** - Core Node
   CUKUP isi `pantiltHorizontal`/`pantiltVertical`/`kameraZoom`/`slipRing`/
   `lrfTrigger`, STM32 yang urus checksum/protokol RS485-nya. Core Node
   gak perlu tau detail Pelco-D/pantilt custom protocol sama sekali.
3. **STM32 CUMA kirim ke RS485 kalau nilainya BERUBAH** dari siklus
   sebelumnya (anti-spam, dicek internal STM32) - berlaku buat
   `pantiltHorizontal`/`pantiltVertical`/`kameraZoom`/`slipRing`, DAN
   `lrfTrigger` pas nilainya `2`/`3` (pointer on/off, ini state). Core Node
   BEBAS ngirim nilai yang sama terus-menerus tiap down-frame buat
   field-field itu, gak perlu logic "cuma kirim sekali" sendiri.
   **KECUALI `lrfTrigger=1`** (baca jarak) - itu TIDAK di-anti-spam (query,
   bukan state), jadi Core Node HARUS jaga sendiri ini cuma kekirim pas
   momen yang tepat (lihat baris `lrfTrigger` di tabel atas - logic
   hold/release).

---

## Konteks: Protokol GCS ↔ STM32 (bukan tanggung jawab ROS2, tapi asal data relay)

STM32 yang pegang langsung link ini (USART2 @ 57600 baud, request-response,
GCS mulai duluan). Dicatat di sini cuma buat konteks dari mana field
`/stm32/gcs_relay` asalnya.

**GCS → STM32, 15 byte** (`"=BbbbbbBBBBbBbBB"`): estop, xJoy1, yJoy1, xJoy2,
yJoy2, zoom, lrf, fLamp, bLamp, slipRing, bodyUpDown, motorIndividualId,
motorIndividualArah, kalibrasi, mode — urutan byte SAMA PERSIS kayak offset
`/stm32/gcs_relay` di tabel BAGIAN 1.

(Field `armWidenNarrow` udah DIHAPUS dari protokol ini - gak relevan lagi
karena actuator arm/RArm/LArm udah dibatalkan. Field `mode` SEMPAT dihapus
juga karena dulu gak ada sumbernya/gak kepake, tapi DITAMBAH BALIK sekarang
buat toggle manual/auto CV - lihat "Catatan soal `mode`" di BAGIAN 2. GCS
app BELUM punya tombolnya, field ini masih di-hardcode `0` terus.)

**STM32 → GCS, 11 byte**: `[marker=0xA5][stm32_status][lrf_status][lrf_jarak_lsb][lrf_jarak_msb][box_terdeteksi][box_pusat_x][box_pusat_y][box_lebar][box_tinggi][checksum]`
- nilainya dari cache yang DIISI Core Node lewat `gcsReply*` di down-frame.
- marker+checksum (XOR ke-9 byte status) ditambahin karena link GCS↔STM32
  ini lewat RF beneran (bukan kabel langsung) - byte bisa geser/rusak di
  udara, ketauan pas testing gcs_app: byte `stm32_status` sesekali kebaca
  0 padahal Core Node selalu kirim 1, ternyata bukan datanya yang salah
  tapi alignment baca di `gcs_app` yang geser gara-gara gak ada proteksi
  framing sama sekali di channel ini (beda dari 3 channel lain yang pakai
  ReceiveToIdle auto-resync). `gcs_app` sekarang buang balasan yang
  marker/checksum-nya gak cocok, dianggap sama kayak timeout/miss.
- `box_pusat_x`/`box_pusat_y` (-100..100) dan `box_lebar`/`box_tinggi`
  (0-100, persentase frame) dipakai `camera_viewer.py` buat overlay kotak
  hijau di atas video analog RC832 - lihat TODO soal sudut kamera di
  `PersonDetection.msg`.

## Saran buat yang baru mulai ROS2

1. **Bahasa: Python (`rclpy`)**.
2. **STM32 Interface Node dulu yang paling gampang divalidasi** - bisa
   dites standalone pakai `ros2 topic pub` buat kirim command manual ke
   `/stm32/command`, amati balasan di `/stm32/gcs_relay` dkk, BARU
   sambungin ke Core Node.
3. **Cek tabel BAGIAN 2** buat mapping up-frame→down-frame - **SEMUA field
   udah [PASTI]**, gak ada lagi yang perlu diputusin (termasuk `speed`,
   Steer, body, pantilt diagonal, dan LRF hold/release).
4. Buat prototyping/debug cepat sebelum nulis node beneran, pakai
   referensi Python yang UDAH TERBUKTI jalan di `Testcode/` (lihat
   tabel di bawah) - tinggal contek pola `struct.pack`/`struct.unpack`
   dan port ke `rclpy` Node class.
5. **Package ROS2**: 2 package - `ugv_robot_msgs` (message custom,
   `msg/*.msg` + `CMakeLists.txt`) dan `ugv_robot` (3 node Python di
   `ugv_robot/ugv_robot/*.py`, daftarin jadi executable di `setup.py`
   `entry_points`).

## Referensi kode (baca ini buat detail persis, bukan cuma percaya brief ini)

| File | Isi |
|---|---|
| `Rapih/Code/NucleoG474RE/Core/Src/main.c` | Firmware STM32 SAAT INI (chip G474RE) - semua protokol (GCS/RS485/Jetson) SUDAH TERBUKTI JALAN via test manual |
| `Rapih/Code/Asus NUC/serial_workers.py`, `main_window.py` | Sisi GCS (NUC) - konteks asal data yang bakal kamu terima di `/stm32/gcs_relay`, dan cara `box_*`/`mode` dipakai di GCS app |
| `ROS2/stm32_interface_node.py` | **CURRENT** - translator byte↔topic, UART ke STM32 (bukan I2C, itu desain lama yang udah di-drop total) |
| `ROS2/core_node.py` | **CURRENT** - satu-satunya tempat logic/keputusan |
| `ROS2/cv_node.py` | **CURRENT** - CV Node, deteksi YOLO (TensorRT) dari kamera RTSP, publish `/vision/deteksi` |
| `ROS2/*.msg` | Definisi message custom (`StmCommand`, `GcsRelay`, `LrfStatus`, `Health`, `PersonDetection`) |
| `Testcode/test_jetson_manual_g474.py`, `test_gcs_manual_g474.py`, `test_gcs_lengkap_manual_g474.py` | **CURRENT** - format `struct.pack`/`unpack`-nya UDAH MATCH protokol saat ini (termasuk checksum & `motorid` 0-8 individual), aman dicontek langsung |
| `Testcode/test_jetson_stm32_g474.py`, `test_gcs_stm32_g474.py`, `test_rs485_stm32_g474.py`, `test_rs485_manual_g474.py` | Referensi Python format `struct.pack`/`unpack` versi LAMA (sebelum `mode`+box relay+checksum ditambah) - masih valid buat ngerti pola dasarnya, tapi ukuran frame di file-file ini SUDAH GAK MATCH protokol saat ini, jangan asal contek angkanya mentah-mentah |
| `Testcode/test_jetson_stm32_g474_lama_arm.py` | Versi LAMA BANGET (down-frame 24-byte/12-actuator) - CUMA arsip, TIDAK nyambung ke STM32 asli sama sekali |
