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
- **PostgreSQL**: localhost:5432 (user: `homeassistant`, password: `hass_password`)
- **Mosquitto (MQTT)**: localhost:1883

## Scripts

All scripts in `scripts/` require `chmod +x` before execution:

| Script | Usage |
|--------|-------|
| `scripts/service_restart.sh` | Restart HA container with health check |
| `scripts/ha_configuration_backup.sh` | Backup HA config (edit paths first) |
| `scripts/container_log_monitoring.sh` | Monitor logs - usage: `check <lines>`, `follow`, `stats` |

## Configuration

HA configuration lives in `homeassistant_config/` (gitignored). Edit paths in scripts before running.

## Key Files

- `docker-compose.yml` - Service definitions
- `documents/` - System planning documents