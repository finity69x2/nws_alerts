"""Adds config flow for NWS Alerts."""

from __future__ import annotations

import logging
from typing import Any, List

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.device_tracker import DOMAIN as TRACKER_DOMAIN
from homeassistant.const import CONF_FRIENDLY_NAME, CONF_NAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    API_ENDPOINT,
    CONF_ANNOUNCE_CRITICAL_ENTITIES,
    CONF_ANNOUNCE_CRITICAL_TYPES,
    CONF_ANNOUNCE_END_TIME,
    CONF_ANNOUNCE_ENTITIES,
    CONF_ANNOUNCE_START_TIME,
    CONF_ANNOUNCE_TYPES,
    CONF_GPS_LOC,
    CONF_INTERVAL,
    CONF_PERSISTENT_NOTIFICATIONS,
    CONF_SEND_ALERTS,
    CONF_SEND_CRITICAL_SERVICES,
    CONF_SEND_CRITICAL_TYPES,
    CONF_SEND_END_TIME,
    CONF_SEND_SERVICES,
    CONF_SEND_START_TIME,
    CONF_SEND_TYPES,
    CONF_TIMEOUT,
    CONF_TRACKER,
    CONF_ZONE_ID,
    DEFAULT_ANNOUNCE_END_TIME,
    DEFAULT_ANNOUNCE_START_TIME,
    DEFAULT_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_PERSISTENT_NOTIFICATIONS,
    DEFAULT_SEND_ALERTS,
    DEFAULT_SEND_END_TIME,
    DEFAULT_SEND_START_TIME,
    DEFAULT_TIMEOUT,
    DOMAIN,
    USER_AGENT,
)

JSON_FEATURES = "features"
JSON_PROPERTIES = "properties"
JSON_ID = "id"

_LOGGER = logging.getLogger(__name__)
MENU_OPTIONS = ["zone", "gps"]
MENU_GPS = ["gps_loc", "gps_tracker"]
ALERT_TYPES_LIST = [
    "Air Quality Alert",
    "Blizzard Warning",
    "Coastal Flood Advisory",
    "Coastal Flood Warning",
    "Coastal Flood Watch",
    "Dense Fog Advisory",
    "Excessive Heat Warning",
    "Excessive Heat Watch",
    "Extreme Wind Warning",
    "Fire Weather Watch",
    "Flash Flood Warning",
    "Flood Warning",
    "Flood Watch",
    "Freeze Warning",
    "Freeze Watch",
    "Frost Advisory",
    "Gale Warning",
    "Hazardous Weather Outlook",
    "Heat Advisory",
    "High Wind Warning",
    "High Wind Watch",
    "Hurricane Force Wind Warning",
    "Hurricane Warning",
    "Hurricane Watch",
    "Ice Storm Warning",
    "Red Flag Warning",
    "River Flood Warning",
    "River Flood Watch",
    "Severe Thunderstorm Warning",
    "Severe Thunderstorm Watch",
    "Small Craft Advisory",
    "Special Marine Warning",
    "Special Weather Statement",
    "Storm Warning",
    "Tornado Warning",
    "Tornado Watch",
    "Tropical Storm Warning",
    "Tropical Storm Watch",
    "Wind Advisory",
    "Wind Chill Advisory",
    "Wind Chill Warning",
    "Winter Storm Warning",
    "Winter Storm Watch",
    "Winter Weather Advisory",
]
ALERT_TYPES_LIST.sort()
ANNOUNCE_MEDIA_PLAYER_INTEGRATION_LIST = ["alexa_media"]


async def _async_get_announce_media_player_entities(hass: HomeAssistant):
    """Get the list of media players"""
    media_player_list = []
    entity_registry = er.async_get(hass)
    for ent in hass.states.async_all(Platform.MEDIA_PLAYER):
        er_ent = entity_registry.async_get(ent.entity_id)
        # _LOGGER.debug(f"Entity ID: {ent.entity_id}, Platform: {er_ent.platform}")
        if er_ent.platform in ANNOUNCE_MEDIA_PLAYER_INTEGRATION_LIST:
            media_player_list.append(
                selector.SelectOptionDict(
                    value=str(ent.entity_id),
                    label=f"{ent.attributes.get(CONF_FRIENDLY_NAME)} ({er_ent.platform})",
                )
            )
    if media_player_list:
        media_player_list_sorted = sorted(
            media_player_list, key=lambda d: d["label"].casefold()
        )
    else:
        media_player_list_sorted = []
    # _LOGGER.debug(f"Media Player List: {media_player_list_sorted}")
    return media_player_list_sorted


