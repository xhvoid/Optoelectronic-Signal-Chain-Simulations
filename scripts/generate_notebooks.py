"""Generate the portfolio demonstration notebooks."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"


def md(text: str):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text: str):
    return nbf.v4.new_code_cell(text.strip())


SETUP = r"""
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path.cwd().resolve()
if not (PROJECT_ROOT / "src").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src import plotting

plotting.set_style()
FIG_DIR = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)
"""


def write_notebook(filename: str, cells: list):
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, NOTEBOOK_DIR / filename)


def photodetector_notebook():
    cells = [
        md(
            r"""
# 01 - Photodetector / APD / SNR / Bandwidth Simulation

This notebook models an optical detector signal chain from photons to current,
then adds the dominant current-noise sources used in photonics test, optical
sensing, laser diagnostics, and imaging front-end design.
"""
        ),
        code(SETUP + "\nfrom src import noise\nfrom src.detector import PhotodetectorParams, photodetector_noise_budget"),
        md(
            r"""
## 1. Engineering Problem

Design a detector front end that can measure weak optical signals while keeping
enough bandwidth for the application. The practical questions are:

- What photocurrent is produced by a given optical power?
- Which noise source dominates at low, medium, and high power?
- How much optical power is needed for a target SNR?
- How does electrical bandwidth trade against SNR?
- Where does saturation invalidate the linear detector model?
"""
        ),
        md(
            r"""
## 2. Physical Assumptions

- Responsivity follows `R = eta q lambda / (h c)` before avalanche gain.
- Photocurrent is linear in optical power until front-end saturation.
- Shot, thermal, dark-current, and read-noise terms are independent RMS currents.
- The electrical noise bandwidth is approximated by the measurement bandwidth.
- APD gain multiplies signal current, while avalanche excess noise is represented
  by an excess-noise factor `F`.
- Saturation is modeled with a smooth current clamp to show the failure regime.
"""
        ),
        md(
            r"""
## 3. System Parameters

The values below are representative of a fast silicon detector or APD readout.
They are not tied to a specific vendor part; the point is to expose the scaling
laws that drive detector selection and front-end design.
"""
        ),
        code(
            r"""
params = PhotodetectorParams(
    wavelength_m=850e-9,
    quantum_efficiency=0.78,
    bandwidth_hz=20e6,
    load_resistance_ohm=1_000.0,
    temperature_k=300.0,
    dark_current_a=2e-9,
    read_noise_current_a=0.25e-9,
    saturation_current_a=1.5e-3,
    apd_gain=1.0,
    apd_excess_noise_factor=1.0,
)

pd.DataFrame(
    [
        ("wavelength_m", params.wavelength_m, "m", "Operating wavelength; sets photon energy and responsivity."),
        ("quantum_efficiency", params.quantum_efficiency, "fraction", "Fraction of incident photons producing collected carriers."),
        ("bandwidth_hz", params.bandwidth_hz, "Hz", "Equivalent electrical noise bandwidth of the receiver."),
        ("load_resistance_ohm", params.load_resistance_ohm, "ohm", "Transimpedance/load resistance setting Johnson current noise."),
        ("temperature_k", params.temperature_k, "K", "Physical temperature for thermal noise."),
        ("dark_current_a", params.dark_current_a, "A", "Leakage current contributing shot noise."),
        ("read_noise_current_a", params.read_noise_current_a, "A RMS", "Input-referred electronics/readout noise."),
        ("saturation_current_a", params.saturation_current_a, "A", "Soft current limit of detector or amplifier."),
        ("apd_gain", params.apd_gain, "x", "Avalanche gain; 1.0 means PIN diode mode."),
    ],
    columns=["parameter", "value", "unit", "engineering meaning"],
)
"""
        ),
        md(
            r"""
## 4. Simulation Model

The first conversion is optical power to photocurrent:

`I_ph = R P_opt`, where `R = eta q lambda / (h c)`.

Longer wavelength photons carry less energy, so the same quantum efficiency gives
higher A/W responsivity at longer wavelength until the material bandgap cuts off.
"""
        ),
        code(
            r"""
wavelength_nm = np.linspace(400, 1_100, 300)
qe_values = [0.45, 0.65, 0.85]

fig, ax = plt.subplots()
for qe in qe_values:
    ax.plot(
        wavelength_nm,
        noise.responsivity_from_qe(wavelength_nm * 1e-9, qe),
        label=f"QE = {qe:.0%}",
    )
ax.set_xlabel("Wavelength (nm)")
ax.set_ylabel("Responsivity (A/W)")
ax.set_title("Responsivity from quantum efficiency")
ax.legend()
plotting.save_figure(fig, FIG_DIR / "01_responsivity_vs_wavelength.png")
plt.show()
"""
        ),
        code(
            r"""
power_w = np.logspace(-12, -2, 500)
qe_scan = [0.4, 0.6, 0.8]

fig, ax = plt.subplots()
for qe in qe_scan:
    r = noise.responsivity_from_qe(params.wavelength_m, qe)
    ax.loglog(power_w, noise.optical_power_to_photocurrent(power_w, r), label=f"QE={qe:.0%}")
ax.set_xlabel("Optical power (W)")
ax.set_ylabel("Photocurrent (A)")
ax.set_title("Optical power to photocurrent")
ax.legend()
plt.show()
"""
        ),
        md(
            r"""
## 5. Noise / Uncertainty Model

The RMS current-noise terms are:

- Shot noise: `i_shot = sqrt(2 q I B)`
- Thermal noise: `i_thermal = sqrt(4 k_B T B / R_L)`
- Dark-current noise: same shot-noise form using dark current
- Read/electronics noise: input-referred RMS current

Independent current noises add in quadrature:

`i_total = sqrt(i_shot^2 + i_thermal^2 + i_dark^2 + i_read^2)`.
"""
        ),
        code(
            r"""
budget = photodetector_noise_budget(power_w, params)

fig, ax = plt.subplots()
ax.loglog(power_w, budget["shot_noise_current_a"], label="signal shot")
ax.loglog(power_w, budget["thermal_noise_current_a"], label="thermal")
ax.loglog(power_w, budget["dark_noise_current_a"], label="dark shot")
ax.loglog(power_w, budget["read_noise_current_a"], label="read")
ax.loglog(power_w, budget["total_noise_current_a"], "k", lw=2, label="total")
ax.set_xlabel("Optical power (W)")
ax.set_ylabel("RMS noise current (A)")
ax.set_title("Detector noise budget")
ax.legend()
plotting.save_figure(fig, FIG_DIR / "01_noise_budget.png")
plt.show()
"""
        ),
        code(
            r"""
fig, ax = plt.subplots()
ax.semilogx(power_w, budget["snr_db"], lw=2)
ax.axhline(20, color="0.35", ls="--", label="20 dB target")
ax.set_xlabel("Optical power (W)")
ax.set_ylabel("SNR (dB)")
ax.set_title("SNR versus optical power")
plotting.add_regime_spans(
    ax,
    [
        (1e-12, 2e-8, "thermal/read limited", "tab:blue"),
        (2e-8, 2e-4, "shot-noise limited", "tab:green"),
        (2e-4, 1e-2, "saturation limited", "tab:red"),
    ],
)
ax.legend(loc="lower right")
plt.show()
"""
        ),
        md(
            r"""
## 6. Parameter Scan

Bandwidth is often the most painful detector trade-off. Increasing bandwidth
raises shot and thermal noise as `sqrt(B)`, so SNR drops even if optical power is
unchanged.
"""
        ),
        code(
            r"""
