# Pin connection

ESP32 Pin    →    Component
--------------------------------
GPIO13       →    LED1 (Anode)
GPIO12       →    LED2 (Anode)
GPIO14       →    LED3 (Anode)
GPIO15       →    Servo (Signal wire)
3.3V/GND     →    LEDs (through 220Ω resistors)
5V/GND       →    Servo (power)

# Testing Commands

Once running, you can control everything via MQTT:

```
# Turn LED1 ON
mosquitto_pub -t "homeassistant/light/esp32_device_xxx/led1/command" -m "on"

# Turn LED2 OFF
mosquitto_pub -t "homeassistant/light/esp32_device_xxx/led2/command" -m "off"

# Move servo to 0°
mosquitto_pub -t "homeassistant/cover/esp32_device_xxx/servo/command" -m "0"

# Move servo to 90°
mosquitto_pub -t "homeassistant/cover/esp32_device_xxx/servo/command" -m "90"

# Open servo (180°)
mosquitto_pub -t "homeassistant/cover/esp32_device_xxx/servo/command" -m "open"
```

# Home Assistant Integration

The script automatically publishes discovery topics, so Home Assistant will automatically detect and add:

3 light entities (LEDs)

1 cover/garage door entity (Servo)

No manual configuration needed in Home Assistant!

Setup Instructions
Flash MicroPython to your ESP32 (if not already done)

Upload the script using ampy, rshell, or Thonny IDE

Configuration Options:
Option 1: Edit credentials directly in main.py (lines 10-17)
Option 2: Use separate config.py file (recommended for easier updates)
   - Update config.py with your WiFi and MQTT settings
   - main.py will automatically read from config.py

Upload umqtt.simple library to the device

Run the script - it will auto-start on boot via boot.py

Connection Information:
- Access ESP32 via Thonny IDE: Select the correct COM/serial port
- Typical ports: COM3, COM4 (Windows) or /dev/ttyUSB0, /dev/ttyACM0 (Linux/Mac)
- Baud rate: 115200 (standard for MicroPython)
- Once connected, you can use Thonny's interface to upload files and monitor output


# Boot Automation
To make it run automatically on power-up, save as boot.py or add to main.py and use:

```
import main
main.main()
```