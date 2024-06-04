""" NWS Alerts """

import logging
import re
from datetime import datetime, timedelta

import aiohttp
from async_timeout import timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_ENDPOINT,
    CONF_GPS_LOC,
    CONF_INTERVAL,
    CONF_SEND_ALERTS,
    CONF_TIMEOUT,
    CONF_TRACKER,
    CONF_ZONE_ID,
    COORDINATOR,
    DEFAULT_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    ISSUE_URL,
    NWS_CERTAINTY,
    NWS_DESCRIPTION,
    NWS_DISPLAY_DESC,
    NWS_EVENT,
    NWS_EVENT_EXPIRES,
    NWS_EVENT_ID,
    NWS_EVENT_ID_SHORT,
    NWS_EVENT_SEVERITY,
    NWS_EVENT_STATUS,
    NWS_HEADLINE,
    NWS_HEADLINE_LONG,
    NWS_ID_PREFIX,
    NWS_INSTRUCTION,
    NWS_MESSAGE_TYPE,
    NWS_PROPERTIES,
    NWS_URL,
    NWS_URL_PREFIX,
    PLATFORMS,
    USER_AGENT,
    VERSION,
)
from .send_nwsalerts import Send_NWSAlerts

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Load the saved entities."""
    # Print startup message
    _LOGGER.info(
        "Version %s is starting, if you have any issues please report" " them here: %s",
        VERSION,
        ISSUE_URL,
    )
    hass.data.setdefault(DOMAIN, {})

    if config_entry.unique_id is not None:
        hass.config_entries.async_update_entry(config_entry, unique_id=None)

        ent_reg = async_get(hass)
        for entity in async_entries_for_config_entry(ent_reg, config_entry.entry_id):
            ent_reg.async_update_entity(
                entity.entity_id, new_unique_id=config_entry.entry_id
            )

    updated_config = config_entry.data.copy()

    # Strip spaces from manually entered GPS locations
    if CONF_GPS_LOC in updated_config:
        updated_config[CONF_GPS_LOC].replace(" ", "")

    if updated_config != config_entry.data:
        hass.config_entries.async_update_entry(config_entry, data=updated_config)

    config_entry.add_update_listener(update_listener)

    # Setup the data coordinator
    coordinator = AlertsDataUpdateCoordinator(
        hass,
        config_entry.data,
        config_entry.data.get(CONF_TIMEOUT),
        config_entry.data.get(CONF_INTERVAL),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    hass.data[DOMAIN][config_entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        _LOGGER.info("Successfully removed sensor from the " + DOMAIN + " integration")
    except ValueError:
        pass
    return True


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Update listener."""
    if config_entry.data == config_entry.options:
        _LOGGER.debug("No changes detected not reloading sensors.")
        return

    new_data = config_entry.options.copy()
    hass.config_entries.async_update_entry(
        entry=config_entry,
        data=new_data,
    )

    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate an old config entry."""
    version = config_entry.version

    # 1-> 2: Migration format
    if version == 1:
        _LOGGER.debug("Migrating from version %s", version)
        updated_config = config_entry.data.copy()

        if CONF_INTERVAL not in updated_config.keys():
            updated_config[CONF_INTERVAL] = DEFAULT_INTERVAL
        if CONF_TIMEOUT not in updated_config.keys():
            updated_config[CONF_TIMEOUT] = DEFAULT_TIMEOUT

        if updated_config != config_entry.data:
            hass.config_entries.async_update_entry(config_entry, data=updated_config)

        config_entry.version = 2
        _LOGGER.debug("Migration to version %s complete", config_entry.version)

    return True


class AlertsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching NWS Alert data."""

    def __init__(self, hass, config, the_timeout: int, interval: int):
        """Initialize."""
        self.interval = timedelta(minutes=interval)
        self.name = config[CONF_NAME]
        self.timeout = the_timeout
        self.config = config
        self.hass = hass
        self._send_nwsalerts = None
        if config.get(CONF_SEND_ALERTS, False):
            self._send_nwsalerts = Send_NWSAlerts(hass, config)

        _LOGGER.debug("Data will be update every %s", self.interval)

        super().__init__(hass, _LOGGER, name=self.name, update_interval=self.interval)

    async def _async_update_data(self):
        """Fetch data"""
        coords = None
        if CONF_TRACKER in self.config:
            coords = await self._get_tracker_gps()
        async with timeout(self.timeout):
            try:
                array, data = await update_alerts(self.config, coords)
            except Exception as error:
                raise UpdateFailed(error) from error
            else:
                if self._send_nwsalerts is not None:
                    await self._send_nwsalerts.async_send(array)
            return data

    async def _get_tracker_gps(self):
        """Return device tracker GPS data."""
        tracker = self.config[CONF_TRACKER]
        entity = self.hass.states.get(tracker)
        if entity and "source_type" in entity.attributes:
            return f"{entity.attributes['latitude']},{entity.attributes['longitude']}"
        return None

    async def async_removing_from_hass(self):
        if self._send_nwsalerts is not None:
            await self.hass.async_add_executor_job(
                self._send_nwsalerts._removing_from_hass
            )


