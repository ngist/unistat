"""The UniStat integration."""

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from .thermal_model import PARAM_VERSION, UniStatModelParamsEncoder
from .const import DOMAIN

from .coordinator import (
    UnistatLearningCoordinator,
    UnistatControlCoordinator,
    UnistatData,
    UnistatConfigEntry,
)

PLATFORMS: tuple[Platform] = (Platform.CLIMATE, Platform.BINARY_SENSOR, Platform.SENSOR)


async def async_setup_entry(hass: HomeAssistant, entry: UnistatConfigEntry) -> bool:
    """Set up UniStat from a config entry."""

    parameter_store = Store(
        hass,
        version=PARAM_VERSION,
        key=f"{DOMAIN}/model_params",
        encoder=UniStatModelParamsEncoder(),
    )
    control_coordinator = UnistatControlCoordinator(hass, entry)
    learning_coordinator = UnistatLearningCoordinator(hass, entry, control_coordinator)

    entry.runtime_data = UnistatData(
        parameter_store=parameter_store,
        coordinator_control=control_coordinator,
        coordinator_learning=learning_coordinator,
    )

    # Parameter store is needed by the controllers so set it up first
    await parameter_store.async_load()

    await asyncio.gather(
        control_coordinator.async_config_entry_first_refresh(),
        learning_coordinator.async_config_entry_first_refresh(),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
