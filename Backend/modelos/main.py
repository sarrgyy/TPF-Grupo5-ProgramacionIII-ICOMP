"""Acceso compatible al punto de entrada actual del proyecto."""

from pathlib import Path
from runpy import run_path


if __name__ == "__main__":
    run_path(str(Path(__file__).resolve().parents[1] / "main.py"), run_name="__main__")
