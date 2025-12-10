"""Unistat DataUpdateCoordinator."""

from datetime import timedelta
from dataclasses import dataclass
import logging
from typing import Any, Optional
from collections import defaultdict


from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.storage import Store
from .const import DOMAIN, TITLE
from .thermal_model import UniStatModelParams, UniStatSystemModel

_LOGGER = logging.getLogger(__name__)


@dataclass
class UnistatData:
    """Data for the UniStat integration."""

    parameter_store: Store
    coordinator_learning: "UnistatLearningCoordinator"
    coordinator_control: "UnistatControlCoordinator"


type UnistatConfigEntry = ConfigEntry[UnistatData]


class UnistatCoordinator(DataUpdateCoordinator):
    """UniStat base coordinator."""

    config_entry: UnistatConfigEntry

    def __init__(
        self, hass, name: str, config_entry, update_interval: timedelta | None
    ):
        """Initialize coordinator."""
        self.data = defaultdict(lambda: "unknown")
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            config_entry=config_entry,
            update_interval=update_interval,
            always_update=False,
        )

    @property
    def device_info(self):
        return DeviceInfo(
            name=TITLE,
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN,)},
            # TODO sw_version=  add sw version info,
        )

    def _massage_parameters(self, model_params: Optional[dict[str, Any]]):
        """Handles non-existent model parameters, and config changes since parameters were last saved."""
        if model_params:
            model_params = UniStatModelParams.from_dict(model_params)
        else:
            model_params = UniStatSystemModel.initialize_state(self.config_entry.data)

        if self.config_entry.data != model_params.conf_data:
            model_params = model_params.migrate(self.config_entry.data)

        return model_params

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        self._entity_registry = er.async_get(self.hass)
        self._integration_entities = er.async_entries_for_config_entry(
            self._entity_registry, self.config_entry.entry_id
        )
        model_params = await self.config_entry.runtime_data.parameter_store.async_load()
        self._model_params = self._massage_parameters(model_params)
        self._model = UniStatSystemModel(self._model_params)


class UnistatControlCoordinator(UnistatCoordinator):
    """UniStat Control coordinator."""

    def __init__(self, hass, config_entry):
        """Initialize coordinator."""
        super().__init__(
            hass,
            name=f"{TITLE} Control Coordinator",
            config_entry=config_entry,
            update_interval=timedelta(minutes=5),
        )

    @property
    def model_params(self):
        return self._model.model_params

    async def async_update_model(self):
        return await self._async_setup()

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        self.data


class UnistatLearningCoordinator(UnistatCoordinator):
    """UniStat Learning coordinator."""

    def __init__(self, hass, config_entry):
        """Initialize coordinator."""
        super().__init__(
            hass,
            name=f"{TITLE} Learning Coordinator",
            config_entry=config_entry,
            update_interval=timedelta(days=1),
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        self.data
