# Project Plan: ESP32 Home Automation with Home Assistant, Weather AI Suggestions & Logging

## 1. Executive Summary
Build a scalable, local-first home automation system using an ESP32 as the sensing/actuating node. Home Assistant (HA) provides the UI, device management, and automation engine. The ESP32 communicates via MQTT. A local weather service (or free API) fetches external temperature; HA compares it with indoor sensor data and optionally calls a local LLM for comfort suggestions. Logs are centralized in HA and accessible from a PC.

## 2. High-Level System Architecture (Text Diagram)
```
[ESP32] ---(MQTT)---> [MQTT Broker (Mosquitto)] ---> [Home Assistant]
   |                          |                              |
   |                          |                              |
   +-- LED                    +-- Logs to InfluxDB/File      +-- UI (PC browser)
   +-- Switch                                               +-- Automation engine
   +-- Servo motor                                          +-- LLM integration (optional)
   +-- Temp sensor (DS18B20/DHT22)                          +-- Weather API (Open-Meteo)
```

## 3. Requirements
```
Functional Requirements
ID	  Requirement	                                                                          Priority
FR1	  Control LED (on/off) from HA dashboard	                                                High
FR2	  Read physical switch state and trigger actions	                                        High
FR3	  Position servomotor (0° to 180°) from HA	                                              Medium
FR4	  Read indoor temperature every 30s and send to HA	                                      High
FR5	  Fetch city external temperature (internet) every 10 min	                                High
FR6	  Compare indoor vs outdoor temp and suggest action (e.g., “Open window if too hot”)	    High
FR7	  Store logs of all events + sensor readings	                                            High
FR8	  Monitor system from any PC on local network via HA web UI	                              High
FR9	  (Optional) Send comparison data to local LLM (Ollama) for natural language suggestion	  Low
FR10	Allow adding new devices (Zigbee, additional ESPs) without rewriting core	              High
```

```
Non-Functional Requirements
ID	  Requirement
NFR1	Response time < 1s for local control
NFR2	ESP32 shall reconnect on WiFi loss
NFR3	Logs retained for 30 days
NFR4	HA runs on low-power device (Raspberry Pi 4 or old PC)
NFR5	MQTT messages encrypted with TLS (optional but recommended)
```

## 4. Hardware & Tools Comparison

```
Component	          Options	                                Selected	                    Reason
Microcontroller	    ESP32 Dev Board, ESP32-C3, M5Stack	    ESP32 Dev Board v4 (38 pins)	Widely supported, enough GPIO, cheap (≈$10)
Temperature sensor	DHT22, DS18B20, BME280	                DS18B20	                      Digital, accurate, waterproof possible, 1-wire bus for multiple sensors
LED	                5mm red LED + 220Ω resistor	            Standard 5mm	                Simple indicator
Switch	            Tactile push button, toggle switch	    Tactile button	              Easy to debounce in software
Servo motor	        SG90, MG995	                            SG90	                        Small, 5V, suitable for prototypes
PC for HA	          Raspberry Pi 4 (4GB), old laptop, NUC	  Raspberry Pi 4 (4GB)	        Low power, community support, runs HA OS
MQTT Broker	        Mosquitto, EMQX	                        Mosquitto	                    Lightweight, native HA add-on
Database for logs	  SQLite (default HA), InfluxDB	          InfluxDB + Grafana (optional)	Time-series logs, better retention/queries
```

## 5. Software Stack & Selected Tools

```
Layer	                Tech	                                                    Purpose
ESP32 firmware	      PlatformIO + Arduino framework	                          C++ code, easy MQTT libraries
MQTT communication	  PubSubClient library	                                    ESP32 → Broker
MQTT Broker	          Mosquitto (HA add-on)	                                    Central message bus
Home Assistant	      HA OS (full install)	                                    UI, automations, entity registry
Weather source	      Open-Meteo (free, no API key)	                            City external temp
LLM integration	      Ollama (run on same RPi or PC) + HA’s Ollama integration	Suggestion generation (optional)
Logging	              HA’s recorder + InfluxDB (optional)	                      Historical data
Monitoring from PC	  Any browser → http://<HA_IP>:8123	                        Full dashboard
```

```
ESP32 Pin Mapping (Example)
Device        GPIO	    Notes
LED	          GPIO 2	  Built-in LED on many boards
Switch	      GPIO 4	  Input with pull-up
Servo signal	GPIO 5	  PWM capable
DS18B20 data	GPIO 18	  With 4.7k pull-up resistor
```

