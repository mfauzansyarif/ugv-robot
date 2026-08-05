"""Widget Camera Viewer - nampilin video feed dari receiver RF video lewat
capture card, muncul sebagai video device biasa ke OpenCV.

Requirement tambahan: pip install pygrabber (cari device by NAME, bukan
index yang bisa geser tiap device lain ditambah/dicabut).
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

# Sisa blanking interval sinyal PAL suka nongol jadi garis/noise warna
# solid di baris paling BAWAH frame - bukan masalah RF/sinyal, itu emang
# artefak normal video analog. Angka ini di-tune manual buat capture
# card & resolusi yang dipakai sekarang (lihat Testcode/test_video_capture.py
# buat cara re-tune-nya kalau ganti capture card/resolusi: set 0 dulu,
# lihat berapa px garisnya, sesuaikan).
CROP_BAWAH_PIXEL = 100


def list_nama_kamera():
    """List semua nama device capture yang kedetect DirectShow - buat isi
    dropdown di Settings dialog. List kosong kalau pygrabber gak ke-install
    atau emang gak ada device."""
    if FilterGraph is None:
        return []
    return FilterGraph().get_input_devices()


def cari_index_kamera(nama_substring):
    """Cari index device yang namanya MENGANDUNG nama_substring
    (case-insensitive). Return: (index, daftar_semua_nama) - index None
    kalau gak ketemu/pygrabber gak ke-install, daftar_semua_nama buat log."""
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
        self._box = None  # dict box_* dari telemetry RF, None = belum ada data

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
        """index_device: nomor device capture card (cek Device Manager)."""
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

    def set_deteksi_box(self, data_telemetry):
        """Dipanggil MainWindow tiap ada telemetry RF baru - simpen box
        terbaru, digambar di frame video BERIKUTNYA yang di-render (gak
        perlu sinkron persis, update-nya udah ~20Hz)."""
        self._box = data_telemetry

    def _gambar_box(self, frame_rgb, lebar_frame, tinggi_frame):
        """Overlay kotak deteksi CV dari Jetson di atas video analog RC832.
        Koordinat dari Jetson itu PERSENTASE (bukan piksel absolut), jadi
        otomatis nyesuaian ke resolusi video analog ini - TAPI asumsinya
        field-of-view kamera CV (Jetson) & kamera analog (RC832) MIRIP,
        jadi posisinya kira-kira pas, bukan presisi piksel sempurna kalau
        ternyata dua kamera fisiknya beda framing."""
        if self._box is None or not self._box.get("box_terdeteksi"):
            return

        pusat_x_px = (self._box["box_pusat_x"] + 100) / 200 * lebar_frame
        pusat_y_px = (100 - self._box["box_pusat_y"]) / 200 * tinggi_frame
        lebar_px = self._box["box_lebar"] / 100 * lebar_frame
        tinggi_px = self._box["box_tinggi"] / 100 * tinggi_frame

        x1 = int(pusat_x_px - lebar_px / 2)
        y1 = int(pusat_y_px - tinggi_px / 2)
        x2 = int(pusat_x_px + lebar_px / 2)
        y2 = int(pusat_y_px + tinggi_px / 2)
        cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)

    def _ambil_frame(self):
        if self._cap is None:
            return
        ret, frame = self._cap.read()
        if not ret:
            return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if CROP_BAWAH_PIXEL > 0:
            frame_rgb = frame_rgb[:-CROP_BAWAH_PIXEL, :]
        tinggi, lebar, _ = frame_rgb.shape
        self._gambar_box(frame_rgb, lebar, tinggi)
        image = QImage(frame_rgb.data, lebar, tinggi, 3 * lebar, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image).scaled(
            self.label_video.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.label_video.setPixmap(pixmap)
