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

## Runining project

```
docker-compose up -d
```