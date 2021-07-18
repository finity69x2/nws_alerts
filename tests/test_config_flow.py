"""Test for config flow"""
from tests.const import CONFIG_DATA
from unittest.mock import patch
import pytest
from homeassistant import config_entries, data_entry_flow, setup
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nws_alerts.const import DOMAIN


@pytest.mark.parametrize(
    "input,step_id,title,data",
    [
        (
            {
                "name": "Testing Alerts",
                "zone_id": "AZZ540,AZC013",
                "interval": 5,
                "timeout": 120,
            },
            "user",
            "Testing Alerts",
            {
                "name": "Testing Alerts",
                "zone_id": "AZZ540,AZC013",
                "interval": 5,
                "timeout": 120,
            },
        ),
    ],
)
async def test_form(
    input,
    step_id,
    title,
    data,
    hass,
):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}
    # assert result["title"] == title_1

    with patch(
        "custom_components.nws_alerts.async_setup", return_value=True
    ) as mock_setup, patch(
        "custom_components.nws_alerts.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], input
        )

        assert result2["type"] == "create_entry"
        assert result2["title"] == title
        assert result2["data"] == data

        await hass.async_block_till_done()
        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_setup_user(hass):
    """Test that the user setup works"""
    with patch("custom_components.nws_alerts.async_setup", return_value=True), patch(
        "custom_components.nws_alerts.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=CONFIG_DATA
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "NWS Alerts"
    assert result["data"] == CONFIG_DATA
