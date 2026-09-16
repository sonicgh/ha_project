# Smart Apartment System — Overview

## 1. Project Introduction

This project turns a standard apartment into a **smart apartment** using off-the-shelf hardware and open-source software. An ESP32 microcontroller controls physical things (lights, blinds) and talks wirelessly to **Home Assistant**, the brain of the system. A web dashboard lets you control everything from any browser. Commands travel through **MQTT**, a lightweight messaging protocol built for IoT devices, and every state change is saved in **PostgreSQL** for history and analysis.

**In short:** physical switches + a smart brain + a web remote + a memory = a fully customizable smart home.

---

## 2. The Stack: What We're Using

| Layer | Tool | Purpose |
|---|---|---|
| **Brain** | Home Assistant | Central controller — receives commands, runs automations, talks to everything |
| **Messenger** | Mosquitto (MQTT) | Lightweight message broker — passes messages between devices and HA |
| **Memory** | PostgreSQL | Database that stores every state change (lights on/off, temperature, etc.) |
| **Switches & Sensors** | ESP32 microcontroller | Physical hardware — buttons, LEDs, servos, sensors |
| **Remote Control** | Web Dashboard | Browser-based UI — Alpine.js + HTMX + Tailwind CSS |
| **Orchestration** | Docker Compose | Runs all services in containers — one command to start everything |

---

## 3. How They All Fit Together

```
                   ┌──────────────────────┐
                   │   Web Dashboard       │  ← Open in browser (localhost:3000)
                   │   (Alpine.js/HTMX)    │
                   └──────┬───────────────┘
                          │ REST API + WebSocket
                          │ (HTTP + real-time)
                          ▼
┌─────────────────────────────────────────────┐
│           Home Assistant (HA)               │  ← The brain
│  • REST API (turn things on/off)            │
│  • WebSocket (push live updates)            │
│  • Automations engine                       │
│  • Recorder (PostgreSQL)                    │
└──────┬──────────────────────┬──────────────┘
       │ MQTT                 │ SQL
       ▼                      ▼
┌──────────────┐    ┌──────────────────┐
│  Mosquitto   │    │   PostgreSQL     │  ← History of everything
│  (MQTT)      │    │   (Database)     │
└──────┬───────┘    └──────────────────┘
       │ WiFi
       ▼
┌──────────────────┐
│  ESP32 Devices   │  ← Physical hardware
│  • LEDs          │     (in your apartment)
│  • Servos        │
│  • Sensors       │
└──────────────────┘
```

**Key point:** Everything talks to Home Assistant. Nothing talks directly to anything else. HA is the middleman.

---

## 4. How It Works (End to End)

### Scenario: You flip a light switch in the dashboard

1. **You click** a toggle on the web dashboard
2. **Dashboard** sends `POST /api/services/light/turn_on` to HA with your auth token
3. **HA** validates the token, then publishes `"ON"` to Mosquitto on topic `homeassistant/light/esp32_xxx/led1/command`
4. **Mosquitto** delivers the message to the ESP32 over WiFi
5. **ESP32** receives it, turns GPIO13 HIGH → LED lights up
6. **ESP32** publishes back `"ON"` on the state topic
7. **HA** receives the state update, records it in PostgreSQL
8. **HA** pushes a `state_changed` event via WebSocket to your dashboard
9. **Dashboard** updates the toggle to show "ON"

**Total round-trip:** ~50-200ms. Feels instant.

### Meanwhile, automatically:
- Every 30 seconds, the ESP32 publishes a heartbeat (`online`) and telemetry (WiFi signal strength, uptime)
- The `esp_health` custom component monitors this and creates `last_seen`, `rssi`, `uptime` sensors in HA
- All state changes for lights, switches, sensors, and binary_sensors are recorded in PostgreSQL (30-day retention)

---

## 5. How to Start and Trigger Things

### Start the System (one-time)

