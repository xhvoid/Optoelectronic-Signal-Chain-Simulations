"""Extract selected high-value figures from executed notebooks.

The notebooks already contain rendered PNG outputs after execution. This script
pulls the curated figures into ``figures/`` so the GitHub README can display a
portfolio-style engineering showcase without rerunning notebooks.
"""

from __future__ import annotations

import base64
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
FIGURE_DIR = ROOT / "figures"


FEATURED = [
    (
        "01_photodetector_noise_snr_bandwidth.ipynb",
        3,
        "featured_01_detector_noise_budget.png",
    ),
    (
        "01_photodetector_noise_snr_bandwidth.ipynb",
        6,
        "featured_01_snr_design_map.png",
    ),
    (
        "02_laser_diode_thermal_pid_control.ipynb",
        4,
        "featured_02_tec_control_response.png",
    ),
    (
        "02_laser_diode_thermal_pid_control.ipynb",
        5,
        "featured_02_tec_authority_failure.png",
    ),
    (
        "03_tof_lidar_link_budget_detection.ipynb",
        4,
        "featured_03_lidar_roc_threshold.png",
    ),
    (
        "03_tof_lidar_link_budget_detection.ipynb",
        5,
        "featured_03_lidar_aperture_bandwidth_map.png",
    ),
    (
        "04_cmos_camera_noise_dynamic_range_mtf.ipynb",
        2,
        "featured_04_camera_noise_dynamic_range.png",
    ),
    (
        "04_cmos_camera_noise_dynamic_range_mtf.ipynb",
        6,
        "featured_04_camera_adc_tradeoff.png",
    ),
    (
        "05_spectrometer_resolution_calibration_peak_fitting.ipynb",
        2,
        "featured_05_calibration_residuals.png",
    ),
    (
        "05_spectrometer_resolution_calibration_peak_fitting.ipynb",
        3,
        "featured_05_peak_fitting_uncertainty.png",
    ),
    (
        "05_spectrometer_resolution_calibration_peak_fitting.ipynb",
        5,
        "featured_05_unresolved_doublet_failure.png",
    ),
    (
        "05_spectrometer_resolution_calibration_peak_fitting.ipynb",
        6,
        "featured_05_resolution_throughput_tradeoff.png",
    ),
]


def image_outputs(notebook_path: Path):
    nb = nbformat.read(notebook_path, as_version=4)
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            data = output.get("data") or {}
            if "image/png" in data:
                yield data["image/png"]


def main() -> None:
    FIGURE_DIR.mkdir(exist_ok=True)
    for notebook_name, image_number, output_name in FEATURED:
        notebook_path = NOTEBOOK_DIR / notebook_name
        images = list(image_outputs(notebook_path))
        if image_number < 1 or image_number > len(images):
            raise ValueError(
                f"{notebook_name} has {len(images)} image outputs, "
                f"cannot extract image {image_number}"
            )
        png_data = images[image_number - 1]
        output_path = FIGURE_DIR / output_name
        output_path.write_bytes(base64.b64decode(png_data))
        print(output_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
