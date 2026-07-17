"""Widget Camera Viewer - nampilin video feed dari receiver RF video (lewat
capture card, muncul sebagai video device biasa ke OpenCV - sama pendekatan
kayak serialControlApp/cameradisplay.py punya v1 lama, cuma di sini pakai
QLabel/PySide6 bukan Tkinter Canvas).

Requirement tambahan: pip install pygrabber (buat cari device by NAME,
bukan angka index yang bisa geser kalau urutan enumerasi DirectShow
Windows berubah - lihat cari_index_kamera()).
"""

import cv2
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

try:
    from pygrabber.dshow_graph import FilterGraph
except ImportError:
    FilterGraph = None

INTERVAL_UPDATE_MS = 33  # ~30fps


def cari_index_kamera(nama_substring):
    """Cari index device capture yang namanya MENGANDUNG nama_substring
    (case-insensitive) lewat DirectShow (pygrabber) - lebih stabil daripada
    hardcode angka index, karena index numerik bisa geser kalau urutan
    enumerasi Windows berubah (device lain ditambah/dicabut, dll), sedangkan
    nama device biasanya tetap.

    Return: (index, daftar_semua_nama)
      - index = None kalau gak ketemu ATAU pygrabber gak ke-install
      - daftar_semua_nama = list nama device yang kedetect (buat debug/log,
        biar user bisa lihat nama persis yang harus dipakai di konstanta)
    """
    if FilterGraph is None:
        return None, []
    graph = FilterGraph()
    daftar_nama = graph.get_input_devices()
    for i, nama in enumerate(daftar_nama):
        if nama_substring.lower() in nama.lower():
            return i, daftar_nama
    return None, daftar_nama


class CameraViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cap = None

        self.label_video = QLabel("Camera Disconnected")
        self.label_video.setAlignment(Qt.AlignCenter)
        self.label_video.setStyleSheet("background-color: black; color: gray;")
        self.label_video.setMinimumSize(320, 240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label_video)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._ambil_frame)

    def mulai(self, index_device):
        """index_device: nomor device capture card (cek Device Manager/coba
        angka 0,1,2,... - sama cara kayak video_source di cameradisplay.py lama)."""
        self.berhenti()
        self._cap = cv2.VideoCapture(index_device)
        if not self._cap.isOpened():
            self.label_video.setText(f"Failed to open camera index {index_device}")
            self._cap = None
            return False
        self._timer.start(INTERVAL_UPDATE_MS)
        return True

    def berhenti(self):
        self._timer.stop()
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self.label_video.setText("Camera Disconnected")

    def _ambil_frame(self):
        if self._cap is None:
            return
        ret, frame = self._cap.read()
        if not ret:
            return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        tinggi, lebar, _ = frame_rgb.shape
        image = QImage(frame_rgb.data, lebar, tinggi, 3 * lebar, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image).scaled(
            self.label_video.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.label_video.setPixmap(pixmap)
