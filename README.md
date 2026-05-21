# SMART APARTMENT PROJECT WITH HOME ASSISTANCE - ESP32 

## Scripts usage:

### 1. Make scripts executable:
```
chmod +x backup_ha.sh restart_ha.sh monitor_ha_logs.sh
```

### 2. Edit the configuration variables in each script (paths, container name, etc.)

### 3. Run scripts:
```
# Backup
./backup_ha.sh

# Restart service
./restart_ha.sh

# Monitor logs (interactive menu)
./monitor_ha_logs.sh

# Or with arguments:
./monitor_ha_logs.sh check 100  # Check last 100 lines
./monitor_ha_logs.sh follow     # Follow logs in real-time
./monitor_ha_logs.sh stats      # Show statistics
```

### Set up cron jobs for automation:
```
# Daily backup at 2 AM
0 2 * * * /path/to/backup_ha.sh >> /var/log/ha_backup.log 2>&1

# Weekly restart on Sunday at 3 AM
0 3 * * 0 /path/to/restart_ha.sh >> /var/log/ha_restart.log 2>&1

# Log check every hour
0 * * * * /path/to/monitor_ha_logs.sh check 100 >> /var/log/ha_monitor.log 2>&1
```

## Data Locations

| Script | Data Location |
|--------|---------------|
| Backup (`ha_configuration_backup.sh`) | `./backups/` - config tar.gz + DB dump |
| Restart (`service_restart.sh`) | No local files - operates on container |
| Log monitoring (`container_log_monitoring.sh`) | No local files - reads container logs |

## Runing/stop project: docker compose

```
docker-compose up -d
```

```
docker-compose down
```

After running docker-compose up -d, the Home Assistant UI will be accessible at:
http://localhost:8123

Docker maps the internal ports of the containers to your computer's localhost (127.0.0.1). Here is what "available" looks like for each service:

1. **Home Assistant (Port 8123)**: You can open a web browser and go to http://localhost:8123 to see the Home Assistant dashboard and configure your smart home.
2. **PostgreSQL (Port 5432)**: You can use a database tool (like DBeaver or the psql command) to connect to localhost:5432 and view the data Home Assistant is storing.
3. **Mosquitto (Port 1883)**: You can use an MQTT client (like MQTT Explorer) to connect to localhost:1883 and see messages being sent by your ESP32 devices or Home Assistant.

## PostgreSQL Recorder

Home Assistant stores entity state history in PostgreSQL (not SQLite).

### How It Works

Running `docker-compose up -d` automatically:
- Installs psycopg2-binary driver
- Connects to PostgreSQL (`ha-postgres:5432`)
- Creates database tables
- Stores state history

No manual setup required. Configuration is in `homeassistant_config/configuration.yaml`.

### Query state history

```bash
psql -h localhost -U homeassistant -d homeassistant -c "SELECT * FROM states LIMIT 10;"
```

### Database access

Access via tools like DBeaver, pgAdmin, or command line:
psql -h localhost -U homeassistant -d homeassistant
Password: hass_password

## API & Frontend Integration

Home Assistant serves as a complete backend (REST API + WebSocket) that can be used directly by a custom frontend (e.g., Alpine.js + HTMX) without any middleware.

### Frontend Port & CORS Configuration
By default, the project is configured to allow frontend connections from **Port 3000**.
- Your frontend should run on: `http://localhost:3000`
- This is configured in `homeassistant_config/configuration.yaml` under `http: cors_allowed_origins:`

If you run your frontend on a different port, update the `cors_allowed_origins` list in `configuration.yaml` and restart the container:
```bash
docker-compose restart homeassistant
```

### Authentication
Generate a **Long-Lived Access Token** in your Home Assistant profile (`http://localhost:8123/profile`) to authenticate your frontend requests.
- **REST API**: Include in headers: `Authorization: Bearer <YOUR_TOKEN>`
- **WebSocket**: Send auth message immediately after connection: `{"type": "auth", "access_token": "<YOUR_TOKEN>"}`

### API Endpoints
- **REST API**: `http://localhost:8123/api/` (States, Services, History)
- **WebSocket**: `ws://localhost:8123/api/websocket` (Real-time state updates)

## Adding Devices

Here is the flow to make a device visible in the dashboard:

### 1. Physical Connection
Connect your device (e.g., an LED, relay, or sensor) to the ESP32's GPIO pins.

### 2. ESP32 Firmware (MQTT)
The ESP32 needs code to control the device and talk to Home Assistant via the Mosquitto broker. You can use ESPHome, Tasmota, or Arduino code.
- **Example (Arduino/MQTT)**: The ESP32 subscribes to a topic like `home/light/bedroom/set` and publishes its state to `home/light/bedroom/state`.

### 3. Entity Creation in Home Assistant
Home Assistant needs to know the device exists. This happens in two ways:
- **MQTT Discovery (Recommended)**: If your ESP32 sends a specific "discovery message" to the `homeassistant/` topic, HA will automatically create the entity (e.g., `light.bedroom_lamp`).
- **Manual Configuration**: You can manually define the device in `configuration.yaml` under the `mqtt:` section.

### 4. Add to Dashboard
Once the entity exists in Home Assistant (you can verify this by checking the **Developer Tools > States** page in the HA UI):
1. Copy the **Entity ID** (e.g., `light.bedroom_lamp`).
2. Open your Alpine.js dashboard.
3. Enter that ID in the **"Add Device"** input field and click **Add**.

**Summary**: The dashboard is just a remote control for entities that already exist inside Home Assistant. If the ESP32 hasn't reported the device to HA yet, the dashboard won't see it.