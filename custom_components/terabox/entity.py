"""Define the Terabox entity."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DRIVE_FOLDER_PREFIX
from .coordinator import TeraboxDataUpdateCoordinator


class TeraboxEntity(CoordinatorEntity[TeraboxDataUpdateCoordinator]):
    """Defines a base Terabox entity."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Google Drive device."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.coordinator.config_entry.unique_id))},
            name=self.coordinator.account_id,
            manufacturer="Terabox",
            model="Terabox Storage",
            configuration_url=f"https://www.terabox.com/main?category=all&path=%2F{DRIVE_FOLDER_PREFIX}",
            entry_type=DeviceEntryType.SERVICE,
        )
