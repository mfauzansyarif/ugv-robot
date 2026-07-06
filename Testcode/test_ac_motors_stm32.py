"""Test tool kirim command ke STM32 (sistem BARU, bukan firmware v1 lama) buat
kontrol 4 motor AC servo (roda utama UGV v2).

=====================================================================
FORMAT FRAME
=====================================================================
ASCII, 1 baris per update, newline-terminated:

    "M <speed1> <speed2> <speed3> <speed4>\\n"

  - "M"              = tag frame ini "Motor AC". Nanti kalau nambah 12 motor
                        linear, itu dikasih tag BEDA, misal "L <speed1> ...
                        <speed12>\\n" - baris terpisah sendiri, biar frame
                        motor AC ini gak ikut kepanjangan pas linear motor
                        ditambahin. STM32 tinggal cek karakter pertama tiap
                        baris (strtok token ke-1) buat nentuin ini frame
                        jenis apa.
  - speed1..speed4   = integer -100..100 buat masing2 dari 4 motor AC.
                        Tanda (+/-) nentuin arah (+ = maju/CW, - = mundur/
                        CCW), angka nentuin besaran speed - nanti di-mapping
                        firmware ke frekuensi pulsa PULS masing2 motor
                        (lihat diskusi position-control-as-continuous-motion
                        di test_position_control_arduino.ino). 0 = motor itu
                        stop.

Kenapa ASCII (bukan binary/checksum kaya protokol pantilt-LRF)
  - Tetap gampang di-debug manual - bisa diketik langsung di serial
    terminal (PuTTY/Arduino Serial Monitor) buat tes tanpa Python sama
    sekali, beda dengan protokol RS485 pantilt/LRF yang emang harus binary
    karena itu ngikutin protokol closed pabrikan hardware-nya.
  - Parsing di STM32 gampang pakai strtok(), pola yang sama kaya yang
    sudah pernah dipakai di main_code_ros.cpp versi lama.
  - Untuk jumlah field sekecil ini (4-16 angka), ukurannya jauh dari bikin
    delay: di 115200 baud, 1 baris ~20-30 karakter cuma butuh ~2-3ms buat
    kekirim penuh, sedangkan frame ini dikirim tiap 50ms (20Hz) - byte di
    kabel jauh lebih santai dibanding rate kirimnya.

Kenapa frame ini dikirim TERUS-MENERUS oleh background thread (bukan cuma
sekali tiap ganti command)
  - Kalau 1 baris hilang/kepotong di jalan (serial noise), baris berikutnya
    yang nyampe 50ms kemudian otomatis "membetulkan" - motor gak nyangkut
    lama di state yang salah.
  - Ini juga buka jalan buat firmware STM32 pasang WATCHDOG: kalau gak ada
    baris valid masuk lebih dari ~300ms, otomatis stop semua motor. Ini
    langsung nutup celah mirip bug lama "default_message 2 kata" yang
    pernah ditemukan di ros_jetson.py (field kurang -> parsing crash MCU).

PENTING buat sisi firmware STM32 (di luar cakupan file Python ini, tapi
WAJIB diterapkan supaya gak mengulang bug lama):
  Sebelum manggil atoi()/atof() ke hasil strtok(), WAJIB cek dulu hasilnya
  bukan NULL, dan jumlah token yang kebaca harus PAS 5 (tag "M" + 4 angka).
  Baris yang formatnya gak lengkap/rusak harus DIABAIKAN total (bukan
  diproses sebagian pakai nilai default 0 diam-diam) - kalau baris tsb
  diabaikan maka watchdog timeout yang akan mengambil alih (stop motor),
  bukan parsing crash kayak main_code_ros.cpp lama.

Requirement: pip install pyserial
"""

import threading
import time

import serial
import serial.tools.list_ports

BAUDRATE = 115200
KIRIM_HZ = 20  # frekuensi kirim frame per detik (20Hz = tiap 50ms)
JUMLAH_MOTOR = 4


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


class PengirimMotorAC:
    """Kirim state 4 motor AC ke STM32 terus-menerus lewat background thread,
    supaya "heartbeat" jalan terlepas dari kapan user ngetik command baru."""

    def __init__(self, ser):
        self.ser = ser
        self.speed = [0] * JUMLAH_MOTOR
        self.lock = threading.Lock()
        self.jalan = True
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.set_semua(0)
        time.sleep(2.0 / KIRIM_HZ)  # kasih waktu 1-2 frame stop beneran kekirim
        self.jalan = False
        self.thread.join(timeout=1)

    def set_motor(self, index, nilai):
        nilai = max(-100, min(100, nilai))
        with self.lock:
            self.speed[index] = nilai

    def set_semua(self, nilai):
        nilai = max(-100, min(100, nilai))
        with self.lock:
            self.speed = [nilai] * JUMLAH_MOTOR

    def _buat_baris(self):
        with self.lock:
            speed_sekarang = list(self.speed)
        return "M " + " ".join(str(s) for s in speed_sekarang) + "\n"

    def _loop(self):
        interval = 1.0 / KIRIM_HZ
        while self.jalan:
            baris = self._buat_baris()
            self.ser.write(baris.encode("utf-8"))
            time.sleep(interval)