bandwidths = np.array([1e6, 5e6, 20e6, 100e6])
fig, ax = plt.subplots()
for bandwidth in bandwidths:
    p = PhotodetectorParams(**{**params.__dict__, "bandwidth_hz": bandwidth})
    b = photodetector_noise_budget(power_w, p)
    ax.semilogx(power_w, b["snr_db"], label=f"{bandwidth/1e6:g} MHz")
ax.axhline(20, color="0.35", ls="--")
ax.set_xlabel("Optical power (W)")
ax.set_ylabel("SNR (dB)")
ax.set_title("Bandwidth penalty in detector SNR")
ax.legend(title="Bandwidth")
plt.show()
"""
        ),
        code(
            r"""
power_grid = np.logspace(-11, -4, 160)
bandwidth_grid = np.logspace(5, 8, 120)
snr_grid = np.empty((len(bandwidth_grid), len(power_grid)))

for i, bandwidth in enumerate(bandwidth_grid):
    p = PhotodetectorParams(**{**params.__dict__, "bandwidth_hz": bandwidth})
    snr_grid[i] = photodetector_noise_budget(power_grid, p)["snr_db"]

fig, ax = plt.subplots(figsize=(8, 5))
mesh = ax.pcolormesh(power_grid, bandwidth_grid / 1e6, snr_grid, shading="auto", cmap="viridis")
contours = ax.contour(power_grid, bandwidth_grid / 1e6, snr_grid, levels=[10, 20, 30, 40], colors="white", linewidths=0.8)
ax.clabel(contours, fmt="%d dB", fontsize=8)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Optical power (W)")
ax.set_ylabel("Bandwidth (MHz)")
ax.set_title("SNR design map")
fig.colorbar(mesh, ax=ax, label="SNR (dB)")
plt.show()
"""
        ),
        md(
            r"""
## 7. Failure Regime

Two failures matter in real measurements:

- Low-power failure: signal is below the noise floor, so SNR is below the target.
- High-power failure: the detector or transimpedance amplifier saturates, so the
  current no longer scales linearly with optical power.
"""
        ),
        code(
            r"""
rows = []
for bandwidth in bandwidths:
    p = PhotodetectorParams(**{**params.__dict__, "bandwidth_hz": bandwidth})
    b = photodetector_noise_budget(power_w, p)
    ok = b["snr_db"] >= 20
    p_min = power_w[np.argmax(ok)] if np.any(ok) else np.nan
    linearity = b["signal_current_a"] / np.maximum(b["ideal_output_signal_current_a"], 1e-30)
    below_90 = np.where(linearity < 0.9)[0]
    p_sat = power_w[below_90[0]] if len(below_90) else np.nan
    rows.append((bandwidth / 1e6, p_min, p_sat, p_sat / p_min))

pd.DataFrame(
    rows,
    columns=["bandwidth_MHz", "min_power_for_20dB_W", "power_at_10pct_compression_W", "usable_power_ratio"],
)
"""
        ),
        md(
            r"""
## 8. Design Trade-Off

APD gain can improve effective responsivity, but it does not create photons.
It also adds avalanche excess noise and reduces saturation headroom. The useful
question is not "maximum gain"; it is "gain at the required bandwidth before
noise and compression erase the benefit."
"""
        ),
        code(
            r"""
gains = [1, 5, 20, 80]
fig, ax = plt.subplots()
for gain in gains:
    excess = 1.0 if gain == 1 else gain**0.35
    p = PhotodetectorParams(
        **{
            **params.__dict__,
            "apd_gain": gain,
            "apd_excess_noise_factor": excess,
            "saturation_current_a": params.saturation_current_a,
        }
    )
    ax.semilogx(power_w, photodetector_noise_budget(power_w, p)["snr_db"], label=f"M={gain}, F={excess:.1f}")
ax.axhline(20, color="0.35", ls="--")
ax.set_xlabel("Optical power (W)")
ax.set_ylabel("SNR (dB)")
ax.set_title("APD gain: sensitivity versus excess noise and saturation")
ax.legend()
plt.show()
"""
        ),
        md(
            r"""
## 9. Key Engineering Conclusions

- Responsivity is set by both quantum efficiency and wavelength; quoting QE alone
  is not enough for system sensitivity.
- At very low optical power, thermal/read noise dominates and SNR improves almost
  linearly with power.
- In the shot-noise-limited region, signal rises as `P` while noise rises as
  `sqrt(P)`, so SNR improves as `sqrt(P)`.
- Wider bandwidth increases RMS noise as `sqrt(B)`, directly raising the minimum
  detectable optical power.
- Saturation creates a hard dynamic-range ceiling; once compressed, more optical
  power no longer gives a trustworthy measurement.
- APD gain is valuable only when the electronics noise floor is the bottleneck;
  excess noise and current compression limit the usable gain.
"""
        ),
    ]
    write_notebook("01_photodetector_noise_snr_bandwidth.ipynb", cells)


def laser_notebook():
    cells = [
        md(
            r"""
# 02 - Laser Diode Thermal Drift and PID Control

This notebook models a laser diode as an electro-optical device coupled to a
first-order thermal package. It shows why industrial laser systems need
temperature control, not just a current driver.
"""
        ),
        code(SETUP + "\nfrom src.laser import LaserDiodeParams, threshold_current, output_power, wavelength, electrical_heat\nfrom src.control import PIDController, simulate_tec_temperature, steady_state_error, overshoot, settling_time"),
        md(
            r"""
## 1. Engineering Problem

Hold laser output power and wavelength stable while electrical heat and ambient
temperature drift. The design needs to answer:

- How does threshold current move with temperature?
- How much wavelength drift does a package-temperature error create?
- What is the difference between no control, proportional control, and PID?
- When does the TEC hit its authority limit?
"""
        ),
        md(
            r"""
## 2. Physical Assumptions

- Threshold current follows `I_th(T) = I_th(T_ref) exp((T - T_ref) / T0)`.
- Optical power follows `P_out = eta_s (I - I_th)` above threshold and zero below.
- Wavelength drift is locally linear: `lambda(T) = lambda_0 + alpha_T (T - T0)`.
- The laser package is a lumped first-order thermal node.
- TEC cooling is represented as a bounded control power.
- Sensor noise and current noise are small perturbations around the operating point.
"""
        ),
        md("## 3. System Parameters"),
        code(
            r"""
params = LaserDiodeParams(
    threshold_current_ref_a=35e-3,
    threshold_reference_temp_k=298.15,
    characteristic_temp_k=55.0,
    slope_efficiency_w_per_a=0.85,
    center_wavelength_m=785e-9,
    wavelength_reference_temp_k=298.15,
    wavelength_temp_coeff_m_per_k=0.28e-9,
    series_voltage_v=2.1,
    thermal_resistance_k_per_w=18.0,
    thermal_capacitance_j_per_k=7.0,
)

pd.DataFrame(
    [
        ("threshold_current_ref_a", params.threshold_current_ref_a, "A", "Threshold current at reference temperature."),
        ("characteristic_temp_k", params.characteristic_temp_k, "K", "Higher T0 means threshold is less temperature-sensitive."),
        ("slope_efficiency_w_per_a", params.slope_efficiency_w_per_a, "W/A", "Incremental optical power above threshold."),
        ("wavelength_temp_coeff_m_per_k", params.wavelength_temp_coeff_m_per_k, "m/K", "Temperature tuning coefficient of diode wavelength."),
        ("series_voltage_v", params.series_voltage_v, "V", "Used to estimate electrical heat load."),
        ("thermal_resistance_k_per_w", params.thermal_resistance_k_per_w, "K/W", "Package-to-ambient thermal resistance."),
        ("thermal_capacitance_j_per_k", params.thermal_capacitance_j_per_k, "J/K", "Thermal inertia; sets response time."),
    ],
    columns=["parameter", "value", "unit", "engineering meaning"],
)
"""
        ),
        md("## 4. Simulation Model"),
        code(
            r"""
