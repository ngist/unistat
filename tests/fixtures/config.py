import pytest

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
    CONF_HEATING_POWER,
    CONF_APPLIANCE_METER,
    CONF_APPLIANCE_TYPE,
    ControlApplianceType,
    ControlMode,
)


@pytest.fixture
def make_room_sensors():
    def _make_room_sensors(room: str, has_humidity: bool = False):
        sensors = {
            CONF_TEMP_ENTITY: f"sensor.{room}_temp",
        }
        if has_humidity:
            sensors[CONF_HUMIDITY_ENTITY] = f"sensor.{room}_humidity"

        return sensors

    return _make_room_sensors


@pytest.fixture
def make_spaceheater():
    def _make_spaceheater(room: str, has_meter: bool = False, join_steps: bool = False):
        step1 = {
            CONF_APPLIANCE_TYPE: ControlApplianceType.SpaceHeater,
            CONF_AREAS: [room],
        }

        step2 = {CONF_HEATING_POWER: 1000.0, CONF_UNIT_OF_MEASUREMENT: UnitOfPower.WATT}
        if has_meter:
            step2.update({CONF_APPLIANCE_METER: f"sensor.{room}_space_heater_meter"})

        if join_steps:
            return step1.update(step2)

        return [step1, step2]

    return _make_spaceheater


@pytest.fixture
def rooms():
    return ["kitchen", "living_room", "bedroom"]


@pytest.fixture
def room_sensors(rooms, make_room_sensors):
    return {r: make_room_sensors(r) for r in rooms}


@pytest.fixture
def room_sensors_w_humidity(rooms, make_room_sensors):
    return {r: make_room_sensors(r, has_humidity=True) for r in rooms}


@pytest.fixture
def spaceheater_minimal(rooms, make_spaceheater):
    """Minimal standalone appliance config"""
    return make_spaceheater(rooms[0])


@pytest.fixture
def spaceheaters_expected(rooms, make_spaceheater):
    return {r: make_spaceheater(r, join_steps=True) for r in rooms}


@pytest.fixture
def main_minimal(rooms):
    return {
        CONF_NAME: "My UniStat",
        CONF_AREAS: [rooms[0]],
        CONF_CONTROLS: [f"switch.{rooms[0]}_space_heater"],
        CONF_WEATHER_ENTITY: "weather.forecast_home",
        CONF_CONTROL_MODE: ControlMode.COMFORT,
        CONF_TEMPERATURE_UNIT: UnitOfTemperature.FAHRENHEIT,
        CONF_ADJACENCY: False,
        CONF_WEATHER_STATION: False,
    }


@pytest.fixture
def main_maximal(main_minimal, rooms):
    data = {**main_minimal}
    data.update(
        {
            CONF_AREAS: rooms,
            CONF_GAS_PRICE_ENTITY: "input_number.gas_price_btuh",
            CONF_ELECTRIC_PRICE_ENTITY: "input_number.electric_price_kWh",
            CONF_ADJACENCY: True,
            CONF_WEATHER_STATION: True,
        }
    )
    return data


@pytest.fixture
def weather_station_minimal():
    return {}


def weather_station_maximal(weather_station_minimal):
    data = {**weather_station_minimal}
    data.update(
        {
            CONF_TEMP_ENTITY: "sensor.outside_temp",
            CONF_HUMIDITY_ENTITY: "sensor.outside_humidity",
            CONF_WIND_SPEED_ENTITY: "sensor.wind_speed",
            CONF_WIND_DIRECTION_ENTITY: "sensor.wind_direction",
            CONF_SOLAR_FLUX_ENTITY: "sensor.solar_irradiance",
        }
    )
    return data
