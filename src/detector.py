"""Detector, LiDAR, camera, and spectrometer helper models."""

from __future__ import annotations

from dataclasses import dataclass
from math import erfc

import numpy as np

from . import noise


@dataclass(frozen=True)
class PhotodetectorParams:
    """Parameters for a photodiode or APD signal-chain model."""

    wavelength_m: float = 850e-9
    quantum_efficiency: float = 0.78
    bandwidth_hz: float = 10e6
    load_resistance_ohm: float = 1_000.0
    temperature_k: float = 300.0
    dark_current_a: float = 1e-9
    read_noise_current_a: float = 0.0
    saturation_current_a: float = 4e-3
    apd_gain: float = 1.0
    apd_excess_noise_factor: float = 1.0

    @property
    def primary_responsivity_a_per_w(self) -> float:
        return float(noise.responsivity_from_qe(self.wavelength_m, self.quantum_efficiency))

    @property
    def effective_responsivity_a_per_w(self) -> float:
        return self.apd_gain * self.primary_responsivity_a_per_w


def soft_saturate_current(current_a, saturation_current_a):
    """Smoothly limit current to mimic amplifier or detector saturation."""

    if saturation_current_a <= 0:
        raise ValueError("saturation_current_a must be positive")
    current = np.asarray(current_a, dtype=float)
    return saturation_current_a * (1.0 - np.exp(-current / saturation_current_a))


def photodetector_noise_budget(power_w, params: PhotodetectorParams, saturate: bool = True):
    """Return signal and noise components for an optical detector."""

    power = np.asarray(power_w, dtype=float)
    if np.any(power < 0):
        raise ValueError("power_w must be non-negative")

    primary_signal_a = noise.optical_power_to_photocurrent(
        power, params.primary_responsivity_a_per_w
    )
    ideal_output_signal_a = params.apd_gain * primary_signal_a
    if saturate:
        signal_a = soft_saturate_current(ideal_output_signal_a, params.saturation_current_a)
    else:
        signal_a = ideal_output_signal_a

    signal_shot_a = params.apd_gain * noise.shot_noise_current_rms(
        primary_signal_a, params.bandwidth_hz, params.apd_excess_noise_factor
    )
    dark_shot_scalar_a = params.apd_gain * noise.shot_noise_current_rms(
        params.dark_current_a, params.bandwidth_hz, params.apd_excess_noise_factor
    )
    thermal_scalar_a = noise.thermal_noise_current_rms(
        params.load_resistance_ohm, params.temperature_k, params.bandwidth_hz
    )
    dark_shot_a = np.zeros_like(signal_a) + dark_shot_scalar_a
    thermal_a = np.zeros_like(signal_a) + thermal_scalar_a
    read_a = np.zeros_like(signal_a) + params.read_noise_current_a
    total_a = noise.total_rms_quadrature(signal_shot_a, dark_shot_a, thermal_a, read_a)

    return {
        "primary_signal_current_a": primary_signal_a,
        "ideal_output_signal_current_a": ideal_output_signal_a,
        "signal_current_a": signal_a,
        "shot_noise_current_a": signal_shot_a,
        "dark_noise_current_a": dark_shot_a,
        "thermal_noise_current_a": thermal_a,
        "read_noise_current_a": read_a,
        "total_noise_current_a": total_a,
        "snr_linear": noise.snr_linear(signal_a, total_a),
        "snr_db": noise.snr_db(signal_a, total_a),
    }


def photodetector_snr(power_w, params: PhotodetectorParams, saturate: bool = True):
    """Convenience wrapper returning detector SNR in linear units."""

    return photodetector_noise_budget(power_w, params, saturate=saturate)["snr_linear"]


@dataclass(frozen=True)
class LidarParams:
    """Pulsed ToF LiDAR link-budget parameters."""

    wavelength_m: float = 905e-9
    pulse_energy_j: float = 20e-9
    aperture_diameter_m: float = 25e-3
    receiver_efficiency: float = 0.45
    detector_quantum_efficiency: float = 0.65
    beam_divergence_rad: float = 2.0e-3
    target_reflectivity: float = 0.25
    target_area_m2: float = 0.1
    atmospheric_transmission: float = 0.95


