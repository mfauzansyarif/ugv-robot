"""
STM32 Interface Node
=====================
Tugas node ini CUMA translator byte <-> topic ROS2, PERSIS prinsip yang sama
kayak GCS Interface (lihat ROS2_BRIEF.md bagian "Prinsip") - GAK ADA
logic/keputusan di sini, semua itu tugas Core Node.

Transport: I2C (STM32 jadi I2C SLAVE, Jetson jadi MASTER) - dipilih setelah
SPI gagal dipakai gara-gara masalah pinmux di Jetson Nano yang gak
kunjung selesai. Field command SAMA PERSIS kayak versi SPI/UART sebelumnya
(cuma beda transport).

Alur singkat:
  Core Node --15 field--> /stm32/command --> di-CACHE (bukan langsung dikirim)
  Tiap 50ms (20Hz, TERUS-MENERUS terlepas dari kapan /stm32/command
  di-publish):
    1. Kirim command yang lagi di-cache ke STM32 lewat I2C (WRITE 15 byte)
    2. Baca balasan 15 byte dari STM32 (READ, repeated-start di transaksi
       I2C yang sama - lihat i2c_rdwr di _heartbeat_tick)
    3. Publish status yang didapat ke /stm32/status

  Kenapa heartbeat terus-menerus (bukan cuma pas ada command baru masuk):
  kalau Core Node crash / topic /stm32/command berhenti publish, node ini
  TETAP kirim command terakhir yang dia punya tiap 50ms - ini yang bikin
  watchdog di firmware STM32 (CekWatchdog(), 300ms) bisa kerja bener (STM32
  cuma tau "koneksi putus" kalau BENERAN berhenti terima byte valid, bukan
  kalau Core Node-nya yang lagi diem doang). Pola sama kayak stm32_node.py
  versi lama (heartbeat 20Hz) dan gcs_interface_node.py (cache + lock).

  CATATAN soal I2C (beda dari SPI): I2C gak bisa kirim+terima BARENGAN
  kayak SPI full-duplex - WAJIB 2 fase terpisah (WRITE dulu, BARU READ).
  Balasan yang didapat di fase READ itu status dari SIKLUS SEBELUMNYA
  (STM32 nyiapin balasannya sebelum tau isi command yang baru aja ditulis
  di WRITE yang SAMA) - batasan yang sama kayak yang didesain buat versi
  SPI dulu, cuma alasannya beda (di I2C ini soal urutan write-lalu-read,
  bukan soal "slave gak bisa mikir di tengah transaksi" kayak SPI).
"""

import struct
import threading

import rclpy
from rclpy.node import Node
from smbus2 import SMBus, i2c_msg

from ugv_robot_msgs.msg import Stm32Command, Stm32Status

JUMLAH_ACTUATOR = 12
FRAME_LEN = 1 + JUMLAH_ACTUATOR + 2  # speed + 12 actuator + flamp + blamp = 15 byte

FORMAT_COMMAND = "=b" + "b" * JUMLAH_ACTUATOR + "BB"  # 15 byte ke STM32
SIZE_COMMAND = struct.calcsize(FORMAT_COMMAND)


class Stm32InterfaceNode(Node):
    def __init__(self):
        super().__init__('stm32_interface_node')

        # --- Parameter: bisa diganti tanpa edit kode, misal:
        #     ros2 run ugv_robot stm32_interface_node --ros-args -p i2c_addr:=0x11
        self.declare_parameter('i2c_bus', 1)
        self.declare_parameter('i2c_addr', 0x10)
        self.declare_parameter('heartbeat_hz', 20.0)

        bus_num = self.get_parameter('i2c_bus').value
        self.i2c_addr = self.get_parameter('i2c_addr').value
        heartbeat_hz = self.get_parameter('heartbeat_hz').value

        # --- Cache command 15-byte terakhir, default AMAN (diam semua)
        #     kalau belum pernah ada command masuk sama sekali. Diproteksi
        #     lock krn diakses dari 2 thread beda (thread ROS2 lewat
        #     callback, thread timer heartbeat). ---
        self._lock = threading.Lock()
        self._cache_command = bytes(FRAME_LEN)  # 15 byte nol semua

        # --- Subscriber: command final dari Core Node, CUMA di-cache ---
        self.sub_command = self.create_subscription(
            Stm32Command, '/stm32/command', self._callback_command, 10)

        # --- Publisher: status dari STM32, diterusin ke Core Node ---
        self.pub_status = self.create_publisher(Stm32Status, '/stm32/status', 10)

        # --- Buka bus I2C ke STM32 ---
        try:
            self.bus = SMBus(bus_num)
            self.get_logger().info(f'I2C terbuka di /dev/i2c-{bus_num}, addr=0x{self.i2c_addr:02X}')
        except FileNotFoundError as e:
            self.get_logger().error(f'Gagal buka I2C bus {bus_num}: {e}')
            raise

        # --- Timer heartbeat, jalan TERUS-MENERUS terlepas dari kapan
        #     /stm32/command di-publish (lihat penjelasan di docstring atas). ---
        heartbeat_period = 1.0 / heartbeat_hz
        self.heartbeat_timer = self.create_timer(heartbeat_period, self._heartbeat_tick)

        self.get_logger().info(f'stm32_interface_node siap, heartbeat {heartbeat_hz:.0f}Hz')

    # ------------------------------------------------------------------
    # Dipanggil otomatis oleh rclpy tiap Core Node publish ke /stm32/command.
    # CUMA nyimpen ke cache - yang beneran kirim ke I2C itu _heartbeat_tick().
    # ------------------------------------------------------------------
    def _callback_command(self, msg: Stm32Command):
        if len(msg.actuator) != JUMLAH_ACTUATOR:
            self.get_logger().warn(
                f'/stm32/command field actuator harus {JUMLAH_ACTUATOR} elemen, '
                f'diterima {len(msg.actuator)}. Diabaikan (command lama tetap dipakai).'
            )
            return

        frame = struct.pack(FORMAT_COMMAND, msg.speed, *msg.actuator, msg.f_lamp, msg.b_lamp)
        with self._lock:
            self._cache_command = frame

    # ------------------------------------------------------------------
    # Dipanggil timer di frekuensi tetap (default 20Hz). Kirim command yang
    # lagi di-cache lewat I2C (WRITE), baca balasan STM32 (READ), publish.
    # ------------------------------------------------------------------
    def _heartbeat_tick(self):
        with self._lock:
            frame = self._cache_command

        try:
            tulis = i2c_msg.write(self.i2c_addr, frame)
            baca = i2c_msg.read(self.i2c_addr, FRAME_LEN)
            self.bus.i2c_rdwr(tulis, baca)
        except OSError as e:
            self.get_logger().warn(f'I2C ke STM32 gagal: {e}')
            return

        balasan = bytes(baca)

        msg = Stm32Status()
        msg.status = balasan[0]
        self.pub_status.publish(msg)

    def destroy_node(self):
        if hasattr(self, 'bus'):
            self.bus.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Stm32InterfaceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
