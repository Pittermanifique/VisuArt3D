from machine import Pin, PWM, UART
import time

# Définition des broches GPIO
IN1 = Pin(16, Pin.OUT)  # Direction du moteur (IN1)
IN2 = Pin(15, Pin.OUT)  # Direction du moteur (IN2)
ENA = Pin(17, Pin.OUT)  # PWM pour contrôler la vitesse

# Configuration PWM pour ENA (vitesse du moteur)
pwm = PWM(ENA)
pwm.freq(1000)  # Fréquence du PWM (peut être ajustée)
pwm.duty(1023)   # Valeur du rapport cyclique (250-1023) pour la vitesse (ici à 50%)(min=250)

uart = UART(1, baudrate=115200, tx=1, rx=3)

# Fonction pour faire tourner le moteur dans le sens horaire
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
    
# Exemple d'utilisation
try:
    while True:        
        if uart.any():
            data = uart.read().decode('utf-8').strip()
            rotation = float(data)
        # Répondre immédiatement
        uart.write("ESP32 dit : " + data + "\n")
    
    # Exemple : envoyer un message périodiquement
    uart.write("ESP32 envoie un ping\n")
    time.sleep(2)

    if rotation<-0.1 :
        tourner_avant()
            
    elif rotation>0.1:
        tourner_arriere()
    
except KeyboardInterrupt:
    print("Arrêt du programme")
    arreter_moteur()  # Assurez-vous d'arrêter le moteur en cas d'interruption