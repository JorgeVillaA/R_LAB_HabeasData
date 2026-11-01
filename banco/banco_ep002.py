"""Banco de EP-002 (identidad): un escenario levanta el doble de Zeus, los clones de portales y el doble del servicio de
captchas, corre `ep002.procesar` y verifica las expectativas. Lo invoca `correr_matriz.py EP-002`.

Esquema del escenario (además de `id` y `ramas`): `doble` (Zeus, como EP-001; `campos` pisa campos de radicados),
`portales` (policia_modo, procuraduria_modo, captcha_rechaza, familias, padron_policia/padron_procuraduria que se
mezclan con el padrón sintético completo, vaciar_policia), `servicio` (modo del servicio de captchas),
`espera` (listas por resultado, códigos, comentarios, consultas que NO debió recibir cada portal).
El banco valida flujo y orquestación contra clones; NO valida la veracidad de los portales reales.
"""
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for carpeta in (REPO, REPO / "Scripts", REPO / "dobles" / "zeus_api", REPO / "banco"):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

from correr_matriz import ENTORNO, CREDENCIALES, RELOJ, preparar_raiz, radicados_de  # noqa: E402
from dobles.portales.captchas import ServicioCaptchas as DobleCaptchas  # noqa: E402
from dobles.portales.servidor import DoblePortales  # noqa: E402
from dobles.zeus_api.servidor import DobleZeus  # noqa: E402
from habeasdata import ep001, ep002, ep003  # noqa: E402
from habeasdata.captcha import ServicioCaptchas  # noqa: E402
from habeasdata.config import cargar  # noqa: E402
from habeasdata.portales import ClientePortales  # noqa: E402
from habeasdata.registro import Registro  # noqa: E402
from habeasdata.zeus import ClienteZeus  # noqa: E402
from equivalencia_robot import rastro as rastro_logs  # noqa: E402
from tests.soporte_ep002 import padrones  # noqa: E402

def instantanea_repositorio(raiz):
    """Lo que dejó el repositorio (sin fechas ni consecutivos): conteos por tabla y las transacciones ordenadas."""
    import sqlite3
    archivos = list(Path(raiz).glob("Documentos/repositorio/*.sqlite"))
    if not archivos:
        return None
    con = sqlite3.connect(archivos[0])
    try:
        tablas = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t in ("Exclusion", "Celulares", "Correos", "MaestraCelulares", "MaestraCorreos", "Insumo")}
        transacciones = sorted(tuple(f) for f in con.execute(
            "SELECT RadicadoZeus, Etapa, EstadoAnterior, EstadoNuevo, Resultado, Motivo FROM Transacciones"))
        return {"tablas": tablas, "transacciones": [list(t) for t in transacciones]}
    finally:
        con.close()


def rastro(raiz):
    """Rastro de logs y reporte (como EP-001/EP-002) más, si hubo repositorio, lo que dejó en sus tablas."""
    resultado = rastro_logs(raiz)
    instantanea = instantanea_repositorio(raiz)
    if instantanea is not None:
        resultado["repositorio"] = instantanea
    return resultado


CLAVES_LISTA = ("validadas", "excepciones_negocio_3", "gestion_manual", "revision_humana", "sin_nombre",
                "excepciones_sistema_identidad")
CLAVES_EP003 = ("excepciones_negocio_4", "excepciones_sistema_repositorio", "exclusion_registrada", "excepciones_sistema_exclusion")


