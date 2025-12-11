import numpy as np
import numpy.typing as npt

from dataclasses import dataclass, asdict
from typing import Self, Final, Any
from types import MappingProxyType
from functools import cached_property

from .const import CONF_AREAS
from homeassistant.helpers.storage import Store


PARAM_VERSION: Final = 1


class UniStatModelParamsStore(Store):
    async def _async_migrate_func(self, old_major_version, old_minor_version, old_data):
        """Migrate to the new version."""
        raise NotImplementedError


@dataclass(frozen=True)
class UniStatModelParams:
    conf_data: dict[str, Any]
    estimate_internal_loads: bool
    radiator_rooms: list[str]
    thermal_lag: list[float]
    room_thermal_masses: list[float]
    thermal_resistances: list[float]
    heat_outputs: list[float]
    cooling_outputs: list[float]
    radiator_constants: list[float]
    boiler_thermal_masses: list[float]
    internal_loads: list[float]
    temp_variance: list[float]

    @cached_property
    def _tunable_fields(self) -> tuple[str]:
        """Returns list of fields that contain tunable parameters"""
        return (
            "thermal_lag",
            "room_thermal_masses",
            "thermal_resistances",
            "heat_outputs",
            "cooling_outputs",
            "boiler_thermal_masses",
            "radiator_constants",
            "internal_loads",
            "temp_variance",
        )

    @cached_property
    def _bounds_map(self) -> MappingProxyType[str, tuple[float, float]]:
        """Dict of fields and their corresponding valid ranges"""
        return MappingProxyType(
            {
                "thermal_lag": (3600 * 0.25, 3600 * 12),
                "room_thermal_masses": (100, 10000),
                "boiler_thermal_masses": (100, 2000),
                "thermal_resistances": (0, 2),
                "heat_outputs": (0.25, 10),
                "cooling_outputs": (-10, -0.25),
                "internal_loads": (0, 1),
                "radiator_constants": (0.001, 1),
                "temp_variance": (0, 3),
            }
        )

    def asdict(self) -> dict[str, Any]:
        return asdict(self)

    def from_vector(self, parameters: npt.NDArray) -> Self:
        """Take in an array and update the UniStatModelParams.

        The input parameters must match the size and ordering of the result of to_vector().
        """

        if parameters.shape != (self.num_params,):
            raise ValueError("provided parameters are the wrong shape.")

        data = self.asdict()

        first = 0
        for tf in self._tunable_fields:
            last = first + np.size(data[tf])
            data[tf] = parameters[first:last].tolist()
            first = last

        return UniStatModelParams(**data)

    def to_vector(self) -> npt.NDArray:
        """Pack tunable parameters into a single vector"""
        data = self.asdict()
        parameters = [data[tf] for tf in self._tunable_fields]
        return np.concat(parameters)

    @property
    def num_rooms(self) -> int:
        return len(self.conf_data[CONF_AREAS])

    @property
    def num_params(self) -> int:
        return self.to_vector().shape[0]

    @property
    def has_boiler(self) -> bool:
        return len(self.boiler_thermal_masses) > 0

    @property
    def adjacency_matrix(self) -> npt.NDArray:
        return np.array(self.conf_data["adjacency"])

    @property
    def param_bounds(self) -> npt.NDArray:
        """Provide optimization bounds for tunable parameters"""

        data = self.asdict()
        bounds_map = self._bounds_map

        constraints_list = []
        for tf in self._tunable_fields:
            constraints_list.extend([bounds_map[tf]] * len(data[tf]))

        return np.array(constraints_list)

    @property
    def in_bounds(self) -> bool:
        """Checks that all parameters are within bounds"""
        data = self.asdict()
        bounds_map = self._bounds_map

        for tf in self._tunable_fields:
            vals = np.array(data[tf])
            bounds = bounds_map[tf]
            if np.any((vals < bounds[0]) | (vals > bounds[1])):
                return False
        return True

    @property
    def self_consistent(self) -> bool:
        """Checks for self consistency of parameter sizes, does not check that parameters are in bounds"""
        interal_loads_consistent = len(self.internal_loads) == (
            self.num_rooms if self.estimate_internal_loads else 0
        )
        thermal_resistances_consistent = len(self.thermal_resistances) == np.sum(
            self.adjacency_matrix
        )
        room_masses_consistent = len(self.room_thermal_masses) == self.num_rooms

        # TODO Implement more checks

        return (
            self.valid_adjacency
            and interal_loads_consistent
            and thermal_resistances_consistent
            and room_masses_consistent
        )

    @property
    def valid_adjacency(self) -> bool:
        # Checks that an supplied adjacency matrix conforms to the expected form
        return self.is_valid_adjacency(self.adjacency_matrix, self.num_rooms)

    @staticmethod
    def is_valid_adjacency(adjacency_matrix: npt.ArrayLike, num_rooms: int):
        right_size = np.shape(adjacency_matrix) == (num_rooms + 1, num_rooms + 1)
        ones_and_zeros = np.all((adjacency_matrix == 0) | (adjacency_matrix == 1))
        upper_triangle = np.array_equal(np.triu(adjacency_matrix, 1), adjacency_matrix)
        return ones_and_zeros and upper_triangle and right_size
