#!/usr/bin/env python3
"""Fetch single entity state: GET /api/states/{entity_id}"""

import os
import sys
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN")
entity_id = sys.argv[1] if len(sys.argv) > 1 else None

if not HA_TOKEN:
    print("ERROR: HA_TOKEN not set in .env")
    exit(1)

if not entity_id:
    print("Usage: python3 get_entity_state.py <entity_id>")
    print("Example: python3 get_entity_state.py light.esp32_device_xxx_led1")
    exit(1)

req = urllib.request.Request(
    f"{HA_URL}/api/states/{entity_id}",
    headers={"Authorization": f"Bearer {HA_TOKEN}"},
)

try:
    with urllib.request.urlopen(req) as resp:
        s = json.loads(resp.read())
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode()}")
    exit(1)
except urllib.error.URLError as e:
    print(f"Connection failed: {e.reason}")
    exit(1)

attrs = s.get("attributes", {})
print(json.dumps({
    "entity_id": s["entity_id"],
    "state": s["state"],
    "last_changed": s["last_changed"],
    "last_updated": s["last_updated"],
    "friendly_name": attrs.get("friendly_name"),
    "area_id": attrs.get("area_id"),
}, indent=2))
