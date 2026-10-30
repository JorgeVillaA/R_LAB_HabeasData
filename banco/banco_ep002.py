"""Banco de EP-002 (identidad): un escenario levanta el doble de Zeus, los clones de portales y el doble del servicio de
captchas, corre `ep002.procesar` y verifica las expectativas. Lo invoca `correr_matriz.py EP-002`.

Esquema del escenario (además de `id` y `ramas`): `doble` (Zeus, como EP-001; `campos` pisa campos de radicados),
`portales` (policia_modo, procuraduria_modo, captcha_rechaza, familias, padron_policia/padron_procuraduria que se
mezclan con el padrón sintético completo, vaciar_policia), `servicio` (modo del servicio de captchas),
`espera` (listas por resultado, códigos, comentarios, consultas que NO debió recibir cada portal).
El banco valida flujo y orquestación contra clones; NO valida la veracidad de los portales reales.
"""
import json
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
from habeasdata import ep001, ep002  # noqa: E402
from habeasdata.captcha import ServicioCaptchas  # noqa: E402
from habeasdata.config import cargar  # noqa: E402
from habeasdata.portales import ClientePortales  # noqa: E402
from habeasdata.registro import Registro  # noqa: E402
from habeasdata.zeus import ClienteZeus  # noqa: E402
from tests.soporte_ep002 import padrones  # noqa: E402

CLAVES_LISTA = ("validadas", "excepciones_negocio_3", "gestion_manual", "revision_humana", "sin_nombre",
                "excepciones_sistema_identidad")


def correr_escenario(escenario):
    especificacion = escenario["doble"]
    filas = radicados_de(especificacion["radicados"])
    filas = [dict(f, **especificacion.get("campos", {}).get(str(f["IDRADICADO"]), {})) for f in filas]
    zeus = DobleZeus(CREDENCIALES, filas).iniciar()
    web = DoblePortales().iniciar()
    servicio = DobleCaptchas().iniciar()
    raiz = preparar_raiz(zeus.puerto, escenario.get("proceso", {}))
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
        cfg = cargar(raiz)
        registro = Registro(cfg, RELOJ)
        cliente = ClienteZeus(cfg, registro, ENTORNO, dormir=lambda s: None)
        portales = ClientePortales(cfg, dormir=lambda s: None)
        captchas = ServicioCaptchas(datos["Portales"]["Fixture"]["UrlCaptchas"], 3, (0,), 5, dormir=lambda s: None)
        resumen = ep002.procesar(cfg, cliente, registro, ep001.EscrituraComentario(cliente), portales, captchas)
        comentarios = sorted(c["IDRADICADO"] for c in zeus.estado.comentarios)
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
        igual("comentarios", comentarios, sorted(espera["comentarios"]))
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