temps_c = np.linspace(15, 55, 200)
temps_k = temps_c + 273.15
currents_ma = np.linspace(0, 140, 300)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].plot(temps_c, threshold_current(temps_k, params) * 1e3)
axes[0].set_xlabel("Temperature (degC)")
axes[0].set_ylabel("Threshold current (mA)")
axes[0].set_title("Temperature-dependent threshold")

for temp_c in [20, 25, 35, 45]:
    p_mw = output_power(currents_ma * 1e-3, temp_c + 273.15, params) * 1e3
    axes[1].plot(currents_ma, p_mw, label=f"{temp_c} degC")
axes[1].set_xlabel("Drive current (mA)")
axes[1].set_ylabel("Output power (mW)")
axes[1].set_title("L-I curve shifts with temperature")
axes[1].legend()
plt.show()
"""
        ),
        code(
            r"""
fig, ax = plt.subplots()
ax.plot(temps_c, wavelength(temps_k, params) * 1e9)
ax.set_xlabel("Temperature (degC)")
ax.set_ylabel("Wavelength (nm)")
ax.set_title("Laser wavelength drift")
plt.show()
"""
        ),
        md(
            r"""
## 5. Noise / Uncertainty Model

Two small uncertainties are propagated around the operating point:

- current driver noise changes output power through slope efficiency;
- temperature-sensor noise changes both threshold current and wavelength.

This is the kind of quick uncertainty budget that helps decide whether the
dominant problem is the current driver, the TEC loop, or the diode itself.
"""
        ),
        code(
            r"""
rng = np.random.default_rng(4)
drive_current_a = 90e-3
nominal_temp_k = 298.15
n = 20_000
current_noise_a = rng.normal(0, 0.15e-3, n)
sensor_noise_k = rng.normal(0, 0.03, n)

p_samples_mw = output_power(drive_current_a + current_noise_a, nominal_temp_k + sensor_noise_k, params) * 1e3
lambda_samples_pm = (wavelength(nominal_temp_k + sensor_noise_k, params) - params.center_wavelength_m) * 1e12

pd.DataFrame(
    {
        "metric": ["output_power_mean_mW", "output_power_std_mW", "wavelength_drift_std_pm"],
        "value": [p_samples_mw.mean(), p_samples_mw.std(), lambda_samples_pm.std()],
    }
)
"""
        ),
        code(
            r"""
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].hist(p_samples_mw, bins=60, color="tab:blue", alpha=0.75)
axes[0].set_xlabel("Output power (mW)")
axes[0].set_ylabel("Samples")
axes[0].set_title("Power uncertainty")
axes[1].hist(lambda_samples_pm, bins=60, color="tab:orange", alpha=0.75)
axes[1].set_xlabel("Wavelength error (pm)")
axes[1].set_title("Wavelength uncertainty from temperature noise")
plt.show()
"""
        ),
        md(
            r"""
## 6. Parameter Scan

The thermal model is:

`C dT/dt = P_heat - P_TEC - (T - T_env) / R_th`.

The controller uses error = measured temperature - setpoint, so positive output
means positive cooling power.
"""
        ),
        code(
            r"""
time_s = np.linspace(0, 240, 2401)
setpoint_k = 298.15
env_k = np.where(time_s < 80, 298.15, 303.15)
heat_w = electrical_heat(90e-3, setpoint_k, params)

no_control = simulate_tec_temperature(
    time_s, setpoint_k, env_k, heat_w,
    params.thermal_resistance_k_per_w, params.thermal_capacitance_j_per_k,
    controller=None, initial_temp_k=setpoint_k,
)
p_controller = PIDController(kp=0.18, ki=0.0, kd=0.0, output_limits=(0.0, 2.0))
p_control = simulate_tec_temperature(
    time_s, setpoint_k, env_k, heat_w,
    params.thermal_resistance_k_per_w, params.thermal_capacitance_j_per_k,
    controller=p_controller, initial_temp_k=setpoint_k,
)
pid_controller = PIDController(kp=0.25, ki=0.025, kd=0.2, output_limits=(0.0, 2.0), integral_limits=(-20, 20))
pid_control = simulate_tec_temperature(
    time_s, setpoint_k, env_k, heat_w,
    params.thermal_resistance_k_per_w, params.thermal_capacitance_j_per_k,
    controller=pid_controller, initial_temp_k=setpoint_k,
)

fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
for label, result in [("no control", no_control), ("P control", p_control), ("PID control", pid_control)]:
    axes[0].plot(time_s, result["temperature_k"] - 273.15, label=label)
axes[0].axhline(setpoint_k - 273.15, color="0.25", ls="--", lw=1)
axes[0].plot(time_s, env_k - 273.15, color="0.6", ls=":", label="ambient")
axes[0].set_ylabel("Temperature (degC)")
axes[0].set_title("TEC control response to ambient step")
axes[0].legend()

axes[1].plot(time_s, p_control["control_power_w"], label="P control")
axes[1].plot(time_s, pid_control["control_power_w"], label="PID control")
axes[1].set_xlabel("Time (s)")
axes[1].set_ylabel("TEC cooling power (W)")
axes[1].legend()
plt.show()
"""
        ),
        code(
            r"""
summary_rows = []
for label, result in [("no control", no_control), ("P control", p_control), ("PID control", pid_control)]:
    temp = result["temperature_k"]
    summary_rows.append(
        (
            label,
            steady_state_error(temp, setpoint_k),
            overshoot(temp, setpoint_k),
            settling_time(time_s, temp, setpoint_k, tolerance=0.10),
            np.max(result["control_power_w"]),
            (wavelength(temp[-1], params) - wavelength(setpoint_k, params)) * 1e12,
        )
    )

pd.DataFrame(
    summary_rows,
    columns=[
        "case",
        "final_temp_error_K",
        "max_positive_temp_error_K",
        "settling_time_to_0p1K_s",
        "max_TEC_power_W",
        "final_wavelength_error_pm",
    ],
)
"""
        ),
        md(
            r"""
## 7. Failure Regime

If heat load or ambient temperature requires more cooling than the TEC can
provide, the loop saturates. After that, integral action cannot remove the error;
it can only stay pinned at the actuator limit.
"""
        ),
        code(
            r"""
heat_scan = np.linspace(0.05, 1.2, 50)
final_errors = []
max_controls = []
for heat in heat_scan:
    ctrl = PIDController(kp=0.25, ki=0.025, kd=0.1, output_limits=(0.0, 0.6), integral_limits=(-20, 20))
    result = simulate_tec_temperature(
        time_s, setpoint_k, env_k, heat,
        params.thermal_resistance_k_per_w, params.thermal_capacitance_j_per_k,
        controller=ctrl, initial_temp_k=setpoint_k,
    )
    final_errors.append(result["temperature_k"][-1] - setpoint_k)
    max_controls.append(np.max(result["control_power_w"]))

