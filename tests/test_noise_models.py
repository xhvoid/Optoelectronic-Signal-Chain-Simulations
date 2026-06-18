import numpy as np
import pytest

from src import noise


def test_responsivity_matches_qe_formula_and_scales_with_wavelength():
    wavelength = np.array([850e-9, 1550e-9])
    responsivity = noise.responsivity_from_qe(wavelength, 0.8)
    expected = 0.8 * noise.Q_E * wavelength / (noise.PLANCK * noise.SPEED_OF_LIGHT)
    assert np.allclose(responsivity, expected)
    assert responsivity[1] > responsivity[0]


def test_shot_noise_scales_with_sqrt_current_and_bandwidth():
    base = noise.shot_noise_current_rms(1e-6, 1e6)
    doubled_current_and_bandwidth = noise.shot_noise_current_rms(2e-6, 2e6)
    assert doubled_current_and_bandwidth == pytest.approx(2.0 * base)


def test_thermal_noise_scales_with_sqrt_bandwidth():
    base = noise.thermal_noise_current_rms(1_000.0, 300.0, 1e6)
    wide = noise.thermal_noise_current_rms(1_000.0, 300.0, 4e6)
    assert wide == pytest.approx(2.0 * base)


def test_total_rms_quadrature():
    assert noise.total_rms_quadrature(3.0, 4.0) == pytest.approx(5.0)


def test_quantization_noise_rejects_invalid_bit_depth():
    with pytest.raises(ValueError):
        noise.quantization_noise_rms(30_000, 0)
