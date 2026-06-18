"""Laser diode optical, thermal, and wavelength-drift models."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LaserDiodeParams:
    """Compact laser diode model parameters."""

    threshold_current_ref_a: float = 35e-3
    threshold_reference_temp_k: float = 298.15
    characteristic_temp_k: float = 55.0
    slope_efficiency_w_per_a: float = 0.85
    center_wavelength_m: float = 785e-9
    wavelength_reference_temp_k: float = 298.15
    wavelength_temp_coeff_m_per_k: float = 0.28e-9
    series_voltage_v: float = 2.1
    thermal_resistance_k_per_w: float = 18.0
    thermal_capacitance_j_per_k: float = 7.0


def threshold_current(temp_k, params: LaserDiodeParams):
    """Temperature-dependent threshold current.

    Uses the common engineering form:
    I_th(T) = I_th(T_ref) exp((T - T_ref) / T0)
    """

    return params.threshold_current_ref_a * np.exp(
        (np.asarray(temp_k, dtype=float) - params.threshold_reference_temp_k)
        / params.characteristic_temp_k
    )


def output_power(drive_current_a, temp_k, params: LaserDiodeParams):
    """Laser output power above threshold."""

    current = np.asarray(drive_current_a, dtype=float)
    ith = threshold_current(temp_k, params)
    return params.slope_efficiency_w_per_a * np.maximum(current - ith, 0.0)


def wavelength(temp_k, params: LaserDiodeParams):
    """Temperature-induced wavelength drift."""

    return params.center_wavelength_m + params.wavelength_temp_coeff_m_per_k * (
        np.asarray(temp_k, dtype=float) - params.wavelength_reference_temp_k
    )


def electrical_heat(drive_current_a, temp_k, params: LaserDiodeParams):
    """Approximate heat load from electrical input minus optical output."""

    electrical_w = params.series_voltage_v * np.asarray(drive_current_a, dtype=float)
    optical_w = output_power(drive_current_a, temp_k, params)
    return np.maximum(electrical_w - optical_w, 0.0)


def simulate_free_running_temperature(
    time_s,
    drive_current_a,
    environment_temp_k,
    params: LaserDiodeParams,
    initial_temp_k=None,
):
    """Simulate laser package temperature without active cooling."""

    t = np.asarray(time_s, dtype=float)
    if t.ndim != 1 or len(t) < 2:
        raise ValueError("time_s must be a 1D array with at least two samples")
    if np.any(np.diff(t) <= 0):
        raise ValueError("time_s must be strictly increasing")

    current = np.broadcast_to(np.asarray(drive_current_a, dtype=float), t.shape)
    env = np.broadcast_to(np.asarray(environment_temp_k, dtype=float), t.shape)
    temp = np.empty_like(t)
    temp[0] = env[0] if initial_temp_k is None else initial_temp_k

    for idx in range(1, len(t)):
        dt = t[idx] - t[idx - 1]
        heat_w = electrical_heat(current[idx - 1], temp[idx - 1], params)
        cooling_w = (temp[idx - 1] - env[idx - 1]) / params.thermal_resistance_k_per_w
        dtemp_dt = (heat_w - cooling_w) / params.thermal_capacitance_j_per_k
        temp[idx] = temp[idx - 1] + dtemp_dt * dt

    return temp
