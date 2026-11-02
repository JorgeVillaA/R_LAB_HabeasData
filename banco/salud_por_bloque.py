"""Mapa de salud por bloque (D-21, práctica experimental): por cada bloque del robot, qué hace, su entrada y salida y QUÉ
ESCENARIO DEL BANCO lo cubre. La cobertura se MIDE: cada escenario de EP-001, EP-002 y EP-003 corre el JSON del robot en el
intérprete (`interprete_robot`) y se anota qué bloques se ejecutaron. Un bloque sin escenario es un hueco de cobertura.

Uso:  python banco/salud_por_bloque.py            (reescribe docs/SALUD-POR-BLOQUE.md)
      python banco/salud_por_bloque.py --huecos   (solo imprime los bloques sin cubrir; sale con 1 si hay)
"""
import json
import os
import re
import sys
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
for carpeta in (REPO, REPO / "Scripts", REPO / "dobles" / "zeus_api", REPO / "banco"):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

import banco_ep002 as b2  # noqa: E402
import equivalencia_robot as eq  # noqa: E402
import interprete_robot  # noqa: E402
from tests.soporte import ENTORNO  # noqa: E402

ROBOT = REPO / "Robots" / "LabHabeasData.robot.json"
DESTINO = REPO / "docs" / "SALUD-POR-BLOQUE.md"
VARIABLE = re.compile(r"\{((?:glb|loc)[A-Za-z0-9_]+)\}")
GETVAR = re.compile(r"GetVar\('([A-Za-z0-9_]+)'\)")
SETVAR = re.compile(r"SetVar\('([A-Za-z0-9_]+)'")
ROTULO = {"trycatch": "Control de errores", "group": "Grupo", "evaluateIf": "Decisión", "for": "Bucle", "setVar": "Asignar",
          "execScriptPython": "Paso (componente)", "log_message": "Log", "openbrowser": "Chrome: abrir", "openUrl": "Chrome: URL",
          "click_web": "Chrome: clic", "sendkey_web": "Chrome: escribir", "textObject": "Chrome: leer texto",
          "waitforobject": "Chrome: esperar"}


def bloques(comandos, ruta=""):
    """Recorre el robot con la misma numeración que el intérprete («1.2.3», `.e` = rama else)."""
    for numero, c in enumerate(comandos or [], 1):
        actual = f"{ruta}.{numero}" if ruta else str(numero)
        yield actual, c
        yield from bloques(c.get("children"), actual)
        yield from bloques(c.get("else"), actual + ".e")


def entrada_salida(c):
    texto = json.dumps(c.get("command", ""), ensure_ascii=False) if not isinstance(c.get("command"), str) else c["command"]
    entradas = set(VARIABLE.findall(texto)) | set(GETVAR.findall(texto))
    salidas = set(SETVAR.findall(texto))
    for clave in ("var", "getvar"):
        if c.get(clave):
            salidas.add(c[clave])
    if c["father"] == "for":
        entradas |= set(VARIABLE.findall(json.loads(c["command"])["iterable"]))
    entradas -= salidas if c["father"] == "for" else set()
    return sorted(entradas), sorted(salidas)


def cobertura():
    """{ruta: [ids de escenario]} midiendo la ejecución real del robot en el intérprete."""
    cubiertos = {}
    escenarios1 = json.loads((REPO / "banco" / "escenarios" / "EP-001.json").read_text(encoding="utf-8"))
    escenarios2 = json.loads((REPO / "banco" / "escenarios" / "EP-002.json").read_text(encoding="utf-8"))
    escenarios3 = json.loads((REPO / "banco" / "escenarios" / "EP-003.json").read_text(encoding="utf-8"))
    with mock.patch.dict(os.environ, {"ZEUS_DOBLE_CLIENT_ID": ENTORNO["ZEUS_DOBLE_CLIENT_ID"],
                                      "ZEUS_DOBLE_CLIENT_SECRET": ENTORNO["ZEUS_DOBLE_CLIENT_SECRET"]}):
        for esc in escenarios1:
            eq.escenario(esc, eq.ejecutar_robot_interpretado)
            for ruta in interprete_robot.ULTIMO.ejecutados:
                cubiertos.setdefault(ruta, []).append(esc["id"])
        for esc in escenarios2 + escenarios3:
            b2.correr_escenario(esc, robot=True)
            for ruta in interprete_robot.ULTIMO.ejecutados:
                cubiertos.setdefault(ruta, []).append(esc["id"])
    return cubiertos


