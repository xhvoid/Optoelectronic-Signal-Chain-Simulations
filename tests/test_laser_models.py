import numpy as np
import pytest

from src.control import PIDController, simulate_tec_temperature, steady_state_error
from src.laser import LaserDiodeParams, output_power, threshold_current, wavelength


def test_threshold_current_increases_with_temperature():
    params = LaserDiodeParams()
    cold = threshold_current(293.15, params)
    hot = threshold_current(313.15, params)
    assert hot > cold


def test_output_power_is_zero_below_threshold():
    params = LaserDiodeParams()
    ith = threshold_current(298.15, params)
    assert output_power(0.5 * ith, 298.15, params) == pytest.approx(0.0)


def test_wavelength_drift_matches_temperature_coefficient():
    params = LaserDiodeParams(wavelength_temp_coeff_m_per_k=0.3e-9)
    drift = wavelength(308.15, params) - wavelength(298.15, params)
    assert drift == pytest.approx(3.0e-9)


def test_pid_control_reduces_steady_state_error():
    time_s = np.linspace(0, 80, 801)
    no_control = simulate_tec_temperature(
        time_s, 298.15, 298.15, 1.2, 18.0, 7.0, controller=None, initial_temp_k=298.15
    )
    pid = PIDController(kp=0.25, ki=0.04, kd=0.0, output_limits=(0.0, 3.0))
    controlled = simulate_tec_temperature(
        time_s, 298.15, 298.15, 1.2, 18.0, 7.0, controller=pid, initial_temp_k=298.15
    )
    assert abs(steady_state_error(controlled["temperature_k"], 298.15)) < abs(
        steady_state_error(no_control["temperature_k"], 298.15)
    )
