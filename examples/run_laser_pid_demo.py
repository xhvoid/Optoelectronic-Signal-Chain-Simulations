"""Run a laser diode thermal PID demo from the command line."""

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

from src.control import PIDController, simulate_tec_temperature
from src.laser import LaserDiodeParams, electrical_heat, wavelength
from src import plotting


def run(output_dir: Path) -> pd.DataFrame:
    plotting.set_style()
    output_dir.mkdir(parents=True, exist_ok=True)

    params = LaserDiodeParams()
    time_s = np.linspace(0, 240, 2401)
    setpoint_k = 298.15
    environment_k = np.where(time_s < 80, 298.15, 303.15)
    heat_w = electrical_heat(90e-3, setpoint_k, params)

    cases = {
        "no_control": None,
        "p_control": PIDController(kp=0.18, output_limits=(0.0, 2.0)),
        "pid_control": PIDController(
            kp=0.25,
            ki=0.025,
            kd=0.2,
            output_limits=(0.0, 2.0),
            integral_limits=(-20, 20),
        ),
    }

    records = []
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for label, controller in cases.items():
        result = simulate_tec_temperature(
            time_s,
            setpoint_k,
            environment_k,
            heat_w,
            params.thermal_resistance_k_per_w,
            params.thermal_capacitance_j_per_k,
            controller=controller,
            initial_temp_k=setpoint_k,
        )
        temp_k = result["temperature_k"]
        control_w = result["control_power_w"]
        axes[0].plot(time_s, temp_k - 273.15, label=label.replace("_", " "))
        axes[1].plot(time_s, control_w, label=label.replace("_", " "))
        records.append(
            {
                "case": label,
                "final_temperature_error_k": temp_k[-1] - setpoint_k,
                "max_temperature_error_k": np.max(temp_k - setpoint_k),
                "max_control_power_w": np.max(control_w),
                "final_wavelength_error_pm": (wavelength(temp_k[-1], params) - wavelength(setpoint_k, params))
                * 1e12,
            }
        )

    axes[0].axhline(setpoint_k - 273.15, color="0.25", ls="--", lw=1)
    axes[0].plot(time_s, environment_k - 273.15, color="0.6", ls=":", label="ambient")
    axes[0].set_ylabel("Temperature (degC)")
    axes[0].set_title("Laser TEC control response")
    axes[0].legend()
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("TEC cooling power (W)")
    axes[1].legend()

    figure_path = output_dir / "laser_pid_response.png"
    table_path = output_dir / "laser_pid_summary.csv"
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
    args = parser.parse_args()
    print(run(args.output_dir).to_string(index=False))


if __name__ == "__main__":
    main()