def abreviar(ids):
    cortos = [i.replace("EP00", "E").replace("EP-00", "E").split("-")[0] + "-" + i.split("-")[1] if i.startswith("EP00") and not i.startswith(("EP002", "EP003")) else i.split("-")[0] + "-" + i.split("-")[1] for i in ids]
    cortos = sorted(set(cortos))
    return ", ".join(cortos[:4]) + (f" (+{len(cortos) - 4})" if len(cortos) > 4 else "")


def documento(robot, cubiertos):
    lista = list(bloques(robot["commands"]))
    sin = [(r, c) for r, c in lista if r not in cubiertos]
    por_tipo = {}
    for _, c in lista:
        por_tipo[c["father"]] = por_tipo.get(c["father"], 0) + 1
    lineas = [
        "# Salud por bloque del robot `LabHabeasData`", "",
        "> Práctica **experimental** D-21 (test por bloque en Studio). Generado por `python banco/salud_por_bloque.py`; **no editar a mano**. "
        "La cobertura se mide: cada escenario del banco (EP-001: 18, EP-002: 25, EP-003: 11) corre el JSON del robot en el intérprete "
        "(`banco/interprete_robot.py`) y se anota qué bloques ejecutó.", "",
        "## Cómo probar un bloque solo",
        "1. En Studio, botón de test del bloque: ejecuta `commands:[ese bloque]` con las variables actuales; `playNode` arranca desde cualquier bloque.",
        "2. Todo bloque tiene **entrada y salida explícitas** (columnas de abajo). Los bloques `Paso (componente)` reciben la raíz "
        "(`glbStrRutaRaiz`) y llaman a `pasos.asegurar(raíz)`: reconstruyen la sesión solos, sin depender de que otro bloque haya corrido antes.",
        "3. La lógica pura sigue en funciones probadas sin abrir Studio (`Scripts/habeasdata`, `tests/`).",
        "4. Los bloques de Chrome necesitan los clones de portales arriba (`python dobles/portales/servidor.py 8766`) y el servicio de captchas.", "",
        "## Resumen",
        f"- Bloques: **{len(lista)}** ({', '.join(f'{ROTULO.get(k, k)} {v}' for k, v in sorted(por_tipo.items()))}).",
        f"- Cubiertos por al menos un escenario: **{len(lista) - len(sin)}**; **sin cubrir: {len(sin)}**.", ""]
    if sin:
        lineas += ["### Huecos de cobertura (bloques sin escenario)", "",
                   "| Bloque | Tipo | Descripción |", "|---|---|---|"]
        lineas += [f"| {r} | {ROTULO.get(c['father'], c['father'])} | {c.get('description', '')} |" for r, c in sin]
        lineas += ["", "Un bloque sin escenario no tiene prueba que lo ejercite: se reporta como hueco, no se declara sano.", ""]
    lineas += ["## Mapa", "", "| Bloque | Tipo | Qué hace | Entrada | Salida | Escenarios del banco |", "|---|---|---|---|---|---|"]
    for ruta, c in lista:
        entrada, salida = entrada_salida(c)
        escenarios = abreviar(cubiertos[ruta]) if ruta in cubiertos else "**sin cubrir**"
        lineas.append(f"| {ruta} | {ROTULO.get(c['father'], c['father'])} | {c.get('description', '').replace('|', '/')} | "
                      f"{', '.join(entrada) or '—'} | {', '.join(salida) or '—'} | {escenarios} |")
    lineas += ["", "Escenarios: `E001-NN` = banco EP-001 (`banco/escenarios/EP-001.json`), `EP002-NN` = banco EP-002, `EP003-NN` = banco EP-003.", ""]
    return "\n".join(lineas), sin


def principal():
    robot = json.loads(ROBOT.read_text(encoding="utf-8"))
    texto, sin = documento(robot, cobertura())
    if "--huecos" in sys.argv:
        for ruta, c in sin:
            print(ruta, c["father"], c.get("description", ""))
        return 1 if sin else 0
    DESTINO.write_text(texto, encoding="utf-8")
    print(f"{DESTINO.name}: {len(sin)} bloques sin cubrir")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
