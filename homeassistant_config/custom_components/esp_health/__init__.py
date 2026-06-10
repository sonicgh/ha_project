"""ESP32 Device Health Monitor."""
from __future__ import annotations
import json
import logging
from datetime import datetime

import paho.mqtt.client as mqtt
import voluptuous as vol

from homeassistant.const import CONF_NAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "esp_health"
DATA_DEVICES = f"{DOMAIN}_devices"
DATA_MQTT_CLIENT = f"{DOMAIN}_mqtt"

CONF_DEVICES = "devices"
CONF_DEVICE_ID = "device_id"
CONF_BROKER = "broker"
CONF_PORT = "port"

DEVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_BROKER): cv.string,
        vol.Optional(CONF_PORT, default=1883): cv.port,
        vol.Optional(CONF_DEVICES, default=[]):
            vol.All(cv.ensure_list, [DEVICE_SCHEMA]),
    })
}, extra=vol.ALLOW_EXTRA)

SENSOR_TYPES = {
    "online": {"name": "Online", "icon": "mdi:wifi", "unit": None},
    "last_seen": {"name": "Last Seen", "icon": "mdi:clock-outline", "unit": None},
    "rssi": {"name": "RSSI", "icon": "mdi:wifi-strength-3", "unit": "dBm"},
    "uptime": {"name": "Uptime", "icon": "mdi:timer-outline", "unit": "s"},
}


def _initial_state(sensor_type: str) -> str:
    defaults = {
        "online": "false",
        "last_seen": "never",
        "rssi": "0",
        "uptime": "0",
    }
    return defaults.get(sensor_type, "unknown")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    hass.data[DATA_DEVICES] = {}
    hass.data[DATA_MQTT_CLIENT] = None

    broker = conf[CONF_BROKER]
    port = conf[CONF_PORT]

    for device in conf.get(CONF_DEVICES, []):
        device_id = device[CONF_DEVICE_ID]
        hass.data[DATA_DEVICES][device_id] = {
            CONF_NAME: device[CONF_NAME],
            "sensors": {},
        }

    client = mqtt.Client(client_id="ha_esp_health", protocol=mqtt.MQTTv311)

    def on_connect(mqttc, userdata, flags, rc):
        _LOGGER.info("Connected to MQTT broker (rc=%s)", rc)
        for device_id in hass.data[DATA_DEVICES]:
            status_topic = f"homeassistant/sensor/{device_id}/status"
            telemetry_topic = f"homeassistant/sensor/{device_id}/telemetry"
            mqttc.subscribe(status_topic, qos=1)
            mqttc.subscribe(telemetry_topic, qos=1)
            _LOGGER.info("Subscribed to %s and %s", status_topic, telemetry_topic)

    def on_message(mqttc, userdata, msg):
        topic_parts = msg.topic.split("/")
        if len(topic_parts) < 4:
            return
        device_id = topic_parts[2]
        topic_type = topic_parts[3]
        if device_id not in hass.data[DATA_DEVICES]:
            return
        dev_data = hass.data[DATA_DEVICES][device_id]

        if topic_type == "status":
            payload = msg.payload.decode()
            _update_sensor(hass, device_id, "last_seen", datetime.now().isoformat())
            if payload == "online":
                _update_sensor(hass, device_id, "online", "true")
            elif payload == "offline":
                _update_sensor(hass, device_id, "online", "false")
        elif topic_type == "telemetry":
            try:
                data = json.loads(msg.payload)
                if "rssi" in data:
                    _update_sensor(hass, device_id, "rssi", str(data["rssi"]))
                if "uptime" in data:
                    _update_sensor(hass, device_id, "uptime", str(data["uptime"]))
            except (json.JSONDecodeError, TypeError):
                pass

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect_async(broker, port, keepalive=60)
        client.loop_start()
        hass.data[DATA_MQTT_CLIENT] = client
        _LOGGER.info("Connecting to MQTT broker at %s:%s", broker, port)
    except Exception as e:
        _LOGGER.error("Failed to connect to MQTT broker: %s", e)

    async def stop_mqtt(event):
        client.loop_stop()
        client.disconnect()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_mqtt)

    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    return True


def _update_sensor(hass: HomeAssistant, device_id: str, sensor_type: str, value: str):
    dev_data = hass.data[DATA_DEVICES][device_id]
    sensor = dev_data["sensors"].get(sensor_type)
    if sensor:
        hass.loop.call_soon_threadsafe(sensor._async_set_state, value)
