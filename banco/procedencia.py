"""Procedencia de un artefacto de evidencia: de qué commit salió, cuándo, con qué comando y con qué robot.

Un artefacto sin esto no cuenta como evidencia (D-35). `cambios_sin_commit` lista lo que difería del commit al correr: si no está vacío,
el artefacto no se puede atribuir al commit a secas y así queda dicho.
"""
import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def procedencia(comando=None):
    cambios = [linea[3:] for linea in _git("status", "--porcelain", "--untracked-files=no").splitlines()
               if not linea[3:].startswith("banco/resultados/")]  # lo que escribe el propio banco no cuenta como diferencia del código
    robot = REPO / "Robots" / "LabHabeasData.robot.json"
    return {
        "commit": _git("rev-parse", "HEAD"),
        "rama": _git("branch", "--show-current"),
        "cambios_sin_commit": cambios,
        "fecha_hora": datetime.now().astimezone().isoformat(timespec="seconds"),
        "comando": comando or " ".join(["python"] + sys.argv),
        "robot_sha256": hashlib.sha256(robot.read_bytes()).hexdigest(),
    }
