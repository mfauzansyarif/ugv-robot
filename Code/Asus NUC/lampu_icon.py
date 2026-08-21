"""Ikon lampu MONOCHROME, digambar manual pakai QPainter (emoji lampu
bawaan OS gak bisa dikontrol warnanya). Nyala = bohlam terisi penuh,
mati = bohlam outline polos.
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

WARNA_NYALA = QColor("#ffc400")  # kuning/amber - standar indikator "ON", kontras jelas ke semua background
WARNA_MATI = QColor("#707070")


class LampuIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self._menyala = False

    def set_menyala(self, menyala):
        self._menyala = menyala
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        warna = WARNA_NYALA if self._menyala else WARNA_MATI
        pen = QPen(warna)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QBrush(warna) if self._menyala else Qt.NoBrush)

        # Bohlam (lingkaran)
        painter.drawEllipse(QRectF(3, 1, 14, 14))
        # Dasar/ulir bohlam (kotak kecil di bawah lingkaran)
        painter.drawRect(QRectF(7, 14, 6, 4))