async def update_alerts(config, coords) -> dict:
    """Fetch new state data for the sensor.
    This is the only method that should fetch new data for Home Assistant.
    """

    array, data = await async_get_state(config, coords)
    return (array, data)


async def async_get_state(config, coords) -> dict:
    """Query API for status."""

    zone_id = ""
    gps_loc = ""
    url = "%s/alerts/active/count" % API_ENDPOINT
    values = {
        "state": 0,
        NWS_EVENT: None,
        NWS_EVENT_ID: None,
        NWS_MESSAGE_TYPE: None,
        NWS_EVENT_STATUS: None,
        NWS_EVENT_SEVERITY: None,
        NWS_EVENT_EXPIRES: None,
        NWS_DISPLAY_DESC: None,
        NWS_HEADLINE: None,
    }
    array = []
    headers = {"User-Agent": USER_AGENT, "Accept": "application/ld+json"}
    data = None

    if CONF_ZONE_ID in config:
        zone_id = config[CONF_ZONE_ID]
        _LOGGER.debug("getting state for %s from %s" % (zone_id, url))
    elif CONF_GPS_LOC in config or CONF_TRACKER in config:
        if coords is not None:
            gps_loc = coords
        else:
            gps_loc = config[CONF_GPS_LOC].replace(" ", "")
        _LOGGER.debug("getting state for %s from %s" % (gps_loc, url))

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            if r.status == 200:
                data = await r.json()
            else:
                _LOGGER.error("Problem updating NWS data: (%s) - %s", r.status, r.body)
    # _LOGGER.debug(f"state data: {data}")
    if data is not None:
        # Reset values before reassigning
        if "zones" in data and zone_id != "":
            for zone in zone_id.split(","):
                if zone in data["zones"]:
                    array, values = await async_get_alerts(zone_id=zone_id)
                    break
        else:
            array, values = await async_get_alerts(gps_loc=gps_loc)

    # _LOGGER.debug(f"values: {values}")
    return (array, values)


def _upper_to_title_case(title_string):
    title_string = title_string.title().replace('"', "").strip()
    title_string = re.sub(
        r"(\s)([A-Z][ds]t)(\s)",
        lambda pat: f"{pat.group(1)}{pat.group(2).upper()}{pat.group(3)}",
        title_string,
    )
    return re.sub(
        r"(\d\s?)([AP]m)(\s)",
        lambda pat: f"{pat.group(1)}{pat.group(2).upper()}{pat.group(3)}",
        title_string,
    )


def _string_cleanup(clean_string):
    if clean_string is None:
        return None
    if clean_string.isupper():
        return (
            _upper_to_title_case(clean_string)
            .replace("\n\n", "<00temp00>")
            .replace("\n", " ")
            .replace("<00temp00>", "\n")
            .replace('"', "")
            .strip()
        )
    else:
        return (
            clean_string.replace("\n\n", "<00temp00>")
            .replace("\n", " ")
            .replace("<00temp00>", "\n")
            .replace('"', "")
            .strip()
        )


