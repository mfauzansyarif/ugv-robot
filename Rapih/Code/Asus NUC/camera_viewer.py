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

# Kamera fisiknya SAMA kayak yang RTSP di Jetson (native 640x360, 16:9),
# tapi video analog PAL ini native-nya 720x576 (~4:3) - kontennya UDAH
# match edge-to-edge, cuma buffer-nya ke-stretch taller dari seharusnya.
# PAKSA_RASIO_16_9 = resize (BUKAN crop) balik ke 16:9, dihitung dari
# tinggi MENTAH (576) biar scale factor-nya presisi.
PAKSA_RASIO_16_9 = True

# Box hijau error dari driver capture card - JUMLAH PIXEL di FRAME MENTAH
# (720x576, SEBELUM di-press). Ditemuin & di-tuning manual pakai
# Testcode/test_video_capture.py (buka bareng Testcode/test_rtsp_kamera_jetson.py
# buat dibandingin) - 96 udah kebukti pas ngilangin hijau tanpa motong
# konten asli. Kalau capture card/resolusi ganti, tuning ulang di situ,
# BUKAN di sini (lebih gampang tes iteratif pakai script berdiri sendiri).
CROP_BAWAH_PIXEL_MENTAH = 96

# --- Kalibrasi FOV kiri/kanan/atas (tambahan kalau ternyata masih ada
# selisih dikit setelah 16:9+crop di atas - dari tes terakhir, framing
# udah match tanpa perlu ini, dibiarin 0.0). Cara tuning: lihat
# Testcode/test_video_capture.py, taruh benda di tepi frame RTSP,
# geser dikit-dikit (misal 0.02 = 2%) sampai posisinya sama di video RF.
CROP_KIRI_PERSEN = 0.0
CROP_KANAN_PERSEN = 0.0
CROP_ATAS_PERSEN = 0.0


def press_ke_16_9(frame_rgb):
    """RESIZE (bukan crop) SELURUH frame mentah ke rasio 16:9 - WAJIB
    dipanggil ke frame ASLI (belum di-crop apapun), soalnya scale factor
    yang bener buat ngoreksi stretch itu dihitung dari tinggi ASLI."""
    tinggi, lebar = frame_rgb.shape[:2]
    tinggi_target = int(lebar * 9 / 16)
    if tinggi_target != tinggi:
        frame_rgb = cv2.resize(frame_rgb, (lebar, tinggi_target), interpolation=cv2.INTER_AREA)
    return frame_rgb


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

    def _gambar_box(self, frame_rgb, lebar_acuan, tinggi_acuan, offset_x, offset_y):
        """Overlay kotak deteksi CV dari Jetson di atas video analog RC832.
        Koordinat dari Jetson itu PERSENTASE dari frame 16:9 MURNI (sama
        skala kayak RTSP di Jetson) - makanya `lebar_acuan`/`tinggi_acuan`
        itu HARUS dimensi SEBELUM crop hijau/kalibrasi diterapin, BUKAN
        dimensi frame_rgb yang beneran digambar (yang lebih kecil, abis
        di-crop). Kalau pakai dimensi abis-crop, skalanya "gepeng" dan box
        makin meleset makin ke bawah/tepi. `offset_x`/`offset_y` geser
        hasilnya biar nyocok sama origin frame_rgb yang baru (abis
        kiri/atas ikut kepotong) - kalau box jatuh di area yang udah
        kepotong, cv2.rectangle otomatis clip, aman gak error."""
        if self._box is None or not self._box.get("box_terdeteksi"):
            return

        pusat_x_px = (self._box["box_pusat_x"] + 100) / 200 * lebar_acuan
        pusat_y_px = (100 - self._box["box_pusat_y"]) / 200 * tinggi_acuan
        lebar_px = self._box["box_lebar"] / 100 * lebar_acuan
        tinggi_px = self._box["box_tinggi"] / 100 * tinggi_acuan

        x1 = int(pusat_x_px - lebar_px / 2) - offset_x
        y1 = int(pusat_y_px - tinggi_px / 2) - offset_y
        x2 = int(pusat_x_px + lebar_px / 2) - offset_x
        y2 = int(pusat_y_px + tinggi_px / 2) - offset_y
        cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)

    def _crop_kalibrasi_fov(self, frame_rgb):
        tinggi, lebar = frame_rgb.shape[:2]
        kiri = int(lebar * CROP_KIRI_PERSEN)
        kanan = lebar - int(lebar * CROP_KANAN_PERSEN)
        atas = int(tinggi * CROP_ATAS_PERSEN)
        # .copy() WAJIB - crop kolom (kiri/kanan) bikin array-nya gak lagi
        # contiguous di memori, padahal QImage butuh buffer contiguous
        # (kalau gak di-copy, gambar bisa geser/rusak/corrupt).
        return frame_rgb[atas:, kiri:kanan].copy(), kiri, atas

    def _ambil_frame(self):
        if self._cap is None:
            return
        ret, frame = self._cap.read()
        if not ret:
            return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        tinggi_mentah = frame_rgb.shape[0]

        if PAKSA_RASIO_16_9:
            frame_rgb = press_ke_16_9(frame_rgb)  # dari frame MENTAH, sebelum crop apapun

        # Dimensi 16:9 MURNI (sama skala kayak RTSP) - direkam SEBELUM
        # crop hijau/kalibrasi, dipakai buat acuan hitung posisi box.
        lebar_acuan = frame_rgb.shape[1]
        tinggi_acuan = frame_rgb.shape[0]

        if CROP_BAWAH_PIXEL_MENTAH > 0:
            # Skala crop-nya ikut rasio resize di atas, biar tetep pas
            # motong box hijau yang udah ikut menyusut proporsional.
            crop_sekarang = int(CROP_BAWAH_PIXEL_MENTAH * frame_rgb.shape[0] / tinggi_mentah)
            if crop_sekarang > 0:
                frame_rgb = frame_rgb[:-crop_sekarang, :]

        frame_rgb, offset_x, offset_y = self._crop_kalibrasi_fov(frame_rgb)
        self._gambar_box(frame_rgb, lebar_acuan, tinggi_acuan, offset_x, offset_y)
        tinggi, lebar, _ = frame_rgb.shape
        image = QImage(frame_rgb.data, lebar, tinggi, 3 * lebar, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image).scaled(
            self.label_video.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.label_video.setPixmap(pixmap)
