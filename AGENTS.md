# Home Assistant Project

## Quick Start

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down
```

## Services

- **Home Assistant**: http://localhost:8123
- **PostgreSQL**: localhost:5432 (user: `homeassistant`, password: `hass_password`, db: `homeassistant`)
- **Mosquitto (MQTT)**: localhost:1883 (anonymous access enabled)

## Project Structure

```
ha_project/
├── docker-compose.yml               # 3 containers: HA, PostgreSQL, Mosquitto
├── .env                             # HA URL/Token, PG, MQTT env vars
├── requirements.txt                 # Pins homeassistant==2025.1.4
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
├── README.md                        # Full system documentation
├── summary.md                       # Project summary
└── technical_document.md            # Technical reference
```

## Scripts

All scripts in `scripts/` require `chmod +x` before execution:

| Script | Usage |
|--------|-------|
| `scripts/service_restart.sh` | Restart HA container with health check |
| `scripts/ha_configuration_backup.sh` | Backup HA config + DB dump to `./backups/` |
| `scripts/container_log_monitoring.sh` | Monitor logs - usage: `check <lines>`, `follow`, `stats` |

### Cron Examples
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/scripts/ha_configuration_backup.sh >> /var/log/ha_backup.log 2>&1

# Log check every hour
0 * * * * /path/to/scripts/container_log_monitoring.sh check 100 >> /var/log/ha_monitor.log 2>&1
```

## Frontend

Served locally (not in Docker):
```bash
python3 -m http.server 3000 -d frontend
```
- Open http://localhost:3000
- Paste a Home Assistant Long-Lived Access Token (generate at http://localhost:8123/profile)
- The dashboard uses HA REST API (`/api/*`) and WebSocket (`/api/websocket`) for real-time updates
- CORS is configured in HA to allow `http://localhost:3000`

## ESP32 Firmware

Files in `esp32/` are MicroPython firmware for ESP32:
- `main.py` — connects to WiFi/MQTT, subscribes to command topics, controls GPIO (LEDs on GPIO13/12/14, servo on GPIO15), publishes HA discovery and heartbeat
- `config.py` — WiFi SSID/password, MQTT broker address/port
- `boot.py` — auto-runs `main.main()` on power-up

Flash with Thonny IDE (or ampy/rshell). See `esp32/ESP32.md` for pinout and MQTT test commands.

## Custom Component: esp_health

Located at `homeassistant_config/custom_components/esp_health/`. Monitors ESP32 device health via MQTT. Configured in `configuration.yaml`:

```yaml
esp_health:
  broker: ha-mosquitto
  port: 1883
  devices:
    - name: "ESP32 Controller"
      device_id: "esp32_device_a0b7652a758c"
```

## PostgreSQL Recorder

Home Assistant stores entity state history in PostgreSQL (not SQLite). Running `docker-compose up -d` automatically:
- Installs `psycopg2-binary` driver via entrypoint
- Connects to PostgreSQL (`ha-postgres:5432`)
- Creates database tables
- Stores state history

Query history:
```bash
psql -h localhost -U homeassistant -d homeassistant -c "SELECT * FROM states LIMIT 10;"
```

## Configuration

HA configuration lives in `homeassistant_config/configuration.yaml`:
- **Recorder**: PostgreSQL connection (`ha-postgres:5432`), 30-day retention for `light`, `switch`, `sensor`, `binary_sensor`
- **CORS**: allows `http://localhost:3000` (frontend)
- **esp_health**: ESP32 device health monitoring via MQTT

Custom entrypoint (`homeassistant_config/entrypoint.sh`) handles psycopg2 installation and HA startup.

## Environment Variables (`.env`)

```
HA_URL=http://localhost:8123
HA_TOKEN=<long-lived-access-token>
PG_HOST=localhost, PG_PORT=5432, PG_USER=homeassistant, PG_PASSWORD=hass_password, PG_DATABASE=homeassistant
MQTT_HOST=localhost, MQTT_PORT=1883
```

Used by Python API scripts in `python_api_requests/` and direct DB queries.

## Requirements

```txt
homeassistant==2025.1.4
```
Install with `pip install -r requirements.txt` for Python-based tooling.

## Key Files

- `docker-compose.yml` - Service definitions (PostgreSQL 15, Mosquitto 2, HA stable)
- `.env` - Environment variables for HA API, PostgreSQL, MQTT access
- `requirements.txt` - Python dependency pinning
- `homeassistant_config/configuration.yaml` - HA config (CORS, recorder, esp_health)
- `homeassistant_config/entrypoint.sh` - Custom HA startup script
- `homeassistant_config/custom_components/esp_health/` - ESP32 health monitoring integration
- `frontend/index.html` - Alpine.js/HTMX dashboard
- `frontend/style.css` - Dashboard styles
- `esp32/main.py` - ESP32 firmware
- `esp32/config.py` - ESP32 WiFi/MQTT credentials
- `esp32/ESP32.md` - Pinout and MQTT test commands
- `documents/` - System planning docs (flowcharts, pseudocode, state tables)
- `README.md` - Full system documentation

## Project Context

Smart apartment project using Home Assistant + ESP32 devices. MQTT broker handles device communication, PostgreSQL stores state history. Frontend uses Alpine.js + HTMX + Tailwind CSS for a real-time dashboard served locally. ESP32 runs MicroPython with MQTT auto-discovery and HA integration.