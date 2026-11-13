"""Delega el acceso anterior al punto de entrada Backend/main.py.

Admite los mismos argumentos y menús que main.py. No conserva otra copia
de las reglas de negocio ni abre una base distinta.
"""

from pathlib import Path
from runpy import run_path


if __name__ == "__main__":
    run_path(str(Path(__file__).resolve().parents[1] / "main.py"), run_name="__main__")
