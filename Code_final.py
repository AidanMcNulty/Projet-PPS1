"""
@Titre          : Script de Monitoring IoT avec ESP32 et ThingsBoard
@description    : Ce script se connecte au WiFi, lit la température, l'humidité d'un capteur DHT22, et la tension de la batterie.
                  Les données sont envoyées périodiquement à une plateforme ThingsBoard via une requête HTTP POST.
@auteur         : XAAN
@date           : 7 novembre 2024
@version        : 1.0
@dépendances    : network, urequests, dht, machine
"""

import network
import urequests     # Bibliothèque pour les requêtes HTTP
import dht           # Pour lire les données du capteur DHT22 ou DHT11
from machine import ADC, Pin
import time

# Configuration de la broche GPIO utilisée pour alimenter le DHT22
vcc_pin = Pin(14, Pin.OUT)  # Utiliser GPIO 14 pour l'alimentation
vcc_pin.value(1)  # Alimenter le capteur en mettant la broche à HIGH

# Informations WiFi (remplace par ton SSID et mot de passe)
ssid = "TGE-IOT"
password = "iOTN3t$$"

# Ton token d'authentification ThingsBoard
token = "ZGsIe4kcUxbCptFZJKmj"

# URL pour envoyer les données à ThingsBoard
url = f"http://10.3.159.3:8081/api/v1/{token}/telemetry"

"""
    @Titre          : Connexion WiFi
    @description    : Connecte l'appareil au réseau WiFi en utilisant les informations d'identification fournies.
                      Affiche l'adresse IP une fois la connexion réussie.
    @auteur         : XAAN
    @date           : 7 novembre 2024
    @param          : ssid (str) - Nom du réseau WiFi
                      password (str) - Mot de passe du réseau WiFi
    @return         : wlan (network.WLAN) - Objet WLAN avec les informations de connexion
"""
def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print("Connexion au WiFi...")
    while not wlan.isconnected():
        time.sleep(1)

    print("Connecté ! Adresse IP :", wlan.ifconfig()[0])
    return wlan

# Se connecter au WiFi
wlan = connect_to_wifi(ssid, password)

# Configurer le capteur DHT22 (sur GPIO 15 pour Data)
sensor = dht.DHT22(Pin(15))

# Configurer l'ADC pour lire la tension sur GP26 (ADC0) pour la batterie
adc = ADC(Pin(26))

"""
    @Titre          : Envoi de données
    @description    : Envoie les données de température, d'humidité, et de niveau de batterie à ThingsBoard via une requête HTTP POST.
    @auteur         : XAAN
    @date           : 7 novembre 2024
    @param          : temperature (float) - Température lue du capteur DHT22
                      humidity (float) - Humidité lue du capteur DHT22
                      batteryLevel (float) - Niveau de batterie en pourcentage
    @return         : Aucun retour. Affiche les données envoyées ou une erreur en cas d'échec.
"""
def send_data(temperature, humidity, batteryLevel):
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "BatteryLevel": batteryLevel
    }
    try:
        response = urequests.post(url, json=data)
        print("Données envoyées :", response.text)
        response.close()
    except Exception as e:
        print("Erreur lors de l'envoi des données :", e)

"""
    @Titre          : Lecture du niveau de batterie
    @description    : Lit la tension de la batterie via l'ADC et la convertit en un pourcentage compris entre des valeurs minimales et maximales.
    @auteur         : XAAN
    @date           : 7 novembre 2024
    @param          : Aucun
    @return         : batteryLevel (float) - Niveau de batterie en pourcentage
"""
def read_battery_level():
    raw_value = adc.read_u16()
    voltage = (raw_value / 65535) * 3.3

    min_voltage = 1.80
    max_voltage = 3.10

    if voltage > max_voltage:
        voltage = max_voltage
    elif voltage < min_voltage:
        voltage = min_voltage

    batteryLevel = (voltage - min_voltage) / (max_voltage - min_voltage) * 100
    return batteryLevel

# Boucle principale
while True:
    try:
        # Lire la tension de la batterie
        batteryLevel = read_battery_level()
        print("Pourcentage de la batterie : {:.2f} %".format(batteryLevel))

        # Activer l'alimentation du capteur avant la lecture
        vcc_pin.value(1)  # Mettre VCC à HIGH
        time.sleep(1)  # Attendre un peu que le capteur s'initialise

        # Lire les données du capteur DHT22
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()

        # Afficher les données dans la console
        print(f"Température: {temperature:.2f} °C, Humidité: {humidity:.2f} %")

        # Envoyer les données à ThingsBoard
        send_data(temperature, humidity, batteryLevel)

        # Désactiver l'alimentation du capteur après la lecture
        vcc_pin.value(0)  # Mettre VCC à LOW pour économiser de l'énergie

    except OSError as e:
        print("Erreur de lecture du capteur ou de la batterie :", e)

    # Attendre 5 secondes avant la prochaine mesure
    time.sleep(5)