def correr_escenario(escenario, robot=False):
    especificacion = escenario["doble"]
    filas = radicados_de(especificacion["radicados"])
    filas = [dict(f, **especificacion.get("campos", {}).get(str(f["IDRADICADO"]), {})) for f in filas]
    import os
    zeus = DobleZeus(CREDENCIALES, filas).iniciar()
    web = DoblePortales().iniciar()
    servicio = DobleCaptchas().iniciar()
    proceso = json.loads(json.dumps(escenario.get("proceso", {})))
    repositorio = escenario.get("repositorio")  # EP-003: {"Fallas": {...}}; ausente = escenario de EP-002 sin repositorio
    proceso.setdefault("Repositorio", {}).update(Habilitado=repositorio is not None, **(repositorio or {}))
    raiz = preparar_raiz(zeus.puerto, proceso)
    if robot == "studio":  # Studio no hereda el entorno de este proceso: el par sintético del doble va en la configuración temporal
        ruta = raiz / "Configuracion" / "ConfiguracionProceso.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos["ZeusApi"]["Fixture"]["ClientId"], datos["ZeusApi"]["Fixture"]["ClientSecret"] = CREDENCIALES
        ruta.write_text(json.dumps(datos), encoding="utf-8")
    try:
        zeus.estado.configurar({k: v for k, v in especificacion.items() if k in ("token_ttl", "denegar", "fallas_radicado", "falla_comentario")})
        ajustes = escenario.get("portales", {})
        policia, procuraduria = padrones()
        if ajustes.get("vaciar_policia"):
            policia = {}
        policia.update(ajustes.get("padron_policia", {}))
        for tipo, numero, nombre in ajustes.get("padron_procuraduria", []):
            procuraduria[(tipo, numero)] = {"nombre": nombre, "antecedentes": False}
        for tipo, numero in ajustes.get("sin_nombre", []):
            procuraduria[(tipo, numero)] = {"nombre": "X", "sin_nombre": True}
        for tipo, numero in ajustes.get("con_antecedentes", []):
            procuraduria[(tipo, numero)]["antecedentes"] = True
        web.estado.configurar({"policia_padron": policia, "procuraduria_padron": procuraduria,
                               **{k: v for k, v in ajustes.items() if k in ("policia_modo", "procuraduria_modo", "captcha_rechaza", "familias")}})
        servicio.configurar(escenario.get("servicio", "normal"))
        ruta = raiz / "Configuracion" / "ConfiguracionProceso.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos["Portales"]["BackoffSegundos"] = [0]
        datos["Portales"]["Fixture"].update(
            UrlPolicia=f"{web.url}/policia/WebJudicial/index.xhtml",
            UrlProcuraduria=f"{web.url}/procuraduria/consulta-de-antecedentes.aspx",
            UrlCaptchas=f"http://127.0.0.1:{servicio.puerto}/resolver")
        ruta.write_text(json.dumps(datos), encoding="utf-8")
        if robot:  # el robot de Studio, ejecutado por el intérprete (navegador emulado), contra los mismos dobles
            return vista_del_robot(raiz, zeus, studio=robot == "studio")
        cfg = cargar(raiz)
        registro = Registro(cfg, RELOJ)
        cliente = ClienteZeus(cfg, registro, ENTORNO, dormir=lambda s: None)
        portales = ClientePortales(cfg, dormir=lambda s: None)
        captchas = ServicioCaptchas(datos["Portales"]["Fixture"]["UrlCaptchas"], 3, (0,), 5, dormir=lambda s: None)
        repo = ep003.abrir_repositorio(cfg, dormir=lambda s: None, reloj=RELOJ) if repositorio is not None else None
        resumen = ep002.procesar(cfg, cliente, registro, ep001.EscrituraComentario(cliente), portales, captchas, repo=repo)
        resumen["rastro"] = rastro(raiz)
        comentarios = sorted((c["IDRADICADO"], c["Detalle"]) for c in zeus.estado.comentarios)
        consultas = {"policia": len(web.estado.consultas["policia"]), "procuraduria": len(web.estado.consultas["procuraduria"]),
                     "casilla_marcada": sum(1 for c in web.estado.consultas["policia"] if c["recaptcha"])}
        archivos = sorted(p.relative_to(raiz).as_posix() for p in raiz.rglob("*.csv"))
        texto_logs = " ".join(p.read_text(encoding="utf-8") for p in raiz.rglob("*.csv"))
        lineas_auditoria = registro.ruta_auditoria().read_text(encoding="utf-8").count("\n")
        return resumen, comentarios, consultas, archivos, texto_logs, lineas_auditoria, portales.modo
    finally:
        for doble in (zeus, web, servicio):
            doble.detener()
        shutil.rmtree(raiz, ignore_errors=True)


def verificar(escenario, resumen, comentarios, consultas, archivos, texto_logs):
    espera, fallos = escenario["espera"], []

    def igual(nombre, real, esperado):
        if real != esperado:
            fallos.append(f"{nombre}: esperado {esperado!r}, real {real!r}")

    igual("estado", resumen["estado"], espera["estado"])
    for clave in CLAVES_LISTA:
        if clave in espera:
            igual(clave, sorted(resumen[clave]), sorted(espera[clave]))
    if "codigos" in espera:
        igual("codigos", resumen["codigos"], espera["codigos"])
    if "vias" in espera:
        igual("vias", {k: v for k, v in resumen["via"].items() if k in espera["vias"]}, espera["vias"])
    if "comentarios" in espera:
        igual("comentarios", [c[0] for c in comentarios], sorted(espera["comentarios"]))
    for portal, tope in espera.get("consultas_maximas", {}).items():
        if consultas[portal] > tope:
            fallos.append(f"consultas a {portal}: {consultas[portal]} > {tope}")
    if espera.get("casilla_nunca_marcada") and consultas["casilla_marcada"]:
        fallos.append("el bot marcó la casilla del reCAPTCHA")
    # Cero PII en los logs: ni nombres ni números de identificación sintéticos aparecen en los CSV
    for dato in ("LOPEZ", "MARIA", "1000000001", "9000000013"):
        if dato in texto_logs:
            fallos.append(f"PII sintética en los logs: {dato}")
    nombres = " ".join(archivos)
    if "LOG_DE_AUDITORIA" not in nombres or "LOG_DE_ERRORES" not in nombres:
        fallos.append("faltan los dos archivos de log del día")
    return fallos


