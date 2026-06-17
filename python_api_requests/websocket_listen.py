#!/usr/bin/env python3
"""Listen to real-time HA events via WebSocket: ws://{HA_URL}/api/websocket

Requires: pip install aiohttp
"""

import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN")

if not HA_TOKEN:
    print("ERROR: HA_TOKEN not set in .env")
    exit(1)

WS_URL = HA_URL.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"


async def listen():
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WS_URL) as ws:
            auth_msg = await ws.receive_json()
            if auth_msg.get("type") != "auth_required":
                print(f"Unexpected: {auth_msg}")
                return

            await ws.send_json({"type": "auth", "access_token": HA_TOKEN})
            auth_result = await ws.receive_json()
            if auth_result.get("type") != "auth_ok":
                print(f"Auth failed: {auth_result}")
                return

            print("Authenticated. Subscribing to state_changed events...")
            await ws.send_json({
                "id": 1,
                "type": "subscribe_events",
                "event_type": "state_changed",
            })

            print("Listening for state changes (Ctrl+C to stop)...\n")
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    event = data.get("event")
                    if event and event.get("event_type") == "state_changed":
                        entity_id = event["data"]["entity_id"]
                        old = event["data"].get("old_state", {}) or {}
                        new = event["data"].get("new_state", {}) or {}
                        old_state = old.get("state", "?")
                        new_state = new.get("state", "?")
                        print(f"  {entity_id:45s} {old_state:15s} → {new_state}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break


if __name__ == "__main__":
    try:
        asyncio.run(listen())
    except KeyboardInterrupt:
        print("\nStopped.")
