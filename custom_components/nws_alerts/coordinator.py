"""Coordinator for nws_alerts."""

from asyncio import timeout
from datetime import datetime, timedelta
import hashlib
import logging
from typing import Any
import uuid

import aiohttp

from homeassistant.const import CONF_NAME
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_ENDPOINT,
    CONF_GPS_LOC,
    CONF_INTERVAL,
    CONF_TIMEOUT,
    CONF_TRACKER,
    CONF_ZONE_ID,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


class AlertsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching NWS Alert data."""

    def __init__(self, hass, config):
        """Initialize."""
        self.interval = timedelta(minutes=config.data.get(CONF_INTERVAL))
        self.name = config.data.get(CONF_NAME)
        self.timeout = config.data.get(CONF_TIMEOUT)
        self._config = config
        self.hass = hass

        _LOGGER.debug("Data will be update every %s", self.interval)

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config,
            name=self.name,
            update_interval=self.interval,
        )

    async def _async_update_data(self):
        """Fetch data."""
        coords = None
        if CONF_TRACKER in self._config.data:
            coords = await self._get_tracker_gps()
        async with timeout(self.timeout):
            try:
                data = await self.update_alerts(coords)
            except AttributeError as error:
                _LOGGER.warning("AttributeError fetching NWS Alerts data: %s. Will retry.", error)
                # Return valid structure instead of None
                return {"state": 0, "alerts": [], "last_updated": datetime.now().isoformat()}
            except Exception as error:
                raise UpdateFailed(error) from error
            _LOGGER.debug("Data: %s", data)
            return data

    async def _get_tracker_gps(self):
        """Return device tracker GPS data."""
        tracker = self._config.data.get(CONF_TRACKER)
        entity = self.hass.states.get(tracker)
        if entity and "source_type" in entity.attributes:
            # Check that latitude and longitude actually exist
            if "latitude" in entity.attributes and "longitude" in entity.attributes:
                return f"{entity.attributes['latitude']},{entity.attributes['longitude']}"
            _LOGGER.warning("Tracker %s found but missing latitude/longitude attributes", tracker)
        return None

    async def update_alerts(self, coords) -> dict:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """

        return await self.async_get_state(coords)

    async def async_get_state(self, coords) -> dict:
        """Query API for status."""

        zone_id = ""
        gps_loc = ""
        values = {"state": 0, "alerts": [], "last_updated": datetime.now().isoformat()}

        if CONF_ZONE_ID in self._config.data:
            zone_id = self._config.data[CONF_ZONE_ID]
            _LOGGER.debug("Fetching alerts for zone: %s", zone_id)
            # Directly fetch alerts for zone_id, don't rely on count endpoint
            values = await self.async_get_alerts(zone_id=zone_id)
        elif CONF_GPS_LOC in self._config.data or CONF_TRACKER in self._config.data:
            if coords is not None:
                gps_loc = coords
            elif CONF_GPS_LOC in self._config.data:
                gps_loc = self._config.data[CONF_GPS_LOC].replace(" ", "")
            else:
                _LOGGER.warning("Tracker configured but no GPS coordinates available")
                return values

            _LOGGER.debug("Fetching alerts for GPS location: %s", gps_loc)
            values = await self.async_get_alerts(gps_loc=gps_loc)

        return values

    async def async_get_alerts(self, zone_id: str = "", gps_loc: str = "") -> dict:
        """Query API for Alerts."""

        url = ""
        alerts: dict[str, Any] = {
            "state": 0,
            "alerts": [],
            "last_updated": datetime.now().isoformat(),
        }
        headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
        data = None

        if zone_id != "":
            url = f"{API_ENDPOINT}/alerts/active?zone={zone_id}"
            _LOGGER.debug("getting alert for %s from %s", zone_id, url)
        elif gps_loc != "":
            url = f"{API_ENDPOINT}/alerts/active?point={gps_loc}"
            _LOGGER.debug("getting alert for %s from %s", gps_loc, url)

        async with aiohttp.ClientSession() as session, session.get(url, headers=headers) as r:
            if r.status == 200:
                data = await r.json()
            else:
                _LOGGER.error("Problem updating NWS data: (%s) - %s", r.status, r.content)

        if data is not None and "features" in data:
            features = data["features"]
            alert_list: list[Any] = []
            for alert in features:
                try:
                    tmp_dict: dict[str, Any] = {}

                    # Generate stable Alert ID
                    alert_id = await self.generate_id(alert["id"])

                    tmp_dict["Event"] = alert["properties"]["event"]
                    tmp_dict["ID"] = alert_id
                    tmp_dict["URL"] = alert["id"]

                    event = alert["properties"]["event"]
                    if "NWSheadline" in alert["properties"]["parameters"]:
                        tmp_dict["Headline"] = alert["properties"]["parameters"]["NWSheadline"][0]
                    else:
                        tmp_dict["Headline"] = event

                    tmp_dict["Type"] = alert["properties"]["messageType"]
                    tmp_dict["Status"] = alert["properties"]["status"]
                    tmp_dict["Severity"] = alert["properties"]["severity"]
                    tmp_dict["Certainty"] = alert["properties"]["certainty"]
                    tmp_dict["Sent"] = alert["properties"]["sent"]
                    tmp_dict["Onset"] = alert["properties"]["onset"]
                    tmp_dict["Expires"] = alert["properties"]["expires"]
                    tmp_dict["Ends"] = alert["properties"]["ends"]
                    tmp_dict["AreasAffected"] = alert["properties"]["areaDesc"]
                    tmp_dict["Description"] = alert["properties"]["description"]
                    tmp_dict["Instruction"] = alert["properties"]["instruction"]

                    alert_list.append(tmp_dict)
                except (KeyError, TypeError) as error:
                    _LOGGER.warning("Error parsing alert data: %s. Skipping this alert.", error)
                    continue

            alerts["state"] = len(alert_list)
            alerts["alerts"] = alert_list
            alerts["last_updated"] = datetime.now().isoformat()

        return alerts

    async def generate_id(self, val: str) -> str:
        """Generate a unique ID for alerts."""
        hex_string = hashlib.md5(val.encode("UTF-8")).hexdigest()
        return str(uuid.UUID(hex=hex_string))
