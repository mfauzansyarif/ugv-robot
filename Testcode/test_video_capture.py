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


def scan_kamera(maks_index=6):
    print(f"Nyari device video index 0-{maks_index - 1}...")
    ketemu = []
    for i in range(maks_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            lebar = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            tinggi = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"  [{i}] kebuka - resolusi {lebar}x{tinggi}")
            ketemu.append(i)
        else:
            print(f"  [{i}] gak kebuka")
        cap.release()
    return ketemu


def tampilkan(index):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"Gagal buka device index {index}.")
        return

    print("\nNampilin video. Klik jendelanya lalu tekan 'q' buat keluar.\n")
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
    print("Pilih:\n  1. Scan device video yang kedetect\n  2. Langsung buka index tertentu")
    pilihan = input("Pilihan: ").strip()
    if pilihan == "1":
        ketemu = scan_kamera()
        if not ketemu:
            print("Gak ada device video yang kebuka sama sekali.")
            return
        idx = int(input(f"Pilih index buat ditampilin {ketemu}: ").strip())
    else:
        idx = int(input("Index device video: ").strip())
    tampilkan(idx)


if __name__ == "__main__":
    main()
