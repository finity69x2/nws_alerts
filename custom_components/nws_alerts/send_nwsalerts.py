import asyncio
import json
import logging
import os
from datetime import datetime, time

import homeassistant.util.dt as dt_util
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

from .const import (
    CONF_ANNOUNCE_CRITICAL_ENTITIES,
    CONF_ANNOUNCE_CRITICAL_TYPES,
    CONF_ANNOUNCE_END_TIME,
    CONF_ANNOUNCE_ENTITIES,
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
    NWS_CERTAINTY,
    NWS_DESCRIPTION,
    NWS_EVENT,
    NWS_EVENT_EXPIRES,
    NWS_EVENT_ID_SHORT,
    NWS_EVENT_SEVERITY,
    NWS_HEADLINE,
    NWS_HEADLINE_LONG,
    NWS_INSTRUCTION,
)

_LOGGER = logging.getLogger(__name__)


class Send_NWSAlerts:
    def __init__(self, hass: HomeAssistant, config) -> None:
        """Initialize the class to send NWS alerts."""
        # _LOGGER.debug(f"Send_NWSAlerts: name: {self._name}, config: {self._config}")
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
        self._entity_registry = er.async_get(hass)
        self._announce_alexa_entities = []
        for ent in self._config.get(CONF_ANNOUNCE_ENTITIES, []):
            er_ent = self._entity_registry.async_get(ent)
            if er_ent.platform == "alexa_media":
                self._announce_alexa_entities.append(ent)
        self._announce_critical_alexa_entities = []
        for ent in self._config.get(CONF_ANNOUNCE_CRITICAL_ENTITIES, []):
            er_ent = self._entity_registry.async_get(ent)
            if er_ent.platform == "alexa_media":
                self._announce_critical_alexa_entities.append(ent)
        self._send_mobile_app_services = self._config.get(CONF_SEND_SERVICES, [])
        self._send_critical_mobile_app_services = self._config.get(
            CONF_SEND_CRITICAL_SERVICES, []
        )

    async def async_send(self, array):
        if not self._history_imported:
            self._history_imported = True
            await self._hass.async_add_executor_job(self._load_json)
        # _LOGGER.debug(f"Send_NWSAlerts async_send: array: {array}")

        # Clear any expired alerts or alerts no longer in the NWS feed
        await self._async_clear_expired_or_removed_alerts(array)

        if len(array) == 0:
            return

        for nwsalert in array:
            # _LOGGER.debug(f"nwsalert: {nwsalert}")

            # Skip if already alerted or already expired. If not, add to alert history and proceed.
            if nwsalert.get(NWS_EVENT_ID_SHORT, None) in self._history.keys():
                # Already Alerted
                # _LOGGER.debug(f"Already Alerted: {nwsalert.get(NWS_EVENT, None)}")
                continue
            elif nwsalert.get(NWS_EVENT_EXPIRES, None) < datetime.now(
                tz=dt_util.get_default_time_zone()
            ):
                # Already Expired
                # _LOGGER.debug(f"In feed but already expired: {nwsalert.get(NWS_EVENT, None)}, expired: {nwsalert.get(NWS_EVENT_EXPIRES, None)}, now: {datetime.now(tz=dt_util.get_default_time_zone())}")
                continue
            else:
                self._history.update(
                    {
                        nwsalert.get(NWS_EVENT_ID_SHORT, None): nwsalert.get(
                            NWS_EVENT_EXPIRES, None
                        )
                    }
                )

            # _LOGGER.debug(f"Sending Alert: {nwsalert.get(NWS_EVENT, None)}")
            if nwsalert.get(NWS_EVENT, None) is None:
                continue
            if self._config.get(CONF_PERSISTENT_NOTIFICATIONS, False) is True:
                await self._async_send_persistent_notification(nwsalert)

            if (
                nwsalert.get(NWS_EVENT, None).lower()
                in [
                    x.lower()
                    for x in self._config.get(CONF_ANNOUNCE_CRITICAL_TYPES, [])
                ]
                and len(self._config.get(CONF_ANNOUNCE_CRITICAL_ENTITIES, [])) > 0
            ):
                await self._async_announce_critical_alert(nwsalert)

            if (
                nwsalert.get(NWS_EVENT, None).lower()
                in [x.lower() for x in self._config.get(CONF_ANNOUNCE_TYPES, [])]
                and len(self._config.get(CONF_ANNOUNCE_ENTITIES, [])) > 0
            ):
                await self._async_announce_alert(nwsalert)

            if (
                nwsalert.get(NWS_EVENT, None).lower()
                in [x.lower() for x in self._config.get(CONF_SEND_CRITICAL_TYPES, [])]
                and len(self._config.get(CONF_SEND_CRITICAL_SERVICES, [])) > 0
            ):
                await self._async_send_critical_alert(nwsalert)

            if (
                nwsalert.get(NWS_EVENT, None).lower()
                in [x.lower() for x in self._config.get(CONF_SEND_TYPES, [])]
                and len(self._config.get(CONF_SEND_SERVICES, [])) > 0
            ):
                await self._async_send_alert(nwsalert)

        await self._hass.async_add_executor_job(self._save_json)

    async def _async_send_persistent_notification(self, nwsalert):
        _LOGGER.debug(
            f"Sending Persistent Notification for {nwsalert.get(NWS_EVENT, None)}"
        )
        # _LOGGER.debug(f"Sending Persistent Notification for {nwsalert.get(NWS_EVENT, None)}: {nwsalert}")
        message = f"### {nwsalert.get(NWS_HEADLINE_LONG, None)}\n"
        if (
            nwsalert.get(NWS_EVENT_SEVERITY, None) is not None
            and nwsalert.get(NWS_EVENT_SEVERITY, None) != "Unknown"
        ):
            message = (
                message
                + f"### **Severity**: {nwsalert.get(NWS_EVENT_SEVERITY, None)}\n"
            )
        if (
            nwsalert.get(NWS_CERTAINTY, None) is not None
            and nwsalert.get(NWS_CERTAINTY, None) != "Unknown"
        ):
            message = (
                message + f"### **Certainty**: {nwsalert.get(NWS_CERTAINTY, None)}\n\n"
            )
        if (
            nwsalert.get(NWS_DESCRIPTION, None) is not None
            and nwsalert.get(NWS_DESCRIPTION, None) != "None"
        ):
            message = (
                message + f"### Description\n{nwsalert.get(NWS_DESCRIPTION, None)}\n\n"
            )
        if (
            nwsalert.get(NWS_INSTRUCTION, None) is not None
            and nwsalert.get(NWS_INSTRUCTION, None) != "None"
        ):
            message = (
                message + f"### Instruction\n{nwsalert.get(NWS_INSTRUCTION, None)}"
            )
        await self._hass.services.async_call(
            "persistent_notification",
            "create",
            service_data={
                "message": message,
                "title": nwsalert.get(NWS_HEADLINE, None),
                "notification_id": nwsalert.get(NWS_EVENT_ID_SHORT, None),
            },
        )

    async def _async_announce_critical_alert(self, nwsalert):
        _LOGGER.debug(f"Announcing Critical Alerts for {nwsalert.get(NWS_EVENT, None)}")
        if len(self._announce_critical_alexa_entities) > 0:
            await self._async_announce_alexa_alert(
                nwsalert, self._announce_critical_alexa_entities, critical=True
            )

    async def _async_announce_alert(self, nwsalert):
        _LOGGER.debug(f"Announcing Alert for {nwsalert.get(NWS_EVENT, None)}")
        if not await self._async_is_now_between(
            self._config.get(CONF_ANNOUNCE_START_TIME, None),
            self._config.get(CONF_ANNOUNCE_END_TIME, None),
        ):
            # Outside of time window
            # _LOGGER.debug(f"Outside of time window [{self._config.get(CONF_ANNOUNCE_START_TIME, None)}, {self._config.get(CONF_ANNOUNCE_END_TIME, None)}], not sending {nwsalert.get(NWS_EVENT, None)}.")
            return
        if len(self._announce_alexa_entities) > 0:
            await self._async_announce_alexa_alert(
                nwsalert, self._announce_alexa_entities
            )

    async def _async_announce_alexa_alert(
        self, nwsalert, alexa_entities, critical=False
    ):
        _LOGGER.debug(
            f"Alexa Sending {nwsalert.get(NWS_EVENT, None)} to: {alexa_entities}"
        )
        await self._hass.services.async_call(
            "media_player",
            "volume_set",
            service_data={"entity_id": alexa_entities, "volume_level": 0.6},
        )
        await self._hass.services.async_call(
            "notify",
            "alexa_media",
            service_data={
                "target": alexa_entities,
                "message": f"Attention!,,,Attention!,,,The National Weather Service Has issued a {nwsalert.get(NWS_EVENT, None)} for our area",
                "data": {"type": "tts"},
            },
        )
        await asyncio.sleep(15)
        if critical:
            await self._hass.services.async_call(
                "notify",
                "alexa_media",
                service_data={
                    "target": alexa_entities,
                    "message": "<audio src='https://h7a3u8r0lt405rwrar1rcgi8ep9a1gez.ui.nabu.casa/local/mp3/nws_alert_tone.mp3'/>",
                    "data": {"type": "tts"},
                },
            )
            await asyncio.sleep(25)
            await self._hass.services.async_call(
                "notify",
                "alexa_media",
                service_data={
                    "target": alexa_entities,
                    "message": f"Attention!,,,Attention!,,,The National Weather Service Has issued a {nwsalert.get(NWS_EVENT, None)} for our area",
                    "data": {"type": "tts"},
                },
            )
            await asyncio.sleep(15)
        await self._hass.services.async_call(
            "media_player",
            "volume_set",
            service_data={"entity_id": alexa_entities, "volume_level": 0.5},
        )

    async def _async_send_critical_alert(self, nwsalert):
        _LOGGER.debug(f"Sending Critical Alert for {nwsalert.get(NWS_EVENT, None)}")

        if len(self._send_critical_mobile_app_services) > 0:
            await self._async_send_mobile_app_alert(
                nwsalert, self._send_critical_mobile_app_services, critical=True
            )

    async def _async_send_alert(self, nwsalert):
        _LOGGER.debug(f"Sending Alert for {nwsalert.get(NWS_EVENT, None)}")
        if not await self._async_is_now_between(
            self._config.get(CONF_SEND_START_TIME, None),
            self._config.get(CONF_SEND_END_TIME, None),
        ):
            # Outside of time window
            # _LOGGER.debug(f"Outside of time window [{self._config.get(CONF_SEND_START_TIME, None)}, {self._config.get(CONF_SEND_END_TIME, None)}], not sending {nwsalert.get(NWS_EVENT, None)}.")
            return

        if len(self._send_mobile_app_services) > 0:
            await self._async_send_mobile_app_alert(
                nwsalert, self._send_mobile_app_services
            )

    async def _async_send_mobile_app_alert(
        self, nwsalert, mobile_app_entities, critical=False
    ):
        _LOGGER.debug(
            f"Mobile App Sending {nwsalert.get(NWS_EVENT, None)} to: {mobile_app_entities}"
        )
        for service in mobile_app_entities:
            # _LOGGER.debug(f"Mobile App Sending {nwsalert.get(NWS_EVENT, None)} to: {service}")
            service_data = {
                "message": f"{nwsalert.get(NWS_HEADLINE, None)}",
                "title": nwsalert.get(NWS_EVENT, None),
            }
            if critical:
                service_data.update(
                    {
                        "data": {
                            "tag": nwsalert.get(NWS_EVENT_ID_SHORT, None),
                            "push": {
                                "sound": {
                                    "name": "default",
                                    "critical": 1,
                                    "volume": 1.0,
                                }
                            },
                            "ttl": 0,
                            "priority": "high",
                            "channel": "alarm_stream",
                        }
                    }
                )
            else:
                service_data.update(
                    {"data": {"tag": nwsalert.get(NWS_EVENT_ID_SHORT, None)}}
                )
            await self._hass.services.async_call(
                "notify",
                service,
                service_data=service_data,
            )

    async def _async_clear_persistent_notification(self, id):
        _LOGGER.debug(f"Clearing {id} from: persistent_notification")
        await self._hass.services.async_call(
            "persistent_notification",
            "dismiss",
            service_data={"notification_id": id},
        )

    async def _async_clear_sent_mobile_app_notification(self, id, services):
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

    async def _async_clear_expired_or_removed_alerts(self, array):
        _LOGGER.debug("Clearing Expired Alerts or Alerts no longer in the Feed")
        expnow = datetime.now(tz=dt_util.get_default_time_zone())
        event_ids = []
        if len(array) > 0:
            event_ids = [nwsalert.get(NWS_EVENT_ID_SHORT) for nwsalert in array]

        for id, expires in self._history.copy().items():
            if id not in event_ids or expires < expnow:
                # _LOGGER.debug(f"Removing: {id}")
                if self._config.get(CONF_PERSISTENT_NOTIFICATIONS, False) is True:
                    await self._async_clear_persistent_notification(id)
                if (
                    len(self._config.get(CONF_SEND_CRITICAL_TYPES, [])) > 0
                    and len(self._send_critical_mobile_app_services) > 0
                ):
                    await self._async_clear_sent_mobile_app_notification(
                        id, self._send_critical_mobile_app_services
                    )
                if (
                    len(self._config.get(CONF_SEND_TYPES, [])) > 0
                    and len(self._send_mobile_app_services) > 0
                ):
                    await self._async_clear_sent_mobile_app_notification(
                        id, self._send_mobile_app_services
                    )
                self._history.pop(id, None)

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
            _LOGGER.info(f"JSON alert history file removed: {self._json_filename}")
