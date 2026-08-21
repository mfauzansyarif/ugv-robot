"""Buka kamera RTSP dengan cara PERSIS SAMA kayak yang dipakai Jetson (dulu
di node ROS2 "cv_node.py" - nama node dari struktur PRA-REFACTOR yang udah
gak ada di repo, node aktif sekarang core_node.py + stm32_interface_node.py)
- buat dijalanin di laptop Windows biar bisa dibandingin visual sama
tampilan video di GCS app (jalur RF analog TS832/RC832).

BUKAN buat CV/deteksi - ini murni cek gambar mentah dari kamera doang,
gak ada YOLO/TensorRT sama sekali (gak perlu library itu di laptop ini).

Requirement: pip install opencv-python
"""

import threading
import time

import cv2

RTSP_URL = "rtsp://admin:123456@192.168.0.123:554/h264/ch1/sub/av_stream"


class KameraStream:
    """SAMA PERSIS kayak class KameraStream yang dulu ada di node cv_node.py
    (nama node lama, lihat catatan di atas) - baca frame di thread terpisah,
    auto-reconnect kalau baca gagal berturut-turut."""

    GAGAL_BERTURUT_MAKS = 20
    JEDA_RECONNECT_S = 3.0

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
                    self.frame = None
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


def main():
    print("Membuka stream kamera...")
    kamera = KameraStream(RTSP_URL)
    if not kamera.isOpened():
        print("Gagal buka stream kamera")
        return

    print("\nNampilin video. Klik jendelanya lalu tekan 'q' buat keluar.\n")

    # WINDOW_AUTOSIZE - kunci window SELALU pas ukuran asli frame, gak
    # bisa di-drag-resize/stretch manual (biar perbandingan visual sama
    # test_video_capture.py adil, dua-duanya native size).
    nama_window = "Kamera RTSP (jalur yang sama kayak Jetson)"
    cv2.namedWindow(nama_window, cv2.WINDOW_AUTOSIZE)

    while True:
        frame = kamera.read()
        if frame is None:
            continue  # belum ada frame pertama, atau lagi reconnect
        print(f"Resolusi native frame: {frame.shape[1]}x{frame.shape[0]}", end="\r")
        cv2.imshow(nama_window, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    kamera.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
