#!/bin/bash
# restart_ha.sh - Restart Home Assistant container

# Configuration
CONTAINER_NAME="homeassistant"  # Change if your container has a different name
SERVICE_WAIT_TIME=60
MAX_WAIT_TIME=180

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Restarting Home Assistant container...${NC}"

# Check if container exists and is running
if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Container $CONTAINER_NAME is not running or doesn't exist${NC}"
    
    # Check if it exists but is stopped
    if docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo "Container exists but is stopped. Starting it..."
        docker start "$CONTAINER_NAME"
    else
        echo -e "${RED}Container $CONTAINER_NAME not found${NC}"
        exit 1
    fi
fi

# Get container health before restart
OLD_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null)
echo "Current health status: ${OLD_HEALTH:-unknown}"

# Restart container
echo "Restarting container..."
docker restart "$CONTAINER_NAME"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to restart container${NC}"
    exit 1
fi

echo -e "${GREEN}Container restart command sent${NC}"

# Wait for container to be healthy
echo "Waiting for Home Assistant to start (max ${MAX_WAIT_TIME}s)..."
WAIT_TIME=0
while [ $WAIT_TIME -lt $MAX_WAIT_TIME ]; do
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$CONTAINER_NAME" | grep -q "healthy"; then
        echo -e "${GREEN}✓ Home Assistant is healthy and running!${NC}"
        break
    elif docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$CONTAINER_NAME" | grep -q "unhealthy"; then
        echo -e "${RED}✗ Container is unhealthy! Check logs for details.${NC}"
        exit 1
    fi
    
    sleep 5
    WAIT_TIME=$((WAIT_TIME + 5))
    echo -n "."
done

if [ $WAIT_TIME -ge $MAX_WAIT_TIME ]; then
    echo -e "\n${RED}Timeout: Home Assistant didn't become healthy within ${MAX_WAIT_TIME}s${NC}"
    echo "Check container status with: docker ps -a"
    exit 1
fi

# Check web interface
echo "Checking web interface..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8123 | grep -q "200"; then
    echo -e "${GREEN}✓ Web interface is responding${NC}"
else
    echo -e "${YELLOW}⚠ Web interface not responding yet (may take a few more seconds)${NC}"
fi

echo -e "${GREEN}Restart completed successfully!${NC}"
