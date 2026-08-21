# Hasil deteksi "person" PALING CONFIDENT dari CV Node (YOLO) - 1 target
# per frame. Belum ada lock/tracking multi-orang di sini, itu logic
# tambahan yang nanti nyusul di Core Node.
#
# TODO PENTING: pusat_x/pusat_y ini relatif ke ARAH KAMERA lagi ngadep,
# BUKAN relatif ke arah badan robot - beda kalau pantilt lagi di-pan/tilt
# dari posisi tengah. Firmware STM32 BELUM punya fitur baca sudut pantilt
# (placeholder "baca sudut" cmd2=0x51/0x53 di RS485 belum diimplementasi -
# lihat dokumentasi/ROS2_BRIEF.md), jadi Core Node BELUM BISA kompensasi
# sudut kamera pas nerjemahin ini jadi steer robot. Buat sementara,
# follow-mode HARUS dibatasi cuma boleh aktif kalau pantilt di posisi
# tengah/lurus depan (tanggung jawab operator, bukan dicek otomatis
# sistem) - sampai fitur baca sudut pantilt beneran diimplementasi.
bool terdeteksi

# -100..100, 0=tengah frame. Kanan=+X, Atas=+Y - konvensi SAMA kayak
# xJoy2/yJoy2 dari GCS, biar Core Node gak perlu mikir 2 konvensi beda.
float32 pusat_x
float32 pusat_y

# 0-100, persentase lebar/tinggi frame - proxy JARAK (box makin gede,
# orangnya makin deket). Bukan jarak asli dalam meter.
float32 lebar
float32 tinggi

float32 confidence
