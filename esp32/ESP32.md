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

Edit configuration (WiFi credentials, MQTT broker IP)

Upload umqtt.simple library to the device

Run the script - it will auto-start on boot


# Boot Automation
To make it run automatically on power-up, save as boot.py or add to main.py and use:

```
import main
main.main()
```