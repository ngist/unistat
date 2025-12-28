import numpy as np
import numpy.typing as npt
import logging

from dataclasses import dataclass, asdict
from typing import Final, Any
from types import MappingProxyType
from functools import cached_property
from collections import defaultdict

from homeassistant.helpers.storage import Store
from homeassistant.util.unit_conversion import PowerConverter
from homeassistant.const import CONF_NAME, CONF_UNIT_OF_MEASUREMENT, UnitOfPower

from .const import (
    CONF_AREAS,
    HVAC_PERIPHERALS,
    ControlApplianceType,
    CentralApplianceType,
    CONF_CONTROLS,
    CONF_APPLIANCE_TYPE,
    CONF_COOLING_POWER,
    CONF_HEATING_POWER,
    CONF_CENTRAL_APPLIANCE,
    CONF_CONTROL_APPLIANCES,
    CONF_CENTRAL_APPLIANCES,
)

_LOGGER = logging.getLogger(__name__)

PARAM_VERSION: Final = 1


class UniStatModelParamsStore(Store):
    async def _async_migrate_func(self, old_major_version, old_minor_version, old_data):
        """Migrate to the new version."""
        raise NotImplementedError


@dataclass(frozen=True)
class UniStatModelParams:
    conf_data: MappingProxyType[str, Any]
    estimate_internal_loads: bool
    radiator_rooms: list[str]
    thermal_lag: list[float]
    room_thermal_masses: list[float]
    thermal_resistances: list[float]
    radiator_constants: list[float]
    hvac_vent_constants: list[float]
    boiler_thermal_masses: list[float]
    internal_loads: list[float]

    @cached_property
    def _tunable_fields(self) -> tuple[str]:
        """Returns list of fields that contain tunable parameters"""
        return (
            "thermal_lag",
            "room_thermal_masses",
            "thermal_resistances",
            "hvac_vent_constants",
            "boiler_thermal_masses",
            "radiator_constants",
            "internal_loads",
        )

    @cached_property
    def _non_constant_fields(self) -> tuple[str]:
        """Returns list of fields that contain time-varying parameters"""
        return ("internal_loads",)

    @cached_property
    def _bounds_map(self) -> MappingProxyType[str, tuple[float, float]]:
        """Dict of fields and their corresponding valid ranges"""
        return MappingProxyType(
            {
                "thermal_lag": (3600 * 0.25, 3600 * 12),
                "room_thermal_masses": (100, 10000),
                "boiler_thermal_masses": (100, 2000),
                "hvac_vent_constants": (0, 1),
                "thermal_resistances": (0, 2),
                "heat_outputs": (0.25, 10),
                "cooling_outputs": (-10, -0.25),
                "internal_loads": (0, 1),
                "radiator_constants": (0.001, 1),
            }
        )

    def asdict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_conf(
        config_data: MappingProxyType, estimate_internal_loads: bool = False
    ) -> "UniStatModelParams":
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
        room_thermal_masses = [DEFAULT_THERMAL_MASS] * num_rooms

        # Massage config data into a more usable format

        boiler_thermal_masses = []
        radiator_constants = []
        radiator_rooms = []
        central_appliances = UniStatModelParams._central_appliances(config_data)
        for ca in central_appliances:
            if ca[CONF_APPLIANCE_TYPE] == CentralApplianceType.HydroBoiler:
                # There is one boiler thermal mass for each zone on each boiler
                boiler_thermal_masses.append([DEFAULT_BOILER_MASS] * ca["num_zones"])
                radiator_constants.append(
                    [DEFAULT_RADIATOR_CONSTANT] * ca["num_fixtures"]
                )
                radiator_rooms.append([])
                for z in ca["zone_map"]:
                    radiator_rooms[-1] = radiator_rooms[-1] + z
                radiator_rooms[-1] = radiator_rooms[-1] + ca["common_rooms"]

        hvac_vent_constants = []
        hvac_system = UniStatModelParams._coalesce_hvac(config_data, central_appliances)
        for z in hvac_system:
            hvac_vent_constants.append([1 / z["num_rooms"]] * z["num_rooms"])

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

        return UniStatModelParams(
            conf_data=dict(config_data),
            estimate_internal_loads=estimate_internal_loads,
            room_thermal_masses=room_thermal_masses,
            thermal_resistances=thermal_resistances,
            boiler_thermal_masses=boiler_thermal_masses,
            radiator_rooms=radiator_rooms,
            radiator_constants=radiator_constants,
            internal_loads=internal_loads,
            thermal_lag=DEFAULT_THERMAL_LAG,
            hvac_vent_constants=hvac_vent_constants,
        )

    @cached_property
    def standalone_appliances(self) -> dict[ControlApplianceType, dict[str, Any]]:
        """Returns a dict of dicts keyed by ControlApplianceType then control_eid"""
        out = defaultdict(list)
        for c, app in zip(
            self.conf_data[CONF_CONTROLS], self.conf_data[CONF_CONTROL_APPLIANCES]
        ):
            if CONF_CENTRAL_APPLIANCE not in app:
                app_type = app[CONF_APPLIANCE_TYPE]
                new_app = {**app, CONF_CONTROLS: c}
                UniStatModelParams._standardize_power(new_app)
                out[app_type].append(new_app)
        return dict(out)

    @cached_property
    def central_appliances(self):
        return self._central_appliances(self.conf_data)

    @staticmethod
    def _central_appliances(conf_data):
        central_appliances = UniStatModelParams._organize_central_appliances(conf_data)
        central_appliances = UniStatModelParams._add_central_appliance_metadata(
            central_appliances
        )
        for ca in central_appliances:
            UniStatModelParams._standardize_power(ca)
        return central_appliances

    @staticmethod
    def _organize_central_appliances(config_data) -> list[dict[str, Any]]:
        """Returns a list of central appliances and their peripheral appliances

        ex:
        result = [
            {
                CONF_NAME: "boiler",
                CONF_APPLIANCE_TYPE: CentralApplianceType.HydroBoiler
                CONF_CONTROLS: [
                    {
                        CONF_CONTROLS: "switch.boiler_zone1",
                        CONF_APPLIANCE_TYPE: ControlApplianceType.BoilerZoneCall,
                        CONF_AREAS: ["living_room", "kitchen"],
                        CONF_CENTRAL_APPLIANCE: "boiler",
                        ...
                    },
                    ...
                ]
                CONF_EFFICIENCY: 80,
                ...
            },
            ...
        ]
        """
        control_lists = defaultdict(list)
        for c, app in zip(
            config_data[CONF_CONTROLS], config_data["control_appliances"]
        ):
            if CONF_CENTRAL_APPLIANCE in app:
                control_lists[app[CONF_CENTRAL_APPLIANCE]].append(
                    {**app, CONF_CONTROLS: c}
                )

        central_appliances = []
        for k in config_data[CONF_CENTRAL_APPLIANCES]:
            if k[CONF_NAME] in control_lists:
                central_appliances.append(
                    {**k, CONF_CONTROLS: control_lists[k[CONF_NAME]]}
                )
            else:
                _LOGGER.error("Central Appliance: %s has no controls.", k[CONF_NAME])

        return central_appliances

    @staticmethod
    def _add_central_appliance_metadata(central_appliances: list[dict[str, Any]]):
        central_appliances = list(central_appliances)
        for i, ca in enumerate(central_appliances):
            match ca[CONF_APPLIANCE_TYPE]:
                case (
                    CentralApplianceType.HydroBoiler
                    | CentralApplianceType.HvacHeatpump
                    | CentralApplianceType.HvacCompressor
                    | CentralApplianceType.HvacFurnace
                ):
                    central_appliances[i] = (
                        UniStatModelParams._add_zoned_appliance_metadata(ca)
                    )
                case CentralApplianceType.MiniSplitHeatpump:
                    central_appliances[i] = UniStatModelParams._add_minisplit_metadata(
                        ca
                    )
                case _:
                    _LOGGER.error(
                        "Error unrecognized CentralApplianceType: %s",
                        ca[CONF_APPLIANCE_TYPE],
                    )
        return central_appliances

    @staticmethod
    def _add_zoned_appliance_metadata(appliance: dict) -> dict:
        """Adds metadata to a boiler config"""
        # Figure out how rooms are organized within zones
        rooms = [set(app[CONF_AREAS]) for app in appliance[CONF_CONTROLS]]

        # First find rooms that are heated on any zone call. These are called common rooms
        common_rooms = set(rooms[0])
        for r in rooms:
            common_rooms &= r

        # Next find rooms that are zone specific
        zone_specific_rooms = [list(r - common_rooms) for r in rooms]

        # Compute number of logical radiators or vents tied to this appliance
        # NOTE this need not be equal to the physical number of radiators, for instance if there
        # are two radiators in a room on the same zone that can't be controlled independently then it can be modeled as one radiator.
        num_fixtures = int(
            np.sum([len(z) for z in zone_specific_rooms]) + len(common_rooms)
        )

        # Check if rooms other than the common rooms are on more than one zone
        for i, r in enumerate(zone_specific_rooms):
            for j, r in enumerate(zone_specific_rooms):
                if i != j:
                    overlaping_rooms = set(zone_specific_rooms[i]) & set(
                        zone_specific_rooms[j]
                    )
                    if overlaping_rooms:
                        _LOGGER.info(
                            "%s has zones %s and %s with non-common overlapping rooms. This is probably not correct",
                            appliance[CONF_NAME],
                            appliance[CONF_CONTROLS][i][CONF_CONTROLS],
                            appliance[CONF_CONTROLS][j][CONF_CONTROLS],
                        )

        return {
            **appliance,
            "num_zones": len(appliance[CONF_CONTROLS]),
            "num_fixtures": num_fixtures,
            "has_common_rooms": len(common_rooms) > 0,
            "common_rooms": list(common_rooms),
            "zone_map": [list(r) for r in rooms],
        }

    @staticmethod
    def _add_minisplit_metadata(minisplit: dict) -> dict:
        return {**minisplit}

    @staticmethod
    def _standardize_power(appliance: dict) -> dict:
        update_vals = {}
        if CONF_HEATING_POWER in appliance:
            update_vals[CONF_HEATING_POWER] = PowerConverter.convert(
                appliance[CONF_HEATING_POWER],
                appliance[CONF_UNIT_OF_MEASUREMENT],
                UnitOfPower.WATT,
            )
            update_vals[CONF_UNIT_OF_MEASUREMENT] = UnitOfPower.WATT
        if CONF_COOLING_POWER in appliance:
            update_vals[CONF_COOLING_POWER] = PowerConverter.convert(
                appliance[CONF_COOLING_POWER],
                appliance[CONF_UNIT_OF_MEASUREMENT],
                UnitOfPower.WATT,
            )
        appliance.update(update_vals)

    @staticmethod
    def _coalesce_hvac(config_data, central_appliances) -> list:
        zones = defaultdict(list)
        for c, app in zip(
            config_data[CONF_CONTROLS], config_data[CONF_CONTROL_APPLIANCES]
        ):
            if app[CONF_APPLIANCE_TYPE] in HVAC_PERIPHERALS:
                zones[set(app[CONF_AREAS])].append({**app, CONF_CONTROLS: c})

        out = []
        for z in zones:
            zone_app_types = [app[CONF_APPLIANCE_TYPE] for app in zones[z]]
            controls = [app[CONF_CONTROLS] for app in zones[z]]
            err_prefix = "An HVAC zone can have either a single climate control or a heat call, a cool call or both."
            too_many_controls = len(zone_app_types) > 2
            too_many_controls |= len(zone_app_types) == 2 and set(
                zone_app_types
            ) != set(
                ControlApplianceType.HVACCoolCall, ControlApplianceType.HVACHeatCall
            )
            if too_many_controls:
                _LOGGER.error(
                    "%s\n\tRooms: %s, are controlled by %s",
                    err_prefix,
                    str(z),
                    str(zip(controls, zone_app_types)),
                )
                raise ValueError(
                    "%s\n\tRooms: %s, are controlled by %s",
                    err_prefix,
                    str(z),
                    str(zip(controls, zone_app_types)),
                )

            centrals = [app[CONF_CENTRAL_APPLIANCE] for app in zones[z]]
            central_appliances = {ca[CONF_NAME]: ca for ca in central_appliances}

            def get_power_field(field):
                field_vals = [
                    (
                        central_appliances[name][field],
                        central_appliances[name][CONF_UNIT_OF_MEASUREMENT],
                    )
                    for name in centrals
                    if field in central_appliances[name]
                ]
                if not field_vals:
                    return None
                result = field_vals[0]
                return PowerConverter.convert(result[0], result[1], UnitOfPower.WATT)

            out.append(
                {
                    CONF_AREAS: list(z),
                    "num_rooms": len(list(z)),
                    CONF_CONTROLS: controls,
                    CONF_APPLIANCE_TYPE: zone_app_types,
                    CONF_HEATING_POWER: get_power_field(CONF_HEATING_POWER),
                    CONF_COOLING_POWER: get_power_field(CONF_COOLING_POWER),
                }
            )

        return out

    def from_vector(self, parameters: npt.NDArray) -> "UniStatModelParams":
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
