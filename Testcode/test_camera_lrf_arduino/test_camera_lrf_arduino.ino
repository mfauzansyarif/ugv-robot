/*
  Test tool STANDALONE: kontrol kamera (zoom/focus, Pelco-D via RS485) dan
  LRF (protokol custom via UART) dari Arduino Mega Pro. Dikontrol lewat
  Serial Monitor USB (menu interaktif) - INI BELUM jadi bridge yang nerima
  bus RS485 dari Jetson lewat slip ring (itu langkah berikutnya setelah
  bagian ini kebukti jalan ke kamera & LRF fisik).

  =====================================================================
  WIRING
  =====================================================================
  - Serial  (USB, pin 0/1)        : ke laptop, buat menu kontrol & lihat hasil
  - Serial1 (pin 18=TX1, 19=RX1)  : ke MODUL RS485 TRANSCEIVER (misal MAX485),
    yang Ain/Bin-nya nyambung ke kamera. RS485 itu HALF-DUPLEX, jadi modul
    transceiver butuh pin DE/RE (driver enable/receive enable) buat gantian
    mode transmit/receive - disambung ke PIN_RS485_DE di bawah (HIGH =
    transmit, LOW = receive). Kalau modul kamu punya 2 pin terpisah (DE dan
    /RE), tinggal sambung keduanya jadi 1 ke PIN_RS485_DE yang sama (pola
    umum di breakout MAX485).
  - Serial2 (pin 16=TX2, 17=RX2)  : LANGSUNG ke LRF (UART biasa/TTL) - LRF
    BUKAN device RS485, jadi gak butuh transceiver buat jalur ini.

  =====================================================================
  BAUDRATE - SESUAIKAN SETELAH TES EMPIRIS
  =====================================================================
  BAUD_KAMERA masih placeholder 9600 (default paling umum Pelco-D) - kalau
  belum pernah dites, coba dulu pakai Testcode/test_camera_zoom_focus.py
  dari laptop buat cari baudrate yang benar sebelum pindah ke sketch ini.
  BAUD_LRF di-set 115200 sesuai temuan sebelumnya (LRF Noptel default-nya
  115200, bukan 9600 kayak pantilt).

  Requirement: tidak perlu library tambahan
*/

const uint8_t PIN_RS485_DE = 4;  // driver enable modul RS485 (HIGH=transmit, LOW=receive)

const uint32_t BAUD_KAMERA = 9600;   // Pelco-D - GANTI sesuai hasil tes empiris
const uint32_t BAUD_LRF = 115200;    // sesuai temuan sebelumnya

const uint8_t ALAMAT_KAMERA = 1;

// ============================= KAMERA (PELCO-D) =============================

void kameraKirim(uint8_t cmd1, uint8_t cmd2, const char *label) {
  uint8_t data1 = 0x00, data2 = 0x00;
  uint8_t checksum = (ALAMAT_KAMERA + cmd1 + cmd2 + data1 + data2) % 256;
  uint8_t frame[7] = {0xFF, ALAMAT_KAMERA, cmd1, cmd2, data1, data2, checksum};

  digitalWrite(PIN_RS485_DE, HIGH);  // mode transmit
  Serial1.write(frame, 7);
  Serial1.flush();                   // tunggu semua byte beneran kekirim
  digitalWrite(PIN_RS485_DE, LOW);   // balik ke mode receive

  Serial.print(F("[TX kamera] "));
  Serial.print(label);
  Serial.print(F(": "));
  for (uint8_t i = 0; i < 7; i++) {
    if (frame[i] < 0x10) Serial.print('0');
    Serial.print(frame[i], HEX);
    Serial.print(' ');
  }
  Serial.println();
}

