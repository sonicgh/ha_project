# Smart Apartment Project — Complete System Documentation

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Project Structure](#2-project-structure)
3. [Architecture & Communication Flow](#3-architecture--communication-flow)
4. [Docker Services & Ports](#4-docker-services--ports)
5. [MQTT Topics](#5-mqtt-topics)
6. [ESP32 Pinout & Hardware](#6-esp32-pinout--hardware)
7. [Home Assistant Role](#7-home-assistant-role)
8. [PostgreSQL Role](#8-postgresql-role)
9. [Frontend Role](#9-frontend-role)
10. [How the System Talks — Step by Step](#10-how-the-system-talks--step-by-step)
11. [How to Start the Project](#11-how-to-start-the-project)
12. [How to Stop the Project](#12-how-to-stop-the-project)
13. [Key Files Reference](#13-key-files-reference)

---

## 1. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| **Container Orchestration** | Docker Compose | 3.8 |
| **Home Automation Platform** | Home Assistant | stable (`ghcr.io`) |
| **Database** | PostgreSQL | 15 Alpine |
| **MQTT Broker** | Eclipse Mosquitto | 2 |
| **ESP32 Firmware** | MicroPython + `umqtt.simple` | — |
| **Frontend** | Alpine.js 3 + HTMX 1.9 + Tailwind CSS | CDN |
| **Icons** | Font Awesome 6 | CDN |

---

## 2. Project Structure

```
ha_project/
├── docker-compose.yml               # 3 containers: HA, PostgreSQL, Mosquitto
├── .env                             # HA URL/Token, PG, MQTT env vars
├── requirements.txt                 # Pins homeassistant==2025.1.4
├── README.md                        # This file
├── frontend/
│   ├── index.html                   # Alpine.js + HTMX + Tailwind dashboard
│   └── style.css                    # Dashboard styles
├── esp32/
│   ├── main.py                      # ESP32 firmware (WiFi, MQTT, GPIO, HA discovery)
│   ├── config.py                    # WiFi/MQTT credentials
│   ├── boot.py                      # Auto-runs main() on power-up
│   └── ESP32.md                     # Pinout reference, MQTT test commands
├── homeassistant_config/
│   ├── configuration.yaml           # CORS, recorder (PostgreSQL), esp_health
│   ├── entrypoint.sh                # Installs psycopg2-binary, starts HA
│   ├── custom_components/
│   │   └── esp_health/              # ESP32 device health monitoring integration
│   └── ...                          # (gitignored: .HA_VERSION, .storage/, etc.)
├── python_api_requests/             # Python scripts for HA REST API calls
├── scripts/
│   ├── service_restart.sh           # Restart HA container with health check
│   ├── ha_configuration_backup.sh   # Backup HA config + DB dump to ./backups/
│   └── container_log_monitoring.sh  # Monitor logs: check <lines>, follow, stats
├── documents/                       # Planning docs (flowcharts, pseudocode, state tables)
├── summary.md                       # Project summary
└── technical_document.md            # Technical reference
```

---

## 3. Architecture & Communication Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                                  │
│  Frontend: index.html (Alpine.js + HTMX + Tailwind)                  │
│  Served by: python3 -m http.server 3000                              │
│  URL: http://localhost:3000                                           │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   │ REST API (http://localhost:8123/api/*)
                   │ WebSocket (ws://localhost:8123/api/websocket)
                   │ Auth: Bearer <Long-Lived Token>
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    HOME ASSISTANT (Docker)                            │
│  Container: homeassistant                                             │
│  Port: 8123                                                           │
│  Role: Orchestrator — receives frontend commands, sends MQTT,        │
│         stores state history in PostgreSQL, serves REST API + WS     │
└───────────┬──────────────────────────────────┬───────────────────────┘
            │                                  │
            │ MQTT (internal Docker network)   │ PostgreSQL (internal)
            │ host: ha-mosquitto               │ host: ha-postgres
            │ port: 1883                       │ port: 5432
            │                                  │ user: homeassistant
            ▼                                  ▼
┌──────────────────────┐       ┌──────────────────────────────┐
│   MOSQUITTO MQTT     │       │        POSTGRESQL            │
│   (Docker)           │       │        (Docker)              │
│   Container:          │       │  Container: ha-postgres      │
│     ha-mosquitto     │       │  Port: 5432                  │
│   Port: 1883         │       │  DB: homeassistant           │
│   Auth: anonymous    │       │  Tables: states, events      │
│   Persistence: yes   │       │  Retains 30 days of history  │
└───────────┬──────────┘       └──────────────────────────────┘
            │
            │ MQTT (over WiFi network)
            │
            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        ESP32 (MicroPython)                            │
│  WiFi SSID: house_network                                             │
│  MQTT Broker: 192.XXX.YY.ZZZ:1883                                     │
│                                                                       │
│  Hardware:                                                             │
│    GPIO13 ──→ LED1 (via 220Ω resistor)                                 │
│    GPIO12 ──→ LED2 (via 220Ω resistor)                                 │
│    GPIO14 ──→ LED3 (via 220Ω resistor)                                 │
│    GPIO15 ──→ Servo (PWM 50Hz, signal wire)                            │
│    GPIO2  ──→ Status LED (built-in, blinks on activity)               │
│    3.3V      → LEDs power                                              │
│    5V/GND    → Servo power                                             │
│                                                                       │
│  On boot:                                                              │
│    1. Connect to WiFi                                                  │
│    2. Connect to MQTT broker                                           │
│    3. Publish HA discovery messages (auto-config)                      │
│    4. Subscribe to command topics                                      │
│    5. Main loop: check for MQTT messages, heartbeat every 30s         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Docker Services & Ports

| Service | Container Name | Internal Port | Host Port | Purpose |
|---|---|---|---|---|
| **Home Assistant** | `homeassistant` | 8123 | **8123** | REST API, WebSocket, UI |
| **PostgreSQL** | `ha-postgres` | 5432 | **5432** | State history storage |
| **Mosquitto** | `ha-mosquitto` | 1883 | **1883** | MQTT message broker |

Services are connected via Docker's internal network. Home Assistant accesses:
- PostgreSQL at `ha-postgres:5432`
- Mosquitto at `ha-mosquitto:1883`

The frontend (running on host) accesses:
- HA API at `http://localhost:8123`
- HA WebSocket at `ws://localhost:8123/api/websocket`

---

## 5. MQTT Topics

### Command Topics (ESP32 subscribes, HA publishes)

| Topic | Payload | Action |
|---|---|---|
| `homeassistant/light/{DEVICE_ID}/led1/command` | `ON` / `OFF` | Turn LED1 on/off |
| `homeassistant/light/{DEVICE_ID}/led2/command` | `ON` / `OFF` | Turn LED2 on/off |
| `homeassistant/light/{DEVICE_ID}/led3/command` | `ON` / `OFF` | Turn LED3 on/off |
| `homeassistant/cover/{DEVICE_ID}/servo/command` | `open` / `close` / `0`-`180` / `position:{angle}` | Control servo |

### State Topics (ESP32 publishes, HA subscribes)

| Topic | Payload | Description |
|---|---|---|
| `homeassistant/light/{DEVICE_ID}/led1/state` | `ON` / `OFF` | LED1 current state |
| `homeassistant/light/{DEVICE_ID}/led2/state` | `ON` / `OFF` | LED2 current state |
| `homeassistant/light/{DEVICE_ID}/led3/state` | `ON` / `OFF` | LED3 current state |
| `homeassistant/cover/{DEVICE_ID}/servo/state` | `open` / `closed` / `position:{angle}` | Servo current state |
| `homeassistant/sensor/{DEVICE_ID}/status` | `online` (retained) | Heartbeat every 30s |

### Discovery Topics (ESP32 publishes for HA auto-config)

| Topic | Purpose |
|---|---|
| `homeassistant/light/{DEVICE_ID}/led1/config` | HA auto-creates LED1 light entity |
| `homeassistant/light/{DEVICE_ID}/led2/config` | HA auto-creates LED2 light entity |
| `homeassistant/light/{DEVICE_ID}/led3/config` | HA auto-creates LED3 light entity |
| `homeassistant/cover/{DEVICE_ID}/servo/config` | HA auto-creates servo cover entity |

Where `{DEVICE_ID}` = `esp32_device_` + 6-byte hex of the ESP32's unique chip ID (e.g., `esp32_device_a1b2c3d4e5f6`).

### Resulting Home Assistant Entity IDs

| Entity ID | Domain | Friendly Name |
|---|---|---|
| `light.esp32_device_{hex}_led1` | light | esp32_controller LED 1 |
| `light.esp32_device_{hex}_led2` | light | esp32_controller LED 2 |
| `light.esp32_device_{hex}_led3` | light | esp32_controller LED 3 |
| `cover.esp32_device_{hex}_servo` | cover | esp32_controller Servo |
| `sensor.esp32_device_{hex}_status` | sensor | (status sensor) |

---

## 6. ESP32 Pinout & Hardware

### GPIO Mapping

| ESP32 Pin | Component | Connection Details |
|---|---|---|
| GPIO13 | LED1 | Anode through 220Ω resistor to 3.3V |
| GPIO12 | LED2 | Anode through 220Ω resistor to 3.3V |
| GPIO14 | LED3 | Anode through 220Ω resistor to 3.3V |
| GPIO15 | Servo | Signal wire (PWM 50Hz) |
| GPIO2 | Status LED | Built-in LED (blinks on MQTT activity) |

### Power

| Component | Power Source |
|---|---|
| LEDs | 3.3V from ESP32 (each through 220Ω resistor) |
| Servo | External 5V supply (separate from ESP32 power) |
| Ground | Common GND between ESP32, LEDs, and servo |

### Servo Control

The servo uses PWM at 50Hz (standard servo frequency). Duty cycle mapping:
- 0° → duty cycle 40
- 90° → duty cycle ~77 (center)
- 180° → duty cycle 115

Adjust `min_duty` / `max_duty` values in `main.py:57-58` if using a different servo model.

---

## 7. Home Assistant Role

Home Assistant is the **central orchestrator** of the system. It:

- **Exposes a REST API** (`http://localhost:8123/api/*`) for the frontend to read states, send commands, and query history.
- **Exposes a WebSocket** (`ws://localhost:8123/api/websocket`) for real-time state change push notifications to the frontend.
- **Connects to Mosquitto** via MQTT to send commands to the ESP32 and receive state updates.
- **Connects to PostgreSQL** to store entity state history (30 days retention for `light`, `switch`, `sensor`, `binary_sensor` domains).
- **Auto-discovers ESP32 entities** via MQTT discovery messages published by the ESP32 on boot.
- **Handles authentication** — the frontend authenticates using a Long-Lived Access Token generated from the HA profile page.
- **CORS configured** to accept requests from `http://localhost:3000` (the frontend).

### HA Configuration (`configuration.yaml`)

```yaml
http:
  cors_allowed_origins:
    - http://localhost:3000

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
```

---

## 8. PostgreSQL Role

PostgreSQL stores **entity state change history**. Every time an entity (like `light.led1`) changes state, the Home Assistant recorder writes a row to the `states` table with:

- `entity_id` — e.g., `light.esp32_device_xxx_led1`
- `state` — e.g., `on`, `off`
- `last_changed` — timestamp
- `last_updated` — timestamp
- `attributes` — JSON with friendly name, etc.

### Query the database

```bash
psql -h localhost -U homeassistant -d homeassistant
# Password: hass_password

SELECT entity_id, state, last_changed FROM states ORDER BY last_changed DESC LIMIT 10;
```

### Database credentials

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| User | `homeassistant` |
| Password | `hass_password` |
| Database | `homeassistant` |

---

## 9. Frontend Role

The frontend (`index.html`) is a single-page dashboard built with:

- **Alpine.js 3** — reactive UI framework (manages state, handles events)
- **HTMX 1.9** — AJAX requests from HTML attributes
- **Tailwind CSS** — utility-first styling via CDN
- **Font Awesome 6** — icons

It runs as a static site served by Python:
```bash
python3 -m http.server 3000 -d frontend
```

### What the frontend does

1. **Auth screen** — prompts for a Home Assistant Long-Lived Access Token.
2. **Authentication** — validates the token against `GET http://localhost:8123/api/`.
3. **WebSocket connection** — opens a persistent connection to `ws://localhost:8123/api/websocket` for real-time updates.
4. **Device dashboard** — displays added devices as cards with toggle switches (lights), sensor values, or action buttons.
5. **Add device** — accepts an entity ID (e.g., `light.esp32_device_xxx_led1`) and validates it against HA.
6. **Device control** — sends commands via `POST /api/services/{domain}/{action}`.
7. **State updates** — receives WebSocket `state_changed` events and updates the UI live.
8. **System logs** — displays in-memory action logs (not persisted to database).

### API endpoints used by the frontend

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/` | Validate token |
| `GET` | `/api/states` | Fetch all entity states |
| `GET` | `/api/states/{entity_id}` | Fetch single entity state |
| `POST` | `/api/services/{domain}/{action}` | Send command (turn_on, turn_off, toggle) |
| `WS` | `/api/websocket` | Real-time state change events |

---

## 10. How the System Talks — Step by Step

### A. ESP32 → Home Assistant (Device Discovery)

1. ESP32 boots, connects to WiFi (`house_network`).
2. ESP32 connects to Mosquitto MQTT at `192.168.78.111:1883`.
3. ESP32 publishes **MQTT discovery messages** to `homeassistant/light/{id}/led1/config`, etc.
4. Home Assistant (connected to the same Mosquitto broker) receives the discovery messages.
5. HA auto-creates entities: 3 lights (LEDs) + 1 cover (servo).
6. ESP32 publishes initial states (LEDs OFF, servo at 90°) and starts the heartbeat loop.

### B. Frontend → Home Assistant (User Authentication)

1. User opens `http://localhost:3000` in a browser.
2. Frontend shows an auth screen asking for a Long-Lived Access Token.
3. User enters the token (generated from HA profile at `http://localhost:8123/profile`).
4. Frontend validates the token via `GET http://localhost:8123/api/`.
5. On success: frontend stores the token, opens a WebSocket, and fetches device states.

### C. Frontend → Home Assistant → ESP32 (Toggle a Light)

1. User clicks a toggle switch on a device card.
2. Alpine.js calls `toggleLight(device, checked)`.
3. Frontend sends `POST http://localhost:8123/api/services/light/turn_on` with `{"entity_id": "light.esp32_device_xxx_led1"}`.
4. Home Assistant receives the REST API call and publishes to MQTT: `homeassistant/light/{id}/led1/command` → `ON`.
5. Mosquitto forwards the message to the ESP32.
6. ESP32's `mqtt_callback()` fires, sets `led1.value(1)`, and publishes state back: `homeassistant/light/{id}/led1/state` → `ON`.
7. Home Assistant receives the state update via MQTT and updates the entity.
8. The frontend's WebSocket receives a `state_changed` event and updates the UI (toggle stays in sync).

### D. ESP32 → Home Assistant → Frontend (State Feedback)

1. ESP32 publishes state change to MQTT (e.g., `led1/state: "ON"`).
2. HA receives the MQTT message → updates the entity state in memory.
3. HA's recorder writes the state change to PostgreSQL.
4. If the frontend has an open WebSocket, it receives the `state_changed` event and updates the UI.

### E. Home Assistant → PostgreSQL (History Persistence)

1. Every state change triggers HA's recorder integration.
2. Recorder inserts a row into the PostgreSQL `states` table.
3. Data includes `entity_id`, `state`, `last_changed`, `last_updated`, `attributes` (JSON).
4. History is retained for 30 days and automatically purged.
5. Only `light`, `switch`, `sensor`, `binary_sensor` domains are recorded (configured in `configuration.yaml`).

---

## 11. How to Start the Project

### Prerequisites

- Docker and Docker Compose installed
- Python 3 (for serving the frontend)
- ESP32 flashed with MicroPython and the project firmware
- Mosquitto MQTT client (optional, for testing)

### Step 1: Start Docker Services

```bash
cd ha_project
docker-compose up -d
```

This starts three containers:
- `ha-postgres` (PostgreSQL)
- `ha-mosquitto` (MQTT)
- `homeassistant` (Home Assistant)

Wait ~1-2 minutes for HA to fully initialize.

### Step 2: Verify Services Are Running

```bash
docker-compose ps
```

All three should show `Up`.

### Step 3: Configure MQTT in Home Assistant

1. Open `http://localhost:8123` in a browser.
2. Complete the HA onboarding (create an account if first run).
3. Go to **Settings > Devices & Services > Add Integration**.
4. Search for and select **MQTT**.
5. Configure:
   - **Broker**: `ha-mosquitto`
   - **Port**: `1883`
   - **Username/Password**: leave blank (anonymous)
6. Click **Submit** and **Finish**.

### Step 4: Generate a Long-Lived Access Token

1. In Home Assistant, click your **profile** (bottom-left).
2. Scroll down to **Long-Lived Access Tokens**.
3. Click **Create Token**, name it (e.g., "dashboard").
4. **Copy the token** — you will not see it again.

### Step 5: Power on the ESP32

1. Connect the ESP32 to your computer via USB.
2. If using Thonny: open `esp32/main.py`, verify `config.py` has the correct WiFi/MQTT settings.
3. Upload `main.py`, `config.py`, and `boot.py` to the ESP32.
4. Power-cycle the ESP32 or press the reset button.
5. The ESP32 will:
   - Connect to WiFi
   - Connect to MQTT broker at `192.168.78.111:1883`
   - Publish discovery configs
   - Subscribe to command topics
   - Start the main loop

### Step 6: Verify ESP32 Entities in HA

1. Go to **Settings > Devices & Services > MQTT**.
2. You should see the `esp32_controller` device with 3 lights + 1 cover.
3. Alternatively, go to **Developer Tools > States** and search for `esp32_device`.

### Step 7: Start the Frontend

```bash
cd ha_project
python3 -m http.server 3000 -d frontend
```

### Step 8: Open the Dashboard

1. Open `http://localhost:3000` in a browser.
2. Paste your Long-Lived Access Token and click **Connect**.
3. The dashboard will show "System Online" once connected.
4. Add devices by clicking **New Device** and entering entity IDs like:
   - `light.esp32_device_{hex}_led1`
   - `light.esp32_device_{hex}_led2`
   - `light.esp32_device_{hex}_led3`
   - `cover.esp32_device_{hex}_servo`
5. Toggle switches to control LEDs and servo.

### Testing MQTT Directly (Optional)

```bash
# Turn LED1 ON
mosquitto_pub -h localhost -t "homeassistant/light/esp32_device_xxx/led1/command" -m "ON"

# Move servo to 90°
mosquitto_pub -h localhost -t "homeassistant/cover/esp32_device_xxx/servo/command" -m "90"
```

Replace `esp32_device_xxx` with your ESP32's actual device ID (printed in the Thonny shell on boot).

---

## 12. How to Stop the Project

### Stop the Frontend

Press `Ctrl+C` in the terminal running the Python HTTP server.

### Stop Docker Services

```bash
docker-compose down
```

This stops and removes all containers. Data in PostgreSQL and Mosquitto volumes persists.

### Remove Everything (including data)

```bash
docker-compose down -v
```

This also removes the named volumes (`postgres_data`, `mosquitto_data`, `mosquitto_log`), deleting all stored data.

### Disconnect the ESP32

Simply unplug the USB/power from the ESP32. It will reconnect automatically when powered back on.

---

## 13. Key Files Reference

| File | Purpose |
|---|---|
| `docker-compose.yml` | Defines all 3 containers, volumes, ports, and environment |
| `homeassistant_config/configuration.yaml` | HA config: DB URL, CORS, recorder domains |
| `homeassistant_config/entrypoint.sh` | Installs psycopg2-binary, starts HA |
| `esp32/config.py` | WiFi SSID/password, MQTT broker address/port |
| `esp32/main.py` | ESP32 firmware: WiFi, MQTT, GPIO control, HA discovery |
| `esp32/boot.py` | Auto-runs `main()` on ESP32 power-up |
| `frontend/index.html` | Single-page dashboard (Alpine.js + HTMX + Tailwind) |
| `frontend/style.css` | Dashboard styles |
| `python_api_requests/validate_token.py` | Validate token: `GET /api/` |
| `python_api_requests/get_states.py` | Fetch all entity states: `GET /api/states` |
| `python_api_requests/get_entity_state.py` | Fetch single entity state: `GET /api/states/{entity_id}` |
| `python_api_requests/send_command.py` | Send command: `POST /api/services/{domain}/{action}` |
| `python_api_requests/websocket_listen.py` | Real-time events: `WS /api/websocket` |
| `scripts/service_restart.sh` | Restarts HA container with health check |
| `scripts/ha_configuration_backup.sh` | Backs up config + PostgreSQL dump |
| `scripts/container_log_monitoring.sh` | Monitor HA container logs |

---

## 14. Python API Scripts

Python scripts in `python_api_requests/` mirror the endpoints used by the frontend. All load `HA_URL` and `HA_TOKEN` from `.env` automatically (via `python-dotenv`) and use standard library `urllib.request` for REST calls.

### Usage

| Script | Endpoint | Command |
|---|---|---|
| `validate_token.py` | `GET /api/` | `python3 python_api_requests/validate_token.py` |
| `get_states.py` | `GET /api/states` | `python3 python_api_requests/get_states.py` |
| `get_entity_state.py` | `GET /api/states/{entity_id}` | `python3 python_api_requests/get_entity_state.py light.esp32_device_xxx_led1` |
| `send_command.py` | `POST /api/services/{domain}/{action}` | `python3 python_api_requests/send_command.py light.esp32_device_xxx_led1 turn_on` |
| `websocket_listen.py` | `WS /api/websocket` | `python3 python_api_requests/websocket_listen.py` |

### Requirements

```bash
pip install python-dotenv aiohttp  # aiohttp only needed for websocket_listen.py
```

### Examples

```bash
# Validate your HA token
python3 python_api_requests/validate_token.py

# List all entities and their states
python3 python_api_requests/get_states.py

# Get a specific entity's state
python3 python_api_requests/get_entity_state.py light.esp32_device_a0b7652a758c_led1

# Turn a light on/off
python3 python_api_requests/send_command.py light.esp32_device_a0b7652a758c_led1 turn_on
python3 python_api_requests/send_command.py light.esp32_device_a0b7652a758c_led1 turn_off

# Listen for real-time state changes
python3 python_api_requests/websocket_listen.py
```

---

## Appendix: Useful Commands

```bash
# View running containers
docker-compose ps

# Follow HA logs
docker logs -f homeassistant

# Follow Mosquitto logs
docker logs -f ha-mosquitto

# Query state history from PostgreSQL
psql -h localhost -U homeassistant -d homeassistant -c "SELECT entity_id, state, last_changed FROM states ORDER BY last_changed DESC LIMIT 10;"

# View all HA entities via API
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8123/api/states

# Restart HA container
docker-compose restart homeassistant

# Rebuild containers after config changes
docker-compose up -d --force-recreate
```
