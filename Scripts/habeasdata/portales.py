"""Clientes de los portales del Estado: Policía Nacional (HU-006) y Procuraduría (HU-007), en dos modos.

`fixture` (por defecto): los clones técnicos de `dobles/portales` (banco determinista, sin red).
`real`: los portales del Estado. Exige la autorización explícita (PORTALES_REAL_AUTORIZADO=1), la ventana operativa y red.
POLÍTICA INNEGOCIABLE: el reCAPTCHA v2 de la Policía NO se evade. En modo real el bot se detiene (RevisionHumana) y lo
resuelve una persona, o el caso se deriva a revisión manual. La casilla solo se marca en modo fixture, donde el captcha del
clon se entrega ya resuelto (el lab no ejercita esa resolución). La pregunta de la Procuraduría la resuelve el servicio de
captchas (HU-026a), no el bot.
Este módulo navega por HTTP lo que el robot de Studio navega en Chrome; ambos leen los mismos controles (ids/nombres del DOM).
"""
import html.parser
import http.cookiejar
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from .captcha import ErrorCaptcha, MAX_REINTENTOS, SERVICIO_NO_DISPONIBLE

TIPOS_PROCURADURIA = {"CEDULA DE CIUDADANIA": "1", "NIT": "2", "PASAPORTE": "3", "TARJETA DE IDENTIDAD": "4",
                      "CEDULA DE EXTRANJERIA": "5"}


class ErrorPortal(Exception):
    """Fallo de sistema del portal: caído, bloqueado por el WAF o con una estructura distinta a la esperada."""


class ErrorBloqueoPortal(Exception):
    """Falta autorización, ventana operativa o red para operar en modo real: se reporta, no se enmascara."""


class RevisionHumana(Exception):
    """El bot se detiene: lo resuelve una persona o el caso va a revisión manual (cuota, reCAPTCHA, reto de imágenes)."""

    def __init__(self, motivo):
        super().__init__(motivo)
        self.motivo = motivo


class Pagina(html.parser.HTMLParser):
    """Lo mínimo de una página: controles por nombre e id, y el texto de los elementos con id."""

    def __init__(self, texto):
        super().__init__()
        self.nombres, self.ids, self.valores, self.textos = set(), set(), {}, {}
        self._abiertos = []
        self.feed(texto)

    def handle_starttag(self, etiqueta, atributos):
        a = dict(atributos)
        if a.get("name"):
            self.nombres.add(a["name"])
            if etiqueta == "input" and a.get("type") == "hidden":
                self.valores[a["name"]] = a.get("value", "")
        if a.get("id"):
            self.ids.add(a["id"])
            self._abiertos.append((etiqueta, a["id"]))
            self.textos.setdefault(a["id"], "")

    def handle_endtag(self, etiqueta):
        for i in range(len(self._abiertos) - 1, -1, -1):
            if self._abiertos[i][0] == etiqueta:
                del self._abiertos[i:]
                break

    def handle_data(self, dato):
        for _, identificador in self._abiertos:
            self.textos[identificador] += dato

    def texto(self, identificador):
        return " ".join(self.textos.get(identificador, "").split())


class Sesion:
    def __init__(self, timeout, backoff, dormir, reintentos):
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.timeout, self.backoff, self.dormir, self.reintentos = timeout, backoff, dormir, reintentos

    def pedir(self, url, datos=None):
        """GET/POST con reintentos y backoff ante caída (5xx o red). 4xx se devuelve como respuesta (p. ej. WAF 403)."""
        cuerpo = urllib.parse.urlencode(datos).encode("utf-8") if datos is not None else None
        ultimo = "sin respuesta"
        for intento in range(self.reintentos):
            try:
                with self.opener.open(urllib.request.Request(url, cuerpo), timeout=self.timeout) as r:
                    return r.status, Pagina(r.read().decode("utf-8", "replace"))
            except urllib.error.HTTPError as error:
                if error.code < 500:
                    return error.code, Pagina(error.read().decode("utf-8", "replace"))
                ultimo = f"HTTP {error.code}"
            except (urllib.error.URLError, OSError) as error:
                ultimo = str(getattr(error, "reason", error))
            if intento < self.reintentos - 1:
                self.dormir(self.backoff[min(intento, len(self.backoff) - 1)])
        raise ErrorPortal(f"el portal no responde tras {self.reintentos} intentos ({ultimo})")


