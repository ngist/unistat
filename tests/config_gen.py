import numpy as np

import random

from typing import Optional, NamedTuple

from functools import partial

from homeassistant.const import (
    CONF_NAME,
    CONF_TEMPERATURE_UNIT,
    CONF_UNIT_OF_MEASUREMENT,
    UnitOfPower,
    UnitOfTemperature,
)

from custom_components.unistat.const import (
    CONF_ADJACENCY,
    CONF_AREAS,
    CONF_CONTROLS,
    CONF_WEATHER_ENTITY,
    CONF_GAS_PRICE_ENTITY,
    CONF_ELECTRIC_PRICE_ENTITY,
    CONF_CONTROL_MODE,
    CONF_HUMIDITY_ENTITY,
    CONF_SOLAR_FLUX_ENTITY,
    CONF_TEMP_ENTITY,
    CONF_WIND_DIRECTION_ENTITY,
    CONF_WIND_SPEED_ENTITY,
    CONF_WEATHER_STATION,
    CONF_SEER_RATING,
    CONF_SEER_STANDARD,
    CONF_BOILER_INLET_TEMP_ENTITY,
    CONF_BOILER_OUTLET_TEMP_ENTITY,
    CONF_HEATING_POWER,
    CONF_CENTRAL_APPLIANCE,
    CONF_COOLING_POWER,
    CONF_HSPF_RATING,
    CONF_HSPF_STANDARD,
    CONF_APPLIANCE_METER,
    CONF_EFFICIENCY,
    CONF_APPLIANCE_TYPE,
    ControlApplianceType,
    CentralApplianceType,
    ControlMode,
)


# These are config generator helper functions, actual concrete configs should live with their unit tests
class ConfigParams(NamedTuple):
    main_conf: dict
    room_sensors: dict
    control_appliances: dict
    central_appliances: list = []
    adjacency: dict = []
    weather_station: dict = {}


# Helpers
def make_expected(config: ConfigParams):
    expected = config.main_conf.copy()
    expected["room_sensors"] = config.room_sensors.copy()
    expected["control_appliances"] = config.control_appliances.copy()
    expected["central_appliances"] = {}
    for app in config.central_appliances:
        app_name = app[1][CONF_NAME]
        app_data = app[1].copy()
        app_data[CONF_APPLIANCE_TYPE] = app[0]
        expected["central_appliances"][app_name] = app_data

    central_counter = 0
    for app in expected["control_appliances"]:
        if CONF_CENTRAL_APPLIANCE in app and app[CONF_CENTRAL_APPLIANCE] == "New":
            app[CONF_CENTRAL_APPLIANCE] = config.central_appliances[central_counter][1][
                "name"
            ]
            central_counter += 1

    rooms = expected[CONF_AREAS]
    size = len(rooms) + 1
    adj = np.zeros((size, size), dtype=np.int32)
    if expected[CONF_ADJACENCY]:
        room2idx = {r: i for i, r in enumerate(config.main_conf[CONF_AREAS])}
        for k in config.adjacency:
            i = int(k.replace("room", ""))
            for r in config.adjacency[k]:
                adj[i, room2idx[r] + 1] = 1 if config.adjacency[k][r] else 0
    else:
        # Create default adjacency
        adj[0, 1:] = 1
    expected["adjacency"] = adj.tolist()
    if expected[CONF_WEATHER_STATION]:
        expected["weather_station"] = config.weather_station.copy()
    return expected


# Room sensor config generators
def make_room_sensors(room: str, has_humidity: bool = False) -> dict[str, str]:
    sensors = {
        CONF_TEMP_ENTITY: f"sensor.{room}_temp",
    }
    if has_humidity:
        sensors[CONF_HUMIDITY_ENTITY] = f"sensor.{room}_humidity"

    return sensors


def make_multiroom_sensors(
    rooms: list[str], has_humidity: bool = False
) -> dict[str, dict[str, str]]:
    return {r: make_room_sensors(r, has_humidity=has_humidity) for r in rooms}


# Room appliance config generators
## Standalone appliances
def make_spaceheater(room: str, has_meter: bool = False) -> dict[str, str]:
    app = {
        CONF_APPLIANCE_TYPE: ControlApplianceType.SpaceHeater,
        CONF_AREAS: [room],
        CONF_HEATING_POWER: 1000.0,
        CONF_UNIT_OF_MEASUREMENT: UnitOfPower.WATT,
    }
    if has_meter:
        app[CONF_APPLIANCE_METER] = f"sensor.{room}_space_heater_meter"

    return app


def make_window_ac(room: str, has_meter: bool = False) -> dict[str, str]:
    app = {
        CONF_APPLIANCE_TYPE: ControlApplianceType.WindowAC,
        CONF_AREAS: [room],
        CONF_COOLING_POWER: 1000.0,
        CONF_UNIT_OF_MEASUREMENT: UnitOfPower.WATT,
        CONF_SEER_RATING: 13.0,
        CONF_SEER_STANDARD: "SEER2",
    }
    if has_meter:
        app[CONF_APPLIANCE_METER] = f"sensor.{room}_window_ac_meter"

    return app


def make_window_hp(room: str, has_meter: bool = False) -> dict[str, str]:
    app = {
        CONF_APPLIANCE_TYPE: ControlApplianceType.WindowHeatpump,
        CONF_AREAS: [room],
        CONF_HEATING_POWER: 1000.0,
        CONF_COOLING_POWER: 1000.0,
        CONF_UNIT_OF_MEASUREMENT: UnitOfPower.WATT,
        CONF_SEER_RATING: 13.0,
        CONF_SEER_STANDARD: "SEER2",
        CONF_HSPF_RATING: 13.0,
        CONF_HSPF_STANDARD: "HSPF2",
    }
    if has_meter:
        app[CONF_APPLIANCE_METER] = f"sensor.{room}_window_hp_meter"

    return app


