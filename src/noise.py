"""Noise and photon/electron conversion utilities.

The functions in this module keep units explicit:

- optical power is in watt
- current is in ampere
- bandwidth is in hertz
- wavelength is in meter
- temperature is in kelvin
"""

from __future__ import annotations

import numpy as np

Q_E = 1.602176634e-19
PLANCK = 6.62607015e-34
SPEED_OF_LIGHT = 299_792_458.0
BOLTZMANN = 1.380649e-23


def _as_array(value):
    return np.asarray(value, dtype=float)


def _require_nonnegative(name: str, value) -> None:
    if np.any(_as_array(value) < 0):
        raise ValueError(f"{name} must be non-negative")


def _require_positive(name: str, value) -> None:
    if np.any(_as_array(value) <= 0):
        raise ValueError(f"{name} must be positive")


def photon_energy(wavelength_m):
    """Return photon energy, E = h c / lambda."""

    _require_positive("wavelength_m", wavelength_m)
    return PLANCK * SPEED_OF_LIGHT / _as_array(wavelength_m)


def responsivity_from_qe(wavelength_m, quantum_efficiency):
    """Convert quantum efficiency to responsivity in A/W.

    R = eta q / (h nu) = eta q lambda / (h c)
    """

    _require_positive("wavelength_m", wavelength_m)
    _require_nonnegative("quantum_efficiency", quantum_efficiency)
    if np.any(_as_array(quantum_efficiency) > 1.0):
        raise ValueError("quantum_efficiency should be a fraction between 0 and 1")
    return _as_array(quantum_efficiency) * Q_E * _as_array(wavelength_m) / (
        PLANCK * SPEED_OF_LIGHT
    )


def optical_power_to_photocurrent(power_w, responsivity_a_per_w, gain=1.0):
    """Convert optical power to measured photocurrent."""

    _require_nonnegative("power_w", power_w)
    _require_nonnegative("responsivity_a_per_w", responsivity_a_per_w)
    _require_nonnegative("gain", gain)
    return _as_array(power_w) * _as_array(responsivity_a_per_w) * _as_array(gain)


def shot_noise_current_rms(current_a, bandwidth_hz, excess_noise_factor=1.0):
    """Shot-noise RMS current: sqrt(2 q I B F)."""

    _require_nonnegative("current_a", current_a)
    _require_nonnegative("bandwidth_hz", bandwidth_hz)
    _require_positive("excess_noise_factor", excess_noise_factor)
    return np.sqrt(
        2.0
        * Q_E
        * _as_array(current_a)
        * _as_array(bandwidth_hz)
        * _as_array(excess_noise_factor)
    )


def thermal_noise_current_rms(load_resistance_ohm, temperature_k, bandwidth_hz):
    """Johnson/Nyquist thermal-noise RMS current: sqrt(4 k_B T B / R)."""

    _require_positive("load_resistance_ohm", load_resistance_ohm)
    _require_positive("temperature_k", temperature_k)
    _require_nonnegative("bandwidth_hz", bandwidth_hz)
    return np.sqrt(
        4.0
        * BOLTZMANN
        * _as_array(temperature_k)
        * _as_array(bandwidth_hz)
        / _as_array(load_resistance_ohm)
    )


def total_rms_quadrature(*components):
    """Combine independent RMS noise terms in quadrature."""

    if not components:
        raise ValueError("At least one noise component is required")
    total = np.zeros_like(_as_array(components[0]), dtype=float)
    for component in components:
        _require_nonnegative("noise component", component)
        total = total + _as_array(component) ** 2
    return np.sqrt(total)


def snr_linear(signal, noise):
    """Return linear signal-to-noise ratio."""

    _require_nonnegative("signal", signal)
    _require_nonnegative("noise", noise)
    return _as_array(signal) / np.maximum(_as_array(noise), np.finfo(float).tiny)


def snr_db(signal, noise):
    """Return SNR in dB using 20 log10(signal/noise)."""

    return 20.0 * np.log10(np.maximum(snr_linear(signal, noise), np.finfo(float).tiny))


def quantization_noise_rms(full_scale_electrons, bit_depth):
    """ADC quantization noise in electrons RMS for a uniform quantizer."""

    _require_positive("full_scale_electrons", full_scale_electrons)
    if int(bit_depth) <= 0:
        raise ValueError("bit_depth must be positive")
    step_e = _as_array(full_scale_electrons) / (2**int(bit_depth) - 1)
    return step_e / np.sqrt(12.0)


def noise_equivalent_power(noise_current_a_per_sqrt_hz, responsivity_a_per_w):
    """Return NEP in W/sqrt(Hz)."""

    _require_nonnegative("noise_current_a_per_sqrt_hz", noise_current_a_per_sqrt_hz)
    _require_positive("responsivity_a_per_w", responsivity_a_per_w)
    return _as_array(noise_current_a_per_sqrt_hz) / _as_array(responsivity_a_per_w)
