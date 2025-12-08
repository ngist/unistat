"""Config flow for the UniStat integration."""

from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN
from homeassistant.components.input_number import DOMAIN as INPUT_NUMBER_DOMAIN
from homeassistant.components.utility_meter import DOMAIN as UTILITY_METER_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_TEMPERATURE_UNIT,
    UnitOfTemperature,
    UnitOfPower,
)
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import section

from .const import (
    CONF_ADJACENCY,
    CONF_AREAS,
    CONF_CONTROLS,
    CONF_APPLIANCE_TYPE,
    CONF_CENTRAL_APPLIANCE,
    CONF_WEATHER_ENTITY,
    CONF_GAS_PRICE_ENTITY,
    CONF_ELECTRIC_PRICE_ENTITY,
    CONF_HEATING_POWER,
    CONF_COOLING_POWER,
    CONF_APPLIANCE_METER,
    CONF_CONTROL_MODE,
    CONF_HUMIDITY_ENTITY,
    CONF_SOLAR_FLUX_ENTITY,
    CONF_TEMP_ENTITY,
    CONF_WIND_DIRECTION_ENTITY,
    CONF_WIND_SPEED_ENTITY,
    CONF_SEER_RATING,
    CONF_SEER_STANDARD,
    CONF_HSPF_RATING,
    CONF_HSPF_STANDARD,
    CONF_EFFICIENCY,
    CONF_BOILER_INLET_TEMP_ENTITY,
    CONF_BOILER_OUTLET_TEMP_ENTITY,
    SWITCH_APPLIANCE_TYPES,
    CLIMATE_APPLIANCE_TYPES,
    CONF_WEATHER_STATION,
    DOMAIN,
    ControlMode,
    ControlApplianceType,
    CentralApplianceType,
)

_MAIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
        vol.Required(CONF_AREAS): selector.AreaSelector(
            selector.AreaSelectorConfig(multiple=True)
        ),
        vol.Required(CONF_CONTROLS): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=[SWITCH_DOMAIN, CLIMATE_DOMAIN], multiple=True
            )
        ),
        vol.Required(CONF_WEATHER_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=WEATHER_DOMAIN,
            )
        ),
        vol.Required(
            CONF_CONTROL_MODE,
            default=ControlMode.COMFORT,
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=list(ControlMode),
                mode=selector.SelectSelectorMode.DROPDOWN,
            ),
        ),
        vol.Required(
            CONF_TEMPERATURE_UNIT,
            default=UnitOfTemperature.FAHRENHEIT,
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS],
                mode=selector.SelectSelectorMode.DROPDOWN,
            ),
        ),
        vol.Optional(
            CONF_GAS_PRICE_ENTITY,
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=[SENSOR_DOMAIN, INPUT_NUMBER_DOMAIN],
                # device_class=[SensorDeviceClass.MONETARY, None],
            )
        ),
        vol.Optional(
            CONF_ELECTRIC_PRICE_ENTITY,
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                # device_class=[SensorDeviceClass.MONETARY, None],
            )
        ),
        vol.Required(CONF_ADJACENCY, default=True): bool,
        vol.Required(CONF_WEATHER_STATION, default=False): bool,
    }
)

_WEATHER_STATION_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_TEMP_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=SensorDeviceClass.TEMPERATURE,
            )
        ),
        vol.Optional(CONF_HUMIDITY_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=SensorDeviceClass.HUMIDITY,
            )
        ),
        vol.Optional(CONF_WIND_SPEED_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=SensorDeviceClass.WIND_SPEED,
            )
        ),
        vol.Optional(CONF_WIND_DIRECTION_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=SensorDeviceClass.WIND_DIRECTION,
            )
        ),
        vol.Optional(CONF_SOLAR_FLUX_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=SensorDeviceClass.IRRADIANCE,
            )
        ),
    }
)

_ROOM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TEMP_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=SensorDeviceClass.TEMPERATURE,
            )
        ),
        vol.Optional(CONF_HUMIDITY_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=SensorDeviceClass.HUMIDITY,
            )
        ),
    }
)

_NAME_SCHEMA = {
    vol.Required(CONF_NAME): selector.TextSelector(),
}

_HEATING_SCHEMA = {
    vol.Required(CONF_HEATING_POWER): selector.NumberSelector(
        {
            "min": 0,
            "mode": selector.NumberSelectorMode.BOX,
        }
    ),
}

