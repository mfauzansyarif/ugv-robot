#include "mbed.h"
#include "platform/mbed_thread.h"

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

Serial pc(USBTX, USBRX);
// Serial deb(PC_10, PC_11);


int main(){
    pc.baud(9600);
    // deb.baud(9600);
    pc.printf("SERIAL mulai 3\n");
    // deb.printf("DEB mulai\n");

    while (true) {
        while(pc.readable() > 0){
		char data = pc.getc();
		if(data == 'o'){
			pwm1 = pwm1 + 0.05;
            pwm2 = pwm2 + 0.05;
            pwm3 = pwm3 + 0.05;
            pwm4 = pwm4 + 0.05;
			pc.printf("pwm increase : %f\n", pwm1.read());

		}else if(data == 'p'){
            pwm1 = pwm1 - 0.05;
            pwm2 = pwm2 - 0.05;
            pwm3 = pwm3 - 0.05;
            pwm4 = pwm4 - 0.05;
			pc.printf("pwm decrease : %f\n", pwm1.read());
            
		}else if(data == 'w'){ //forward
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
			pc.printf("forward\n");
            
		}else if(data == 's'){ //reverse
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
			pc.printf("reverse\n");
            
		}else if(data == 'a'){ //left
			f1 = 1.0;
			r1 = 0.0;
			b1 = 0.0;

            f2 = 1.0;
			r2 = 0.0;
			b2 = 0.0;

            f3 = 0.0;
			r3 = 1.0;
			b3 = 0.0;

            f4 = 0.0;
			r4 = 1.0;
			b4 = 0.0;
			pc.printf("kiri\n");
            
		}else if(data == 'd'){ //right
			f1 = 0.0;
			r1 = 1.0;
			b1 = 0.0;

            f2 = 0.0;
			r2 = 1.0;
			b2 = 0.0;

            f3 = 1.0;
			r3 = 0.0;
			b3 = 0.0;

            f4 = 1.0;
			r4 = 0.0;
			b4 = 0.0;
			pc.printf("kanan\n");
            
		}else if(data == 'c'){ //break
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
			pc.printf("break\n");
            
		}else if(data == '1'){
            ml_pwm_E = 1.0;
            ml_dir1_E = 1;ml_dir2_E = 0;

            ml_pwm_H = 1.0;
            ml_dir1_H = 0;ml_dir2_H = 1;
            pc.printf("linear fw turn left\n");
        }else if(data == '2'){ 
            ml_pwm_E = 1.0;
            ml_dir1_E = 0;ml_dir2_E = 1;

            ml_pwm_H = 1.0;
            ml_dir1_H = 1;ml_dir2_H = 0;
            pc.printf("linear fw turn right\n");
        }else if(data == '3'){
            ml_pwm_G = 1.0;
            ml_dir1_G = 1;ml_dir2_G = 0;

            ml_pwm_J = 1.0;
            ml_dir1_J = 0;ml_dir2_J = 1;
            pc.printf("linear bw turn left\n");
        }else if(data == '4'){
            ml_pwm_G = 1.0;
            ml_dir1_G = 0;ml_dir2_G = 1;

            ml_pwm_J = 1.0;
            ml_dir1_J = 1;ml_dir2_J = 0;
            pc.printf("linear bw turn right\n");
        }else if(data == '5'){
            ml_pwm_D = 1.0;
            ml_dir1_D = 0;ml_dir2_D = 1;

            ml_pwm_L = 1.0;
            ml_dir1_L = 0;ml_dir2_L = 1;

            ml_pwm_I = 1.0;
            ml_dir1_I = 0;ml_dir2_I = 1;

            ml_pwm_F = 1.0;
            ml_dir1_F = 0;ml_dir2_F = 1;
            pc.printf("linear turn down\n");
        }else if(data == '6'){
            ml_pwm_D = 1.0;
            ml_dir1_D = 1;ml_dir2_D = 0;

            ml_pwm_L = 1.0;
            ml_dir1_L = 1;ml_dir2_L = 0;

            ml_pwm_I = 1.0;
            ml_dir1_I = 1;ml_dir2_I = 0;

            ml_pwm_F = 1.0;
            ml_dir1_F = 1;ml_dir2_F = 0;
            pc.printf("linear turn up\n");
        }else if(data == '0'){
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
	}
    }
}
