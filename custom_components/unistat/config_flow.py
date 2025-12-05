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

MAIN_SCHEMA = vol.Schema(
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

WEATHER_STATION_SCHEMA = vol.Schema(
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

ROOM_SCHEMA = vol.Schema(
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

NAME_SCHEMA = {
    vol.Required(CONF_NAME): selector.TextSelector(),
}

HEATING_SCHEMA = {
    vol.Required(CONF_HEATING_POWER): selector.NumberSelector(
        {
            "min": 0,
            "mode": selector.NumberSelectorMode.BOX,
        }
    ),
}

COOLING_SCHEMA = {
    vol.Required(CONF_COOLING_POWER): selector.NumberSelector(
        {
            "min": 0,
            "mode": selector.NumberSelectorMode.BOX,
        }
    ),
}

POWER_UNIT_SCHEMA = {
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

METER_SCHEMA = {
    vol.Optional(CONF_APPLIANCE_METER): selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=UTILITY_METER_DOMAIN,
        )
    ),
}

SEER_SCHEMA = {
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

HSPF_SCHEMA = {
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

FURNACE_SCHEMA = (
    vol.Schema(NAME_SCHEMA)
    .extend(HEATING_SCHEMA)
    .extend(POWER_UNIT_SCHEMA)
    .extend(METER_SCHEMA)
    .extend(
        {
            vol.Optional(CONF_EFFICIENCY, default=80): selector.NumberSelector(
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

BOILER_SCHEMA = FURNACE_SCHEMA.extend(
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

COMPRESSOR_SCHEMA = (
    vol.Schema(NAME_SCHEMA)
    .extend(HEATING_SCHEMA)
    .extend(COOLING_SCHEMA)
    .extend(POWER_UNIT_SCHEMA)
    .extend(SEER_SCHEMA)
    .extend(METER_SCHEMA)
)

HEATPUMP_COMP_SCHEMA = (
    vol.Schema(NAME_SCHEMA)
    .extend(HEATING_SCHEMA)
    .extend(COOLING_SCHEMA)
    .extend(HEATING_SCHEMA)
    .extend(POWER_UNIT_SCHEMA)
    .extend(SEER_SCHEMA)
    .extend(HSPF_SCHEMA)
    .extend(METER_SCHEMA)
)

WINDOW_AC_SCHEMA = (
    vol.Schema(COOLING_SCHEMA)
    .extend(POWER_UNIT_SCHEMA)
    .extend(SEER_SCHEMA)
    .extend(METER_SCHEMA)
)
WINDOW_HP_SCHEMA = (
    vol.Schema(COOLING_SCHEMA)
    .extend(HEATING_SCHEMA)
    .extend(POWER_UNIT_SCHEMA)
    .extend(SEER_SCHEMA)
    .extend(HSPF_SCHEMA)
    .extend(METER_SCHEMA)
)
SPACE_HEATER_SCHEMA = (
    vol.Schema(HEATING_SCHEMA).extend(POWER_UNIT_SCHEMA).extend(METER_SCHEMA)
)


def gen_room_appliance_schema(entity_id: str) -> vol.Schema:
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


APPLIANCE_SCHEMA_MAP = {
    ControlApplianceType.WindowAC: WINDOW_AC_SCHEMA,
    ControlApplianceType.WindowHeatpump: WINDOW_HP_SCHEMA,
    ControlApplianceType.SpaceHeater: SPACE_HEATER_SCHEMA,
}

A2C_MAP = {
    ControlApplianceType.BoilerZoneValve: CentralApplianceType.HydroBoiler,
    ControlApplianceType.ThermoStaticRadiatorValve: CentralApplianceType.HydroBoiler,
    ControlApplianceType.HVACCoolCall: CentralApplianceType.AcCompressor,
    ControlApplianceType.HVACHeatCall: CentralApplianceType.HvacFurnace,
    ControlApplianceType.HVACThermostat: CentralApplianceType.HeatpumpCompressor,
    ControlApplianceType.HeatpumpFanUnit: CentralApplianceType.HeatpumpCompressor,
}

CENTRAL_APPLIANCE_MAP = {
    CentralApplianceType.HydroBoiler: BOILER_SCHEMA,
    CentralApplianceType.AcCompressor: COMPRESSOR_SCHEMA,
    CentralApplianceType.HvacFurnace: FURNACE_SCHEMA,
    CentralApplianceType.HeatpumpCompressor: HEATPUMP_COMP_SCHEMA,
}


def gen_adjacency_schema(rooms) -> tuple[vol.Schema, dict[str, str]]:
    """Generates an adjacency matrix schema based on the number of rooms, and associated placeholder data."""
    locations = ["Outside", *rooms]
    placeholders = {f"room{i}": r for i, r in enumerate(locations)}
    # placeholders = base_placeholders.copy()
    # placeholders["sections"] = {}
    # for i in range(len(locations)):
    #     placeholders["sections"].update({f"room{i}": base_placeholders})

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


def gen_select_central_schema(central_appliances: list[str]) -> vol.Schema:
    """Dynamically generate a dropdown selecto for central appliances based on ones that have already been added."""
    central_appliances = ["New", *central_appliances]
    return vol.Schema(
        {
            vol.Required("central_appliance", default="New"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=central_appliances,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                ),
            ),
        }
    )


# def gen_appliance_schema(appliance_type: ControlApplianceType) -> vol.Schema:


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config or options flow for UniStat."""

    VERSION = 1
    MINOR_VERSION = 1

    # def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
    #     """Return config entry title."""
    #     return cast(str, options["name"]) if "name" in options else ""

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

        return self.async_show_form(step_id="user", data_schema=MAIN_SCHEMA)

    async def async_step_adjacency(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure room adjacency matrix."""
        if user_input is not None:
            # Input is valid, set data.
            # TODO Format adjacency better
            self.data["adjacency"] = user_input
            # Return the form of the next step.
            if self.data[CONF_WEATHER_STATION]:
                return await self.async_step_weather_station()

            return await self.async_step_room_sensors()

        schema, placeholders = gen_adjacency_schema(self.data[CONF_AREAS])

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
            data_schema=WEATHER_STATION_SCHEMA,
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
            data_schema=ROOM_SCHEMA,
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
            data_schema=gen_room_appliance_schema(self.this_appliance),
            description_placeholders={
                "appliance": self.this_appliance,
            },
        )

    async def async_step_room_appliance_2(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Captures configuration of thermal controls in each room."""

        schema = (
            APPLIANCE_SCHEMA_MAP[self.appliance_type]
            if self.appliance_type in APPLIANCE_SCHEMA_MAP
            else gen_select_central_schema(list(self.data["central_appliances"].keys()))
        )

        if user_input is not None:
            # Input is valid, set data.
            if (
                "central_appliance" in user_input
                and user_input["central_appliance"] == "New"
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
            self.data["room_appliances"][self.this_appliance]["central_appliance"] = (
                user_input[CONF_NAME]
            )
            user_input["appliance_type"] = A2C_MAP[self.appliance_type]
            self.data["central_appliances"][user_input[CONF_NAME]] = user_input

            if self.room_appliance_index + 1 == len(self.data[CONF_CONTROLS]):
                return self.async_create_entry(
                    title=self.data[CONF_NAME], data=self.data
                )

            # Return the form of the next step.
            return await self.async_step_room_appliance_1()

        return self.async_show_form(
            step_id="central_appliance",
            data_schema=CENTRAL_APPLIANCE_MAP[A2C_MAP[self.appliance_type]],
            description_placeholders={
                "appliance": self.this_appliance,
                "central_appliance": str(A2C_MAP[self.appliance_type]),
            },
        )


# class MyOptionsFlow(OptionsFlowWithReload):
#     async def async_step_init(
#         self, user_input: dict[str, Any] | None = None
#     ) -> ConfigFlowResult:
#         """Invoked when a user initiates a flow via the user interface."""
#         if user_input is not None:
#             self.data = user_input
#             self.data["room_conf"] = []
#             self.added_temp_sensors = set()
#             self.added_humidity_sensors = set()
#             self.added_areas = set()
#             if CONF_OUTDOOR_SENSORS in user_input:
#                 if CONF_TEMP_ENTITY in user_input[CONF_OUTDOOR_SENSORS]:
#                     self.added_temp_sensors.add(
#                         user_input[CONF_OUTDOOR_SENSORS][CONF_TEMP_ENTITY]
#                     )
#                 if CONF_HUMIDITY_ENTITY in user_input[CONF_OUTDOOR_SENSORS]:
#                     self.added_humidity_sensors.add(
#                         user_input[CONF_OUTDOOR_SENSORS][CONF_HUMIDITY_ENTITY]
#                     )
#             self.data[CONF_ADJACENCY] = False  # TODO Remove once adjacency is supported
#             if self.data[CONF_BOILER]:
#                 return await self.async_step_boiler()
#             # Return the form of the next step.
#             return await self.async_step_room()

#         return self.async_show_form(step_id="user", data_schema=MAIN_SCHEMA)
