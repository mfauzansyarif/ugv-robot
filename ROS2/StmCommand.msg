# Down-frame Jetson -> STM32, 21 byte, format "=b8bBBBbbbBBBBBB"
# Semua field SUDAH FINAL - STM32 tinggal apply, gak mikir apa-apa lagi.
int8 speed
int8[8] act
uint8 f_lamp
uint8 b_lamp
uint8 b_lamp_mode
int8 pantilt_horizontal
int8 pantilt_vertical
int8 kamera_zoom
uint8 slip_ring
uint8 lrf_trigger
uint8 gcs_reply_stm32_status
uint8 gcs_reply_lrf_status
uint8 gcs_reply_lrf_lsb
uint8 gcs_reply_lrf_msb
