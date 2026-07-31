/* ============================================================================
 * Panel GCS Arduino Mega Pro - FINAL
 * Protokol Arduino -> NUC: lihat dokumentasi/ARDUINO_GCS_BRIEF.md
 * (ASCII, 12 field dipisah spasi, "\n"-terminated, 57600 baud, 20Hz):
 *
 *   "<X> <Y> <lrf> <zoomin> <zoomout> <bodyup> <bodydown> <lampu>
 *    <cam_atas> <cam_kanan> <cam_bawah> <cam_kiri>\n"
 *
 * Diturunkan dari Testcode/gcs_panel_arduino_filtered (versi tes tombol),
 * dengan 2 perubahan buat jadi final:
 *   1. Pin 9/11 ("fokus naik/turun" - dead field, gak ada di protokol
 *      final) di-relabel jadi Body Naik/Turun (tombol fisiknya sama,
 *      cuma fungsinya yang beda - dikonfirmasi user).
 *   2. Joystick sekarang di-map ke rentang 0-1000 (dulu cuma raw ADC
 *      0-1023 + deadzone, belum di-remap) - range fisik joystick yang
 *      dipakai ternyata cuma ~100-900 (gak mentok 0-1023 penuh, sudah
 *      diukur manual & dikonfirmasi user), makanya perlu MIN_TERUKUR/
 *      MAX_TERUKUR di bawah, BUKAN 0-1023.
 * ==========================================================================*/

const int PIN_JOY_VRX = A1;   // X - steering (kabel fisik ketuker sama Y, dibalik di sini)
const int PIN_JOY_VRY = A0;   // Y - speed   (kabel fisik ketuker sama X, dibalik di sini)

const int PIN_LRF         = 3;
const int PIN_ZOOM_NAIK   = 5;   // zoomin
const int PIN_ZOOM_TURUN  = 7;   // zoomout
const int PIN_BODY_NAIK   = 9;   // bodyup   (dulu label "fokus naik")
const int PIN_BODY_TURUN  = 11;  // bodydown (dulu label "fokus turun")
const int PIN_LAMPU_UTAMA = 25;  // lampu - switch TOGGLE, bukan momentary
const int PIN_KAM_ATAS    = 15;  // cam_atas
const int PIN_KAM_BAWAH   = 17;  // cam_bawah
const int PIN_KAM_KIRI    = 19;  // cam_kiri
const int PIN_KAM_KANAN   = 23;  // cam_kanan

const int PIN_LAMPU_INDIKATOR = 13;  // OUTPUT - HIGH kalo lampu utama nyala (indikator LED lokal di panel, gak ikut dikirim ke NUC)

const unsigned long KIRIM_INTERVAL_MS = 50;  // 20Hz, sama kayak siklus RFLink NUC
unsigned long waktuKirimTerakhir = 0;

/* ---- Filter + kalibrasi joystick ----
 * Range mentah joystick INI (sudah diukur manual, JANGAN pakai 0-1023
 * default) ~100-900 - kalau ganti unit joystick, ukur ulang: gerakin ke
 * ekstrem kiri/kanan/atas/bawah, catat analogRead() mentahnya, update
 * RAW_MIN/RAW_MAX di bawah. */
const int RAW_MIN         = 100;
const int RAW_MAX         = 900;
const int RAW_TENGAH      = (RAW_MIN + RAW_MAX) / 2;  // 500 - dipakai buat deadzone
const int JUMLAH_SAMPLE   = 8;      // berapa kali analogRead per baca (averaging)
const int LEBAR_DEADZONE  = 15;     // +-15 (skala RAW) di sekitar tengah dianggap "diam"
const float ALPHA_SMOOTH  = 0.3f;   // 0.0-1.0, makin kecil makin smooth (tapi makin lambat respon)

float vrxSmooth = RAW_TENGAH;
float vrySmooth = RAW_TENGAH;

/* Baca 1 axis: averaging -> exponential smoothing -> deadzone (skala RAW)
 * -> map ke 0-1000 (skala yang dikirim ke NUC, 500 = netral). */
