int pulsePin = 9;     // Pin untuk sinyal pulse (kecepatan)
int signPin = 10;     // Pin untuk sinyal sign (arah)
int frequency = 500;  // Frekuensi awal untuk pulse (Hz)

void setup() {
  pinMode(pulsePin, OUTPUT);  // Atur pin pulse sebagai output
  pinMode(signPin, OUTPUT);   // Atur pin sign sebagai output
}

void loop() {
  // Mengatur arah motor
  digitalWrite(signPin, HIGH);  // HIGH = maju, LOW = mundur

  // Mengirim sinyal pulse dengan frekuensi tertentu
  tone(pulsePin, frequency);    // Mengaktifkan pulse dengan frekuensi

//  delay(2000);                  // Motor berputar selama 2 detik

  // Mengubah arah motor
//  digitalWrite(signPin, LOW);   // Ganti arah

//  delay(2000);                  // Motor berputar selama 2 detik dengan arah baru

  // Mematikan pulse
//  noTone(pulsePin);             // Matikan sinyal di pin pulse

//  delay(1000);                  // Jeda sebelum mulai lagi
}
