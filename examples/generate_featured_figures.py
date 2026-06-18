"""Refresh the README featured figures from executed notebook outputs."""

from __future__ import annotations

import runpy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    script = PROJECT_ROOT / "scripts" / "extract_featured_figures.py"
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
