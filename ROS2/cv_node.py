"""CV Node - baca kamera RTSP + jalanin YOLO (TensorRT) + publish deteksi
'person' PALING CONFIDENT ke topic /vision/deteksi. Node ini CUMA persepsi
mentah (dumb perception) - gak mutusin apa-apa soal gerak robot, itu
kerjaan Core Node (subscribe PersonDetection, keputusan follow/lock ada
di situ) - prinsip yang sama kayak kenapa STM32 Interface Node juga gak
boleh mikir.

Basis kode: yolotest.py (udah tested manual, jalan lancar & smooth) -
dibungkus jadi node ROS2, loop `while True` + cv2.imshow diganti timer
callback biar terintegrasi sama rclpy event loop (gak ada window GUI lagi,
node ini jalan headless).
"""

import threading
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit  # noqa: F401 - otomatis init CUDA context, JANGAN dihapus

from ugv_robot_msgs.msg import PersonDetection, GcsRelay

PERSON_CLASS_ID = 0  # index "person" di COCO_CLASSES, urutan training YOLOv8


class YoloTRT:
    """Bungkus load engine TensorRT + alokasi buffer GPU/CPU + jalanin inference."""

    def __init__(self, engine_path):
        logger = trt.Logger(trt.Logger.WARNING)
        with open(engine_path, "rb") as f, trt.Runtime(logger) as runtime:
            self.engine = runtime.deserialize_cuda_engine(f.read())
        self.context = self.engine.create_execution_context()

        self.inputs, self.outputs, self.bindings = [], [], []
        self.stream = cuda.Stream()

        for binding in self.engine:
            shape = self.engine.get_binding_shape(binding)
            size = trt.volume(shape)
            dtype = trt.nptype(self.engine.get_binding_dtype(binding))

            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            self.bindings.append(int(device_mem))

            if self.engine.binding_is_input(binding):
                self.inputs.append({"host": host_mem, "device": device_mem, "shape": shape})
            else:
                self.outputs.append({"host": host_mem, "device": device_mem, "shape": shape})

    def infer(self, input_data):
        np.copyto(self.inputs[0]["host"], input_data.ravel())
        cuda.memcpy_htod_async(self.inputs[0]["device"], self.inputs[0]["host"], self.stream)
        self.context.execute_async_v2(bindings=self.bindings, stream_handle=self.stream.handle)
        cuda.memcpy_dtoh_async(self.outputs[0]["host"], self.outputs[0]["device"], self.stream)
        self.stream.synchronize()
        return self.outputs[0]["host"].reshape(self.outputs[0]["shape"])


def preprocess(frame, size):
    img = cv2.resize(frame, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = img.transpose(2, 0, 1)
    img = np.expand_dims(img, axis=0)
    return np.ascontiguousarray(img)


def nms_manual(boxes, scores, iou_threshold):
    """NMS manual pakai numpy - pengganti cv2.dnn.NMSBoxes yang gak ada di
    OpenCV versi lama (3.2.0, dari apt Ubuntu 18.04, gak include modul dnn)."""
    boxes = np.array(boxes, dtype=np.float32)
    scores = np.array(scores, dtype=np.float32)

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 0] + boxes[:, 2]
    y2 = boxes[:, 1] + boxes[:, 3]
    areas = boxes[:, 2] * boxes[:, 3]

    order = scores.argsort()[::-1]
    keep = []

    while order.size > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)

        sisa = np.where(iou <= iou_threshold)[0]
        order = order[sisa + 1]

    return keep


def postprocess(output, frame_w, frame_h, input_size, conf_threshold, nms_threshold):
    """Output YOLOv8 mentah -> filter confidence -> NMS -> kotak siap pakai.
    Full vectorized numpy - JANGAN pakai `for` loop Python manual di sini
    (~3549 kandidat kotak buat input 416x416, bikin CPU Jetson Nano
    keteteran & frame RTSP numpuk gak sempet diproses)."""
    predictions = output[0].T

    class_scores = predictions[:, 4:]
    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(len(class_scores)), class_ids]

    mask = confidences >= conf_threshold
    if not np.any(mask):
        return []

    filtered = predictions[mask]
    class_ids = class_ids[mask]
    confidences = confidences[mask]

    cx, cy, w, h = filtered[:, 0], filtered[:, 1], filtered[:, 2], filtered[:, 3]
    x1 = (cx - w / 2) / input_size * frame_w
    y1 = (cy - h / 2) / input_size * frame_h
    box_w = w / input_size * frame_w
    box_h = h / input_size * frame_h
    boxes = np.stack([x1, y1, box_w, box_h], axis=1)

    indices = nms_manual(boxes, confidences, nms_threshold)
    return [(boxes[i], confidences[i], class_ids[i]) for i in indices]