_COOLING_SCHEMA = {
    vol.Required(CONF_COOLING_POWER): selector.NumberSelector(
        {
            "min": 0,
            "mode": selector.NumberSelectorMode.BOX,
        }
    ),
}

_POWER_UNIT_SCHEMA = {
    vol.Required(
        CONF_UNIT_OF_MEASUREMENT,
        default=UnitOfPower.BTU_PER_HOUR,
    ): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[UnitOfPower.BTU_PER_HOUR, UnitOfPower.KILO_WATT, UnitOfPower.WATT],
            mode=selector.SelectSelectorMode.DROPDOWN,
        ),
    ),
}

_METER_SCHEMA = {
    vol.Optional(CONF_APPLIANCE_METER): selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=UTILITY_METER_DOMAIN,
        )
    ),
}

_SEER_SCHEMA = {
    vol.Optional(CONF_SEER_RATING, default=15): selector.NumberSelector(
        {
            "min": 10,
            "max": 30,
            "mode": selector.NumberSelectorMode.BOX,
        }
    ),
    vol.Required(
        CONF_SEER_STANDARD,
        default="SEER",
    ): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=["SEER", "SEER2"],
            mode=selector.SelectSelectorMode.DROPDOWN,
        ),
    ),
}

_HSPF_SCHEMA = {
    vol.Optional(CONF_HSPF_RATING, default=15): selector.NumberSelector(
        {
            "min": 5,
            "max": 15,
            "mode": selector.NumberSelectorMode.BOX,
        }
    ),
    vol.Required(
        CONF_HSPF_STANDARD,
        default="HSPF",
    ): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=["HSPF", "HSPF2"],
            mode=selector.SelectSelectorMode.DROPDOWN,
        ),
    ),
}

_FURNACE_SCHEMA = (
    vol.Schema(_NAME_SCHEMA)
    .extend(_HEATING_SCHEMA)
    .extend(_POWER_UNIT_SCHEMA)
    .extend(_METER_SCHEMA)
    .extend(
        {
            vol.Required(CONF_EFFICIENCY, default=80): selector.NumberSelector(
                {
                    "min": 0,
                    "max": 100,
                    CONF_UNIT_OF_MEASUREMENT: "%",
                    "mode": selector.NumberSelectorMode.BOX,
                }
            ),
        }
    )
)

_BOILER_SCHEMA = _FURNACE_SCHEMA.extend(
    {
        vol.Optional(CONF_BOILER_INLET_TEMP_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=SensorDeviceClass.TEMPERATURE,
            )
        ),
        vol.Optional(CONF_BOILER_OUTLET_TEMP_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=SensorDeviceClass.TEMPERATURE,
            )
        ),
    }
)

_COMPRESSOR_SCHEMA = (
    vol.Schema(_NAME_SCHEMA)
    .extend(_COOLING_SCHEMA)
    .extend(_POWER_UNIT_SCHEMA)
    .extend(_SEER_SCHEMA)
    .extend(_METER_SCHEMA)
)

_HEATPUMP_COMP_SCHEMA = (
    vol.Schema(_NAME_SCHEMA)
    .extend(_COOLING_SCHEMA)
    .extend(_HEATING_SCHEMA)
    .extend(_POWER_UNIT_SCHEMA)
    .extend(_SEER_SCHEMA)
    .extend(_HSPF_SCHEMA)
    .extend(_METER_SCHEMA)
)

_WINDOW_AC_SCHEMA = (
    vol.Schema(_COOLING_SCHEMA)
    .extend(_POWER_UNIT_SCHEMA)
    .extend(_SEER_SCHEMA)
    .extend(_METER_SCHEMA)
)
_WINDOW_HP_SCHEMA = (
    vol.Schema(_COOLING_SCHEMA)
    .extend(_HEATING_SCHEMA)
    .extend(_POWER_UNIT_SCHEMA)
    .extend(_SEER_SCHEMA)
    .extend(_HSPF_SCHEMA)
    .extend(_METER_SCHEMA)
)
_SPACE_HEATER_SCHEMA = (
    vol.Schema(_HEATING_SCHEMA).extend(_POWER_UNIT_SCHEMA).extend(_METER_SCHEMA)
)


