"""Test the UniStat integration."""

from custom_components.unistat.const import (
    CONF_AREAS,
    DOMAIN,
)
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.climate import ClimateEntityFeature, HVACMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

PLATFORMS = ["climate"]


@pytest.mark.parametrize("platform", PLATFORMS)
@pytest.mark.usefixtures(
    "main_maximal", "room_sensors_w_humidity", "spaceheaters_expected"
)
async def test_setup_and_remove_config_entry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    platform: str,
    main_maximal,
    room_sensors_w_humidity,
    spaceheaters_expected,
) -> None:
    """Test setting up and removing a config entry."""
    data = main_maximal
    data["room_sensors"] = room_sensors_w_humidity
    data["room_appliances"] = spaceheaters_expected

    entity_ids = [f"{platform}.my_unistat_{room}" for room in data[CONF_AREAS]]
    friendly_names = [f"My UniStat {room}" for room in data[CONF_AREAS]]
    # Setup the config entry
    config_entry = MockConfigEntry(
        data=data,
        domain=DOMAIN,
        options={},
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the entities are registered in the entity registry

    common_attribs = {
        "current_temperature": None,
        "hvac_modes": (
            HVACMode.OFF,
            HVACMode.HEAT_COOL,
            HVACMode.AUTO,
        ),
        "max_temp": 29.4,
        "min_temp": 15.6,
        "target_temp_step": 1,
        "temperature": 22.2,
        "supported_features": (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        ),
    }

    for eid, friendly_name in zip(entity_ids, friendly_names):
        assert entity_registry.async_get(eid) is not None

        # Check the platform is setup correctly
        state = hass.states.get(eid)
        assert state.state == "off"
        expected_attributes = {**common_attribs, "friendly_name": friendly_name}
        assert state.attributes == expected_attributes

    # Remove the config entry
    assert await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the state and entity registry entry are removed
    for eid in entity_ids:
        assert hass.states.get(eid) is None
        assert entity_registry.async_get(eid) is None