class KameraStream:
    """Baca frame di thread terpisah, main loop selalu ambil frame TERAKHIR
    (frame yang kelewat pas inference sibuk otomatis di-skip) - biar RTSP
    session tetap sehat walau inference lebih lambat dari FPS kamera asli.

    Auto-reconnect kalau baca gagal berturut-turut - kamera bisa BENERAN
    padam total (misal slip ring dimatiin operator), bukan cuma glitch RF
    sesaat, jadi harus nyoba connect ulang terus-menerus (dengan jeda,
    biar gak spam), BUKAN diam macet nunggu restart manual node."""

    GAGAL_BERTURUT_MAKS = 20  # ~2 detik @ ~10Hz baca sebelum declare putus
    JEDA_RECONNECT_S = 3.0    # jeda antar percobaan reconnect

    def __init__(self, url, log_fn=print):
        self.url = url
        self.log_fn = log_fn
        self.cap = cv2.VideoCapture(url)
        self.frame = None
        self.lock = threading.Lock()
        self.stopped = False
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        gagal_berturut = 0
        while not self.stopped:
            ret, frame = self.cap.read()
            if ret:
                gagal_berturut = 0
                with self.lock:
                    self.frame = frame
                continue

            gagal_berturut += 1
            if gagal_berturut >= self.GAGAL_BERTURUT_MAKS:
                self.log_fn(f'Kamera putus ({gagal_berturut} gagal baca berturut) - '
                            f'coba reconnect tiap {self.JEDA_RECONNECT_S}s...')
                with self.lock:
                    self.frame = None  # buang frame lama, jangan diproses seolah masih fresh
                self.cap.release()
                time.sleep(self.JEDA_RECONNECT_S)
                self.cap = cv2.VideoCapture(self.url)
                gagal_berturut = 0

    def read(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def isOpened(self):
        return self.cap.isOpened()

    def stop(self):
        self.stopped = True
        self.thread.join(timeout=1)
        self.cap.release()


class CvNode(Node):
    def __init__(self):
        super().__init__('cv_node')

        self.declare_parameter('engine_path', '/home/respatijetson/yolov8n.engine')
        self.declare_parameter(
            'rtsp_url', 'rtsp://admin:123456@192.168.0.123:554/h264/ch1/sub/av_stream')
        self.declare_parameter('input_size', 416)
        self.declare_parameter('conf_threshold', 0.5)
        self.declare_parameter('nms_threshold', 0.45)

        self.input_size = self.get_parameter('input_size').value
        self.conf_threshold = self.get_parameter('conf_threshold').value
        self.nms_threshold = self.get_parameter('nms_threshold').value

        self.get_logger().info('Loading TensorRT engine...')
        self.model = YoloTRT(self.get_parameter('engine_path').value)

        self.get_logger().info('Membuka stream kamera...')
        self.kamera = KameraStream(
            self.get_parameter('rtsp_url').value, log_fn=self.get_logger().warn)
        if not self.kamera.isOpened():
            self.get_logger().error('Gagal buka stream kamera')

        # Default aman: manual (0), slip ring dianggap OFF - gak jalanin
        # inference sampai beneran ada frame /stm32/gcs_relay masuk yang
        # bilang mode=1 (auto) DAN slip_ring=1 (kamera beneran dapet daya -
        # slip ring mati = kamera padam total secara fisik, gak ada
        # gunanya nyoba baca frame).
        self._mode = 0
        self._slip_ring = 0
        self.create_subscription(GcsRelay, '/stm32/gcs_relay', self._callback_relay, 10)

        self.pub_deteksi = self.create_publisher(PersonDetection, '/vision/deteksi', 10)

        # 10Hz itu TARGET MINIMAL jeda ANTAR SIKLUS (bukan target rate
        # kaku) - self._siklus_deteksi_wrapper() manggil timer.reset() di
        # UJUNG, SETELAH inference kelar, bukan pakai timer periodik biasa.
        # Kalau pakai create_timer biasa DOANG, dan 1 siklus inference di
        # Jetson Nano ternyata lebih lambat dari 100ms, ROS2 bakal manggil
        # siklus berikutnya LANGSUNG begitu yang sekarang kelar (gak ada
        # jeda sama sekali) - numpuk beruntun tanpa henti, node jadi gak
        # sempet proses topic lain (mode/slip_ring), keliatan kayak freeze.
        self.interval_siklus_s = 0.1
        self.timer = self.create_timer(self.interval_siklus_s, self._siklus_wrapper)

    def _callback_relay(self, msg: GcsRelay):
        self._mode = msg.mode
        self._slip_ring = msg.slip_ring

    def _siklus_wrapper(self):
        mulai = time.monotonic()
        self._siklus_deteksi()
        durasi_ms = (time.monotonic() - mulai) * 1000
        if durasi_ms > self.interval_siklus_s * 1000:
            self.get_logger().warn(
                f'Siklus deteksi {durasi_ms:.0f}ms - lebih lambat dari target '
                f'{self.interval_siklus_s * 1000:.0f}ms (Jetson kewalahan/GPU throttle?)')
        self.timer.reset()  # jadwalin siklus berikutnya SEJAK SEKARANG, bukan sejak start

    def _siklus_deteksi(self):
        if self._mode != 1 or self._slip_ring != 1:
            # Manual, ATAU auto tapi slip ring mati (kamera gak dapet daya
            # sama sekali) - kamera TETAP nyoba reconnect di background
            # (biar begitu slip ring nyala lagi langsung pulih sendiri),
            # tapi inference (bagian BERAT di GPU) di-skip total. Tetap
            # publish "gak terdeteksi" tiap siklus biar cache di Core Node
            # gak nyangkut ke deteksi LAMA dari sebelum kondisi ini.
            msg = PersonDetection()
            msg.terdeteksi = False
            self.pub_deteksi.publish(msg)
            return

        frame = self.kamera.read()
        if frame is None:
            # Mode+slip ring udah bener tapi kamera lagi gak ke-reach
            # (misal baru aja putus, belum sempet reconnect) - tetap
            # publish False, jangan diem doang, biar cache Core Node gak
            # nyangkut ke deteksi lama.
            msg = PersonDetection()
            msg.terdeteksi = False
            self.pub_deteksi.publish(msg)
            return

        frame_h, frame_w = frame.shape[:2]
        input_data = preprocess(frame, self.input_size)
        output = self.model.infer(input_data)
        hasil = postprocess(output, frame_w, frame_h, self.input_size,
                             self.conf_threshold, self.nms_threshold)

        # Filter cuma class "person", ambil confidence PALING TINGGI -
        # placeholder buat 1 orang. Kalau lagi ada BEBERAPA orang dan perlu
        # "lock" konsisten ke 1 spesifik antar-frame, itu logic tambahan
        # yang nyusul di Core Node - BUKAN di sini (lihat docstring atas).
        orang = [h for h in hasil if h[2] == PERSON_CLASS_ID]

        msg = PersonDetection()
        if not orang:
            msg.terdeteksi = False
            self.pub_deteksi.publish(msg)
            return

        (x, y, w, h), confidence, _ = max(orang, key=lambda o: o[1])
        cx = x + w / 2
        cy = y + h / 2

        msg.terdeteksi = True
        # -100..100, 0=tengah. Kanan=+X, Atas=+Y (dibalik dari koordinat
        # gambar yang Y-nya makin gede makin ke bawah) - samain konvensi
        # kayak xJoy2/yJoy2 dari GCS.
        msg.pusat_x = float((cx / frame_w) * 200 - 100)
        msg.pusat_y = float(100 - (cy / frame_h) * 200)
        msg.lebar = float((w / frame_w) * 100)
        msg.tinggi = float((h / frame_h) * 100)
        msg.confidence = float(confidence)
        self.pub_deteksi.publish(msg)

    def destroy_node(self):
        self.kamera.stop()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CvNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