```bash
# 1. Start all Docker containers (HA + PostgreSQL + Mosquitto)
docker-compose up -d

# 2. Serve the dashboard locally (in a separate terminal)
python3 -m http.server 3000 -d frontend
```

Then open http://localhost:3000 in your browser, paste your HA access token, and the dashboard loads in real time.

### Stop the System

```bash
# Stop everything
docker-compose down

# Or stop just the dashboard with Ctrl+C in its terminal
```

### From the Dashboard
- Click toggles → HA REST API → MQTT → ESP32
- The "Execute" button on switch-type devices
- New device form: paste any HA entity ID (e.g., `light.kitchen`) and it appears in the dashboard

### From MQTT Directly (no dashboard)
```bash
# Turn LED1 ON
mosquitto_pub -h localhost -t "homeassistant/light/esp32_device_a0b7652a758c/led1/command" -m "ON"

# Move servo to 90 degrees
mosquitto_pub -h localhost -t "homeassistant/cover/esp32_device_a0b7652a758c/servo/command" -m "90"
```

### From Python Scripts (in `python_api_requests/`)
```bash
python send_command.py light.turn_on light.esp32_controller_esp32_controller_led_1
```

### From HA Automations (planned but not yet built)
- Weather fetch every 10 minutes (Open-Meteo API)
- Temperature comparison logic with smart suggestions

---

## 6. How to Add More Things

### Add a new LED/sensor to the existing ESP32
1. Wire the new component to a free GPIO pin
2. Edit `esp32/main.py` — add a new MQTT topic and discovery message
3. Re-flash the ESP32
4. The dashboard finds the new entity automatically via HA's API

### Add a whole new ESP32 device
1. Flash MicroPython + the firmware files to a new ESP32 board
2. Set its WiFi credentials in `config.py`
3. Power it on — it auto-discovers itself to HA via MQTT
4. Add its device ID to `configuration.yaml` under `esp_health` for health monitoring
5. Add its entity IDs to the dashboard using the "New Device" button

### Add any non-ESP32 device (Zigbee, Z-Wave, Wi-Fi plug, etc.)
1. Connect it to Home Assistant using any of HA's 2000+ built-in integrations
2. Once HA recognizes it, get its entity ID from Developer Tools → States
3. Paste that entity ID into the dashboard's "New Device" form

### Add a new dashboard feature
1. Edit `frontend/index.html` — add a new case in `getDeviceType()` and a new card template
2. The dashboard already classifies entities as: toggle (lights), display (sensors), or execute (switches)

---

## 7. Possible Replacements — If You Wanted to Swap Things Out

### Home Assistant → Alternatives

| Alternative | Why Consider It | Trade-offs |
|---|---|---|
| **openHAB** | Java-based, very mature, runs anywhere | Bigger learning curve, smaller community |
| **Node-RED** | Visual flow programming, extremely easy to prototype | Not a full automation platform — needs add-ons for dashboards, auth, etc. |
| **ioBroker** | Very popular in Europe, strong IoT focus | Less English-language community, JavaScript-based |
| **ESPHome** | Tight ESP32 integration, YAML-defined devices | Only works with ESP devices, not a general hub for Zigbee/Z-Wave etc. |
| **building your own** (Flask/FastAPI + MQTT) | Total control | Massive effort to replicate HA's 2000+ integrations, auth, dashboards, history |

**Bottom line:** Home Assistant is hard to beat for a general-purpose smart home. Its ecosystem (2000+ integrations, mature REST API, WebSocket, companion apps) would take years to replicate. The main reasons to switch would be: you need something even lighter (ESPHome), or you prefer visual programming (Node-RED).

### Mosquitto (MQTT) → Alternatives

| Alternative | Why Consider It | Trade-offs |
|---|---|---|
| **EMQX** | Clustering, higher scalability, built-in rule engine | Heavier (Erlang/OTP), overkill for a home setup |
| **VerneMQ** | Clustering, high availability | Same as EMQX — enterprise features for a home scenario |
| **RabbitMQ** | AMQP + MQTT plugin, more general-purpose messaging | Not MQTT-first, more complex config |
| **NanoMQ** | Ultra-lightweight C implementation, designed for edge/IoT | Newer, smaller community |
| **HA's built-in MQTT (add-on)** | Simplest possible — no separate broker config | Only works inside HA's ecosystem |

