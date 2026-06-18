"""Control-system utilities for optoelectronic thermal simulations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class PIDController:
    """Discrete PID controller.

    The input to ``update`` is an already-defined error signal. For TEC cooling
    examples in this project, error = measured_temperature - setpoint, so a
    positive output means positive cooling power.
    """

    kp: float
    ki: float = 0.0
    kd: float = 0.0
    output_limits: tuple[float, float] = (-np.inf, np.inf)
    integral_limits: tuple[float, float] = (-np.inf, np.inf)

    def __post_init__(self):
        self.integral = 0.0
        self.previous_error = None

    def reset(self):
        self.integral = 0.0
        self.previous_error = None

    def update(self, error, dt):
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.integral = np.clip(
            self.integral + error * dt, self.integral_limits[0], self.integral_limits[1]
        )
        derivative = 0.0 if self.previous_error is None else (error - self.previous_error) / dt
        self.previous_error = error
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        return float(np.clip(output, self.output_limits[0], self.output_limits[1]))


def _profile(values, shape):
    arr = np.asarray(values, dtype=float)
    return np.broadcast_to(arr, shape)


def simulate_tec_temperature(
    time_s,
    setpoint_k,
    environment_temp_k,
    heat_load_w,
    thermal_resistance_k_per_w,
    thermal_capacitance_j_per_k,
    controller: PIDController | None = None,
    initial_temp_k=None,
):
    """Simulate first-order package temperature with optional TEC cooling."""

    t = np.asarray(time_s, dtype=float)
    if t.ndim != 1 or len(t) < 2:
        raise ValueError("time_s must be a 1D array with at least two samples")
    if np.any(np.diff(t) <= 0):
        raise ValueError("time_s must be strictly increasing")
    if thermal_resistance_k_per_w <= 0 or thermal_capacitance_j_per_k <= 0:
        raise ValueError("thermal resistance and capacitance must be positive")

    setpoint = _profile(setpoint_k, t.shape)
    env = _profile(environment_temp_k, t.shape)
    heat = _profile(heat_load_w, t.shape)
    temp = np.empty_like(t)
    control_w = np.zeros_like(t)
    temp[0] = env[0] if initial_temp_k is None else initial_temp_k

    if controller is not None:
        controller.reset()

    for idx in range(1, len(t)):
        dt = t[idx] - t[idx - 1]
        if controller is not None:
            error = temp[idx - 1] - setpoint[idx - 1]
            control_w[idx - 1] = controller.update(error, dt)
        passive_w = (temp[idx - 1] - env[idx - 1]) / thermal_resistance_k_per_w
        dtemp_dt = (heat[idx - 1] - control_w[idx - 1] - passive_w) / thermal_capacitance_j_per_k
        temp[idx] = temp[idx - 1] + dtemp_dt * dt

    control_w[-1] = control_w[-2]
    return {"time_s": t, "temperature_k": temp, "control_power_w": control_w}


def steady_state_error(response, target):
    """Final sample minus target."""

    return float(np.asarray(response, dtype=float)[-1] - target)


def overshoot(response, target):
    """Maximum positive excursion above target."""

    return float(max(0.0, np.max(np.asarray(response, dtype=float) - target)))


def settling_time(time_s, response, target, tolerance):
    """Return first time after which response stays within target +/- tolerance."""

    t = np.asarray(time_s, dtype=float)
    y = np.asarray(response, dtype=float)
    within = np.abs(y - target) <= tolerance
    for idx in range(len(t)):
        if np.all(within[idx:]):
            return float(t[idx])
    return np.nan
