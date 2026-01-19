"""Support for Terabox sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import (
    SensorData,
    TeraboxConfigEntry,
    TeraboxDataUpdateCoordinator,
)
from .entity import TeraboxEntity

# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class TeraboxSensorEntityDescription(SensorEntityDescription):
    """Describes Terabox sensor entity."""

    exists_fn: Callable[[SensorData], bool] = lambda _: True
    value_fn: Callable[[SensorData], StateType]


SENSORS: tuple[TeraboxSensorEntityDescription, ...] = (
    TeraboxSensorEntityDescription(
        key="storage_total",
        translation_key="storage_total",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=0,
        device_class=SensorDeviceClass.DATA_SIZE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.storage_quota.limit,
        exists_fn=lambda data: data.storage_quota.limit is not None,
    ),
    TeraboxSensorEntityDescription(
        key="storage_used",
        translation_key="storage_used",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=0,
        device_class=SensorDeviceClass.DATA_SIZE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.storage_quota.usage,
    ),
    TeraboxSensorEntityDescription(
        key="backups_size",
        translation_key="backups_size",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.MEBIBYTES,
        suggested_display_precision=0,
        device_class=SensorDeviceClass.DATA_SIZE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.all_backups_size,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeraboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Terabox sensor based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        TeraboxSensorEntity(coordinator, description)
        for description in SENSORS
        if description.exists_fn(coordinator.data)
    )


class TeraboxSensorEntity(TeraboxEntity, SensorEntity):
    """Defines a Terabox sensor entity."""

    entity_description: TeraboxSensorEntityDescription

    def __init__(
        self,
        coordinator: TeraboxDataUpdateCoordinator,
        description: TeraboxSensorEntityDescription,
    ) -> None:
        """Initialize a Terabox sensor entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
