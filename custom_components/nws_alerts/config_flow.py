"""Adds config flow for NWS Alerts."""
import logging
from collections import OrderedDict

import voluptuous as vol

from homeassistant.core import callback
from homeassistant import config_entries
from .const import (
    DOMAIN,
    CONF_ZONE_ID,
    DEFAULT_NAME,
)

from homeassistant.const import CONF_NAME

_LOGGER = logging.getLogger(__name__)


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

        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title=self._data[CONF_NAME],
                                           data=self._data)
            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""

        # Defaults
        name = DEFAULT_NAME

        if user_input is not None:
            if "name" in user_input:
                name = user_input["name"]
            if "zone_id" in user_input:
                zone_id = user_input["zone_id"]

        data_schema = OrderedDict()
        data_schema[vol.Required("name", default=name)] = str
        data_schema[vol.Required("zone_id")] = str
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema),
            errors=self._errors)

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
            return self.async_create_entry(title=self._data[CONF_NAME],
                                           data=self._data)

            return await self._show_options_form(user_input)

        return await self._show_options_form(user_input)

    async def _show_options_form(self, user_input):
        """Show the configuration form to edit location data."""

        # Defaults
        name = self.config.options.get(CONF_NAME)
        zone_id = self.config.options.get(CONF_ZONE_ID)

        if user_input is not None:
            if "name" in user_input:
                name = user_input["name"]
            if "zone_id" in user_input:
                zone_id = user_input["zone_id"]

        data_schema = OrderedDict()
        data_schema[vol.Required("name", default=name)] = str
        data_schema[vol.Required("zone_id", default=zone_id)] = str
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(data_schema),
            errors=self._errors)
