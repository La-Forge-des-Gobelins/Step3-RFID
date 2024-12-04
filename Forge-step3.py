import network
import time
import json
from machine import Pin, SPI
from mfrc522 import MFRC522
from WebSocketClient import WebSocketClient
import gc

# Configuration WiFi
WIFI_SSID = "Cudy-EFFC"
WIFI_PASSWORD = "33954721"

# Configuration WebSocket
WEBSOCKET_URL = "ws://192.168.10.250:8080/say"  # Adresse à adapter

# Configuration RFID
spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = MFRC522(spi, sda=Pin(5), rst=Pin(4))

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print(f'Connexion au réseau {WIFI_SSID}...')
    
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            print('Attente de connexion...')
            time.sleep(1)
            
    if wlan.isconnected():
        print('Connexion WiFi réussie!')
        print('Adresse IP:', wlan.ifconfig()[0])
        return True
    else:
        print('Échec de connexion WiFi')
        return False

def send_rfid_data(ws, uid):
    try:
        data = {
            'uid': [hex(x) for x in uid],
            'timestamp': time.time()
        }
        message = json.dumps(data)
        if ws.send(message):
            print('Données envoyées:', message)
        else:
            print("Erreur d'envoi du message WebSocket")
    except Exception as e:
        print('Erreur lors de l\'envoi:', e)

def main():
    gc.collect()

    if not connect_wifi():
        print("Impossible de continuer sans connexion WiFi")
        return

    ws = WebSocketClient(WEBSOCKET_URL)

    try:
        if ws.connect():
            print("Connecté au serveur WebSocket")
            ws.socket.setblocking(False)
            
             # Envoi du message de connexion
            connect_message = json.dumps({"message": "ESP32 connecté", "timestamp": time.time()})
            if ws.send(connect_message):
                print(f"Message de connexion envoyé: {connect_message}")
            
            print("Scanner RFID prêt. Approche une carte...")

            while True:
                (stat, tag_type) = rdr.request(rdr.REQIDL)
                if stat == rdr.OK:
                    print("Tag détecté, type:", tag_type)
                    (stat, uid) = rdr.anticoll()
                    if stat == rdr.OK:
                        print("UID du tag:", uid)
                        send_rfid_data(ws, uid)
                        time.sleep(2)  # Pause pour éviter les lectures répétées
                time.sleep(0.1)  # Mini délai pour réduire l'utilisation CPU

    except KeyboardInterrupt:
        print("Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        if ws:
            ws.close()
            print("Connexion WebSocket fermée")
            
if __name__ == "__main__":
    main()
