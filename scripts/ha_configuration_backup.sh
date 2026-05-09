#!/bin/bash
# backup_ha.sh - Backup Home Assistant configuration

# Configuration
BACKUP_DIR="/path/to/your/backup/location"  # Change this
HA_CONFIG_DIR="/path/to/ha/config"          # Change this (e.g., /home/user/homeassistant)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="ha_backup_${TIMESTAMP}"
RETENTION_DAYS=7

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Home Assistant backup...${NC}"

# Check if config directory exists
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo -e "${RED}Error: HA config directory not found at $HA_CONFIG_DIR${NC}"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup
echo "Creating backup: $BACKUP_NAME"
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" -C "$(dirname $HA_CONFIG_DIR)" "$(basename $HA_CONFIG_DIR)"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup completed successfully: ${BACKUP_NAME}.tar.gz${NC}"
    
    # Create backup info file
    echo "Backup created: $TIMESTAMP" > "${BACKUP_DIR}/${BACKUP_NAME}.info"
    echo "Config size: $(du -sh $HA_CONFIG_DIR | cut -f1)" >> "${BACKUP_DIR}/${BACKUP_NAME}.info"
    
    # Remove old backups
    echo "Cleaning backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "ha_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "ha_backup_*.info" -type f -mtime +$RETENTION_DAYS -delete
    
    # List current backups
    echo -e "${YELLOW}Current backups:${NC}"
    ls -lh "$BACKUP_DIR" | grep "ha_backup"
else
    echo -e "${RED}✗ Backup failed!${NC}"
    exit 1
fi
