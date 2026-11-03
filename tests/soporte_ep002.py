"""Soporte de EP-002: doble de Zeus + clones de portales + doble del servicio de captchas, todo en loopback y sintético."""
import json

from tests.soporte import PruebaConDoble, RADICADOS
from dobles.portales.captchas import ServicioCaptchas as DobleCaptchas
from dobles.portales.servidor import DoblePortales
from habeasdata.captcha import ServicioCaptchas
from habeasdata.portales import ClientePortales


def apellidos_primero(nombre):
    """Policía devuelve «apellidos y luego nombres»: los fixtures traen nombres y luego apellidos (dos y dos)."""
    c = nombre.split()
    return " ".join(c[-2:] + c[:-2]) if len(c) >= 3 else nombre


def padrones(radicados=RADICADOS):
    policia, procuraduria = {}, {}
    for r in radicados:
        numero, nombre = str(r["NOIDENTIFICACIONDELCLIENTE"]), r["NOMBREDELCLIENTE"].strip()
        if not nombre or not numero.isdigit():
            continue
        if r["TIPODEIDENTIFICACION"] == "CEDULA DE CIUDADANIA":
            policia[numero] = apellidos_primero(nombre)
            procuraduria[("1", numero)] = {"nombre": nombre, "antecedentes": False}
        elif r["TIPODEIDENTIFICACION"] == "NIT":
            procuraduria[("2", numero)] = {"nombre": nombre, "antecedentes": False}
    return policia, procuraduria


class PruebaIdentidad(PruebaConDoble):
    """Levanta los tres dobles de EP-002 además del de Zeus. `self.portales` y `self.captchas` son los clientes del robot."""

    def setUp(self):
        super().setUp()
        self.web = DoblePortales().iniciar()
        self.addCleanup(self.web.detener)
        self.servicio = DobleCaptchas().iniciar()
        self.addCleanup(self.servicio.detener)
        policia, procuraduria = padrones()
        self.web.estado.configurar({"policia_padron": policia, "procuraduria_padron": procuraduria})
        ajustes = self.cfg.proceso["Portales"]
        ajustes["BackoffSegundos"] = [0]
        ajustes["Fixture"].update(UrlPolicia=f"{self.web.url}/policia/WebJudicial/index.xhtml",
                                  UrlProcuraduria=f"{self.web.url}/procuraduria/consulta-de-antecedentes.aspx",
                                  UrlCaptchas=f"http://127.0.0.1:{self.servicio.puerto}/resolver")
        self.portales = ClientePortales(self.cfg, dormir=lambda s: None)
        self.captchas = ServicioCaptchas(ajustes["Fixture"]["UrlCaptchas"], 3, (0,), 5, dormir=lambda s: None)

    def configurar_web(self, **cambios):
        with self.web.estado.bloqueo:
            self.web.estado.configurar(cambios)

    def caso(self, id_radicado):
        """Caso normalizado (como lo entrega HU-003) de un radicado del fixture."""
        from habeasdata import ep001
        return ep001.extraer(self.cliente, self.cfg, str(id_radicado))
