"""Define the Terabox entity."""

from urllib.parse import quote

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_BACKUP_LOCATION, DEFAULT_BACKUP_LOCATION, DOMAIN
from .coordinator import TeraboxDataUpdateCoordinator


class TeraboxEntity(CoordinatorEntity[TeraboxDataUpdateCoordinator]):
    """Defines a base Terabox entity."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Google Drive device."""
        backup_location = (
            self.coordinator.config_entry.data.get(CONF_BACKUP_LOCATION)
            or DEFAULT_BACKUP_LOCATION
        ).strip("/")
        path = quote(f"/{backup_location}", safe="")
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.coordinator.config_entry.unique_id))},
            name=self.coordinator.account_id,
            manufacturer="Terabox",
            model="Terabox Storage",
            configuration_url=f"https://www.terabox.com/main?category=all&path={path}",
            entry_type=DeviceEntryType.SERVICE,
        )
