import pytest
import numpy as np

from custom_components.unistat.thermal_model import UniStatModelParams


MODEL_PARAMS_MIN = UniStatModelParams(
    num_rooms=2,
    has_boiler=False,
    estimate_internal_loads=False,
    adjacency_matrix=np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]]),
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 2000]),
    thermal_resistances=np.array([1, 2, 3]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([]),
    radiator_constants=np.array([]),
    internal_loads=np.array([]),
)

MODEL_PARAMS_FULL = UniStatModelParams(
    num_rooms=2,
    has_boiler=True,
    estimate_internal_loads=True,
    adjacency_matrix=np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]]),
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 2000]),
    thermal_resistances=np.array([1, 2, 3]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([100, 101]),
    radiator_constants=np.array([0.1, 0.2]),
    internal_loads=np.array([3, 5]),
)

MODEL_PARAMS_NO_LOADS = UniStatModelParams(
    num_rooms=2,
    has_boiler=True,
    estimate_internal_loads=False,
    adjacency_matrix=np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]]),
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 2000]),
    thermal_resistances=np.array([1, 2, 3]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([100, 101]),
    radiator_constants=np.array([0.1, 0.2]),
    internal_loads=np.array([]),
)

MODEL_PARAMS_NO_BOILER = UniStatModelParams(
    num_rooms=2,
    has_boiler=False,
    estimate_internal_loads=True,
    adjacency_matrix=np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]]),
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 2000]),
    thermal_resistances=np.array([1, 2, 3]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([]),
    radiator_constants=np.array([]),
    internal_loads=np.array([3, 5]),
)


class TestUniStatModelParams:
    @pytest.mark.parametrize(
        "input",
        [
            MODEL_PARAMS_MIN,
            MODEL_PARAMS_NO_LOADS,
            MODEL_PARAMS_NO_BOILER,
            MODEL_PARAMS_FULL,
        ],
    )
    def test_tunable_params_roundtrip(self, input: UniStatModelParams):
        result = input.from_params(input.tunable_params)
        assert result == input
