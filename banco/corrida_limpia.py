"""Corrida limpia con el código de HEAD: el robot real (intérprete, navegador emulado) dos veces sobre la MISMA base nueva.

Deja `banco/evidencia/corrida-limpia/CORRIDA-LIMPIA.json` con la procedencia (commit, fecha/hora, comando, robot) y lo que se
comprueba EN la base resultante: el esquema, `LogEjecucion` (id de corrida, pasos), `Parametros`, el reporte y los logs por corrida y que la
segunda corrida no mezcle filas de la primera. La base no se versiona (D-33): este resumen es el artefacto.

    python banco/corrida_limpia.py
"""
import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "banco"), str(REPO / "Scripts"), str(REPO)]
import banco_ep002 as b  # noqa: E402
from habeasdata import ep003  # noqa: E402
from habeasdata import repositorio as r  # noqa: E402
from habeasdata.config import cargar  # noqa: E402
from procedencia import procedencia  # noqa: E402

SALIDA = REPO / "banco" / "evidencia" / "corrida-limpia" / "CORRIDA-LIMPIA.json"
TABLAS_POR_CORRIDA = ("Insumo", "Transacciones", "Excepciones", "Exclusion", "Gestores", "AuditoriaMaestras", "LogEjecucion")


def correr_dos_veces(escenario, destino):
    """El robot dos veces sobre la misma raíz; tras cada una copia la base y los CSV (el archivo debe estar libre para poder moverse)."""
    originales = b.liberar_y_anotar_pasos, b.vista_del_robot
    instantaneas = []

    def liberar(raiz, pasos=None):
        originales[0](raiz, pasos)  # falla si el robot dejó abierta la conexión
        carpeta = destino / f"corrida{len(instantaneas) + 1}"
        carpeta.mkdir()
        shutil.copy(raiz / "Documentos" / "repositorio" / "lab.sqlite", carpeta / "lab.sqlite")
        for csv in raiz.rglob("*.csv"):
            shutil.copy(csv, carpeta / csv.name)
        instantaneas.append(carpeta)

    def dos_veces(raiz, zeus, studio=False):
        originales[1](raiz, zeus, studio)
        return originales[1](raiz, zeus, studio)

    b.liberar_y_anotar_pasos, b.vista_del_robot = liberar, dos_veces
    try:
        b.correr_escenario(escenario, robot=True)
    finally:
        b.liberar_y_anotar_pasos, b.vista_del_robot = originales
    return instantaneas


def tabla(con, sql, *args):
    return [list(f) for f in con.execute(sql, args).fetchall()]


def resumen_de(carpeta, id_corrida):
    con = sqlite3.connect(carpeta / "lab.sqlite")
    columnas = {t: [c[1] for c in con.execute(f"PRAGMA table_info({t})")] for t in TABLAS_POR_CORRIDA + ("Parametros",)}
    filas = {t: con.execute(f"SELECT COUNT(*) FROM {t} WHERE IdCorrida = ?", (id_corrida,)).fetchone()[0] for t in TABLAS_POR_CORRIDA}
    return con, columnas, filas


