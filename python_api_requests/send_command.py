#!/usr/bin/env python3
"""Send a command to an entity: POST /api/services/{domain}/{action}"""

import os
import sys
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

if len(sys.argv) < 3:
    print("Usage: python3 send_command.py <entity_id> <action> [extra_json]")
    print("")
    print("Examples:")
    print("  python3 send_command.py light.esp32_device_xxx_led1 turn_on")
    print("  python3 send_command.py light.esp32_device_xxx_led1 turn_off")
    print("  python3 send_command.py cover.esp32_device_xxx_servo close")
    print("  python3 send_command.py cover.esp32_device_xxx_servo open")
    exit(1)

entity_id = sys.argv[1]
action = sys.argv[2]
domain = entity_id.split(".")[0]

payload = {"entity_id": entity_id}
if len(sys.argv) > 3:
    payload.update(json.loads(sys.argv[3]))

req = urllib.request.Request(
    f"{HA_URL}/api/services/{domain}/{action}",
    method="POST",
    headers={
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    },
    data=json.dumps(payload).encode(),
)

try:
    with urllib.request.urlopen(req) as resp:
        results = json.loads(resp.read())
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode()}")
    exit(1)
except urllib.error.URLError as e:
    print(f"Connection failed: {e.reason}")
    exit(1)

print(f"OK — {domain}/{action} sent to {entity_id}")
for s in results:
    print(f"  {s['entity_id']:45s} → {s['state']}")
