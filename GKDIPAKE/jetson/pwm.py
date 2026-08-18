import board
import busio
import adafruit_pca9685
from adafruit_motor import motor
import time

i2c = busio.I2C(board.SCL, board.SDA)
pca = adafruit_pca9685.PCA9685(i2c)

pca.frequency = 60

channel0 = pca.channels[0]
channel1 = pca.channels[1]
channel2 = pca.channels[2]
channel3 = pca.channels[3]
channel4 = pca.channels[4]
channel5 = pca.channels[5]
channel6 = pca.channels[6]
channel7 = pca.channels[7]
channel8 = pca.channels[8]
channel9 = pca.channels[9]
channel10 = pca.channels[10]
channel11 = pca.channels[11]
channel12 = pca.channels[12]
channel13 = pca.channels[13]
channel14 = pca.channels[14]
channel15 = pca.channels[15]

motor1 = motor.DCMotor(channel0, channel1)
motor2 = motor.DCMotor(channel2, channel3)
motor3 = motor.DCMotor(channel4, channel5)
motor4 = motor.DCMotor(channel6, channel7)
motor5 = motor.DCMotor(channel8, channel9)
motor6 = motor.DCMotor(channel10, channel11)
motor7 = motor.DCMotor(channel12, channel13)
motor8 = motor.DCMotor(channel14, channel15)

#motor1.throttle = 1
