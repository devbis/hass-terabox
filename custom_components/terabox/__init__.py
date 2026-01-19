"""The Terabox integration."""

from __future__ import annotations

import logging
from collections.abc import Callable

# from aioterabox.exceptions import TeraboxApiError
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant

# from homeassistant.exceptions import ConfigEntryNotReady
# from homeassistant.helpers import instance_id
# from homeassistant.helpers.aiohttp_client import async_get_clientsession
# from homeassistant.helpers.config_entry_oauth2_flow import (
#     OAuth2Session,
#     async_get_config_entry_implementation,
# )
from homeassistant.util.hass_dict import HassKey

from .api import TeraboxClient
from .const import CONF_BACKUP_LOCATION, DOMAIN
from .coordinator import TeraboxConfigEntry, TeraboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

DATA_BACKUP_AGENT_LISTENERS: HassKey[list[Callable[[], None]]] = HassKey(
    f"{DOMAIN}.backup_agent_listeners"
)

PLATFORMS = (Platform.SENSOR,)


async def async_setup_entry(hass: HomeAssistant, entry: TeraboxConfigEntry) -> bool:
    """Set up Terabox from a config entry."""

    client = TeraboxClient(
        hass,
        config_entry=entry,
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        cookies=entry.options if entry.options else None,
    )
    await client.login()

    coordinator = TeraboxDataUpdateCoordinator(
        hass,
        client=client,
        backup_location=entry.data[CONF_BACKUP_LOCATION],
        config_entry=entry,
    )
    entry.runtime_data = coordinator
    # Query the device for the first time and initialise coordinator.data
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # entry.async_on_unload(entry.add_update_listener(update_listener))

    def async_notify_backup_listeners() -> None:
        for listener in hass.data.get(DATA_BACKUP_AGENT_LISTENERS, []):
            listener()

    entry.async_on_unload(entry.async_on_state_change(async_notify_backup_listeners))

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: TeraboxConfigEntry
) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return True
