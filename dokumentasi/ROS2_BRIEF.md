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
- Prinsip **"dumb driver, smart brain"**: STM32 gak mikir/mutusin apa-apa,
  cuma APPLY command final yang dikirim Jetson dan RELAY data mentah
  balik. **SATU-SATUNYA tempat ada logic/keputusan ada di Core Node.**

## 2 Node ROS2 - pembagian tugas TEGAS

| Node | Boleh ada logic/keputusan? | Tugas |
|---|---|---|
| **STM32 Interface Node** | **TIDAK** - translator byte↔topic murni | Baca/tulis serial USART3 ke STM32, publish data mentah apa adanya, subscribe command final dari Core Node dan kirim apa adanya |
| **Core Node** | **YA - SATU-SATUNYA tempat logic** | Baca data mentah dari STM32 Interface, OLAH jadi command final, publish ke STM32 Interface |

Kenapa dipisah tegas gini: kalau logic nyebar ke translator juga, gampang
lupa update salah satu pas ada perubahan. Interface Node harus BISA dites
sendirian pakai `ros2 topic pub` manual tanpa perlu Core Node nyala,
justru karena dia gak punya keputusan apapun buat digantungin ke node lain.

---

# BAGIAN 1: STM32 Interface Node

## Tanggung jawab
1. Buka serial ke STM32 (USART3 @ **115200 baud**)
2. **Kirim** (subscribe topic dari Core Node, pack jadi 20 byte, tulis serial) - berkala **~10-20Hz**, Jetson yang inisiatif
3. **Terima** (baca serial, unpack up-frame 18 byte, publish ke beberapa topic) - STM32 balas LANGSUNG tiap kali terima 1 down-frame valid
4. **TIDAK BOLEH** interpretasi/putusin apapun dari isi frame - itu kerjaan Core Node

## Topic yang node ini urus

| Topic | Arah | Isi |
|---|---|---|
| `/stm32/command` | **Subscribe** (dari Core Node) | Semua 20 field down-frame, sudah final, tinggal di-`struct.pack` dan kirim |
| `/stm32/gcs_relay` | **Publish** (ke Core Node) | 14 field relay GCS mentah dari up-frame offset 0-13 |
| `/stm32/lrf_status` | **Publish** (ke Core Node) | Jarak LRF real-time + status baca, dari up-frame offset 14-16 |
| `/stm32/health` | **Publish** (ke Core Node) | `stm32Status`, dari up-frame offset 17 |

## Down-frame yang HARUS dikirim: Jetson → STM32, 20 byte (`"=b8bBBBBbBBBBBB"`)

| Offset | Field | Tipe | Range |
|---|---|---|---|
| 0 | speed | int8 | -100..100 |
| 1-8 | act0..act7 | int8 ×8 | -100..100 |
| 9 | fLamp | uint8 | 0-100 |
| 10 | bLamp | uint8 | 0-100 |
| 11 | bLampMode | uint8 | 0/1/2 |
| 12 | pantiltArah | uint8 | 0-4 |
| 13 | kameraZoom | int8 | -1/0/1 |
| 14 | slipRing | uint8 | 0/1 |
| 15 | lrfTrigger | uint8 | 0-3 |
| 16 | gcsReplyStm32Status | uint8 | 0-255 |
| 17 | gcsReplyLrfStatus | uint8 | 0-255 |
| 18 | gcsReplyLrfLsb | uint8 | 0-255 |
| 19 | gcsReplyLrfMsb | uint8 | 0-255 |

(Arti/efek tiap field ada di BAGIAN 2 - Interface Node gak perlu tau
artinya, cuma perlu tau cara pack-nya benar)

## Up-frame yang HARUS diterima & di-publish: STM32 → Jetson, 18 byte

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
| 14 | lrfJarakLsb | uint8 | `/stm32/lrf_status` |
| 15 | lrfJarakMsb | uint8 | `/stm32/lrf_status` |
| 16 | lrfStatus | uint8 | `/stm32/lrf_status` |
| 17 | stm32Status | uint8 | `/stm32/health` |

