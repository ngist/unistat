"""Unistat DataUpdateCoordinator."""

from datetime import timedelta
from dataclasses import dataclass
import logging


from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.storage import Store
from .const import DOMAIN, CONF_AREAS, CONF_CONTROLS, TITLE
from .thermal_model import UniStatModelParams, UniStatSystemModel

_LOGGER = logging.getLogger(__name__)


@dataclass
class UnistatData:
    """Data for the UniStat integration."""

    parameter_store: Store
    coordinator_learning: "UnistatLearningCoordinator"
    coordinator_control: "UnistatControlCoordinator"


type UnistatConfigEntry = ConfigEntry[UnistatData]


def _read_model_params() -> UniStatModelParams:
    return None


def _write_model_params(model_params: UniStatModelParams):
    pass


class UnistatControlCoordinator(DataUpdateCoordinator):
    """UniStat coordinator."""

    config_entry: UnistatConfigEntry

    def __init__(self, hass, config_entry):
        """Initialize coordinator."""
        self.device_info = _get_device_info()
        super().__init__(
            hass,
            _LOGGER,
            name="UniStat Control Coordinator",
            config_entry=config_entry,
            update_interval=timedelta(minutes=5),
            always_update=False,
        )

    @property
    def model_params(self):
        return self._model.model_params

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        model_params = _read_model_params()
        if model_params is None:
            model_params = UniStatSystemModel.initialize_state(self.config_entry.data)
        elif (
            model_params.rooms != self.config_entry.data[CONF_AREAS]
            or model_params.controls != self.config_entry.data[CONF_CONTROLS]
        ):
            # TODO update loaded model as needed to preserve learned constants.
            model_params = UniStatSystemModel.initialize_state(self.config_entry.data)

        self._model = UniStatSystemModel(model_params)

    async def async_update_model(self):
        return await self._async_setup()

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        pass


class UnistatLearningCoordinator(DataUpdateCoordinator):
    config_entry: UnistatConfigEntry

    def __init__(
        self,
        hass,
        config_entry: UnistatConfigEntry,
        controller: UnistatControlCoordinator,
    ):
        """Initialize coordinator."""
        self.device_info = _get_device_info()
        self._controller = controller
        super().__init__(
            hass,
            _LOGGER,
            name="UniStat Learning Coordinator",
            config_entry=config_entry,
            update_interval=timedelta(days=1),
            always_update=True,
        )

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        self._model_params = _read_model_params()

    async def _async_update_data(self):
        """Run the learning task to update model parameters"""

        _write_model_params(self._model_params)
        await self._controller.async_update_model()


def _get_device_info():
    return DeviceInfo(
        name=TITLE,
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN,)},
        # TODO sw_version=  add sw version info,
    )
