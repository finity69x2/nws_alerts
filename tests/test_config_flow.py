"""Test for config flow"""

from unittest.mock import patch
import pytest
from homeassistant import config_entries, setup
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.nws_alerts.const import DOMAIN

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "steps,title,data",
    [
        (
            [
                {"next_step_id": "zone"},
                {
                    "name": "Testing Alerts",
                    "zone_id": "AZZ540,AZC013",
                    "interval": 5,
                    "timeout": 120,
                },
            ],
            "Testing Alerts",
            {
                "name": "Testing Alerts",
                "zone_id": "AZZ540,AZC013",
                "interval": 5,
                "timeout": 120,
            },
        ),
        (
            [
                {"next_step_id": "gps"},
                {"next_step_id": "gps_loc"},
                {
                    "name": "Testing Alerts",
                    "gps_loc": "123,-456",
                    "interval": 5,
                    "timeout": 120,
                },
            ],
            "Testing Alerts",
            {
                "name": "Testing Alerts",
                "gps_loc": "123,-456",
                "interval": 5,
                "timeout": 120,
            },
        ),
    ],
)
async def test_form_zone(steps, title, data, hass: HomeAssistant, mocker):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    mocker.patch(
        "custom_components.nws_alerts.config_flow._get_zone_list",
        return_value=None,
    )
    mock_setup_entry = mocker.patch(
        "custom_components.nws_alerts.async_setup_entry",
        return_value=True,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    for index, step in enumerate(steps):
        if index == (len(steps) - 1):
            assert result["type"] == FlowResultType.FORM
        else:
            assert result["type"] == FlowResultType.MENU

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], step
        )
        await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == title
    assert result["data"] == data

    assert len(mock_setup_entry.mock_calls) == 1
