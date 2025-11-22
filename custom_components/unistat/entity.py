"""Sensor platform for UniStat integration."""

import logging
from typing import List
import voluptuous as vol
from datetime import timedelta
from .climate import UniStatClimateEntity
from .const import (
    DOMAIN,
    CONF_AREA,
    CONF_TEMP_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_WIND_SPEED_ENTITY,
    CONF_HEATING_CALL_ENTITY,
    CONF_WIND_DIRECTION_ENTITY,
    CONF_SOLAR_FLUX_ENTITY,
    CONF_BOILER_OUTLET_TEMP_ENTITY,
    CONF_BOILER_UNIT_COST,
    CONF_BOILER_BTUH,
    CONF_BOILER_METER,
    CONF_BOILER_INLET_TEMP_ENTITY,
    CONF_OUTDOOR_SENSORS,
    SERVICE_ADD_ROOM,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_TEMPERATURE_UNIT,
    EVENT_HOMEASSISTANT_START,
    SERVICE_SAVE_PERSISTENT_STATES,
    SERVICE_RELOAD,
    UnitOfTemperature,
)
from homeassistant.core import (
    CoreState,
    Event,
    HomeAssistant,
    callback,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.util.hass_dict import HassKey

_LOGGER = logging.getLogger(__name__)

DATA_COMPONENT = HassKey(DOMAIN)
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up UniStatContoller entities."""
    component = hass.data[DATA_COMPONENT] = EntityComponent[UniStatControllerEntity](
        _LOGGER, DOMAIN, hass, SCAN_INTERVAL
    )
    await component.async_setup(config)

    component.async_register_entity_service(
        SERVICE_SAVE_PERSISTENT_STATES,
        None,
        "async_save_persistent_states",
    )
    component.async_register_entity_service(
        SERVICE_RELOAD,
        None,
        "async_reload",
    )
    component.async_register_entity_service(
        SERVICE_ADD_ROOM,
        vol.Schema({vol.Required("unistat_climate"): UniStatClimateEntity}),
        "async_add_room",
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Initialize UniStat config entry."""

    def format_entity_id(name: str):
        return name.lower().replace(" ", "_").replace("-", "_")

    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    _LOGGER.info("Configuring UniStat Controller")
    name = config_entry.data[CONF_NAME]
    entity_id = er.async_validate_entity_id(
        registry, format_entity_id(f"entity.{name}")
    )

    # Unpack settings
    outdoor_sensors = config_entry.data.get(CONF_OUTDOOR_SENSORS, {})
    boiler_settings = config_entry.data.get("boiler_conf", {})
    for key in ["temp_sensors", "energy_settings"]:
        boiler_settings.update(boiler_settings[key])
        del boiler_settings[key]

    async_add_entities(
        [
            UniStatControllerEntity(
                hass,
                unique_id=config_entry.entry_id,
                name=name,
                wrapped_entity_id=entity_id,
                temperature_unit=config_entry.data[CONF_TEMPERATURE_UNIT],
                outside_temp_entity_id=outdoor_sensors.get(CONF_TEMP_ENTITY, None),
                outside_humidity_entity_id=outdoor_sensors.get(
                    CONF_HUMIDITY_ENTITY, None
                ),
                wind_speed_entity_id=outdoor_sensors.get(CONF_WIND_SPEED_ENTITY, None),
                wind_direction_entity_id=outdoor_sensors.get(
                    CONF_WIND_DIRECTION_ENTITY, None
                ),
                solar_irradiance_entity_id=outdoor_sensors.get(
                    CONF_SOLAR_FLUX_ENTITY, None
                ),
                boiler_inlet_temp_entity_id=boiler_settings.get(
                    CONF_BOILER_INLET_TEMP_ENTITY, None
                ),
                boiler_outlet_temp_entity_id=boiler_settings.get(
                    CONF_BOILER_OUTLET_TEMP_ENTITY, None
                ),
                boiler_utility_meter_entity_id=boiler_settings.get(
                    CONF_BOILER_METER, None
                ),
                boiler_btuh=boiler_settings.get(CONF_BOILER_BTUH, None),
                boiler_unit_cost=boiler_settings.get(CONF_BOILER_UNIT_COST, None),
                boiler_common_areas=boiler_settings.get(CONF_AREA, None),
                boiler_heat_call_entity_ids=boiler_settings.get(
                    CONF_HEATING_CALL_ENTITY, None
                ),
            )
        ]
    )


class UniStatControllerEntity(RestoreEntity):
    """UniStat CLimate."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        unique_id: str,
        name: str,
        wrapped_entity_id: str,
        temperature_unit: UnitOfTemperature,
        outside_temp_entity_id: str | None = None,
        outside_humidity_entity_id: str | None = None,
        wind_speed_entity_id: str | None = None,
        wind_direction_entity_id: str | None = None,
        solar_irradiance_entity_id: str | None = None,
        boiler_inlet_temp_entity_id: str | None = None,
        boiler_outlet_temp_entity_id: str | None = None,
        boiler_utility_meter_entity_id: str | None = None,
        boiler_btuh: int | None = None,
        boiler_unit_cost: float | None = None,
        boiler_common_areas: List[str] | None = None,
        boiler_heat_call_entity_ids: List[str] | None = None,
    ) -> None:
        """Initialize UniStat Controller."""
        super().__init__()

        # Set builtin attributes
        self._wrapped_entity_id = wrapped_entity_id
        self._attr_name = name
        self._attr_unique_id = unique_id

        self._temperature_unit = temperature_unit
        self._outside_temp_entity_id = outside_temp_entity_id
        self._outside_humidity_entity_id = outside_humidity_entity_id
        self._wind_speed_entity_id = wind_speed_entity_id
        self._wind_direction_entity_id = wind_direction_entity_id
        self._solar_irradiance_entity_id = solar_irradiance_entity_id
        self._boiler_inlet_temp_entity_id = boiler_inlet_temp_entity_id
        self._boiler_outlet_temp_entity_id = boiler_outlet_temp_entity_id
        self._boiler_utility_meter_entity_id = boiler_utility_meter_entity_id
        self._boiler_btuh = boiler_btuh
        self._boiler_unit_cost = boiler_unit_cost
        self._boiler_common_areas = boiler_common_areas
        self._boiler_heat_call_entity_ids = boiler_heat_call_entity_ids

        self._unistat_entity_ids = []

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        @callback
        def _async_startup(_: Event | None = None) -> None:
            """Init on startup."""

            # TODO Fetch data from added entities

            # TODO set initial heating/cooling/humidity control states

        if self.hass.state is CoreState.running:
            _async_startup()
        else:
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _async_startup)

        # Check If we have an old state
        if (old_state := await self.async_get_last_state()) is not None:
            if old_state:
                pass
            # TODO Load old state
        else:
            await self.async_rebuild()

    async def async_add_room(self, unistat_climate: UniStatClimateEntity):
        self._unistat_entity_ids.add(unistat_climate)
        await self.async_rebuild()

    async def async_rebuild(self):
        raise NotImplementedError
