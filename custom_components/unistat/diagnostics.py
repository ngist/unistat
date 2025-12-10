"""Diagnostics support for UniStat."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .coordinator import UnistatConfigEntry, UnistatData

TO_REDACT = {}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: UnistatConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    unistat_data: UnistatData = config_entry.runtime_data

    return {
        "config_entry_data": async_redact_data(dict(config_entry.data), TO_REDACT),
        "runtime_data": {
            "learning": unistat_data.coordinator_learning.data,
            "control": unistat_data.coordinator_control.data,
        },
    }
