"""Sensor platform for UltraStat integration."""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback


def format_name(name: str):
    return name.lower().replace(" ", "_").replace("-", "_")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Initialize UltraStat config entry."""
    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    entity_id = er.async_validate_entity_id(
        registry, "climate." + format_name(config_entry.data[CONF_NAME])
    )
    # TODO Optionally validate config entry options before creating entity
    name = config_entry.title
    unique_id = config_entry.entry_id

    async_add_entities([ultrastatClimateEntity(unique_id, name, entity_id)])


class ultrastatClimateEntity(ClimateEntity):
    """ultrastat CLimate."""

    def __init__(self, unique_id: str, name: str, wrapped_entity_id: str) -> None:
        """Initialize ultrastat Sensor."""
        super().__init__()
        self._wrapped_entity_id = wrapped_entity_id
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
        ]
