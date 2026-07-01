const int hallSensorPin = A0; // Analog pin connected to the Linear Hall Sensor module

void setup() {
  pinMode(hallSensorPin, INPUT); // Set the Hall Sensor pin as INPUT
  Serial.begin(9600); // Initialize serial communication for debugging (optional)
}

void loop() {
  int hallValue = analogRead(hallSensorPin); // Read the analog value from the Linear Hall Sensor
  
  // Display the Hall Sensor value on the Serial Monitor
  Serial.print("Hall Sensor Value: ");
  Serial.println(hallValue);

  // Add your custom actions or functions here based on the sensor readings.

  delay(100); // Add a small delay to avoid rapid repeated detections
}
