#!/usr/bin/env python3
"""Get count and IDs of all ESP32-registered entities from Home Assistant"""

import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN")

if not HA_TOKEN:
    print("ERROR: HA_TOKEN not set in .env")
    exit(1)

req = urllib.request.Request(
    f"{HA_URL}/api/states",
    headers={"Authorization": f"Bearer {HA_TOKEN}"},
)

try:
    with urllib.request.urlopen(req) as resp:
        states = json.loads(resp.read())
except urllib.error.HTTPError as e:
    print(f"Error: {e.code} {e.read().decode()}")
    exit(1)
except urllib.error.URLError as e:
    print(f"Connection failed: {e.reason}")
    exit(1)

esp32_entities = [s for s in states if "esp32" in s["entity_id"].lower()]

print(f"ESP32 Entities: {len(esp32_entities)} found\n")
for s in sorted(esp32_entities, key=lambda x: x["entity_id"]):
    print(f"  {s['entity_id']}")
