"""Sensor platform for ESP32 Device Health."""
from __future__ import annotations
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN, DATA_DEVICES, SENSOR_TYPES, _initial_state

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    devices = hass.data.get(DATA_DEVICES, {})
    if not devices:
        _LOGGER.warning("No ESP devices configured")
        return

    sensors = []

    for device_id, device_info in devices.items():
        for sensor_type, sensor_meta in SENSOR_TYPES.items():
            sensor = ESPHealthSensor(device_id, device_info, sensor_type, sensor_meta)
            sensors.append(sensor)
            device_info["sensors"][sensor_type] = sensor

    async_add_entities(sensors)


class ESPHealthSensor(SensorEntity):
    def __init__(self, device_id, device_info, sensor_type, sensor_meta):
        self._device_id = device_id
        self._device_info = device_info
        self._sensor_type = sensor_type
        self._attr_name = f"{device_info[CONF_NAME]} {sensor_meta['name']}"
        self._attr_unique_id = f"{device_id}_{sensor_type}"
        self._attr_icon = sensor_meta["icon"]
        self._attr_native_unit_of_measurement = sensor_meta["unit"]
        self._attr_should_poll = False
        self._state = _initial_state(sensor_type)

    @property
    def native_value(self):
        return self._state

    @callback
    def _async_set_state(self, value: str) -> None:
        self._state = value
        self.async_write_ha_state()
