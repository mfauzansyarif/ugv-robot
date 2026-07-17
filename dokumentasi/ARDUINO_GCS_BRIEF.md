# Brief: Firmware Arduino Mega Pro - Panel GCS (UGV Lidikzi v2)

Dokumen ini rangkuman kebutuhan buat nulis firmware Arduino Mega Pro yang
baca panel fisik GCS (tombol/joystick) dan kirim ke aplikasi NUC (Windows
11, layar touchscreen) lewat USB serial. Ini BUKAN protokol RF (itu beda
lapisan, lihat `dokumentasi/ROS2_BRIEF.md` section 3.5) - Arduino ini
cuma "penerjemah" panel fisik → serial USB, aplikasi NUC yang nanti
gabungin data ini + widget touchscreen jadi 1 frame RF ke Jetson.

**PENTING**: dokumen ini BELUM diimplementasi sama sekali (baik firmware
Arduino maupun parsing di sisi NUC) - ini masih tahap desain protokol,
per 2026-07-16.

## 1. Kenapa Arduino yang urus kalibrasi joystick, bukan NUC

Arduino Mega Pro yang LANGSUNG terwiring ke potensiometer joystick fisik,
jadi kalibrasi (titik tengah, dead-zone, mapping ADC mentah ke rentang
abstrak) HARUS jadi tanggung jawab Arduino - konsisten sama prinsip yang
sudah dipakai di desain protokol STM32 (`dokumentasi/STM32_BRIEF.md` &
`ROS2_BRIEF.md` 3.4): kalibrasi hardware-specific dipegang SATU tempat
yang paling dekat sama hardware-nya, supaya konsumen di lapisan atas
(NUC app, nanti Jetson) gak perlu tau detail ADC mentah/quirks fisik
joystick tertentu.

Jadi Arduino OUTPUT-nya sudah dalam rentang ABSTRAK -100..100 (bukan ADC
mentah 0-1023), sama seperti konvensi `speed` di protokol STM32.

## 2. Input fisik panel (dari diskusi GCS)

| Input | Tipe | Keterangan |
|---|---|---|
| Joystick 1 [X,Y] | analog x2 | Gerak: X=steering, Y=speed (asumsi - konfirmasi ke user urutan sumbu yang benar) |
| DJoystick [X,Y] | analog x2 | Kontrol pan-tilt |
| LRF | digital, EDGE-SENSITIVE | HOLD = laser nyala, LEPAS = request baca jarak (device LRF sendiri auto-matiin laser begitu ngirim hasil jarak) |
| Zoom in | digital, momentary | - |
| Zoom out | digital, momentary | - |
| Body Up | digital, momentary | Kontrol motor linear sederhana (grup fbody/bbody, lihat gap protokol di `ROS2_BRIEF.md` 7.3) |
| Body Down | digital, momentary | sama seperti Body Up, arah kebalikan |
| Lampu Switch | digital, TOGGLE (bukan momentary) | Nyalain/matiin lampu depan+belakang sekaligus. Depan ikutin slider brightness di app NUC (di luar scope Arduino), belakang digital ON/OFF (kedip-nya kalau mundur itu logic yang dihitung firmware STM32, BUKAN Arduino) |
| Power | digital, switch | Power GCS sendiri (BUKAN slip ring mobil - itu switch terpisah di touchscreen app, gak ada di panel Arduino) |

**Catatan**: "Slip Ring" (switch power kamera+LRF mobil) dan slider
brightness lampu depan itu **widget di touchscreen app NUC**, BUKAN
tombol fisik di panel Arduino - jangan bingung sama daftar di atas.

## 3. Protokol Arduino → NUC (USULAN, BELUM final/dikonfirmasi user)

ASCII, dipisah spasi, `\n`-terminated - konsisten sama gaya protokol lain
di project ini (gampang debug manual lewat Serial Monitor tanpa perlu
Python):

```
"<x1> <y1> <x2> <y2> <lrf> <zoomin> <zoomout> <bodyup> <bodydown> <lampu> <power>\n"
```

