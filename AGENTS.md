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

HA configuration lives in `homeassistant_config/` (gitignored). Edit paths in scripts before running.
Custom entrypoint (`homeassistant_config/entrypoint.sh`) handles psycopg2 installation and DB setup.

## Key Files

- `docker-compose.yml` - Service definitions (PostgreSQL 15, Mosquitto 2, HA stable)
- `homeassistant_config/entrypoint.sh` - Custom HA startup script
- `documents/` - System planning docs (flowcharts, pseudocode, state tables, ESP32 docs)
- `README.md` - Project overview and setup instructions

## Project Context

Smart apartment project using Home Assistant + ESP32 devices. MQTT broker handles device communication, PostgreSQL stores state history.