async def async_get_alerts(zone_id: str = "", gps_loc: str = "") -> dict:
    """Query API for Alerts."""

    url = ""
    values = {
        "state": 0,
        NWS_EVENT: None,
        NWS_EVENT_ID: None,
        NWS_MESSAGE_TYPE: None,
        NWS_EVENT_STATUS: None,
        NWS_EVENT_SEVERITY: None,
        NWS_EVENT_EXPIRES: None,
        NWS_DISPLAY_DESC: None,
        NWS_HEADLINE: None,
    }
    array = []
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    data = None

    if zone_id != "":
        url = "%s/alerts/active?zone=%s" % (API_ENDPOINT, zone_id)
        _LOGGER.debug("getting alert for %s from %s" % (zone_id, url))
    elif gps_loc != "":
        url = "%s/alerts/active?point=%s" % (API_ENDPOINT, gps_loc)
        _LOGGER.debug("getting alert for %s from %s" % (gps_loc, url))

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            if r.status == 200:
                data = await r.json()
            else:
                _LOGGER.error("Problem updating NWS data: (%s) - %s", r.status, r.body)

    if data is not None:
        event = ""
        event_id = ""
        message_type = ""
        event_status = ""
        event_severity = ""
        event_expires = ""
        display_desc = ""
        spoken_desc = ""
        features = data.get("features", {})
        events = 0
        for alert in features:
            alert_dict = {}
            events += 1
            event_name = alert.get(NWS_PROPERTIES)[NWS_EVENT]
            if "NWSheadline" in alert.get(NWS_PROPERTIES).get("parameters", None):
                headline = (
                    alert.get(NWS_PROPERTIES)
                    .get("parameters")
                    .get("NWSheadline", None)[0]
                )
            else:
                headline = event_name
            headline = _string_cleanup(headline)
            if (
                "headline" in alert.get(NWS_PROPERTIES)
                and alert.get(NWS_PROPERTIES).get("headline", None) is not None
            ):
                headline_long = alert.get(NWS_PROPERTIES).get("headline", None)
            else:
                headline_long = headline
            headline_long = _string_cleanup(headline_long)

            url = _string_cleanup(alert.get("id", None))
            mtype = _string_cleanup(alert.get(NWS_PROPERTIES).get("messageType", None))
            status = _string_cleanup(alert.get(NWS_PROPERTIES).get("status", None))
            description = _string_cleanup(
                alert.get(NWS_PROPERTIES).get(NWS_DESCRIPTION, None)
            )
            instruction = _string_cleanup(
                alert.get(NWS_PROPERTIES).get(NWS_INSTRUCTION, None)
            )
            severity = _string_cleanup(alert.get(NWS_PROPERTIES).get("severity", None))
            certainty = _string_cleanup(
                alert.get(NWS_PROPERTIES).get(NWS_CERTAINTY, None)
            )
            expires = _string_cleanup(alert.get(NWS_PROPERTIES).get("expires", None))

            if event != "":
                event += " - "
            event += event_name
            alert_dict.update({NWS_EVENT: event_name})

            if display_desc != "":
                display_desc += "\n\n-\n\n"

            display = (
                "\n>\nHeadline: %s\nStatus: %s\nMessage Type: %s\nSeverity: %s\nCertainty: %s\nExpires: %s\nDescription: %s\n\nInstruction: %s"
                % (
                    headline,
                    status,
                    mtype,
                    severity,
                    certainty,
                    expires,
                    description,
                    instruction,
                )
            )
            display_desc += display
            alert_dict.update({NWS_DISPLAY_DESC: display})

            if event_id != "":
                event_id += " - "
            event_id += url
            alert_dict.update({NWS_URL: url})

            if message_type != "":
                message_type += " - "
            message_type += mtype
            alert_dict.update({NWS_MESSAGE_TYPE: mtype})

            if event_status != "":
                event_status += " - "
            event_status += status
            alert_dict.update({NWS_EVENT_STATUS: status})

            if event_severity != "":
                event_severity += " - "
            event_severity += severity
            alert_dict.update({NWS_EVENT_SEVERITY: severity})

            if event_expires != "":
                event_expires += " - "
            event_expires += expires
            if expires is not None:
                expires = datetime.fromisoformat(expires)
            alert_dict.update({NWS_EVENT_EXPIRES: expires})

            if spoken_desc != "":
                spoken_desc += "\n\n-\n\n"
            spoken_desc += headline
            alert_dict.update({NWS_HEADLINE: headline})

            id = url.replace(NWS_URL_PREFIX, "")
            alert_dict.update({NWS_EVENT_ID: id})
            id_short = id.replace(NWS_ID_PREFIX, "").replace(".", "")
            alert_dict.update({NWS_EVENT_ID_SHORT: id_short})

            alert_dict.update({NWS_HEADLINE_LONG: headline_long})
            alert_dict.update({NWS_DESCRIPTION: description})
            alert_dict.update({NWS_CERTAINTY: certainty})
            alert_dict.update({NWS_INSTRUCTION: instruction})

            array.append(alert_dict)

        if events > 0:

            values["state"] = events
            values[NWS_EVENT] = event
            values[NWS_EVENT_ID] = event_id
            values[NWS_MESSAGE_TYPE] = message_type
            values[NWS_EVENT_STATUS] = event_status
            values[NWS_EVENT_SEVERITY] = event_severity
            values[NWS_EVENT_EXPIRES] = event_expires
            values[NWS_DISPLAY_DESC] = display_desc
            values[NWS_HEADLINE] = spoken_desc
    # _LOGGER.debug(f"array: {array}")
    return (array, values)