def _gen_room_appliance_schema(entity_id: str) -> vol.Schema:
    """Returns schema for room appliance the filters appliance types based on entity domain."""
    type_options = {
        SWITCH_DOMAIN: SWITCH_APPLIANCE_TYPES,
        CLIMATE_DOMAIN: CLIMATE_APPLIANCE_TYPES,
    }
    domain = entity_id.split(".", maxsplit=1)[0]
    return vol.Schema(
        {
            vol.Required(CONF_APPLIANCE_TYPE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=type_options[domain],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                ),
            ),
            vol.Required(CONF_AREAS): selector.AreaSelector(
                selector.AreaSelectorConfig(multiple=True)
            ),
        }
    )


_APPLIANCE_SCHEMA_MAP = {
    ControlApplianceType.WindowAC: _WINDOW_AC_SCHEMA,
    ControlApplianceType.WindowHeatpump: _WINDOW_HP_SCHEMA,
    ControlApplianceType.SpaceHeater: _SPACE_HEATER_SCHEMA,
}

_A2C_MAP = {
    ControlApplianceType.BoilerZoneValve: CentralApplianceType.HydroBoiler,
    ControlApplianceType.ThermoStaticRadiatorValve: CentralApplianceType.HydroBoiler,
    ControlApplianceType.HVACCoolCall: CentralApplianceType.AcCompressor,
    ControlApplianceType.HVACHeatCall: CentralApplianceType.HvacFurnace,
    ControlApplianceType.HVACThermostat: CentralApplianceType.HeatpumpCompressor,
    ControlApplianceType.HeatpumpFanUnit: CentralApplianceType.HeatpumpCompressor,
}

_CENTRAL_APPLIANCE_MAP = {
    CentralApplianceType.HydroBoiler: _BOILER_SCHEMA,
    CentralApplianceType.AcCompressor: _COMPRESSOR_SCHEMA,
    CentralApplianceType.HvacFurnace: _FURNACE_SCHEMA,
    CentralApplianceType.HeatpumpCompressor: _HEATPUMP_COMP_SCHEMA,
}


def _gen_adjacency_schema(rooms) -> tuple[vol.Schema, dict[str, str]]:
    """Generates an adjacency matrix schema based on the number of rooms, and associated placeholder data."""
    locations = ["Outside", *rooms]
    placeholders = {f"room{i}": r for i, r in enumerate(locations)}

    schema = {}
    for i, _ in enumerate(locations):
        if len(locations) - 1 != i:
            sub_schema = {}
            for x in locations[i + 1 :]:
                sub_schema[vol.Required(x, default=True)] = bool
            schema[vol.Required(f"room{i}")] = section(
                vol.Schema(sub_schema), options=None
            )

    schema = vol.Schema(schema)

    return schema, placeholders


def _gen_select_central_schema(central_appliances: list[str]) -> vol.Schema:
    """Dynamically generate a dropdown selecto for central appliances based on ones that have already been added."""
    central_appliances = ["New", *central_appliances]
    return vol.Schema(
        {
            vol.Required(
                CONF_CENTRAL_APPLIANCE, default="New"
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=central_appliances,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                ),
            ),
        }
    )


