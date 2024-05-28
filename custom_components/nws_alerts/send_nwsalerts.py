import logging
from datetime import datetime, time

import homeassistant.util.dt as dt_util
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.util.async_ import run_callback_threadsafe

from .const import (
    CONF_ANNOUNCE_CRITICAL_SERVICES,
    CONF_ANNOUNCE_CRITICAL_TYPES,
    CONF_ANNOUNCE_END_TIME,
    CONF_ANNOUNCE_SERVICES,
    CONF_ANNOUNCE_START_TIME,
    CONF_ANNOUNCE_TYPES,
    CONF_PERSISTENT_NOTIFICATIONS,
    CONF_SEND_ALERTS,
    CONF_SEND_CRITICAL_SERVICES,
    CONF_SEND_CRITICAL_TYPES,
    CONF_SEND_END_TIME,
    CONF_SEND_SERVICES,
    CONF_SEND_START_TIME,
    CONF_SEND_TYPES,
)

_LOGGER = logging.getLogger(__name__)


class Send_NWSAlerts:

    def __init__(self, hass: HomeAssistant, config) -> None:
        """Initialize the class to send NWS alerts."""
        self._hass = hass
        self._config = config
        self._name = config.get(CONF_NAME, None)
        _LOGGER.debug(f"Send_NWSAlerts: name: {self._name}, config: {self._config}")

    def send(self, data):
        return run_callback_threadsafe(self._hass.loop, self.async_send(data))

    async def async_send(self, data):
        _LOGGER.debug(f"Send_NWSAlerts async_send: data: {data}")
        if (
            self._config.get(CONF_SEND_ALERTS, False) is False
            or data.get("state", 0) == 0
        ):
            return

        # Clear any expired alerts

        for count in range(data.get("state", 0)):
            nwsalert = await self._parse_alert(count, data)

            # Check if already alerted and if not add to alert history

            if self._config.get(CONF_PERSISTENT_NOTIFICATIONS, False) is True:
                await self._send_persistent_notifications(count, nwsalert)

            if (
                nwsalert.get("event", None)
                in self._config.get(CONF_ANNOUNCE_CRITICAL_TYPES, [])
                and self._config.get(CONF_ANNOUNCE_CRITICAL_SERVICES, None) is not None
            ):
                await self._announce_critical_alerts(count, nwsalert)

            if (
                nwsalert.get("event", None) in self._config.get(CONF_ANNOUNCE_TYPES, [])
                and self._config.get(CONF_ANNOUNCE_SERVICES, None) is not None
            ):
                await self._announce_alerts(count, nwsalert)

            if (
                nwsalert.get("event", None)
                in self._config.get(CONF_SEND_CRITICAL_TYPES, [])
                and self._config.get(CONF_SEND_CRITICAL_SERVICES, None) is not None
            ):
                await self._send_critical_alerts(count, nwsalert)

            if (
                nwsalert.get("event", None) in self._config.get(CONF_SEND_TYPES, [])
                and self._config.get(CONF_SEND_SERVICES, None) is not None
            ):
                await self._send_alerts(count, nwsalert)

    async def _parse_alert(self, count, data):
        _LOGGER.debug(f"Parse Alert: count: {count}")
        nwsalert = {}

        nwsalert["event"] = data.get("event", "").split(" - ")[count].replace('"', "")
        _LOGGER.debug(f"event: {nwsalert['event']}")
        nwsalert["event_id"] = (
            data.get("event_id", "")
            .split(" - ")[count]
            .replace('"', "")
            .replace("https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.", "")
            .replace(".", "")
        )
        _LOGGER.debug(f"event_id: {nwsalert['event_id']}")
        nwsalert["message_type"] = (
            data.get("message_type", "").split(" - ")[count].replace('"', "")
        )
        _LOGGER.debug(f"message_type: {nwsalert['message_type']}")
        nwsalert["event_status"] = (
            data.get("event_status", "").split(" - ")[count].replace('"', "")
        )
        _LOGGER.debug(f"event_status: {nwsalert['event_status']}")
        nwsalert["event_severity"] = (
            data.get("event_severity", "").split(" - ")[count].replace('"', "")
        )
        _LOGGER.debug(f"event_severity: {nwsalert['event_severity']}")
        event_expires_str = (
            data.get("event_expires", "").split(" - ")[count].replace('"', "")
        )
        # 2024-05-29T22:30:00-05:00
        # event_expires = datetime.strptime(event_expires_str, "%Y-%m-%dT%H:%M:%s%z")
        nwsalert["event_expires"] = datetime.fromisoformat(event_expires_str)
        _LOGGER.debug(f"event_expires: {nwsalert['event_expires']}")

        nwsalert["display_desc"] = (
            data.get("display_desc", "")
            .split("\n\n-\n\n")[count]
            .replace('"', "")
            .replace("\n>\n", "")
        )

        nwsalert["certainty"] = nwsalert["display_desc"][
            nwsalert["display_desc"].find("Certainty: ")
            + len("Certainty: "): nwsalert["display_desc"].find("\nExpires:")
        ].strip()
        _LOGGER.debug(f"certainty: {nwsalert["certainty"]}")

        nwsalert["description"] = (
            nwsalert["display_desc"][
                nwsalert["display_desc"].find("Description: ") + len("Description: "):
            ]
            .replace("\n\n", "<00temp00>")
            .replace("\n", " ")
            .replace("<00temp00>", "\n\n")
            .strip()
        )
        _LOGGER.debug(f"description: {nwsalert["description"]}")

        nwsalert["spoken_desc"] = (
            data.get("spoken_desc", "").split("\n\n-\n\n")[count].replace('"', "")
        )
        if nwsalert["spoken_desc"].isupper():
            nwsalert["spoken_desc"] = nwsalert["spoken_desc"].title()
        _LOGGER.debug(f"spoken_desc: {nwsalert['spoken_desc']}")
        return nwsalert

    async def _send_persistent_notifications(self, count, nwsalert):
        _LOGGER.debug(f"Send Persistent Notifications: count: {count}")
        _LOGGER.debug(f"nwsalert: {nwsalert}")

    async def _announce_critical_alerts(self, count, nwsalert):
        _LOGGER.debug(f"Announce Critical Alerts: count: {count}")

    async def _announce_alerts(self, count, nwsalert):
        _LOGGER.debug(f"Announce Alerts: count: {count}")
        if not self._is_now_between(
            self._config.get(CONF_ANNOUNCE_START_TIME, None),
            self._config.get(CONF_ANNOUNCE_END_TIME, None),
        ):
            _LOGGER.debug(
                "Outside of time window "
                f"[{self._config.get(CONF_ANNOUNCE_START_TIME, None)}, "
                f"{self._config.get(CONF_ANNOUNCE_END_TIME, None)}], not sending."
            )
            return

    async def _send_critical_alerts(self, count, nwsalert):
        _LOGGER.debug(f"Send Critical Alerts: count: {count}")

    async def _send_alerts(self, count, nwsalert):
        _LOGGER.debug(f"Send Alerts: count: {count}")
        if not self._is_now_between(
            self._config.get(CONF_SEND_START_TIME, None),
            self._config.get(CONF_SEND_END_TIME, None),
        ):
            _LOGGER.debug(
                "Outside of time window "
                f"[{self._config.get(CONF_SEND_START_TIME, None)}, "
                f"{self._config.get(CONF_SEND_END_TIME, None)}], not sending."
            )
            return

    async def _extract_from_display_desc(self, desc, start, end):
        idx_start = desc.find(start)
        idx_end = desc.find(end)
        return desc[idx_start + len(start): idx_end].strip()

    def _is_now_between(self, begin_time_str, end_time_str):
        begin_time = time(
            hour=begin_time_str.split(":")[0],
            minute=begin_time_str.split(":")[1],
            second=begin_time_str.split(":")[2],
            tzinfo=dt_util.get_time_zone(self._hass.config.time_zone),
        )
        end_time = time(
            hour=end_time_str.split(":")[0],
            minute=end_time_str.split(":")[1],
            second=end_time_str.split(":")[2],
            tzinfo=dt_util.get_time_zone(self._hass.config.time_zone),
        )

        check_time = datetime.now(
            tz=dt_util.get_time_zone(self._hass.config.time_zone)
        ).time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else:  # crosses midnight
            return check_time >= begin_time or check_time <= end_time