def principal():
    escenarios = json.loads((REPO / "banco" / "escenarios" / "EP-003.json").read_text(encoding="utf-8"))
    escenario = next(e for e in escenarios if e["id"].startswith("EP003-12"))
    destino = Path(tempfile.mkdtemp(prefix="corrida_limpia_"))
    try:
        proc = procedencia()
        primera, segunda = correr_dos_veces(escenario, destino)
        con1 = sqlite3.connect(primera / "lab.sqlite")
        con2 = sqlite3.connect(segunda / "lab.sqlite")
        log = tabla(con2, "SELECT IdCorrida, Fecha, CasosProcesados, Descartados, Exitosos, NoExitosos, Parciales, Excepciones, Pasos, ComandosStudio "
                          "FROM LogEjecucion ORDER BY Id")
        ids = [f[0] for f in log]
        fallos = []
        if len(ids) != 2 or ids[0] == ids[1] or not all(ids):
            fallos.append(f"LogEjecucion debe traer dos corridas con id distinto y no vacío: {ids}")
        if any(not f[8] for f in log):
            fallos.append("LogEjecucion.Pasos sin valor en alguna corrida (lo escribe el producto)")
        esquema = {t: [c[1] for c in con2.execute(f"PRAGMA table_info({t})")] for t in TABLAS_POR_CORRIDA}
        for t, columnas in esquema.items():
            if "IdCorrida" not in columnas:
                fallos.append(f"{t} sin columna IdCorrida")
        if "Pasos" not in esquema["LogEjecucion"] or "ComandosStudio" not in esquema["LogEjecucion"]:
            fallos.append("LogEjecucion sin Pasos o ComandosStudio")

        # Parametros: todas las hojas de configuración + la raíz efectiva
        cfg = cargar(REPO)
        hojas = set(dict(ep003._aplanar(cfg.maestro))) | set(dict(ep003._aplanar(cfg.proceso))) | {"Maquina." + k for k in dict(ep003._aplanar(cfg.maquina))}
        claves = {f[0] for f in con2.execute("SELECT Clave FROM Parametros")}
        faltan = sorted(h for h in hojas if h not in claves)
        if faltan or len(claves) != len(hojas) + 1:
            fallos.append(f"Parametros: faltan {faltan}, filas {len(claves)} (esperadas {len(hojas) + 1})")

        # reporte y logs por corrida
        reporte = [l.split(";") for l in next(segunda.glob("*INFORMEGESTION*.csv")).read_text(encoding="utf-8").splitlines()]
        por_corrida = {i: [f for f in reporte[1:] if f[6] == i] for i in ids}
        if reporte[0][-1] != "IdCorrida" or any(len(f) != 7 for f in reporte[1:]):
            fallos.append("el reporte no trae la columna IdCorrida en todas sus filas")
        for i, filas in por_corrida.items():
            if not filas or filas[-1][3] != "FIN DE CORRIDA":
                fallos.append(f"el reporte de {i} no cierra con FIN DE CORRIDA")
        logs = {}
        for nombre in ("AUDITORIA", "ERRORES"):
            lineas = next(segunda.glob(f"*LOG_DE_{nombre}*.csv")).read_text(encoding="utf-8").splitlines()[1:]
            logs[nombre.lower()] = {i: sum(1 for l in lineas if l.split(";")[3].startswith(f"[{i}] ")) for i in ids}
            if sum(logs[nombre.lower()].values()) != len(lineas) or any(len(l.split(";")) != 4 for l in lineas):
                fallos.append(f"log de {nombre.lower()}: filas sin prefijo de corrida o fuera de los 4 campos")

        # la segunda corrida no mezcla: lo de la primera quedó idéntico y lo nuevo lleva el id de la segunda
        mezcla = {}
        for t, orden in (("Gestores", "Id"), ("Exclusion", "Id"), ("Excepciones", "Id"), ("Transacciones", "IdTransaccion"), ("AuditoriaMaestras", "Id")):
            antes = tabla(con1, f"SELECT * FROM {t} WHERE IdCorrida = ? ORDER BY {orden}", ids[0])
            despues = tabla(con2, f"SELECT * FROM {t} WHERE IdCorrida = ? ORDER BY {orden}", ids[0])
            nuevas = tabla(con2, f"SELECT COUNT(*) FROM {t} WHERE IdCorrida = ?", ids[1])[0][0]
            sin_id = tabla(con2, f"SELECT COUNT(*) FROM {t} WHERE IdCorrida IS NULL OR IdCorrida NOT IN (?, ?)", *ids)[0][0]
            mezcla[t] = {"filas_corrida1": len(antes), "filas_corrida1_tras_la_segunda": len(despues), "filas_corrida2": nuevas, "filas_sin_corrida": sin_id}
            if antes != despues:
                fallos.append(f"{t}: la segunda corrida cambió filas de la primera")
            if sin_id:
                fallos.append(f"{t}: {sin_id} filas sin id de corrida")
        for t, minimo in (("Gestores", 1), ("Exclusion", 1)):
            if mezcla[t]["filas_corrida2"] < minimo:
                fallos.append(f"{t}: la segunda corrida no dejó su propio rastro")
        gestores = tabla(con2, "SELECT IdCorrida, RadicadoZeus, FechaAsignacion, Motivo FROM Gestores ORDER BY Id")
        exclusion = tabla(con2, "SELECT IdCorrida, RadicadoZeus, FechaExclusion FROM Exclusion ORDER BY Id")
        resultado = {
            "procedencia": proc,
            "escenario": escenario["id"],
            "robot": "Robots/LabHabeasData.robot.json por el intérprete (navegador emulado), no Studio",
            "base_nueva": True,
            "corridas_sobre_la_misma_base": 2,
            "archivo_movible_tras_cada_corrida": True,  # liberar_y_anotar_pasos lanza RuntimeError si no lo fuera
            "log_ejecucion": {"columnas": ["IdCorrida", "Fecha", "CasosProcesados", "Descartados", "Exitosos", "NoExitosos", "Parciales", "Excepciones",
                                           "Pasos", "ComandosStudio"], "filas": log},
            "parametros": {"filas": len(claves), "hojas_de_configuracion": len(hojas), "faltan": faltan},
            "esquema_con_IdCorrida": {t: "IdCorrida" in c for t, c in esquema.items()},
            "reporte": {"encabezado": reporte[0], "filas_por_corrida": {i: len(f) for i, f in por_corrida.items()},
                        "ultima_fila_por_corrida": {i: f[-1][3] for i, f in por_corrida.items()}},
            "logs_filas_por_corrida": logs,
            "mezcla_entre_corridas": mezcla,
            "gestores": gestores,
            "exclusion": exclusion,
            "fallos": fallos,
            "verde": not fallos,
        }
        SALIDA.parent.mkdir(parents=True, exist_ok=True)
        SALIDA.write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({k: resultado[k] for k in ("log_ejecucion", "parametros", "reporte", "logs_filas_por_corrida", "mezcla_entre_corridas", "fallos", "verde")},
                         indent=1, ensure_ascii=False))
        for con in (con1, con2):
            con.close()
        return 0 if not fallos else 1
    finally:
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(principal())
