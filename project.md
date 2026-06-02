# Smart Apartment Project - Architecture Overview

## Architecture Overview

This is a **Smart Apartment** system using **Home Assistant** as the central brain, communicating with **ESP32** hardware via **MQTT**, storing history in **PostgreSQL**, and exposing a custom **Alpine.js/HTMX frontend**.

---

## Technologies

| Layer | Technology |
|---|---|
| **Orchestration** | Docker Compose |
| **Home Automation** | Home Assistant (stable, `ghcr.io`) |
| **Database** | PostgreSQL 15 (Alpine) |
| **MQTT Broker** | Eclipse Mosquitto 2 |
| **ESP32 Firmware** | MicroPython (`umqtt.simple`) |
| **Frontend** | Alpine.js + HTMX + Tailwind CSS (CDN) |

---

## Docker Services & Ports

| Service | Container Name | Internal Port | Host Port | Purpose |
|---|---|---|---|---|
| **Home Assistant** | `homeassistant` | 8123 | **8123** | REST API + WebSocket + UI |
| **PostgreSQL** | `ha-postgres` | 5432 | **5432** | State history storage |
| **Mosquitto** | `ha-mosquitto` | 1883 | **1883** | MQTT message broker |

---

## Connection Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Browser)                           │
│  Frontend: index.html (Alpine.js + Tailwind)               │
│  Runs on: python3 -m http.server 3000                      │
│  OR: any static server                                     │
└────────────┬────────────────────────────────────────────┘
             │
             │ REST API (http://localhost:8123/api/*)
             │ WebSocket (ws://localhost:8123/api/websocket)
             │ Auth: Long-Lived Access Token (Bearer)
             ▼
┌─────────────────────────────────────────────────────────┐
│              HOME ASSISTANT (Docker)                     │
│  Port 8123                                               │
│  - Receives commands (turn_on/toggle/turn_off)           │
│  - Publishes MQTT commands to Mosquitto                  │
│  - Receives state updates from ESP32 via MQTT            │
│  - Stores state history in PostgreSQL                    │
│  - Exposes REST API for states, history, services        │
│  - CORS configured for localhost:3000                    │
└────┬────────────────────┬──────────────────────────────┘
     │                    │
     │ MQTT (internal)    │ PostgreSQL (internal)
     │ host: ha-mosquitto │ host: ha-postgres
     │ port: 1883         │ port: 5432
     │                    │ user: homeassistant
     ▼                    ▼
┌──────────────┐   ┌──────────────────┐
│  MOSQUITTO   │   │   POSTGRESQL     │
│  MQTT Broker │   │  (Docker)        │
│  Port 1883   │   │  Port 5432       │
│  anonymous   │   │  DB: homeassistant│
│  (no auth)   │   │  Tables: states, │
└──────┬───────┘   │  events, etc.    │
       │           └──────────────────┘
       │ MQTT
       │ (WiFi network)
       ▼
┌────────────────────────────────────────────────────────┐
│               ESP32 (MicroPython)                      │
│  WiFi: house_network                                   │
│  MQTT Broker: 192.168.78.111:1883                      │
│                                                        │
│  Hardware:                                             │
│  ├─ GPIO13 → LED1                                      │
│  ├─ GPIO12 → LED2                                      │
│  ├─ GPIO14 → LED3                                      │
│  └─ GPIO15 → Servo (PWM, 50Hz)                        │
│                                                        │
│  On boot:                                              │
│  1. Connect WiFi                                       │
│  2. Connect MQTT                                       │
│  3. Publish discovery topics (HA auto-config)          │
│  4. Subscribe to command topics                        │
│  5. Main loop: check_msg() + heartbeat every 30s       │
└────────────────────────────────────────────────────────┘
```

---

## How Components Interact (Step by Step)

### 1. ESP32 → Home Assistant (Device Discovery)
- ESP32 publishes **MQTT discovery messages** to `homeassistant/light/{id}/led1/config` etc.
- Home Assistant (subscribed to Mosquitto) auto-creates entities: 3 lights + 1 cover (servo)

### 2. Frontend → Home Assistant (User Commands)
- `index.html` authenticates with a **Long-Lived Access Token** via `GET /api/`
- Opens **WebSocket** at `ws://localhost:8123/api/websocket` for real-time state updates
- Sends commands via `POST /api/services/{domain}/{action}` (e.g., `light/turn_on`)
- Fetches states via `GET /api/states`, history via `GET /api/history/period/...`

### 3. Home Assistant → ESP32 (Command Execution)
- HA receives the REST API call → publishes to the ESP32's MQTT **command topic**
- Mosquitto forwards the message → ESP32 receives it in `mqtt_callback()`
- ESP32 actuates hardware (LED on/off, servo angle)

### 4. ESP32 → Home Assistant (State Feedback)
- ESP32 publishes **state** back to MQTT (e.g., `led1/state: "ON"`)
- HA receives the MQTT message → updates the entity state
- Frontend WebSocket receives the `state_changed` event → UI updates in real-time

### 5. Home Assistant → PostgreSQL (History Persistence)
- HA's `recorder` integration (configured in `configuration.yaml`) writes every state change to PostgreSQL
- Connection string: `postgresql://homeassistant:hass_password@ha-postgres:5432/homeassistant`
- Retains 30 days of history for `light`, `switch`, `sensor`, `binary_sensor` domains

---

## Entrypoint Customization

The custom `entrypoint.sh` installs `psycopg2-binary` at container startup before launching HA, enabling the PostgreSQL connection. Without this, HA defaults to SQLite.

---

## Key Files

| File | Role |
|---|---|
| `docker-compose.yml` | Defines all 3 containers, volumes, ports, env vars |
| `homeassistant_config/configuration.yaml` | HA config: DB URL, CORS, recorder domains |
| `homeassistant_config/entrypoint.sh` | Installs psycopg2, starts HA |
| `esp32/main.py` | ESP32 firmware: WiFi, MQTT, GPIO control, discovery |
| `esp32/config.py` | WiFi/MQTT credentials (edit for your network) |
| `esp32/boot.py` | Auto-runs `main()` on power-up |
| `frontend/index.html` | Single-page dashboard: auth, device control, history, DB logs |
| `scripts/service_restart.sh` | Restarts HA container with health check |
| `scripts/ha_configuration_backup.sh` | Backs up config + PostgreSQL dump to `./backups/` |
| `scripts/container_log_monitoring.sh` | Monitor HA logs for errors, follow mode, statistics |
