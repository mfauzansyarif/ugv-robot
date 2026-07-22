import spidev
import time

# Ganti bus & device sesuai SPI yang mau dites
# spi1 (pin 19,21,23,24,26) -> bus 0
# spi2 (pin 13,16,18,22,37) -> bus 1
BUS = 0
DEVICE = 0

spi = spidev.SpiDev()
spi.open(BUS, DEVICE)

spi.max_speed_hz = 500000
spi.mode = 0b00  # CPOL=0, CPHA=0

test_data = [0x01, 0x55, 0xAA, 0xFF, 0x00, 0x12, 0x34]

print(f"Testing loopback on /dev/spidev{BUS}.{DEVICE}")
print(f"Sending: {[hex(x) for x in test_data]}")

result = spi.xfer2(test_data)

print(f"Received: {[hex(x) for x in result]}")

if result == test_data:
    print("✅ LOOPBACK SUCCESS — data match!")
else:
    print("❌ LOOPBACK FAILED — data mismatch")

spi.close()