## Framing
`HAL_UARTEx_ReceiveToIdle_IT` di sisi STM32 - frame HARUS pas ukurannya
(20 byte down / 18 byte up), kalau kepotong/lebih otomatis dibuang. Gak
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
| `act[motorIndividualId-1]` (override, prioritas di atas logic normal) | `motorIndividualId` + `motorIndividualArah` | **[PASTI]** Kalau `motorIndividualId != 0`: `act[motorIndividualId-1] = motorIndividualArah` (abaikan logic normal actuator itu buat sementara). `motorIndividualId=0` → semua actuator balik ke logic normal |
| `fLamp` | `fLamp` | **[PASTI]** Passthrough langsung, sama-sama 0-100 |
| `bLamp` | `fLamp` (BUKAN `bLamp`!) | **[PASTI]** `bLamp (down) = fLamp (relay)` - COPY nilai fLamp, karena `bLamp` di relay itu MODE bukan brightness (lihat baris di bawah) |
| `bLampMode` | `bLamp` (relay) | **[PASTI]** Passthrough langsung, sama-sama 0/1/2. GCS udah ngitung ini sendiri (`2` kalau `yJoy1<0`/mundur, `1` kalau nyala biasa, `0` kalau mati) |
| `pantiltArah` | `xJoy2` + `yJoy2` | **[PERLU DIPUTUSIN sebagian]** Terjemahin 2 field diskrit (-100/0/100) jadi 1 enum 0-4: `xJoy2>0`→kanan(1), `xJoy2<0`→kiri(0), `yJoy2>0`→atas(2), `yJoy2<0`→bawah(3), semua nol→stop(4). Yang belum diputusin: prioritas kalau xJoy2 DAN yJoy2 sama-sama aktif barengan (device fisik cuma 1 arah per waktu, jadi kemungkinan gak akan kejadian, tapi tetap perlu didefinisiin) |
| `kameraZoom` | `zoom` | **[PASTI]** Passthrough langsung, sama-sama -1/0/1 |
| `slipRing` | `slipRing` | **[PASTI]** Passthrough langsung, sama-sama 0/1 |
| `lrfTrigger` | `lrf` | **[PASTI, simpel]** `lrf==1` → `lrfTrigger=1` (baca jarak), `lrf==0` → `lrfTrigger=0` (idle). Boleh passthrough langsung tiap frame (STM32 gak anti-spam `lrfTrigger`, aman diminta berkali-kali). Pointer LRF (`lrfTrigger=2/3`) belum ada sumber field-nya dari GCS - **[PERLU DIPUTUSIN]** mau dipicu dari mana |
| `gcsReplyStm32Status` | `stm32Status` (dari `/stm32/health`) | **[PASTI]** Passthrough - STM32 sehat, relay balik status kesehatannya sendiri |
| `gcsReplyLrfStatus` | `lrfStatus` (dari `/stm32/lrf_status`) | **[PASTI]** Passthrough - hasil baca LRF terakhir |
| `gcsReplyLrfLsb`/`Msb` | `lrfJarakLsb`/`Msb` (dari `/stm32/lrf_status`) | **[PASTI]** Passthrough - jarak LRF terakhir |

**Catatan soal `kalibrasi`** (relay offset 13): field ini NAIK ke Jetson
(GCS→STM32→relay), tapi **gak ada slot balik** di down-frame - STM32
firmware sekarang juga gak punya logic kalibrasi apapun (gak ada
encoder/posisi tersimpan buat actuator). Jadi field ini **belum
actionable sama sekali** - kemungkinan cuma dipakai bareng
`motorIndividualId`/`motorIndividualArah` buat proses kalibrasi manual
yang dilakuin OPERATOR langsung liat gerakan fisiknya (bukan otomatis).

## 3 aturan penting lain

1. **"Stale-by-1-cycle" buat balasan GCS**: `gcsReply*` yang kamu isi di
   down-frame BARU kepake STM32 buat balas GCS di request BERIKUTNYA
   (bukan instan). Wajar ada delay 1-2 siklus antara "Jetson tau status
   LRF terbaru" dan "GCS lihat status itu di layarnya" - disengaja, STM32
   gak boleh nunggu Jetson mikir pas lagi ngebales GCS.
2. **RS485 (pantilt/kamera/LRF) FULL tanggung jawab STM32** - Core Node
   CUKUP isi `pantiltArah`/`kameraZoom`/`slipRing`/`lrfTrigger`, STM32
   yang urus checksum/protokol RS485-nya. Core Node gak perlu tau detail
   Pelco-D/pantilt custom protocol sama sekali.
3. **STM32 CUMA kirim ke RS485 kalau `pantiltArah`/`kameraZoom`/`slipRing`
   BERUBAH** dari siklus sebelumnya (anti-spam, dicek internal STM32) -
   Core Node BEBAS ngirim nilai yang sama terus-menerus tiap down-frame,
   gak perlu logic "cuma kirim sekali" sendiri. `lrfTrigger` TIDAK
   di-anti-spam (boleh di-request berkali-kali, itu query bukan state).

---

## Konteks: Protokol GCS ↔ STM32 (bukan tanggung jawab ROS2, tapi asal data relay)

