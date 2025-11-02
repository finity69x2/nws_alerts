"""Tests for init."""

import logging

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nws_alerts.const import DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from tests.const import CONFIG_DATA, CONFIG_DATA_3

pytestmark = pytest.mark.asyncio


async def test_setup_entry(hass, mock_api, caplog):
    """Test settting up entities."""
    with caplog.at_level(logging.DEBUG):
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="NWS Alerts",
            data=CONFIG_DATA,
            version=1,
        )

        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 2
        entries = hass.config_entries.async_entries(DOMAIN)
        assert len(entries) == 1
        assert "Migration to version 2 complete" in caplog.text


async def test_unload_entry(hass, mock_api):
    """Test unloading entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NWS Alerts",
        data=CONFIG_DATA_3,
    )

    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 2
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    assert await hass.config_entries.async_unload(entries[0].entry_id)
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 2
    assert len(hass.states.async_entity_ids(DOMAIN)) == 0

    assert await hass.config_entries.async_remove(entries[0].entry_id)
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 0
