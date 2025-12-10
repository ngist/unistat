"""BinarySensor platform for UniStat integration."""

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import UnistatConfigEntry, UnistatControlCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: UnistatConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Initialize UniStat BinarySensors."""
    sensors = [
        UniStatBinarySensorEntity(
            coordinator=config_entry.runtime_data.coordinator, description=desc
        )
        for desc in UNISTAT_BINARY_SENSOR_TYPES
    ]

    async_add_entities(sensors)


UNISTAT_BINARY_SENSOR_TYPES = (
    BinarySensorEntityDescription(
        name="High Temp Alert",
        key="high_temp",
        device_class=BinarySensorDeviceClass.HEAT,
        translation_key="high_temp",
    ),
    BinarySensorEntityDescription(
        name="Low Temp Alert",
        key="low_temp",
        device_class=BinarySensorDeviceClass.COLD,
        translation_key="low_temp",
    ),
    BinarySensorEntityDescription(
        name="Update available",
        key="update_available",
        device_class=BinarySensorDeviceClass.UPDATE,
        translation_key="update_available",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        name="Control Deviation",
        key="control_deviation",
        device_class=BinarySensorDeviceClass.PROBLEM,
        translation_key="control_deviation",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        name="Control Failure",
        key="control_failure",
        device_class=BinarySensorDeviceClass.PROBLEM,
        translation_key="control_failure",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        name="Sensor Failure",
        key="sensor_failure",
        translation_key="sensor_failure",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        name="Health",
        key="health",
        translation_key="health",
        icon="mdi:heart-pulse",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


class UniStatBinarySensorEntity(
    CoordinatorEntity[UnistatControlCoordinator], BinarySensorEntity
):
    """unistat Binary Sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UnistatControlCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize unistat Sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{coordinator.location_key}-{description.key}".lower()

    @callback
    def _handle_coordinator_update(self):
        """Handle data update."""
        self._sensor_data = self.coordinator.data[self.entity_description.key]
        self.async_write_ha_state()
