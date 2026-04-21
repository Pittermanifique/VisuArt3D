from machine import Pin,PWM, UART
import time


# Définition des broches GPIO
IN1 = Pin(16, Pin.OUT)  # Direction du moteur (IN1)
IN2 = Pin(15, Pin.OUT)  # Direction du moteur (IN2)
ENA = Pin(17, Pin.OUT)  # PWM pour contrôler la vitesse

uart = UART(1, baudrate=115200, tx=1, rx=3)

led = Pin(13,Pin.OUT)
ledR = Pin(12,Pin.OUT)
switch = Pin(2,Pin.IN)

# Configuration PWM pour ENA (vitesse du moteur)
pwm = PWM(ENA)
pwm.freq(1000)  # Fréquence du PWM (peut être ajustée)
pwm.duty(1023)   # Valeur du rapport cyclique (250-1023) pour la vitesse (ici à 50%)(min=250)

def tourner_avant():
    IN1.value(1)
    IN2.value(0)
    print("Le moteur tourne en avant")

# Fonction pour faire tourner le moteur dans le sens antihoraire
def tourner_arriere():
    IN1.value(0)
    IN2.value(1)
    print("Le moteur tourne en arrière")

# Fonction pour arrêter le moteur
def arreter_moteur():
    IN1.value(0)
    IN2.value(0)
    print("Le moteur est arrêté")

if switch.value()== 0:
    while True:
        led.value(1)
        time.sleep(1)
        led.value(0)
        time.sleep(1)
        
        uart.write("test"+"\n")
        
        if uart.any():
            data = uart.read().decode('utf-8').strip()
            if data == "0" :
                ledR.value(0)
                arreter_moteur()
                
            elif data=="1":
                ledR.value(1)
                tourner_arriere()
                
            else:
                uart.write("error"+"\n")
                

    
    