# Brief: Firmware Arduino Mega Pro - Panel GCS (UGV Lidikzi v2)

Dokumen ini rangkuman protokol Arduino Mega Pro (baca panel fisik GCS) ke
aplikasi NUC (Windows 11, PySide6, lihat `gcs_app/`) lewat USB serial. Ini
BUKAN protokol RF (itu beda lapisan, lihat `dokumentasi/ROS2_BRIEF.md`
section 3.5) - Arduino ini cuma "penerjemah" panel fisik → serial USB,
aplikasi NUC yang gabungin data ini + widget touchscreen jadi 1 frame RF
ke Jetson.

**STATUS per 2026-07-16: panel fisik + Arduino SUDAH SELESAI DIRAKIT oleh
user, protokol di bawah FINAL (bukan usulan lagi). Parsing di sisi NUC
(`gcs_app/serial_workers.py`) sudah diupdate match dokumen ini.**

## 1. Kenapa Arduino yang urus kalibrasi & noise-filtering joystick, bukan NUC

Arduino Mega Pro yang LANGSUNG terwiring ke potensiometer joystick fisik,
jadi kalibrasi (titik tengah, dead-zone, mapping ADC mentah ke rentang
target) DAN noise-filtering HARUS jadi tanggung jawab Arduino - konsisten
sama prinsip yang sudah dipakai di desain protokol STM32
(`dokumentasi/STM32_BRIEF.md` & `ROS2_BRIEF.md` 3.4): kalibrasi
hardware-specific dipegang SATU tempat yang paling dekat sama
hardware-nya, supaya konsumen di lapisan atas (NUC app, nanti Jetson)
gak perlu tau detail ADC mentah/quirks fisik joystick tertentu.

**Catatan dari user (2026-07-16)**: joystick fisik yang dipakai ternyata
(1) noisy dan (2) rentang mentahnya cuma ~100-900 (bukan 0-1000/1023
penuh, karena potensiometer gak mentok secara mekanis). Fix yang
disarankan (dilakukan di Arduino, BUKAN di-forward mentah ke NUC):
- **Range**: `map(nilaiMentah, MIN_TERUKUR, MAX_TERUKUR, 0, 1000)` +
  `constrain()` - `MIN_TERUKUR`/`MAX_TERUKUR` harus diukur manual per unit
  joystick (gerakin ke ekstrem, catat `analogRead()`-nya).
- **Noise**: moving average (rata-ratakan beberapa sampel `analogRead()`
  berturut-turut) sebelum di-map.
- **Dead-zone** di titik tengah supaya joystick yang dilepas ngasih nilai
  tengah (500) PERSIS, bukan nilai goyang kecil di sekitar situ.

## 2. Protokol Arduino → NUC (FINAL, 12 field)

ASCII, dipisah spasi, `\n`-terminated:

```
"<X> <Y> <lrf> <zoomin> <zoomout> <bodyup> <bodydown> <lampu> <cam_atas> <cam_kanan> <cam_bawah> <cam_kiri>\n"
```

| # | Field | Range | Arti |
|---|---|---|---|
| 1 | `X` | 0..1000 (SUDAH dikalibrasi+difilter noise di Arduino) | Joystick gerak, sumbu X (steering) |
| 2 | `Y` | 0..1000 | Joystick gerak, sumbu Y (speed) |
| 3 | `lrf` | 0/1 | 1 = tombol LRF lagi ditahan (hold=laser ON, lepas=request jarak) |
| 4 | `zoomin` | 0/1 | 1 = tombol zoom in lagi ditekan |
| 5 | `zoomout` | 0/1 | 1 = tombol zoom out lagi ditekan |
| 6 | `bodyup` | 0/1 | 1 = tombol body up lagi ditekan |
| 7 | `bodydown` | 0/1 | 1 = tombol body down lagi ditekan |
| 8 | `lampu` | 0/1 | state TOGGLE switch lampu (bukan momentary) - nyalain depan+belakang sekaligus |
| 9 | `cam_atas` | 0/1 | pantilt arah atas - tombol digital, BUKAN joystick analog |
| 10 | `cam_kanan` | 0/1 | pantilt arah kanan |
| 11 | `cam_bawah` | 0/1 | pantilt arah bawah |
| 12 | `cam_kiri` | 0/1 | pantilt arah kiri |

