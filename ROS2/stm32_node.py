import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import serial


class Stm32Node(Node):
    """
    Driver ke STM32 (motor AC + 12 motor linear + lampu).
    TIDAK ada logic keputusan di sini - node ini cuma translator:
    terima 8 angka dari topic /cmd_vehicle, format jadi command,
    kirim ke STM32. Semua logic (mapping joystick, mode, interlock
    keselamatan) ada di vehicle_control_node (belum dibuat).

    Field urutan (harus selalu 8 angka, sesuai urutan ini):
        speed  -100..100   (kontinu)  4 motor AC, + = maju, - = mundur
        steer  -1/0/1       (diskrit)  motor linear steering
        fbody  -1/0/1       (diskrit)  motor linear body depan
        bbody  -1/0/1       (diskrit)  motor linear body belakang
        rarm   -1/0/1       (diskrit)  motor linear arm kanan
        larm   -1/0/1       (diskrit)  motor linear arm kiri
        flamp  0..100       (unsigned) brightness lampu depan (PWM)
        blamp  0/1/2        (unsigned) lampu belakang: mati/steady/kedip

    HEARTBEAT (penting buat safety):
    Node ini kirim command TERUS-MENERUS ke STM32 di frekuensi tetap
    (default 20Hz), bukan cuma pas ada pesan baru masuk ke /cmd_vehicle -
    pola yang sama kayak test_ac_motors_stm32.py yang udah terbukti jalan.
    Alasannya: kalau vehicle_control_node crash / RF putus / topic
    berhenti publish, stm32_node TETAP kirim state terakhir yang dia
    punya tiap 50ms. Ini yang bikin firmware STM32 nanti BISA pasang
    watchdog (kalau >300ms gak ada baris valid masuk -> auto-stop motor) -
    tanpa heartbeat ini, STM32 gak akan pernah tahu koneksi putus.
    cmd_callback() CUMA nyimpen command terbaru ke self.last_command;
    yang beneran ngirim ke serial adalah _heartbeat_tick() yang dipanggil
    timer, terpisah total dari kapan pesan ROS2 datang.

    Struktur dipisah 2 lapis transport, karena masih bisa ganti
    UART sekarang -> I2C/SPI nanti di Jetson:
        _pack_command() : angka Python -> bytes yang mau dikirim
        _send()          : bytes -> beneran dikirim ke hardware
    """

    FIELD_COUNT = 8
    # Command default kalau belum pernah terima apa-apa dari /cmd_vehicle
    # sama sekali - semua diam/aman (bukan sembarang angka).
    SAFE_COMMAND = [0.0] * FIELD_COUNT

    def __init__(self):
        super().__init__('stm32_node')

        # Semua path/config jadi parameter - JANGAN di-hardcode
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 57600)
        self.declare_parameter('serial_timeout', 0.1)
        self.declare_parameter('heartbeat_hz', 20.0)

        port = self.get_parameter('serial_port').get_parameter_value().string_value
        baud = self.get_parameter('baudrate').get_parameter_value().integer_value
        timeout = self.get_parameter('serial_timeout').get_parameter_value().double_value
        heartbeat_hz = self.get_parameter('heartbeat_hz').get_parameter_value().double_value

        self.ser = None
        try:
            self.ser = serial.Serial(port, baud, timeout=timeout)
            self.get_logger().info(f'Serial terbuka di {port} @ {baud} baud')
        except serial.SerialException as e:
            # Sengaja gak crash node-nya - biar bisa tetap dites logic-nya
            # (packing command, subscribe topic) walau STM32/kabel belum
            # terpasang. Bakal keliatan jelas di log kalau serial gagal.
            self.get_logger().error(f'Gagal buka serial {port}: {e}')

        # State command terakhir yang diterima - inilah yang dikirim
        # berulang-ulang oleh heartbeat, bukan cmd_callback yang kirim
        # langsung.
        self.last_command = list(self.SAFE_COMMAND)

        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/cmd_vehicle',
            self.cmd_callback,
            10
        )

        heartbeat_period = 1.0 / heartbeat_hz
        self.heartbeat_timer = self.create_timer(heartbeat_period, self._heartbeat_tick)

        self.get_logger().info(
            f'stm32_node siap, heartbeat {heartbeat_hz:.0f}Hz, nunggu /cmd_vehicle...'
        )

    # ------------------------------------------------------------------
    # Layer 1: packing - angka Python -> bytes
    # UART sekarang: ASCII, dipisah spasi, diakhiri newline.
    # Nanti kalau pindah I2C/SPI, ganti isi fungsi ini jadi struct.pack
    # (misal '<bbbbbbBB' - signed byte x6 + unsigned byte x2), TANPA
    # perlu ubah cmd_callback/_heartbeat_tick atau bagian lain node ini.
    # ------------------------------------------------------------------
    def _pack_command(self, data) -> bytes:
        speed, steer, fbody, bbody, rarm, larm, flamp, blamp = data
        line = (
            f'{int(speed)} {int(steer)} {int(fbody)} {int(bbody)} '
            f'{int(rarm)} {int(larm)} {int(flamp)} {int(blamp)}\n'
        )
        return line.encode('ascii')

    # ------------------------------------------------------------------
    # Layer 2: transport - bytes -> beneran dikirim ke hardware
    # UART sekarang: ser.write(). Nanti I2C: bus.write_i2c_block_data(),
    # atau SPI: spi.xfer2(). Ganti isi fungsi ini + __init__ (buka
    # bus I2C/SPI bukan buka serial port), sisanya gak perlu disentuh.
    # ------------------------------------------------------------------
    def _send(self, payload: bytes) -> bool:
        if self.ser is None or not self.ser.is_open:
            return False
        try:
            self.ser.write(payload)
            return True
        except serial.SerialException as e:
            self.get_logger().error(f'Gagal kirim ke serial: {e}')
            return False

    def cmd_callback(self, msg: Float32MultiArray):
        """CUMA nyimpen command terbaru. TIDAK kirim ke serial langsung -
        itu tugas _heartbeat_tick(). Ini yang bikin heartbeat tetap jalan
        stabil di frekuensi tetap walaupun /cmd_vehicle di-publish gak
        beraturan (kadang cepat, kadang telat, dsb)."""
        data = msg.data

        if len(data) != self.FIELD_COUNT:
            self.get_logger().warn(
                f'/cmd_vehicle harus {self.FIELD_COUNT} elemen, '
                f'diterima {len(data)}. Diabaikan (command lama tetap dipakai).'
            )
            return

        self.last_command = list(data)

    def _heartbeat_tick(self):
        """Dipanggil timer di frekuensi tetap (default 20Hz). Selalu kirim
        self.last_command apa adanya - kalau belum pernah ada pesan masuk
        sama sekali, itu masih SAFE_COMMAND (semua nol/diam)."""
        payload = self._pack_command(self.last_command)
        self.get_logger().info(f'-> STM32: {payload!r}')
        self._send(payload)

    def destroy_node(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Stm32Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()