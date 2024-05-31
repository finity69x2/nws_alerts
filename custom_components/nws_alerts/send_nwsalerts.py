import json
import logging
import os
from datetime import datetime, time

import homeassistant.util.dt as dt_util
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

from .const import (
    CONF_ANNOUNCE_CRITICAL_SERVICES,
    CONF_ANNOUNCE_CRITICAL_TYPES,
    CONF_ANNOUNCE_END_TIME,
    CONF_ANNOUNCE_SERVICES,
    CONF_ANNOUNCE_START_TIME,
    CONF_ANNOUNCE_TYPES,
    CONF_GPS_LOC,
    CONF_PERSISTENT_NOTIFICATIONS,
    CONF_SEND_CRITICAL_SERVICES,
    CONF_SEND_CRITICAL_TYPES,
    CONF_SEND_END_TIME,
    CONF_SEND_SERVICES,
    CONF_SEND_START_TIME,
    CONF_SEND_TYPES,
    CONF_TRACKER,
    CONF_ZONE_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
NWS_PREFIX_TO_CLEAR = "https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0."

NWS_EVENT = "event"
NWS_URL = "url"
NWS_EVENT_ID = "event_id"
NWS_MESSAGE_TYPE = "message_type"
NWS_EVENT_STATUS = "event_status"
NWS_EVENT_SEVERITY = "event_severity"
NWS_EVENT_EXPIRES = "event_expires"
NWS_DISPLAY_DESC = "display_desc"
NWS_CERTAINTY = "certainty"
NWS_DESCRIPTION = "description"
NWS_SPOKEN_DESC = "spoken_desc"


class Send_NWSAlerts:

    def __init__(self, hass: HomeAssistant, config) -> None:
        """Initialize the class to send NWS alerts."""
        self._hass = hass
        self._config = config
        self._name = config.get(CONF_NAME, None)
        self._history = {}
        self._history_imported = False
        self._unique_id = ""
        if CONF_ZONE_ID in config:
            self._unique_id = slugify(f"{config.get(CONF_ZONE_ID, '')}")
        elif CONF_GPS_LOC in config:
            self._unique_id = slugify(f"{config.get(CONF_GPS_LOC, '')}")
        elif CONF_TRACKER in config:
            self._unique_id = slugify(f"{config.get(CONF_TRACKER, '')}")
        self._json_filename = f"{DOMAIN}_{self._unique_id}.json"
        self._json_folder = self._hass.config.path(
            "custom_components", DOMAIN, "alert_history"
        )
        # _LOGGER.debug(f"Send_NWSAlerts: name: {self._name}, config: {self._config}")

    async def async_send(self, data):
        _LOGGER.debug("Send_NWSAlerts async_send")
        if not self._history_imported:
            self._history_imported = True
            await self._hass.async_add_executor_job(self._load_json)
        # _LOGGER.debug(f"Send_NWSAlerts async_send: data: {data}")

        # Clear any expired alerts or alerts no longer in the NWS feed
        # _LOGGER.debug(f"Initial self._history: {self._history}")
        await self._async_clear_expired_or_removed_alerts(data)
        # _LOGGER.debug(f"Updated self._history: {self._history}")

        if data.get("state", 0) == 0:
            return

        # _LOGGER.debug(f"Parsing {data.get('state', 0)}  alerts.")
        for count in range(data.get("state", 0)):
            nwsalert = await self._async_parse_alert(count, data)
            # _LOGGER.debug(f"nwsalert: {nwsalert}")

            # Skip if already alerted or already expired. If not, add to alert history and proceed.
            if nwsalert.get(NWS_EVENT_ID, None) in self._history.keys():
                _LOGGER.debug(
                    f"Already Alerted: {nwsalert.get(NWS_EVENT, None)}, Count: {count}"
                )
                continue
            elif nwsalert.get(NWS_EVENT_EXPIRES, None) < datetime.now(
                tz=dt_util.get_default_time_zone()
            ):
                _LOGGER.debug(
                    f"In feed but already expired: {nwsalert.get(NWS_EVENT, None)}, Count: {count}, expired: {
                        nwsalert.get(NWS_EVENT_EXPIRES, None)}, now: {datetime.now(tz=dt_util.get_default_time_zone())}"
                )
                continue
            else:
                self._history.update(
                    {
                        nwsalert.get(NWS_EVENT_ID, None): nwsalert.get(
                            NWS_EVENT_EXPIRES, None
                        )
                    }
                )

            # _LOGGER.debug(f"Sending Alert: {nwsalert.get(NWS_EVENT, None)}, Count: {count}")
            if self._config.get(CONF_PERSISTENT_NOTIFICATIONS, False) is True:
                await self._async_send_persistent_notification(count, nwsalert)

            if (
                nwsalert.get(NWS_EVENT, None)
                in self._config.get(CONF_ANNOUNCE_CRITICAL_TYPES, [])
                and len(self._config.get(CONF_ANNOUNCE_CRITICAL_SERVICES, [])) > 0
            ):
                await self._async_announce_critical_alert(count, nwsalert)

            if (
                nwsalert.get(NWS_EVENT, None)
                in self._config.get(CONF_ANNOUNCE_TYPES, [])
                and len(self._config.get(CONF_ANNOUNCE_SERVICES, [])) > 0
            ):
                await self._async_announce_alert(count, nwsalert)

            if (
                nwsalert.get(NWS_EVENT, None)
                in self._config.get(CONF_SEND_CRITICAL_TYPES, [])
                and len(self._config.get(CONF_SEND_CRITICAL_SERVICES, [])) > 0
            ):
                await self._async_send_critical_alert(count, nwsalert)

            if (
                nwsalert.get(NWS_EVENT, None) in self._config.get(CONF_SEND_TYPES, [])
                and len(self._config.get(CONF_SEND_SERVICES, [])) > 0
            ):
                await self._async_send_alert(count, nwsalert)

        await self._hass.async_add_executor_job(self._save_json)

    async def _async_parse_alert(self, count, data):
        nwsalert = {}

        nwsalert[NWS_EVENT] = (
            data.get(NWS_EVENT, "").split(" - ")[count].replace('"', "")
        )
        _LOGGER.debug(
            f"Parse Alert: count: {count}, event: {nwsalert.get(NWS_EVENT, None)}"
        )
        nwsalert[NWS_URL] = (
            data.get(NWS_EVENT_ID, "").split(" - ")[count].replace('"', "")
        )
        # _LOGGER.debug(f"url: {nwsalert['url']}")

        nwsalert[NWS_EVENT_ID] = (
            data.get(NWS_EVENT_ID, "")
            .split(" - ")[count]
            .replace('"', "")
            .replace(NWS_PREFIX_TO_CLEAR, "")
            .replace(".", "")
        )
        # _LOGGER.debug(f"event_id: {nwsalert[NWS_EVENT_ID]}")
        nwsalert[NWS_MESSAGE_TYPE] = (
            data.get(NWS_MESSAGE_TYPE, "").split(" - ")[count].replace('"', "")
        )
        # _LOGGER.debug(f"message_type: {nwsalert[NWS_MESSAGE_TYPE]}")
        nwsalert[NWS_EVENT_STATUS] = (
            data.get(NWS_EVENT_STATUS, "").split(" - ")[count].replace('"', "")
        )
        # _LOGGER.debug(f"event_status: {nwsalert[NWS_EVENT_STATUS]}")
        nwsalert[NWS_EVENT_SEVERITY] = (
            data.get(NWS_EVENT_SEVERITY, "").split(" - ")[count].replace('"', "")
        )
        # _LOGGER.debug(f"event_severity: {nwsalert[NWS_EVENT_SEVERITY]}")
        event_expires_str = (
            data.get(NWS_EVENT_EXPIRES, "").split(" - ")[count].replace('"', "")
        )
        # 2024-05-29T22:30:00-05:00
        # event_expires = datetime.strptime(event_expires_str, "%Y-%m-%dT%H:%M:%s%z")
        nwsalert[NWS_EVENT_EXPIRES] = datetime.fromisoformat(event_expires_str)
        # _LOGGER.debug(f"event_expires: {nwsalert[NWS_EVENT_EXPIRES]}")

        nwsalert[NWS_DISPLAY_DESC] = (
            data.get(NWS_DISPLAY_DESC, "")
            .split("\n\n-\n\n")[count]
            .replace('"', "")
            .replace("\n>\n", "")
            .strip()
        )
        headline = nwsalert[NWS_DISPLAY_DESC][
            nwsalert[NWS_DISPLAY_DESC].find("Headline: ")
            + len("Headline: "): nwsalert[NWS_DISPLAY_DESC].find("\nStatus:")
        ].strip()
        if headline.isupper():
            nwsalert[NWS_DISPLAY_DESC] = (
                nwsalert[NWS_DISPLAY_DESC][
                    : nwsalert[NWS_DISPLAY_DESC].find("Headline: ") + len("Headline: ")
                ]
                + headline.title()
                + nwsalert[NWS_DISPLAY_DESC][
                    nwsalert[NWS_DISPLAY_DESC].find("\nStatus:"):
                ]
            )

        nwsalert[NWS_CERTAINTY] = nwsalert[NWS_DISPLAY_DESC][
            nwsalert[NWS_DISPLAY_DESC].find("Certainty: ")
            + len("Certainty: "): nwsalert[NWS_DISPLAY_DESC].find("\nExpires:")
        ].strip()
        # _LOGGER.debug(f"certainty: {nwsalert[NWS_CERTAINTY]}")

        nwsalert[NWS_DESCRIPTION] = (
            nwsalert[NWS_DISPLAY_DESC][
                nwsalert[NWS_DISPLAY_DESC].find("Description: ")
                + len("Description: "):
            ]
            .replace("\n\n", "<00temp00>")
            .replace("\n", " ")
            .replace("<00temp00>", "\n\n")
            .strip()
        )
        # _LOGGER.debug(f"description: {nwsalert[NWS_DESCRIPTION]}")

        nwsalert[NWS_SPOKEN_DESC] = (
            data.get(NWS_SPOKEN_DESC, "").split("\n\n-\n\n")[count].replace('"', "")
        )
        if nwsalert[NWS_SPOKEN_DESC].isupper():
            nwsalert[NWS_SPOKEN_DESC] = nwsalert[NWS_SPOKEN_DESC].title()
        # _LOGGER.debug(f"spoken_desc: {nwsalert[NWS_SPOKEN_DESC]}")
        return nwsalert

    async def _async_send_persistent_notification(self, count, nwsalert):
        _LOGGER.debug(
            f"Send Persistent Notification: count: {
                count}, event: {nwsalert.get(NWS_EVENT, None)}"
        )
        await self._hass.services.async_call(
            "persistent_notification",
            "create",
            service_data={
                "message": f"{nwsalert.get(NWS_DISPLAY_DESC, None)}\n\n{nwsalert.get(NWS_EVENT_ID, None)}",
                "title": nwsalert.get(NWS_EVENT, None),
                "notification_id": nwsalert.get(NWS_EVENT_ID, None),
            },
        )

    async def _async_announce_critical_alert(self, count, nwsalert):
        _LOGGER.debug(
            f"Announce Critical Alerts: count: {
                count}, event: {nwsalert.get(NWS_EVENT, None)}"
        )

    async def _async_announce_alert(self, count, nwsalert):
        _LOGGER.debug(
            f"Announce Alerts: count: {count}, event: {nwsalert.get(NWS_EVENT, None)}"
        )
        if not await self._async_is_now_between(
            self._config.get(CONF_ANNOUNCE_START_TIME, None),
            self._config.get(CONF_ANNOUNCE_END_TIME, None),
        ):
            _LOGGER.debug(
                "Outside of time window "
                f"[{self._config.get(CONF_ANNOUNCE_START_TIME, None)}, "
                f"{self._config.get(CONF_ANNOUNCE_END_TIME, None)}], not sending {
                    nwsalert.get(NWS_EVENT, None)}."
            )
            return

    async def _async_send_critical_alert(self, count, nwsalert):
        _LOGGER.debug(
            f"Send Critical Alerts: count: {count}, event: {
                nwsalert.get(NWS_EVENT, None)}"
        )

        for service in self._config.get(CONF_SEND_CRITICAL_SERVICES, []):
            _LOGGER.debug(f"Sending {nwsalert.get(NWS_EVENT, None)} to: {service}")
            await self._hass.services.async_call(
                "notify",
                service,
                service_data={
                    "message": f"{nwsalert.get(NWS_SPOKEN_DESC, None)}\n\n{nwsalert.get(NWS_EVENT_ID, None)}",
                    "title": nwsalert.get(NWS_EVENT, None),
                    "data": {
                        "tag": nwsalert.get(NWS_EVENT_ID, None),
                        "push": {
                            "sound": {"name": "default", "critical": 1, "volume": 1.0}
                        },
                        "ttl": 0,
                        "priority": "high",
                        "channel": "alarm_stream",
                    },
                },
            )

    async def _async_send_alert(self, count, nwsalert):
        _LOGGER.debug(
            f"Send Alerts: count: {count}, event: {nwsalert.get(NWS_EVENT, None)}"
        )
        if not await self._async_is_now_between(
            self._config.get(CONF_SEND_START_TIME, None),
            self._config.get(CONF_SEND_END_TIME, None),
        ):
            _LOGGER.debug(
                "Outside of time window "
                f"[{self._config.get(CONF_SEND_START_TIME, None)}, "
                f"{self._config.get(CONF_SEND_END_TIME, None)}], not sending {
                    nwsalert.get(NWS_EVENT, None)}."
            )
            return

        for service in self._config.get(CONF_SEND_SERVICES, []):
            _LOGGER.debug(f"Sending {nwsalert.get(NWS_EVENT, None)} to: {service}")
            await self._hass.services.async_call(
                "notify",
                service,
                service_data={
                    "message": f"{nwsalert.get(NWS_SPOKEN_DESC, None)}\n\n{nwsalert.get(NWS_EVENT_ID, None)}",
                    "title": nwsalert.get(NWS_EVENT, None),
                    "data": {
                        "tag": nwsalert.get(NWS_EVENT_ID, None),
                    },
                },
            )

    async def _async_clear_persistent_notification(self, id):
        _LOGGER.debug(f"Clearing {id} from: persistent_notification")
        await self._hass.services.async_call(
            "persistent_notification",
            "dismiss",
            service_data={"notification_id": id},
        )

    async def _async_clear_sent_notification(self, id, services):
        for service in services:
            _LOGGER.debug(f"Clearing {id} from: {service}")
            await self._hass.services.async_call(
                "notify",
                service,
                service_data={
                    "message": "clear_notification",
                    "data": {
                        "tag": id,
                    },
                },
            )

    async def _async_clear_expired_or_removed_alerts(self, data):
        _LOGGER.debug("Clearing Expired Alerts or Alerts no longer in the Feed")
        expnow = datetime.now(tz=dt_util.get_default_time_zone())
        event_ids_full = []
        if data.get(NWS_EVENT_ID, None) is not None:
            event_ids_full = data.get(NWS_EVENT_ID, "").split(" - ")
        event_ids = []
        for full_id in event_ids_full:
            event_ids.append(
                full_id.replace('"', "")
                .replace(NWS_PREFIX_TO_CLEAR, "")
                .replace(".", "")
            )
        for id, expires in self._history.copy().items():
            if id not in event_ids or expires < expnow:
                _LOGGER.debug(f"Removing: {id}")
                # Clear notifications here
                if self._config.get(CONF_PERSISTENT_NOTIFICATIONS, False) is True:
                    await self._async_clear_persistent_notification(id)
                if (
                    len(self._config.get(CONF_SEND_CRITICAL_TYPES, [])) > 0
                    and len(self._config.get(CONF_SEND_CRITICAL_SERVICES, [])) > 0
                ):
                    await self._async_clear_sent_notification(
                        self, id, self._config.get(CONF_SEND_CRITICAL_SERVICES, [])
                    )

                if (
                    len(self._config.get(CONF_SEND_TYPES, [])) > 0
                    and len(self._config.get(CONF_SEND_SERVICES, [])) > 0
                ):
                    await self._async_clear_sent_notification(
                        self, id, self._config.get(CONF_SEND_SERVICES, [])
                    )
                self._history.pop(id, None)
            # else:
            #    _LOGGER.debug(f"Keeping: {id} expires: {expires}, now: {expnow}")

    def _create_json_folder(self):
        _LOGGER.debug("Creating JSON Folder")
        try:
            os.makedirs(self._json_folder, exist_ok=True)
        except OSError as e:
            _LOGGER.warning(
                "OSError creating folder for JSON alert history files: "
                f"{e.__class__.__qualname__}: {e}"
            )
        except Exception as e:
            _LOGGER.warning(
                "Exception creating folder for JSON alert history files: "
                f"{e.__class__.__qualname__}: {e}"
            )

    def _load_json(self):
        self._create_json_folder()
        _LOGGER.debug("Loading JSON")
        history = {}
        try:
            with open(
                os.path.join(self._json_folder, self._json_filename),
                "r",
            ) as jsonfile:
                history = json.load(jsonfile)
        except OSError as e:
            _LOGGER.debug(
                "No JSON file to import "
                f"({self._json_filename}): {e.__class__.__qualname__}: {e}"
            )
            return
        except Exception as e:
            _LOGGER.debug(
                "Exception importing JSON file "
                f"({self._json_filename}): {e.__class__.__qualname__}: {e}"
            )
            return
        _LOGGER.debug(f"json history: {history}")
        for k, v in history.items():
            self._history.update({k: datetime.fromisoformat(v)})

    def _save_json(self):
        _LOGGER.debug("Saving JSON")
        save_history = {}
        for k, v in self._history.items():
            save_history.update({k: v.isoformat()})
        try:
            with open(
                os.path.join(self._json_folder, self._json_filename),
                "w",
            ) as jsonfile:
                json.dump(save_history, jsonfile)
        except OSError as e:
            _LOGGER.debug(
                "OSError writing JSON alert history file "
                f"({self._json_filename}): {e.__class__.__qualname__}: {e}"
            )
        except Exception as e:
            _LOGGER.debug(
                "Exception writing JSON alert history file "
                f"({self._json_filename}): {e.__class__.__qualname__}: {e}"
            )

    async def _async_is_now_between(self, begin_time_str, end_time_str):
        begin_time = time(
            hour=int(begin_time_str.split(":")[0]),
            minute=int(begin_time_str.split(":")[1]),
            second=int(begin_time_str.split(":")[2]),
            # dt_util.get_time_zone(self._hass.config.time_zone),
            tzinfo=dt_util.get_default_time_zone(),
        )
        end_time = time(
            hour=int(end_time_str.split(":")[0]),
            minute=int(end_time_str.split(":")[1]),
            second=int(end_time_str.split(":")[2]),
            tzinfo=dt_util.get_default_time_zone(),
        )

        check_time = datetime.now(tz=dt_util.get_default_time_zone()).time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else:  # crosses midnight
            return check_time >= begin_time or check_time <= end_time

    def _removing_from_hass(self):
        try:
            os.remove(os.path.join(self._json_folder, self._json_filename))
        except OSError as e:
            _LOGGER.debug(
                "OSError removing JSON alert history file "
                f"({self._json_filename}): {e.__class__.__qualname__}: {e}"
            )
        except Exception as e:
            _LOGGER.debug(
                "Unknown Exception removing JSON alert history file "
                f"({self._json_filename}): {e.__class__.__qualname__}: {e}"
            )
        else:
            _LOGGER.info(
                "JSON alert history file removed: "
                f"{
                    self._json_filename}"
            )
