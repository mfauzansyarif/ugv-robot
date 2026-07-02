"""
Test tool nampilin video dari capture card (murni Python, TANPA OBS).

Kode lama project ini (serialControlApp/cameradisplay.py) sebenarnya udah pakai
cv2.VideoCapture() langsung, gak manggil OBS di kode-nya. Instruksi "OBS harus jalan"
di dokumentasi lama kemungkinan cuma workaround driver capture card yang rewel pas
pertama diakses di Windows - coba dulu TANPA OBS. Kalau gambar item/gagal, baru coba
buka OBS di background (gak perlu virtual camera aktif, cuma buat "manasin" driver-nya)
lalu ulangi.

Requirement: pip install opencv-python
"""

import cv2

# Coba beberapa backend Windows - device capture card kadang cuma kedetect di salah satu
BACKENDS = [
    ("DSHOW", cv2.CAP_DSHOW),
    ("MSMF", cv2.CAP_MSMF),
    ("ANY (default)", cv2.CAP_ANY),
]


def scan_kamera(maks_index=10):
    print(f"Nyari device video index 0-{maks_index - 1}, coba tiap backend ({[b[0] for b in BACKENDS]})...")
    ketemu = []  # list of (index, backend_nama, backend_id)
    for i in range(maks_index):
        for nama_backend, id_backend in BACKENDS:
            cap = cv2.VideoCapture(i, id_backend)
            if cap.isOpened():
                lebar = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                tinggi = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"  [{i}] kebuka pakai backend {nama_backend} - resolusi {lebar}x{tinggi}")
                ketemu.append((i, nama_backend, id_backend))
                cap.release()
                break  # udah ketemu backend yang jalan buat index ini, gak usah coba backend lain
            cap.release()
        else:
            print(f"  [{i}] gak kebuka di backend manapun")
    return ketemu


def tampilkan(index, id_backend, paksa_mjpg=True):
    cap = cv2.VideoCapture(index, id_backend)
    if not cap.isOpened():
        print(f"Gagal buka device index {index}.")
        return

    if paksa_mjpg:
        # Banyak capture card murah (termasuk ezcap) nampilin gambar item/rusak kalau
        # OpenCV negotiate format piksel default yang salah - paksa MJPG sering fix ini
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

    print("\nNampilin video. Klik jendelanya lalu tekan 'q' buat keluar.\n")
    print("Kalau item/garis doang: cek apakah kamera-TX-RX beneran nyala & transmit,")
    print("bukan cuma capture card-nya doang yang aktif.\n")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Gagal baca frame (device putus / gak ada sinyal masuk?).")
            break
        cv2.imshow("Video Capture Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    print("Pilih:\n  1. Scan device video yang kedetect (semua backend)\n  2. Langsung buka index+backend tertentu")
    pilihan = input("Pilihan: ").strip()
    if pilihan == "1":
        ketemu = scan_kamera()
        if not ketemu:
            print("Gak ada device video yang kebuka sama sekali di backend manapun.")
            print("Cek Device Manager - apakah capture card-nya kedetect Windows sama sekali?")
            return
        print("\nKetemu:", [(i, b) for i, b, _ in ketemu])
        idx_pilih = int(input("Pilih index yang mau ditampilin: ").strip())
        id_backend = next(b_id for i, _, b_id in ketemu if i == idx_pilih)
    else:
        idx_pilih = int(input("Index device video: ").strip())
        for i, (nama, _) in enumerate(BACKENDS):
            print(f"  [{i}] {nama}")
        pilihan_backend = int(input("Pilih backend: ").strip())
        id_backend = BACKENDS[pilihan_backend][1]
    tampilkan(idx_pilih, id_backend)


if __name__ == "__main__":
    main()