class ClientePortales:
    def __init__(self, cfg, entorno=None, dormir=time.sleep, ahora=datetime.now):
        ajustes = cfg.proceso["Portales"]
        self.modo = ajustes["Modo"]
        self.ajustes = ajustes["Real" if self.modo == "real" else "Fixture"]
        self.maestro = cfg.maestro
        self.reintentos = int(cfg.maestro.get("NUMERO_REINTENTOS_SISTEMA", 3))
        self.backoff = tuple(ajustes["BackoffSegundos"])
        self.timeout = ajustes["TimeoutSegundos"]
        self.dormir = dormir
        if self.modo == "real":
            entorno = os.environ if entorno is None else entorno
            if entorno.get(self.ajustes["AutorizacionEnv"]) != "1":
                raise ErrorBloqueoPortal("BLOQUEO: falta la autorización de uso de los portales reales "
                                         f"({self.ajustes['AutorizacionEnv']}=1); no hay consulta")
            ventana = self.ajustes["VentanaOperativa"]
            if not (ventana["Desde"] <= f"{ahora():%H:%M}" <= ventana["Hasta"]):
                raise ErrorBloqueoPortal(f"BLOQUEO: fuera de la ventana operativa {ventana['Desde']}-{ventana['Hasta']}; "
                                         "no se fuerzan corridas fuera de ella")

    def _sesion(self):
        return Sesion(self.timeout, self.backoff, self.dormir, self.reintentos)

    # ---------- HU-006: Policía Nacional ----------
    def consultar_policia(self, cedula):
        """Devuelve {"resultado": "nombre"|"sin_resultado", "nombre": ...}; lanza ErrorPortal (caída) o RevisionHumana."""
        sesion = self._sesion()
        base = self.ajustes["UrlPolicia"]
        estado, pagina = sesion.pedir(base)
        if "aceptaOption" not in pagina.nombres:
            raise ErrorPortal(f"la Policía devolvió una estructura inesperada (HTTP {estado})")
        _, pagina = sesion.pedir(base, {"javax.faces.ViewState": pagina.valores.get("javax.faces.ViewState", ""),
                                        "aceptaOption": "true", "continuarBtn": "Continuar"})
        if "cuota" in pagina.texto("msgCaptcha").lower():
            raise RevisionHumana("cuota agotada del reCAPTCHA de la Policía")
        if "cedulaInput" not in pagina.nombres:
            raise ErrorPortal("la Policía no mostró el formulario de consulta")
        if self.modo == "real":
            raise RevisionHumana("reCAPTCHA v2 de la Policía: lo resuelve una persona (no se automatiza su evasión)")
        datos = {"javax.faces.ViewState": pagina.valores.get("javax.faces.ViewState", ""), "cedulaTipo": "cc",
                 "cedulaInput": str(cedula), "recaptchaCheck": "1", "j_idt17": "Consultar"}  # fixture: captcha ya resuelto
        _, resultado = sesion.pedir(urllib.parse.urljoin(base, "antecedentes.xhtml"), datos)
        if "retoImagenes" in resultado.ids:
            raise RevisionHumana("reto de imágenes del reCAPTCHA: lo resuelve una persona")
        if "nombreResultado" in resultado.ids:
            return {"resultado": "nombre", "nombre": resultado.texto("nombreResultado")}
        if "msgResultado" in resultado.ids:
            return {"resultado": "sin_resultado", "nombre": None}
        raise ErrorPortal("la Policía devolvió una respuesta sin resultado reconocible")

    # ---------- HU-007: Procuraduría ----------
    def consultar_procuraduria(self, tipo_codigo, numero, nombre, captchas):
        """Devuelve {"resultado": "nombre"|"sin_nombre", "nombre", "antecedentes"}. Lanza ErrorPortal o ErrorCaptcha."""
        sesion = self._sesion()
        url = self.ajustes["UrlProcuraduria"]
        estado, pagina = sesion.pedir(url)
        if estado == 403:
            raise ErrorPortal("la Procuraduría bloquea la página principal (WAF, HTTP 403)")
        if "continuarBtn" not in pagina.nombres:
            raise ErrorPortal("la Procuraduría devolvió el «formulario de atención de incidentes» u otra estructura inesperada")
        _, pagina = sesion.pedir(url, {"__VIEWSTATE": pagina.valores.get("__VIEWSTATE", ""), "rblAcepto": "1",
                                       "continuarBtn": "Continuar"})
        maximo = int(self.maestro.get("CAPTCHA_MAX_REINTENTOS", 3))
        for _ in range(maximo):
            if "lblPregunta" not in pagina.ids:
                raise ErrorPortal("la Procuraduría no mostró la pregunta del captcha")
            try:
                respuesta = captchas.resolver(pagina.texto("lblPregunta"), numero, nombre)
            except ErrorCaptcha as error:
                if error.codigo == SERVICIO_NO_DISPONIBLE:
                    raise
                # el servicio no resuelve esta familia: se pide otra pregunta con el botón de refresco (cuenta como intento)
                _, pagina = sesion.pedir(url, {"__VIEWSTATE": pagina.valores.get("__VIEWSTATE", ""), "ImageButton1.x": "1",
                                               "ImageButton1.y": "1"})
                continue
            _, pagina = sesion.pedir(url, {
                "__VIEWSTATE": pagina.valores.get("__VIEWSTATE", ""), "txtNombre": nombre, "ddlTipoID": tipo_codigo,
                "txtNumID": numero, "txtCorreoEle": "", "txtObservaciones": "", "txtRespuestaPregunta": respuesta,
                "btnExportar": "Consultar"})
            if "divDatosCiudadano" in pagina.ids:
                texto_estado = pagina.texto("lblEstado")
                return {"resultado": "nombre", "nombre": pagina.texto("lblNombre"),
                        "antecedentes": bool(re.search(r"\bpresenta antecedentes", texto_estado)) and not re.search(r"\bno presenta", texto_estado)}
            if "no se encontr" in pagina.texto("lblMensaje").lower():
                return {"resultado": "sin_nombre", "nombre": None, "antecedentes": None}
        raise ErrorCaptcha(MAX_REINTENTOS, f"{maximo} intentos")

    def verificar_url_procuraduria(self):
        """Antes de la primera corrida real: ¿la URL vigente responde con el formulario esperado? (HU-007 §4, C-14)."""
        estado, pagina = self._sesion().pedir(self.ajustes["UrlProcuraduria"])
        return {"http": estado, "formulario_esperado": "continuarBtn" in pagina.nombres,
                "incidentes": "txtIncidente" in pagina.nombres}
