from machine import Pin
from lib.mfrc522 import MFRC522
import utime
from WSclient import WSclient
from WebSocketClient import WebSocketClient

# Initialize WebSocket client
# ws_client = WSclient("Cudy-EFFC", "33954721", "ws://192.168.10.244:8080/step3")
ws_client = WSclient("Potatoes 2.4Ghz", "Hakunamatata7342!", "ws://192.168.2.241:8080/step3")

# Attempt to connect WiFi and WebSocket
def setup_connection():
    try:
        if ws_client.connect_wifi():
            ws = WebSocketClient(ws_client.WEBSOCKET_URL)
            if ws.connect():
                print("WebSocket connection established")
                ws.send("Seau connecté")
                return ws
        print("Failed to establish connection")
        return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

# Initialize components
reader = MFRC522(spi_id=0, sck=5, miso=16, mosi=17, cs=18, rst=4)
led = Pin(2, Pin.OUT)
relay = Pin(19, Pin.OUT) 


# Establish WebSocket connection
ws = setup_connection()

# Variable to track the previous tag state
previous_tag_detected = False
# Variable relai
relay_active = False
relay_timeout = None


print("Bring TAG closer...")
print("")

try:
    while True:
        reader.init()
        (stat, tag_type) = reader.request(reader.REQIDL)
        
        # Check if a tag is currently detected
        current_tag_detected = (stat == reader.OK)
        
        # Detect tag first detection
        if current_tag_detected and not previous_tag_detected:
            (stat, uid) = reader.SelectTagSN()
            if stat == reader.OK:
                card = int.from_bytes(bytes(uid), "little", False)
                print("TAG FIRST DETECTED - CARD ID: " + str(card))
                
                # Activation du relais
                relay.value(1)
                relay_active = True
                relay_timeout = utime.ticks_add(current_time, 5000)  # Timeout de 5 secondes
                
                
                # Send card ID via WebSocket
                if ws:
                    try:
                        message = f"TAG_DETECTED:{card}"
                        if ws.send(message):
                            print(f"Sent message: {message}")
                            led.value(1)  # Optional: Blink LED to confirm send
                            utime.sleep_ms(200)
                            led.value(0)
                        else:
                            print("Failed to send message")
                            # Attempt to reconnect if sending fails
                            ws = setup_connection()
                    except Exception as e:
                        print(f"Send error: {e}")
                        ws = setup_connection()
        
        # Detect tag removal
        elif not current_tag_detected and previous_tag_detected:
            print("TAG REMOVED")
            if ws:
                try:
                    message = "TAG_REMOVED"
                    if ws.send(message):
                        print(f"Sent message: {message}")
                    else:
                        print("Failed to send removal message")
                        ws = setup_connection()
                except Exception as e:
                    print(f"Send error: {e}")
                    ws = setup_connection()
        
        # Vérifier le timeout du relais
        if relay_active and utime.ticks_diff(relay_timeout, current_time) <= 0:
            relay.value(0)
            relay_active = False
            print("Relay timeout - turned off")
        
        
        # Update the previous state
        previous_tag_detected = current_tag_detected
        
        utime.sleep_ms(50)  # Short delay to prevent excessive polling

except KeyboardInterrupt:
    print("Bye")
finally:
    # Ensure WebSocket is closed
    if ws:
        ws.close()
    relay.value(0)  # Ensure relay is off when exiting
    led.value(0)    # Ensure LED is off when exiting