**PENTING - koreksi dari draft sebelumnya**: pantilt TERNYATA pakai **4
tombol digital arah** (kayak D-pad), **BUKAN joystick analog kedua**
seperti asumsi draft awal dokumen ini. Cuma ada **1 joystick analog**
(field X/Y di atas, buat gerak/steering).

**Field yang DIHAPUS dari draft sebelumnya**: `power` (switch power GCS
sendiri) - ternyata gak perlu jadi bagian frame data ini, karena kalau
GCS/NUC mati ya gak ada software yang jalan buat baca frame apapun -
power itu urusan hardware murni, bukan data yang perlu dikirim/dibaca.

**Baudrate: 57600** (konsisten sama konvensi lain di project).

Aplikasi NUC (`gcs_app/serial_workers.py`, class `ArduinoReader`) parsing
frame ini, hasilnya dict dengan key: `x`, `y`, `lrf`, `zoomin`, `zoomout`,
`bodyup`, `bodydown`, `lampu`, `cam_atas`, `cam_kanan`, `cam_bawah`,
`cam_kiri`.

### Kenapa ASCII + kirim terus-menerus (heartbeat), bukan event-driven
Sama alasannya kayak protokol STM32 (`STM32_BRIEF.md` bagian 4): gampang
didebug manual, dan kalau 1 baris nyasar/rusak di serial USB, baris
berikutnya otomatis "membetulkan" - gak perlu ack/retry logic rumit.

## 3. Cara NUC terjemahin frame ini jadi frame 10-byte GCS→Jetson

Lihat `gcs_app/main_window.py` fungsi `_bangun_frame_gcs()`:
- `X`/`Y` (0-1000) di-remap ke -100..100 buat field `XJoystick1`/`YJoystick1`.
- `cam_atas/kanan/bawah/kiri` (4 digital) diterjemahin jadi 2 field
  `XJoystick2`/`YJoystick2` versi diskrit (-100/0/100) - TODO: konfirmasi
  konvensi tanda (+/-) ke user, ini masih asumsi (kanan=+X, atas=+Y).
- `zoomin`/`zoomout` digabung jadi 1 field `Zoom` (-1/0/1).
- `lrf` passthrough langsung.
- `lampu` dikombinasikan sama slider brightness (widget NUC) buat
  `FLamp`, dan sama arah gerak (`Y`) buat nentuin `BLamp` kedip/nggak.
- **`Estop` dan `Mode` MASIH placeholder 0** - field ini gak ada
  sumbernya di frame 12-field Arduino, belum dikonfirmasi ke user asalnya
  dari mana (lihat `ROS2_BRIEF.md` section 6).
- **Raise/Lower/Widen/Narrow (`bodyup`/`bodydown` + tombol Widen/Narrow
  touchscreen) BELUM ada field tujuan di frame 10-byte** - gap ini
  masih terbuka, lihat `ROS2_BRIEF.md` section 7.3. Keputusan
  arsitektur (2026-07-16): kalau/ketika field ini ditambahkan, NUC
  HARUS kirim command AGGREGATE (misal 1 field "body_updown" -1/0/1),
  BUKAN nilai per-motor individual - biar logic "grup mana gerak
  bareng" tetap terpusat di `vehicle_control_node` (Jetson), bukan
  tersebar ke NUC juga.

## 4. Yang masih perlu dikonfirmasi

1. **Konvensi tanda pantilt** (`cam_kanan`=+X, `cam_atas`=+Y) - asumsi
   saya, perlu dikonfirmasi ke user.
2. **Rate kirim** - saat ini 20Hz (mengikuti RFLink di `serial_workers.py`),
   belum dites apa cukup responsif buat joystick gerak.
3. **Asal field `Estop` dan `Mode`** di protokol 10-byte - lihat poin di
   atas.
4. **Field tujuan buat Raise/Lower/Widen/Narrow** di frame 10-byte -
   perlu diperluas jadi berapa byte, atau ada rencana lain.

## 5. Referensi terkait

- `dokumentasi/ROS2_BRIEF.md` - brief utama, section 3.5 (protokol RF),
  section 7 (arsitektur app NUC, termasuk gap Raise/Lower/Widen/Narrow)
- `gcs_app/serial_workers.py` - implementasi parsing frame ini (`ArduinoReader`)
- `gcs_app/main_window.py` - implementasi penerjemahan ke frame 10-byte (`_bangun_frame_gcs`)
- `Testcode/test_rf_link.py` - format 13-field SISTEM LAMA ("panel
  koper"), BUKAN protokol yang dipakai sekarang
