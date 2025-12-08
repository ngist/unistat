"""Test the UniStat config flow."""

from unittest.mock import AsyncMock


from custom_components.unistat.const import (
    CONF_AREAS,
    CONF_CONTROLS,
    CONF_ADJACENCY,
    CONF_WEATHER_STATION,
    CONF_CENTRAL_APPLIANCE,
    CONF_APPLIANCE_TYPE,
    DOMAIN,
)
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .config_gen import (
    ConfigParams,
    make_adjacency,
    make_boiler,
    make_expected,
    make_main_conf,
    make_multiroom_sensors,
    make_spaceheater,
    make_weather_station,
    make_zonevalve,
)

pytestmark = pytest.mark.usefixtures("mock_setup_entry")


def split_room_app_config(room_appliance: dict):
    STEP1_KEYS = [CONF_APPLIANCE_TYPE, CONF_AREAS]
    step1 = {k: room_appliance[k] for k in room_appliance if k in STEP1_KEYS}
    step2 = room_appliance.copy()
    for k in STEP1_KEYS:
        step2.pop(k)
    return (step1, step2)


async def config_step(hass, result, config_data):
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        config_data,
    )
    await hass.async_block_till_done()
    return result


rooms = ["kitchen"]
controls = ["switch.spaceheater"]
# Minimal config flow
_NOMINAL_MINIMAL_CONF = ConfigParams(
    main_conf=make_main_conf(rooms=rooms, controls=controls),
    room_sensors=make_multiroom_sensors(rooms),
    room_appliances={controls[0]: make_spaceheater(rooms[0])},
)

# Minimal config flow with weather station
_NOMINAL_MIN_WS_CONF = ConfigParams(
    main_conf=make_main_conf(rooms=rooms, controls=controls, use_weather_station=True),
    room_sensors=make_multiroom_sensors(rooms),
    room_appliances={controls[0]: make_spaceheater(rooms[0])},
    weather_station=make_weather_station(temp="sensor.outside_temp"),
)

# Minimal config flow with adjacency
_NOMINAL_MIN_ADJ_CONF = ConfigParams(
    main_conf=make_main_conf(rooms=rooms, controls=controls, use_adjacency=True),
    room_sensors=make_multiroom_sensors(rooms),
    room_appliances={controls[0]: make_spaceheater(rooms[0])},
    adjacency=make_adjacency(rooms),
)

# Minimal config flow with weather station and adjacency
_NOMINAL_MIN_ADJ_WS_CONF = ConfigParams(
    main_conf=make_main_conf(
        rooms=rooms, controls=controls, use_weather_station=True, use_adjacency=True
    ),
    room_sensors=make_multiroom_sensors(rooms),
    room_appliances={controls[0]: make_spaceheater(rooms[0])},
    weather_station=make_weather_station(temp="sensor.outside_temp"),
    adjacency=make_adjacency(rooms),
)

# Minimal config flow with a central appliance
controls = ["switch.zonevalve"]
_NOMINAL_MINIMAL_WCENTRAL_CONF = ConfigParams(
    main_conf=make_main_conf(rooms=rooms, controls=controls),
    room_sensors=make_multiroom_sensors(rooms),
    room_appliances={controls[0]: make_zonevalve(rooms)},
    central_appliances=[make_boiler()],
)

rooms = ["kitchen", "bedroom", "living_room"]
controls = [
    "switch.kitchen_spaceheater",
    "switch.boiler_zonevalve",
    "switch.boiler_zonevalve2",
]
_NOMINAL_COMPLEX_CONF = ConfigParams(
    main_conf=make_main_conf(rooms=rooms, controls=controls),
    room_sensors=make_multiroom_sensors(rooms),
    room_appliances={
        controls[0]: make_spaceheater(rooms[0]),
        controls[1]: make_zonevalve([rooms[1]], central_appliance="New"),
        controls[2]: make_zonevalve([rooms[2]], central_appliance="boiler"),
    },
    central_appliances=[make_boiler(name="boiler")],
)

_NOMINAL_NONTRIV_ADJ_CONF = ConfigParams(
    main_conf=make_main_conf(rooms=rooms, controls=controls, use_adjacency=True),
    room_sensors=make_multiroom_sensors(rooms),
    room_appliances={
        controls[0]: make_spaceheater(rooms[0]),
        controls[1]: make_zonevalve([rooms[1]], central_appliance="New"),
        controls[2]: make_zonevalve([rooms[2]], central_appliance="boiler"),
    },
    central_appliances=[make_boiler(name="boiler")],
    adjacency=make_adjacency(rooms),
)

CONFIG_FLOWS = [
    _NOMINAL_MINIMAL_CONF,
    _NOMINAL_MIN_WS_CONF,
    _NOMINAL_MIN_ADJ_CONF,
    _NOMINAL_MIN_ADJ_WS_CONF,
    _NOMINAL_MINIMAL_WCENTRAL_CONF,
    _NOMINAL_COMPLEX_CONF,
    _NOMINAL_NONTRIV_ADJ_CONF,
]

PLATFORMS = ["climate"]