**Bottom line:** Mosquitto is the gold standard for home MQTT — tiny (~2MB), battle-tested, zero-config in this setup. EMQX is the only realistic replacement if you later need thousands of devices or clustered brokers.

### PostgreSQL → Alternatives

| Alternative | Why Consider It | Trade-offs |
|---|---|---|
| **SQLite** (HA default) | No separate container, simpler setup | Slower with many devices, no concurrent access |
| **MySQL/MariaDB** | Familiar to many developers | Less native HA support than PostgreSQL |
| **InfluxDB + Grafana** | Purpose-built for time-series data, beautiful dashboards | HA doesn't natively support it — requires add-on |

### ESP32 → Alternatives

| Alternative | Why Consider It | Trade-offs |
|---|---|---|
| **ESP32-C3** | Newer, cheaper, RISC-V core | Fewer GPIO pins, different architecture |
| **Raspberry Pi Pico W** | Cheaper, MicroPython-native | Less WiFi reliability, smaller community |
| **M5Stack** | All-in-one with display, buttons, battery | 10x the cost |
| **Arduino + WiFi shield** | Traditional Arduino ecosystem | More wiring, less capable |

### Firmware Approach → Alternatives

| Alternative | Why Consider It | Trade-offs |
|---|---|---|
| **PlatformIO + Arduino (C++)** | More performance, lower power | More complex build chain, harder to iterate |
| **ESP-IDF (C)** | Maximum performance, full ESP32 API | Steep learning curve, no REPL |
| **Tasmota/ESPHome** | No coding — flash and configure | Limited to predefined device behaviors |

---

## 8. Architecture Diagram (Logical Flow)

```
┌──────────────┐     REST/WS     ┌──────────────────┐     MQTT      ┌──────────────┐
│   Browser    │ ◄──────────────► │  Home Assistant  │ ◄───────────► │   Mosquitto   │
│  (Dashboard) │                  │  (The Brain)      │              │   (MQTT)      │
└──────────────┘                  └──────────┬───────┘              └──────┬─────────┘
                                              │                            │
                                              │ SQL                        │ WiFi
                                              ▼                            ▼
                                       ┌──────────────┐           ┌──────────────┐
                                       │  PostgreSQL   │           │    ESP32     │
                                       │  (History)    │           │  (Hardware)  │
                                       └──────────────┘           └──────────────┘
```

**Three Docker containers** (one command to start):
- `ha-core` (Home Assistant) — port 8123
- `ha-postgres` (PostgreSQL) — port 5432
- `ha-mosquitto` (Mosquitto) — port 1883

**One process on your host machine:**
- `python3 -m http.server 3000` — serves the dashboard

**One or more ESP32 devices on your WiFi:**
- Run MicroPython firmware that connects to Mosquitto and auto-discovers to HA

---

## 9. Key Design Decisions

1. **MQTT over direct GPIO/mesh** — because MQTT decouples the physical device from the controller. You can replace the ESP32, change the dashboard, or swap the database without touching anything else.

2. **PostgreSQL over SQLite** — because SQLite can't handle concurrent readers (multiple dashboard tabs + HA + scripts all reading/writing history). PostgreSQL handles this natively.

3. **HA auto-discovery via MQTT** — the ESP32 publishes its capabilities when it boots. No manual configuration needed for new devices. Plug-and-play.

4. **Separate dashboard (not HA's built-in)** — because the custom Alpine.js/HTMX dashboard is faster, lighter, and fully customizable without HA's UI constraints.

5. **Docker Compose** — because it makes the whole system reproducible. One `docker-compose up -d` and everything runs, regardless of the host OS.
