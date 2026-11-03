"""Doble local del servicio externo de resolución de captchas (HU-026a): la interfaz del servicio contratado por CISA.

Entrada: la pregunta del captcha + el documento y el nombre cuando la pregunta los requiere. Salida: la respuesta, o un
código de error. El BOT no calcula la respuesta: la interpretación de la pregunta es responsabilidad de este servicio.
Familias soportadas: aritmética, contextual del documento y contextual del nombre. «Capital de Colombia» (HU-026b) queda
fuera del lab: se devuelve FAMILIA_NO_SOPORTADA y el caso va a gestión manual. Solo biblioteca estándar.

Insumo B2 / regla del «primer nombre»: primer componente del nombre en el orden recibido (nombres y luego apellidos).
"""
import json
import re
import threading
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FAMILIA_NO_SOPORTADA = "FAMILIA_NO_SOPORTADA"
DATO_FALTANTE = "DATO_FALTANTE"


def _sin_tildes(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()


def resolver(pregunta, documento=None, nombre=None):
    """Devuelve (respuesta, None) o (None, código_de_error)."""
    texto = _sin_tildes(pregunta or "")
    m = re.search(r"cuanto es\s+(\d+)\s*([+xX*])\s*(\d+)", texto)
    if m:
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        return str(a + b if op == "+" else a * b), None
    if "digitos" in texto and "documento" in texto:
        digitos = re.sub(r"\D", "", str(documento or ""))
        m = re.search(r"(dos|tres|2|3)\s+(primeros|ultimos)", texto) or re.search(r"(primeros|ultimos)\s+(dos|tres|2|3)", texto)
        if not digitos or not m:
            return (None, DATO_FALTANTE) if not digitos else (None, FAMILIA_NO_SOPORTADA)
        cantidad, lado = (m.group(1), m.group(2)) if m.group(1) in ("dos", "tres", "2", "3") else (m.group(2), m.group(1))
        cuantos = 2 if cantidad in ("dos", "2") else 3
        return (digitos[:cuantos] if lado == "primeros" else digitos[-cuantos:]), None
    if "primer nombre" in texto:
        componentes = str(nombre or "").split()
        if not componentes:
            return None, DATO_FALTANTE
        return (str(len(componentes[0])) if "cantidad" in texto else componentes[0]), None
    return None, FAMILIA_NO_SOPORTADA


class ServicioCaptchas:
    """Servicio HTTP en loopback: POST /resolver {pregunta, documento?, nombre?} → {respuesta} | {codigo}."""

    def __init__(self):
        self.modo = "normal"   # normal | no_disponible | respuesta_erronea
        self.llamadas = []
        self._servidor = None

    def configurar(self, modo="normal"):
        self.modo = modo

    def iniciar(self, puerto=0):
        servicio = self

        class Manejador(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                largo = int(self.headers.get("Content-Length") or 0)
                cuerpo = json.loads(self.rfile.read(largo) or b"{}")
                servicio.llamadas.append(cuerpo)
                if self.path != "/resolver":
                    return self._responder(404, {"codigo": "RUTA"})
                if servicio.modo == "no_disponible":
                    return self._responder(503, {"codigo": "SERVICIO_NO_DISPONIBLE"})
                respuesta, codigo = resolver(cuerpo.get("pregunta"), cuerpo.get("documento"), cuerpo.get("nombre"))
                if codigo:
                    return self._responder(422, {"codigo": codigo})
                if servicio.modo == "respuesta_erronea":
                    respuesta = "ERRONEA"
                self._responder(200, {"respuesta": respuesta})

            def _responder(self, estado, cuerpo):
                datos = json.dumps(cuerpo).encode("utf-8")
                self.send_response(estado)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(datos)))
                self.end_headers()
                self.wfile.write(datos)

        self._servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
        self.puerto = self._servidor.server_address[1]
        threading.Thread(target=self._servidor.serve_forever, daemon=True).start()
        return self

    def detener(self):
        if self._servidor:
            self._servidor.shutdown()
            self._servidor.server_close()
            self._servidor = None


if __name__ == "__main__":  # servicio local de captchas en el puerto 8767 (el de ConfiguracionProceso.json)
    import sys
    import threading
    servicio = ServicioCaptchas().iniciar(int(sys.argv[1]) if len(sys.argv) > 1 else 8767)
    print(f"Servicio de captchas en http://127.0.0.1:{servicio.puerto}/resolver")
    threading.Event().wait()