| # | Field | Range | Arti |
|---|---|---|---|
| 1 | `x1` | -100..100 (signed) | Joystick 1 X (steering) |
| 2 | `y1` | -100..100 (signed) | Joystick 1 Y (speed) |
| 3 | `x2` | -100..100 (signed) | DJoystick X (pantilt horizontal) |
| 4 | `y2` | -100..100 (signed) | DJoystick Y (pantilt vertikal) |
| 5 | `lrf` | 0/1 | 1 = tombol LRF lagi ditahan |
| 6 | `zoomin` | 0/1 | 1 = tombol zoom in lagi ditekan |
| 7 | `zoomout` | 0/1 | 1 = tombol zoom out lagi ditekan |
| 8 | `bodyup` | 0/1 | 1 = tombol body up lagi ditekan |
| 9 | `bodydown` | 0/1 | 1 = tombol body down lagi ditekan |
| 10 | `lampu` | 0/1 | state toggle switch lampu (bukan momentary) |
| 11 | `power` | 0/1 | state switch power GCS |

**11 field total.** Baudrate diusulkan **57600** (konsisten sama
konvensi lain di project), boleh disesuaikan.

### Kenapa ASCII + kirim terus-menerus (heartbeat), bukan event-driven
Sama alasannya kayak protokol STM32 (`STM32_BRIEF.md` bagian 4): gampang
didebug manual, dan kalau 1 baris nyasar/rusak di serial USB, baris
berikutnya (dikirim ~50ms kemudian kalau rate 20Hz) otomatis
"membetulkan" - gak perlu ack/retry logic rumit.

### Dead-zone joystick
Arduino WAJIB terapkan dead-zone di titik tengah tiap sumbu analog
(misal ±5 dari titik tengah kalibrasi) sebelum di-map ke -100..100 -
biar joystick yang dilepas beneran ngasih 0 persis, bukan nilai kecil
random akibat ketidaksempurnaan mekanik/listrik potensiometer.

## 4. Yang PERLU dikonfirmasi ke user sebelum implementasi

1. **Urutan sumbu Joystick 1** - X=steering & Y=speed itu asumsi saya,
   perlu dikonfirmasi mana yang benar secara fisik.
2. **Rate kirim** - diusulkan 20Hz (samain protokol lain), tapi joystick
   gerak/pantilt mungkin butuh rate lebih tinggi buat terasa responsif -
   perlu dites langsung.
3. **Tombol LRF, Zoom, Body Up/Down** - saya asumsikan MOMENTARY (aktif
   selama ditekan, 0 kalau lepas) KECUALI Lampu Switch & Power yang saya
   asumsikan TOGGLE (state tersimpan). Perlu dikonfirmasi asumsi ini benar.
4. **Bagaimana relasi frame ini dengan protokol GCS→Jetson 10-byte**
   (`ROS2_BRIEF.md` 3.5, field `[Estop][Mode][XJoystick1][YJoystick1]
   [XJoystick2][YJoystick2][Zoom][LRF][FLamp][BLamp]`) - aplikasi NUC
   yang tugasnya GABUNGIN frame 11-field dari Arduino ATAU dengan widget
   touchscreen (slip ring switch, slider lampu depan, dll) jadi 1 frame
   10-byte itu. Perlu dipetakan persis field mana ketemu field mana
   (misal `zoomin`+`zoomout` Arduino → gimana jadi 1 field `Zoom` di
   protokol 10-byte - mungkin encoding -1/0/1 kayak pola `steer` di
   protokol STM32?). **Field `Estop` dan `Mode` di protokol 10-byte
   TIDAK ADA sumbernya di frame Arduino ini** - dari mana asalnya? (Estop
   mungkin tombol fisik terpisah yang belum masuk daftar? Mode mungkin
   udah gak relevan - lihat `ROS2_BRIEF.md` section 6 poin 3.)

## 5. Referensi terkait

- `dokumentasi/ROS2_BRIEF.md` - brief utama, section 3.5 (protokol RF),
  3.7 & section 6 (konteks mode/GCS lama), section 7 (arsitektur app NUC)
- `Testcode/test_rf_link.py` - format 13-field SISTEM LAMA ("panel
  koper"), BUKAN protokol yang dipakai sekarang, tapi berguna sebagai
  referensi gaya/konvensi kalau perlu
- `dokumentasi/GCS/GCS.drawio` - kemungkinan ada detail skema kontrol GCS
  yang lebih visual
