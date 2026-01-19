"""DataUpdateCoordinator for Terabox."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aioterabox.exceptions import TeraboxApiError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import StorageQuotaData, TeraboxClient
from .const import DOMAIN, SCAN_INTERVAL

type TeraboxConfigEntry = ConfigEntry[TeraboxDataUpdateCoordinator]

_LOGGER = logging.getLogger(__name__)


@dataclass
class SensorData:
    """Class to represent sensor data."""

    storage_quota: StorageQuotaData
    all_backups_size: int


class TeraboxDataUpdateCoordinator(DataUpdateCoordinator[SensorData]):
    """Class to manage fetching Terabox data from single endpoint."""

    client: TeraboxClient
    config_entry: TeraboxConfigEntry
    email_address: str
    backup_folder_id: str

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        client: TeraboxClient,
        backup_location: str,
        config_entry: TeraboxConfigEntry,
    ) -> None:
        """Initialize Terabox data updater."""
        self.client = client
        self.account_id = client.account_id
        self.backup_location = backup_location

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_setup(self) -> None:
        """Do initialization logic."""
        await self.client.login()

    async def _async_update_data(self) -> SensorData:
        """Fetch data from Terabox."""
        try:
            storage_quota = await self.client.async_get_storage_quota()
            all_backups_size = await self.client.async_get_size_of_all_backups()
            return SensorData(
                storage_quota=storage_quota,
                all_backups_size=all_backups_size,
            )
        except TeraboxApiError as error:
            _LOGGER.exception('Failed to update data from Terabox API')
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_response_terabox_error",
                translation_placeholders={"error": str(error)},
            ) from error