int bacaAxis0_1000(int pin, float *nilaiSmooth) {
    long total = 0;
    for (int i = 0; i < JUMLAH_SAMPLE; i++) {
        total += analogRead(pin);
        delayMicroseconds(50);  // jeda kecil antar sample, biar ADC settle
    }
    int rataRata = total / JUMLAH_SAMPLE;

    *nilaiSmooth = (ALPHA_SMOOTH * rataRata) + ((1.0f - ALPHA_SMOOTH) * (*nilaiSmooth));
    int rawHasil = (int)(*nilaiSmooth);

    if (abs(rawHasil - RAW_TENGAH) < LEBAR_DEADZONE) {
        rawHasil = RAW_TENGAH;
        *nilaiSmooth = RAW_TENGAH;  // reset smoothing state juga, biar gak "nyangkut"
    }

    int hasil0_1000 = map(rawHasil, RAW_MIN, RAW_MAX, 0, 1000);
    return constrain(hasil0_1000, 0, 1000);
}

int bacaTombol(int pin) {
    return (digitalRead(pin) == LOW) ? 1 : 0;
}

/* Tombol pantilt (cam_atas/kanan/bawah/kiri) wiring fisiknya NC (Normally
 * Closed) - kebalik dari tombol lain yang NO: idle=switch closed=LOW,
 * ditekan=switch open=HIGH (dikonfirmasi user lewat test_arduino_baca_g474.py,
 * kebaca 1 pas idle & malah jadi 0 pas ditekan). Dibalik di sini aja,
 * BUKAN rewiring fisik ke NO. */
int bacaTombolNC(int pin) {
    return (digitalRead(pin) == HIGH) ? 1 : 0;
}

void setup() {
    Serial.begin(57600);

    pinMode(PIN_LRF, INPUT_PULLUP);
    pinMode(PIN_ZOOM_NAIK, INPUT_PULLUP);
    pinMode(PIN_ZOOM_TURUN, INPUT_PULLUP);
    pinMode(PIN_BODY_NAIK, INPUT_PULLUP);
    pinMode(PIN_BODY_TURUN, INPUT_PULLUP);
    pinMode(PIN_LAMPU_UTAMA, INPUT_PULLUP);
    pinMode(PIN_KAM_ATAS, INPUT_PULLUP);
    pinMode(PIN_KAM_BAWAH, INPUT_PULLUP);
    pinMode(PIN_KAM_KIRI, INPUT_PULLUP);
    pinMode(PIN_KAM_KANAN, INPUT_PULLUP);
    pinMode(PIN_LAMPU_INDIKATOR, OUTPUT);
}

void loop() {
    if (millis() - waktuKirimTerakhir >= KIRIM_INTERVAL_MS) {
        waktuKirimTerakhir = millis();

        int x = bacaAxis0_1000(PIN_JOY_VRX, &vrxSmooth);
        int y = bacaAxis0_1000(PIN_JOY_VRY, &vrySmooth);

        int lrf       = bacaTombol(PIN_LRF);
        int zoomin    = bacaTombol(PIN_ZOOM_NAIK);
        int zoomout   = bacaTombol(PIN_ZOOM_TURUN);
        int bodyup    = bacaTombol(PIN_BODY_NAIK);
        int bodydown  = bacaTombol(PIN_BODY_TURUN);
        int lampu     = bacaTombol(PIN_LAMPU_UTAMA);
        digitalWrite(PIN_LAMPU_INDIKATOR, lampu ? HIGH : LOW);

        int camAtas   = bacaTombolNC(PIN_KAM_ATAS);
        int camKanan  = bacaTombolNC(PIN_KAM_KANAN);
        int camBawah  = bacaTombolNC(PIN_KAM_BAWAH);
        int camKiri   = bacaTombolNC(PIN_KAM_KIRI);

        Serial.print(x);         Serial.print(' ');
        Serial.print(y);         Serial.print(' ');
        Serial.print(lrf);       Serial.print(' ');
        Serial.print(zoomin);    Serial.print(' ');
        Serial.print(zoomout);   Serial.print(' ');
        Serial.print(bodyup);    Serial.print(' ');
        Serial.print(bodydown);  Serial.print(' ');
        Serial.print(lampu);     Serial.print(' ');
        Serial.print(camAtas);   Serial.print(' ');
        Serial.print(camKanan);  Serial.print(' ');
        Serial.print(camBawah);  Serial.print(' ');
        Serial.println(camKiri);
    }
}
