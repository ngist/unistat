"""The UniStat integration."""

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import (
    UnistatLearningCoordinator,
    UnistatControlCoordinator,
    UnistatData,
    UnistatConfigEntry,
)

PLATFORMS: tuple[Platform] = (Platform.CLIMATE, Platform.BINARY_SENSOR, Platform.SENSOR)


async def async_setup_entry(hass: HomeAssistant, entry: UnistatConfigEntry) -> bool:
    """Set up UniStat from a config entry."""

    control_coordinator = UnistatControlCoordinator(hass, entry)
    learning_coordinator = UnistatLearningCoordinator(hass, entry, control_coordinator)

    await asyncio.gather(
        control_coordinator.async_config_entry_first_refresh(),
        learning_coordinator.async_config_entry_first_refresh(),
    )

    entry.runtime_data = UnistatData(
        coordinator_control=control_coordinator,
        coordinator_learning=learning_coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
