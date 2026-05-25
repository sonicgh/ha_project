import machine
import ubinascii
import ujson
import network
import time
from umqtt.simple import MQTTClient
from machine import Pin, PWM

# ========== CONFIGURATION ==========
import config
WIFI_SSID = config.WIFI_SSID
WIFI_PASSWORD = config.WIFI_PASSWORD

# MQTT Configuration
MQTT_BROKER = config.MQTT_BROKER
MQTT_PORT = config.MQTT_PORT
MQTT_USER = config.MQTT_USER
MQTT_PASSWORD = config.MQTT_PASSWORD

# Device Configuration
DEVICE_ID = "esp32_device_" + ubinascii.hexlify(machine.unique_id()).decode()
DEVICE_NAME = "esp32_controller"

# Topic Structure
TOPIC_STATUS = f"homeassistant/sensor/{DEVICE_ID}/status"
TOPIC_LED1 = f"homeassistant/light/{DEVICE_ID}/led1/command"
TOPIC_LED2 = f"homeassistant/light/{DEVICE_ID}/led2/command"
TOPIC_LED3 = f"homeassistant/light/{DEVICE_ID}/led3/command"
TOPIC_SERVO = f"homeassistant/cover/{DEVICE_ID}/servo/command"

# Discovery topics for Home Assistant auto-configuration
DISCOVERY_LED1 = f"homeassistant/light/{DEVICE_ID}/led1/config"
DISCOVERY_LED2 = f"homeassistant/light/{DEVICE_ID}/led2/config"
DISCOVERY_LED3 = f"homeassistant/light/{DEVICE_ID}/led3/config"
DISCOVERY_SERVO = f"homeassistant/cover/{DEVICE_ID}/servo/config"

# ========== HARDWARE SETUP ==========
# LEDs (using GPIO pins - adjust as needed)
led1 = Pin(13, Pin.OUT)  # GPIO13
led2 = Pin(12, Pin.OUT)  # GPIO12
led3 = Pin(14, Pin.OUT)  # GPIO14

# Servo motor (using PWM on GPIO15)
servo_pin = Pin(15, Pin.OUT)
servo = PWM(servo_pin, freq=50)  # 50Hz for standard servos

# Optional: Built-in LED for status indication
status_led = Pin(2, Pin.OUT)

# Servo position mapping
def set_servo_angle(angle):
    """
    Set servo to specific angle (0-180 degrees)
    Duty cycle: 40 (0°) to 115 (180°) for most servos
    Adjust min/max values based on your servo specs
    """
    min_duty = 40
    max_duty = 115
    if angle < 0:
        angle = 0
    if angle > 180:
        angle = 180
   
    duty = min_duty + (angle / 180) * (max_duty - min_duty)
    servo.duty(int(duty))
    print(f"Servo set to {angle}° (duty: {int(duty)})")

# ========== WIFI CONNECTION ==========
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        status_led.value(0)  # LED off while connecting
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            machine.idle()
            time.sleep(1)
    print(f"WiFi connected: {wlan.ifconfig()}")
    status_led.value(1)  # LED on when connected

# ========== MQTT CALLBACK ==========
def mqtt_callback(topic, msg):
    """Handle incoming MQTT messages"""
    topic_str = topic.decode()
    msg_str = msg.decode().lower().strip()
   
    print(f"Received: {topic_str} -> {msg_str}")
    status_led.value(not status_led.value())  # Blink LED briefly
   
    # Control LEDs
    if topic_str == TOPIC_LED1:
        if msg_str == "on" or msg_str == "true":
            led1.value(1)
            print("LED1 ON")
            mqtt.publish(f"homeassistant/light/{DEVICE_ID}/led1/state", "ON")
        elif msg_str == "off" or msg_str == "false":
            led1.value(0)
            print("LED1 OFF")
            mqtt.publish(f"homeassistant/light/{DEVICE_ID}/led1/state", "OFF")
   
    elif topic_str == TOPIC_LED2:
        if msg_str == "on" or msg_str == "true":
            led2.value(1)
            print("LED2 ON")
            mqtt.publish(f"homeassistant/light/{DEVICE_ID}/led2/state", "ON")
        elif msg_str == "off" or msg_str == "false":
            led2.value(0)
            print("LED2 OFF")
            mqtt.publish(f"homeassistant/light/{DEVICE_ID}/led2/state", "OFF")
   
    elif topic_str == TOPIC_LED3:
        if msg_str == "on" or msg_str == "true":
            led3.value(1)
            print("LED3 ON")
            mqtt.publish(f"homeassistant/light/{DEVICE_ID}/led3/state", "ON")
        elif msg_str == "off" or msg_str == "false":
            led3.value(0)
            print("LED3 OFF")
            mqtt.publish(f"homeassistant/light/{DEVICE_ID}/led3/state", "OFF")
   
    # Control Servo
    elif topic_str == TOPIC_SERVO:
        try:
            if msg_str == "open":
                set_servo_angle(180)
                mqtt.publish(f"homeassistant/cover/{DEVICE_ID}/servo/state", "open")
            elif msg_str == "close":
                set_servo_angle(0)
                mqtt.publish(f"homeassistant/cover/{DEVICE_ID}/servo/state", "closed")
            elif msg_str.startswith("position:"):
                angle = int(msg_str.split(":")[1])
                set_servo_angle(angle)
                mqtt.publish(f"homeassistant/cover/{DEVICE_ID}/servo/state",
                           f"position:{angle}")
            else:
                angle = int(msg_str)
                set_servo_angle(angle)
                mqtt.publish(f"homeassistant/cover/{DEVICE_ID}/servo/state",
                           f"position:{angle}")
        except ValueError:
            print(f"Invalid servo command: {msg_str}")

