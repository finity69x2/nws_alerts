import logging
import uuid
from typing import Final

from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import ATTRIBUTION, COORDINATOR, DOMAIN

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
    """Setup the sensor platform."""
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
        self.coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
        self._key = sensor_description.key

        self._attr_icon = sensor_description.icon
        self._attr_name = f'{entry.data[CONF_NAME]} {sensor_description.name}'
        self._attr_device_class = sensor_description.device_class
        self._attr_unique_id = f"{slugify(self._attr_name)}_{entry.entry_id}"

    @property
    def state(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        elif self._key in self.coordinator.data.keys():
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

        attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config.entry_id)},
            manufacturer="NWS",
            name="NWS Alerts",
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data != "AttributeError":
            self.async_write_ha_state()
