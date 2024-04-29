""" NWS Alerts """

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from async_timeout import timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    API_ENDPOINT,
    CONF_GPS_LOC,
    CONF_INTERVAL,
    CONF_TIMEOUT,
    CONF_TRACKER,
    CONF_ZONE_ID,
    COORDINATOR,
    DEFAULT_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    ISSUE_URL,
    PLATFORMS,
    USER_AGENT,
    VERSION,
)

SHORT_SEPARATOR = " - "
LONG_SEPARATOR = "\n\n-\n\n"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """Load the saved entities."""
    # Print startup message
    _LOGGER.info(
        "Version %s is starting, if you have any issues please report"
        " them here: %s",
        VERSION,
        ISSUE_URL,
    )
    hass.data.setdefault(DOMAIN, {})

    if config_entry.unique_id is not None:
        hass.config_entries.async_update_entry(config_entry, unique_id=None)

        ent_reg = async_get(hass)
        for entity in async_entries_for_config_entry(
            ent_reg, config_entry.entry_id
        ):
            ent_reg.async_update_entity(
                entity.entity_id, new_unique_id=config_entry.entry_id
            )

    updated_config = config_entry.data.copy()

    # Strip spaces from manually entered GPS locations
    if CONF_GPS_LOC in updated_config:
        updated_config[CONF_GPS_LOC].replace(" ", "")

    if updated_config != config_entry.data:
        hass.config_entries.async_update_entry(
            config_entry, data=updated_config
        )

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
            hass.config_entries.async_forward_entry_setup(
                config_entry, platform
            )
        )
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(
            config_entry, "sensor"
        )
        _LOGGER.info(
            "Successfully removed sensor from the %s integration", DOMAIN
        )
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
            hass.config_entries.async_update_entry(
                config_entry, data=updated_config
            )

        config_entry.version = 2
        _LOGGER.debug("Migration to version %s complete", config_entry.version)

    return True


class AlertsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching NWS Alert data."""

    def __init__(
        self, hass, config, the_timeout: int | None, interval: int | None
    ):
        """Initialize."""
        self.interval = (
            None if interval is None else timedelta(minutes=interval)
        )
        self.name = config[CONF_NAME]
        self.timeout = the_timeout
        self.config = config
        self.hass = hass

        _LOGGER.debug("Data will be update every %s", self.interval)

        super().__init__(
            hass, _LOGGER, name=self.name, update_interval=self.interval
        )

    async def _async_update_data(self):
        """Fetch data"""
        async with timeout(self.timeout):
            try:
                data = await async_get_state(self.hass, self.config)
            except Exception as error:
                raise UpdateFailed(error) from error
            return data


async def _get_tracker_gps(hass: HomeAssistant, tracker: str) -> str | None:
    """Return device tracker GPS data."""
    entity = hass.states.get(tracker)
    if entity and "source_type" in entity.attributes:
        lat = entity.attributes["latitude"]
        lon = entity.attributes["longitude"]
        return f"{lat},{lon}"
    return None


async def async_get_state(hass: HomeAssistant, config: dict[str, Any]) -> dict:
    """Query API for status."""
    url = f"{API_ENDPOINT}/alerts/active/count"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/ld+json"}
    data: dict[str, Any] | None = None

    _LOGGER.debug("getting state from %s", url)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            if r.status == 200:
                data = await r.json()
            else:
                _LOGGER.error(
                    "Problem updating NWS data: (%s) - %s",
                    r.status,
                    r._body,  # pylint: disable=protected-access
                )

    alerts: list[dict[str, Any]] = []
    if data is not None:
        # Reset values before reassigning
        if CONF_ZONE_ID in config:
            if "zones" in data:
                zone_id = config[CONF_ZONE_ID]
                for zone in zone_id.split(","):
                    if zone in data["zones"]:
                        alerts = await async_get_alerts(zone_id=zone_id)
                        break
        elif CONF_GPS_LOC in config:
            gps_loc = config[CONF_GPS_LOC].replace(" ", "")
            alerts = await async_get_alerts(gps_loc=gps_loc)
        elif CONF_TRACKER in config:
            gps_loc = await _get_tracker_gps(hass, config[CONF_TRACKER])
            alerts = await async_get_alerts(gps_loc=gps_loc)

    values = join_alerts(alerts)
    values['alerts'] = alerts
    return values


async def async_get_alerts(
    zone_id: str | None = None, gps_loc: str | None = None
) -> list[dict[str, Any]]:
    """Query API for Alerts."""
    url = ""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    data = None
    if zone_id is not None and zone_id != "":
        url = f"{API_ENDPOINT}/alerts/active?zone={zone_id}"
        _LOGGER.debug("getting alert for %s from %s", zone_id, url)
    elif gps_loc is not None and gps_loc != "":
        url = f"{API_ENDPOINT}/alerts/active?point={gps_loc}"
        _LOGGER.debug("getting alert for %s from %s", gps_loc, url)
    else:
        _LOGGER.error("Problem updating NWS data from config")
        return []

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            if r.status == 200:
                data = await r.json()
            else:
                _LOGGER.error(
                    "Problem updating NWS data: (%s) - %s",
                    r.status,
                    r._body,  # pylint: disable=protected-access
                )

    alerts = []
    if data is not None:
        for alert in data["features"]:
            properties = alert["properties"]

            if "NWSheadline" in properties["parameters"]:
                spoken_desc = properties["parameters"]["NWSheadline"][0]
            else:
                spoken_desc = properties["event"]

            display_desc = (
                f"Headline: {spoken_desc}\n"
                f"Status: {properties["status"]}\n"
                f"Message Type: {properties["messageType"]}\n"
                f"Severity: {properties["severity"]}\n"
                f"Certainty: {properties["certainty"]}\n"
                f"Expires: {properties["expires"]}\n"
                f"Description: {properties["description"]}\n"
                f"Instruction: {properties["instruction"]}"
            )

            alerts.append(
                {
                    "title": properties["event"],
                    "event_id": alert["id"],
                    "message_type": properties["messageType"],
                    "event_status": properties["status"],
                    "event_severity": properties["severity"],
                    "event_expires": properties["expires"],
                    "event_certainty": properties["certainty"],
                    "event_instruction": properties["instruction"],
                    "event_description": properties["description"],
                    "display_desc": display_desc,
                    "spoken_desc": spoken_desc,
                }
            )

    return alerts


def join_alerts(alerts: list[dict[str, Any]]) -> dict[str, Any]:
    """Joins multiple alerts into a single concatenated alert."""

    values: dict[str, Any] = {
        "state": len(alerts),
        "title": None,
        "event_id": None,
        "message_type": None,
        "event_status": None,
        "event_severity": None,
        "event_expires": None,
        "display_desc": None,
        "spoken_desc": None,
    }

    if len(alerts) > 0:
        v = {k: [dic[k] for dic in alerts] for k in alerts[0]}

        values["title"] = SHORT_SEPARATOR.join(v["title"])
        values["event_id"] = SHORT_SEPARATOR.join(v['event_id'])
        values["message_type"] = SHORT_SEPARATOR.join(v['message_type'])
        values["event_status"] = SHORT_SEPARATOR.join(v['event_status'])
        values["event_severity"] = SHORT_SEPARATOR.join(v['event_severity'])
        values["event_expires"] = SHORT_SEPARATOR.join(v['event_expires'])
        values["display_desc"] = LONG_SEPARATOR.join(
            ["\n>\n" + d for d in v['display_desc']])
        values["spoken_desc"] = LONG_SEPARATOR.join(v['spoken_desc'])

    return values
