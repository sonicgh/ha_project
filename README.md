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