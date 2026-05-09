#!/bin/bash
# monitor_ha_logs.sh - Monitor Home Assistant logs

# Configuration
CONTAINER_NAME="homeassistant"
LOG_FILE="/var/log/ha_monitor.log"  # Change as needed
ERROR_PATTERNS=("ERROR" "FATAL" "WARNING" "Exception" "Failed" "Unable")
ALERT_EMAIL="your-email@example.com"  # Optional: set for email alerts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to send alert
send_alert() {
    local message="$1"
    echo -e "${RED}[ALERT] $message${NC}"
    
    # Log to file
    echo "$(date): ALERT - $message" >> "$LOG_FILE"
    
    # Send email if configured
    if [ -n "$ALERT_EMAIL" ] && command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "Home Assistant Alert" "$ALERT_EMAIL"
    fi
}

# Function to check container logs
check_logs() {
    local lines=${1:-50}  # Default to last 50 lines
    
    echo -e "${BLUE}=== Home Assistant Log Monitor ===${NC}"
    echo "Monitoring container: $CONTAINER_NAME"
    echo "Checking last $lines lines of logs..."
    echo "----------------------------------------"
    
    # Get container logs
    LOGS=$(docker logs --tail "$lines" "$CONTAINER_NAME" 2>&1)
    
    if [ -z "$LOGS" ]; then
        echo -e "${YELLOW}No logs found or container not running${NC}"
        return 1
    fi
    
    # Display recent logs
    echo -e "${BLUE}Recent logs:${NC}"
    echo "$LOGS" | tail -20
    
    # Check for errors/warnings
    echo "----------------------------------------"
    echo -e "${YELLOW}Scanning for issues...${NC}"
    
    for pattern in "${ERROR_PATTERNS[@]}"; do
        matches=$(echo "$LOGS" | grep -i "$pattern" | wc -l)
        if [ $matches -gt 0 ]; then
            echo -e "${RED}Found $matches occurrence(s) of '$pattern'${NC}"
            echo "$LOGS" | grep -i "$pattern" | head -5 | while read line; do
                echo "  → $line"
            done
            echo ""
            
            # Send alert for critical errors
            if [[ "$pattern" == "ERROR" ]] || [[ "$pattern" == "FATAL" ]]; then
                send_alert "Critical: Found $pattern in logs (${matches} times)"
            fi
        fi
    done
    
    echo "----------------------------------------"
    echo -e "${GREEN}Log check completed${NC}"
}

# Function to follow logs in real-time
follow_logs() {
    echo -e "${BLUE}Following logs in real-time (Ctrl+C to stop)...${NC}"
    echo -e "${YELLOW}Highlighted patterns: ${ERROR_PATTERNS[*]}${NC}\n"
    
    docker logs -f "$CONTAINER_NAME" 2>&1 | while read line; do
        colored=false
        for pattern in "${ERROR_PATTERNS[@]}"; do
            if echo "$line" | grep -qi "$pattern"; then
                echo -e "${RED}$line${NC}"
                colored=true
                
                # Log critical errors to file
                if [[ "$pattern" == "ERROR" ]] || [[ "$pattern" == "FATAL" ]]; then
                    echo "$(date): $line" >> "$LOG_FILE"
                fi
                break
            fi
        done
        
        if [ "$colored" = false ]; then
            echo "$line"
        fi
    done
}

# Function to show log statistics
show_stats() {
    echo -e "${BLUE}=== Log Statistics ===${NC}"
    
    # Get last 1000 lines for analysis
    LOGS=$(docker logs --tail 1000 "$CONTAINER_NAME" 2>&1)
    
    echo "Time range: Last 1000 lines"
    echo "----------------------------------------"
    
    for pattern in "${ERROR_PATTERNS[@]}"; do
        count=$(echo "$LOGS" | grep -ic "$pattern")
        echo "$pattern: $count occurrences"
    done
    
    # Top error sources
    echo "----------------------------------------"
    echo -e "${YELLOW}Top 5 error sources:${NC}"
    echo "$LOGS" | grep -i "error" | awk '{print $4}' | sort | uniq -c | sort -rn | head -5
}

# Main menu
show_menu() {
    echo ""
    echo -e "${BLUE}Home Assistant Log Monitor${NC}"
    echo "1) Check recent logs (last 50 lines)"
    echo "2) Check recent logs (last 200 lines)"
    echo "3) Follow logs in real-time"
    echo "4) Show log statistics"
    echo "5) Exit"
    echo -n "Select option [1-5]: "
}

# Main execution
case "${1}" in
    check)
        check_logs "${2:-50}"
        ;;
    follow)
        follow_logs
        ;;
    stats)
        show_stats
        ;;
    *)
        while true; do
            show_menu
            read option
            case $option in
                1) check_logs 50 ;;
                2) check_logs 200 ;;
                3) follow_logs ;;
                4) show_stats ;;
                5) echo "Exiting..."; exit 0 ;;
                *) echo -e "${RED}Invalid option${NC}" ;;
            esac
            echo ""
        done
        ;;
esac
