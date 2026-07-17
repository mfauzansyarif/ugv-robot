"""GUI proof-of-concept: kontrol individual 12 motor linear (actuator BTS7960).
Tiap slider = 1 actuator, posisi -1/0/1 = retract/stop/extend.

Frame yang dikirim ke STM32 (format BARU, terpisah dari frame 8-field utama):
  "I <index 1-12> <dir -1/0/1>\n"

CATATAN: format ini masih proof-of-concept - firmware STM32 PERLU direvisi
dulu buat nerima & proses command "I ..." ini (belum ada di ProsesFrame8
yang sekarang, itu cuma parse frame 8-field grouping).

Requirement: pip install pyserial
(tkinter sudah bawaan Python, gak perlu install terpisah)
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

import serial
import serial.tools.list_ports

BAUDRATE = 57600

NAMA_ACTUATOR = [
    "0 SteerFD", "1 SteerFK", "2 SteerBD", "3 SteerBK",
    "4 FBodyKi", "5 FBodyKa",
    "6 BBodyKi", "7 BBodyKa",
    "8 RArmDpn", "9 RArmBlk",
    "10 LArmDpn", "11 LArmBlk",
]


class ActuatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("POC - Kontrol Individual 12 Motor Linear")
        self.ser = None
        self.lock = threading.Lock()

        self._buat_panel_koneksi()
        self._buat_panel_slider()

        self.root.protocol("WM_DELETE_WINDOW", self._saat_tutup)

    # ---------------- Koneksi serial ----------------
    def _buat_panel_koneksi(self):
        frame = ttk.Frame(self.root, padding=8)
        frame.pack(fill="x")

        ttk.Label(frame, text="Port:").pack(side="left")
        self.combo_port = ttk.Combobox(frame, width=30, state="readonly")
        self.combo_port.pack(side="left", padx=4)
        self._refresh_port()

        ttk.Button(frame, text="Refresh", command=self._refresh_port).pack(side="left", padx=2)
        self.btn_connect = ttk.Button(frame, text="Connect", command=self._toggle_connect)
        self.btn_connect.pack(side="left", padx=8)

        self.label_status = ttk.Label(frame, text="Belum connect", foreground="red")
        self.label_status.pack(side="left", padx=8)

    def _refresh_port(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.combo_port["values"] = ports
        if ports:
            self.combo_port.current(0)

    def _toggle_connect(self):
        if self.ser is None:
            port = self.combo_port.get()
            if not port:
                messagebox.showerror("Error", "Pilih port dulu.")
                return
            try:
                self.ser = serial.Serial(port, BAUDRATE, timeout=1)
                self.ser.dtr = False
                self.ser.rts = False
            except Exception as e:
                messagebox.showerror("Gagal connect", str(e))
                self.ser = None
                return
            self.label_status.config(text=f"Connected: {port}", foreground="green")
            self.btn_connect.config(text="Disconnect")
        else:
            self._kirim_stop_semua()
            self.ser.close()
            self.ser = None
            self.label_status.config(text="Belum connect", foreground="red")
            self.btn_connect.config(text="Connect")

    # ---------------- Panel slider ----------------
    def _buat_panel_slider(self):
        frame = ttk.Frame(self.root, padding=8)
        frame.pack(fill="both", expand=True)

        self.scales = []
        self.value_labels = []

        for i, nama in enumerate(NAMA_ACTUATOR):
            baris = ttk.Frame(frame)
            baris.pack(fill="x", pady=2)

            ttk.Label(baris, text=nama, width=12).pack(side="left")

            lbl_val = ttk.Label(baris, text="0", width=3)

            scale = tk.Scale(
                baris, from_=-1, to=1, resolution=1, orient="horizontal",
                length=200, showvalue=False,
                command=lambda val, idx=i, lbl=lbl_val: self._on_slider_change(idx, val, lbl),
            )
            scale.set(0)
            scale.pack(side="left", padx=6)
            lbl_val.pack(side="left")

            self.scales.append(scale)
            self.value_labels.append(lbl_val)

        tombol_frame = ttk.Frame(frame)
        tombol_frame.pack(fill="x", pady=10)
        btn_stop = tk.Button(
            tombol_frame, text="STOP SEMUA ACTUATOR", bg="red", fg="white",
            font=("Arial", 11, "bold"), command=self._stop_semua_ui,
        )
        btn_stop.pack(fill="x")

    def _on_slider_change(self, index, val, label_widget):
        dir_val = int(val)
        label_widget.config(text=str(dir_val))
        self._kirim_individual(index, dir_val)

    def _stop_semua_ui(self):
        for scale in self.scales:
            scale.set(0)  # otomatis trigger _on_slider_change -> kirim dir=0
        self._kirim_stop_semua()

    # ---------------- Kirim ke STM32 ----------------
    def _kirim_individual(self, index, dir_val):
        if self.ser is None:
            return  # belum connect, abaikan diam-diam (UI tetap responsif)
        baris = f"I {index} {dir_val}\n"
        with self.lock:
            try:
                self.ser.write(baris.encode("ascii"))
            except Exception as e:
                print(f"Gagal kirim: {e}")

    def _kirim_stop_semua(self):
        if self.ser is None:
            return
        with self.lock:
            for i in range(12):
                try:
                    self.ser.write(f"I {i} 0\n".encode("ascii"))
                except Exception as e:
                    print(f"Gagal kirim stop actuator {i}: {e}")

    def _saat_tutup(self):
        if self.ser is not None:
            self._kirim_stop_semua()
            self.ser.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ActuatorGUI(root)
    root.mainloop()