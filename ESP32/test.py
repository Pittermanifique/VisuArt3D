from machine import Pin, UART, I2C, PWM
from lsm303 import LSM303D
from time import sleep
from math import sqrt, atan2, pi, asin, cos, sin
import gc

# Configuration des Pins
lr = Pin(14, Pin.OUT)
lb = Pin(13, Pin.OUT)

IN1 = Pin(16, Pin.OUT)  
IN2 = Pin(15, Pin.OUT)  
ENA = Pin(17, Pin.OUT)

pwm = PWM(ENA)
pwm.freq(1000)  # Fréquence du PWM (peut être ajustée)
pwm.duty(1023)   # Valeur du rapport cyclique (250-1023) pour la vitesse (ici à 50%)(min=250)

# Fonction pour faire tourner le moteur dans le sens horaire
def tourner_avant(data):
    pwm.duty((100-data)*10+20)
    IN1.value(1)
    IN2.value(0)
    print("Le moteur tourne en avant")

# Fonction pour faire tourner le moteur dans le sens antihoraire
def tourner_arriere(data):
    pwm.duty(data*10+20)
    IN1.value(0)
    IN2.value(1)
    print("Le moteur tourne en arrière")

# Fonction pour arrêter le moteur
def arreter_moteur():
    IN1.value(0)
    IN2.value(0)
    print("Le moteur est arrêté")

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
                    if data < 100:
                        lr.value(1)
                        lb.value(0)
                        tourner_avant(data)
                    elif data > 100:
                        lb.value(1)
                        lr.value(0)
                        tourner_arriere(data - 100)
                    else:
                        lb.value(0)
                        lr.value(0)
                        arreter_moteur()
                except ValueError:
                    # Handle cases where data might be malformed
                    pass
                
    except Exception as e:
        uart.write("error" + e + "\n")
    gc.collect()