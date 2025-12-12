import numpy as np
import numpy.typing as npt
import logging

from typing import Any
from functools import cached_property


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
            self._model_params = UniStatModelParams.from_conf(config_data)

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
            self._model_params = UniStatModelParams.from_conf(config_data)

        # self._ss_model = control.ss(self.A, self.B, self.C, self.D)

    def simulate(self, states, controls) -> tuple[npt.NDArray, npt.NDArray]:
        raise NotImplementedError

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
