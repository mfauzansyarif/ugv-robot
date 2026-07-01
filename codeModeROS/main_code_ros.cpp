// kode ini kontrol dari ros -->> BLDC dan motor linear Steering
// pin motor linear harus ditinjau ulang karna ada yang nabrak dengan serial monitor
// Serial RX TX ada dua yang di pakai USBTX,USBRX (belum tau di pin brpa yang keganggu sm motor linear)
// Serial RX TX 1 lagi untuk debuging ada pada pin PA_9 dan PA_10


#include "mbed.h"

DigitalOut b1(PB_9); 
DigitalOut f1(PB_15);
DigitalOut r1(PB_8);
PwmOut pwm1(PC_6);

DigitalOut b2(PB_5); 
DigitalOut f2(PG_14); 
DigitalOut r2(PA_15); 
PwmOut pwm2(PC_7);

DigitalOut b3(PF_5); 
DigitalOut r3(PF_4);
DigitalOut f3(PG_12); 
PwmOut pwm3(PD_14);

DigitalOut b4(PA_4); 
DigitalOut r4(PB_4); 
DigitalOut f4(PF_3);
PwmOut pwm4(PD_15);

DigitalOut ml_dir1_I(PB_2);
DigitalOut ml_dir2_I(PE_8);
PwmOut ml_pwm_I(PD_13);

DigitalOut ml_dir1_J(PE_7);//
DigitalOut ml_dir2_J(PE_10);
PwmOut ml_pwm_J(PD_12);

DigitalOut ml_dir1_K(PD_11);
DigitalOut ml_dir2_K(PE_0);//
PwmOut ml_pwm_K(PA_0);

DigitalOut ml_dir1_L(PE_12);
DigitalOut ml_dir2_L(PE_15);
PwmOut ml_pwm_L(PB_10);

DigitalOut ml_dir1_A(PD_7);
DigitalOut ml_dir2_A(PD_6);
PwmOut ml_pwm_A(PA_3);

DigitalOut ml_dir1_B(PD_4);//
DigitalOut ml_dir2_B(PD_3);
PwmOut ml_pwm_B(PB_1);

DigitalOut ml_dir1_C(PE_4);
DigitalOut ml_dir2_C(PE_2);//
// PwmOut ml_pwm_C(PE_5);

DigitalOut ml_dir1_D(PC_8);
DigitalOut ml_dir2_D(PC_10);
PwmOut ml_pwm_D(PC_9);

DigitalOut ml_dir1_E(PE_6);
DigitalOut ml_dir2_E(PE_3);
PwmOut ml_pwm_E(PB_3);

DigitalOut ml_dir1_F(PD_0);//
DigitalOut ml_dir2_F(PD_1);
PwmOut ml_pwm_F(PA_5);

DigitalOut ml_dir1_G(PG_0);
DigitalOut ml_dir2_G(PG_1);//
PwmOut ml_pwm_G(PF_9);

DigitalOut ml_dir1_H(PB_6);
DigitalOut ml_dir2_H(PB_7);
PwmOut ml_pwm_H(PA_6);


// Serial communication configuration
Serial uart1(USBTX, USBRX); // Serial communication with the PC
Serial pc(PA_9, PA_10);     // UART1 for communication with Jetson Nano

int mode;
float pwm_value = 0.0;
int mode_fbw_steer,mode_mid_elv;
int init_motor;
int dir_motor;
char *vx;

bool newData = false;
const int numChars = 100;
char receivedChars[numChars];

void recvWithEndMarker() {
    static int ndx = 0;
    char endMarker = '\n';
    char rc;
    
    while (uart1.readable() > 0 && newData == false){
        rc = uart1.getc();
    //    printf("%c\n",rc);

        if (rc != endMarker){
              receivedChars[ndx] = rc;
              ndx++;
              if (ndx >= numChars) {
                  ndx = numChars;
              }
        }
        else {
            receivedChars[ndx] = '\0'; // terminate the string
            ndx = 0;
            newData = true;
        }
    }
}

