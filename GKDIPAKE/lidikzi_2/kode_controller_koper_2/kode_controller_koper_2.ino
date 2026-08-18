#include <ezButton.h>
#include <Keypad.h>

const byte ROWS = 4; 
const byte COLS = 4; 

char hexaKeys[ROWS][COLS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

byte rowPins[ROWS] = {34, 36, 38, 40}; 
byte colPins[COLS] = {42, 44, 43, 45}; //34 36 38 40 42 43 44 45

Keypad customKeypad = Keypad(makeKeymap(hexaKeys), rowPins, colPins, ROWS, COLS);
char key = '0'; 
char ind_motor ='0';

ezButton button1(32);  // create ezButton object that attach to pin 7;
ezButton button2(33);
ezButton button3(46);
ezButton button4(47);
ezButton button5(3); //swtich 1
ezButton button6(5); //switch 2
ezButton button7(7); //switch 3
ezButton button8(9); //switch 4
ezButton button9(11); //switch 5

// max = 922 , min = 110

const int hallSensorPinx = A1; // Analog pin connected to the Linear Hall Sensor module
const int hallSensorPiny = A0;

struct MotorCommand {
    int mode;
    int speed;
};

MotorCommand motor_command(int value) {
    MotorCommand result; // Create an instance of the struct

    if (value > 100) {
        result.mode = 1;
        result.speed = value - 100;
    } 
    else if (value < 100) {
        result.mode = 2;
        result.speed = 100 - value;
    } 
    else { // Handle the case where value == 100
        result.mode = 0; 
        result.speed = 0; 
    }

    return result; // Return the struct with both values
}

int speedselect(int value) {
    if (value < 5) {
        return 0; // Return 0% if value is below 10
    }
    else if (value >= 5 && value <= 202) {
        int speedPercentage = (value / 10) * 10; // Map to nearest 10%
        return speedPercentage;
    }
    else {
        return 100; // default value
    }
}

void setup() {
  pinMode(hallSensorPinx, INPUT); // Set the Hall Sensor pin as INPUT
  pinMode(hallSensorPiny, INPUT); // Set the Hall Sensor pin as INPUT
  Serial.begin(57600); // Initialize serial communication for debugging (optional)
  int pantilt = 0;
//  Serial.println("start");
}

void loop() {
  int hallValuex = analogRead(hallSensorPinx); // Read the analog value from the Linear Hall Sensor
  int hallValuey = analogRead(hallSensorPiny);

  
  hallValuex = map(hallValuex, 100, 915, 0, 200);
  hallValuey = map(hallValuey, 100, 913, 0, 200);

  if (hallValuex >= 125){
    int belok = 3; //kanan
    // Serial.print(" Mode: ");
      Serial.print(belok);
      Serial.print(" ");
      Serial.print("0");
      Serial.print(" ");
      // Serial.print("  -----");
  }
  else if (hallValuex < 90){
    int belok = 4; //kiri
    // Serial.print(" Mode: ");
      Serial.print(belok);
      Serial.print(" ");
      Serial.print("0");
      Serial.print(" ");
      // Serial.print("  -----");
  }
  else {
    // Display the Hall Sensor value on the Serial Monitor
    
    int motor_speed = speedselect(hallValuey);
    MotorCommand command = motor_command(motor_speed);
      // Serial.print(" Mode: ");
      Serial.print(command.mode);
      Serial.print(" ");
      // Serial.print(", Speed: ");
      Serial.print(command.speed);
      Serial.print(" ");
      // Serial.print("  -----");
      // Serial.print("  ");
      // Serial.print(motor_speed);
  }
  button7.loop();
  button8.loop();
  int mid_up = button7.getState();
  int mid_down = button8.getState();
  Serial.print(mid_up);
  Serial.print(" ");
  Serial.print(mid_down);
  Serial.print(" ");

  //keypad
  char customKey = customKeypad.getKey();
  if (customKey){
//    Serial.println(customKey);
    key = customKey;
  }
  Serial.print(key);
  Serial.print(" ");
  
  button5.loop(); //sw 1
  button9.loop();
  int state5 = button5.getState();
  int state9 = button9.getState();

  //button switch ccw state5 dan state9
  if(state5 == 1 && state9 == 1){
    ind_motor = '0';
  }else if(state5 == 0 && state9 == 1){
    //motor ccw
    ind_motor = '1';
  }else if(state5 == 1 && state9 == 0){
    ind_motor = '2';
  }else {
    ind_motor = '0';
  }
  Serial.print(ind_motor);
  Serial.print(" ");

  //button switch cw
  Serial.print("0");
  Serial.print(" ");


  button1.loop(); // MUST call the loop() function first
  button2.loop();
  button3.loop();
  button4.loop();
  button6.loop(); //sw 2


  int state1 = button1.getState();
  int state2 = button2.getState();
  int state3 = button3.getState();
  int state4 = button4.getState();
  int state6 = button6.getState();

  int pantilt = 0;
  if (state2 == 1){
    pantilt = 1; // atas
  }
  else if (state1 == 1){
    pantilt = 2; //kanan
  }
  else if (state3 == 1){
    pantilt = 3; // bawah
  }
  else if (state4 == 1){
    pantilt = 4;  // kiri
  }
  else{
    pantilt = 0;
  }
  Serial.print(pantilt);
  Serial.print(" ");
  Serial.print("0"); //LRF
  Serial.print(" ");

  //sementara decoy zoom +
  Serial.print(state6); //not assigned
  Serial.print(" ");

  //decoy focus +l
  Serial.print("0");
  Serial.print(" ");

  //decoy focus -
  Serial.print("0");
  Serial.print(" ");

  //decoy lampu
  Serial.print("0");
  Serial.print(" ");

  Serial.println("  ");
  delay(250); // Add a small delay to avoid rapid repeated detections
}
