/*
  Kontrol 2 motor AC servo (HK Series driver, Position Control PA4=0) dari
  Arduino Mega Pro. Generate pulse train independen buat 2 motor SEKALIGUS,
  pakai akses timer hardware langsung (Timer3 & Timer4) - BUKAN tone(),
  karena tone() cuma bisa 1 channel aktif dalam satu waktu.

  MOTOR 1: PULS1 = D6 (OC4A/Timer4), SIGN1 = D7 (digital biasa)
  MOTOR 2: PULS2 = D5 (OC3A/Timer3), SIGN2 = D8 (digital biasa)
  (Ganti pin ini kalau mau beda - pastikan PULS pin tetap di pin yang
  support Output Compare Timer3/Timer4 kalau mau ganti)

  Setting parameter driver (SAMA buat kedua driver motor):
  PA4=0, PA14=0, PA20=1, PA53=0001 (lihat versi 1-motor sebelumnya buat
  penjelasan detail tiap parameter)
*/

const uint8_t PIN_PULS1 = 6;
const uint8_t PIN_SIGN1 = 7;
const uint8_t PIN_PULS2 = 5;
const uint8_t PIN_SIGN2 = 8;

bool arahCW1 = true, arahCW2 = true;
bool jalan1 = false, jalan2 = false;
unsigned int freq1 = 5000, freq2 = 5000;

// Hitung prescaler & OCR paling presisi buat frekuensi yang diminta
uint8_t hitungPrescaler(long freqHz, uint16_t &ocrOut) {
  const uint32_t prescalers[] = {1, 8, 64, 256, 1024};
  const uint8_t csBits[]      = {0b001, 0b010, 0b011, 0b100, 0b101};
  for (uint8_t i = 0; i < 5; i++) {
    uint32_t ocr = (F_CPU / (2UL * prescalers[i] * freqHz)) - 1;
    if (ocr <= 65535UL) {
      ocrOut = (uint16_t)ocr;
      return csBits[i];
    }
  }
  ocrOut = 65535;
  return 0b101; // fallback prescaler terbesar kalau freq kelewat rendah
}

void setFreqMotor1(long freqHz) {
  uint16_t ocr;
  uint8_t cs = hitungPrescaler(freqHz, ocr);
  TCCR4A = (1 << COM4A0);              // toggle OC4A tiap compare match
  TCCR4B = (1 << WGM42) | cs;          // CTC mode, set prescaler
  OCR4A = ocr;
}

void setFreqMotor2(long freqHz) {
  uint16_t ocr;
  uint8_t cs = hitungPrescaler(freqHz, ocr);
  TCCR3A = (1 << COM3A0);
  TCCR3B = (1 << WGM32) | cs;
  OCR3A = ocr;
}

void stopMotor1() { TCCR4A = 0; digitalWrite(PIN_PULS1, LOW); jalan1 = false; }
void stopMotor2() { TCCR3A = 0; digitalWrite(PIN_PULS2, LOW); jalan2 = false; }

void tampilkanMenu() {
  Serial.println();
  Serial.println(F("=== Kontrol 2 Motor - Position Control (timer langsung) ==="));
  Serial.print(F("Motor1: ")); Serial.print(jalan1 ? "JALAN" : "STOP");
  Serial.print(F(" arah=")); Serial.print(arahCW1 ? "CW" : "CCW");
  Serial.print(F(" freq=")); Serial.println(freq1);
  Serial.print(F("Motor2: ")); Serial.print(jalan2 ? "JALAN" : "STOP");
  Serial.print(F(" arah=")); Serial.print(arahCW2 ? "CW" : "CCW");
  Serial.print(F(" freq=")); Serial.println(freq2);
  Serial.println(F("--- Motor 1 (huruf kecil) ---"));
  Serial.println(F("w=jalan s=stop d=ganti arah +=freq naik -=freq turun"));
  Serial.println(F("--- Motor 2 (huruf besar) ---"));
  Serial.println(F("W=jalan S=stop D=ganti arah I=freq naik K=freq turun"));
  Serial.println(F("? = tampilkan menu ini lagi"));
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_PULS1, OUTPUT); pinMode(PIN_SIGN1, OUTPUT);
  pinMode(PIN_PULS2, OUTPUT); pinMode(PIN_SIGN2, OUTPUT);
  digitalWrite(PIN_PULS1, LOW); digitalWrite(PIN_SIGN1, arahCW1 ? HIGH : LOW);
  digitalWrite(PIN_PULS2, LOW); digitalWrite(PIN_SIGN2, arahCW2 ? HIGH : LOW);
  tampilkanMenu();
}

void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();

  switch (c) {
    // Motor 1
    case 'w': if (!jalan1) { digitalWrite(PIN_SIGN1, arahCW1?HIGH:LOW); setFreqMotor1(freq1); jalan1=true; } break;
    case 's': stopMotor1(); break;
    case 'd': if (!jalan1) { arahCW1=!arahCW1; digitalWrite(PIN_SIGN1, arahCW1?HIGH:LOW); } else Serial.println(F("Stop motor1 dulu (s)")); break;
    case '+': freq1 += 5000; if (jalan1) setFreqMotor1(freq1); break;
    case '-': if (freq1>5000) freq1 -= 5000; if (jalan1) setFreqMotor1(freq1); break;

    // Motor 2
    case 'W': if (!jalan2) { digitalWrite(PIN_SIGN2, arahCW2?HIGH:LOW); setFreqMotor2(freq2); jalan2=true; } break;
    case 'S': stopMotor2(); break;
    case 'D': if (!jalan2) { arahCW2=!arahCW2; digitalWrite(PIN_SIGN2, arahCW2?HIGH:LOW); } else Serial.println(F("Stop motor2 dulu (S)")); break;
    case 'I': freq2 += 5000; if (jalan2) setFreqMotor2(freq2); break;
    case 'K': if (freq2>5000) freq2 -= 5000; if (jalan2) setFreqMotor2(freq2); break;

    case '?': tampilkanMenu(); break;
    default: break;
  }

  if (c!='?') tampilkanMenu();
}