STM32 yang pegang langsung link ini (USART2 @ 57600 baud, request-response,
GCS mulai duluan). Dicatat di sini cuma buat konteks dari mana field
`/stm32/gcs_relay` asalnya.

**GCS → STM32, 14 byte** (`"=BbbbbbBBBBbBbB"`): estop, xJoy1, yJoy1, xJoy2,
yJoy2, zoom, lrf, fLamp, bLamp, slipRing, bodyUpDown, motorIndividualId,
motorIndividualArah, kalibrasi — urutan byte SAMA PERSIS kayak offset
`/stm32/gcs_relay` di tabel BAGIAN 1.

(Field `mode` dan `armWidenNarrow` udah DIHAPUS dari protokol ini - `mode`
dari awal gak ada sumbernya/gak kepake, `armWidenNarrow` gak relevan lagi
karena actuator arm/RArm/LArm udah dibatalkan.)

**STM32 → GCS, 4 byte** (`"=BBBB"`): `[stm32_status][lrf_status][lrf_jarak_lsb][lrf_jarak_msb]`
- nilainya dari cache yang DIISI Core Node lewat `gcsReply*` di down-frame.

## Saran buat yang baru mulai ROS2

1. **Bahasa: Python (`rclpy`)**.
2. **STM32 Interface Node dulu yang paling gampang divalidasi** - bisa
   dites standalone pakai `ros2 topic pub` buat kirim command manual ke
   `/stm32/command`, amati balasan di `/stm32/gcs_relay` dkk, BARU
   sambungin ke Core Node.
3. **Cek tabel BAGIAN 2** buat mapping up-frame→down-frame yang udah
   confirmed - semua field logic-nya udah **[PASTI]** sekarang (termasuk
   `speed`, Steer, body), tinggal sisa `lrfTrigger=2/3` (pointer LRF) yang
   belum ada sumber field-nya dari GCS kalau mau dipakai.
4. Buat prototyping/debug cepat sebelum nulis node beneran, pakai
   referensi Python yang UDAH TERBUKTI jalan di `Testcode/` (lihat
   tabel di bawah) - tinggal contek pola `struct.pack`/`struct.unpack`
   dan port ke `rclpy` Node class.
5. **Package ROS2**: 1 package (misal `ugv_robot`), 2 node di
   `ugv_robot/ugv_robot/*.py`, daftarin jadi executable di `setup.py`
   (`entry_points`).

## Referensi kode (baca ini buat detail persis, bukan cuma percaya brief ini)

| File | Isi |
|---|---|
| `STM32Cube/motorugv_G474RE/Core/Src/main.c` | Firmware STM32 SAAT INI (chip G474RE) - semua protokol (GCS/RS485/Jetson) SUDAH TERBUKTI JALAN via test manual |
| `Testcode/test_jetson_stm32_g474.py` | Referensi Python paling relevan buat STM32 Interface Node - format `struct.pack`/`unpack` down-frame & up-frame PERSIS yang harus dipakai `rclpy` node |
| `Testcode/test_jetson_manual_g474.py` | Sama kayak di atas tapi kontrol manual interaktif, enak buat ngerti efek tiap field satu-satu |
| `Testcode/test_gcs_stm32_g474.py` | Referensi format 14-byte GCS request + 4-byte reply |
| `Testcode/test_gcs_manual_g474.py` | Kontrol manual GCS interaktif (`set <field> <value>`), field-nya udah dibatasin sesuai makna asli (bukan cuma batas mentah uint8/int8) |
| `Testcode/test_rs485_stm32_g474.py`, `test_rs485_manual_g474.py` | Referensi protokol RS485 (buat ngerti APA yang STM32 lakuin di baliknya - Core Node gak perlu implementasi ini sendiri) |
| `Testcode/test_jetson_stm32_g474_lama_arm.py` | Versi LAMA (down-frame 24-byte/12-actuator + relay GCS 16-byte/masih ada mode+armWidenNarrow) - CUMA buat kompatibilitas tes node ROS2 yang belum migrasi, TIDAK nyambung ke STM32 asli |
| `gcs_app/serial_workers.py`, `main_window.py` | Sisi GCS (NUC) - konteks asal data yang bakal kamu terima di `/stm32/gcs_relay` |
| `~ROS2/STM32 interface/stm32_interface_node.py`~ | **OUTDATED** - masih pakai I2C dari desain sebelum pivot ke UART, perlu ditulis ulang sesuai protokol di atas |
| `~ROS2/GCS interface/~` | **OBSOLETE TOTAL** - sisa arsitektur 4-node lama (sebelum STM32 jadi hub), GCS Interface Node gak ada lagi di desain sekarang |
