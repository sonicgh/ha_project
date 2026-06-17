#!/usr/bin/env python3
"""Validate HA token: GET /api/"""

import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN")

if not HA_TOKEN:
    print("ERROR: HA_TOKEN not set in .env")
    exit(1)

req = urllib.request.Request(
    f"{HA_URL}/api/",
    headers={
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    },
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print(f"Token valid — HA version: {data.get('message', 'N/A')}")
except urllib.error.HTTPError as e:
    print(f"Token invalid or HA unreachable: {e.code} {e.read().decode()}")
except urllib.error.URLError as e:
    print(f"Connection failed: {e.reason}")