## Peripheral appliances
def _make_peripheral(
    rooms: str, app_type: ControlApplianceType, central_appliance=None
):
    return {
        CONF_APPLIANCE_TYPE: app_type,
        CONF_AREAS: rooms,
        CONF_CENTRAL_APPLIANCE: central_appliance if central_appliance else "New",
    }


make_zonevalve = partial(_make_peripheral, app_type=ControlApplianceType.BoilerZoneCall)
make_trv = partial(
    _make_peripheral, app_type=ControlApplianceType.ThermoStaticRadiatorValve
)
make_hvac_climate = partial(
    _make_peripheral, app_type=ControlApplianceType.HVACThermostat
)
make_heat_call = partial(_make_peripheral, app_type=ControlApplianceType.HVACHeatCall)
make_cool_call = partial(_make_peripheral, app_type=ControlApplianceType.HVACCoolCall)

# Central appliance generators


def make_furnace(name: str = "furnace", has_meter: bool = False):
    conf = {
        CONF_NAME: name,
        CONF_HEATING_POWER: 140000.0,
        CONF_UNIT_OF_MEASUREMENT: UnitOfPower.BTU_PER_HOUR,
        CONF_EFFICIENCY: 80.0,
    }
    if has_meter:
        conf[CONF_APPLIANCE_METER] = f"sensor.{name}_meter"

    return (CentralApplianceType.HvacFurnace, conf)


def make_boiler(
    name: str = "boiler",
    inlet_temp: Optional[str] = None,
    outlet_temp: Optional[str] = None,
    has_meter: bool = False,
):
    conf = {
        CONF_NAME: name,
        CONF_HEATING_POWER: 140000.0,
        CONF_UNIT_OF_MEASUREMENT: UnitOfPower.BTU_PER_HOUR,
        CONF_EFFICIENCY: 80.0,
    }
    if inlet_temp:
        conf[CONF_BOILER_INLET_TEMP_ENTITY] = inlet_temp
    if outlet_temp:
        conf[CONF_BOILER_OUTLET_TEMP_ENTITY] = outlet_temp
    if has_meter:
        conf[CONF_APPLIANCE_METER] = f"sensor.{name}_meter"
    return (CentralApplianceType.HydroBoiler, conf)


def make_ac_compressor(name: str = "compressor", has_meter: bool = False):
    conf = {
        CONF_NAME: name,
        CONF_COOLING_POWER: 140000.0,
        CONF_UNIT_OF_MEASUREMENT: UnitOfPower.BTU_PER_HOUR,
        CONF_SEER_RATING: 13.0,
        CONF_SEER_STANDARD: "SEER2",
    }
    if has_meter:
        conf[CONF_APPLIANCE_METER] = f"sensor.{name}_meter"
    return (CentralApplianceType.AcCompressor, conf)


def make_hp_compressor(name: str = "compressor", has_meter: bool = False):
    conf = {
        CONF_NAME: name,
        CONF_COOLING_POWER: 140000.0,
        CONF_HEATING_POWER: 140000.0,
        CONF_UNIT_OF_MEASUREMENT: UnitOfPower.BTU_PER_HOUR,
        CONF_SEER_RATING: 13.0,
        CONF_SEER_STANDARD: "SEER2",
        CONF_HSPF_RATING: 13.0,
        CONF_HSPF_STANDARD: "HSPF2",
    }
    if has_meter:
        conf[CONF_APPLIANCE_METER] = f"sensor.{name}_meter"
    return (CentralApplianceType.HeatpumpCompressor, conf)


# Other configs


def make_main_conf(
    rooms: list[str],
    controls: list[str],
    temp_unit: UnitOfTemperature = UnitOfTemperature.FAHRENHEIT,
    control_mode: ControlMode = ControlMode.COMFORT,
    weather_entity: str = "weather.forecast_home",
    use_adjacency: bool = False,
    use_weather_station: bool = False,
    gas_price: Optional[str] = None,
    electric_price: Optional[str] = None,
):
    conf = {
        CONF_AREAS: rooms,
        CONF_CONTROLS: controls,
        CONF_WEATHER_ENTITY: weather_entity,
        CONF_CONTROL_MODE: control_mode,
        CONF_TEMPERATURE_UNIT: temp_unit,
        CONF_ADJACENCY: use_adjacency,
        CONF_WEATHER_STATION: use_weather_station,
    }
    if gas_price:
        conf[CONF_GAS_PRICE_ENTITY] = gas_price
    if electric_price:
        conf[CONF_ELECTRIC_PRICE_ENTITY] = electric_price

    return conf


def make_adjacency(rooms):
    conf = {}
    locations = ["outside", *rooms]
    for i, _ in enumerate(locations):
        if i + 1 != len(locations):
            conf[f"room{i}"] = {x: random.choice([True, False]) for x in rooms[i:]}

    return conf


def make_weather_station(
    temp: Optional[str] = None,
    humidity: Optional[str] = None,
    wind_speed: Optional[str] = None,
    wind_dir: Optional[str] = None,
    solar_flux: Optional[str] = None,
):
    conf = {}
    if temp:
        conf[CONF_TEMP_ENTITY] = temp
    if humidity:
        conf[CONF_HUMIDITY_ENTITY] = humidity
    if wind_speed:
        conf[CONF_WIND_SPEED_ENTITY] = wind_speed
    if wind_dir:
        conf[CONF_WIND_DIRECTION_ENTITY] = wind_dir
    if solar_flux:
        conf[CONF_SOLAR_FLUX_ENTITY] = solar_flux
    return conf
