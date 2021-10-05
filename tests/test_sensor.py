"""Test NWS Alerts Sensors"""
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.util import slugify
from homeassistant.helpers import entity_registry as er

from custom_components.nws_alerts.const import DOMAIN
from tests.const import CONFIG_DATA, CONFIG_DATA_2

NWS_SENSOR = "sensor.nws_alerts"
NWS_SENSOR_2 = "sensor.nws_alerts_yaml"


async def test_sensor(hass):

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NWS Alerts",
        data=CONFIG_DATA,
    )

    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert "nws_alerts" in hass.config.components
    state = hass.states.get(NWS_SENSOR)
    assert state
    entity_registry = er.async_get(hass)
    entity = entity_registry.async_get(NWS_SENSOR)
    assert entity.unique_id == f"{slugify(entry.title)}_{entry.entry_id}"

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NWS Alerts YAML",
        data=CONFIG_DATA_2,
    )

    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert "nws_alerts" in hass.config.components
    state = hass.states.get(NWS_SENSOR_2)
    assert state
    entity_registry = er.async_get(hass)
    entity = entity_registry.async_get(NWS_SENSOR_2)
    assert entity.unique_id == f"{slugify(entry.title)}_{entry.entry_id}"