def lidar_return_energy(range_m, params: LidarParams, model: str = "diffuse_extended"):
    """Estimate returned pulse energy.

    ``diffuse_extended`` follows an R^-2 scaling for a large Lambertian target.
    ``small_target`` adds target interception by the expanding beam, which tends
    toward R^-4 when the target is smaller than the beam footprint.
    """

    ranges = np.asarray(range_m, dtype=float)
    if np.any(ranges <= 0):
        raise ValueError("range_m must be positive")

    aperture_area = np.pi * (params.aperture_diameter_m / 2.0) ** 2
    receiver_solid_angle_factor = aperture_area / (np.pi * ranges**2)
    two_way_atmosphere = params.atmospheric_transmission**2

    if model == "diffuse_extended":
        intercept = 1.0
    elif model == "small_target":
        beam_radius = np.maximum(ranges * params.beam_divergence_rad / 2.0, 1e-12)
        beam_area = np.pi * beam_radius**2
        intercept = np.minimum(params.target_area_m2 / beam_area, 1.0)
    else:
        raise ValueError("model must be 'diffuse_extended' or 'small_target'")

    return (
        params.pulse_energy_j
        * intercept
        * params.target_reflectivity
        * receiver_solid_angle_factor
        * params.receiver_efficiency
        * two_way_atmosphere
    )


def photoelectrons_from_energy(energy_j, wavelength_m, quantum_efficiency):
    """Convert collected optical energy to detected photoelectrons."""

    photons = np.asarray(energy_j, dtype=float) / noise.photon_energy(wavelength_m)
    return photons * quantum_efficiency


def _normal_survival(z):
    vectorized_erfc = np.vectorize(erfc)
    return 0.5 * vectorized_erfc(np.asarray(z, dtype=float) / np.sqrt(2.0))


def gaussian_threshold_detection(signal_electrons, noise_sigma_electrons, thresholds_electrons):
    """Return detection and false-alarm probabilities for Gaussian thresholding."""

    if noise_sigma_electrons <= 0:
        raise ValueError("noise_sigma_electrons must be positive")
    signal = np.asarray(signal_electrons, dtype=float)
    thresholds = np.asarray(thresholds_electrons, dtype=float)
    false_alarm = _normal_survival(thresholds / noise_sigma_electrons)
    detection = _normal_survival((thresholds - signal[..., None]) / noise_sigma_electrons)
    return {
        "thresholds_electrons": thresholds,
        "false_alarm_probability": false_alarm,
        "detection_probability": detection,
    }


@dataclass(frozen=True)
class CameraParams:
    """CMOS/CCD sensor parameters in electron-domain units."""

    quantum_efficiency: float = 0.62
    dark_current_e_per_s: float = 0.8
    read_noise_e: float = 2.2
    full_well_e: float = 30_000.0
    bit_depth: int = 12
    prnu_fraction: float = 0.01
    hot_pixel_fraction: float = 0.001
    hot_pixel_dark_current_e_per_s: float = 100.0


def camera_noise_budget(signal_electrons, exposure_s, params: CameraParams):
    """Return camera noise terms and SNR for a signal level."""

    signal = np.asarray(signal_electrons, dtype=float)
    if np.any(signal < 0):
        raise ValueError("signal_electrons must be non-negative")
    if exposure_s <= 0:
        raise ValueError("exposure_s must be positive")

    dark_scalar_e = params.dark_current_e_per_s * exposure_s
    dark_e = np.zeros_like(signal) + dark_scalar_e
    shot_e = np.sqrt(signal)
    dark_noise_e = np.sqrt(dark_e)
    read_e = np.zeros_like(signal) + params.read_noise_e
    quant_e = noise.quantization_noise_rms(params.full_well_e, params.bit_depth)
    total_e = noise.total_rms_quadrature(shot_e, dark_noise_e, read_e, quant_e)
    snr = noise.snr_linear(np.minimum(signal, params.full_well_e), total_e)

    return {
        "signal_electrons": signal,
        "dark_electrons": dark_e,
        "shot_noise_e": shot_e,
        "dark_noise_e": dark_noise_e,
        "read_noise_e": read_e,
        "quantization_noise_e": np.zeros_like(signal) + quant_e,
        "total_noise_e": total_e,
        "snr_linear": snr,
        "snr_db": noise.snr_db(np.minimum(signal, params.full_well_e), total_e),
        "dynamic_range_db": 20.0 * np.log10(params.full_well_e / params.read_noise_e),
    }


