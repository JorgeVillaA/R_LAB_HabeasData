"""Lanzador de EP-001 para el robot de Rocketbot (execScriptPython) o la línea de comandos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from habeasdata.ep001 import principal  # noqa: E402

if __name__ == "__main__":
    sys.exit(principal())
