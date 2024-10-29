"""Test NWS Alerts Sensors"""

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nws_alerts.const import DOMAIN
from tests.const import CONFIG_DATA, CONFIG_DATA_2, CONFIG_DATA_BAD

pytestmark = pytest.mark.asyncio

NWS_SENSOR = "sensor.nws_alerts"
NWS_SENSOR_2 = "sensor.nws_alerts_yaml"


async def test_sensor(hass, mock_api):
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
    assert state.state == "2"
    assert state.attributes["alerts"] == [
        {
            "event": "Excessive Heat Warning",
            "id": "7681487b-41c6-0308-1a00-3cade72982c1",
            "url": "https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.505a7220d91b00eb1d75a3fb4f339f825496a522.004.1",
            "headline": "EXCESSIVE HEAT WARNING REMAINS IN EFFECT FROM 10 AM FRIDAY TO 8 PM MST SATURDAY",
            "type": "Update",
            "status": "Actual",
            "severity": "Severe",
            "certainty": "Likely",
            "onset": "2024-07-19T10:00:00-07:00",
            "expires": "2024-07-19T03:00:00-07:00",
            "description": "* WHAT...Dangerously hot conditions. Afternoon temperatures 112 to\n116 expected. Major Heat Risk. Overexposure can cause heat cramps\nand heat exhaustion to develop and, without intervention, can lead\nto heat stroke.\n\n* WHERE...The Northwest Valley of the Phoenix Metro Area, The East\nValley of the Phoenix Metro Area, Buckeye/Avondale, Deer Valley,\nCentral Phoenix, North Phoenix/Glendale, Scottsdale/Paradise\nValley, South Mountain/Ahwatukee, and Southeast Valley/Queen Creek.\n\n* WHEN...From 10 AM Friday to 8 PM MST Saturday.\n\n* IMPACTS...Heat related illnesses increase significantly during\nextreme heat events.\n\n* ADDITIONAL DETAILS...In Maricopa County, call 2-1-1 to find a free\ncooling center, transportation, water, and more.\nhttps://www.maricopa.gov/heat",
            "instruction": "An Excessive Heat Warning means that a period of very hot\ntemperatures, even by local standards, will occur. Actions should be\ntaken to lessen the impact of the extreme heat.\n\nTake extra precautions if you work or spend time outside. When\npossible, reschedule strenuous activities to early morning or\nevening. Know the signs and symptoms of heat exhaustion and heat\nstroke. Wear lightweight and loose-fitting clothing when possible\nand drink plenty of water.\n\nTo reduce risk during outdoor work, the Occupational Safety and\nHealth Administration recommends scheduling frequent rest breaks in\nshaded or air conditioned environments. Anyone overcome by heat\nshould be moved to a cool and shaded location. Heat stroke is an\nemergency! Call 9 1 1.\n\nPublic cooling shelters are available in some areas. Consult county\nofficials for more details.",
        },
        {
            "event": "Air Quality Alert",
            "id": "cbc5f830-921d-10c7-b447-e9bc1b744965",
            "url": "https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.32b8fe5b1e8094248fdbb7a32619581ec4e1df14.001.1",
            "headline": "OZONE HIGH POLLUTION ADVISORY FOR MARICOPA COUNTY INCLUDING THE PHOENIX METRO AREA THROUGH FRIDAY",
            "type": "Alert",
            "status": "Actual",
            "severity": "Unknown",
            "certainty": "Unknown",
            "onset": "2024-07-18T08:13:00-07:00",
            "expires": "2024-07-19T21:00:00-07:00",
            "description": "AQAPSR\n\nThe Arizona Department of Environmental Quality (ADEQ) has issued an\nOzone High Pollution Advisory for the Phoenix Metro Area through\nFriday.\n\nThis means that forecast weather conditions combined with existing\nozone levels are expected to result in local maximum 8-hour ozone\nconcentrations that pose a health risk. Adverse health effects\nincrease as air quality deteriorates.\n\nOzone is an air contaminant which can cause breathing difficulties\nfor children, older adults, as well as persons with respiratory\nproblems. A decrease in physical activity is recommended.\n\nYou are urged to car pool, telecommute or use mass transit.\nThe use of gasoline-powered equipment should be reduced or done late\nin the day.\n\nFor details on this High Pollution Advisory, visit the ADEQ internet\nsite at www.azdeq.gov/forecast/phoenix or call 602-771-2300.",
            "instruction": None,
        },
    ]
    assert state.attributes["alerts"][0]["id"] == "7681487b-41c6-0308-1a00-3cade72982c1"
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
