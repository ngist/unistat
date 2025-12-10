import pytest
import numpy as np

from custom_components.unistat.thermal_model import UniStatModelParams
from homeassistant.const import CONF_NAME


from .config_gen import (
    ConfigParams,
    make_expected,
    make_main_conf,
    make_multiroom_sensors,
    make_spaceheater,
    make_zonevalve,
    make_boiler,
)


def conf_simple():
    rooms = ["kitchen", "bedroom", "living_room"]
    controls = ["switch.spaceheater1", "switch.spaceheater2"]
    params = ConfigParams(
        main_conf=make_main_conf(rooms, controls),
        room_sensors=make_multiroom_sensors(rooms),
        room_appliances={
            c: make_spaceheater([rooms[i]]) for i, c in enumerate(controls)
        },
    )
    return make_expected(params)


MODEL_PARAMS_MIN = UniStatModelParams(
    conf_data=conf_simple(),
    estimate_internal_loads=False,
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 1500, 2000]),
    thermal_resistances=np.array([1, 1.5, 2]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([]),
    radiator_constants=np.array([]),
    internal_loads=np.array([]),
    temp_variance=np.array([0.1, 0.2]),
)


def conf_with_boiler():
    rooms = ["kitchen", "bedroom", "living_room"]
    controls = ["switch.zone1_valve", "switch.zone2_valve"]
    boiler = make_boiler()
    params = ConfigParams(
        main_conf=make_main_conf(rooms, controls),
        room_sensors=make_multiroom_sensors(rooms),
        room_appliances={
            c: make_zonevalve(
                [rooms[i]], central_appliance=(boiler[1][CONF_NAME] if i > 0 else None)
            )
            for i, c in enumerate(controls)
        },
        central_appliances=[boiler],
    )
    return make_expected(params)


MODEL_PARAMS_NO_LOADS = UniStatModelParams(
    conf_data=conf_with_boiler(),
    estimate_internal_loads=False,
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 1500, 2000]),
    thermal_resistances=np.array([1, 1.5, 2]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([100, 101]),
    radiator_constants=np.array([0.1, 0.2]),
    internal_loads=np.array([]),
    temp_variance=np.array([0.1, 0.2]),
)

MODEL_PARAMS_NO_BOILER = UniStatModelParams(
    conf_data=conf_simple(),
    estimate_internal_loads=True,
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 1500, 2000]),
    thermal_resistances=np.array([1, 1.5, 2]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([]),
    radiator_constants=np.array([]),
    internal_loads=np.array([0.3, 0.4, 0.5]),
    temp_variance=np.array([0.1, 0.2]),
)

MODEL_PARAMS_FULL = UniStatModelParams(
    conf_data=conf_with_boiler(),
    estimate_internal_loads=True,
    thermal_lag=np.array([3600 * 6]),
    room_thermal_masses=np.array([1000, 1500, 2000]),
    thermal_resistances=np.array([1, 1.5, 2]),
    heat_outputs=np.array([1.1, 2.1]),
    cooling_outputs=np.array([-1, -2]),
    boiler_thermal_masses=np.array([100, 101]),
    radiator_constants=np.array([0.1, 0.2]),
    internal_loads=np.array([0.3, 0.4, 0.5]),
    temp_variance=np.array([0.1, 0.2]),
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
        assert input.num_rooms == 3

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
            [[0, 1, 2], [0, 0, 1], [0, 0, 0]],  # Invalid value
            [[0, 1, 1], [1, 0, 1], [0, 0, 0]],  # Not upper triangular
            [[0, 1], [0, 0], [0, 0]],  # Invalid Shape
            [[1, 1, 1], [0, 0, 1], [0, 0, 0]],  # Has diagonal val
        ],
    )
    def test_valid_adjacency(self, adjacency):
        data = MODEL_PARAMS_FULL._asdict()
        data["conf_data"]["adjacency"] = adjacency
        mp = UniStatModelParams(**data)
        assert not mp.valid_adjacency
        assert not mp.self_consistent

    @pytest.mark.parametrize(
        "key,val",
        [
            ("internal_loads", np.array([0.1, 0.2])),
            ("thermal_resistances", np.array([1, 1.5, 2])),
        ],
    )
    def test_self_consistent(self, key, val):
        data = MODEL_PARAMS_FULL._asdict()
        data[key] = val
        mp = UniStatModelParams(**data)
        assert not mp.self_consistent