fig, ax1 = plt.subplots()
ax1.plot(heat_scan, final_errors, label="final temp error")
ax1.axhline(0.1, color="tab:red", ls="--", label="0.1 K spec")
ax1.set_xlabel("Laser heat load (W)")
ax1.set_ylabel("Final temperature error (K)")
ax1.set_title("Failure when TEC authority is insufficient")
ax2 = ax1.twinx()
ax2.plot(heat_scan, max_controls, color="tab:orange", label="max TEC power")
ax2.set_ylabel("Max TEC power (W)")
lines = ax1.get_lines() + ax2.get_lines()
ax1.legend(lines, [line.get_label() for line in lines], loc="upper left")
plt.show()
"""
        ),
        md("## 8. Design Trade-Off"),
        code(
            r"""
kp_values = np.linspace(0.05, 0.6, 30)
trade_rows = []
for kp in kp_values:
    ctrl = PIDController(kp=kp, ki=0.02, kd=0.05, output_limits=(0.0, 2.0), integral_limits=(-20, 20))
    result = simulate_tec_temperature(
        time_s, setpoint_k, env_k, heat_w,
        params.thermal_resistance_k_per_w, params.thermal_capacitance_j_per_k,
        controller=ctrl, initial_temp_k=setpoint_k,
    )
    temp = result["temperature_k"]
    trade_rows.append((kp, overshoot(temp, setpoint_k), settling_time(time_s, temp, setpoint_k, 0.1), np.max(result["control_power_w"])))

trade = pd.DataFrame(trade_rows, columns=["kp", "overshoot_K", "settling_time_s", "max_TEC_power_W"])

fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
axes[0].plot(trade["kp"], trade["overshoot_K"])
axes[0].set_xlabel("Kp (W/K)")
axes[0].set_ylabel("Overshoot (K)")
axes[1].plot(trade["kp"], trade["settling_time_s"])
axes[1].set_xlabel("Kp (W/K)")
axes[1].set_ylabel("Settling time (s)")
axes[2].plot(trade["kp"], trade["max_TEC_power_W"])
axes[2].set_xlabel("Kp (W/K)")
axes[2].set_ylabel("Peak TEC power (W)")
fig.suptitle("Controller tuning trade-off")
plt.tight_layout()
plt.show()
"""
        ),
        md(
            r"""
## 9. Key Engineering Conclusions

- Laser threshold current rises exponentially with temperature, so constant
  current does not guarantee constant optical power.
- Wavelength drift can be converted directly from temperature error using the
  diode tuning coefficient; sub-kelvin thermal errors can still matter.
- Proportional control reduces drift but leaves steady-state error under heat
  load and ambient changes.
- Integral action removes steady-state error until the TEC reaches its cooling
  limit.
- Controller tuning is a compromise among settling time, overshoot, noise
  amplification, and actuator headroom.
- A useful laser-system portfolio project should report thermal stability in K,
  wavelength stability in pm, and optical-power stability in mW or percent.
"""
        ),
    ]
    write_notebook("02_laser_diode_thermal_pid_control.ipynb", cells)


def lidar_notebook():
    cells = [
        md(
            r"""
# 03 - ToF LiDAR Link Budget and Detection Simulation

This notebook connects emitted pulse energy, geometric return loss, detector
photoelectrons, background noise, threshold detection, and ROC curves.
"""
        ),
        code(SETUP + "\nfrom scipy.stats import norm\nfrom src import noise\nfrom src.detector import LidarParams, lidar_return_energy, photoelectrons_from_energy, gaussian_threshold_detection"),
        md(
            r"""
## 1. Engineering Problem

Estimate whether a pulsed ToF LiDAR can detect a diffuse target at range while
controlling false alarms. The industrial questions are:

- How many return photoelectrons are available versus distance?
- How do aperture, beam divergence, and target reflectivity affect range?
- How does sunlight/background power change detection probability?
- What threshold gives an acceptable false positive rate?
- Where does the link budget fail?
"""
        ),
        md(
            r"""
## 2. Physical Assumptions

- A single emitted optical pulse has fixed energy and wavelength.
- Large diffuse targets follow an approximate `R^-2` return scaling.
- Small targets smaller than the beam footprint add beam-interception loss and
  tend toward `R^-4` scaling.
- Detector output is modeled in photoelectrons per range gate.
- Background, dark current, and read noise are approximated as Gaussian electron
  noise for threshold detection.
- Timing walk, afterpulsing, speckle, and eye-safety limits are outside this
  compact model but should be added for a product design.
"""
        ),
        md("## 3. System Parameters"),
        code(
            r"""
params = LidarParams(
    wavelength_m=905e-9,
    pulse_energy_j=20e-9,
    aperture_diameter_m=25e-3,
    receiver_efficiency=0.45,
    detector_quantum_efficiency=0.65,
    beam_divergence_rad=2.0e-3,
    target_reflectivity=0.25,
    target_area_m2=0.1,
    atmospheric_transmission=0.95,
)

gate_time_s = 8e-9
dark_current_a = 4e-9
read_noise_e = 6.0
background_power_w = 80e-9

pd.DataFrame(
    [
        ("wavelength_m", params.wavelength_m, "m", "905 nm is common for silicon-detector automotive/industrial LiDAR."),
        ("pulse_energy_j", params.pulse_energy_j, "J", "Optical energy emitted per pulse."),
        ("aperture_diameter_m", params.aperture_diameter_m, "m", "Receiver aperture; collected return scales with area."),
        ("beam_divergence_rad", params.beam_divergence_rad, "rad", "Sets beam footprint and small-target interception."),
        ("target_reflectivity", params.target_reflectivity, "fraction", "Diffuse reflectivity of the target."),
        ("gate_time_s", gate_time_s, "s", "Detection integration window around expected time of flight."),
        ("background_power_w", background_power_w, "W", "Background optical power admitted during the gate."),
        ("read_noise_e", read_noise_e, "e RMS", "Input-referred read/electronics noise per gate."),
    ],
    columns=["parameter", "value", "unit", "engineering meaning"],
)
"""
        ),
        md("## 4. Simulation Model"),
        code(
            r"""
ranges_m = np.linspace(2, 180, 400)
energy_extended = lidar_return_energy(ranges_m, params, model="diffuse_extended")
energy_small = lidar_return_energy(ranges_m, params, model="small_target")
electrons_extended = photoelectrons_from_energy(energy_extended, params.wavelength_m, params.detector_quantum_efficiency)
electrons_small = photoelectrons_from_energy(energy_small, params.wavelength_m, params.detector_quantum_efficiency)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].loglog(ranges_m, energy_extended, label="extended diffuse target")
axes[0].loglog(ranges_m, energy_small, label="small target")
axes[0].set_xlabel("Range (m)")
axes[0].set_ylabel("Returned pulse energy (J)")
axes[0].set_title("LiDAR geometric return loss")
axes[0].legend()

axes[1].semilogy(ranges_m, electrons_extended, label="extended")
axes[1].semilogy(ranges_m, electrons_small, label="small")
axes[1].set_xlabel("Range (m)")
axes[1].set_ylabel("Signal photoelectrons / pulse")
axes[1].set_title("Detector-domain signal")
axes[1].legend()
plt.show()
"""
        ),
        md(
            r"""
## 5. Noise / Uncertainty Model

For one range gate:

- Background electrons: `P_bg t_gate / E_photon * QE`
- Dark electrons: `I_dark t_gate / q`
- Total noise sigma: `sqrt(background + dark + read_noise^2)`

