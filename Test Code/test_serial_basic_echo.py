"""Test dasar serial - paling sederhana buat cek port & baudrate udah bener.
Kirim "Hello" tiap 1 detik lewat 1 thread, sekaligus dengerin balasan yang
masuk lewat thread lain, jalan paralel. Cocok buat tes loopback (TX-RX
disilang manual) atau device apapun yang sekadar echo balik.

Port: COM3 (ganti PORT di bawah), baudrate 57600.
Requirement: pip install pyserial
"""

import serial
import threading
import time

PORT = 'COM3'  # ganti sesuai port di komputer kamu
BAUD_RATE = 57600

def send_fixed_message(ser):
    """Kirim pesan tetap "Hello" tiap 1 detik, terus-terusan."""
    try:
        while True:
            data = "Hello\n"
            ser.write(data.encode())
            print(f"Sent: {data.strip()}")
            time.sleep(1)
    except serial.SerialException as e:
        print(f"Error sending data: {e}")

def receive_message(ser):
    """Baca & tampilkan data yang masuk dari serial port, terus-terusan."""
    try:
        while True:
            if ser.in_waiting > 0:  # cek ada data yang bisa dibaca
                received = ser.readline().decode('utf-8', errors='replace').strip()
                print(f"Received: {received}")
    except serial.SerialException as e:
        print(f"Error receiving data: {e}")

def main():
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # jeda nunggu koneksi settle
        print(f"Connected to {PORT} at {BAUD_RATE} baud.")

        send_thread = threading.Thread(target=send_fixed_message, args=(ser,))
        receive_thread = threading.Thread(target=receive_message, args=(ser,))

        send_thread.start()
        receive_thread.start()

        send_thread.join()
        receive_thread.join()

    except serial.SerialException as e:
        print(f"Could not open serial port {PORT}: {e}")
    except KeyboardInterrupt:
        print("Program interrupted. Exiting gracefully.")
    finally:
        # pastikan port ketutup pas keluar
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