def parse_adjacency(
    user_input: dict[str, dict[str, bool]], rooms: list[str]
) -> list[list[bool]]:
    """Converts the user input to an array like list of lists."""
    dim = len(user_input.keys()) + 1
    adj_mat = [[False] * dim for i in range(dim)]
    room2idx = {r: i for i, r in enumerate(rooms)}
    for k in user_input:
        i = int(k.replace("room", ""))
        for r in user_input[k]:
            adj_mat[i][room2idx[r] + 1] = 1 if user_input[k][r] else 0
    return adj_mat


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config or options flow for UniStat."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Invoked when a user initiates a flow via the user interface."""
        if user_input is not None:
            self.data = user_input
            self.data["room_sensors"] = {}
            self.data["central_appliances"] = {}
            self.data["room_appliances"] = {}
            # Return the form of the next step.
            if self.data[CONF_ADJACENCY]:
                return await self.async_step_adjacency()
            elif self.data[CONF_WEATHER_STATION]:
                return await self.async_step_weather_station()
            return await self.async_step_room_sensors()

        return self.async_show_form(step_id="user", data_schema=_MAIN_SCHEMA)

    async def async_step_adjacency(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure room adjacency matrix."""
        if user_input is not None:
            # Input is valid, set data.
            self.data["adjacency"] = parse_adjacency(
                user_input=user_input, rooms=self.data[CONF_AREAS]
            )
            # Return the form of the next step.
            if self.data[CONF_WEATHER_STATION]:
                return await self.async_step_weather_station()

            return await self.async_step_room_sensors()

        schema, placeholders = _gen_adjacency_schema(self.data[CONF_AREAS])

        return self.async_show_form(
            step_id="adjacency",
            data_schema=schema,
            description_placeholders=placeholders,
        )

    async def async_step_weather_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure local weather station sensors."""
        if user_input is not None:
            # Input is valid, set data.
            self.data["weather_station"] = user_input
            # Return the form of the next step.
            return await self.async_step_room_sensors()

        return self.async_show_form(
            step_id="weather_station",
            data_schema=_WEATHER_STATION_SCHEMA,
        )

    async def async_step_room_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Captures configuration of thermal sensors in each room."""

        room_index = len(self.data["room_sensors"])
        this_room = self.data[CONF_AREAS][room_index]

        if user_input is not None:
            # Input is valid, set data.
            self.data["room_sensors"][this_room] = user_input

            if room_index + 1 == len(self.data[CONF_AREAS]):
                # Room sensors done move onto appliances
                return await self.async_step_room_appliance_1()

            # Return the form of the next room.
            return await self.async_step_room_sensors()

        return self.async_show_form(
            step_id="room_sensors",
            data_schema=_ROOM_SCHEMA,
            description_placeholders={
                "room": this_room,
            },
        )

    async def async_step_room_appliance_1(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Captures configuration of a room appliance."""

        self.room_appliance_index = len(self.data["room_appliances"].keys())
        self.this_appliance = self.data[CONF_CONTROLS][self.room_appliance_index]

        if user_input is not None:
            # Input is valid, set data.
            self.data["room_appliances"][self.this_appliance] = user_input
            self.appliance_type = user_input[CONF_APPLIANCE_TYPE]
            return await self.async_step_room_appliance_2()

        return self.async_show_form(
            step_id="room_appliance_1",
            data_schema=_gen_room_appliance_schema(self.this_appliance),
            description_placeholders={
                "appliance": self.this_appliance,
            },
        )

    async def async_step_room_appliance_2(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Captures configuration of thermal controls in each room."""

        schema = (
            _APPLIANCE_SCHEMA_MAP[self.appliance_type]
            if self.appliance_type in _APPLIANCE_SCHEMA_MAP
            else _gen_select_central_schema(
                list(self.data["central_appliances"].keys())
            )
        )

        if user_input is not None:
            # Input is valid, set data.
            if (
                CONF_CENTRAL_APPLIANCE in user_input
                and user_input[CONF_CENTRAL_APPLIANCE] == "New"
            ):
                return await self.async_step_central_appliance()

            self.data["room_appliances"][self.this_appliance].update(user_input)

            if self.room_appliance_index + 1 == len(self.data[CONF_CONTROLS]):
                return self.async_create_entry(
                    title=self.data[CONF_NAME], data=self.data
                )

            # Return the form of the next step.
            return await self.async_step_room_appliance_1()

        return self.async_show_form(
            step_id="room_appliance_2",
            data_schema=schema,
            description_placeholders={
                "appliance": self.this_appliance,
            },
        )

    async def async_step_central_appliance(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Captures configuration of thermal controls in each room."""

        if user_input is not None:
            # Input is valid, set data.
            self.data["room_appliances"][self.this_appliance][
                CONF_CENTRAL_APPLIANCE
            ] = user_input[CONF_NAME]
            user_input["appliance_type"] = _A2C_MAP[self.appliance_type]
            self.data["central_appliances"][user_input[CONF_NAME]] = user_input

            if self.room_appliance_index + 1 == len(self.data[CONF_CONTROLS]):
                return self.async_create_entry(
                    title=self.data[CONF_NAME], data=self.data
                )

            # Return the form of the next step.
            return await self.async_step_room_appliance_1()

        return self.async_show_form(
            step_id="central_appliance",
            data_schema=_CENTRAL_APPLIANCE_MAP[_A2C_MAP[self.appliance_type]],
            description_placeholders={
                "appliance": self.this_appliance,
                "central_appliance": str(_A2C_MAP[self.appliance_type]),
            },
        )
