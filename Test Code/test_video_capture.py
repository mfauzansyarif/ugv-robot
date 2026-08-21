"""
Test tool nampilin video dari capture card (murni Python, TANPA OBS).

Kode lama project ini sebenarnya udah pakai cv2.VideoCapture() langsung,
gak manggil OBS di kode-nya. Instruksi "OBS harus jalan"
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

# Kamera fisiknya SAMA kayak yang RTSP (native 640x360, rasio 16:9), dan
# konten video analog ini UDAH edge-to-edge sama persis kayak RTSP -
# buffer-nya doang yang lebih gede (720x576, ~4:3) gara-gara ke-stretch
# taller dari yang seharusnya. Solusinya RESIZE (press) balik ke 16:9,
# BUKAN crop - crop bakal buang konten asli yang valid, padahal gak ada
# yang perlu dibuang, cuma proporsinya yang perlu dikompres balik.
PAKSA_RASIO_16_9 = True

# Box hijau error dari driver capture card - JUMLAH PIXEL di FRAME MENTAH
# (720x576, SEBELUM di-press). Di-press DULUAN (pakai tinggi asli 576,
# biar scale factor buat ngoreksi stretch-nya PRESISI), baru abis itu
# crop sisa hijau yang udah ikut menyusut proporsional - kalau kebalik
# (crop dulu baru press), scale factor-nya keitung dari tinggi yang udah
# kepotong, hasilnya gambar masih keliatan dikit stretch. 96 = angka yang
# udah kebukti pas ngilangin hijau (di frame MENTAH, sebelum di-press).
CROP_BAWAH_PIXEL_MENTAH = 96

# --- Kalibrasi FOV kiri/kanan/atas (jarang perlu diubah - framing udah
# kebukti match) - lihat test_rtsp_kamera_jetson.py, taruh benda
# di tepi frame RTSP, geser dikit-dikit (misal 0.02 = 2%) kalau ternyata
# masih ada selisih. Sinkronin ke camera_viewer.py kalau diubah.
CROP_KIRI_PERSEN = 0.0
CROP_KANAN_PERSEN = 0.0
CROP_ATAS_PERSEN = 0.0


def press_ke_16_9(frame):
    """RESIZE (bukan crop) tinggi frame ke rasio 16:9 presis - semua
    konten TETAP ada edge-to-edge, cuma dikompres vertikal biar proporsi
    orang/benda balik natural (gak gepeng), sekalian ngilangin box hijau
    error yang ikut kekompres jadi tipis banget/gak keliatan."""
    tinggi, lebar = frame.shape[:2]
    tinggi_target = int(lebar * 9 / 16)
    if tinggi_target != tinggi:
        frame = cv2.resize(frame, (lebar, tinggi_target), interpolation=cv2.INTER_AREA)
    return frame


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

    # WINDOW_AUTOSIZE - kunci window SELALU pas ukuran asli frame, gak
    # bisa di-drag-resize/stretch manual (biar perbandingan visual sama
    # test_rtsp_kamera_jetson.py adil, dua-duanya native size).
    nama_window = "Video Capture Test"
    cv2.namedWindow(nama_window, cv2.WINDOW_AUTOSIZE)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Gagal baca frame (device putus / gak ada sinyal masuk?).")
            break
        print(f"Resolusi native frame: {frame.shape[1]}x{frame.shape[0]}", end="\r")
        tinggi_mentah = frame.shape[0]

        if PAKSA_RASIO_16_9:
            frame = press_ke_16_9(frame)  # dari frame MENTAH, sebelum crop apapun

        if CROP_BAWAH_PIXEL_MENTAH > 0:
            # Skala crop-nya ikut rasio resize di atas, biar tetep pas
            # motong box hijau yang udah ikut menyusut proporsional.
            crop_sekarang = int(CROP_BAWAH_PIXEL_MENTAH * frame.shape[0] / tinggi_mentah)
            if crop_sekarang > 0:
                frame = frame[:-crop_sekarang, :]

        tinggi, lebar = frame.shape[:2]
        kiri = int(lebar * CROP_KIRI_PERSEN)
        kanan = lebar - int(lebar * CROP_KANAN_PERSEN)
        atas = int(tinggi * CROP_ATAS_PERSEN)
        frame = frame[atas:, kiri:kanan]
        cv2.imshow(nama_window, frame)
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
    tampilkan(idx_pilih, id_backend, paksa_mjpg=False)


if __name__ == "__main__":
    main()
