"""Sensor platform for UniStat integration."""

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorEntityDescription,
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
    """Initialize UniStat Sensors."""
    sensors = [
        UnistatSensorEntity(
            unique_id_base=config_entry.entry_id,
            coordinator=config_entry.runtime_data.coordinator_control,
            description=desc,
        )
        for desc in UNISTAT_SENSOR_TYPES
    ]

    async_add_entities(sensors)


UNISTAT_SENSOR_TYPES = (
    SensorEntityDescription(
        name="Control Error",
        key="control_error",
        translation_key="control_error",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        name="Daily Control Error",
        key="daily_control_error",
        translation_key="daily_control_error",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        name="Daily Cost",
        key="daily_cost",
        device_class=SensorDeviceClass.MONETARY,
        translation_key="daily_cost",
    ),
    SensorEntityDescription(
        name="Most Demanding Room",
        key="most_demanding_room",
        translation_key="most_demanding_room",
    ),
)


class UnistatSensorEntity(CoordinatorEntity[UnistatControlCoordinator], SensorEntity):
    """Unistat Sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        unique_id_base: str,
        coordinator: UnistatControlCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize unistat Sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{unique_id_base}-{description.key}".lower()

    @callback
    def _handle_coordinator_update(self):
        """Handle data update."""
        self._sensor_data = self.coordinator.data[self.entity_description.key]
        self.async_write_ha_state()
