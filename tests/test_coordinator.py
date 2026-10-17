"""Test coordinator error handling (issue #147)."""

import json
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nws_alerts.const import COORDINATOR, DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from tests.conftest import ZONE_URL, load_fixture
from tests.const import CONFIG_DATA

pytestmark = pytest.mark.asyncio

TRACKER = "device_tracker.test"
CONFIG_DATA_TRACKER = {"name": "NWS Alerts", "tracker": TRACKER}

PROBLEM_JSON = {
    "correlationId": "abc123",
    "title": "Unexpected Problem",
    "type": "https://api.weather.gov/problems/UnexpectedProblem",
    "status": 500,
    "detail": "An unexpected problem has occurred.",
}


async def _setup(hass, data):
    """Set the entry up against the repeating api.json mock and return its coordinator."""
    entry = MockConfigEntry(domain=DOMAIN, title="NWS Alerts", data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    assert coordinator.data["state"] == 2
    return coordinator


def _alerts_state(hass):
    entity_id = next(
        eid for eid in hass.states.async_entity_ids(SENSOR_DOMAIN) if eid.endswith("_alerts")
    )
    return hass.states.get(entity_id).state


async def _refresh_and_assert_failed(hass, coordinator, message):
    """Refresh, then check the old data survived and the sensor went unavailable."""
    before = dict(coordinator.data)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success is False
    assert message in str(coordinator.last_exception)
    assert coordinator.data == before
    assert _alerts_state(hass) == "unavailable"


@pytest.mark.parametrize(
    "body",
    [
        PROBLEM_JSON,
        [],
        {"type": "FeatureCollection"},
        {"type": "FeatureCollection", "features": None},
    ],
    ids=["problem_json_200", "non_object", "no_features", "features_not_list"],
)
async def test_bad_200_body_fails_update(hass, mock_api, body):
    """A 200 without a FeatureCollection is a failed update, not zero alerts."""
    coordinator = await _setup(hass, CONFIG_DATA)
    mock_api.clear()
    mock_api.get(ZONE_URL, status=200, body=json.dumps(body))
    await _refresh_and_assert_failed(hass, coordinator, "Unexpected NWS response")


async def test_attribute_error_fails_update(hass, mock_api):
    """An AttributeError no longer turns into zero alerts with a fresh timestamp."""
    coordinator = await _setup(hass, CONFIG_DATA)
    with patch.object(coordinator, "update_alerts", side_effect=AttributeError("boom")):
        await _refresh_and_assert_failed(hass, coordinator, "boom")


async def test_empty_features_is_zero_alerts(hass, mock_api):
    """An explicit empty features list is a confirmed zero-alert result."""
    coordinator = await _setup(hass, CONFIG_DATA)
    mock_api.clear()
    mock_api.get(ZONE_URL, status=200, body='{"type": "FeatureCollection", "features": []}')
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success is True
    assert coordinator.data["state"] == 0
    assert coordinator.data["alerts"] == []
    assert _alerts_state(hass) == "0"


async def test_malformed_feature_is_skipped(hass, mock_api, caplog):
    """One feature the parser can't read is dropped; the rest of the list still publishes."""
    coordinator = await _setup(hass, CONFIG_DATA)
    good = json.loads(load_fixture("api.json"))
    body = {
        "type": "FeatureCollection",
        "features": [
            good["features"][0],
            {"id": "https://api.weather.gov/alerts/bad"},
            good["features"][1],
        ],
    }
    mock_api.clear()
    mock_api.get(ZONE_URL, status=200, body=json.dumps(body))
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success is True
    assert coordinator.data["state"] == 2
    assert {a["URL"] for a in coordinator.data["alerts"]} == {f["id"] for f in good["features"]}
    assert _alerts_state(hass) == "2"
    assert "Skipping this alert" in caplog.text


async def test_tracker_without_coordinates_fails_update(hass, mock_api):
    """A tracker that loses its GPS attributes fails the update instead of reporting zero alerts."""
    hass.states.async_set(
        TRACKER, "home", {"source_type": "gps", "latitude": 123, "longitude": -456}
    )
    coordinator = await _setup(hass, CONFIG_DATA_TRACKER)
    hass.states.async_set(TRACKER, "not_home", {"source_type": "gps"})
    await _refresh_and_assert_failed(hass, coordinator, "no GPS coordinates")
