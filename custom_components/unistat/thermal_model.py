import numpy as np
import numpy.typing as npt
import logging

from typing import Any
from functools import cached_property

from .const import CONF_AREAS, CONF_CONTROLS, CONF_APPLIANCE_TYPE, ControlApplianceType
from .model_params import UniStatModelParams

_LOGGER = logging.getLogger(__name__)


class UniStatSystemModel:
    def __init__(
        self,
        config_data,
        model_params: UniStatModelParams | dict[str, Any] | None = None,
    ):
        # If no model params are provided initialize the model based on the config
        self._model_params = model_params
        if not self._model_params:
            _LOGGER.info("No model_params provided initializing from scratch")
            self._initialize_model_params(config_data=config_data)

        # Munge model parameters into the right type if they are not.
        if isinstance(self._model_params, dict):
            _LOGGER.info("Coercing model_params to UniStatModelParams")
            self._model_params = UniStatModelParams(**model_params)

        if not isinstance(self._model_params, UniStatModelParams):
            raise TypeError(
                f"model_params of type: {type(model_params)} is unexpected."
            )

        if config_data != self._model_params.conf_data:
            # TODO actually preserve data that can be preserved but for now just reinitialize
            _LOGGER.warning(
                "Mismatch between current config and config in model_params, reinitializing."
            )
            self._initialize_state(config_data=config_data)

        # self._ss_model = control.ss(self.A, self.B, self.C, self.D)

    def simulate(self, states, controls) -> tuple[npt.NDArray, npt.NDArray]:
        raise NotImplementedError

    def _initialize_model_params(
        self,
        config_data,
        estimate_internal_loads: bool = False,
    ) -> UniStatModelParams:
        """Generates a UniStatModelParams with default values based"""

        # CONSTANTS
        HEAT_CAPACITY_OF_WATER = 4.186  # kJ/(kg*K)
        UNINSULATED_U_FACTOR = 1.658  # W/(K m^2)
        THREE_WYTHE_BRICK_WALL = 7.381  # W/(k m^2)

        DEFAULT_THERMAL_MASS = 1000  # TODO Put in reasonable value
        DEFAULT_BOILER_MASS = (
            190 * HEAT_CAPACITY_OF_WATER
        )  # This is 190L or 50gal of water
        DEFAULT_RESISTANCE_OUTSIDE = (
            10 * THREE_WYTHE_BRICK_WALL / 1000
        )  # ~10sq meter 3 course brick wall
        DEFAULT_RESISTANCE_INSIDE = (
            10 * UNINSULATED_U_FACTOR / 1000
        )  # ~10sq meter separating drywall with no insulation
        DEFAULT_RADIATOR_CONSTANT = 0.03
        DEFAULT_THERMAL_LAG = 3600 * 6  # 6 hours

        rooms = config_data[CONF_AREAS]
        num_rooms = len(rooms)
        temp_variance = [0.0] * num_rooms
        room_thermal_masses = [DEFAULT_THERMAL_MASS] * num_rooms

        boiler_thermal_masses = []
        radiator_rooms = set()
        for c in config_data[CONF_CONTROLS]:
            control_app = config_data["control_appliances"][c]
            if control_app[CONF_APPLIANCE_TYPE] in [
                ControlApplianceType.BoilerZoneCall,
            ]:
                boiler_thermal_masses.append(DEFAULT_BOILER_MASS)
                radiator_rooms |= set(control_app[CONF_AREAS])

        radiator_rooms = list(radiator_rooms)
        radiator_constants = [DEFAULT_RADIATOR_CONSTANT]

        # TODO Populate heating and cooling outputs

        adjacency_matrix = np.array(config_data["adjacency"], dtype=bool)

        outside_resistances = [DEFAULT_RESISTANCE_OUTSIDE] * np.count_nonzero(
            adjacency_matrix[0, :]
        )
        inside_resistances = [DEFAULT_RESISTANCE_INSIDE] * np.count_nonzero(
            adjacency_matrix[1:, :]
        )
        thermal_resistances = outside_resistances + inside_resistances
        assert np.size(thermal_resistances) == np.count_nonzero(adjacency_matrix)

        internal_loads = [0] * num_rooms if estimate_internal_loads else []

        self._model_params = UniStatModelParams(
            conf_data=dict(config_data),
            estimate_internal_loads=estimate_internal_loads,
            room_thermal_masses=room_thermal_masses,
            thermal_resistances=thermal_resistances,
            boiler_thermal_masses=boiler_thermal_masses,
            radiator_rooms=radiator_rooms,
            radiator_constants=radiator_constants,
            internal_loads=internal_loads,
            temp_variance=temp_variance,
            thermal_lag=DEFAULT_THERMAL_LAG,
            heat_outputs=[],
            cooling_outputs=[],
        )

    @property
    def model_params(self):
        return self._model_params

    @cached_property
    def A(self):
        """Generates the A matrix based on system parameters"""

        # Only regenerate matrix if needed
        resistance_matrix = np.zeros_like(self.model_params.adjacency_matrix)
        resistance_matrix[self.model_params.adjacency_matrix] = (
            self.model_params.thermal_resistances
        )
        resistance_matrix = resistance_matrix + np.flip(resistance_matrix)

        # populate eye
        eye_vals = -np.sum(resistance_matrix, axis=0) * -1
        eye = np.eye(resistance_matrix.shape[0], dtype=bool)
        a = resistance_matrix
        a[eye] = eye_vals

        # First row is the outside, outside thermal mass is effectively infinite so zero the first row
        a[0, :] = np.zeros_like(a[0, :])

        if self.model_params.estimate_internal_loads:
            # If there's a load in the room then add a final column to include this static load
            a = np._c[a, self.model_params.internal_loads]

        # Divide the other rows by the thermal mass
        temp = a[1:, :].T / self.model_params.room_thermal_masses
        a[1:, :] = temp.T

        return a

    @cached_property
    def B(self):
        """Generates the B matrix based on system parameters."""

        num_rooms = len(self.model_params.rooms)
        num_controls = len(self.model_params.heat_outputs) + len(
            self.model_params.cooling_outputs
        )

        b = np.zeros_like((num_rooms + 1, num_controls))

        return b

    @cached_property
    def C(self):
        """Generates the C matrix based on system parameters."""
        return 1

    @cached_property
    def D(self):
        """Generates the D matrix based on system parameters."""
        return 0
