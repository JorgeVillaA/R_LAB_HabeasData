"""HU-026a: cliente del servicio de resolución de captchas (el contratado por CISA; en el lab, su doble local).

El bot NO calcula la respuesta: envía la pregunta (más el documento y el nombre cuando aplica) y usa lo que el servicio
devuelve. Códigos: CAPTCHA_SERVICIO_NO_DISPONIBLE (tras NUMERO_REINTENTOS_SISTEMA reintentos con backoff),
FAMILIA_NO_SOPORTADA y DATO_FALTANTE (el servicio no puede resolver; no se inventa respuesta) y CAPTCHA_MAX_REINTENTOS
(lo emite quien consume el servicio cuando el portal rechaza N respuestas: ver portales.consultar_procuraduria).
"""
import json
import time
import urllib.error
import urllib.request

SERVICIO_NO_DISPONIBLE = "CAPTCHA_SERVICIO_NO_DISPONIBLE"
MAX_REINTENTOS = "CAPTCHA_MAX_REINTENTOS"


class ErrorCaptcha(Exception):
    def __init__(self, codigo, detalle=""):
        super().__init__(f"{codigo}: {detalle}" if detalle else codigo)
        self.codigo = codigo


class ServicioCaptchas:
    def __init__(self, url, reintentos=3, backoff=(1, 2, 4), timeout=10, dormir=time.sleep):
        self.url, self.reintentos, self.backoff, self.timeout, self.dormir = url, int(reintentos), tuple(backoff), timeout, dormir
        self.llamadas = 0

    def resolver(self, pregunta, documento=None, nombre=None):
        cuerpo = json.dumps({"pregunta": pregunta, "documento": documento, "nombre": nombre}, ensure_ascii=False).encode("utf-8")
        for intento in range(self.reintentos):
            self.llamadas += 1
            try:
                pedido = urllib.request.Request(self.url, cuerpo, {"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(pedido, timeout=self.timeout) as respuesta:
                    return json.loads(respuesta.read())["respuesta"]
            except urllib.error.HTTPError as error:
                if error.code == 422:  # el servicio entendió y dijo que no puede: no se reintenta
                    raise ErrorCaptcha(json.loads(error.read() or b"{}").get("codigo", "ERROR_DE_SERVICIO")) from error
            except (urllib.error.URLError, OSError, ValueError):
                pass
            if intento < self.reintentos - 1:
                self.dormir(self.backoff[min(intento, len(self.backoff) - 1)])
        raise ErrorCaptcha(SERVICIO_NO_DISPONIBLE, f"{self.reintentos} intentos sin respuesta")
