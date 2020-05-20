""" NWS Alerts """
import logging
from homeassistant import config_entries
from .const import (
    DOMAIN,
    VERSION,
    ISSUE_URL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config_entry):
    """Set up this component using YAML."""
    if config_entry.get(DOMAIN) is None:
        # We get here if the integration is set up using config flow
        return True

    # Print startup message
    _LOGGER.info('Version %s is starting, if you have any issues please report'
                 ' them here: %s', VERSION, ISSUE_URL)

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
        )
    )

    return True


async def async_setup_entry(hass, config_entry):
    """Load the saved entities."""
    # Print startup message
    _LOGGER.info('Version %s is starting, if you have any issues please report'
                 ' them here: %s', VERSION, ISSUE_URL)
    config_entry.options = config_entry.data
    config_entry.add_update_listener(update_listener)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )

    return True


async def async_unload_entry(hass, config_entry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry,
                                                             "sensor")
        _LOGGER.info(
            "Successfully removed sensor from the " + DOMAIN + " integration"
        )
    except ValueError:
        pass
    return True


async def update_listener(hass, entry):
    """Update listener."""
    entry.data = entry.options
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry,
                                                                     "sensor"))
