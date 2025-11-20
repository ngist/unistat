"""Sensor platform for UltraStat integration."""

from .const import CONF_AREA, CONF_HUMIDITY_ENTITY
from homeassistant.components.climate import (
    ClimateEntity,
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfTemperature, CONF_TEMPERATURE_UNIT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback


def format_entity_id(name: str):
    return name.lower().replace(" ", "_").replace("-", "_")


def gen_name_list(base_name, room_conf):
    return [f"{base_name} {room[CONF_AREA].rsplit('.', 1)[1]}" for room in room_conf]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Initialize UltraStat config entry."""
    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    names = gen_name_list(config_entry.data[CONF_NAME], config_entry.data["room_conf"])
    entity_ids = [format_entity_id(f"climate.{name}") for name in names]
    entity_ids = [er.async_validate_entity_id(registry, eid) for eid in entity_ids]
    unique_ids = [
        config_entry.entry_id + format_entity_id(r[CONF_AREA].rsplit(".", 1)[1])
        for r in config_entry.data["room_conf"]
    ]
    has_humidity = [CONF_HUMIDITY_ENTITY in r for r in config_entry.data["room_conf"]]
    temp_unit = [config_entry.data[CONF_TEMPERATURE_UNIT]] * len(entity_ids)
    print(temp_unit)
    zipped_args = zip(unique_ids, names, entity_ids, temp_unit, has_humidity)

    async_add_entities([UniStatClimateEntity(*za) for za in zipped_args])


class UniStatClimateEntity(ClimateEntity):
    """UniStat CLimate."""

    def __init__(
        self,
        unique_id: str,
        name: str,
        wrapped_entity_id: str,
        temp_unit: UnitOfTemperature,
        has_humidity: bool,
    ) -> None:
        """Initialize ultrastat Sensor."""
        super().__init__()
        self._wrapped_entity_id = wrapped_entity_id
        self._attr_name = name
        self._attr_unique_id = unique_id

        self._attr_temperature_unit = temp_unit
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_hvac_modes = (
            HVACMode.OFF,
            HVACMode.AUTO,
        )
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )

        if temp_unit == UnitOfTemperature.FAHRENHEIT:
            self._attr_max_temp = 85
            self._attr_min_temp = 60
            self._attr_target_temperature = 72
            self._attr_target_temperature_low = 71
            self._attr_target_temperature_high = 73
        else:
            self._attr_max_temp = 30
            self._attr_min_temp = 15
            self._attr_target_temperature_high = 24
            self._attr_target_temperature_low = 22
            self._attr_target_temperature = 23
        self._attr_target_temperature_step = 1

        if has_humidity:
            self._attr_target_humidity = 40
            self._attr_min_humidity = 20
            self._attr_max_humidity = 70
            self._attr_supported_features |= ClimateEntityFeature.TARGET_HUMIDITY