def proses_perintah(pengirim, teks):
    bagian = teks.strip().lower().split()
    if not bagian:
        return True

    perintah = bagian[0]

    if perintah in ("keluar", "q"):
        return False

    if perintah == "status":
        with pengirim.lock:
            print(f"Speed motor saat ini: {pengirim.speed}")
        return True

    if perintah == "stop":
        pengirim.set_semua(0)
        print("Semua motor AC: STOP")
        return True

    if perintah == "maju":
        speed = int(bagian[1]) if len(bagian) > 1 else 50
        pengirim.set_semua(speed)
        print(f"Semua motor AC: MAJU @ speed {speed}")
        return True

    if perintah == "mundur":
        speed = int(bagian[1]) if len(bagian) > 1 else 50
        pengirim.set_semua(-speed)
        print(f"Semua motor AC: MUNDUR @ speed {speed}")
        return True

    if perintah == "motor":
        if len(bagian) < 3:
            print("Format: motor <1-4> <maju/mundur/stop> [speed]")
            return True
        try:
            nomor = int(bagian[1])
        except ValueError:
            print("Nomor motor harus angka 1-4")
            return True
        if nomor < 1 or nomor > JUMLAH_MOTOR:
            print(f"Nomor motor harus 1-{JUMLAH_MOTOR}")
            return True
        aksi = bagian[2]
        speed_input = int(bagian[3]) if len(bagian) > 3 else 50
        if aksi == "maju":
            pengirim.set_motor(nomor - 1, speed_input)
        elif aksi == "mundur":
            pengirim.set_motor(nomor - 1, -speed_input)
        elif aksi == "stop":
            pengirim.set_motor(nomor - 1, 0)
        else:
            print("Aksi harus maju/mundur/stop")
            return True
        speed_tampil = 0 if aksi == "stop" else speed_input
        print(f"Motor {nomor}: {aksi} @ speed {speed_tampil}")
        return True

    print("Perintah gak dikenali. Ketik '?' buat lihat menu.")
    return True


def tampilkan_menu():
    print(
        "\n=== Kontrol 4 Motor AC (roda utama) via STM32 ===\n"
        "  maju [speed]               -> semua motor maju bareng (default speed 50)\n"
        "  mundur [speed]             -> semua motor mundur bareng\n"
        "  stop                       -> semua motor stop\n"
        "  motor <1-4> maju [speed]   -> 1 motor spesifik maju\n"
        "  motor <1-4> mundur [speed] -> 1 motor spesifik mundur\n"
        "  motor <1-4> stop           -> 1 motor spesifik stop\n"
        "  status                     -> lihat speed semua motor saat ini\n"
        "  ?                          -> tampilkan menu ini lagi\n"
        "  keluar                     -> keluar (otomatis stop semua dulu)\n"
        "  speed: -100..100 (+ = maju/CW, - = mundur/CCW)\n"
    )


def main():
    port = pilih_port()
    baud_input = input(f"Baudrate (kosongkan buat default {BAUDRATE}): ").strip()
    baudrate = int(baud_input) if baud_input else BAUDRATE

    print(f"\nMembuka {port} @ {baudrate} baud...")
    with serial.Serial(port, baudrate, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        time.sleep(2)  # kasih waktu board settle abis port dibuka
        print("Terhubung.")

        pengirim = PengirimMotorAC(ser)
        pengirim.start()
        print(f"Mulai kirim frame otomatis @ {KIRIM_HZ}Hz (tiap {1000 / KIRIM_HZ:.0f}ms) di background.")
        tampilkan_menu()

        try:
            while True:
                teks = input("> ")
                if teks.strip() == "?":
                    tampilkan_menu()
                    continue
                if not proses_perintah(pengirim, teks):
                    break
        except KeyboardInterrupt:
            print("\nCtrl+C - stop semua motor dulu...")
        finally:
            pengirim.stop()
            print("Semua motor sudah di-stop. Keluar.")


if __name__ == "__main__":
    main()
