"""Widget Console Log - lihat dokumentasi/ROS2_BRIEF.md section 7.4 buat desain
lengkapnya. Prinsip: log PERUBAHAN STATUS/EVENT DISKRIT, bukan tiap siklus RF -
pemanggil widget ini yang tanggung jawab gak nge-log tiap tick, widget ini
sendiri gak nge-throttle apapun.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTextEdit
from datetime import datetime

MAX_BARIS = 500

WARNA_LEVEL = {
    "INFO": "#a0a0a0",
    "WARNING": "#e0c040",
    "ERROR": "#e05050",
}


class ConsoleLog(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setStyleSheet("background-color: #1e1e1e; font-family: Consolas, monospace;")
        self._jumlah_baris = 0
        self._autoscroll = True

        # Kalau user scroll manual ke atas, pause autoscroll sampai dia balik ke bawah
        self.verticalScrollBar().valueChanged.connect(self._cek_posisi_scroll)

    def _cek_posisi_scroll(self, nilai):
        scrollbar = self.verticalScrollBar()
        self._autoscroll = nilai >= scrollbar.maximum() - 4

    def log(self, level, pesan):
        """level: 'INFO' / 'WARNING' / 'ERROR'"""
        warna = WARNA_LEVEL.get(level, "#ffffff")
        waktu = datetime.now().strftime("%H:%M:%S")
        baris_html = f'<span style="color:{warna};">[{waktu}] {level}: {pesan}</span>'
        self.append(baris_html)
        self._jumlah_baris += 1

        if self._jumlah_baris > MAX_BARIS:
            self._buang_baris_lama()

        if self._autoscroll:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _buang_baris_lama(self):
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deleteChar()  # buang newline sisa
        self._jumlah_baris -= 1

    def info(self, pesan):
        self.log("INFO", pesan)

    def warning(self, pesan):
        self.log("WARNING", pesan)

    def error(self, pesan):
        self.log("ERROR", pesan)
