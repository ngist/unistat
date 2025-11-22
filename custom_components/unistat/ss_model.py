import numpy as np

from typing import List, Optional

HEAT_CAPACITY_OF_WATER = 4.186  # kJ/(kg*K)c

DEFAULT_THERMAL_MASS = 1000  # TODO Put in reasonable value
DEFAULT_BOILER_MASS = 190 * HEAT_CAPACITY_OF_WATER  # This is 190L or 50gal of water
DEFAULT_RESISTANCE_OUTSIDE = 10  # TODO Put in reasonable value
DEFAULT_RESISTANCE_INSIDE = 1  # TODO Put in reasonable value


class UniStatSystemModel:
    def __init__(self):
        self.ss_model = None
        self.room_thermal_masses = np.array()
        self.boiler_thermal_masses = np.array()
        self.thermal_resistances = np.array()

    @staticmethod
    def valid_adjacency(adjacency_matrix) -> bool:
        ones_and_zeros = np.all((adjacency_matrix == 0) | (adjacency_matrix == 1))
        upper_triangle = np.array_equal(np.triu(adjacency_matrix, 1), adjacency_matrix)
        return ones_and_zeros and upper_triangle

    def initialize_model(
        self,
        num_rooms: int,
        thermal_appliance_entities: List[str],
        adjacency_matrix: Optional[List] = None,
        boiler_zone_entities: List[str] = None,
    ):
        self.room_thermal_masses = np.ones(num_rooms) * DEFAULT_THERMAL_MASS
        if len(boiler_zone_entities) > 0:
            self.boiler_thermal_masses = (
                np.ones(len(boiler_zone_entities))
                * DEFAULT_BOILER_MASS
                / len(boiler_zone_entities)
            )

        if adjacency_matrix is None:
            # If not specified assume all rooms are adjacent to the outside other and heat sharing between rooms doesn't happen.
            adjacency_matrix = np.zeros((num_rooms, num_rooms))
            adjacency_matrix[0, :] = np.ones(num_rooms)
            adjacency_matrix[0, 0] = 0

        assert self.valid_adjacency(adjacency_matrix)
        self.adjacency_matrix = adjacency_matrix

        outside_resistances = (
            np.ones(np.count_nonzero(adjacency_matrix[0, :]))
            * DEFAULT_RESISTANCE_OUTSIDE
        )
        inside_resistances = (
            np.ones(np.count_nonzero(adjacency_matrix[1:, :]))
            * DEFAULT_RESISTANCE_INSIDE
        )
        self.thermal_resistances = np.concatenate(
            outside_resistances, inside_resistances
        )
        assert np.shape(self.thermal_resistances)[0] == np.count_nonzero(
            adjacency_matrix
        )

        self.thermal_appliance_entities = thermal_appliance_entities