# ========== MQTT SETUP ==========
def publish_discovery():
    """Publish Home Assistant MQTT discovery configuration"""
   
    # LED1 Discovery
    led1_config = {
        "name": f"{DEVICE_NAME} LED 1",
        "unique_id": f"{DEVICE_ID}_led1",
        "command_topic": TOPIC_LED1,
        "state_topic": f"homeassistant/light/{DEVICE_ID}/led1/state",
        "payload_on": "ON",
        "payload_off": "OFF",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "ESP32 Controller",
            "manufacturer": "Custom"
        }
    }
    mqtt.publish(DISCOVERY_LED1, ujson.dumps(led1_config), retain=True)
   
    # LED2 Discovery
    led2_config = {
        "name": f"{DEVICE_NAME} LED 2",
        "unique_id": f"{DEVICE_ID}_led2",
        "command_topic": TOPIC_LED2,
        "state_topic": f"homeassistant/light/{DEVICE_ID}/led2/state",
        "payload_on": "ON",
        "payload_off": "OFF",
        "device": {"identifiers": [DEVICE_ID], "name": DEVICE_NAME}
    }
    mqtt.publish(DISCOVERY_LED2, ujson.dumps(led2_config), retain=True)
   
    # LED3 Discovery
    led3_config = {
        "name": f"{DEVICE_NAME} LED 3",
        "unique_id": f"{DEVICE_ID}_led3",
        "command_topic": TOPIC_LED3,
        "state_topic": f"homeassistant/light/{DEVICE_ID}/led3/state",
        "payload_on": "ON",
        "payload_off": "OFF",
        "device": {"identifiers": [DEVICE_ID], "name": DEVICE_NAME}
    }
    mqtt.publish(DISCOVERY_LED3, ujson.dumps(led3_config), retain=True)
   
    # Servo Discovery (as a cover/garage door)
    servo_config = {
        "name": f"{DEVICE_NAME} Servo",
        "unique_id": f"{DEVICE_ID}_servo",
        "command_topic": TOPIC_SERVO,
        "state_topic": f"homeassistant/cover/{DEVICE_ID}/servo/state",
        "payload_open": "open",
        "payload_close": "close",
        "state_open": "open",
        "state_closed": "closed",
        "device_class": "garage",
        "device": {"identifiers": [DEVICE_ID], "name": DEVICE_NAME}
    }
    mqtt.publish(DISCOVERY_SERVO, ujson.dumps(servo_config), retain=True)
   
    print("Discovery configuration published")

def connect_mqtt():
    """Connect to MQTT broker"""
    global mqtt
    client_id = DEVICE_ID
    mqtt = MQTTClient(client_id, MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD)
    mqtt.set_callback(mqtt_callback)
   
    try:
        mqtt.connect()
        print(f"Connected to MQTT broker at {MQTT_BROKER}")
       
        # Subscribe to control topics
        topics = [TOPIC_LED1, TOPIC_LED2, TOPIC_LED3, TOPIC_SERVO]
        for topic in topics:
            mqtt.subscribe(topic)
            print(f"Subscribed to {topic}")
       
        # Publish discovery config for Home Assistant
        publish_discovery()
       
        # Publish online status
        mqtt.publish(TOPIC_STATUS, "online", retain=True)
       
        return True
    except Exception as e:
        print(f"MQTT connection failed: {e}")
        return False

# ========== MAIN LOOP ==========
def main():
    # Initialize hardware
    led1.value(0)
    led2.value(0)
    led3.value(0)
    set_servo_angle(90)  # Center position
   
    # Connect to WiFi
    connect_wifi()
   
    # Connect to MQTT
    if not connect_mqtt():
        print("FATAL: Could not connect to MQTT. Restarting...")
        machine.reset()
   
    print(f"\n=== Device Ready ===")
    print(f"Device ID: {DEVICE_ID}")
    print(f"MQTT Topics:")
    print(f"  LED1: {TOPIC_LED1}")
    print(f"  LED2: {TOPIC_LED2}")
    print(f"  LED3: {TOPIC_LED3}")
    print(f"  Servo: {TOPIC_SERVO}")
    print("\nWaiting for commands...\n")
   
    # Main loop
    last_ping = time.time()
    while True:
        try:
            # Check for MQTT messages
            mqtt.check_msg()
           
            # Send keep-alive every 30 seconds
            if time.time() - last_ping > 30:
                mqtt.publish(TOPIC_STATUS, "online", retain=True)
                last_ping = time.time()
                status_led.value(not status_led.value())  # Blink status LED
                print("Heartbeat sent")
           
            time.sleep(0.1)  # Small delay to prevent watchdog issues
           
        except Exception as e:
            print(f"Error in main loop: {e}")
            print("Reconnecting MQTT...")
            try:
                mqtt.disconnect()
            except:
                pass
            time.sleep(5)
            if connect_mqtt():
                print("Reconnected successfully")
            else:
                print("Failed to reconnect. Restarting...")
                machine.reset()

# ========== RUN THE SCRIPT ==========
if __name__ == "__main__":
    main()
