from machine import UART, Pin
from lib.mfrc522 import MFRC522
import time
from lib.kt403a import KT403A
from WSclient import WSclient
from WebSocketClient import WebSocketClient

# Initialize WebSocket client
ws_client = WSclient("Cudy-EFFC", "33954721", "ws://192.168.10.250:8080/step3")
# ws_client = WSclient("Cudy-EFFC", "33954721", "ws://192.168.10.31:8080/step3")
# ws_client = WSclient("Potatoes 2.4Ghz", "Hakunamatata7342!", "ws://192.168.2.241:8080/step3")

# Attempt to connect WiFi and WebSocket
def setup_connection():
    try:
        if ws_client.connect_wifi():
            ws = WebSocketClient(ws_client.WEBSOCKET_URL)
            if ws.connect():
                print("WebSocket connection established")
                ws.send("connect")
                return ws
        print("Failed to establish connection")
        return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

led = Pin(2, Pin.OUT)
relay = Pin(26, Pin.OUT)
kt = KT403A(pin_TX=17, pin_RX=16, debug=False)
# Régler le volume à 50%
kt.SetVolume(100)
time.sleep(2)

print("init websocket connection")
# Establish WebSocket connection
ws = None
while ws is None:
    ws = setup_connection()
    if ws is None:
        print("Connection failed. Retrying in 5 seconds...")
        time.sleep(5)

print("Ready")
# Variable relai
relay_active = False
relay_timeout = None

try:
    while True:
        if ws:
            try:
                msg = ws.receive()
                print("Message reçu :", msg)
                
                if msg == "Start":
                    kt.SetVolume(100)  
                    print("Activation du relais...")
                    relay.value(1)
                    
                    print("Playing music")
                    kt.PlaySpecific(1)
                    time.sleep(3)
                    
                    kt.Stop()
                    relay.value(0)
                    
                elif msg == "ping":
                    print("ping")
                    ws.send("Seau-pong")
                    
                elif msg == "Play":
                    kt.SetVolume(70)
                    print("Playing music")
                    kt.PlaySpecific(2)
                    time.sleep(15)
                    kt.Stop()
                    
            except Exception as e:
                print(f"WebSocket error: {e}")
                ws = None  # Reset connection on error
                
        if ws is None:
            print("Connection lost. Attempting to reconnect...")
            ws = setup_connection()
            if ws is None:
                print("Reconnection failed. Retrying in 5 seconds...")
                time.sleep(5)
                continue
        
        # Vérifier le timeout du relais
        if relay_active and time.ticks_diff(relay_timeout) <= 0:
            relay.value(0)
            relay_active = False
            print("Relay timeout - turned off")
        
        time.sleep_ms(50)  # Short delay to prevent excessive polling

except KeyboardInterrupt:
    print("Bye")
finally:
    # Ensure WebSocket is closed
    if ws:
        ws.close()
    relay.value(0)  # Ensure relay is off when exiting
    led.value(0)    # Ensure LED is off when exiting
