import spidev

BUS = 0
DEVICE = 0

spi = spidev.SpiDev()
spi.open(BUS, DEVICE)

spi.max_speed_hz = 10000  # pelanin dulu, 10kHz
spi.mode = 0b00

print("Max speed:", spi.max_speed_hz)
print("Mode:", spi.mode)
print("Bits per word:", spi.bits_per_word)

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