## 6. MQTT Topics Structure (Scalable)

```
Topic	Direction	Payload Example
home/livingroom/led/set	      HA → ESP32	            ON / OFF
home/livingroom/led/state	   ESP32 → HA	            ON / OFF (retain)
home/livingroom/switch/state	ESP32 → HA	            0 or 1
home/livingroom/servo/set	   HA → ESP32	            0-180
home/livingroom/temp	         ESP32 → HA	            22.5
home/weather/external	      HA → HA (automation)	   28.1
```

##  7. Automation & LLM Suggestion Logic (YAML for HA)

```
# automation.yaml extract
- alias: Compare indoor vs outdoor temp
  trigger:
    platform: state
    entity_id: sensor.livingroom_temp
  action:
    - service: weather.get_forecast
      data:
        entity_id: weather.openmeteo_home
    - service: input_text.set_value
      target:
        entity_id: input_text.temp_suggestion
      data:
        value: >
          {% if states('sensor.livingroom_temp')|float > states('sensor.external_temp')|float + 2 %}
            Suggestion: It's warmer inside. Open a window or use a fan.
          {% elif states('sensor.livingroom_temp')|float < states('sensor.external_temp')|float - 2 %}
            Suggestion: It's colder inside. Close windows or add heating.
          {% else %}
            Suggestion: Temperatures are balanced. No action needed.
          {% endif %}
# Optional: send this text to Ollama -> "Rephrase this like a smart assistant: ..."
```

## 8. Logging & Monitoring from PC

```
Log type	                                       Retention	Access method
All sensor readings	                           30 days	   HA History panel → PC browser
Device state changes (LED on/off, servo moves)	30 days	   HA Logbook
ESP32 connection events	                        30 days	   HA System logs + MQTT logs
Custom application logs	                        7 days	   ESP32 via serial + remote syslog (optional)
```

### PC Monitoring:
```
-URL: http://<raspberry_pi_ip>:8123
-Dashboard: Create a dedicated “Living Room” card with temp graph, LED toggle, servo slider, suggestion text.
-SSH access to ESP32 logs: not required from PC (use HA).
```


## 9. Timeline & Milestones (Total: 3 weeks, part-time)

```
Week	Days	Task	                                                                                                Deliverable
1	   1-2	Set up Raspberry Pi: install HA OS, configure basic network, access from PC	                        HA login page accessible
1	   3-4	Install Mosquitto MQTT broker (HA add-on), configure user/password, test with MQTT Explorer from PC	MQTT working
1	   5-7	ESP32 code: connect to WiFi, MQTT, read switch, control LED	                                          LED toggles from HA
2	   1-2	Add DS18B20 sensor → publish temp to MQTT	                                                            Temp visible in HA
2	   3-4	Add servo control via MQTT	                                                                           Slider in UI moves servo
2	   5-7	Integrate Open-Meteo weather automation + comparison logic	                                          Suggestion text appears in HA
3	   1-2	Configure logging (enable recorder, optionally InfluxDB)	                                             Charts with 30-day history
3	   3-4	(Optional) Install Ollama on RPi, connect HA OpenAI integration (custom endpoint)	                  LLM rephrases suggestions
3	   5-7	Final dashboard design, testing, documentation	                                                      Complete working system + PC monitoring guide
```


## 10. Risks & Mitigations

```

Risk	                                    Probability	   Impact	Mitigation
ESP32 disconnects from WiFi	            Medium	      High	   Enable auto-reconnect, watchdogs, MQTT last will
Weather API changes	                     Low	         Medium	Use stable API (Open-Meteo), cache results
Servo jitter due to MQTT latency	         Medium	      Low	   Use local ESP32 ramp-up, accept final position
LLM too slow on RPi 4	                  Medium	      Low	   Make LLM optional; fallback to rule-based suggestions
Logs fill SD card	                        Low	         Medium	Configure retention policy in HA (30d)
```


## 11. Next Steps & Recommendation from the PM
```
✅ Start with minimal viable product:
ESP32 + LED + Switch → MQTT → HA (on RPi) → PC browser.
Then add temp sensor → external weather → comparison logic.
Add servo last.
Integrate LLM only if you have spare RAM on RPi (Ollama needs ~4GB). For a small project, the built-in text suggestion is sufficient.
```