def simulate_camera_frame(photon_rate_per_pixel_s, exposure_s, params: CameraParams, seed=1):
    """Simulate a noisy camera frame from a photon-rate image."""

    rng = np.random.default_rng(seed)
    photon_rate = np.asarray(photon_rate_per_pixel_s, dtype=float)
    if np.any(photon_rate < 0):
        raise ValueError("photon_rate_per_pixel_s must be non-negative")

    signal_mean_e = params.quantum_efficiency * photon_rate * exposure_s
    dark_rate = np.zeros_like(signal_mean_e) + params.dark_current_e_per_s

    if params.hot_pixel_fraction > 0:
        hot_mask = rng.random(signal_mean_e.shape) < params.hot_pixel_fraction
        dark_rate = np.where(hot_mask, params.hot_pixel_dark_current_e_per_s, dark_rate)
    else:
        hot_mask = np.zeros(signal_mean_e.shape, dtype=bool)

    prnu = rng.normal(1.0, params.prnu_fraction, signal_mean_e.shape)
    signal_e = rng.poisson(np.maximum(signal_mean_e * prnu, 0.0))
    dark_e = rng.poisson(np.maximum(dark_rate * exposure_s, 0.0))
    read_e = rng.normal(0.0, params.read_noise_e, signal_mean_e.shape)

    electrons = np.clip(signal_e + dark_e + read_e, 0.0, params.full_well_e)
    max_adu = 2**params.bit_depth - 1
    adu = np.round(electrons / params.full_well_e * max_adu).astype(int)
    return {
        "electrons": electrons,
        "adu": adu,
        "hot_pixel_mask": hot_mask,
        "signal_mean_e": signal_mean_e,
    }


def gaussian_mtf(spatial_frequency_cycles_per_pixel, sigma_pixels):
    """MTF of a Gaussian PSF: exp(-2 pi^2 sigma^2 f^2)."""

    if sigma_pixels < 0:
        raise ValueError("sigma_pixels must be non-negative")
    frequency = np.asarray(spatial_frequency_cycles_per_pixel, dtype=float)
    return np.exp(-2.0 * (np.pi * sigma_pixels * frequency) ** 2)


def grating_diffraction_angle(
    wavelength_m, groove_density_lines_per_m, incidence_angle_rad=0.0, order=1
):
    """Return diffraction angle from m lambda = d(sin alpha + sin beta)."""

    if groove_density_lines_per_m <= 0:
        raise ValueError("groove_density_lines_per_m must be positive")
    spacing_m = 1.0 / groove_density_lines_per_m
    sin_beta = order * np.asarray(wavelength_m, dtype=float) / spacing_m - np.sin(
        incidence_angle_rad
    )
    if np.any(np.abs(sin_beta) > 1.0):
        raise ValueError("No real diffraction angle for the provided parameters")
    return np.arcsin(sin_beta)


def gaussian_peak(x, amplitude, center, sigma, baseline=0.0):
    """Gaussian peak with area-like amplitude convention."""

    if sigma <= 0:
        raise ValueError("sigma must be positive")
    x_arr = np.asarray(x, dtype=float)
    return baseline + amplitude * np.exp(-0.5 * ((x_arr - center) / sigma) ** 2)


def lorentzian_peak(x, amplitude, center, gamma, baseline=0.0):
    """Lorentzian peak model."""

    if gamma <= 0:
        raise ValueError("gamma must be positive")
    x_arr = np.asarray(x, dtype=float)
    return baseline + amplitude * gamma**2 / ((x_arr - center) ** 2 + gamma**2)


def resolving_power(wavelength_nm, fwhm_nm):
    """Spectrometer resolving power R = lambda / delta-lambda."""

    fwhm = np.asarray(fwhm_nm, dtype=float)
    if np.any(fwhm <= 0):
        raise ValueError("fwhm_nm must be positive")
    return np.asarray(wavelength_nm, dtype=float) / fwhm
