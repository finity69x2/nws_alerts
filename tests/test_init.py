"""Tests for init."""
import pytest
from unittest.mock import patch

from homeassistant.const import CONF_NAME
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nws_alerts.const import CONF_ZONE_ID, DOMAIN
from tests.const import CONFIG_DATA


async def test_setup_entry(
    hass,
):
    """Test settting up entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NWS Alerts",
        data=CONFIG_DATA,
    )

    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 1
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1


async def test_unload_entry(hass):
    """Test unloading entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NWS Alerts",
        data=CONFIG_DATA,
    )

    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 1
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    assert await hass.config_entries.async_unload(entries[0].entry_id)
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 1
    assert len(hass.states.async_entity_ids(DOMAIN)) == 0

    assert await hass.config_entries.async_remove(entries[0].entry_id)
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 0


@pytest.mark.parametrize(
    "config, expected_config_entry, expected_calls, expected_to_succeed",
    [
        (
            {
                DOMAIN: {
                    CONF_NAME: "NWS Alerts",
                    CONF_ZONE_ID: "AZZ540,AZC013",
                }
            },
            {
                CONF_NAME: "NWS Alerts",
                CONF_ZONE_ID: "AZZ540,AZC013",
            },
            1,
            True,
        )
    ],
)
async def test_import(
    hass,
    config,
    expected_config_entry,
    expected_calls,
    expected_to_succeed,
):
    """Test importing a gateway."""
    await async_setup_component(hass, "persistent_notification", {})
    with patch(
        "custom_components.nws_alerts.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await async_setup_component(hass, DOMAIN, config)
        assert result == expected_to_succeed
        await hass.async_block_till_done()

    assert len(mock_setup_entry.mock_calls) == expected_calls

    config_entry = mock_setup_entry.mock_calls[0][1][1]
    config_entry_data = dict(config_entry.data)
    assert config_entry_data == expected_config_entry
