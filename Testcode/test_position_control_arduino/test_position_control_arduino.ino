/*
  Test tool: muterin AC servo motor (HK Series driver) pakai POSITION CONTROL
  mode (PA4=0), dari Arduino Mega Pro. Generate pulse train PULS+SIGN terus
  menerus (bukan gerak ke 1 titik terus berhenti) - jadi efeknya motor muter
  terus selama pulsa dikirim, kecepatan putarnya sebanding dengan frekuensi
  pulsa (PULS_PIN pakai tone()/noTone() bawaan Arduino, jalan di hardware
  timer, gak nge-block CPU).

  VERSI MINIMAL - cuma PULS+/PULS- dan SIGN+/SIGN- yang disambung ke driver.
  SON dan CLE SENGAJA TIDAK disambung fisik sama sekali (lihat setting
  parameter di bawah kenapa ini aman dilakukan).

  =====================================================================
  SEBELUM COBA KE HARDWARE ASLI - SETTING PARAMETER DULU LEWAT PANEL DRIVER:
  =====================================================================

  PA4  = 0      (position control mode - biasanya sudah default)
  PA14 = 0      (pulse+sign mode - sudah default, jangan diubah)
  PA20 = 1      (driver disable input diabaikan, jadi FSTP/RSTP gak perlu
                 disambung fisik)
  PA53 = 0001   (force SON ON secara internal terus-menerus, jadi SON
                 TIDAK PERLU disambung kabel/pin sama sekali. Ini persis
                 skenario yang manual sebut: "if it's inconvenient to
                 enable the external control (SON), set PA53 to 0001".
                 Bit ke-0 = SON, itu yang di-set ke 1, bit lain tetap 0)

  Motor U/V/W dan encoder CN2 WAJIB sudah tersambung benar ke driver
  sebelum coba (ini wiring daya/encoder, di luar cakupan kode ini).

  CATATAN soal CLE yang juga tidak disambung: deviation counter mulai dari
  0 setiap kali driver baru dinyalakan (power-on), jadi untuk testing awal
  di frekuensi pulsa rendah ini seharusnya tidak masalah. Kalau suatu saat
  muncul alarm Err-4 (position error / deviation counter kelewat besar),
  cara clear-nya karena CLE gak ada kabel: matikan-nyalakan ulang power
  driver (power cycle) - itu otomatis reset counter ke 0.

  =====================================================================
  WIRING PULS/SIGN (Type3 pulse input, single-ended):
  =====================================================================
  PULS+/SIGN+ itu optocoupler, butuh VCC eksternal + resistor seri di
  jalur +. Kalau pakai VCC=5V (boleh dari 5V Arduino), resistor yang
  dipasang di PULS+ dan SIGN+ masing-masing sekitar 82~120 ohm (sesuai
  tabel Empirical data di manual, Figure 3.5). Pin Arduino di kode ini
  (PIN_PULS, PIN_SIGN) disambung ke PULS- dan SIGN- (bukan ke sisi +).

  Requirement: tidak perlu library tambahan (tone()/noTone() bawaan Arduino)
*/

const uint8_t PIN_PULS = 6;
const uint8_t PIN_SIGN = 7;

bool arahCW = true;
bool motorJalan = false;
unsigned int frekuensiPulsa = 5000;  // Hz - kecepatan awal (lihat catatan di bawah)

void tampilkanMenu() {
  Serial.println();
  Serial.println(F("=== Kontrol Motor - Position Control Mode (minimal, tanpa SON/CLE) ==="));
  Serial.print(F("Status: ")); Serial.println(motorJalan ? "JALAN" : "STOP");
  Serial.print(F("Arah  : ")); Serial.println(arahCW ? "CW" : "CCW");
  Serial.print(F("Freq  : ")); Serial.print(frekuensiPulsa); Serial.println(F(" Hz"));
  Serial.println(F("w = mulai putar     s = stop putar"));
  Serial.println(F("d = ganti arah (harus stop dulu)"));
  Serial.println(F("+ = naikin freq 100Hz     - = turunin freq 100Hz"));
  Serial.println(F("? = tampilkan menu ini lagi"));
}

void mulaiPutar() {
  digitalWrite(PIN_SIGN, arahCW ? HIGH : LOW);
  tone(PIN_PULS, frekuensiPulsa);
  motorJalan = true;
  Serial.println(F("[PULS] motor jalan"));
}

void berhentiPutar() {
  noTone(PIN_PULS);
  digitalWrite(PIN_PULS, LOW);
  motorJalan = false;
  Serial.println(F("[PULS] motor stop"));
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_PULS, OUTPUT);
  pinMode(PIN_SIGN, OUTPUT);

  digitalWrite(PIN_PULS, LOW);
  digitalWrite(PIN_SIGN, arahCW ? HIGH : LOW);

  tampilkanMenu();
}

void loop() {
  if (!Serial.available()) return;
  char masuk = Serial.read();

  switch (masuk) {
    case 'w':
      if (!motorJalan) mulaiPutar();
      break;
    case 's':
      if (motorJalan) berhentiPutar();
      break;
    case 'd':
      if (motorJalan) {
        Serial.println(F("Stop motor dulu (s) sebelum ganti arah."));
      } else {
        arahCW = !arahCW;
        digitalWrite(PIN_SIGN, arahCW ? HIGH : LOW);
        Serial.print(F("Arah diganti ke: "));
        Serial.println(arahCW ? "CW" : "CCW");
      }
      break;
    case '+':
      frekuensiPulsa += 5000;
      if (motorJalan) tone(PIN_PULS, frekuensiPulsa);
      Serial.print(F("Freq sekarang: ")); Serial.println(frekuensiPulsa);
      break;
    case '-':
      if (frekuensiPulsa > 100) frekuensiPulsa -= 5000;
      if (motorJalan) tone(PIN_PULS, frekuensiPulsa);
      Serial.print(F("Freq sekarang: ")); Serial.println(frekuensiPulsa);
      break;
    case '?':
      tampilkanMenu();
      break;
    default:
      break;
  }
}
