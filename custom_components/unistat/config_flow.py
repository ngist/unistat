"""Config flow for the UniStat integration."""

from typing import Any, Tuple, Dict, List

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
from homeassistant.helpers import selector, NumberSelectorMode
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
        vol.Required(CONF_CONTROLS): selector.AreaSelector(
            selector.EntitySelectorConfig(
                domain=[SWITCH_DOMAIN, CLIMATE_DOMAIN],
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
                device_class=[SensorDeviceClass.MONETARY, None],
            )
        ),
        vol.Optional(
            CONF_ELECTRIC_PRICE_ENTITY,
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=[SensorDeviceClass.MONETARY, None],
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

BASE_CENTRAL_APPLIANCE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_APPLIANCE_TYPE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=CentralApplianceType,
                mode=selector.SelectSelectorMode.DROPDOWN,
            ),
        ),
        vol.Optional(CONF_APPLIANCE_METER): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=UTILITY_METER_DOMAIN,
            )
        ),
    }
)

BASE_HEATING_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HEATING_POWER): selector.NumberSelector(
            {
                "min": 0,
                "mode": NumberSelectorMode.BOX,
            }
        ),
    }
)

BASE_COOLING_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COOLING_POWER): selector.NumberSelector(
            {
                "min": 0,
                "mode": NumberSelectorMode.BOX,
            }
        ),
    }
)

POWER_UNIT_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_UNIT_OF_MEASUREMENT,
            default=UnitOfPower.BTU_PER_HOUR,
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[UnitOfPower.BTU_PER_HOUR, UnitOfPower.WATT],
                mode=selector.SelectSelectorMode.DROPDOWN,
            ),
        ),
    }
)

METER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_APPLIANCE_METER): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=UTILITY_METER_DOMAIN,
            )
        ),
    }
)

BOILER_SCHEMA = (
    BASE_CENTRAL_APPLIANCE_SCHEMA.extend(BASE_HEATING_SCHEMA)
    .extend(POWER_UNIT_SCHEMA)
    .extend(METER_SCHEMA)
    .extend(
        vol.Schema(
            {
                vol.Optional(CONF_EFFICIENCY, default=80): selector.NumberSelector(
                    {
                        "min": 0,
                        "max": 100,
                        CONF_UNIT_OF_MEASUREMENT: "%",
                        "mode": NumberSelectorMode.BOX,
                    }
                ),
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
    )
)

SEER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SEER_RATING, default=15): selector.NumberSelector(
            {
                "min": 10,
                "max": 30,
                "mode": NumberSelectorMode.BOX,
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
)

HSPF_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_HSPF_RATING, default=15): selector.NumberSelector(
            {
                "min": 5,
                "max": 15,
                "mode": NumberSelectorMode.BOX,
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
)

COMPRESSOR_SCHEMA = (
    BASE_CENTRAL_APPLIANCE_SCHEMA.extend(BASE_COOLING_SCHEMA)
    .extend(POWER_UNIT_SCHEMA)
    .extend(SEER_SCHEMA)
    .extend(METER_SCHEMA)
)

HEATPUMP_COMP_SCHEMA = (
    BASE_CENTRAL_APPLIANCE_SCHEMA.extend(BASE_COOLING_SCHEMA)
    .extend(BASE_HEATING_SCHEMA)
    .extend(POWER_UNIT_SCHEMA)
    .extend(SEER_SCHEMA)
    .extend(HSPF_SCHEMA)
    .extend(METER_SCHEMA)
)


def gen_room_appliance_schema(entity_id: str) -> vol.Schema:
    type_options = {
        SWITCH_DOMAIN: SWITCH_APPLIANCE_TYPES,
        CLIMATE_DOMAIN: CLIMATE_APPLIANCE_TYPES,
    }
    domain = entity_id.split(".", maxsplit=1)[0]
    vol.Schema(
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


WINDOW_AC_SCHEMA = (
    BASE_COOLING_SCHEMA.extend(POWER_UNIT_SCHEMA)
    .extend(SEER_SCHEMA)
    .extend(METER_SCHEMA)
)
WINDOW_HP_SCHEMA = (
    BASE_COOLING_SCHEMA.extend(BASE_HEATING_SCHEMA)
    .extend(POWER_UNIT_SCHEMA)
    .extend(SEER_SCHEMA)
    .extend(HSPF_SCHEMA)
    .extend(METER_SCHEMA)
)
SPACE_HEATER_SCHEMA = BASE_HEATING_SCHEMA.extend(POWER_UNIT_SCHEMA).extend(METER_SCHEMA)

APPLIANCE_SCHEMA_MAP = {
    ControlApplianceType.WindowAC: WINDOW_AC_SCHEMA,
    ControlApplianceType.WindowHeatpump: WINDOW_HP_SCHEMA,
    ControlApplianceType.SpaceHeater: SPACE_HEATER_SCHEMA,
}

CENTRAL_APPLIANCE_MAP = {
    ControlApplianceType.BoilerZoneValve: BOILER_SCHEMA,
    ControlApplianceType.HVACCoolCall: None,
    ControlApplianceType.HVACHeatCall: None,
    ControlApplianceType.HVACThermostat: None,
    ControlApplianceType.HeatpumpFanUnit: HEATPUMP_COMP_SCHEMA,
    ControlApplianceType.ThermoStaticRadiatorValve: BOILER_SCHEMA,
}


def gen_adjacency_schema(rooms) -> Tuple[vol.Schema, Dict[str, str]]:
    """Generates an adjacency matrix schema based on the number of rooms, and associated placeholder data."""
    schema = {}
    for i, r in enumerate(rooms):
        if len(rooms) - 1 != i:
            sub_schema = {}
            for x in rooms[i + 1 :]:
                sub_schema[vol.Required(x, default=True)] = bool
            schema[vol.Required(r)] = section(sub_schema, options=None)

    schema = vol.Schema(schema)
    placeholders = {f"room{i}": r for i, r in enumerate(rooms)}

    return schema, placeholders


def gen_select_central_schema(central_appliances: List[str]) -> vol.Schema:
    central_appliances = central_appliances + ["New"]
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
            return await self.async_step_room()

        schema, placeholders = gen_adjacency_schema(self.data[CONF_AREAS])

        return self.async_show_form(
            step_id="adjacency",
            data_schema=schema,
            description_placeholders=placeholders,
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

            if room_index == len(self.data[CONF_AREAS]):
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

        self.room_appliance_index = len(self.data["room_appliances"])
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
            if user_input["central_appliance"] == "New":
                return self.async_step_central_appliance()

            self.data["room_appliances"][self.this_appliance].update(user_input)

            if self.room_appliance_index == len(self.data[CONF_CONTROLS]):
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
            self.data["central_appliances"][user_input[CONF_NAME]] = user_input
            if user_input[CONF_NAME] == "New":
                return self.async_step_central_appliance()

            if self.room_appliance_index == len(self.data[CONF_CONTROLS]):
                return self.async_create_entry(
                    title=self.data[CONF_NAME], data=self.data
                )

            # Return the form of the next step.
            return await self.async_step_room_appliance_1()

        return self.async_show_form(
            step_id="central_appliance",
            data_schema=CENTRAL_APPLIANCE_MAP[self.appliance_type],
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
