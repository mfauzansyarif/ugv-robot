# Up-frame offset 0-14: relay MENTAH dari GCS, STM32 gak interpretasi apapun
uint8 estop
int8 x_joy1
int8 y_joy1
int8 x_joy2
int8 y_joy2
int8 zoom
uint8 lrf
uint8 f_lamp
uint8 b_lamp
uint8 slip_ring
int8 body_up_down
uint8 motor_individual_id
int8 motor_individual_arah
uint8 kalibrasi

# 0=manual, 1=auto - placeholder, belum ada tombol di GCS app (masih
# selalu 0). CV Node cek field ini buat mutusin jalanin inference atau
# nggak (hemat GPU/panas Jetson kalau lagi manual).
uint8 mode
