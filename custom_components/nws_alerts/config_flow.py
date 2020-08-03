"""Adds config flow for NWS Alerts."""
import aiohttp
import logging
from collections import OrderedDict

import voluptuous as vol

from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant import config_entries
from .const import (
    API_ENDPOINT,
    DOMAIN,
    CONF_ZONE_ID,
    DEFAULT_NAME,
    USER_AGENT,
)

JSON_FEATURES = "features"
JSON_PROPERTIES = "properties"
JSON_ID = "id"

_LOGGER = logging.getLogger(__name__)


async def _get_zone_list(self):
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
            return zone_list
    return None


@config_entries.HANDLERS.register(DOMAIN)
class NWSAlertsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for NWS Alerts."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._data = {}
        self._errors = {}

    async def async_step_user(self, user_input={}):
        """Handle a flow initialized by the user."""
        self._errors = {}
        self._zone_list = await _get_zone_list(self)

        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""

        # Defaults
        name = DEFAULT_NAME
        zone_id = self._zone_list

        if user_input is not None:
            if "name" in user_input:
                name = user_input["name"]
            if CONF_ZONE_ID in user_input:
                zone_id = user_input[CONF_ZONE_ID]

        data_schema = OrderedDict()
        data_schema[vol.Optional("name", default=name)] = str
        data_schema[vol.Required(CONF_ZONE_ID, default=zone_id)] = str
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
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
        self._data = dict(config_entry.options)
        self._errors = {}

    async def async_step_init(self, user_input=None):
        """Manage Mail and Packages options."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
        return await self._show_options_form(user_input)

    async def _show_options_form(self, user_input):
        """Show the configuration form to edit location data."""

        # Defaults
        name = self.config.options.get(CONF_NAME)
        zone_id = self.config.options.get(CONF_ZONE_ID)

        if user_input is not None:
            if "name" in user_input:
                name = user_input["name"]
            if CONF_ZONE_ID in user_input:
                zone_id = user_input[CONF_ZONE_ID]

        data_schema = OrderedDict()
        data_schema[vol.Optional("name", default=name)] = str
        data_schema[vol.Required("zone_id", default=zone_id)] = str
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(data_schema), errors=self._errors
        )
