"""Ikon kecil lampu - MONOCHROME (bukan emoji berwarna), digambar manual
pakai QPainter biar konsisten di semua sistem (emoji lampu bawaan OS
biasanya berwarna kuning/oranye, gak bisa dikontrol). Nyala = bohlam
terisi penuh, mati = cuma garis outline.
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

WARNA_NYALA = QColor("#e8e8e8")
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
        # Filamen silang sederhana - cuma keliatan pas mati (biar gak nutupin
        # warna solid pas nyala)
        if not self._menyala:
            painter.drawLine(7, 5, 13, 11)
            painter.drawLine(13, 5, 7, 11)
