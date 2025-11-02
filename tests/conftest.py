"""Fixtures for tests."""

import pathlib
from unittest.mock import patch

from aioresponses import aioresponses
import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

API_URL = "https://api.weather.gov"
COUNT_URL = "https://api.weather.gov/alerts/active/count"
ZONE_URL = "https://api.weather.gov/alerts/active?zone=AZZ540,AZC013"
POINT_URL = "https://api.weather.gov/alerts/active?point=123,-456"


# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integration tests."""
    return


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with (
        patch("homeassistant.components.persistent_notification.async_create"),
        patch("homeassistant.components.persistent_notification.async_dismiss"),
    ):
        yield


@pytest.fixture
def aioclient_mock():
    """Fixture to mock aioclient calls."""
    with aioresponses() as mock_aiohttp:
        mock_headers = {"content-type": "content-type: application/geo+json"}
        mock_aiohttp.get(
            API_URL,
            status=200,
            headers=mock_headers,
            body={},
        )

        yield mock_aiohttp


@pytest.fixture
def mock_aioclient():
    """Fixture to mock aioclient calls."""
    with aioresponses() as m:
        yield m


def get_fixture_path(filename: str, integration: str | None = None) -> pathlib.Path:
    """Get path of fixture."""
    if integration is None and "/" in filename and not filename.startswith("helpers/"):
        integration, filename = filename.split("/", 1)

    if integration is None:
        return pathlib.Path(__file__).parent.joinpath("fixtures", filename)

    return pathlib.Path(__file__).parent.joinpath("components", integration, "fixtures", filename)


def load_fixture(filename: str, integration: str | None = None) -> str:
    """Load a fixture."""
    return get_fixture_path(filename, integration).read_text(encoding="utf8")


@pytest.fixture(name="mock_api")
def mock_api(mock_aioclient):
    """Load the charger data."""
    mock_aioclient.get(
        ZONE_URL,
        status=200,
        body=load_fixture("api.json"),
        repeat=True,
    )
    mock_aioclient.get(
        POINT_URL,
        status=200,
        body=load_fixture("api.json"),
        repeat=True,
    )
    mock_aioclient.get(
        COUNT_URL,
        status=200,
        body=load_fixture("count_reply.json"),
        repeat=True,
    )
    return mock_aioclient
