"""
GCS Interface Node
===================
Tugas node ini CUMA translator byte <-> topic ROS2. GAK ADA logic/keputusan
di sini (itu tugas Core Node) - lihat ROS2_BRIEF.md bagian "Prinsip".

Alur singkat:
  GCS --16 byte--> [serial RX] --> publish ke /gcs/command_mentah
  Core Node --> /gcs/status_balik --> di-CACHE (bukan langsung dipakai)
  Setiap kali 16 byte lengkap diterima dari GCS, node ini WAJIB langsung
  balas 4 byte memakai cache tadi - TANPA nunggu Core Node proses dulu.
  Ini supaya siklus request-response ~20Hz (GCS) gak macet nunggu logic.
"""

import struct
import threading

import serial
import rclpy
from rclpy.node import Node

from ugv_robot_msgs.msg import GcsCommand, GcsStatus

# "=" artinya: standard size, no byte-alignment padding (byte per byte apa adanya)
# B = uint8 (0..255), b = int8 (-128..127)
FORMAT_REQUEST = "=BBbbbbbBBBBbbBbB"   # 16 byte dari GCS
FORMAT_RESPONSE = "=BBBB"             # 4 byte balasan ke GCS

SIZE_REQUEST = struct.calcsize(FORMAT_REQUEST)    # harus = 16
SIZE_RESPONSE = struct.calcsize(FORMAT_RESPONSE)  # harus = 4


class GcsInterfaceNode(Node):
    def __init__(self):
        super().__init__('gcs_interface_node')

        # --- Parameter: bisa diganti tanpa edit kode, misal:
        #     ros2 run ugv_robot gcs_interface_node --ros-args -p serial_port:=/dev/ttyUSB1
        self.declare_parameter('serial_port', '/dev/ttyUSB0')  # dummy dulu
        self.declare_parameter('baudrate', 57600)

        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baudrate').value

        # --- Publisher: command mentah dari GCS diterusin ke Core Node ---
        self.pub_command = self.create_publisher(GcsCommand, '/gcs/command_mentah', 10)

        # --- Subscriber: status dari Core Node, buat di-cache ---
        self.sub_status = self.create_subscription(
            GcsStatus, '/gcs/status_balik', self._callback_status, 10)

        # --- Cache balasan 5-byte. Diproteksi lock krn diakses dari 2 thread
        #     beda (thread ROS2 nulis lewat callback, thread serial baca). ---
        self._lock = threading.Lock()
        self._cache_response = struct.pack(FORMAT_RESPONSE, 0, 0, 0, 0)  # default aman

        # --- Buka koneksi serial ke radio RF ---
        try:
            self.serial_conn = serial.Serial(port, baud, timeout=1)
            self.get_logger().info(f'Serial terbuka di {port} @ {baud} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Gagal buka serial {port}: {e}')
            raise

        # --- Thread terpisah khusus baca serial. WAJIB terpisah dari thread
        #     utama ROS2 (yang jalanin rclpy.spin()), karena baca serial itu
        #     BLOCKING (nunggu byte datang). Kalau ditaruh 1 thread yang sama
        #     dengan spin(), subscriber /gcs/status_balik jadi ikut nge-block. ---
        self._stop_thread = False
        self.reader_thread = threading.Thread(target=self._loop_baca_serial, daemon=True)
        self.reader_thread.start()

    # ------------------------------------------------------------------
    # Dipanggil otomatis oleh rclpy tiap Core Node publish ke /gcs/status_balik
    # ------------------------------------------------------------------
    def _callback_status(self, msg: GcsStatus):
        with self._lock:
            self._cache_response = struct.pack(
                FORMAT_RESPONSE,
                msg.stm32_status,
                msg.lrf_status,
                msg.lrf_jarak_lsb,
                msg.lrf_jarak_msb,
                
            )
        # CATATAN: fungsi ini SENGAJA cuma nyimpen data, gak manggil serial
        # write apapun. Kirim balik ke GCS cuma kejadian pas frame baru
        # datang (lihat _proses_frame_masuk), bukan pas status berubah.

    # ------------------------------------------------------------------
    # Loop tak-berhenti di thread terpisah: kumpulin byte sampai 16 byte
    # penuh, baru diproses. Pendekatan ini disebut "buffering".
    # ------------------------------------------------------------------
    def _loop_baca_serial(self):
        buffer = bytearray()
        while not self._stop_thread:
            byte_baru = self.serial_conn.read(1)  # blocking max 1 detik (timeout=1)
            if not byte_baru:
                continue  # timeout, belum ada data masuk, ulangi nunggu

            buffer += byte_baru

            if len(buffer) < SIZE_REQUEST:
                continue  # masih kurang dari 16 byte, lanjut kumpulin

            frame = bytes(buffer[:SIZE_REQUEST])
            buffer = buffer[SIZE_REQUEST:]  # sisa byte (kalau ada) disimpan buat siklus berikutnya
            self._proses_frame_masuk(frame)

    # ------------------------------------------------------------------
    # Frame 16 byte lengkap sudah ada -> ubah jadi ROS2 message -> publish
    # -> LALU langsung balas 5 byte dari cache.
    # ------------------------------------------------------------------
    def _proses_frame_masuk(self, frame: bytes):
        try:
            fields = struct.unpack(FORMAT_REQUEST, frame)
        except struct.error as e:
            self.get_logger().warn(f'Frame korup, dibuang: {e}')
            return

        msg = GcsCommand()
        (msg.estop, msg.mode, msg.x_joystick1, msg.y_joystick1,
         msg.x_joystick2, msg.y_joystick2, msg.zoom, msg.lrf,
         msg.f_lamp, msg.b_lamp, msg.slip_ring, msg.body_up_down,
         msg.arm_widen_narrow, msg.motor_individual_id,
         msg.motor_individual_arah, msg.kalibrasi) = fields

        self.pub_command.publish(msg)

        with self._lock:
            response_bytes = self._cache_response
        self.serial_conn.write(response_bytes)

    # ------------------------------------------------------------------
    # Dipanggil otomatis pas node di-shutdown (Ctrl+C dll), biar thread
    # dan koneksi serial ditutup rapi, gak nyisa proses nyangkut.
    # ------------------------------------------------------------------
    def destroy_node(self):
        self._stop_thread = True
        if self.reader_thread.is_alive():
            self.reader_thread.join(timeout=2)
        if hasattr(self, 'serial_conn'):
            self.serial_conn.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = GcsInterfaceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