def _get_schema_zone(hass: Any, user_input: list, default_dict: list) -> Any:
    """Gets a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key):
        """Gets default value for key."""
        return user_input.get(key, default_dict.get(key))

    schema = vol.Schema(
        {
            vol.Required(CONF_ZONE_ID, default=_get_default(CONF_ZONE_ID)): str,
            vol.Optional(CONF_NAME, default=_get_default(CONF_NAME)): str,
            vol.Optional(CONF_INTERVAL, default=_get_default(CONF_INTERVAL)): int,
            vol.Optional(CONF_TIMEOUT, default=_get_default(CONF_TIMEOUT)): int,
        }
    )
    return _add_alert_options_to_schema(hass, user_input, default_dict, schema)


def _get_schema_gps(hass: Any, user_input: list, default_dict: list) -> Any:
    """Gets a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key):
        """Gets default value for key."""
        return user_input.get(key, default_dict.get(key))

    schema = vol.Schema(
        {
            vol.Required(CONF_GPS_LOC, default=_get_default(CONF_GPS_LOC)): str,
            vol.Optional(CONF_NAME, default=_get_default(CONF_NAME)): str,
            vol.Optional(CONF_INTERVAL, default=_get_default(CONF_INTERVAL)): int,
            vol.Optional(CONF_TIMEOUT, default=_get_default(CONF_TIMEOUT)): int,
        }
    )
    return _add_alert_options_to_schema(hass, user_input, default_dict, schema)


def _get_schema_tracker(hass: Any, user_input: list, default_dict: list) -> Any:
    """Gets a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> None:
        """Gets default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    schema = vol.Schema(
        {
            vol.Required(
                CONF_TRACKER, default=_get_default(CONF_TRACKER, "(none)")
            ): vol.In(_get_entities(hass, TRACKER_DOMAIN)),
            vol.Optional(CONF_NAME, default=_get_default(CONF_NAME)): str,
            vol.Optional(CONF_INTERVAL, default=_get_default(CONF_INTERVAL)): int,
            vol.Optional(CONF_TIMEOUT, default=_get_default(CONF_TIMEOUT)): int,
        }
    )
    return _add_alert_options_to_schema(hass, user_input, default_dict, schema)


