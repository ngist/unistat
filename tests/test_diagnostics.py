"""Test the UniStat integration."""

import json
from custom_components.unistat.const import (
    DOMAIN,
)
from custom_components.unistat.diagnostics import async_get_config_entry_diagnostics
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
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


def is_jsonable(diagnostics):
    """Check that diagnostics are serializable"""
    try:
        json.dumps(diagnostics)
        return True
    except (TypeError, OverflowError) as e:
        print(e)
        return False


@pytest.mark.parametrize("platform", PLATFORMS)
async def test_diagnostics(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    platform: str,
    mydata: ConfigParams,
) -> None:
    """Test getting diagnostics"""
    # Setup the config entry
    config_entry = MockConfigEntry(
        data=mydata,
        domain=DOMAIN,
        options={},
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(
        hass, config_entry=config_entry
    )

    assert "model_parameters" in diagnostics
    assert "config_entry_data" in diagnostics

    assert is_jsonable(diagnostics)
