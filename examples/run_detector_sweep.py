"""Run a photodetector SNR/bandwidth sweep from the command line."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.detector import PhotodetectorParams, photodetector_noise_budget
from src import plotting


def run(output_dir: Path, target_snr_db: float) -> pd.DataFrame:
    plotting.set_style()
    output_dir.mkdir(parents=True, exist_ok=True)

    powers_w = np.logspace(-12, -3, 500)
    bandwidths_hz = np.array([1e6, 5e6, 20e6, 100e6])
    base = PhotodetectorParams(
        wavelength_m=850e-9,
        quantum_efficiency=0.78,
        bandwidth_hz=20e6,
        load_resistance_ohm=1_000.0,
        dark_current_a=2e-9,
        read_noise_current_a=0.25e-9,
        saturation_current_a=1.5e-3,
    )

    records = []
    fig, ax = plt.subplots()
    for bandwidth in bandwidths_hz:
        params = PhotodetectorParams(**{**base.__dict__, "bandwidth_hz": bandwidth})
        budget = photodetector_noise_budget(powers_w, params)
        ax.semilogx(powers_w, budget["snr_db"], label=f"{bandwidth / 1e6:g} MHz")

        meets_target = budget["snr_db"] >= target_snr_db
        min_power = powers_w[np.argmax(meets_target)] if np.any(meets_target) else np.nan
        records.append(
            {
                "bandwidth_hz": bandwidth,
                "target_snr_db": target_snr_db,
                "min_power_for_target_w": min_power,
                "thermal_noise_current_a": budget["thermal_noise_current_a"][0],
                "dark_noise_current_a": budget["dark_noise_current_a"][0],
            }
        )

    ax.axhline(target_snr_db, color="0.35", ls="--", label=f"{target_snr_db:g} dB target")
    ax.set_xlabel("Optical power (W)")
    ax.set_ylabel("SNR (dB)")
    ax.set_title("Photodetector bandwidth sweep")
    ax.legend()

    figure_path = output_dir / "detector_bandwidth_sweep.png"
    table_path = output_dir / "detector_bandwidth_sweep.csv"
    plotting.save_figure(fig, figure_path)
    summary = pd.DataFrame.from_records(records)
    summary.to_csv(table_path, index=False)
    print(f"wrote {figure_path}")
    print(f"wrote {table_path}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "figures" / "generated",
        help="Directory for generated CSV and PNG outputs.",
    )
    parser.add_argument("--target-snr-db", type=float, default=20.0)
    args = parser.parse_args()
    print(run(args.output_dir, args.target_snr_db).to_string(index=False))


if __name__ == "__main__":
    main()
