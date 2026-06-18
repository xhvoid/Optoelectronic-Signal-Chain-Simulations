import numpy as np
import pytest

from src.detector import (
    CameraParams,
    LidarParams,
    PhotodetectorParams,
    camera_noise_budget,
    gaussian_mtf,
    lidar_return_energy,
    photodetector_noise_budget,
    photoelectrons_from_energy,
    resolving_power,
)


def test_photodetector_signal_current_is_linear_before_saturation():
    params = PhotodetectorParams(saturation_current_a=1.0, bandwidth_hz=1e6)
    powers = np.array([1e-9, 2e-9])
    budget = photodetector_noise_budget(powers, params, saturate=False)
    assert budget["signal_current_a"][1] == pytest.approx(2 * budget["signal_current_a"][0])


def test_photodetector_saturation_limits_signal_current():
    params = PhotodetectorParams(saturation_current_a=1e-6)
    budget = photodetector_noise_budget(np.array([1.0]), params, saturate=True)
    assert 0 < budget["signal_current_a"][0] <= params.saturation_current_a


def test_lidar_small_target_range_scaling_is_steeper_than_extended():
    params = LidarParams(beam_divergence_rad=10e-3, target_area_m2=0.01)
    near, far = 20.0, 40.0
    extended_ratio = lidar_return_energy(near, params) / lidar_return_energy(far, params)
    small_ratio = lidar_return_energy(near, params, model="small_target") / lidar_return_energy(
        far, params, model="small_target"
    )
    assert extended_ratio == pytest.approx(4.0)
    assert small_ratio > extended_ratio


def test_photoelectron_conversion_is_positive():
    params = LidarParams()
    electrons = photoelectrons_from_energy(1e-18, params.wavelength_m, 0.5)
    assert electrons > 0


def test_camera_dynamic_range_and_mtf_behave_reasonably():
    params = CameraParams(full_well_e=30_000, read_noise_e=3.0)
    budget = camera_noise_budget(np.array([1000.0]), 0.1, params)
    assert budget["dynamic_range_db"] == pytest.approx(80.0, rel=0.1)
    assert gaussian_mtf(0.0, 1.2) == pytest.approx(1.0)
    assert gaussian_mtf(0.5, 1.2) < gaussian_mtf(0.1, 1.2)


def test_resolving_power_accepts_vector_fwhm():
    fwhm = np.array([0.5, 1.0])
    assert np.allclose(resolving_power(650.0, fwhm), np.array([1300.0, 650.0]))
