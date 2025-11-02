"""nws_alert sensors."""

import logging
from typing import Final

from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import ATTRIBUTION, CONF_GPS_LOC, CONF_TRACKER, CONF_ZONE_ID, COORDINATOR, DOMAIN

SENSOR_TYPES: Final[dict[str, SensorEntityDescription]] = {
    "state": SensorEntityDescription(key="state", name="Alerts", icon="mdi:alert"),
    "last_updated": SensorEntityDescription(
        name="Last Updated",
        key="last_updated",
        icon="mdi:update",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
}

# ---------------------------------------------------------
# API Documentation
# ---------------------------------------------------------
# https://www.weather.gov/documentation/services-web-api
# https://forecast-v3.weather.gov/documentation
# ---------------------------------------------------------

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Sensor platform setup."""
    sensors = [NWSAlertSensor(hass, entry, sensor) for sensor in SENSOR_TYPES.values()]
    async_add_entities(sensors, True)


class NWSAlertSensor(CoordinatorEntity):
    """Representation of a Sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        sensor_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass.data[DOMAIN][entry.entry_id][COORDINATOR])
        self._config = entry
        self._key = sensor_description.key

        self._attr_icon = sensor_description.icon
        self._attr_name = f"{entry.data[CONF_NAME]} {sensor_description.name}"
        self._attr_device_class = sensor_description.device_class
        self._attr_unique_id = f"{slugify(self._attr_name)}_{entry.entry_id}"

    @property
    def state(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        if self._key in self.coordinator.data:
            return self.coordinator.data[self._key]
        return None

    @property
    def extra_state_attributes(self):
        """Return the state message."""
        attrs = {}
        if self.coordinator.data is None:
            return attrs
        if "alerts" in self.coordinator.data and self._key == "state":
            attrs["Alerts"] = self.coordinator.data["alerts"]

        # Add configuration information for diagnostics
        config_data = self._config.data

        if CONF_ZONE_ID in config_data:
            attrs["configuration_type"] = "Zone ID"
            attrs["zone_id"] = config_data[CONF_ZONE_ID]
        elif CONF_GPS_LOC in config_data:
            attrs["configuration_type"] = "GPS Location"
            attrs["gps_location"] = config_data[CONF_GPS_LOC]
        elif CONF_TRACKER in config_data:
            attrs["configuration_type"] = "Device Tracker"
            attrs["tracker_entity"] = config_data[CONF_TRACKER]

        attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        config_data = self._config.data

        # Create a more descriptive device name based on configuration
        if CONF_ZONE_ID in config_data:
            zone_id = config_data[CONF_ZONE_ID]
            device_name = (
                f"NWS Alerts (Zone: {zone_id[:20]}...)"
                if len(zone_id) > 20
                else f"NWS Alerts (Zone: {zone_id})"
            )
        elif CONF_GPS_LOC in config_data:
            # Truncate GPS to 4 decimal places for readability (~11 meter precision)
            gps = config_data[CONF_GPS_LOC]
            try:
                parts = gps.replace(" ", "").split(",")
                lat = f"{float(parts[0]):.4f}"
                lon = f"{float(parts[1]):.4f}"
                device_name = f"NWS Alerts (GPS: {lat},{lon})"
            except (ValueError, IndexError):
                # Fallback if parsing fails
                device_name = (
                    f"NWS Alerts (GPS: {gps[:25]}...)"
                    if len(gps) > 25
                    else f"NWS Alerts (GPS: {gps})"
                )
        elif CONF_TRACKER in config_data:
            tracker_name = config_data[CONF_TRACKER].split(".")[-1]  # Get entity name part
            device_name = f"NWS Alerts (Tracker: {tracker_name})"
        else:
            device_name = "NWS Alerts"

        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config.entry_id)},
            manufacturer="NWS",
            name=device_name,
        )
