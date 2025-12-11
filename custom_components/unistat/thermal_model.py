import control
import numpy as np
import numpy.typing as npt
from dataclasses import dataclass, asdict
from typing import Self, Final, Any
from types import MappingProxyType
from functools import cached_property

from .const import CONF_AREAS, CONF_CONTROLS, CONF_APPLIANCE_TYPE, ControlApplianceType
from homeassistant.helpers.storage import Store

PARAM_VERSION: Final = 1


class UniStatModelParamsStore(Store):
    async def _async_migrate_func(self, old_major_version, old_minor_version, old_data):
        """Migrate to the new version."""
        raise NotImplementedError


@dataclass(eq=True)
class UniStatModelParams:
    conf_data: dict[str, Any]
    estimate_internal_loads: bool
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

        parameters = []
        for tf in self._tunable_fields:
            parameters.append(data[tf])

        return np.concat(parameters)

    @property
    def num_rooms(self) -> int:
        return len(self.conf_data[CONF_AREAS])

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


class UniStatSystemModel:
    def __init__(
        self,
        config_data,
        model_params: UniStatModelParams | dict[str, Any] | None = None,
    ):
        self._a = None
        self._b = None
        self._c = None
        self._d = None

        # If no model params are provided initialize the model based on the config
        if not model_params:
            self._initialize_model_params(config_data=config_data)
            # self._update_model()
            return

        # Munge model parameters into the right type if they are not.
        if isinstance(model_params, dict):
            model_params = UniStatModelParams.fromdict(model_params)

        if not isinstance(model_params, UniStatModelParams):
            raise TypeError(
                f"model_params of type: {type(model_params)} is unexpected."
            )

        # If config data has changed update the model parameters based on the new config while preserving existing data
        if config_data != model_params.conf_data:
            # TODO actually preserve data for now just reinitialize
            self._initialize_state(config_data=config_data)
            # self._update_model()
            return

    def _initialize_model_params(
        self,
        config_data,
        estimate_internal_loads: bool = False,
    ) -> UniStatModelParams:
        """Generates a UniStatModelParams with default values"""

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

        # In kW
        # DEFAULT_HVAC_COOL = 1  # ~3500 BTU/hr
        # DEFAULT_HVAC_HEAT = 2  # ~7000 BTU/hr
        # DEFAULT_SPACEHEATER_HEAT = 1.5  # 1500 W
        # DEFAULT_HEATPUMP_COOLING = -3.5  # 12,000 BTU/hr
        # DEFAULT_HEATPUMP_HEATING = 4.22  # 14,400 BTU/hr
        # DEFAULT_CENTRAL_BOILER_HEAT = 41  # 140,000 BTU/hr

        rooms = config_data[CONF_AREAS]
        num_rooms = len(rooms)
        temp_variance = [0.0] * num_rooms
        room_thermal_masses = [DEFAULT_THERMAL_MASS] * num_rooms

        boiler_thermal_masses = []
        radiator_constants = []
        for c in config_data[CONF_CONTROLS]:
            control_app = config_data["control_appliances"][c]
            if control_app[CONF_APPLIANCE_TYPE] in [
                ControlApplianceType.BoilerZoneCall,
                ControlApplianceType.ThermoStaticRadiatorValve,
            ]:
                boiler_thermal_masses.append(DEFAULT_BOILER_MASS)
                radiator_constants.append(DEFAULT_RADIATOR_CONSTANT)

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
            boiler_thermal_masses=boiler_thermal_masses,
            thermal_resistances=thermal_resistances,
            radiator_constants=radiator_constants,
            internal_loads=internal_loads,
            temp_variance=temp_variance,
            thermal_lag=DEFAULT_THERMAL_LAG,
            heat_outputs=[],
            cooling_outputs=[],
        )

    def _update_model(self):
        """Called after making updates to the model parameters to regenerate the model"""
        self._needs_update = True
        self._ss_model = control.ss(self.A, self.B, self.C, self.D)
        self._needs_update = False

    @property
    def model_params(self):
        return self._model_params

    @property
    def A(self):
        """Generates the A matrix based on system parameters"""

        # Only regenerate matrix if needed
        if self._a and not self._needs_update:
            return self._a

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
        self._a = a

        return self._a

    @property
    def B(self):
        """Generates the A matrix based on system parameters."""

        # Only regenerate matrix if needed
        if self._b and not self._needs_update:
            return self._b

        num_rooms = len(self.model_params.rooms)
        num_controls = len(self.model_params.heat_outputs) + len(
            self.model_params.cooling_outputs
        )

        b = np.zeros_like((num_rooms + 1, num_controls))

        self._b = b
        return self._b

    @property
    def C(self):
        """Generates the C matrix based on system parameters."""
        return 1

    @property
    def D(self):
        """Generates the D matrix based on system parameters."""
        return 0