def vista_de_resumen(resumen, comentarios):
    # El detalle del motivo de un fallo de portal difiere (el parser conoce el HTTP; Chrome solo ve el selector ausente): se
    # compara hasta el CÓDIGO del error.
    rastro_ = dict(resumen["rastro"], errores=sorted(re.sub(r"^(.*?Radicado \d+: [A-Z_]+):.*$", r"", f) for f in resumen["rastro"]["errores"]))
    resumen = dict(resumen, rastro=rastro_)
    return {"estado": resumen["estado"], **{k: sorted(resumen[k]) for k in CLAVES_LISTA}, "codigos": resumen["codigos"],
            "comentarios": comentarios, "rastro": resumen["rastro"]}


def vista_del_robot(raiz, zeus, studio=False):
    import ast
    import os
    from unittest import mock
    import interprete_robot
    shutil.copytree(REPO / "Scripts", raiz / "Scripts", ignore=shutil.ignore_patterns("__pycache__"))
    robot = json.loads((REPO / "Robots" / "LabHabeasData.robot.json").read_text(encoding="utf-8"))
    if studio:  # Studio en Chrome: el MCP recorta cada variable a 120 caracteres; las listas de 10 radicados caben
        import equivalencia_robot as eq
        for variable in robot["vars"]:
            if variable["name"] == "glbStrRutaRaiz":
                variable["data"] = raiz.as_posix()
        proyecto = os.environ["RPA_AIO_PROYECTO"]
        eq.mcp("write_robot", {"project": proyecto, "perfil": "trycore", "robot": robot})
        r = eq.mcp("run_in_studio", {"project": proyecto, "robot": robot["name"], "confirmar": True, "max_pasos": 100000})
        if r.get("error"):
            raise RuntimeError(f"el robot falló: {r['error']}")
        v = {x["nombre"]: x["valor"] for x in r["variables"]}
        lista = lambda n: [str(i) for i in ast.literal_eval(v[n])]  # noqa: E731
        resumen = {"estado": re.search(r"'estado': '(\w+)'", v["glbDicEstado"]).group(1), "codigos": ast.literal_eval(v["glbDicCodigos"]),
                   "validadas": lista("glbArrValidadas"), "excepciones_negocio_3": lista("glbArrExcepcionesNegocioTres"),
                   "gestion_manual": lista("glbArrGestionManual"), "revision_humana": lista("glbArrRevisionHumana"),
                   "sin_nombre": lista("glbArrSinNombre"), "excepciones_sistema_identidad": lista("glbArrExcepcionesSistemaIdentidad"), "rastro": rastro(raiz)}
        return vista_de_resumen(resumen, sorted((c["IDRADICADO"], c["Detalle"]) for c in zeus.estado.comentarios)), r["errores_capturados"]
    interprete = interprete_robot.Interprete(robot, raiz.as_posix())
    with mock.patch.dict(os.environ, ENTORNO):
        v = interprete_robot.correr(interprete)
    resumen = {"estado": v["glbDicEstado"]["estado"], "codigos": dict(v["glbDicCodigos"]),
               "validadas": v["glbArrValidadas"], "excepciones_negocio_3": v["glbArrExcepcionesNegocioTres"],
               "gestion_manual": v["glbArrGestionManual"], "revision_humana": v["glbArrRevisionHumana"],
               "sin_nombre": v["glbArrSinNombre"], "excepciones_sistema_identidad": v["glbArrExcepcionesSistemaIdentidad"], "rastro": rastro(raiz)}
    return vista_de_resumen(resumen, sorted((c["IDRADICADO"], c["Detalle"]) for c in zeus.estado.comentarios)), interprete.capturadas


def principal_studio(ids=None):
    """Equivalencia en Studio y Chrome: el robot real contra los clones, comparado con el orquestador de referencia."""
    escenarios = json.loads((REPO / "banco" / "escenarios" / "EP-002.json").read_text(encoding="utf-8"))
    resultados, todos = [], True
    for esc in escenarios:
        if ids and esc["id"].split("-")[1] not in ids:
            continue
        resumen, comentarios, *_ = correr_escenario(esc)
        esperado = vista_de_resumen(resumen, comentarios)
        obtenido, capturados = correr_escenario(esc, robot="studio")
        igual = obtenido == esperado
        todos &= igual
        resultados.append({"id": esc["id"], "equivalente": igual, "errores_capturados": capturados,
                           "diferencias": {k: (esperado[k], obtenido[k]) for k in esperado if esperado[k] != obtenido[k]}})
        print("IGUAL " if igual else "DISTINTO", esc["id"], f"capturados={capturados}", resultados[-1]["diferencias"] or "")
    import subprocess
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    (REPO / "banco" / "resultados" / "EP-002_equivalencia_robot.json").write_text(
        json.dumps({"head_at_run": sha, "anchored_at": {"sha": sha, "robot": "Robots/LabHabeasData.robot.json"},
                    "navegador": "Chrome (run_in_studio)", "escenarios": resultados}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("robot de Studio en Chrome equivalente al orquestador en los escenarios corridos:", todos)
    return 0 if todos else 1


if __name__ == "__main__":
    sys.exit(principal_studio(sys.argv[1:] or None))