The threshold detector compares measured electrons against a threshold. A lower
threshold improves sensitivity but increases false positives.
"""
        ),
        code(
            r"""
background_e = photoelectrons_from_energy(background_power_w * gate_time_s, params.wavelength_m, params.detector_quantum_efficiency)
dark_e = dark_current_a * gate_time_s / noise.Q_E
noise_sigma_e = np.sqrt(background_e + dark_e + read_noise_e**2)
target_false_alarm = 1e-4
threshold_e = noise_sigma_e * norm.isf(target_false_alarm)

snr_extended = electrons_extended / np.sqrt(electrons_extended + background_e + dark_e + read_noise_e**2)
detection_probability = norm.sf((threshold_e - electrons_extended) / noise_sigma_e)

pd.DataFrame(
    [
        ("background_e", background_e, "e/gate", "Sunlight/background contribution."),
        ("dark_e", dark_e, "e/gate", "Dark-current charge during gate."),
        ("noise_sigma_e", noise_sigma_e, "e RMS", "Gaussian threshold-noise approximation."),
        ("threshold_e", threshold_e, "e", "Threshold chosen for 1e-4 false alarm probability."),
    ],
    columns=["quantity", "value", "unit", "meaning"],
)
"""
        ),
        code(
            r"""
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].plot(ranges_m, snr_extended)
axes[0].axhline(5, color="tab:red", ls="--", label="SNR=5")
axes[0].set_xlabel("Range (m)")
axes[0].set_ylabel("Single-pulse SNR")
axes[0].set_title("SNR versus range")
axes[0].legend()

axes[1].plot(ranges_m, detection_probability)
axes[1].axhline(0.9, color="tab:green", ls="--", label="90% Pd")
axes[1].set_xlabel("Range (m)")
axes[1].set_ylabel("Detection probability")
axes[1].set_title("Detection probability at fixed false alarm rate")
axes[1].legend()
plt.show()
"""
        ),
        md("## 6. Parameter Scan"),
        code(
            r"""
apertures_mm = [12, 25, 50]
backgrounds_nw = [20, 80, 250]

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for aperture_mm in apertures_mm:
    p = LidarParams(**{**params.__dict__, "aperture_diameter_m": aperture_mm * 1e-3})
    signal_e = photoelectrons_from_energy(
        lidar_return_energy(ranges_m, p), p.wavelength_m, p.detector_quantum_efficiency
    )
    pd_range = norm.sf((threshold_e - signal_e) / noise_sigma_e)
    axes[0].plot(ranges_m, pd_range, label=f"{aperture_mm} mm")
axes[0].set_xlabel("Range (m)")
axes[0].set_ylabel("Detection probability")
axes[0].set_title("Aperture improves photon collection")
axes[0].legend(title="Aperture")

for bg_nw in backgrounds_nw:
    bg_e = photoelectrons_from_energy(bg_nw * 1e-9 * gate_time_s, params.wavelength_m, params.detector_quantum_efficiency)
    sigma = np.sqrt(bg_e + dark_e + read_noise_e**2)
    threshold = sigma * norm.isf(target_false_alarm)
    pd_range = norm.sf((threshold - electrons_extended) / sigma)
    axes[1].plot(ranges_m, pd_range, label=f"{bg_nw} nW")
axes[1].set_xlabel("Range (m)")
axes[1].set_ylabel("Detection probability")
axes[1].set_title("Background sunlight reduces range")
axes[1].legend(title="Background")
plt.show()
"""
        ),
        md("## 7. Failure Regime"),
        code(
            r"""
thresholds = np.linspace(0, 120, 300)
ranges_for_roc = [30, 70, 120]
signals_for_roc = np.interp(ranges_for_roc, ranges_m, electrons_extended)
metrics = gaussian_threshold_detection(signals_for_roc, noise_sigma_e, thresholds)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for idx, range_value in enumerate(ranges_for_roc):
    axes[0].semilogx(
        metrics["false_alarm_probability"],
        metrics["detection_probability"][idx],
        label=f"{range_value} m",
    )
axes[0].invert_xaxis()
axes[0].set_xlabel("False alarm probability")
axes[0].set_ylabel("Detection probability")
axes[0].set_title("ROC curves")
axes[0].legend()

for idx, range_value in enumerate(ranges_for_roc):
    axes[1].plot(thresholds, metrics["detection_probability"][idx], label=f"Pd {range_value} m")
axes[1].plot(thresholds, metrics["false_alarm_probability"], "k--", label="Pfa")
axes[1].set_yscale("log")
axes[1].set_xlabel("Threshold (electrons)")
axes[1].set_ylabel("Probability")
axes[1].set_title("Threshold trade-off")
axes[1].legend()
plt.show()
"""
        ),
        md("## 8. Design Trade-Off"),
        code(
            r"""
aperture_grid_mm = np.linspace(8, 60, 90)
bandwidth_grid_mhz = np.linspace(20, 250, 90)
range_target_m = 100
snr_map = np.empty((len(bandwidth_grid_mhz), len(aperture_grid_mm)))

for i, bandwidth_mhz in enumerate(bandwidth_grid_mhz):
    gate = 1.0 / (2 * bandwidth_mhz * 1e6)
    for j, aperture_mm in enumerate(aperture_grid_mm):
        p = LidarParams(**{**params.__dict__, "aperture_diameter_m": aperture_mm * 1e-3})
        sig_e = photoelectrons_from_energy(lidar_return_energy(range_target_m, p), p.wavelength_m, p.detector_quantum_efficiency)
        bg_e = photoelectrons_from_energy(background_power_w * gate, p.wavelength_m, p.detector_quantum_efficiency)
        dark_gate_e = dark_current_a * gate / noise.Q_E
        snr_map[i, j] = sig_e / np.sqrt(sig_e + bg_e + dark_gate_e + read_noise_e**2)

fig, ax = plt.subplots(figsize=(8, 5))
mesh = ax.pcolormesh(aperture_grid_mm, bandwidth_grid_mhz, snr_map, shading="auto", cmap="magma")
contours = ax.contour(aperture_grid_mm, bandwidth_grid_mhz, snr_map, levels=[3, 5, 8, 10], colors="white", linewidths=0.8)
ax.clabel(contours, fmt="SNR %.0f", fontsize=8)
ax.set_xlabel("Receiver aperture (mm)")
ax.set_ylabel("Detector bandwidth (MHz)")
ax.set_title(f"SNR trade-off at {range_target_m} m")
fig.colorbar(mesh, ax=ax, label="SNR")
plt.show()
"""
        ),
        md(
            r"""
## 9. Key Engineering Conclusions

- Range performance is fundamentally photon-limited: aperture area, pulse energy,
  target reflectivity, and atmospheric loss directly set the return electrons.
- Large diffuse targets and small targets can have very different range scaling;
  using the wrong model can overstate range.
- A threshold must be selected with both detection probability and false alarm
  rate in mind; ROC curves are more informative than one SNR number.
- Background sunlight raises the noise floor and threshold, reducing useful range.
- Larger aperture improves SNR but increases cost, size, alignment sensitivity,
  and stray-light management.
- Wider bandwidth improves timing resolution but shortens the gate and can raise
  receiver noise requirements, so bandwidth must be co-designed with timing specs.
"""
        ),
    ]
    write_notebook("03_tof_lidar_link_budget_detection.ipynb", cells)


def camera_notebook():
    cells = [
        md(
            r"""
# 04 - CMOS / CCD Camera Noise, Dynamic Range, and MTF Simulator

