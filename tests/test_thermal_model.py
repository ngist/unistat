import pytest
import numpy as np

from custom_components.unistat.thermal_model import UniStatModelParams


MODEL_PARAMS_MIN = UniStatModelParams(
    rooms=["living_room", "kitchen"],
    has_boiler=False,
    estimate_internal_loads=False,
    adjacency_matrix=np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]]),
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 2000]),
    thermal_resistances=np.array([1, 1.5, 2]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([]),
    radiator_constants=np.array([]),
    internal_loads=np.array([]),
)

MODEL_PARAMS_FULL = UniStatModelParams(
    rooms=["living_room", "kitchen"],
    has_boiler=True,
    estimate_internal_loads=True,
    adjacency_matrix=np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]]),
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 2000]),
    thermal_resistances=np.array([1, 1.5, 2]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([100, 101]),
    radiator_constants=np.array([0.1, 0.2]),
    internal_loads=np.array([0.3, 0.5]),
)

MODEL_PARAMS_NO_LOADS = UniStatModelParams(
    rooms=["living_room", "kitchen"],
    has_boiler=True,
    estimate_internal_loads=False,
    adjacency_matrix=np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]]),
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 2000]),
    thermal_resistances=np.array([1, 1.5, 2]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([100, 101]),
    radiator_constants=np.array([0.1, 0.2]),
    internal_loads=np.array([]),
)

MODEL_PARAMS_NO_BOILER = UniStatModelParams(
    rooms=["living_room", "kitchen"],
    has_boiler=False,
    estimate_internal_loads=True,
    adjacency_matrix=np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]]),
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 2000]),
    thermal_resistances=np.array([1, 1.5, 2]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([]),
    radiator_constants=np.array([]),
    internal_loads=np.array([0.3, 0.5]),
)


@pytest.mark.parametrize(
    "input",
    [
        MODEL_PARAMS_MIN,
        MODEL_PARAMS_NO_LOADS,
        MODEL_PARAMS_NO_BOILER,
        MODEL_PARAMS_FULL,
    ],
)
class TestUniStatModelParams_Nominal:
    def test_tunable_params_roundtrip(self, input: UniStatModelParams):
        result = input.from_params(input.tunable_params)
        assert result == input

    def test_bounds_shape(self, input: UniStatModelParams):
        param_shape = input.tunable_params.shape
        bounds_shape = input.param_bounds.shape
        assert param_shape[0] == bounds_shape[0]
        assert bounds_shape[1] == 2

    def test_bounds_finite(self, input: UniStatModelParams):
        assert np.all(np.isfinite(input.param_bounds))

    def test_self_consistent(self, input: UniStatModelParams):
        assert input.self_consistent

    def test_in_bounds(self, input: UniStatModelParams):
        assert input.in_bounds

    def test_num_rooms(self, input: UniStatModelParams):
        assert input.num_rooms == 2

    def test_valid_adjacency(self, input: UniStatModelParams):
        assert input.valid_adjacency


class TestUniStatModelParams_OffNominal:
    def test_in_bounds_fail_low(self):
        orig_params = MODEL_PARAMS_FULL.tunable_params
        for i in range(len(orig_params)):
            new_params = MODEL_PARAMS_FULL.tunable_params
            new_params[i] = -1e9
            new_obj = MODEL_PARAMS_FULL.from_params(new_params)
            assert not new_obj.in_bounds

    def test_in_bounds_fail_high(self):
        orig_params = MODEL_PARAMS_FULL.tunable_params
        for i in range(len(orig_params)):
            new_params = MODEL_PARAMS_FULL.tunable_params
            new_params[i] = 1e9
            new_obj = MODEL_PARAMS_FULL.from_params(new_params)
            assert not new_obj.in_bounds

    @pytest.mark.parametrize(
        "adjacency",
        [
            np.array([[0, 1, 2], [0, 0, 1], [0, 0, 0]]),  # Invalid value
            np.array([[0, 1, 1], [1, 0, 1], [0, 0, 0]]),  # Not upper triangular
            np.array([[0, 1], [0, 0], [0, 0]]),  # Invalid Shape
            np.array([[1, 1, 1], [0, 0, 1], [0, 0, 0]]),  # Has diagonal val
        ],
    )
    def test_valid_adjacency(self, adjacency):
        data = MODEL_PARAMS_FULL._asdict()
        data["adjacency_matrix"] = adjacency
        mp = UniStatModelParams(**data)
        assert not mp.valid_adjacency
        assert not mp.self_consistent

    @pytest.mark.parametrize(
        "key,val",
        [
            ("internal_loads", np.array([0.1, 0.2, 0.3])),
            ("thermal_resistances", np.array([1, 1.5])),
        ],
    )
    def test_self_consistent(self, key, val):
        data = MODEL_PARAMS_FULL._asdict()
        data[key] = val
        mp = UniStatModelParams(**data)
        assert not mp.self_consistent
