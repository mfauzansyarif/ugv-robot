"""Konfigurasi yang bisa diubah TANPA compile ulang .exe - disimpan di file
JSON (config.json) di folder yang SAMA dengan exe/script yang jalan, biar
bisa diedit manual pakai text editor ATAU lewat field input di aplikasi
sendiri (lihat tombol "Simpan" di panel Koneksi, main_window.py).
"""

import json
import os
import sys

NAMA_FILE_CONFIG = "config.json"

DEFAULT_CONFIG = {
    "port_arduino": "COM5",
    "port_rf": "COM7",
    "camera_device_name": "USB Video",
}


def _direktori_aplikasi():
    """Kalau udah di-compile jadi .exe (PyInstaller dkk), __file__ nunjuk ke
    folder temp ekstraksi, BUKAN lokasi exe yang sebenarnya - makanya harus
    cek sys.frozen dan pakai sys.executable biar config.json kesimpan di
    sebelah exe yang beneran, bukan ke folder temp yang ilang begitu app
    ditutup."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def path_config():
    return os.path.join(_direktori_aplikasi(), NAMA_FILE_CONFIG)


def load_config():
    path = path_config()
    if not os.path.exists(path):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        hasil = dict(DEFAULT_CONFIG)
        hasil.update(data)  # jaga-jaga kalau file lama kurang lengkap key-nya
        return hasil
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)


def save_config(config_dict):
    path = path_config()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)
