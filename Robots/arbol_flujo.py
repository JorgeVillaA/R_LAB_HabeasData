"""Imprime el flujo de LabHabeasData como árbol legible (para explicarlo a cliente) y lo guarda en la evidencia.

Uso:  python Robots/arbol_flujo.py
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ROBOT = json.loads((RAIZ / "Robots" / "LabHabeasData.robot.json").read_text(encoding="utf-8"))
ROTULO = {"trycatch": "Control de errores", "group": "Grupo", "evaluateIf": "Si", "for": "Para cada", "setVar": "Asignar",
          "execScriptPython": "Paso (componente)", "log_message": "Log"}


def lineas(comandos, nivel=0):
    for comando in comandos:
        sangria = "  " * nivel
        yield f"{sangria}- **{ROTULO.get(comando['father'], comando['father'])}**: {comando.get('description', '')}"
        if comando.get("children"):
            yield from lineas(comando["children"], nivel + 1)
        if comando.get("else"):
            yield f"{sangria}  *(en caso contrario)*"
            yield from lineas(comando["else"], nivel + 1)


def contar(comandos):
    total = {}
    for comando in comandos:
        total[comando["father"]] = total.get(comando["father"], 0) + 1
        for hijo in ("children", "else"):
            for clave, valor in contar(comando.get(hijo) or []).items():
                total[clave] = total.get(clave, 0) + valor
    return total


if __name__ == "__main__":
    conteo = contar(ROBOT["commands"])
    texto = [f"# Flujo del robot {ROBOT['name']} (EP-001: HU-002, HU-003, HU-004)", "",
             f"Comandos por tipo: {', '.join(f'{k}={v}' for k, v in sorted(conteo.items()))}. Total: {sum(conteo.values())}.", "",
             *lineas(ROBOT["commands"])]
    destino = RAIZ / "banco" / "evidencia" / "EP-001" / "flujo_LabHabeasData.md"
    destino.write_text("\n".join(texto) + "\n", encoding="utf-8")
    print(f"{destino.name}: {sum(conteo.values())} comandos; {conteo}")
