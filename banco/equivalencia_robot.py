"""Equivalencia del robot de Studio con el orquestador Python, escenario por escenario.

Corre cada escenario de banco/escenarios/<épica>.json dos veces contra el MISMO doble (fixture offline): una con el
orquestador Python (`ep001.procesar`, el que usan el banco y las pruebas) y otra con el robot LabHabeasData ejecutado en
Studio (`run_in_studio`). Compara estado, listas por resultado, descartados, motivo sin casos, aviso y comentarios.

Requisitos de entorno (sin rutas fijas en el código):
  RPA_AIO_SERVER            ruta de server.mjs del MCP rpa-aio
  RPA_AIO_PROYECTO          carpeta del proyecto de Studio (R_LAB_HabeasData)
  ZEUS_DOBLE_CLIENT_ID / ZEUS_DOBLE_CLIENT_SECRET   los mismos valores que tiene el proceso de Studio en su entorno
Uso:  python banco/equivalencia_robot.py EP-001
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for carpeta in (REPO, REPO / "Scripts", REPO / "dobles" / "zeus_api", REPO / "banco"):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

from correr_matriz import cambios_del_doble, mezclar, radicados_de  # noqa: E402
from habeasdata import ep001  # noqa: E402
from habeasdata.config import cargar  # noqa: E402
from dobles.zeus_api.servidor import DobleZeus  # noqa: E402

ESCRIBIR = ("token_ttl", "denegar", "fallas_radicado", "falla_comentario")


def mcp(herramienta, argumentos, espera=300):
    """Una llamada al MCP rpa-aio por stdio (JSON-RPC, una línea por mensaje)."""
    proceso = subprocess.Popen(["node", os.environ["RPA_AIO_SERVER"]], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, encoding="utf-8")

    def enviar(mensaje):
        proceso.stdin.write(json.dumps(mensaje) + "\n")
        proceso.stdin.flush()

    def leer(identificador):
        for linea in proceso.stdout:
            if linea.strip():
                mensaje = json.loads(linea)
                if mensaje.get("id") == identificador:
                    return mensaje.get("result") or mensaje.get("error")
        raise RuntimeError("el MCP cerró sin responder")

    try:
        enviar({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "equivalencia", "version": "1"}}})
        leer(1)
        enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})
        enviar({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": herramienta, "arguments": argumentos}})
        resultado = leer(2)
    finally:
        proceso.kill()
    texto = "".join(c.get("text", "") for c in resultado.get("content", []))
    if resultado.get("isError"):
        raise RuntimeError(f"{herramienta}: {texto[:300]}")
    return json.loads(texto)


def preparar_raiz(puerto, cambios_proceso):
    raiz = Path(tempfile.mkdtemp(prefix="equiv_hd_"))
    shutil.copytree(REPO / "Configuracion", raiz / "Configuracion")
    # El robot hace sys.path.insert(raíz/Scripts): la raíz de la corrida lleva su copia de los componentes.
    shutil.copytree(REPO / "Scripts", raiz / "Scripts", ignore=shutil.ignore_patterns("__pycache__"))
    ruta = raiz / "Configuracion" / "ConfiguracionProceso.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    for clave in ("UrlBase", "UrlToken", "UrlComentario"):
        datos["ZeusApi"]["Fixture"][clave] = datos["ZeusApi"]["Fixture"][clave].replace("8765", str(puerto))
    datos["ZeusApi"]["BackoffSegundos"] = [0]
    datos["Identidad"] = {"Habilitada": False}  # la equivalencia de EP-001 no consulta portales; EP-002 tiene la suya
    datos.setdefault("Repositorio", {})["Habilitado"] = False  # ni repositorio: EP-003 tiene su equivalencia
    # Credenciales del doble explícitas en la configuración temporal: el robot de Studio las lee
    # de aquí y no depende de que su proceso tenga las variables de entorno.
    datos["ZeusApi"]["Fixture"]["ClientId"] = os.environ["ZEUS_DOBLE_CLIENT_ID"]
    datos["ZeusApi"]["Fixture"]["ClientSecret"] = os.environ["ZEUS_DOBLE_CLIENT_SECRET"]
    mezclar(datos, cambios_proceso)
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return raiz


def ejecutar_robot(raiz):
    robot = json.loads((REPO / "Robots" / "LabHabeasData.robot.json").read_text(encoding="utf-8"))
    for variable in robot["vars"]:
        if variable["name"] == "glbStrRutaRaiz":
            variable["data"] = raiz.as_posix()
    proyecto = os.environ["RPA_AIO_PROYECTO"]
    mcp("write_robot", {"project": proyecto, "perfil": "trycore", "robot": robot})
    resultado = mcp("run_in_studio", {"project": proyecto, "robot": robot["name"], "confirmar": True, "max_pasos": 50000})
    if resultado.get("error"):
        raise RuntimeError(f"el robot falló: {resultado['error']}")
    variables = {v["nombre"]: v["valor"] for v in resultado["variables"]}
    # El MCP recorta cada variable a 120 caracteres: se comparan las variables del robot una por una, no el resumen JSON.
    def lista(nombre):
        return [str(x) for x in ast.literal_eval(variables[nombre])]

    # glbDicEstado se recorta a 120 caracteres: «estado» y «motivo_sin_casos» van primero en el diccionario por eso.
    texto = variables["glbDicEstado"]
    estado = {clave: (None if valor == "None" else valor.strip("'")) for clave, valor in
              re.findall(r"'(estado|motivo_sin_casos)': ('[^']*'|None)", texto)}
    motivo = estado["motivo_sin_casos"]
    resumen = {
        "estado": estado["estado"],
        "avanzan": lista("glbArrAvanzan"),
        "excepciones_negocio_1": lista("glbArrExcepcionesNegocioUno"),
        "excepciones_sistema": lista("glbArrExcepcionesSistema"),
        "descartados_identificacion_ausente": lista("glbArrIdsDescartados"),
        "motivo_sin_casos": motivo or None,
        "notificacion": {"asunto": variables["glbStrAsuntoAviso"]} if variables["glbStrAsuntoAviso"] else None,
    }
    return resumen, resultado["pasos"], resultado["errores_capturados"]


def resumen_de_variables(variables):
    """Resumen comparable a partir de las variables completas del robot (intérprete local, sin recorte a 120 caracteres)."""
    estado = variables["glbDicEstado"]
    return {
        "estado": estado["estado"],
        "avanzan": [str(x) for x in variables["glbArrAvanzan"]],
        "excepciones_negocio_1": [str(x) for x in variables["glbArrExcepcionesNegocioUno"]],
        "excepciones_sistema": [str(x) for x in variables["glbArrExcepcionesSistema"]],
        "descartados_identificacion_ausente": [str(x) for x in variables["glbArrIdsDescartados"]],
        "motivo_sin_casos": estado["motivo_sin_casos"] or None,
        "notificacion": ({"asunto": variables["glbStrAsuntoAviso"], "motivo": estado["motivo_detencion"]}
                         if variables["glbStrAsuntoAviso"] else None),
    }


def ejecutar_robot_interpretado(raiz):
    import interprete_robot
    robot = json.loads((REPO / "Robots" / "LabHabeasData.robot.json").read_text(encoding="utf-8"))
    interprete = interprete_robot.Interprete(robot, raiz.as_posix())
    variables = interprete_robot.correr(interprete)
    return resumen_de_variables(variables), interprete.bloques, interprete.capturadas


def vista(resumen, comentarios, motivo=True):
    vista_ = {
        "estado": resumen["estado"],
        "avanzan": resumen["avanzan"],
        "excepciones_negocio_1": resumen["excepciones_negocio_1"],
        "excepciones_sistema": resumen["excepciones_sistema"],
        "descartados": resumen["descartados_identificacion_ausente"],
        "motivo_sin_casos": resumen["motivo_sin_casos"],
        "aviso": (resumen.get("notificacion") or {}).get("asunto"),
        "motivo_detencion": (resumen.get("notificacion") or {}).get("motivo"),
        "comentarios": sorted(comentarios),
    }
    if not motivo:  # Studio recorta cada variable a 120 caracteres: allí solo se compara el asunto del aviso
        del vista_["motivo_detencion"]
    return vista_


def filas_csv(raiz, patron, columna_fecha):
    """Filas de los CSV de una corrida sin la columna de fecha (así se comparan orquestador y robot)."""
    filas = []
    for ruta in sorted(raiz.rglob(patron)):
        for linea in ruta.read_text(encoding="utf-8").splitlines()[1:]:
            columnas = linea.split(";")
            del columnas[columna_fecha]
            columnas = [re.sub(r"^\[C\d+\] ", "", c) for c in columnas]  # el identificador de corrida cambia entre orquestador y robot
            if "INFORMEGESTION" in patron:
                columnas = columnas[:5]
            filas.append(";".join(columnas))
    return sorted(filas)


def rastro(raiz):
    """Lo que el proceso deja escrito: reporte de gestión y log de errores (criterios de aceptación de las HU)."""
    return {"reporte": filas_csv(raiz, "*INFORMEGESTION*.csv", 0), "errores": filas_csv(raiz, "*LOG_DE_ERRORES*.csv", 1),
            "auditoria": filas_csv(raiz, "*LOG_DE_AUDITORIA*.csv", 1)}


def escenario(esc, ejecutor=None):
    ejecutor = ejecutor or ejecutar_robot
    # Credenciales sintéticas del doble: deben coincidir con las del proceso de Studio
    # (Configuracion/ConfiguracionProceso.json → ZeusApi.Fixture.ClientIdEnv/ClientSecretEnv).
    # Se fijan por defecto aquí para que una corrida no falle por el entorno; Studio las recibe
    # al lanzarse con R_LAB_HabeasData.bat, que exporta el mismo par.
    os.environ.setdefault("ZEUS_DOBLE_CLIENT_ID", "cliente-banco")
    os.environ.setdefault("ZEUS_DOBLE_CLIENT_SECRET", "secreto-banco-no-real")
    spec = esc["doble"]
    doble = DobleZeus((os.environ["ZEUS_DOBLE_CLIENT_ID"], os.environ["ZEUS_DOBLE_CLIENT_SECRET"]),
                      radicados_de(spec["radicados"])).iniciar()
    puerto = doble.puerto
    raiz = preparar_raiz(puerto, esc.get("proceso", {}))
    try:
        doble.estado.configurar(cambios_del_doble(spec))
        if spec.get("apagado"):
            doble.detener()
        py = ep001.procesar(cargar(raiz))
        vista_py = vista(py, motivo=ejecutor is not ejecutar_robot, comentarios=[(c["IDRADICADO"], c["Detalle"]) for c in doble.estado.comentarios] if not spec.get("apagado") else [])
        if not spec.get("apagado"):
            doble.estado.configurar({"reiniciar": True})
        raiz_robot = preparar_raiz(puerto, esc.get("proceso", {}))  # carpeta propia: sus filas no se mezclan con las del orquestador
        rastro_py = rastro(raiz)
        resumen_robot, pasos, capturados = ejecutor(raiz_robot)
        rastro_robot = rastro(raiz_robot)
        shutil.rmtree(raiz_robot, ignore_errors=True)
        vista_robot = vista(resumen_robot, motivo=ejecutor is not ejecutar_robot, comentarios=[(c["IDRADICADO"], c["Detalle"]) for c in doble.estado.comentarios] if not spec.get("apagado") else [])
        return dict(vista_py, **rastro_py), dict(vista_robot, **rastro_robot), pasos, capturados
    finally:
        if not spec.get("apagado"):
            doble.detener()
        shutil.rmtree(raiz, ignore_errors=True)


def principal():
    epica = sys.argv[1]
    escenarios = json.loads((REPO / "banco" / "escenarios" / f"{epica}.json").read_text(encoding="utf-8"))
    resultados = []
    for esc in escenarios:
        vista_py, vista_robot, pasos, capturados = escenario(esc, ejecutar_robot_interpretado if "--interprete" in sys.argv else None)
        iguales = vista_py == vista_robot and capturados == 0
        diferencias = {k: (vista_py[k], vista_robot[k]) for k in vista_py if vista_py[k] != vista_robot[k]}
        resultados.append({"id": esc["id"], "equivalente": iguales, "pasos_robot": pasos, "errores_capturados": capturados,
                           "diferencias": diferencias})
        print(("IGUAL " if iguales else "DISTINTO"), esc["id"], f"pasos={pasos}", diferencias or "")
    sufijo = "_interprete" if "--interprete" in sys.argv else ""
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    (REPO / "banco" / "resultados" / f"{epica}_equivalencia_robot{sufijo}.json").write_text(
        json.dumps({"head_at_run": sha, "anchored_at": {"sha": sha, "robot": "Robots/LabHabeasData.robot.json"},
                    "escenarios": resultados}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    todos = all(r["equivalente"] for r in resultados)
    print(f"escenarios: {len(resultados)}  robot de Studio equivalente al orquestador Python en todos: {todos}")
    return 0 if todos else 1


if __name__ == "__main__":
    sys.exit(principal())
