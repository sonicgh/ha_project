#!/bin/bash
set -e

echo "Installing psycopg2-binary..."
pip install psycopg2-binary -q

echo "Starting Home Assistant..."
exec python -m homeassistant --config /config