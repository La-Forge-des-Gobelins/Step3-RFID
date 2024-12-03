import network
import socket
import json
import time
from machine import Pin, SPI
from mfrc522 import MFRC522

# Configuration WiFi
WIFI_SSID = "Cudy-EFFC"
WIFI_PASSWORD = "33954721"

# Configuration WebSocket
WEBSOCKET_HOST = "192.168.1.100"  # Adresse IP serveur A METTRE
WEBSOCKET_PORT = 81

# Configuration RFID
spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = MFRC522(spi, sda=Pin(5), rst=Pin(4))

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    while not wlan.isconnected():
        print('Connexion WiFi...')
        time.sleep(1)
    
    print('Connecté au WiFi')
    print('Adresse IP:', wlan.ifconfig()[0])

def create_websocket_client():
    try:
        ws = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ws.connect(socket.getaddrinfo(WEBSOCKET_HOST, WEBSOCKET_PORT)[0][-1])
        ws.send(b'GET / HTTP/1.1\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n')
        
        return ws
    except Exception as e:
        print('Erreur de connexion WebSocket:', e)
        return None

def send_rfid_data(ws, uid):
    try:
        data = {
            'uid': [hex(x) for x in uid],
            'timestamp': time.time()
        }
        message = json.dumps(data)
        
        ws.send(message)
        print('Données envoyées:', message)
    except Exception as e:
        print('Erreur lors de l\'envoi:', e)

def main():
    connect_wifi()
    ws = create_websocket_client()
    
    if not ws:
        return
    
    print("Scanner RFID prêt. Approche une carte...")
    
    try:
        while True:
            (stat, tag_type) = rdr.request(rdr.REQIDL)
            if stat == rdr.OK:
                print("Tag détecté, type:", tag_type)
                
                (stat, uid) = rdr.anticoll()
                if stat == rdr.OK:
                    print("UID du tag:", uid)
                    send_rfid_data(ws, uid)
                    
                    time.sleep(2)
    
    except KeyboardInterrupt:
        print("Arrêt du scan.")
    finally:
        ws.close()

if __name__ == '__main__':
    main()