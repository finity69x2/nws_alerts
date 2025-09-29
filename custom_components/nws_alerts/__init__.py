"""NWS Alerts."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_entries_for_config_entry, async_get

from .const import (
    CONF_GPS_LOC,
    CONF_INTERVAL,
    CONF_TIMEOUT,
    CONFIG_VERSION,
    COORDINATOR,
    DEFAULT_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    ISSUE_URL,
    PLATFORMS,
    VERSION,
)
from .coordinator import AlertsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Load the saved entities."""
    # Print startup message
    _LOGGER.info(
        "Version %s is starting, if you have any issues please report them here: %s",
        VERSION,
        ISSUE_URL,
    )
    hass.data.setdefault(DOMAIN, {})

    if config_entry.unique_id is not None:
        hass.config_entries.async_update_entry(config_entry, unique_id=None)

        ent_reg = async_get(hass)
        for entity in async_entries_for_config_entry(ent_reg, config_entry.entry_id):
            ent_reg.async_update_entity(entity.entity_id, new_unique_id=config_entry.entry_id)

    updated_config = config_entry.data.copy()

    # Strip spaces from manually entered GPS locations
    if CONF_GPS_LOC in updated_config:
        updated_config[CONF_GPS_LOC].replace(" ", "")

    if updated_config != config_entry.data:
        hass.config_entries.async_update_entry(config_entry, data=updated_config)

    config_entry.add_update_listener(update_listener)

    # Setup the data coordinator
    coordinator = AlertsDataUpdateCoordinator(
        hass,
        config_entry,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    hass.data[DOMAIN][config_entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle removal of an entry."""
    _LOGGER.debug("Attempting to unload entities from the %s integration", DOMAIN)

    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    if unload_ok:
        _LOGGER.debug("Successfully removed entities from the %s integration", DOMAIN)

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Update listener."""
    if config_entry.data == config_entry.options:
        _LOGGER.debug("No changes detected not reloading sensors.")
        return

    new_data = config_entry.options.copy()
    hass.config_entries.async_update_entry(
        entry=config_entry,
        data=new_data,
    )

    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate an old config entry."""
    version = config_entry.version

    # 1-> 2: Migration format
    if version == 1:
        _LOGGER.debug("Migrating from version %s", version)
        updated_config = config_entry.data.copy()

        if CONF_INTERVAL not in updated_config:
            updated_config[CONF_INTERVAL] = DEFAULT_INTERVAL
        if CONF_TIMEOUT not in updated_config:
            updated_config[CONF_TIMEOUT] = DEFAULT_TIMEOUT

    if updated_config != config_entry.data:
        hass.config_entries.async_update_entry(config_entry, data=updated_config)

        _LOGGER.debug("Migration to version %s complete", CONFIG_VERSION)

    return True