This notebook models the camera signal chain in electrons, then visualizes how
exposure, full well, ADC depth, hot pixels, flat-field error, and PSF blur affect
image quality.
"""
        ),
        code(SETUP + "\nfrom scipy.ndimage import gaussian_filter\nfrom src.detector import CameraParams, camera_noise_budget, simulate_camera_frame, gaussian_mtf"),
        md(
            r"""
## 1. Engineering Problem

Choose exposure and sensor settings that produce useful SNR without saturation
or image-quality loss. This is relevant to machine vision, microscopy, astronomy
instrumentation, semiconductor imaging, and camera characterization.
"""
        ),
        md(
            r"""
## 2. Physical Assumptions

- Photon and dark-current arrival are Poisson processes.
- Read noise is Gaussian in electron units.
- Quantization noise is uniform over one ADC code.
- Full-well capacity clips charge before digitization.
- PRNU is modeled as multiplicative pixel-response variation.
- Hot pixels have much larger dark current.
- Optical blur is represented by a Gaussian PSF and its MTF.
"""
        ),
        md("## 3. System Parameters"),
        code(
            r"""
params = CameraParams(
    quantum_efficiency=0.62,
    dark_current_e_per_s=0.8,
    read_noise_e=2.2,
    full_well_e=30_000.0,
    bit_depth=12,
    prnu_fraction=0.01,
    hot_pixel_fraction=0.001,
    hot_pixel_dark_current_e_per_s=100.0,
)

pd.DataFrame(
    [
        ("quantum_efficiency", params.quantum_efficiency, "fraction", "Photon-to-electron conversion efficiency."),
        ("dark_current_e_per_s", params.dark_current_e_per_s, "e/s/pixel", "Thermal generation rate per pixel."),
        ("read_noise_e", params.read_noise_e, "e RMS", "Electronics noise after charge collection."),
        ("full_well_e", params.full_well_e, "e", "Maximum charge before saturation/clipping."),
        ("bit_depth", params.bit_depth, "bits", "ADC quantization depth."),
        ("prnu_fraction", params.prnu_fraction, "fraction RMS", "Pixel-response non-uniformity."),
        ("hot_pixel_fraction", params.hot_pixel_fraction, "fraction", "Fraction of pixels with high dark current."),
    ],
    columns=["parameter", "value", "unit", "engineering meaning"],
)
"""
        ),
        md("## 4. Simulation Model"),
        code(
            r"""
ny, nx = 160, 220
y, x = np.mgrid[0:ny, 0:nx]
scene_rate = 2_000 + 70_000 * np.exp(-((x - 70) ** 2 + (y - 80) ** 2) / (2 * 18**2))
scene_rate += 30_000 * (np.sin(2 * np.pi * x / 18) > 0) * (y > 25) * (y < 135)
scene_rate += 8_000 * (x / nx)
blurred_rate = gaussian_filter(scene_rate, sigma=1.0)

frame_short = simulate_camera_frame(blurred_rate, 0.01, params, seed=2)
frame_long = simulate_camera_frame(blurred_rate, 0.10, params, seed=2)

fig, axes = plt.subplots(1, 3, figsize=(13, 4))
im0 = axes[0].imshow(scene_rate, cmap="gray")
axes[0].set_title("Ideal photon-rate scene")
im1 = axes[1].imshow(frame_short["adu"], cmap="gray", vmin=0, vmax=2**params.bit_depth - 1)
axes[1].set_title("10 ms exposure")
im2 = axes[2].imshow(frame_long["adu"], cmap="gray", vmin=0, vmax=2**params.bit_depth - 1)
axes[2].set_title("100 ms exposure")
for ax in axes:
    ax.set_xticks([])
    ax.set_yticks([])
fig.colorbar(im2, ax=axes, shrink=0.8, label="ADU")
plt.show()
"""
        ),
        md("## 5. Noise / Uncertainty Model"),
        code(
            r"""
signal_e = np.logspace(0, np.log10(params.full_well_e), 300)
budget = camera_noise_budget(signal_e, exposure_s=0.05, params=params)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].loglog(signal_e, budget["shot_noise_e"], label="photon shot")
axes[0].loglog(signal_e, budget["dark_noise_e"], label="dark")
axes[0].loglog(signal_e, budget["read_noise_e"], label="read")
axes[0].loglog(signal_e, budget["quantization_noise_e"], label="quantization")
axes[0].loglog(signal_e, budget["total_noise_e"], "k", lw=2, label="total")
axes[0].set_xlabel("Signal (electrons)")
axes[0].set_ylabel("Noise (e RMS)")
axes[0].set_title("Camera noise budget")
axes[0].legend()

axes[1].semilogx(signal_e, budget["snr_db"])
axes[1].axvline(params.full_well_e, color="tab:red", ls="--", label="full well")
axes[1].set_xlabel("Signal (electrons)")
axes[1].set_ylabel("SNR (dB)")
axes[1].set_title(f"Dynamic range = {budget['dynamic_range_db']:.1f} dB")
axes[1].legend()
plt.show()
"""
        ),
        md("## 6. Parameter Scan"),
        code(
            r"""
exposures_s = np.logspace(-4, 0, 220)
photon_rates = [500, 5_000, 50_000, 500_000]

fig, ax = plt.subplots()
for rate in photon_rates:
    signal = params.quantum_efficiency * rate * exposures_s
    snr_db = camera_noise_budget(signal, exposures_s[0], params)["snr_db"]
    saturated = signal >= params.full_well_e
    snr_db = np.where(saturated, np.nan, snr_db)
    ax.semilogx(exposures_s * 1e3, snr_db, label=f"{rate:g} photons/s/pixel")
ax.set_xlabel("Exposure time (ms)")
ax.set_ylabel("SNR (dB)")
ax.set_title("SNR versus exposure for different scene brightness")
ax.legend()
plt.show()
"""
        ),
        code(
            r"""
freq = np.linspace(0, 0.5, 300)
sigma_values = [0.4, 0.8, 1.2, 2.0]

fig, ax = plt.subplots()
for sigma in sigma_values:
    ax.plot(freq, gaussian_mtf(freq, sigma), label=f"sigma={sigma} px")
ax.set_xlabel("Spatial frequency (cycles/pixel)")
ax.set_ylabel("MTF")
ax.set_title("Gaussian PSF blur reduces contrast at high frequency")
ax.legend()
plt.show()
"""
        ),
        md("## 7. Failure Regime"),
        code(
            r"""
exposure_scan = np.logspace(-3, 0, 80)
saturation_fraction = []
hot_counts = []
median_adu = []

for exposure in exposure_scan:
    frame = simulate_camera_frame(blurred_rate, exposure, params, seed=3)
    saturation_fraction.append(np.mean(frame["electrons"] >= params.full_well_e))
    hot_counts.append(np.sum(frame["hot_pixel_mask"]))
    median_adu.append(np.median(frame["adu"]))

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].semilogx(exposure_scan * 1e3, saturation_fraction)
axes[0].axhline(0.01, color="tab:red", ls="--", label="1% saturated")
axes[0].set_xlabel("Exposure time (ms)")
axes[0].set_ylabel("Saturated pixel fraction")
axes[0].set_title("Overexposure failure")
axes[0].legend()

axes[1].semilogx(exposure_scan * 1e3, median_adu)
axes[1].set_xlabel("Exposure time (ms)")
axes[1].set_ylabel("Median ADU")
axes[1].set_title("Signal level versus exposure")
plt.show()
"""
        ),
        md("## 8. Design Trade-Off"),
        code(
            r"""
