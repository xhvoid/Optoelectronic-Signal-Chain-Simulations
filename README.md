# Optoelectronic Signal Chain Simulations

[![tests](https://github.com/xhvoid/Optoelectronic-Signal-Chain-Simulations/actions/workflows/ci.yml/badge.svg)](https://github.com/xhvoid/Optoelectronic-Signal-Chain-Simulations/actions/workflows/ci.yml)

Photonics and optoelectronics simulations for detector, laser,
LiDAR, imaging sensor, and spectrometer engineering workflows.

The notebooks are written as engineering case studies. Each one follows the same
structure:

1. Engineering problem
2. Physical assumptions
3. System parameters
4. Simulation model
5. Noise / uncertainty model
6. Parameter scan
7. Failure regime
8. Design trade-off
9. Key engineering conclusions

## Featured Engineering Figures

### Photodetector / APD Receiver

<table>
<tr>
<td width="50%">
<img src="figures/featured_01_detector_noise_budget.png" alt="Photodetector noise budget">
<br><strong>Detector noise budget.</strong> Separates signal shot noise,
thermal noise, dark-current noise, read noise, and total RMS current noise. This
is the key diagnostic plot for deciding whether sensitivity is limited by the
detector physics, the load/TIA front end, or the electronics floor.
</td>
<td width="50%">
<img src="figures/featured_01_snr_design_map.png" alt="Photodetector SNR design map">
<br><strong>SNR design map.</strong> Shows SNR contours versus optical power and
bandwidth. This is a design-review figure: it converts a target SNR and required
bandwidth into a minimum optical power or detector/front-end requirement.
</td>
</tr>
</table>

### Laser Diode Thermal Control

<table>
<tr>
<td width="50%">
<img src="figures/featured_02_tec_control_response.png" alt="Laser TEC PID control response">
<br><strong>TEC control response.</strong> Compares no control, proportional
control, and full PID control after an ambient temperature step. It demonstrates
stability metrics such as steady-state error, settling behavior, control effort,
and wavelength stability through temperature.
</td>
<td width="50%">
<img src="figures/featured_02_tec_authority_failure.png" alt="Laser TEC authority failure">
<br><strong>TEC authority failure.</strong> Shows the heat-load point where the
controller saturates and temperature error can no longer be regulated away. This
is a practical actuator-sizing plot for laser packages and thermal test setups.
</td>
</tr>
</table>

### ToF LiDAR Detection

<table>
<tr>
<td width="50%">
<img src="figures/featured_03_lidar_roc_threshold.png" alt="LiDAR ROC and threshold trade-off">
<br><strong>ROC and threshold trade-off.</strong> Connects detector electrons,
noise sigma, threshold choice, detection probability, and false alarm rate. This
is more industrially useful than quoting SNR alone because it supports threshold
selection for a specified false-positive budget.
</td>
<td width="50%">
<img src="figures/featured_03_lidar_aperture_bandwidth_map.png" alt="LiDAR aperture bandwidth SNR map">
<br><strong>Aperture-bandwidth SNR map.</strong> Shows SNR at a fixed range as a
function of receiver aperture and detector bandwidth. This exposes the trade
between photon collection, timing bandwidth, package size, cost, and receiver
noise requirements.
</td>
</tr>
</table>

### CMOS / CCD Camera Sensor

<table>
<tr>
<td width="50%">
<img src="figures/featured_04_camera_noise_dynamic_range.png" alt="Camera noise budget and dynamic range">
<br><strong>Camera noise and dynamic range.</strong> Breaks the electron-domain
noise budget into photon shot noise, dark noise, read noise, and quantization
noise. It shows where the sensor transitions from read-noise limited to
shot-noise limited, and where full-well capacity sets the ceiling.
</td>
<td width="50%">
<img src="figures/featured_04_camera_adc_tradeoff.png" alt="Camera ADC bit depth trade-off">
<br><strong>ADC bit-depth trade-off.</strong> Compares quantization noise with
read noise and full-well capacity. It shows when adding ADC bits improves the
signal chain and when it is only digital precision beyond the analog noise
floor.
</td>
</tr>
</table>

### Spectrometer Calibration and Peak Fitting

<table>
<tr>
<td width="50%">
<img src="figures/featured_05_calibration_residuals.png" alt="Spectrometer wavelength calibration residuals">
<br><strong>Wavelength calibration residuals.</strong> Shows the fitted
pixel-to-wavelength calibration and residual error in picometers. This is a
metrology-facing figure because it reports calibration quality instead of only a
pretty spectrum.
</td>
<td width="50%">
<img src="figures/featured_05_peak_fitting_uncertainty.png" alt="Spectrometer peak fitting with noise and baseline">
<br><strong>Peak fitting with uncertainty.</strong> Compares Gaussian,
Lorentzian, and Voigt fits under baseline and detector noise. It demonstrates
model selection, center estimation, and uncertainty reporting for spectroscopy
or laser-characterization workflows.
</td>
</tr>
<tr>
<td width="50%">
<img src="figures/featured_05_unresolved_doublet_failure.png" alt="Spectrometer unresolved doublet failure">
<br><strong>Unresolved doublet failure.</strong> Quantifies how two close lines
can bias a single-peak fit before visual separation is obvious. This is the kind
of failure-regime plot needed for analytical instruments and optical metrology.
</td>
<td width="50%">
<img src="figures/featured_05_resolution_throughput_tradeoff.png" alt="Spectrometer resolution throughput trade-off">
<br><strong>Resolution-throughput trade-off.</strong> Shows how slit width
changes line width, resolving power, and relative SNR. This links optical
hardware choices to measurement performance.
</td>
</tr>
</table>

## Project Layout

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── README.md
├── pyproject.toml
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── detector.py
│   ├── laser.py
│   ├── noise.py
│   ├── control.py
│   └── plotting.py
├── notebooks/
│   ├── 01_photodetector_noise_snr_bandwidth.ipynb
│   ├── 02_laser_diode_thermal_pid_control.ipynb
│   ├── 03_tof_lidar_link_budget_detection.ipynb
│   ├── 04_cmos_camera_noise_dynamic_range_mtf.ipynb
│   └── 05_spectrometer_resolution_calibration_peak_fitting.ipynb
├── examples/
│   ├── run_detector_sweep.py
│   ├── run_laser_pid_demo.py
│   └── generate_featured_figures.py
├── scripts/
│   ├── generate_notebooks.py
│   └── extract_featured_figures.py
├── tests/
└── figures/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest
jupyter lab
```

## Reproducibility

The notebooks are the narrative layer, while `src/` contains reusable models,
`examples/` contains command-line demos, `scripts/` regenerates notebook and
README artifacts, and `tests/` checks core physical behavior.

```bash
python examples/run_detector_sweep.py
python examples/run_laser_pid_demo.py
python examples/generate_featured_figures.py
```

Generated example outputs are written to `figures/generated/`, which is ignored
by Git so the repository stays focused on curated portfolio figures.

## Engineering Themes

- Photodetector/APD SNR, bandwidth, and saturation limits
- Laser diode temperature drift and TEC PID control
- ToF LiDAR link budget, threshold detection, and ROC curves
- CMOS/CCD sensor noise, dynamic range, flat-field effects, and MTF
- Spectrometer calibration, resolution, peak fitting, and uncertainty

The models are intentionally compact rather than vendor-specific. They are meant
to demonstrate practical signal-chain reasoning: units, assumptions, scaling
laws, failure regimes, and design trade-offs.

## Validation and Limitations

These models are compact engineering simulations, not vendor-specific design
tools. They are intended to demonstrate signal-chain reasoning, parameter
sensitivity, noise scaling, and failure regimes.

Main limitations:

- Detector models use simplified RMS noise budgets and do not include a full
  transimpedance-amplifier frequency response or layout/parasitic model.
- Laser thermal simulations use a lumped first-order thermal model rather than a
  spatial package, mount, and TEC finite-element model.
- LiDAR return models use simplified geometric spreading, diffuse-target
  assumptions, and Gaussian threshold detection.
- Camera simulations use simplified PRNU, hot-pixel, read-noise, dark-current,
  and quantization models.
- Spectrometer models are intended for calibration and fitting intuition, not
  full optical design, stray-light analysis, or vendor-grade instrument
  qualification.

## License

MIT License. See [LICENSE](LICENSE).
