"""Test the UniStat integration."""

from custom_components.unistat.const import (
    CONF_AREAS,
    DOMAIN,
    TITLE,
)
from custom_components.unistat.sensor import UNISTAT_SENSOR_TYPES
from custom_components.unistat.binary_sensor import UNISTAT_BINARY_SENSOR_TYPES
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN


from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .config_gen import (
    ConfigParams,
    make_expected,
    make_main_conf,
    make_multiroom_sensors,
    make_spaceheater,
)

PLATFORMS = [CLIMATE_DOMAIN]


@pytest.fixture
def mydata():
    rooms = ["kitchen", "bedroom", "living_room"]
    controls = ["switch.spaceheater1", "switch.spaceheater2"]
    params = ConfigParams(
        main_conf=make_main_conf(rooms, controls),
        room_sensors=make_multiroom_sensors(rooms),
        room_appliances={
            c: make_spaceheater([rooms[i]]) for i, c in enumerate(controls)
        },
    )
    return make_expected(params)


@pytest.fixture
def eids(mydata):
    climate_eids = [f"{CLIMATE_DOMAIN}.{DOMAIN}_{room}" for room in mydata[CONF_AREAS]]
    sensor_eids = [f"{SENSOR_DOMAIN}.{DOMAIN}_{s.key}" for s in UNISTAT_SENSOR_TYPES]
    binary_sensor_eids = [
        f"{BINARY_SENSOR_DOMAIN}.{DOMAIN}_{s.key}" for s in UNISTAT_BINARY_SENSOR_TYPES
    ]

    return {
        CLIMATE_DOMAIN: climate_eids,
        SENSOR_DOMAIN: sensor_eids,
        BINARY_SENSOR_DOMAIN: binary_sensor_eids,
    }


@pytest.fixture
def friendly_names(mydata):
    climate_names = [f"{TITLE} {room}" for room in mydata[CONF_AREAS]]
    sensor_names = [f"{SENSOR_DOMAIN}.{TITLE} {s.name}" for s in UNISTAT_SENSOR_TYPES]
    binary_sensor_names = [
        f"{BINARY_SENSOR_DOMAIN}.{TITLE} {s.name}" for s in UNISTAT_BINARY_SENSOR_TYPES
    ]

    return {
        CLIMATE_DOMAIN: climate_names,
        SENSOR_DOMAIN: sensor_names,
        BINARY_SENSOR_DOMAIN: binary_sensor_names,
    }


@pytest.mark.parametrize("platform", PLATFORMS)
async def test_setup_and_remove_config_entry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    platform: str,
    eids: dict[str, list[str]],
    friendly_names: dict[str, list[str]],
    mydata: ConfigParams,
) -> None:
    """Test setting up and removing a config entry."""

    # Setup the config entry
    config_entry = MockConfigEntry(
        data=mydata,
        domain=DOMAIN,
        options={},
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    for eid, friendly_name in zip(eids[platform], friendly_names[platform]):
        assert entity_registry.async_get(eid) is not None

        # Check the friendly name
        state = hass.states.get(eid)
        assert state.attributes["friendly_name"] == friendly_name

    # Remove the config entry
    assert await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the state and entity registry entry are removed
    for eid in eids[platform]:
        assert hass.states.get(eid) is None
        assert entity_registry.async_get(eid) is None