bit_depths = np.arange(8, 17)
read_noises = np.array([1.0, 2.2, 5.0, 10.0])

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for rn in read_noises:
    dr = 20 * np.log10(params.full_well_e / rn)
    axes[0].plot(bit_depths, [dr] * len(bit_depths), label=f"read noise {rn:g} e")
axes[0].set_xlabel("ADC bit depth")
axes[0].set_ylabel("Read-noise-limited DR (dB)")
axes[0].set_title("Dynamic range is often read-noise limited")
axes[0].legend()

full_scale = params.full_well_e
quant_noise = full_scale / (2**bit_depths - 1) / np.sqrt(12)
axes[1].plot(bit_depths, quant_noise, marker="o")
axes[1].axhline(params.read_noise_e, color="tab:red", ls="--", label="read noise")
axes[1].set_yscale("log")
axes[1].set_xlabel("ADC bit depth")
axes[1].set_ylabel("Quantization noise (e RMS)")
axes[1].set_title("ADC depth should not dominate read noise")
axes[1].legend()
plt.show()
"""
        ),
        md(
            r"""
## 9. Key Engineering Conclusions

- Camera SNR should be analyzed in electrons first; ADU values hide the physics.
- At low signal, read noise and quantization can dominate; at high signal, photon
  shot noise dominates until full-well saturation.
- Longer exposure improves SNR only until full-well clipping, motion blur, or
  dark current becomes limiting.
- Dynamic range depends strongly on full-well capacity and read noise; increasing
  ADC bit depth helps only if quantization noise is comparable to other noises.
- PRNU and hot pixels are calibration problems, not just random-noise problems.
- MTF connects optics and sensor sampling: a high-SNR image can still fail if PSF
  blur removes the spatial frequencies required by the application.
"""
        ),
    ]
    write_notebook("04_cmos_camera_noise_dynamic_range_mtf.ipynb", cells)


def spectrometer_notebook():
    cells = [
        md(
            r"""
# 05 - Spectrometer Resolution, Calibration, and Peak Fitting

This notebook models a compact spectrometer workflow: grating geometry,
wavelength calibration, line-spread function, detector noise, baseline
subtraction, peak fitting, uncertainty, and resolving close spectral lines.
"""
        ),
        code(SETUP + "\nfrom scipy.optimize import curve_fit\nfrom scipy.special import voigt_profile\nfrom src.detector import grating_diffraction_angle, gaussian_peak, lorentzian_peak, resolving_power"),
        md(
            r"""
## 1. Engineering Problem

Build a calibration and fitting workflow that turns detector pixels into
wavelengths and reports peak centers with uncertainty. The practical questions:

- What spectral range and resolution does the grating geometry allow?
- How accurately can calibration lines map pixel to wavelength?
- Does Gaussian, Lorentzian, or Voigt peak fitting change the reported center?
- When do two close lines become unresolved?
- How does slit width trade resolution against throughput and SNR?
"""
        ),
        md(
            r"""
## 2. Physical Assumptions

- Grating equation: `m lambda = d(sin alpha + sin beta)`.
- The pixel-to-wavelength map is locally polynomial after optical alignment.
- The line-spread function is approximated by Gaussian, Lorentzian, or Voigt
  profiles depending on the dominant broadening mechanism.
- Detector noise combines shot/read noise and a slowly varying baseline.
- Peak-parameter covariance from nonlinear least squares is used as a local
  uncertainty estimate.
"""
        ),
        md("## 3. System Parameters"),
        code(
            r"""
groove_density = 1_200e3  # lines/m
incidence_angle = np.deg2rad(12.0)
order = 1
pixel_count = 2048
true_coeff = np.array([1.2e-6, 0.115, 520.0])  # nm = a2*x^2 + a1*x + a0
fwhm_nm = 0.35
read_noise_counts = 8.0

pd.DataFrame(
    [
        ("groove_density", groove_density, "lines/m", "Grating groove density; sets angular dispersion."),
        ("incidence_angle", np.rad2deg(incidence_angle), "deg", "Input angle in grating equation."),
        ("order", order, "integer", "Diffraction order."),
        ("pixel_count", pixel_count, "pixels", "Linear detector size."),
        ("calibration_polynomial", "quadratic", "nm(pixel)", "Maps detector pixel to wavelength."),
        ("fwhm_nm", fwhm_nm, "nm", "Instrument line-spread FWHM."),
        ("read_noise_counts", read_noise_counts, "counts RMS", "Detector/electronics read noise."),
    ],
    columns=["parameter", "value", "unit", "engineering meaning"],
)
"""
        ),
        md("## 4. Simulation Model"),
        code(
            r"""
wavelengths_nm = np.linspace(450, 800, 300)
angles_deg = np.rad2deg(grating_diffraction_angle(wavelengths_nm * 1e-9, groove_density, incidence_angle, order))
res_power = resolving_power(wavelengths_nm, fwhm_nm)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].plot(wavelengths_nm, angles_deg)
axes[0].set_xlabel("Wavelength (nm)")
axes[0].set_ylabel("Diffraction angle (deg)")
axes[0].set_title("Grating angular dispersion")
axes[1].plot(wavelengths_nm, res_power)
axes[1].set_xlabel("Wavelength (nm)")
axes[1].set_ylabel("Resolving power lambda / delta_lambda")
axes[1].set_title("Resolution from LSF width")
plt.show()
"""
        ),
        code(
            r"""
rng = np.random.default_rng(12)
cal_pixels = np.array([120, 380, 760, 1100, 1450, 1780, 1980])
cal_wavelengths_true = np.polyval(true_coeff, cal_pixels)
cal_wavelengths_measured = cal_wavelengths_true + rng.normal(0, 0.03, len(cal_pixels))
fit_coeff = np.polyfit(cal_pixels, cal_wavelengths_measured, deg=2)
pixel_axis = np.arange(pixel_count)
wavelength_axis = np.polyval(fit_coeff, pixel_axis)
cal_residual_pm = (np.polyval(fit_coeff, cal_pixels) - cal_wavelengths_true) * 1e3

pd.DataFrame(
    {
        "pixel": cal_pixels,
        "true_wavelength_nm": cal_wavelengths_true,
        "measured_line_nm": cal_wavelengths_measured,
        "fit_residual_pm": cal_residual_pm,
    }
)
"""
        ),
        code(
            r"""
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].plot(pixel_axis, wavelength_axis)
axes[0].scatter(cal_pixels, cal_wavelengths_measured, color="tab:red", label="cal lines")
axes[0].set_xlabel("Pixel")
axes[0].set_ylabel("Wavelength (nm)")
axes[0].set_title("Wavelength calibration")
axes[0].legend()
axes[1].axhline(0, color="0.3", lw=1)
axes[1].scatter(cal_pixels, cal_residual_pm)
axes[1].set_xlabel("Pixel")
axes[1].set_ylabel("Calibration residual (pm)")
axes[1].set_title("Calibration residuals")
plt.show()
"""
        ),
        md("## 5. Noise / Uncertainty Model"),
        code(
            r"""
def gaussian_model(x, amplitude, center, sigma, baseline0, baseline1):
    return baseline0 + baseline1 * (x - x.mean()) + amplitude * np.exp(-0.5 * ((x - center) / sigma) ** 2)

def lorentzian_model(x, amplitude, center, gamma, baseline0, baseline1):
    return baseline0 + baseline1 * (x - x.mean()) + amplitude * gamma**2 / ((x - center) ** 2 + gamma**2)

