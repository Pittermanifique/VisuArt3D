from machine import Pin, UART, I2C
from lsm303 import LSM303D
from time import sleep
from math import sqrt, atan2, pi, asin, cos, sin
import gc

# Configuration des Pins
lr = Pin(16, Pin.OUT)
lb = Pin(17, Pin.OUT)

# Initialisation I2C et UART
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
uart = UART(1, baudrate=115200, tx=1, rx=3)

# Initialisation capteur
# Remplacez par vos offsets calculés si nécessaire
imu = LSM303D(i2c, ox=0, oy=0, oz=0, sx=1, sy=1, sz=1)

# Constantes
RAD_TO_DEG = 180 / pi

# Routine de calibration (si activée)
CALIBRATE_COMP = False
if CALIBRATE_COMP:
    imu.calibrate_mag()

# État initial des LEDs
lr.value(1)
lb.value(1)

while True:
    try:
        acc = imu.get_acc()
        mag = imu.get_mag()
        
        # Calcul des normes
        norm_acc = sqrt(sum(x*x for x in acc))
        norm_mag = sqrt(sum(x*x for x in mag))

        if norm_acc > 0 and norm_mag > 0:
            # Normalisation
            ax, ay, az = [x / norm_acc for x in acc]
            bx, by, bz = [x / norm_mag for x in mag]
            
            # Calcul Pitch et Roll
            pitch = asin(-ax)
            cos_pitch = cos(pitch)
            
            if abs(cos_pitch) > 0.001:
                roll = asin(ay / cos_pitch)
            else:
                roll = 0
            
            # Inclinaison compensée (Tilt-compensated Heading)
            xh = bx * cos(pitch) + bz * sin(pitch)
            yh = bx * sin(roll) * sin(pitch) + by * cos(roll) - bz * sin(roll) * cos(pitch)
            
            # Calcul du cap avec atan2 (gère tous les quadrants automatiquement)
            heading = atan2(yh, xh)
            heading_deg = heading * RAD_TO_DEG
            
            if heading_deg < 0:
                heading_deg += 360
            
            uart.write(str(heading_deg) + "\n")

        # Gestion UART
        if uart.any():
            line = uart.readline() # Reads until \n
            if line:
                try:
                    data = int(line.decode('utf-8').strip())
                    # Logic for pins
                    lr.value(1 if data < 100 else 0)
                    lb.value(1 if data > 100 else 0)
                except ValueError:
                    # Handle cases where data might be malformed
                    pass
                
    except Exception as e:
        uart.write("error" + e + "\n")
    gc.collect()
    sleep(0.1) # Petite pause pour stabiliser la boucle