void olahDataString(){
        vx = strtok(receivedChars," ");
        mode = atof(vx); // data pertama
        
        vx = strtok(NULL, " "); 
        pwm_value = atof(vx); // data kedua

        vx = strtok(NULL, " ");
        mode_fbw_steer = atof(vx);// data ketiga

        vx = strtok(NULL, " ");
        mode_mid_elv = atof(vx); // data keempat

        vx = strtok(NULL, " ");
        init_motor = atof(vx); // data kelima

        vx = strtok(NULL, " ");
        dir_motor = atof(vx); // data keenam
}

int main() {
    // Initialize serial communication
    pc.baud(115200);
    uart1.baud(115200);
    pc.printf("tes ulang 12\n");

    while (true) {
        recvWithEndMarker();
        if(newData == true){
        //   pc.printf("%s \n", receivedChars);
          olahDataString(); 
        // //   printf("%f \t", Exr);
          pc.printf("%d \t", mode);
          pc.printf("%f \t", pwm_value/100);
          pc.printf("%d \t", mode_fbw_steer);
          pc.printf("%d \t", mode_mid_elv);
          pc.printf("%d \t", init_motor);
          pc.printf("%d \n", dir_motor);
            // independent control start
        if(mode == 4){
            if(init_motor == 1){
                pc.printf("motor 1\n");
                if(dir_motor == 1){
                    ml_pwm_E = 1.0;
                    ml_dir1_E = 1;ml_dir2_E = 0;
                    pc.printf("motor 1 kanan\n");
                }else if(dir_motor == 2){
                    ml_pwm_E = 1.0;
                    ml_dir1_E = 0;ml_dir2_E = 1;
                    pc.printf("motor 1 kiri\n");
                }else{
                    ml_pwm_E = 0.0;
                    ml_dir1_E = 0;ml_dir2_E = 0;
                    pc.printf("motor 1 stop\n");
                }
            }else if(init_motor == 2){
                pc.printf("motor 2\n");
                if(dir_motor == 1){
                    ml_pwm_G = 1.0;
                    ml_dir1_G = 1;ml_dir2_G = 0;
                    pc.printf("motor 2 kanan\n");
                }else if(dir_motor == 2){
                    ml_pwm_G = 1.0;
                    ml_dir1_G = 0;ml_dir2_G = 1;
                    pc.printf("motor 2 kiri\n");
                }else{
                    ml_pwm_G = 0.0;
                    ml_dir1_G = 0;ml_dir2_G = 0;
                    pc.printf("motor 2 stop\n");
                }
            }else if (init_motor == 3) {
                pc.printf("motor 3\n");
                if(dir_motor == 1){
                    ml_pwm_H = 1.0;
                    ml_dir1_H = 1;ml_dir2_H = 0;
                    pc.printf("motor 3 kanan\n");
                }else if(dir_motor == 2){
                    ml_pwm_H = 1.0;
                    ml_dir1_H = 0;ml_dir2_H = 1;
                    pc.printf("motor 3 kiri\n");
                }else{
                    ml_pwm_H = 0.0;
                    ml_dir1_H = 0;ml_dir2_H = 0;
                    pc.printf("motor 3 stop\n");
                }
            }else if (init_motor == 4) {
                pc.printf("motor 4\n");
                if(dir_motor == 1){
                    ml_pwm_J = 1.0;
                    ml_dir1_J = 1;ml_dir2_J = 0;
                    pc.printf("motor 4 kanan\n");
                }else if(dir_motor == 2){
                    ml_pwm_J = 1.0;
                    ml_dir1_J = 0;ml_dir2_J = 1;
                    pc.printf("motor 4 kiri\n");
                }else{
                    ml_pwm_J = 0.0;
                    ml_dir1_J = 0;ml_dir2_J = 0;
                    pc.printf("motor 4 stop\n");
                }
            }else if (init_motor == 5) {
                pc.printf("motor 5\n");
                if(dir_motor == 1){
                    ml_pwm_D = 1.0;
                    ml_dir1_D = 1;ml_dir2_D = 0;
                    pc.printf("motor 5 kanan\n");
                }else if(dir_motor == 2){
                    ml_pwm_D = 1.0;
                    ml_dir1_D = 0;ml_dir2_D = 1;
                    pc.printf("motor 5 kiri\n");
                }else{
                    ml_pwm_D = 0.0;
                    ml_dir1_D = 0;ml_dir2_D = 0;
                    pc.printf("motor 5 stop\n");
                }
            }else if (init_motor == 6) {
                pc.printf("motor 6\n");
                if(dir_motor == 1){
                    ml_pwm_L = 1.0;
                    ml_dir1_L = 1;ml_dir2_L = 0;
                    pc.printf("motor 6 kanan\n");
                }else if(dir_motor == 2){
                    ml_pwm_L = 1.0;
                    ml_dir1_L = 0;ml_dir2_L = 1;
                    pc.printf("motor 6 kiri\n");
                }else{
                    ml_pwm_L = 0.0;
                    ml_dir1_L = 0;ml_dir2_L = 0;
                    pc.printf("motor 6 stop\n");
                }
            }else if (init_motor == 7) {
                pc.printf("motor 7\n");
                if(dir_motor == 1){
                    ml_pwm_I = 1.0;
                    ml_dir1_I = 1;ml_dir2_I = 0;
                    pc.printf("motor 7 kanan\n");
                }else if(dir_motor == 2){
                    ml_pwm_I = 1.0;
                    ml_dir1_I = 0;ml_dir2_I = 1;
                    pc.printf("motor 7 kiri\n");
                }else{
                    ml_pwm_I = 0.0;
                    ml_dir1_I = 0;ml_dir2_I = 0;
                    pc.printf("motor 7 stop\n");
                }
            }else if (init_motor == 8) {
                pc.printf("motor 8\n");
                if(dir_motor == 1){
                    ml_pwm_F = 1.0;
                    ml_dir1_F = 1;ml_dir2_F = 0;
                    pc.printf("motor 8 kanan\n");
                }else if(dir_motor == 2){
                    ml_pwm_F = 1.0;
                    ml_dir1_F = 0;ml_dir2_F = 1;
                    pc.printf("motor 8 kiri\n");
                }else{
                    ml_pwm_F = 0.0;
                    ml_dir1_F = 0;ml_dir2_F = 0;
                    pc.printf("motor 8 stop\n");
                }
            }
        }else if(mode == 1){
                f1 = 1.0;
                r1 = 0.0;
                b1 = 0.0;

                f2 = 1.0;
                r2 = 0.0;
                b2 = 0.0;

                f3 = 1.0;
                r3 = 0.0;
                b3 = 0.0;

                f4 = 1.0;
                r4 = 0.0;
                b4 = 0.0;

                pwm1 = pwm_value/100;
                pwm2 = pwm_value/100;
                pwm3 = pwm_value/100;
                pwm4 = pwm_value/100;
                pc.printf("forward\n");


            }else if(mode == 2){
                f1 = 0.0;
                r1 = 1.0;
                b1 = 0.0;

                f2 = 0.0;
                r2 = 1.0;
                b2 = 0.0;

                f3 = 0.0;
                r3 = 1.0;
                b3 = 0.0;

                f4 = 0.0;
                r4 = 1.0;
                b4 = 0.0;

                pwm1 = pwm_value/100;
                pwm2 = pwm_value/100;
                pwm3 = pwm_value/100;
                pwm4 = pwm_value/100;
                pc.printf("reverse\n");

            }else if(mode == 3){ //break
                f1 = 0.0;
                r1 = 0.0;
                b1 = 1.0;

                f2 = 0.0;
                r2 = 0.0;
                b2 = 1.0;

                f3 = 0.0;
                r3 = 0.0;
                b3 = 1.0;

                f4 = 0.0;
                r4 = 0.0;
                b4 = 1.0;
                pwm1 = pwm_value/100;
                pwm2 = pwm_value/100;
                pwm3 = pwm_value/100;
                pwm4 = pwm_value/100;
                pc.printf("break\n");
                
            }else if(mode == 0){
                f1 = 0.0;
                r1 = 0.0;
                b1 = 0.0;

                f2 = 0.0;
                r2 = 0.0;
                b2 = 0.0;

                f3 = 0.0;
                r3 = 0.0;
                b3 = 0.0;

                f4 = 0.0;
                r4 = 0.0;
                b4 = 0.0;
                pc.printf("zero state\n");
            }
            // independent control end

        if(mode != 4){    
            if(mode_fbw_steer == 1){
                ml_pwm_E = 1.0;
                ml_dir1_E = 1;ml_dir2_E = 0;

                ml_pwm_H = 1.0;
                ml_dir1_H = 0;ml_dir2_H = 1;
                pc.printf("linear fw turn left\n");
            }else if(mode_fbw_steer == 2){ 
                ml_pwm_E = 1.0;
                ml_dir1_E = 0;ml_dir2_E = 1;

                ml_pwm_H = 1.0;
                ml_dir1_H = 1;ml_dir2_H = 0;
                pc.printf("linear fw turn right\n");
            }
            
            if(mode_mid_elv == 1){
                ml_pwm_D = 1.0;
                ml_dir1_D = 0;ml_dir2_D = 1;

                ml_pwm_L = 1.0;
                ml_dir1_L = 0;ml_dir2_L = 1;

                ml_pwm_I = 1.0;
                ml_dir1_I = 0;ml_dir2_I = 1;

                ml_pwm_F = 1.0;
                ml_dir1_F = 0;ml_dir2_F = 1;
                pc.printf("linear turn down\n");
            }else if(mode_mid_elv == 2){
                ml_pwm_D = 1.0;
                ml_dir1_D = 1;ml_dir2_D = 0;

                ml_pwm_L = 1.0;
                ml_dir1_L = 1;ml_dir2_L = 0;

                ml_pwm_I = 1.0;
                ml_dir1_I = 1;ml_dir2_I = 0;

                ml_pwm_F = 1.0;
                ml_dir1_F = 1;ml_dir2_F = 0;
                pc.printf("linear turn up\n");
            }else if(mode_mid_elv == 0 && mode_fbw_steer == 0){
                ml_pwm_A = 0;
                ml_dir1_A = 0;ml_dir2_A = 0;

                ml_pwm_B = 0;
                ml_dir1_B = 0;ml_dir2_B = 0;

                // ml_pwm_C = 0;
                ml_dir1_C = 0;ml_dir2_C = 0;

                ml_pwm_D = 0;
                ml_dir1_D = 0;ml_dir2_D = 0;

                ml_pwm_E = 0;
                ml_dir1_E = 0;ml_dir2_E = 0;

                ml_pwm_F = 0;
                ml_dir1_F = 0;ml_dir2_F = 0;

                ml_pwm_G = 0;
                ml_dir1_G = 0;ml_dir2_G = 0;

                ml_pwm_H = 0;
                ml_dir1_H = 0;ml_dir2_H = 0;

                ml_pwm_I = 0;
                ml_dir1_I = 0;ml_dir2_I = 0;

                ml_pwm_J = 0;
                ml_dir1_J = 0;ml_dir2_J = 0;

                ml_pwm_K = 0;
                ml_dir1_K = 0;ml_dir2_K = 0;

                ml_pwm_L = 0;
                ml_dir1_L = 0;ml_dir2_L = 0;
                pc.printf("zero state\n");
            }
        }
        }
            newData = false;
        
    }
}