@pytest.mark.parametrize("platform", PLATFORMS)
@pytest.mark.parametrize("config", CONFIG_FLOWS)
async def test_nominal_config_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    platform,
    config,
) -> None:
    """Test the minimal config flow with no optional inputs."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Main Config step "user"
    result = await config_step(hass, result, config.main_conf)

    # Adjacency config
    if config.main_conf[CONF_ADJACENCY]:
        result = await config_step(hass, result, config.adjacency)

    # Weather station config
    if config.main_conf[CONF_WEATHER_STATION]:
        result = await config_step(hass, result, config.weather_station)

    # Room sensor config
    for r in config.main_conf[CONF_AREAS]:
        result = await config_step(hass, result, config.room_sensors[r])

    # Appliance config
    central_app_index = 0
    for c in config.main_conf[CONF_CONTROLS]:
        step1_conf, step2_conf = split_room_app_config(config.room_appliances[c])
        # Step 1
        result = await config_step(hass, result, step1_conf)

        # Step 2
        result = await config_step(hass, result, step2_conf)

        if (
            CONF_CENTRAL_APPLIANCE in step2_conf
            and step2_conf[CONF_CENTRAL_APPLIANCE] == "New"
        ):
            # central appliance conf
            result = await config_step(
                hass, result, config.central_appliances[central_app_index][1]
            )
            central_app_index += 1

    # Check results
    expected = make_expected(config)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My UniStat"
    assert result["data"] == expected
    assert result["options"] == {}
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == expected
    assert config_entry.options == {}
    assert config_entry.title == "My UniStat"


# DUPLICATE_CASES = [
#     (ROOM_2_DUPE_AREA, "area_reused"),
#     (ROOM_2_DUPE_TEMP_INSIDE, "temp_sensor_reused"),
#     (ROOM_2_DUPE_TEMP_OUTSIDE, "temp_sensor_reused"),
#     (ROOM_2_DUPE_TEMP_BOILER, "temp_sensor_reused"),
#     (ROOM_2_DUPE_HUMIDITY_INSIDE, "humidity_sensor_reused"),
#     (ROOM_2_DUPE_HUMIDITY_OUTSIDE, "humidity_sensor_reused"),
# ]


# @pytest.mark.parametrize("platform", PLATFORMS)
# @pytest.mark.parametrize("bad_room,expected_error", DUPLICATE_CASES)
# async def test_config_flow_duplicate_area(
#     hass: HomeAssistant, mock_setup_entry: AsyncMock, platform, bad_room, expected_error
# ) -> None:
#     """Test the config flow with all optional inputs."""

#     # User Step
#     result = await hass.config_entries.flow.async_init(
#         DOMAIN, context={"source": config_entries.SOURCE_USER}
#     )
#     assert result["type"] is FlowResultType.FORM
#     assert not result["errors"]

#     result = await hass.config_entries.flow.async_configure(
#         result["flow_id"],
#         MAIN_SETTINGS_MAXIMAL,
#     )
#     await hass.async_block_till_done()

#     # Boiler Settings Step
#     assert result["type"] is FlowResultType.FORM
#     assert not result["errors"]
#     result = await hass.config_entries.flow.async_configure(
#         result["flow_id"],
#         BOILER_SETTINGS_MAXIMAL,
#     )
#     await hass.async_block_till_done()

#     # ROOM 1
#     assert result["type"] is FlowResultType.FORM
#     assert not result["errors"]
#     result = await hass.config_entries.flow.async_configure(
#         result["flow_id"],
#         ROOM_1_SETTINGS_HUMIDITY,
#     )
#     await hass.async_block_till_done()

#     # ROOM 2
#     assert result["type"] is FlowResultType.FORM
#     assert not result["errors"]
#     result = await hass.config_entries.flow.async_configure(
#         result["flow_id"],
#         bad_room,
#     )
#     await hass.async_block_till_done()
#     assert result["type"] is FlowResultType.FORM
#     assert expected_error == result["errors"]["base"]


# def get_suggested(schema, key):
#     """Get suggested value for key in voluptuous schema."""
#     for k in schema:
#         if k == key:
#             if k.description is None or "suggested_value" not in k.description:
#                 return None
#             return k.description["suggested_value"]
#     # Wanted key absent from schema
#     raise KeyError(f"Key `{key}` is missing from schema")


# @pytest.mark.skip
# @pytest.mark.parametrize("platform", ["sensor"])
# async def test_options(hass: HomeAssistant, platform) -> None:
#     """Test reconfiguring."""
#     input_sensor_1_entity_id = "sensor.input1"
#     input_sensor_2_entity_id = "sensor.input2"

#     # Setup the config entry
#     config_entry = MockConfigEntry(
#         data={},
#         domain=DOMAIN,
#         options={
#             "entity_id": input_sensor_1_entity_id,
#             "name": "My UniStat",
#         },
#         title="My UniStat",
#     )
#     config_entry.add_to_hass(hass)
#     assert await hass.config_entries.async_setup(config_entry.entry_id)
#     await hass.async_block_till_done()

#     result = await hass.config_entries.options.async_init(config_entry.entry_id)
#     assert result["type"] is FlowResultType.FORM
#     assert result["step_id"] == "init"
#     schema = result["data_schema"].schema
#     assert get_suggested(schema, "entity_id") == input_sensor_1_entity_id

#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input={
#             "entity_id": input_sensor_2_entity_id,
#         },
#     )
#     assert result["type"] is FlowResultType.CREATE_ENTRY
#     assert result["data"] == {
#         "entity_id": input_sensor_2_entity_id,
#         "name": "My UniStat",
#     }
#     assert config_entry.data == {}
#     assert config_entry.options == {
#         "entity_id": input_sensor_2_entity_id,
#         "name": "My UniStat",
#     }
#     assert config_entry.title == "My UniStat"

#     # Check config entry is reloaded with new options
#     await hass.async_block_till_done()

#     # Check the entity was updated, no new entity was created
#     assert len(hass.states.async_all()) == 1

#     # TODO Check the state of the entity has changed as expected
#     state = hass.states.get(f"{platform}.my_unistat")
#     assert state.attributes == {}
