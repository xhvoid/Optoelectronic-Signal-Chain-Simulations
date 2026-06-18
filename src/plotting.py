"""Small plotting helpers shared by notebooks."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def set_style():
    """Apply a clean engineering-report Matplotlib style."""

    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.figsize": (8.0, 4.8),
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "legend.frameon": False,
            "grid.alpha": 0.25,
        }
    )


def save_figure(fig, path, dpi=180):
    """Save a Matplotlib figure and create the parent directory if needed."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, bbox_inches="tight")
    return output


def add_regime_spans(ax, spans):
    """Add translucent regime spans.

    ``spans`` is an iterable of ``(x_min, x_max, label, color)`` tuples.
    """

    ymin, ymax = ax.get_ylim()
    label_y = ymin + 0.86 * (ymax - ymin)
    for x_min, x_max, label, color in spans:
        ax.axvspan(x_min, x_max, color=color, alpha=0.12, lw=0)
        ax.text(
            (x_min * x_max) ** 0.5,
            label_y,
            label,
            ha="center",
            va="center",
            fontsize=9,
            color=color,
        )
