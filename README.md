# Optoelectronic Signal Chain Simulations

Portfolio-style photonics and optoelectronics simulations for detector, laser,
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

## Project Layout

```text
.
├── README.md
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
├── tests/
└── figures/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
jupyter lab
```

## Engineering Themes

- Photodetector/APD SNR, bandwidth, and saturation limits
- Laser diode temperature drift and TEC PID control
- ToF LiDAR link budget, threshold detection, and ROC curves
- CMOS/CCD sensor noise, dynamic range, flat-field effects, and MTF
- Spectrometer calibration, resolution, peak fitting, and uncertainty

The models are intentionally compact rather than vendor-specific. They are meant
to demonstrate practical signal-chain reasoning: units, assumptions, scaling
laws, failure regimes, and design trade-offs.

## License

MIT License. See [LICENSE](LICENSE).