def _add_alert_options_to_schema(
    hass: HomeAssistant, user_input: list, default_dict: list, schema
) -> Any:
    """Gets a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> None:
        """Gets default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    schema = schema.extend(
        {
            vol.Optional(
                CONF_SEND_ALERTS, default=_get_default(CONF_SEND_ALERTS)
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
        }
    )
    return schema


async def _async_get_schema_alerts(
    hass: HomeAssistant, user_input: list, default_dict: list
) -> Any:
    """Gets a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> None:
        """Gets default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    _LOGGER.debug(f"hass.data['mobile_app']: {hass.data['mobile_app']}")

    # NOTIFY_SERVICES_LIST = list(hass.services.async_services_for_domain("notify").keys())
    NOTIFY_SERVICES_LIST = []
    for service in hass.services.async_services_for_domain("notify").keys():
        if service.startswith("mobile_app"):
            NOTIFY_SERVICES_LIST.append(service)
    NOTIFY_SERVICES_LIST.sort()
    _LOGGER.debug(f"NOTIFY_SERVICES_LIST: {NOTIFY_SERVICES_LIST}")

    return vol.Schema(
        {
            vol.Optional(
                CONF_PERSISTENT_NOTIFICATIONS,
                default=_get_default(CONF_PERSISTENT_NOTIFICATIONS),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            vol.Optional(
                CONF_ANNOUNCE_CRITICAL_TYPES,
                default=_get_default(CONF_ANNOUNCE_CRITICAL_TYPES, []),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=ALERT_TYPES_LIST,
                    multiple=True,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_ANNOUNCE_CRITICAL_ENTITIES,
                default=_get_default(CONF_ANNOUNCE_CRITICAL_ENTITIES, []),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=await _async_get_announce_media_player_entities(hass),
                    multiple=True,
                    custom_value=False,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_ANNOUNCE_TYPES, default=_get_default(CONF_ANNOUNCE_TYPES, [])
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=ALERT_TYPES_LIST,
                    multiple=True,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_ANNOUNCE_ENTITIES,
                default=_get_default(CONF_ANNOUNCE_ENTITIES, []),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=await _async_get_announce_media_player_entities(hass),
                    multiple=True,
                    custom_value=False,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_ANNOUNCE_START_TIME, default=_get_default(CONF_ANNOUNCE_START_TIME)
            ): selector.TimeSelector(selector.TimeSelectorConfig()),
            vol.Optional(
                CONF_ANNOUNCE_END_TIME, default=_get_default(CONF_ANNOUNCE_END_TIME)
            ): selector.TimeSelector(selector.TimeSelectorConfig()),
            vol.Optional(
                CONF_SEND_CRITICAL_TYPES,
                default=_get_default(CONF_SEND_CRITICAL_TYPES, []),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=ALERT_TYPES_LIST,
                    multiple=True,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_SEND_CRITICAL_SERVICES,
                default=_get_default(CONF_SEND_CRITICAL_SERVICES, []),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=NOTIFY_SERVICES_LIST,
                    multiple=True,
                    custom_value=False,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_SEND_TYPES, default=_get_default(CONF_SEND_TYPES, [])
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=ALERT_TYPES_LIST,
                    multiple=True,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_SEND_SERVICES, default=_get_default(CONF_SEND_SERVICES, [])
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=NOTIFY_SERVICES_LIST,
                    multiple=True,
                    custom_value=False,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_SEND_START_TIME, default=_get_default(CONF_SEND_START_TIME)
            ): selector.TimeSelector(selector.TimeSelectorConfig()),
            vol.Optional(
                CONF_SEND_END_TIME, default=_get_default(CONF_SEND_END_TIME)
            ): selector.TimeSelector(selector.TimeSelectorConfig()),
        }
    )


def _get_entities(
    hass: HomeAssistant,
    domain: str,
    search: List[str] = None,
    extra_entities: List[str] = None,
) -> List[str]:
    data = ["(none)"]
    if domain not in hass.data:
        return data

    for entity in hass.data[domain].entities:
        if search is not None and not any(map(entity.entity_id.__contains__, search)):
            continue
        data.append(entity.entity_id)

    if extra_entities:
        data.extend(extra_entities)

    return data


async def _get_zone_list(self) -> list | None:
    """Return list of zone by lat/lon"""

    data = None
    lat = self.hass.config.latitude
    lon = self.hass.config.longitude

    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}

    url = API_ENDPOINT + "/zones?point=%s,%s" % (lat, lon)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            _LOGGER.debug("getting zone list for %s,%s from %s" % (lat, lon, url))
            if r.status == 200:
                data = await r.json()

    zone_list = []
    if data is not None:
        if "features" in data:
            x = 0
            while len(data[JSON_FEATURES]) > x:
                zone_list.append(data[JSON_FEATURES][x][JSON_PROPERTIES][JSON_ID])
                x += 1
            _LOGGER.debug("Zones list: %s", zone_list)
            zone_list = ",".join(str(x) for x in zone_list)  # convert list to str
            return zone_list
    return None


@config_entries.HANDLERS.register(DOMAIN)
class NWSAlertsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for NWS Alerts."""

    VERSION = 2

    def __init__(self):
        """Initialize."""
        self._data = {}
        self._errors = {}

    # async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
    #     """Import a config entry."""

    #     user_input = user_input[DOMAIN]
    #     result: FlowResult = await self.async_step_user(user_input=user_input)
    #     if errors := result.get("errors"):
    #         return self.async_abort(reason=next(iter(errors.values())))
    #     return result

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the flow initialized by the user."""
        return self.async_show_menu(step_id="user", menu_options=MENU_OPTIONS)

    async def async_step_gps(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the flow initialized by the user."""
        return self.async_show_menu(step_id="gps", menu_options=MENU_GPS)

    async def async_step_gps_tracker(self, user_input=None):
        """Handle a flow for device trackers."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"self._data: {self._data}")
            if self._data.get(CONF_SEND_ALERTS, False) is True:
                return await self.async_step_alerts()
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
        return await self._show_config_gps_tracker(user_input)

    async def _show_config_gps_tracker(self, user_input):
        """Show the configuration form to edit location data."""

        # Defaults
        defaults = {
            CONF_NAME: DEFAULT_NAME,
            CONF_INTERVAL: DEFAULT_INTERVAL,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            CONF_SEND_ALERTS: DEFAULT_SEND_ALERTS,
        }

        return self.async_show_form(
            step_id="gps_tracker",
            data_schema=_get_schema_tracker(self.hass, user_input, defaults),
            errors=self._errors,
        )

    async def async_step_gps_loc(self, user_input=None):
        """Handle a flow initialized by the user."""
        lat = self.hass.config.latitude
        lon = self.hass.config.longitude
        self._errors = {}
        self._gps_loc = f"{lat},{lon}"

        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"self._data: {self._data}")
            if self._data.get(CONF_SEND_ALERTS, False) is True:
                return await self.async_step_alerts()
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
        return await self._show_config_gps_loc(user_input)

    async def _show_config_gps_loc(self, user_input):
        """Show the configuration form to edit location data."""

        # Defaults
        defaults = {
            CONF_NAME: DEFAULT_NAME,
            CONF_INTERVAL: DEFAULT_INTERVAL,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            CONF_GPS_LOC: self._gps_loc,
            CONF_SEND_ALERTS: DEFAULT_SEND_ALERTS,
        }

        return self.async_show_form(
            step_id="gps_loc",
            data_schema=_get_schema_gps(self.hass, user_input, defaults),
            errors=self._errors,
        )

    async def async_step_zone(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        self._zone_list = await _get_zone_list(self)
        _LOGGER.debug(f"Zone step. user_input: {user_input}")
        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"self._data: {self._data}")
            if self._data.get(CONF_SEND_ALERTS, False) is True:
                _LOGGER.debug("Starting alerts step")
                return await self.async_step_alerts()
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
        return await self._show_config_zone(user_input)

    async def _show_config_zone(self, user_input):
        """Show the configuration form to edit location data."""
        _LOGGER.debug(f"Show Config Zone. user_input: {user_input}")
        # Defaults
        defaults = {
            CONF_NAME: DEFAULT_NAME,
            CONF_INTERVAL: DEFAULT_INTERVAL,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            CONF_ZONE_ID: self._zone_list,
            CONF_SEND_ALERTS: DEFAULT_SEND_ALERTS,
        }

        return self.async_show_form(
            step_id="zone",
            data_schema=_get_schema_zone(self.hass, user_input, defaults),
            errors=self._errors,
        )

    async def async_step_alerts(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        _LOGGER.debug(f"Alerts step. user_input: {user_input}")
        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"self._data: {self._data}")
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
        return await self._show_config_alerts(user_input)

    async def _show_config_alerts(self, user_input):
        """Show the configuration form to edit location data."""

        _LOGGER.debug(f"Show Config Alerts. user_input: {user_input}")
        # Defaults
        defaults = {
            CONF_PERSISTENT_NOTIFICATIONS: DEFAULT_PERSISTENT_NOTIFICATIONS,
            CONF_ANNOUNCE_START_TIME: DEFAULT_ANNOUNCE_START_TIME,
            CONF_ANNOUNCE_END_TIME: DEFAULT_ANNOUNCE_END_TIME,
            CONF_SEND_START_TIME: DEFAULT_SEND_START_TIME,
            CONF_SEND_END_TIME: DEFAULT_SEND_END_TIME,
        }

        return self.async_show_form(
            step_id="alerts",
            data_schema=await _async_get_schema_alerts(self.hass, user_input, defaults),
            errors=self._errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NWSAlertsOptionsFlow(config_entry)


class NWSAlertsOptionsFlow(config_entries.OptionsFlow):
    """Options flow for NWS Alerts."""

    def __init__(self, config_entry):
        """Initialize."""
        self.config = config_entry
        self._data = dict(config_entry.data)
        self._errors = {}

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)
        return await self._show_options_form(user_input)

    async def async_step_gps_loc(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"self._data: {self._data}")
            if self._data.get(CONF_SEND_ALERTS, False) is True:
                _LOGGER.debug("Starting alerts step")
                return await self.async_step_alerts()
            return self.async_create_entry(title="", data=self._data)
        return await self._show_options_form(user_input)

    async def async_step_gps_tracker(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"self._data: {self._data}")
            if self._data.get(CONF_SEND_ALERTS, False) is True:
                _LOGGER.debug("Starting alerts step")
                return await self.async_step_alerts()
            return self.async_create_entry(title="", data=self._data)
        return await self._show_options_form(user_input)

    async def async_step_zone(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"self._data: {self._data}")
            if self._data.get(CONF_SEND_ALERTS, False) is True:
                _LOGGER.debug("Starting alerts step")
                return await self.async_step_alerts()
            return self.async_create_entry(title="", data=self._data)
        return await self._show_options_form(user_input)

    async def async_step_alerts(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        _LOGGER.debug(f"Alerts step. user_input: {user_input}")
        if user_input is not None:
            self._data.update(user_input)
            _LOGGER.debug(f"self._data: {self._data}")
            return self.async_create_entry(title="", data=self._data)
        return await self._show_config_alerts(user_input)

    async def _show_config_alerts(self, user_input):
        """Show the configuration form to edit location data."""

        _LOGGER.debug(f"Show Config Alerts. user_input: {user_input}")

        return self.async_show_form(
            step_id="alerts",
            data_schema=await _async_get_schema_alerts(
                self.hass, user_input, self._data
            ),
            errors=self._errors,
        )

    async def _show_options_form(self, user_input):
        """Show the configuration form to edit location data."""

        if CONF_GPS_LOC in self.config.data:
            return self.async_show_form(
                step_id="gps_loc",
                data_schema=_get_schema_gps(self.hass, user_input, self._data),
                errors=self._errors,
            )
        elif CONF_ZONE_ID in self.config.data:
            return self.async_show_form(
                step_id="zone",
                data_schema=_get_schema_zone(self.hass, user_input, self._data),
                errors=self._errors,
            )
        elif CONF_TRACKER in self.config.data:
            return self.async_show_form(
                step_id="gps_tracker",
                data_schema=_get_schema_tracker(self.hass, user_input, self._data),
                errors=self._errors,
            )
