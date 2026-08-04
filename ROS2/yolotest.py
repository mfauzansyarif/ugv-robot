"""
Deteksi objek real-time pakai YOLOv8n (TensorRT) dari kamera RTSP Sony FCB-EV7520.

Alur:
  1. Buka stream kamera via GStreamer (OpenCV)
  2. Load TensorRT engine (yolov8n.engine)
  3. Loop: ambil frame -> preprocess -> inference -> postprocess (NMS)
     -> gambar kotak -> tampilkan

Requirement (semua udah terpasang): tensorrt, pycuda, opencv (GStreamer), numpy
"""

import threading

import cv2
import numpy as np
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit  # noqa: F401 - otomatis init CUDA context, JANGAN dihapus

ENGINE_PATH = "/home/respatijetson/yolov8n.engine"
RTSP_URL = "rtsp://admin:123456@192.168.0.123:554/h264/ch1/sub/av_stream"
INPUT_SIZE = 416          # HARUS SAMA PERSIS kayak imgsz pas export ONNX kemarin
CONF_THRESHOLD = 0.5
NMS_THRESHOLD = 0.45

# Nama kelas COCO, urutan HARUS sama persis kayak training YOLOv8 (jangan diubah)
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush",
]


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
        # input_data harus udah preprocessed: shape (1,3,H,W), float32
        np.copyto(self.inputs[0]["host"], input_data.ravel())
        cuda.memcpy_htod_async(self.inputs[0]["device"], self.inputs[0]["host"], self.stream)
        self.context.execute_async_v2(bindings=self.bindings, stream_handle=self.stream.handle)
        cuda.memcpy_dtoh_async(self.outputs[0]["host"], self.outputs[0]["device"], self.stream)
        self.stream.synchronize()
        return self.outputs[0]["host"].reshape(self.outputs[0]["shape"])


def preprocess(frame, size):
    """Resize + normalisasi + ubah urutan channel, sesuai format input model."""
    img = cv2.resize(frame, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = img.transpose(2, 0, 1)          # HWC -> CHW
    img = np.expand_dims(img, axis=0)     # tambah dimensi batch
    return np.ascontiguousarray(img)


def nms_manual(boxes, scores, iou_threshold):
    """NMS manual pakai numpy - pengganti cv2.dnn.NMSBoxes yang gak ada di
    OpenCV versi lama (3.2.0, dari apt Ubuntu 18.04, gak include modul dnn)."""
    boxes = np.array(boxes, dtype=np.float32)  # format: x, y, w, h
    scores = np.array(scores, dtype=np.float32)

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 0] + boxes[:, 2]
    y2 = boxes[:, 1] + boxes[:, 3]
    areas = boxes[:, 2] * boxes[:, 3]

    order = scores.argsort()[::-1]  # urut dari confidence tertinggi
    keep = []

    while order.size > 0:
        i = order[0]
        keep.append(i)

        # Hitung overlap kotak ke-i dengan SISA kotak lain yang masih tersisa
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)

        # Buang kotak yang overlap-nya terlalu tinggi (dianggap "kotak sama")
        sisa = np.where(iou <= iou_threshold)[0]
        order = order[sisa + 1]

    return keep


def postprocess(output, frame_w, frame_h, input_size):
    """Output YOLOv8 mentah -> filter confidence -> NMS -> kotak siap gambar.
    Full vectorized pakai numpy - JANGAN pakai `for` loop Python manual di
    sini, soalnya jumlah kandidat kotak per frame bisa ribuan (~3549 buat
    input 416x416), dan loop Python murni buat itu LAMBAT BANGET di CPU
    Jetson Nano - bikin frame RTSP numpuk gak sempet diproses, ujungnya
    kamera nge-drop koneksi karena dianggap client-nya gak responsif."""
    predictions = output[0].T  # (num_anchor, 84)

    class_scores = predictions[:, 4:]          # (num_anchor, 80)
    class_ids = np.argmax(class_scores, axis=1)  # (num_anchor,) - vectorized
    confidences = class_scores[np.arange(len(class_scores)), class_ids]

    mask = confidences >= CONF_THRESHOLD
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

    indices = nms_manual(boxes, confidences, NMS_THRESHOLD)
    hasil = [(boxes[i], confidences[i], class_ids[i]) for i in indices]
    return hasil


def gambar_deteksi(frame, hasil):
    for (x, y, w, h), score, class_id in hasil:
        x, y, w, h = int(x), int(y), int(w), int(h)
        label = f"{COCO_CLASSES[class_id]} {score:.2f}"
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, label, (x, max(y - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return frame


class KameraStream:
    """Baca frame di THREAD TERPISAH, terus-menerus secepat kamera ngirim.
    Loop utama (inference) tinggal ambil frame TERAKHIR yang tersimpan,
    kapanpun dia siap - kalau ada frame yang "kelewat" pas inference masih
    sibuk, itu otomatis di-skip (di-timpa frame baru), bukan diproses semua
    berurutan. Ini yang bikin RTSP session tetap "sehat" (kamera terus
    ngerasa direspons), walau inference-nya sendiri lebih lambat dari FPS
    kamera aslinya."""

    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.frame = None
        self.lock = threading.Lock()
        self.stopped = False
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame

    def read(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def isOpened(self):
        return self.cap.isOpened()

    def stop(self):
        self.stopped = True
        self.thread.join(timeout=1)
        self.cap.release()


def main():
    print("Loading TensorRT engine...")
    model = YoloTRT(ENGINE_PATH)

    print("Membuka stream kamera...")
    kamera = KameraStream(RTSP_URL)
    if not kamera.isOpened():
        print("Gagal buka stream kamera")
        return

    while True:
        frame = kamera.read()
        if frame is None:
            continue  # thread baca belum sempat dapat frame pertama, tunggu

        frame_h, frame_w = frame.shape[:2]
        input_data = preprocess(frame, INPUT_SIZE)
        output = model.infer(input_data)
        hasil = postprocess(output, frame_w, frame_h, INPUT_SIZE)
        frame = gambar_deteksi(frame, hasil)

        cv2.imshow("Deteksi Objek - Kamera FCB", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    kamera.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()