"""Test NWS Alerts Sensors"""

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify
from homeassistant.helpers import entity_registry as er

from custom_components.nws_alerts.const import (
    DOMAIN,
    API_ENDPOINT,
    LIST_ALERTS_SERVICE_NAME,
)
from tests.const import (
    CONFIG_DATA,
    CONFIG_DATA_2,
    NWS_RESPONSE,
    NWS_COUNT_RESPONSE,
)

pytestmark = pytest.mark.asyncio

NWS_SENSOR = "sensor.nws_alerts"
NWS_SENSOR_2 = "sensor.nws_alerts_yaml"


async def test_sensor(hass: HomeAssistant):
    """Test the sensor."""
    entry = await setup_entry(hass, "NWS Alerts", CONFIG_DATA)

    state = hass.states.get(NWS_SENSOR)
    assert state
    entity_registry = er.async_get(hass)
    entity = entity_registry.async_get(NWS_SENSOR)
    assert entity
    assert entity.unique_id == f"{slugify(entry.title)}_{entry.entry_id}"

    entry = await setup_entry(hass, "NWS Alerts YAML", CONFIG_DATA_2)

    state = hass.states.get(NWS_SENSOR_2)
    assert state
    entity_registry = er.async_get(hass)
    entity = entity_registry.async_get(NWS_SENSOR_2)
    assert entity
    assert entity.unique_id == f"{slugify(entry.title)}_{entry.entry_id}"


async def test_sensor_service(hass: HomeAssistant, mocker):
    """Validate the service call to get alerts"""

    session_builder = AiohttpClientMocker()
    session_builder.request(
        "get", f"{API_ENDPOINT}/alerts/active/count", json=NWS_COUNT_RESPONSE
    )
    session_builder.request(
        "get",
        f"{API_ENDPOINT}/alerts/active?zone={CONFIG_DATA['zone_id']}",
        json=NWS_RESPONSE,
    )

    mocker.patch(
        "aiohttp.ClientSession",
        return_value=session_builder.create_session(None),
    )

    await setup_entry(hass, "NWS Alerts", CONFIG_DATA)

    state = hass.states.get(NWS_SENSOR)
    assert state
    assert state.state == "2"

    response = await hass.services.async_call(
        DOMAIN,
        LIST_ALERTS_SERVICE_NAME,
        target={"entity_id": NWS_SENSOR},
        blocking=True,
        return_response=True,
    )
    assert response
    alerts: list[dict[str, Any]] = response[NWS_SENSOR]
    assert len(alerts) == 2
    assert alerts[0]["title"] == "Flood Advisory"
    assert alerts[0]["message_type"] == "Alert"
    assert alerts[0]["event_status"] == "Actual"
    assert alerts[0]["event_severity"] == "Minor"
    assert alerts[0]["event_expires"] == "2024-04-28T17:00:00-05:00"
    assert alerts[0]["display_desc"] == (
        "Headline: FLOOD ADVISORY IN EFFECT UNTIL 5 PM CDT THIS AFTERNOON"
        "\nStatus: Actual\nMessage Type: Alert\nSeverity: Minor\n"
        "Certainty: Likely\nExpires: 2024-04-28T17:00:00-05:00\nDescription: "
        "* WHAT...Urban and small stream flooding caused by excessive\n"
        "rainfall is expected.\nInstruction: Turn around, don't drown when "
        "encountering flooded roads. Most flood\ndeaths occur in vehicles."
    )
    assert alerts[0]["spoken_desc"] == (
        "FLOOD ADVISORY IN EFFECT UNTIL 5 PM CDT THIS AFTERNOON"
    )
    assert alerts[1]["title"] == "Special Weather Statement"
    assert alerts[1]["message_type"] == "Alert"
    assert alerts[1]["event_status"] == "Actual"
    assert alerts[1]["event_severity"] == "Moderate"
    assert alerts[1]["event_expires"] == "2024-04-28T14:15:00-05:00"
    assert alerts[1]["display_desc"] == (
        "Headline: A strong thunderstorm will impact portions of central "
        "Williamson County through 215 PM CDT\nStatus: Actual\nMessage Type: "
        "Alert\nSeverity: Moderate\nCertainty: Observed\nExpires: "
        "2024-04-28T14:15:00-05:00\nDescription: At 131 PM CDT, Doppler radar "
        "was tracking a strong thunderstorm near places.\nInstruction: If "
        "outdoors, consider seeking shelter inside a building."
    )
    assert alerts[1]["spoken_desc"] == (
        "A strong thunderstorm will impact portions of central Williamson "
        "County through 215 PM CDT"
    )


async def test_sensor_attributes(hass: HomeAssistant, mocker):
    """Validate the format of the sensor attributes"""

    session_builder = AiohttpClientMocker()
    session_builder.request(
        "get", f"{API_ENDPOINT}/alerts/active/count", json=NWS_COUNT_RESPONSE
    )
    session_builder.request(
        "get",
        f"{API_ENDPOINT}/alerts/active?zone={CONFIG_DATA['zone_id']}",
        json=NWS_RESPONSE,
    )

    mocker.patch(
        "aiohttp.ClientSession",
        return_value=session_builder.create_session(None),
    )

    await setup_entry(hass, "NWS Alerts", CONFIG_DATA)

    state = hass.states.get(NWS_SENSOR)
    assert state
    assert state.state == "2"
    assert (
        state.attributes["title"]
        == "Flood Advisory - Special Weather Statement"
    )
    assert state.attributes["message_type"] == "Alert - Alert"
    assert state.attributes["event_status"] == "Actual - Actual"
    assert state.attributes["event_severity"] == "Minor - Moderate"
    assert (
        state.attributes["event_expires"]
        == "2024-04-28T17:00:00-05:00 - 2024-04-28T14:15:00-05:00"
    )
    assert state.attributes["display_desc"] == (
        "\n>\nHeadline: FLOOD ADVISORY IN EFFECT UNTIL 5 PM CDT THIS AFTERNOON"
        "\nStatus: Actual\nMessage Type: Alert\nSeverity: Minor\n"
        "Certainty: Likely\nExpires: 2024-04-28T17:00:00-05:00\nDescription: "
        "* WHAT...Urban and small stream flooding caused by excessive\n"
        "rainfall is expected.\nInstruction: Turn around, don't drown when "
        "encountering flooded roads. Most flood\ndeaths occur in vehicles."
        "\n\n-\n\n"
        "\n>\nHeadline: A strong thunderstorm will impact portions of central "
        "Williamson County through 215 PM CDT\nStatus: Actual\nMessage Type: "
        "Alert\nSeverity: Moderate\nCertainty: Observed\nExpires: "
        "2024-04-28T14:15:00-05:00\nDescription: At 131 PM CDT, Doppler radar "
        "was tracking a strong thunderstorm near places.\nInstruction: If "
        "outdoors, consider seeking shelter inside a building."
    )
    assert state.attributes["spoken_desc"] == (
        "FLOOD ADVISORY IN EFFECT UNTIL 5 PM CDT THIS AFTERNOON"
        "\n\n-\n\n"
        "A strong thunderstorm will impact portions of central Williamson "
        "County through 215 PM CDT"
    )
    assert "alerts" not in state.attributes


async def setup_entry(hass: HomeAssistant, entry_title, config):
    """Set up the sensor in hass"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=entry_title,
        data=config,
    )

    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert "nws_alerts" in hass.config.components
    return entry
