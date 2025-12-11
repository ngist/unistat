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
    thermal_lag=[3600 * 6],
    room_thermal_masses=[1000, 1500, 2000],
    thermal_resistances=[1, 1.5, 2],
    heat_outputs=[1.1, 2.1],
    cooling_outputs=[-1, -2],
    boiler_thermal_masses=[],
    radiator_constants=[],
    internal_loads=[],
    temp_variance=[0.1, 0.2],
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
    thermal_lag=[3600 * 6],
    room_thermal_masses=[1000, 1500, 2000],
    thermal_resistances=[1, 1.5, 2],
    heat_outputs=[1.1, 2.1],
    cooling_outputs=[-1, -2],
    boiler_thermal_masses=[100, 101],
    radiator_constants=[0.1, 0.2],
    internal_loads=[],
    temp_variance=[0.1, 0.2],
)

MODEL_PARAMS_NO_BOILER = UniStatModelParams(
    conf_data=conf_simple(),
    estimate_internal_loads=True,
    thermal_lag=[3600 * 6],
    room_thermal_masses=[1000, 1500, 2000],
    thermal_resistances=[1, 1.5, 2],
    heat_outputs=[1.1, 2.1],
    cooling_outputs=[-1, -2],
    boiler_thermal_masses=[],
    radiator_constants=[],
    internal_loads=[0.3, 0.4, 0.5],
    temp_variance=[0.1, 0.2],
)

MODEL_PARAMS_FULL = UniStatModelParams(
    conf_data=conf_with_boiler(),
    estimate_internal_loads=True,
    thermal_lag=[3600 * 6],
    room_thermal_masses=[1000, 1500, 2000],
    thermal_resistances=[1, 1.5, 2],
    heat_outputs=[1.1, 2.1],
    cooling_outputs=[-1, -2],
    boiler_thermal_masses=[100, 101],
    radiator_constants=[0.1, 0.2],
    internal_loads=[0.3, 0.4, 0.5],
    temp_variance=[0.1, 0.2],
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
    def test_to_vector_roundtrip(self, input: UniStatModelParams):
        initial_vector = input.to_vector()
        final = input.from_vector(initial_vector)
        final_vector = final.to_vector()

        print(final.__eq__(input))
        assert final.__eq__(input)
        assert np.all(final_vector == initial_vector)

    def test_bounds_shape(self, input: UniStatModelParams):
        param_shape = input.to_vector().shape
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
        """Check that low bounds check is performed on each tunable parameter"""
        for i in range(len(MODEL_PARAMS_FULL.to_vector())):
            new_params = MODEL_PARAMS_FULL.to_vector()
            new_params[i] = -1e9
            obj = MODEL_PARAMS_FULL.from_vector(new_params)
            assert not obj.in_bounds

    def test_in_bounds_fail_high(self):
        """Check that high bounds check is performed on each tunable parameter"""
        for i in range(len(MODEL_PARAMS_FULL.to_vector())):
            new_params = MODEL_PARAMS_FULL.to_vector()
            new_params[i] = 1e9
            obj = MODEL_PARAMS_FULL.from_vector(new_params)
            assert not obj.in_bounds

    @pytest.mark.parametrize(
        "adjacency",
        [
            [[0, 1, 2, 1], [0, 0, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],  # Invalid value
            [
                [0, 1, 1, 0],
                [1, 0, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],  # Not upper triangular
            [[0, 1], [0, 0]],  # Invalid Shape
            [
                [1, 1, 1, 1],
                [0, 0, 1, 1],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],  # Has diagonal val
        ],
    )
    def test_valid_adjacency(self, adjacency):
        data = MODEL_PARAMS_FULL.asdict()
        data["conf_data"]["adjacency"] = adjacency
        mp = UniStatModelParams(**data)
        assert not mp.valid_adjacency
        assert not mp.self_consistent

    @pytest.mark.parametrize(
        "key,val",
        [
            ("internal_loads", [0.1, 0.2]),
            ("thermal_resistances", [1, 2]),
            ("room_thermal_masses", [1, 2]),
        ],
    )
    def test_self_consistent(self, key, val):
        data = MODEL_PARAMS_FULL.asdict()
        data[key] = val
        mp = UniStatModelParams(**data)
        assert not mp.self_consistent
