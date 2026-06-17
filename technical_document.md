# Smart Apartment — Technical Document

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Project Structure](#2-project-structure)
3. [System Architecture](#3-system-architecture)
4. [Docker Infrastructure](#4-docker-infrastructure)
5. [Backend — Home Assistant](#5-backend--home-assistant)
6. [Backend — PostgreSQL](#6-backend--postgresql)
7. [Backend — Mosquitto MQTT Broker](#7-backend--mosquitto-mqtt-broker)
8. [ESP32 Firmware (IoT Layer)](#8-esp32-firmware-iot-layer)
9. [Frontend — Dashboard](#9-frontend--dashboard)
10. [Communication Protocol](#10-communication-protocol)
11. [Data Flow & Lifecycle](#11-data-flow--lifecycle)
12. [MQTT Topics Map](#12-mqtt-topics-map)
13. [Storage & Persistence](#13-storage--persistence)
14. [Operations & Scripts](#14-operations--scripts)
15. [Security Model](#15-security-model)
16. [Planned Extensions](#16-planned-extensions)
17. [Paradigm Used](#17-paradigm-used)

---

## 1. Technology Stack

| Layer | Technology | Version | Role |
|---|---|---|---|
| **Container orchestration** | Docker Compose | 3.8 | Multi-container lifecycle management |
| **Home automation platform** | Home Assistant | 2026.3.2 (`ghcr.io`) | Core orchestrator, REST API, WebSocket, Web UI |
| **Database** | PostgreSQL | 15 Alpine | Entity state history, 30-day retention |
| **MQTT Broker** | Eclipse Mosquitto | 2 | Message bus between HA and ESP32 |
| **IoT firmware** | MicroPython + `umqtt.simple` | — | ESP32 device control and telemetry |
| **Frontend framework** | Alpine.js 3 | 3.x (CDN) | Reactive state management and UI binding |
| **AJAX library** | HTMX | 1.9.12 (CDN) | Partial page updates from HTML attributes |
| **CSS framework** | Tailwind CSS | CDN | Utility-first styling |
| **Icons** | Font Awesome 6 | CDN | UI iconography |
| **Python HTTP server** | `http.server` (stdlib) | 3.x | Static file serving for the frontend (dev) |

---

## 2. Project Structure

```
ha_project/
├── docker-compose.yml                     # Defines 3 containers: postgres, mosquitto, homeassistant
├── AGENTS.md                              # Opencode agent instructions for AI-assisted development
├── technical_document.md                  # This file
├── frontend/
│   ├── index.html                         # Single-page dashboard (Alpine.js + HTMX + Tailwind)
│   └── style.css                          # Dashboard custom styles (card, toggle, overlay)
├── homeassistant_config/
│   ├── configuration.yaml                 # HA config: CORS, PostgreSQL recorder, history, logbook
│   ├── entrypoint.sh                      # Custom entrypoint: installs psycopg2, starts HA
│   ├── .HA_VERSION                        # Pinned version file (2026.3.2)
│   ├── .storage/                          # HA runtime state (auth, entities, devices, config entries)
│   │   ├── auth                           # 5 users, credentials, refresh tokens
│   │   ├── core.config_entries            # 2 entries: backup (system) + MQTT (user)
│   │   ├── core.device_registry           # 2 devices: Backup (service) + ESP32 Controller
│   │   ├── core.entity_registry           # 9 entities: 4 backup + 5 ESP32 (3 lights, 1 cover, 1 sensor)
│   │   ├── core.restore_state             # Restore state for backup event + 3 lights (all off)
│   │   ├── http                           # CORS, port 8123, SSL profile, IP ban
│   │   └── onboarding                     # Onboarding completed
│   ├── blueprints/
│   │   └── automation/homeassistant/
│   │       ├── motion_light.yaml          # Motion-activated light blueprint
│   │       └── notify_leaving_zone.yaml   # Zone-leaving notification blueprint
│   │   └── script/homeassistant/
│   │       └── confirmable_notification.yaml # Actionable notification blueprint
│   └── custom_components/
│       └── esp32_controller/              # (compiled bytecode, no source available)
├── esp32/
│   ├── boot.py                            # Auto-runs main() on power-up
│   ├── main.py                            # Full firmware: WiFi, MQTT, GPIO, HA discovery (291 LoC)
│   ├── config.py                          # WiFi SSID/password, MQTT broker address/port
│   └── ESP32.md                           # Pinout and testing reference
├── scripts/
│   ├── service_restart.sh                 # Restart HA container with health check (77 LoC)
│   ├── ha_configuration_backup.sh         # Config tar.gz + PostgreSQL dump (64 LoC)
│   └── container_log_monitoring.sh        # Log checking, following, stats (165 LoC)
├── documents/
│   ├── 1-ha_flowchart.png                 # Architecture flowchart (binary)
│   ├── 2-ha_flowchart_device_example.md   # Text flowchart: ESP32 loop + HA automations
│   ├── 3-data_flow_per_layer.md           # Per-layer data flow table (5 layers)
│   ├── 4-pseudocode_ha.md                 # HA automation pseudocode (3 automations)
│   ├── 5-system_states_tables.md          # System state definitions (6 states)
│   ├── 6-pseudocode_esp32.md              # ESP32 firmware pseudocode
│   ├── classes_diagram_v1.png             # Class diagram (binary)
│   ├── ha_planning_document_1.pdf         # Planning doc (binary)
│   └── ha_planning_document_2.md          # Full project plan, requirements, timeline
├── python_api_request/                    # Empty — reserved for future API scripts
├── logs/                                  # Runtime log output (gitignored)
├── backups/                               # Backup output (gitignored)
└── .gitignore                             # 265 lines: Python, Docker, HA runtime artifacts
```

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BROWSER (http://localhost:3000)                       │
│  Alpine.js 3 + HTMX 1.9 + Tailwind CSS + Font Awesome 6                     │
│  Auth via Long-Lived Access Token from HA profile                            │
└──────────────────────┬──────────────────────────────────────────────────────┘
                       │
                       │ REST: GET /api/states, POST /api/services/{domain}/{action}
                       │ WS:   ws://localhost:8123/api/websocket (state_changed events)
                       │ Port: 8123
                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    HOME ASSISTANT (Docker container)                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐   │
│  │ REST API + WS   │  │ Automation Engine│  │ MQTT Client (Paho)         │   │
│  │ Port 8123       │  │ + Entity Registry│  │ Subscribes to state topics │   │
│  └─────────────────┘  └──────────────────┘  └───────────┬────────────────┘   │
│                                                          │                    │
│                          ┌───────────────────────────┐   │                    │
│                          │ Recorder (psycopg2)        │   │                    │
│                          │ Writes states table        │   │                    │
│                          └───────────┬───────────────┘   │                    │
└──────────────────────────────────────┼───────────────────┼────────────────────┘
                                       │                   │
                 PostgreSQL (5432)      │     MQTT (1883)   │
                 Internal Docker net   │     Internal net   │
                                       ▼                   ▼
              ┌──────────────────────┐    ┌──────────────────────────┐
              │   PostgreSQL 15      │    │  Mosquitto MQTT Broker 2 │
              │   ha-postgres:5432   │    │  ha-mosquitto:1883       │
              │   DB: homeassistant  │    │  Anonymous access        │
              │   User: homeassistant│    │  Persistence enabled     │
              └──────────────────────┘    └───────────┬──────────────┘
                                                      │ MQTT over WiFi
                                                      ▼
              ┌───────────────────────────────────────────────────────────┐
              │              ESP32 (MicroPython)                          │
              │  WiFi: house_network                                      │
              │  MQTT: 192.XXX.YY.ZZZ:1883                                │
              │  Hardware:                                                │
              │    GPIO13 → LED1 (220Ω → 3.3V)                           │
              │    GPIO12 → LED2 (220Ω → 3.3V)                           │
              │    GPIO14 → LED3 (220Ω → 3.3V)                           │
              │    GPIO15 → Servo (PWM 50Hz, 5V power)                   │
              │    GPIO2  → Status LED (built-in, blinks on activity)     │
              │  Behavior:                                                │
              │    1. Boot → WiFi → MQTT connect                          │
              │    2. Publish HA discovery messages (auto-config)          │
              │    3. Subscribe to command topics                          │
              │    4. Main loop: check_msg(), heartbeat every 30s          │
              └───────────────────────────────────────────────────────────┘
```

### Communication Layers

| Layer | Component | Input | Output |
|---|---|---|---|
| **Perception** | ESP32 | Physical temperature, switch state | Digital values via MQTT |
| **Communication** | MQTT (Mosquitto) | Topic + payload from ESP32/HA | Message routing to subscribers |
| **Processing** | Home Assistant Core | MQTT messages, API calls | Entity updates, automations, API responses |
| **Actuation** | ESP32 | MQTT commands (LED on/off, servo angle) | Physical device state change |
| **Visualization** | Browser (Alpine.js + HTMX) | HA API + WebSocket state changes | Rendered HTML dashboard |

---

## 4. Docker Infrastructure

### 4.1 docker-compose.yml

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    container_name: ha-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: homeassistant
      POSTGRES_PASSWORD: hass_password
      POSTGRES_DB: homeassistant
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  mosquitto:
    image: eclipse-mosquitto:2
    container_name: ha-mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"
    volumes:
      - mosquitto_data:/mosquitto/data
      - mosquitto_log:/mosquitto/log
    command: >
      sh -c "mkdir -p /mosquitto/config &&
      echo 'listener 1883 0.0.0.0' > /mosquitto/config/mosquitto.conf &&
      echo 'allow_anonymous true' >> /mosquitto/config/mosquitto.conf &&
      echo 'persistence true' >> /mosquitto/config/mosquitto.conf &&
      echo 'persistence_location /mosquitto/data/' >> /mosquitto/config/mosquitto.conf &&
      mosquitto -c /mosquitto/config/mosquitto.conf"

  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:stable
    container_name: homeassistant
    restart: unless-stopped
    depends_on:
      - postgres
      - mosquitto
    volumes:
      - ./homeassistant_config:/config
      - ./homeassistant_config/entrypoint.sh:/entrypoint.sh
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "8123:8123"
    environment:
      - TZ=Europe/London
    privileged: true
    entrypoint: /bin/sh /entrypoint.sh

volumes:
  postgres_data:
  mosquitto_data:
  mosquitto_log:
```

### 4.2 Service Matrix

| Service | Container Name | Image | Host Port | Internal Port | Depends On |
|---|---|---|---|---|---|
| PostgreSQL | `ha-postgres` | `postgres:15-alpine` | 5432 | 5432 | — |
| Mosquitto | `ha-mosquitto` | `eclipse-mosquitto:2` | 1883 | 1883 | — |
| Home Assistant | `homeassistant` | `ghcr.io/home-assistant/home-assistant:stable` | 8123 | 8123 | postgres, mosquitto |

### 4.3 Network Topology

All three containers communicate over the default Docker bridge network using internal hostnames:
- HA connects to `ha-postgres:5432` for the recorder
- HA connects to `ha-mosquitto:1883` for MQTT
- External clients (frontend browser, PostgreSQL tools, MQTT clients) connect via `localhost` on mapped ports

### 4.4 Entrypoint (`entrypoint.sh`)

```bash
#!/bin/bash
set -e
echo "Installing psycopg2-binary..."
pip install psycopg2-binary -q
echo "Starting Home Assistant..."
exec python -m homeassistant --config /config
```

This entrypoint:
1. Installs the `psycopg2-binary` PostgreSQL driver at container start (required for the recorder integration)
2. Launches Home Assistant with `--config /config` which points to the mounted `homeassistant_config/` directory

---

## 5. Backend — Home Assistant

### 5.1 Configuration (`configuration.yaml`)

```yaml
# CORS — allows the frontend at localhost:3000 to call the HA API
http:
  cors_allowed_origins:
    - http://localhost:3000

# Recorder — entity state history in PostgreSQL
recorder:
  db_url: postgresql://homeassistant:hass_password@ha-postgres:5432/homeassistant
  purge_keep_days: 30
  include:
    domains:
      - light
      - switch
      - sensor
      - binary_sensor
  exclude:
    entities:
      - sun.sun
      - zone.home

history:
logbook:
```

### 5.2 APIs Exposed

| Method | Endpoint | Purpose | Auth Required |
|---|---|---|---|
| `GET` | `/api/` | Token validation | Yes (Bearer) |
| `GET` | `/api/states` | Fetch all entity states | Yes |
| `GET` | `/api/states/{entity_id}` | Fetch single entity state | Yes |
| `POST` | `/api/services/{domain}/{action}` | Execute service (turn_on, turn_off, toggle) | Yes |
| `WS` | `/api/websocket` | Real-time state change events | Yes (auth message) |

### 5.3 Registered Entities (from `.storage/core.entity_registry`)

| Entity ID | Domain | Friendly Name | Platform | Unique ID |
|---|---|---|---|---|
| `cover.esp32_controller_esp32_controller_servo` | cover | esp32_controller Servo | mqtt | `esp32_device_a0b7652a758c_servo` |
| `light.esp32_controller_esp32_controller_led_1` | light | esp32_controller LED 1 | mqtt | `esp32_device_a0b7652a758c_led1` |
| `light.esp32_controller_esp32_controller_led_2` | light | esp32_controller LED 2 | mqtt | `esp32_device_a0b7652a758c_led2` |
| `light.esp32_controller_esp32_controller_led_3` | light | esp32_controller LED 3 | mqtt | `esp32_device_a0b7652a758c_led3` |
| `event.backup_automatic_backup` | event | Automatic backup | backup | `automatic_backup_event` |
| `sensor.backup_backup_manager_state` | sensor | Backup Manager state | backup | `backup_manager_state` |
| `sensor.backup_next_scheduled_automatic_backup` | sensor | Next scheduled backup | backup | `next_scheduled_automatic_backup` |
| `sensor.backup_last_successful_automatic_backup` | sensor | Last successful backup | backup | `last_successful_automatic_backup` |
| `sensor.backup_last_attempted_automatic_backup` | sensor | Last attempted backup | backup | `last_attempted_automatic_backup` |

### 5.4 Config Entries (from `.storage/core.config_entries`)

| Entry ID | Domain | Source | Title | Data |
|---|---|---|---|---|
| `01KTQK3M7625JHWM70W9HR4YYV` | backup | system | Backup | `{}` |
| `01KTQKQFGX8JZ03M6DX1DTGDEC` | mqtt | user | 192.XXX.YY.ZZZ | `{"broker": "192.XXX.YY.ZZZ", "port": 1883}` |

### 5.5 Registered Devices (from `.storage/core.device_registry`)

| Device ID | Name | Manufacturer | Model | Identifiers |
|---|---|---|---|---|
| `e05d4f5e89d0451841ec5a472d2912a0` | Backup | Home Assistant | Home Assistant Backup | `[["backup", "backup_manager"]]` |
| `77df92b90f0d2c39aabf8ccc6b197617` | esp32_controller | Custom | ESP32 Controller | `[["mqtt", "esp32_device_a0b7652a758c"]]` |

### 5.6 Authentication (from `.storage/auth`)

The auth store contains:
- **5 users**: 1 owner (`apto1816`), 4 system/read-only users
- **Credentials**: Hashed passwords for each user
- **Refresh tokens**: Including long-lived access tokens used by the frontend
- **Long-lived access token**: A persistent token (generated from `/profile`) that the frontend stores in `localStorage` and uses for all API and WebSocket calls

### 5.7 Automations (planned, from `documents/4-pseudocode_ha.md`)

Three automations are designed but not yet deployed:

1. **Weather fetch** (every 10 min): Calls Open-Meteo API, stores external temperature in `input_number.external_temp`
2. **Temperature comparison**: Triggers on state change of indoor temp or external temp, compares values, generates a suggestion text (e.g., "Open window if too hot"), optionally sends to Ollama LLM for natural language rephrasing
3. **State logging**: Logs every entity state change to `system_log.write`

---

## 6. Backend — PostgreSQL

### 6.1 Role

PostgreSQL replaces the default SQLite recorder for entity state history. Every time an entity changes state, the HA recorder inserts a row into the `states` table.

### 6.2 Connection

- **Host**: `ha-postgres` (Docker internal DNS) / `localhost` (external)
- **Port**: `5432`
- **Database**: `homeassistant`
- **User**: `homeassistant`
- **Password**: `hass_password`
- **Driver**: `psycopg2-binary` (installed by entrypoint)

### 6.3 Schema (HA recorder tables)

The HA recorder creates the following tables automatically:

| Table | Description |
|---|---|
| `states` | Entity state changes (entity_id, state, last_changed, last_updated, attributes JSON) |
| `events` | Event log entries |
| `state_attributes` | Normalized attributes (for query efficiency) |
| `event_data` | Normalized event data |
| `statistics` | Long-term statistics (min/max/mean) |
| `statistics_meta` | Statistics metadata |
| `schema_migrations` | Migration tracking |

### 6.4 Sample Query

```sql
SELECT entity_id, state, last_changed
FROM states
ORDER BY last_changed DESC
LIMIT 10;
```

### 6.5 Retention

- **30 days** of history (`purge_keep_days: 30`)
- Only `light`, `switch`, `sensor`, `binary_sensor` domains are recorded
- `sun.sun` and `zone.home` are explicitly excluded

### 6.6 Volume

Data persists in the named Docker volume `postgres_data`, mapped to `/var/lib/postgresql/data`.

---

## 7. Backend — Mosquitto MQTT Broker

### 7.1 Configuration

Generated dynamically at container start:
- **Listener**: `1883 0.0.0.0` (binds all interfaces)
- **Authentication**: Anonymous (no username/password required)
- **Persistence**: Enabled, stored in `/mosquitto/data/`
- **No TLS configured** (plaintext MQTT)

### 7.2 Volumes

| Volume | Container Path | Purpose |
|---|---|---|
| `mosquitto_data` | `/mosquitto/data` | Persistent message store |
| `mosquitto_log` | `/mosquitto/log` | Broker logs |

### 7.3 Role in the System

- **ESP32 publishes** state changes and discovery messages
- **HA subscribes** to state topics, publishes command topics
- **No direct frontend-to-ESP32 communication** — all traffic flows through HA
- Mosquitto acts as the transparent message bus between HA and the ESP32

---

## 8. ESP32 Firmware (IoT Layer)

### 8.1 Boot Sequence (`boot.py`)

```python
import main
main.main()
```

Minimal boot loader — on power-up, immediately runs the main firmware.

### 8.2 Configuration (`config.py`)

```python
WIFI_SSID = "house_network"
WIFI_PASSWORD = "house_network_pass"
MQTT_BROKER = "192.XXX.YY.ZZZ"   # Docker host IP
MQTT_PORT = 1883
MQTT_USER = ""
MQTT_PASSWORD = ""
```

### 8.3 Firmware Architecture (`main.py`, 291 lines)

#### Initialization Flow
1. Read config from `config.py`
2. Generate unique `DEVICE_ID` from chip ID: `esp32_device_` + 6-byte hex (e.g., `esp32_device_a0b7652a758c`)
3. Configure GPIO pins:
   - LED1: GPIO13 (output)
   - LED2: GPIO12 (output)
   - LED3: GPIO14 (output)
   - Servo: GPIO15 (PWM, 50Hz)
   - Status LED: GPIO2 (built-in)
4. All LEDs start OFF; servo centers at 90°

#### WiFi Connection
```python
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        machine.idle()
        time.sleep(1)
```

Blocks until connected. Status LED turns on when WiFi is established.

#### MQTT Connection
```python
def connect_mqtt():
    mqtt = MQTTClient(client_id, MQTT_BROKER, MQTT_PORT)
    mqtt.set_callback(mqtt_callback)
    mqtt.connect()
    # Subscribe to command topics
    for topic in [TOPIC_LED1, TOPIC_LED2, TOPIC_LED3, TOPIC_SERVO]:
        mqtt.subscribe(topic)
    publish_discovery()
    mqtt.publish(TOPIC_STATUS, "online", retain=True)
```

#### MQTT Discovery (auto-configuration for HA)
On connect, the ESP32 publishes 4 discovery messages:

| Topic | Entity Created |
|---|---|
| `homeassistant/light/{DEVICE_ID}/led1/config` | `light.{DEVICE_NAME}_led_1` |
| `homeassistant/light/{DEVICE_ID}/led2/config` | `light.{DEVICE_NAME}_led_2` |
| `homeassistant/light/{DEVICE_ID}/led3/config` | `light.{DEVICE_NAME}_led_3` |
| `homeassistant/cover/{DEVICE_ID}/servo/config` | `cover.{DEVICE_NAME}_servo` |

Each discovery payload includes: name, unique_id, command_topic, state_topic, payload mapping, and device metadata (manufacturer: "Custom", model: "ESP32 Controller").

#### Main Loop
```python
while True:
    mqtt.check_msg()                         # Process incoming MQTT commands
    if time.time() - last_ping > 30:
        mqtt.publish(TOPIC_STATUS, "online", retain=True)  # Heartbeat
        status_led.toggle()
    time.sleep(0.1)                          # 100ms cycle
```

On any exception:
1. Disconnect MQTT
2. Wait 5 seconds
3. Attempt reconnect
4. On failure: `machine.reset()` (hard reset)

#### MQTT Callback (`mqtt_callback`)

Handles 4 command topics:

| Topic Match | Message | Action | State Publish |
|---|---|---|---|
| `led1/command` | `ON`/`true` | `led1.value(1)` | `led1/state` → `ON` |
| `led1/command` | `OFF`/`false` | `led1.value(0)` | `led1/state` → `OFF` |
| `led2/command` | `ON`/`OFF` | Same pattern | Same pattern |
| `led3/command` | `ON`/`OFF` | Same pattern | Same pattern |
| `servo/command` | `open` | `servo(180°)` | `servo/state` → `open` |
| `servo/command` | `close` | `servo(0°)` | `servo/state` → `closed` |
| `servo/command` | `position:{angle}` | `servo(angle)` | `servo/state` → `position:{angle}` |
| `servo/command` | `0`-`180` (raw int) | `servo(int)` | `servo/state` → `position:{angle}` |

#### Servo Control

```python
def set_servo_angle(angle):
    min_duty = 40    # 0°
    max_duty = 115   # 180°
    duty = min_duty + (angle / 180) * (max_duty - min_duty)
    servo.duty(int(duty))
```

Standard servo PWM at 50Hz. Duty cycle range configurable via `min_duty`/`max_duty` constants.

### 8.4 Hardware Pinout

| ESP32 Pin | Component | Electrical Detail |
|---|---|---|
| GPIO13 | LED1 | Anode → 220Ω → 3.3V |
| GPIO12 | LED2 | Anode → 220Ω → 3.3V |
| GPIO14 | LED3 | Anode → 220Ω → 3.3V |
| GPIO15 | Servo signal | PWM 50Hz |
| GPIO2 | Status LED | Built-in (active high) |
| 3.3V/GND | LEDs power | Shared from ESP32 |
| 5V/GND | Servo power | External supply |

---

## 9. Frontend — Dashboard

### 9.1 Delivery

The frontend is served as a static site:
```bash
python3 -m http.server 3000 -d frontend
```

No build step, bundler, or npm required. All dependencies loaded from CDN.

### 9.2 Dependencies (CDN)

| Library | URL | Purpose |
|---|---|---|
| Tailwind CSS | `cdn.tailwindcss.com` | Utility-first CSS |
| HTMX | `unpkg.com/htmx.org@1.9.12` | AJAX via HTML attributes |
| Alpine.js | `cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js` | Reactive UI framework |
| Font Awesome | `cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css` | Icons |
| Inter font | `fonts.googleapis.com` | Typography |

### 9.3 Page Structure

The single-page dashboard (`index.html`, 472 lines) has 3 main states:

#### 9.3.1 Auth Screen
- Full-screen centered overlay
- Password input for Long-Lived Access Token
- "Connect" button with `@click="authenticate()"`
- Error message display (`x-show="authError"`)
- Token persisted in `localStorage('ha_token')` for session resumption
- `@keyup.enter` shortcut on the input

#### 9.3.2 Main Dashboard (post-auth)
- **Header**: New Device button, current date/time display, connection status indicator (green/amber), Smart Control System title, disconnect button
- **Device Grid**: Responsive grid (1–4 columns) of device cards with:
  - Delete button (top-right)
  - Icon (lightbulb/temperature/bullhorn) + name + location + online status
  - Dynamic content based on device type:
    - `lights`: Toggle switch
    - `sensor`: Value display
    - `actionable`: Execute button
  - Last-seen timestamp
- **Session Logs**: Scrollable log area with timestamps, clear button
- **Add Device Modal**: Entity ID input, validation against HA API, confirmation/cancel

### 9.4 Alpine.js Application (`appDashboard()`)

The `appDashboard()` function (lines 177–468) manages all application state:

#### State Properties

| Property | Type | Default | Description |
|---|---|---|---|
| `token` | string | `localStorage('ha_token')` | HA auth token |
| `authenticated` | boolean | `false` | Auth status |
| `authError` | string | `''` | Auth error message |
| `isConnected` | boolean | `false` | API connectivity |
| `wsConnected` | boolean | `false` | WebSocket connectivity |
| `ws` | WebSocket | `null` | Active WebSocket instance |
| `devices` | array | `[]` | Registered device objects |
| `newEntityId` | string | `''` | Add-device modal input |
| `logs` | array | `[]` | Session action logs |
| `openModal` | boolean | `false` | Add-device modal visibility |
| `currentDate` | string | `''` | Formatted date/time |

#### Key Methods

| Method | Trigger | Action |
|---|---|---|
| `init()` | `x-init` | Auto-authenticate if token exists, start date updater |
| `authenticate()` | Connect button | `GET /api/` with Bearer token, on success: store token, connect WS, fetch states |
| `disconnect()` | Disconnect button | Clear token, close WS, clear devices and logs |
| `connectWebSocket()` | After auth | Open `ws://localhost:8123/api/websocket`, send auth, subscribe to `state_changed` |
| `fetchAllDevices()` | After auth | `GET /api/states`, refresh tracked devices |
| `addDevice()` | Modal submit | `GET /api/states/{entity_id}`, validate, push to devices array |
| `deleteDevice(id)` | Delete button | Splice from devices array, persist to localStorage |
| `toggleLight(device, checked)` | Toggle switch | Optimistic update, `POST /api/services/{domain}/turn_on\|turn_off`, rollback on failure |
| `triggerActionable(device)` | Execute button | `POST /api/services/{domain}/turn_on` |
| `mapToDevice(state)` | Internal | Convert HA state object to dashboard device object |
| `getDeviceType(entityId)` | Internal | `light` → `lights`, `sensor`/`binary_sensor` → `sensor`, else → `actionable` |
| `persistDevices()` | After device change | Save to `localStorage('ha_dashboard_devices')` |
| `loadFromStorage()` | On init | Restore devices from localStorage |
| `addLog(message)` | Various | Prepend timestamped log entry |
| `clearLogs()` | Clear button | Empty logs array |

#### WebSocket Protocol

The frontend sends:
```json
// Auth (on open)
{"type": "auth", "access_token": "<TOKEN>"}

// Subscribe to state_changed events
{"id": 1, "type": "subscribe_events", "event_type": "state_changed"}
```

And receives:
```json
{"type": "auth_ok"}  // Success
{"type": "auth_invalid"}  // Failure

// State change event
{"event": {"data": {"entity_id": "light.xxx", "new_state": {...}}}}
```

On WebSocket close, the frontend auto-reconnects every 3 seconds.

### 9.5 API Endpoints Consumed

| Method | Endpoint | Usage |
|---|---|---|
| `GET` | `/api/` | Token validation |
| `GET` | `/api/states` | Fetch all states after auth |
| `GET` | `/api/states/{entity_id}` | Validate entity on add |
| `POST` | `/api/services/{domain}/turn_on` | Toggle on / trigger |
| `POST` | `/api/services/{domain}/turn_off` | Toggle off |
| `WS` | `/api/websocket` | Real-time state change subscription |

### 9.6 Custom Styles (`style.css`, 98 lines)

- Warm off-white color scheme (`#f7f6f2`)
- Inter font family
- Device card: white/translucent background, backdrop blur, subtle shadow, hover lift effect
- Toggle switch: custom CSS with rounded slider, green/beige color states
- Modal overlay: semi-transparent black with backdrop blur
- Custom scrollbar (thin, beige)
- Dark mode media query (minor color adjustment)
- `x-cloak` handling

### 9.7 Offline Behavior

- Failed `POST` calls roll back optimistic UI updates
- WebSocket auto-reconnect with 3-second backoff
- Connection status indicator changes from green to amber
- No offline queue — state is read-only when disconnected

---

## 10. Communication Protocol

### 10.1 End-to-End Command Flow (Toggle LED)

```
User clicks toggle
       │
       ▼
Alpine.js: toggleLight(device, checked)
  ├─ Optimistic: device.state = 'on'
  ├─ fetch POST http://localhost:8123/api/services/light/turn_on
  │   Body: {"entity_id": "light.esp32_device_xxx_led1"}
  │   Headers: Authorization: Bearer <TOKEN>
  │
  ▼
Home Assistant REST API
  ├─ Validates token
  ├─ Calls light.turn_on service
  │   └─ MQTT integration publishes to:
  │      homeassistant/light/{DEVICE_ID}/led1/command → "ON"
  │
  ▼
Mosquitto MQTT Broker (internal docker network)
  │
  ▼
ESP32 (via WiFi)
  ├─ mqtt.check_msg() picks up message
  ├─ mqtt_callback() fires
  ├─ led1.value(1)
  ├─ Publishes: homeassistant/light/{DEVICE_ID}/led1/state → "ON"
  │
  ▼
Home Assistant (receives state via MQTT)
  ├─ Updates entity state
  ├─ Recorder writes to PostgreSQL states table
  │
  ▼
Frontend (receives via WebSocket)
  ├─ ws.onmessage: state_changed event
  ├─ mapToDevice() updates device object
  ├─ UI re-renders reactively
```

### 10.2 Round-trip Latency

| Segment | Estimated Latency |
|---|---|
| Browser → HA REST API (localhost) | < 5ms |
| HA → Mosquitto (Docker network) | < 1ms |
| Mosquitto → ESP32 (WiFi) | 10–50ms |
| ESP32 GPIO write | < 1ms |
| ESP32 → Mosquitto (state publish) | 10–50ms |
| Mosquitto → HA (state receive) | < 1ms |
| HA → WebSocket push | < 5ms |
| **Total round-trip** | **30–120ms** |

---

## 11. Data Flow & Lifecycle

### 11.1 Device Discovery

1. ESP32 powers on
2. Connects to WiFi (`house_network`)
3. Connects to MQTT broker at `192.XXX.YY.ZZZ:1883`
4. Publishes 4 discovery messages to `homeassistant/light/{id}/led{1,2,3}/config` and `homeassistant/cover/{id}/servo/config`
5. HA (subscribed to `homeassistant/#`) receives discovery
6. HA auto-creates entities and registers the device
7. ESP32 publishes initial state (`led/state: OFF`, `servo/state: position:90`)
8. ESP32 publishes `sensor/{id}/status: online` (retained) and repeats every 30s

### 11.2 State Change Lifecycle

1. User interacts with dashboard toggle
2. Frontend sends REST POST to HA
3. HA publishes MQTT command
4. ESP32 executes physical action
5. ESP32 publishes new state via MQTT
6. HA receives state, updates entity
7. HA recorder writes to PostgreSQL
8. HA pushes `state_changed` event via WebSocket
9. Frontend updates UI reactively

### 11.3 Heartbeat / Keepalive

- ESP32 publishes `sensor/{id}/status: online` (retained) every 30 seconds
- If ESP32 goes offline, the retained message remains "online" until HA detects the connection loss via MQTT Last Will (if configured) or missing heartbeat
- Frontend detects HA disconnection via WebSocket `onclose` event and shows "Connecting..."

---

## 12. MQTT Topics Map

### 12.1 Discovery Topics (ESP32 → HA, retained)

| Topic | Entity Type |
|---|---|
| `homeassistant/light/{DEVICE_ID}/led1/config` | Light (LED1) |
| `homeassistant/light/{DEVICE_ID}/led2/config` | Light (LED2) |
| `homeassistant/light/{DEVICE_ID}/led3/config` | Light (LED3) |
| `homeassistant/cover/{DEVICE_ID}/servo/config` | Cover (Servo, device_class: garage) |

### 12.2 Command Topics (HA → ESP32)

| Topic | Payload Examples | Result |
|---|---|---|
| `homeassistant/light/{DEVICE_ID}/led1/command` | `ON`, `OFF` | LED1 on/off |
| `homeassistant/light/{DEVICE_ID}/led2/command` | `ON`, `OFF` | LED2 on/off |
| `homeassistant/light/{DEVICE_ID}/led3/command` | `ON`, `OFF` | LED3 on/off |
| `homeassistant/cover/{DEVICE_ID}/servo/command` | `open`, `close`, `90`, `position:45` | Servo positioning |

### 12.3 State Topics (ESP32 → HA)

| Topic | Payload Examples | Description |
|---|---|---|
| `homeassistant/light/{DEVICE_ID}/led1/state` | `ON`, `OFF` | LED1 current state |
| `homeassistant/light/{DEVICE_ID}/led2/state` | `ON`, `OFF` | LED2 current state |
| `homeassistant/light/{DEVICE_ID}/led3/state` | `ON`, `OFF` | LED3 current state |
| `homeassistant/cover/{DEVICE_ID}/servo/state` | `open`, `closed`, `position:90` | Servo current state |
| `homeassistant/sensor/{DEVICE_ID}/status` | `online` (retained) | Heartbeat |

Where `{DEVICE_ID}` = `esp32_device_` + 6-byte hex unique chip ID.

### 12.4 Entity IDs (as registered in HA)

| Entity ID |
|---|
| `light.esp32_controller_esp32_controller_led_1` |
| `light.esp32_controller_esp32_controller_led_2` |
| `light.esp32_controller_esp32_controller_led_3` |
| `cover.esp32_controller_esp32_controller_servo` |

---

## 13. Storage & Persistence

### 13.1 PostgreSQL (Docker Volume: `postgres_data`)

- **Data**: Entity state history (states table), events, statistics
- **Retention**: 30 days (auto-purged by recorder)
- **Schema**: Auto-created by HA recorder integration
- **Persistence**: Survives container restarts; removed with `docker-compose down -v`

### 13.2 Mosquitto Data (Docker Volume: `mosquitto_data`)

- **Data**: Retained MQTT messages (discovery configs, status messages)
- **Persistence**: Survives container restarts
- **Purpose**: Retained messages allow HA to discover entities even if ESP32 briefly disconnects

### 13.3 Frontend (Browser localStorage)

| Key | Content | Persistence |
|---|---|---|
| `ha_token` | Long-Lived Access Token string | Until logout or manual clear |
| `ha_dashboard_devices` | JSON array of device objects | Until logout or manual clear |

### 13.4 Home Assistant Config (`homeassistant_config/`)

- Mounted as Docker bind volume (`./homeassistant_config:/config`)
- Contains all HA configuration, storage state, blueprints, custom components
- Backed up by `ha_configuration_backup.sh`

### 13.5 Backups (`./backups/`)

Created by `ha_configuration_backup.sh`:
- `ha_backup_{timestamp}.tar.gz` — compressed `homeassistant_config/` directory
- `ha_backup_{timestamp}.dump` — PostgreSQL custom format dump (if `pg_dump` available)
- `ha_backup_{timestamp}.info` — metadata file
- Retention: 7 days (auto-cleanup via `find -mtime +7`)

---

## 14. Operations & Scripts

### 14.1 Start

```bash
docker-compose up -d                # Start all containers
python3 -m http.server 3000 -d frontend  # Start frontend dev server
```

### 14.2 Stop

```bash
docker-compose down                 # Stop and remove containers (data persists)
docker-compose down -v              # Stop and remove volumes (deletes all data)
```

### 14.3 Service Restart (`scripts/service_restart.sh`)

```bash
./scripts/service_restart.sh
```

Sequence:
1. Check container exists and is running
2. Get current health status
3. `docker restart homeassistant`
4. Wait up to 180s for healthy status (poll every 5s)
5. Check web interface responds on port 8123

### 14.4 Backup (`scripts/ha_configuration_backup.sh`)

```bash
./scripts/ha_configuration_backup.sh
```

Sequence:
1. Verify `homeassistant_config/` exists
2. Create `tar.gz` of config directory
3. Attempt `pg_dump` of PostgreSQL database (optional, non-critical failure)
4. Create `.info` file with backup timestamp and config size
5. Clean backups older than 7 days
6. List current backups

### 14.5 Log Monitoring (`scripts/container_log_monitoring.sh`)

```bash
./scripts/container_log_monitoring.sh             # Interactive menu
./scripts/container_log_monitoring.sh check 100   # Last 100 lines
./scripts/container_log_monitoring.sh follow      # Real-time tail
./scripts/container_log_monitoring.sh stats       # Error statistics
```

Features:
- Ansi-colored output
- Pattern matching: ERROR, FATAL, WARNING, Exception, Failed, Unable
- Email alerts (optional, via `mail` command)
- Log file output to `./logs/ha_monitor.log`
- Interactive menu with 5 options

### 14.6 Planned Testing Commands (MQTT)

```bash
mosquitto_pub -h localhost -t "homeassistant/light/esp32_device_xxx/led1/command" -m "ON"
mosquitto_pub -h localhost -t "homeassistant/cover/esp32_device_xxx/servo/command" -m "90"
```

---

## 15. Security Model

### 15.1 Authentication

- **Frontend → HA**: Long-Lived Access Token (Bearer auth)
  - Generated from HA profile page at `/profile`
  - Stored in browser localStorage
  - Sent in `Authorization: Bearer <TOKEN>` header
  - Sent as `access_token` in WebSocket auth message
- **ESP32 → MQTT**: Anonymous (no auth configured)
- **PostgreSQL**: Password-based (`homeassistant:hass_password`)

### 15.2 Authorization

- HA's built-in RBAC: users have roles (owner, admin, user, read-only)
- API endpoints require valid Bearer token
- MQTT broker allows anonymous publish/subscribe to all topics

### 15.3 Network Exposure

| Service | Exposed Port | Bound To | Risk |
|---|---|---|---|
| PostgreSQL | 5432 | 0.0.0.0 | Accessible from anywhere on the LAN |
| Mosquitto | 1883 | 0.0.0.0 | No TLS, anonymous access |
| HA | 8123 | 0.0.0.0 | Protected by token auth |
| Frontend | 3000 | 0.0.0.0 | Static files only |

### 15.4 CORS

HA configured to accept requests only from `http://localhost:3000`.

### 15.5 TLS

Not configured for any service. Mosquitto and HA would need Let's Encrypt or self-signed certificates for TLS.

### 15.6 Secrets

- PostgreSQL password hardcoded in `docker-compose.yml` and `configuration.yaml`
- WiFi credentials in `esp32/config.py`
- Frontend token in browser localStorage (accessible via DevTools)

---

## 16. Planned Extensions

Based on planning documents (`documents/ha_planning_document_2.md` and `documents/4-pseudocode_ha.md`):

### 16.1 Temperature Sensor (DS18B20)

- Add DS18B20 to ESP32 (GPIO18, 1-wire with 4.7kΩ pull-up)
- Publish temperature every 30s to MQTT
- Display in HA as a sensor entity

### 16.2 Physical Switch

- Add tactile push button (GPIO4, input with pull-up)
- Software debounce (30ms)
- Publish switch state changes to MQTT

### 16.3 Weather Integration (Open-Meteo)

- HA automation fetches external temperature every 10 minutes
- Free API, no API key required
- Stores in `input_number.external_temp`

### 16.4 Temperature Comparison + Suggestion

- HA automation compares indoor vs outdoor temperature
- Generates suggestion text based on rules:
  - Indoor > Outdoor + 2°C → "Open window or use fan"
  - Indoor < Outdoor - 2°C → "Close windows or add heating"
  - Balanced → "No action needed"

### 16.5 Optional LLM Integration (Ollama)

- Run Ollama locally (requires ~4GB RAM)
- Send suggestion text to LLM for natural language rephrasing
- Display LLM output alongside basic suggestion

### 16.6 System States

| State | ESP32 Action | HA Action | UI Display |
|---|---|---|---|
| Boot | Connect WiFi/MQTT, init sensors | Wait for MQTT | "Connecting..." |
| Normal | Publish temp every 30s, listen for commands | Show dashboard, run automations | Active controls, updated graphs |
| No WiFi | Retry every 5s | Show "ESP32 offline" | Error message, disabled controls |
| Suggestion active | (no change) | Compare indoor/outdoor, generate text | Suggestion box visible |
| LLM querying | (no change) | Send prompt to Ollama, wait | "Generating suggestion..." |
| Logging | (no change) | Write to database | History accessible |

---

## 17. Paradigm Used

The paradigm I used is **exploration-first comprehension**: I recursively discovered every file in the project, read each one in its entirety, synthesized the information into a mental model of the system, then authored the document with consistent depth across all layers. This is essentially a **reverse-engineering + structured documentation** approach — I treated the codebase as the source of truth and extracted architecture, behavior, and rationale from raw files rather than from pre-existing spec.