def voigt_model(x, amplitude, center, sigma, gamma, baseline0, baseline1):
    profile = voigt_profile(x - center, sigma, gamma)
    profile = profile / profile.max()
    return baseline0 + baseline1 * (x - x.mean()) + amplitude * profile

x_nm = np.linspace(630, 638, 900)
true_center_nm = 633.42
sigma_nm = fwhm_nm / 2.355
baseline = 120 + 1.5 * (x_nm - x_nm.mean())
clean = baseline + 2200 * np.exp(-0.5 * ((x_nm - true_center_nm) / sigma_nm) ** 2)
noisy = rng.poisson(np.maximum(clean, 0)) + rng.normal(0, read_noise_counts, len(x_nm))

popt_g, pcov_g = curve_fit(gaussian_model, x_nm, noisy, p0=[2000, 633.4, 0.15, 120, 0])
popt_l, pcov_l = curve_fit(lorentzian_model, x_nm, noisy, p0=[2000, 633.4, 0.15, 120, 0])
popt_v, pcov_v = curve_fit(voigt_model, x_nm, noisy, p0=[2000, 633.4, 0.12, 0.08, 120, 0])

fit_summary = pd.DataFrame(
    [
        ("Gaussian", popt_g[1], np.sqrt(pcov_g[1, 1]) * 1e3),
        ("Lorentzian", popt_l[1], np.sqrt(pcov_l[1, 1]) * 1e3),
        ("Voigt", popt_v[1], np.sqrt(pcov_v[1, 1]) * 1e3),
    ],
    columns=["model", "fitted_center_nm", "center_uncertainty_pm"],
)
fit_summary
"""
        ),
        code(
            r"""
fig, ax = plt.subplots(figsize=(9, 4.8))
ax.plot(x_nm, noisy, ".", ms=3, alpha=0.45, label="noisy detector data")
ax.plot(x_nm, gaussian_model(x_nm, *popt_g), lw=2, label="Gaussian fit")
ax.plot(x_nm, lorentzian_model(x_nm, *popt_l), lw=2, label="Lorentzian fit")
ax.plot(x_nm, voigt_model(x_nm, *popt_v), lw=2, label="Voigt fit")
ax.set_xlabel("Wavelength (nm)")
ax.set_ylabel("Counts")
ax.set_title("Peak fitting with baseline and detector noise")
ax.legend()
plt.show()
"""
        ),
        md("## 6. Parameter Scan"),
        code(
            r"""
def two_line_spectrum(x, separation_nm, fwhm):
    sigma = fwhm / 2.355
    c0 = 650.0
    return (
        gaussian_peak(x, 1000, c0 - separation_nm / 2, sigma, 0)
        + gaussian_peak(x, 900, c0 + separation_nm / 2, sigma, 0)
        + 80
    )

sep_values = [0.15, 0.25, 0.35, 0.50, 0.80]
x2 = np.linspace(648.5, 651.5, 800)

fig, ax = plt.subplots()
for sep in sep_values:
    ax.plot(x2, two_line_spectrum(x2, sep, fwhm_nm), label=f"sep={sep:.2f} nm")
ax.set_xlabel("Wavelength (nm)")
ax.set_ylabel("Counts")
ax.set_title("Resolving close spectral lines")
ax.legend()
plt.show()
"""
        ),
        md("## 7. Failure Regime"),
        code(
            r"""
def single_gaussian_with_baseline(x, amplitude, center, sigma, baseline):
    return gaussian_peak(x, amplitude, center, sigma, baseline)

failure_rows = []
for sep in np.linspace(0.05, 0.8, 30):
    y_clean = two_line_spectrum(x2, sep, fwhm_nm)
    y_obs = rng.poisson(np.maximum(y_clean, 0)) + rng.normal(0, read_noise_counts, len(x2))
    popt, _ = curve_fit(
        single_gaussian_with_baseline,
        x2,
        y_obs,
        p0=[1800, 650, sigma_nm, 80],
        bounds=([0, 649.0, 1e-3, 0], [np.inf, 651.0, 1.0, np.inf]),
        maxfev=5000,
    )
    valley = np.min(y_clean[(x2 > 650 - sep / 2) & (x2 < 650 + sep / 2)]) if sep > 0.06 else np.nan
    peak = np.max(y_clean)
    failure_rows.append((sep, popt[1] - 650.0, valley / peak if np.isfinite(valley) else np.nan))

failure = pd.DataFrame(failure_rows, columns=["true_separation_nm", "single_peak_center_bias_nm", "valley_to_peak_ratio"])

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].plot(failure["true_separation_nm"], failure["single_peak_center_bias_nm"] * 1e3)
axes[0].axhline(0, color="0.3", lw=1)
axes[0].set_xlabel("True line separation (nm)")
axes[0].set_ylabel("Single-peak center bias (pm)")
axes[0].set_title("Unresolved doublet biases peak center")
axes[1].plot(failure["true_separation_nm"], failure["valley_to_peak_ratio"])
axes[1].axhline(0.8, color="tab:red", ls="--", label="poor visual separation")
axes[1].set_xlabel("True line separation (nm)")
axes[1].set_ylabel("Valley / peak")
axes[1].set_title("Failure to resolve close lines")
axes[1].legend()
plt.show()
"""
        ),
        md("## 8. Design Trade-Off"),
        code(
            r"""
slit_width_um = np.linspace(10, 150, 100)
base_fwhm_nm = 0.22
slit_broadening_nm = 0.0035 * slit_width_um
effective_fwhm = np.sqrt(base_fwhm_nm**2 + slit_broadening_nm**2)
throughput = slit_width_um / slit_width_um.max()
relative_snr = np.sqrt(throughput)
resolution = resolving_power(650, effective_fwhm)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].plot(slit_width_um, effective_fwhm, label="FWHM")
axes[0].set_xlabel("Slit width (um)")
axes[0].set_ylabel("FWHM (nm)")
axes[0].set_title("Wider slit broadens spectral lines")
axes[1].plot(slit_width_um, resolution / resolution.max(), label="normalized resolving power")
axes[1].plot(slit_width_um, relative_snr, label="relative SNR")
axes[1].set_xlabel("Slit width (um)")
axes[1].set_ylabel("Normalized metric")
axes[1].set_title("Resolution versus throughput")
axes[1].legend()
plt.show()
"""
        ),
        md(
            r"""
## 9. Key Engineering Conclusions

- A spectrometer project should report both calibration residuals and peak-fit
  uncertainty; a fitted center without uncertainty is incomplete.
- The line-spread function matters: Gaussian, Lorentzian, and Voigt fits can give
  different centers and widths when the model is mismatched.
- Polynomial calibration is reliable inside the calibrated pixel range but can
  fail badly when extrapolated.
- Two close lines become a metrology failure before they become visually obvious;
  unresolved doublets can bias the reported center.
- Narrower slits improve resolution but reduce throughput and SNR, while wider
  slits improve signal at the cost of spectral resolving power.
- For industrial spectroscopy, the useful output is not just a plot; it is a
  calibrated wavelength axis, residuals, fit parameters, uncertainty, and a clear
  statement of the resolution limit.
"""
        ),
    ]
    write_notebook("05_spectrometer_resolution_calibration_peak_fitting.ipynb", cells)


def main():
    photodetector_notebook()
    laser_notebook()
    lidar_notebook()
    camera_notebook()
    spectrometer_notebook()


if __name__ == "__main__":
    main()
