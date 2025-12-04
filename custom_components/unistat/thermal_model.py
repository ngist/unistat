import control
import numpy as np
import numpy.typing as npt

from enum import Enum, auto
from typing import Dict, List, Optional, NamedTuple, Tuple, Self


class ParameterType(Enum):
    RadiatorConstant = auto()


class ApplianceType(Enum):
    InRoomAppliance = auto()
    Boiler = auto()
    HvacFurnace = auto()
    HvacCompressor = auto()


class ThermalAppliance(NamedTuple):
    entity_id: str
    appliance_type: ApplianceType
    variable_power: bool
    heating_power: float | None
    cooling_power: float | None
    monetary_cost: float
    carbon_cost: float
    rated_efficiency: float
    room_indexes: List[int]


class UniStatModelParams(NamedTuple):
    rooms: List[str]
    has_boiler: bool
    estimate_internal_loads: bool
    adjacency_matrix: npt.ArrayLike
    thermal_lag: npt.ArrayLike
    room_thermal_masses: npt.ArrayLike
    thermal_resistances: npt.ArrayLike
    heat_outputs: npt.ArrayLike
    cooling_outputs: npt.ArrayLike
    radiator_constants: npt.ArrayLike
    boiler_thermal_masses: npt.ArrayLike
    internal_loads: npt.ArrayLike
    temp_variance: npt.ArrayLike

    def from_params(self, parameters: npt.NDArray) -> Self:
        """Take in an array and return a new UniStatModelParams.

        The input parameters must match the size and ordering of the tunable_params property.
        Presumably those from a model fitting process.

        """
        data = self._asdict()

        first = 0
        for tf in self.tunable_fields:
            last = first + np.size(data[tf])
            data[tf] = parameters[first:last]
            first = last

        return UniStatModelParams(**data)

    def __eq__(self, value):
        """Check for equivalence"""
        if not isinstance(value, (UniStatModelParams)):
            return False
        other = value._asdict()
        me = self._asdict()
        result = True
        for k in me:
            if isinstance(me[k], (np.ndarray)):
                if not np.all(me[k] == other[k]):
                    result = False
            else:
                if me[k] != other[k]:
                    result = False
        return result

    @property
    def tunable_fields(self) -> List[str]:
        """Returns list of fields that contain tunable parameters"""
        return [
            "thermal_lag",
            "room_thermal_masses",
            "thermal_resistances",
            "heat_outputs",
            "cooling_outputs",
            "boiler_thermal_masses",
            "radiator_constants",
            "internal_loads",
            "temp_variance",
        ]

    @property
    def bounds_map(self) -> Dict[str, Tuple[float, float]]:
        """Dict of fields and their corresponding valid ranges"""
        return {
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

    @property
    def tunable_params(self) -> npt.NDArray:
        """Pack tunable parameters into a single vector"""

        data = self._asdict()

        parameters = []
        for tf in self.tunable_fields:
            parameters.append(data[tf])

        return np.concat(parameters)

    @property
    def param_bounds(self) -> npt.NDArray:
        """Provide optimization bounds for tunable parameters"""

        data = self._asdict()
        bounds_map = self.bounds_map

        constraints_list = []
        for tf in self.tunable_fields:
            constraints_list.extend([bounds_map[tf]] * np.size(data[tf]))

        return np.array(constraints_list)

    @property
    def self_consistent(self) -> bool:
        """Checks for self consistency of parameter sizes, does not check bounds"""
        interal_loads_consistent = self.internal_loads.shape == (
            (self.num_rooms,) if self.estimate_internal_loads else (0,)
        )
        thermal_resistances_consistent = self.thermal_resistances.shape == (
            np.sum(self.adjacency_matrix),
        )

        # TODO Implement more checks

        return (
            self.valid_adjacency
            and interal_loads_consistent
            and thermal_resistances_consistent
        )

    @property
    def in_bounds(self) -> bool:
        """Checks that all parameters are within bounds"""
        data = self._asdict()
        bounds_map = self.bounds_map

        for tf in self.tunable_fields:
            if np.any((data[tf] < bounds_map[tf][0]) | (data[tf] > bounds_map[tf][1])):
                print(f"{tf}: bound[{bounds_map[tf]}] data[{data[tf]}]")
                return False
        return True

    @property
    def num_rooms(self) -> int:
        return len(self.rooms)

    @property
    def valid_adjacency(self) -> bool:
        # Checks that an supplied adjacency matrix conforms to the expected form
        return self.is_valid_adjacency(self.adjacency_matrix, self.num_rooms)

    @staticmethod
    def is_valid_adjacency(adjacency_matrix: npt.NDArray, num_rooms: int):
        right_size = np.shape(adjacency_matrix) == (num_rooms + 1, num_rooms + 1)
        ones_and_zeros = np.all((adjacency_matrix == 0) | (adjacency_matrix == 1))
        upper_triangle = np.array_equal(np.triu(adjacency_matrix, 1), adjacency_matrix)
        return ones_and_zeros and upper_triangle and right_size


class UniStatSystemModel:
    def __init__(
        self,
        model_params: Optional[UniStatModelParams] = None,
    ):
        self._model_params = model_params
        self._a = None
        self._b = None
        self._c = None
        self._d = None

        self._update_model()

    @staticmethod
    def initialize_state(
        rooms: List[str],
        room_conf: List[Dict[str, List[int]]],
        adjacency_matrix: Optional[List] = None,
        boiler_zone_entities: List[str] = None,
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
        # DEFAULT_RADIATOR_CONSTANT = 0.03
        DEFAULT_THERMAL_LAG = 3600 * 6  # 6 hours

        # In kW
        # DEFAULT_HVAC_COOL = 1  # ~3500 BTU/hr
        # DEFAULT_HVAC_HEAT = 2  # ~7000 BTU/hr
        # DEFAULT_SPACEHEATER_HEAT = 1.5  # 1500 W
        # DEFAULT_HEATPUMP_COOLING = -3.5  # 12,000 BTU/hr
        # DEFAULT_HEATPUMP_HEATING = 4.22  # 14,400 BTU/hr
        # DEFAULT_CENTRAL_BOILER_HEAT = 41  # 140,000 BTU/hr

        num_rooms = len(rooms)
        temp_variance = np.zeros(num_rooms)
        room_thermal_masses = np.ones(num_rooms) * DEFAULT_THERMAL_MASS
        boiler_thermal_masses = np.array([])
        if len(boiler_zone_entities) > 0:
            has_boiler = True
            boiler_thermal_masses = (
                np.ones(len(boiler_zone_entities))
                * DEFAULT_BOILER_MASS
                / len(boiler_zone_entities)
            )

        if adjacency_matrix is None:
            # If not specified assume all rooms are adjacent to the outside and each other.
            adjacency_matrix = np.ones((num_rooms + 1, num_rooms + 1))
            adjacency_matrix = np.triu(adjacency_matrix, 1)
        else:
            adjacency_matrix = np.array(adjacency_matrix)
        assert UniStatSystemModel.valid_adjacency(adjacency_matrix)

        outside_resistances = (
            np.ones(np.count_nonzero(adjacency_matrix[0, :]))
            * DEFAULT_RESISTANCE_OUTSIDE
        )
        inside_resistances = (
            np.ones(np.count_nonzero(adjacency_matrix[1:, :]))
            * DEFAULT_RESISTANCE_INSIDE
        )
        thermal_resistances = np.concatenate(outside_resistances, inside_resistances)
        assert np.size(thermal_resistances) == np.count_nonzero(adjacency_matrix)

        internal_loads = np.array([])
        if estimate_internal_loads:
            internal_loads = np.zeros((1, num_rooms))

        room_conf = room_conf

        # #TODO
        # self.radiator_constants = np.ones()*DEFAULT_RADIATOR_CONSTANT
        # self.heat_outputs = np.ones()*DEFAULT_HVAC_HEAT
        # self.cooling_outputs = np.ones()*DEFAULT_HVAC_COOL

        # # for room in room_conf:

        # # self.radiator_indexes = list(radiator_rooms)
        # # self.radiator_costants = np.ones_like(self.radiator_indexes)*DEFAULT_RADIATOR_CONSTANT
        # # self.hvac_indexes = list(hvac_rooms)
        # # self.hvac_constants =

        return UniStatModelParams(
            rooms=rooms,
            has_boiler=has_boiler,
            estimate_internal_loads=estimate_internal_loads,
            adjacency_matrix=adjacency_matrix,
            room_thermal_masses=room_thermal_masses,
            boiler_thermal_masses=boiler_thermal_masses,
            internal_loads=internal_loads,
            temp_variance=temp_variance,
            thermal_lag=DEFAULT_THERMAL_LAG,
        )

    def _update_model(self):
        """Called after making updates to the model parameters to regenerate the model"""
        self._needs_update = True
        self._ss_model = control.ss(self.A, self.B, self.C, self.D)
        self._needs_update = False

    @property
    def A(self):
        """Generates the A matrix based on system parameters"""

        # Only regenerate matrix if needed
        if self._a and not self._needs_update:
            return self._a

        resistance_matrix = np.zeros_like(self.adjacency_matrix)
        resistance_matrix[self.adjacency_matrix] = self.thermal_resistances
        resistance_matrix = resistance_matrix + np.flip(resistance_matrix)

        # populate eye
        eye_vals = -np.sum(resistance_matrix, axis=0) * -1
        eye = np.eye(resistance_matrix.shape[0])
        a = resistance_matrix
        a[eye] = eye_vals

        # First row is the outside, outside thermal mass is effectively infinite so zero the first row
        a[0, :] = np.zeros_like(a[0, :])

        if self.estimate_internal_loads:
            # If there's a load in the room then add a final column to include this static load
            a = np._c[a, self.internal_loads]

        # Divide the other rows by the thermal mass
        a[1:, :] = a[1:, :] / self.room_thermal_masses

        self._a = a

        return self._a

    @property
    def B(self):
        """Generates the A matrix based on system parameters."""

        # Only regenerate matrix if needed
        if self._b and not self._needs_update:
            return self._b

        b = np.zeros_like((self.num_rooms + 1, len(self.thermal_appliances)))

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