void kameraZoomIn()    { kameraKirim(0x00, 0x20, "zoom in"); }
void kameraZoomOut()   { kameraKirim(0x00, 0x40, "zoom out"); }
void kameraFocusNear() { kameraKirim(0x01, 0x00, "focus near"); }
void kameraFocusFar()  { kameraKirim(0x00, 0x80, "focus far"); }
void kameraStop()      { kameraKirim(0x00, 0x00, "stop"); }

// ============================= LRF (CUSTOM PROTOCOL) =============================

uint8_t lrfChecksum(uint8_t *payload, uint8_t panjang) {
  uint16_t jumlah = 0;
  for (uint8_t i = 0; i < panjang; i++) jumlah += payload[i];
  return (uint8_t)((jumlah % 256) ^ 0x50);
}

void lrfBacaJarak() {
  uint8_t payload[4] = {0xCC, 0x10, 0x00, 0x00};
  uint8_t checksum = lrfChecksum(payload, 4);

  while (Serial2.available()) Serial2.read();  // bersihin sisa buffer sebelumnya

  Serial2.write(payload, 4);
  Serial2.write(checksum);

  uint8_t respons[22];
  uint8_t diterima = 0;
  unsigned long batasWaktu = millis() + 500;
  while (diterima < 22 && millis() < batasWaktu) {
    if (Serial2.available()) {
      respons[diterima++] = Serial2.read();
    }
  }

  if (diterima != 22) {
    Serial.print(F("[RX LRF] Respons gak lengkap ("));
    Serial.print(diterima);
    Serial.println(F(" byte, harusnya 22)"));
    return;
  }
  if (respons[0] != 0x59 || respons[1] != 0xCC) {
    Serial.println(F("[RX LRF] Header salah (harusnya 59 CC)"));
    return;
  }
  uint8_t checksumHitung = lrfChecksum(respons, 21);
  if (checksumHitung != respons[21]) {
    Serial.println(F("[RX LRF] Checksum mismatch"));
    return;
  }
  float jarak;
  memcpy(&jarak, &respons[2], 4);
  Serial.print(F("[RX LRF] Jarak: "));
  Serial.print(jarak, 2);
  Serial.println(F(" meter"));
}

void lrfLampu(bool nyala) {
  uint8_t payload[2] = {0xC5, (uint8_t)(nyala ? 0x02 : 0x00)};
  uint8_t checksum = lrfChecksum(payload, 2);
  Serial2.write(payload, 2);
  Serial2.write(checksum);
  Serial.println(nyala ? F("[TX LRF] lampu ON") : F("[TX LRF] lampu OFF"));
}

// ============================= MENU =============================

void tampilkanMenu() {
  Serial.println();
  Serial.println(F("=== Test Kamera (Pelco-D) + LRF ==="));
  Serial.println(F("-- Kamera --"));
  Serial.println(F("  i = zoom in       o = zoom out"));
  Serial.println(F("  n = focus near    f = focus far"));
  Serial.println(F("  s = stop kamera"));
  Serial.println(F("-- LRF --"));
  Serial.println(F("  r = baca jarak"));
  Serial.println(F("  l = lampu ON      k = lampu OFF"));
  Serial.println(F("? = tampilkan menu ini lagi"));
}

void setup() {
  Serial.begin(115200);
  Serial1.begin(BAUD_KAMERA);
  Serial2.begin(BAUD_LRF);

  pinMode(PIN_RS485_DE, OUTPUT);
  digitalWrite(PIN_RS485_DE, LOW);  // default mode receive

  tampilkanMenu();
}

void loop() {
  if (!Serial.available()) return;
  char masuk = Serial.read();

  switch (masuk) {
    case 'i': kameraZoomIn(); break;
    case 'o': kameraZoomOut(); break;
    case 'n': kameraFocusNear(); break;
    case 'f': kameraFocusFar(); break;
    case 's': kameraStop(); break;
    case 'r': lrfBacaJarak(); break;
    case 'l': lrfLampu(true); break;
    case 'k': lrfLampu(false); break;
    case '?': tampilkanMenu(); break;
    default: break;
  }
}
