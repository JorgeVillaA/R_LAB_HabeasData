"""Clones técnicos de los portales del Estado (Policía Nacional y Procuraduría) para el banco y la revisión en Chrome.

Fieles técnicamente, no visualmente: sin logotipos ni identidad oficial. Replican la estructura que inspeccionó Villa
(2026-10-30): campos, nombres de control, flujo y comportamientos de fallo. Datos 100 % sintéticos. Solo biblioteca estándar.

Procuraduría  /procuraduria/consulta-de-antecedentes.aspx
  términos (radios + continuarBtn) → formulario (txtNombre, ddlTipoID, txtNumID, txtCorreoEle, txtObservaciones, botón de
  imagen de refresco Media/Image/refresh.png, lblPregunta, txtRespuestaPregunta, btnExportar) → bloque «Datos del ciudadano»
  en la misma página. Captcha: pregunta en lenguaje natural que rota entre 4 familias (aritmética, capital de Colombia,
  contextual del documento, contextual del nombre), con erratas conocidas («Capital del Vallle del Cauca»).
  Comportamientos: normal | caido | waf (página principal bloqueada) | incidentes (la URL webcert devuelve el
  «formulario de atención de incidentes»); y por documento: antecedentes, sin nombre.
Policía       /policia/WebJudicial/index.xhtml  (JSF, javax.faces.ViewState)
  términos (radio aceptaOption + continuarBtn) → formulario (cedulaTipo solo cédula, cedulaInput, casilla reCAPTCHA «No soy
  un robot» que puede escalar a reto de imágenes) → resultado con «Apellidos y Nombres:».
  Comportamientos: normal | cuota («este sitio supera la cuota gratuita de reCAPTCHA») | caido | reto.
  La casilla del doble la marca quien consulta (en el lab, un fixture; en modo real, una persona: el bot no evade el captcha).
"""
import base64
import html
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

PNG_1X1 = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
TIPOS_PROCURADURIA = [("1", "Cédula de ciudadanía"), ("2", "Nit"), ("3", "Pasaporte"), ("4", "Tarjeta de identidad"),
                      ("5", "Cédula extranjería")]
FAMILIAS = ("aritmetica", "capital", "documento", "nombre")
PIE = "<p>Clon técnico del lab R_LAB_HabeasData: datos sintéticos, sin identidad oficial.</p>"


def pagina(titulo, cuerpo):
    return (f"<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\"><title>{html.escape(titulo)}</title></head>"
            f"<body><h1>{html.escape(titulo)}</h1>{cuerpo}{PIE}</body></html>").encode("utf-8")


class Estado:
    def __init__(self):
        self.bloqueo = threading.Lock()
        self.policia_padron = {}        # cédula → "APELLIDOS NOMBRES"
        self.procuraduria_padron = {}   # (código tipo, número) → {"nombre", "antecedentes", "sin_nombre"}
        self.policia_modo = "normal"
        self.procuraduria_modo = "normal"
        self.captcha_rechaza = False    # la Procuraduría rechaza toda respuesta (escenario «rechazada por el portal»)
        self.familias = list(FAMILIAS)  # orden de rotación de las preguntas
        self.contador_preguntas = 0
        self.sesiones = {}
        self.consultas = {"policia": [], "procuraduria": [], "preguntas": []}

    def configurar(self, cambios):
        for clave in ("policia_modo", "procuraduria_modo", "captcha_rechaza", "familias"):
            if clave in cambios:
                setattr(self, clave, cambios[clave])
        if "policia_padron" in cambios:
            self.policia_padron = dict(cambios["policia_padron"])
        if "procuraduria_padron" in cambios:
            self.procuraduria_padron = {tuple(k): dict(v) for k, v in cambios["procuraduria_padron"].items()}
        if cambios.get("reiniciar"):
            self.contador_preguntas = 0
            self.sesiones.clear()
            self.consultas = {"policia": [], "procuraduria": [], "preguntas": []}

    def siguiente_pregunta(self):
        """Pregunta determinista: la familia rota en cada carga o refresco (como el portal real)."""
        n = self.contador_preguntas
        self.contador_preguntas += 1
        familia = self.familias[n % len(self.familias)]
        if familia == "aritmetica":
            a, b, op = 2 + n % 7, 3 + (n * 2) % 6, ("+", "X")[n % 2]
            texto, respuesta = f"¿Cuánto es {a} {op} {b}?", str(a + b if op == "+" else a * b)
            return {"familia": familia, "texto": texto, "respuesta": respuesta}
        if familia == "capital":
            texto, respuesta = [("¿Cuál es la capital de Colombia?", "Bogotá"),
                                ("¿Cuál es la capital del Vallle del Cauca?", "Cali")][n % 2]  # errata real del portal
            return {"familia": familia, "texto": texto, "respuesta": respuesta}
        if familia == "documento":
            variante = ("ultimos", 2) if n % 2 == 0 else ("primeros", 3)
            etiqueta = "dos últimos" if variante == ("ultimos", 2) else "tres primeros"
            return {"familia": familia, "texto": f"¿Escriba los {etiqueta} dígitos del documento a consultar?", "variante": variante}
        cantidad = n % 2 == 1
        texto = ("¿Escriba la cantidad de letras del primer nombre de la persona a la cual esta consultando?" if cantidad
                 else "¿Cuál es el primer nombre de la persona a la cual esta consultando?")
        return {"familia": familia, "texto": texto, "cantidad": cantidad}


def respuesta_esperada(pregunta, nombre, numero):
    if pregunta["familia"] in ("aritmetica", "capital"):
        return pregunta["respuesta"]
    if pregunta["familia"] == "documento":
        cual, cuantos = pregunta["variante"]
        digitos = "".join(c for c in numero if c.isdigit())
        return digitos[:cuantos] if cual == "primeros" else digitos[-cuantos:]
    primero = (nombre.split() or [""])[0]
    return str(len(primero)) if pregunta["cantidad"] else primero


def crear_servidor(estado, puerto=0):
    class Manejador(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        # ---------- utilidades ----------
        def responder(self, codigo, cuerpo, tipo="text/html; charset=utf-8", cookie=None):
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(cuerpo)))
            if cookie:
                self.send_header("Set-Cookie", f"sid={cookie}; Path=/")
            self.end_headers()
            self.wfile.write(cuerpo)

        def sesion(self):
            for parte in (self.headers.get("Cookie") or "").split(";"):
                if parte.strip().startswith("sid="):
                    sid = parte.strip()[4:]
                    if sid in estado.sesiones:
                        return sid, estado.sesiones[sid], None
            sid = secrets.token_hex(8)
            estado.sesiones[sid] = {}
            return sid, estado.sesiones[sid], sid

        def formulario(self):
            largo = int(self.headers.get("Content-Length") or 0)
            crudo = self.rfile.read(largo).decode("utf-8")
            return {k: v[0] for k, v in parse_qs(crudo, keep_blank_values=True).items()}

        def do_GET(self):
            ruta = urlsplit(self.path).path.lower()
            with estado.bloqueo:
                if ruta.endswith("/media/image/refresh.png"):
                    return self.responder(200, PNG_1X1, "image/png")
                if ruta.startswith("/procuraduria"):
                    return self.procuraduria_get(ruta)
                if ruta.startswith("/policia"):
                    return self.policia_get(ruta)
            self.responder(404, pagina("No encontrado", ""))

        def do_POST(self):
            ruta = urlsplit(self.path).path.lower()
            datos = self.formulario()
            with estado.bloqueo:
                if ruta.startswith("/procuraduria"):
                    return self.procuraduria_post(datos)
                if ruta.startswith("/policia"):
                    return self.policia_post(ruta, datos)
            self.responder(404, pagina("No encontrado", ""))

        # ---------- Procuraduría ----------
        def procuraduria_get(self, ruta):
            modo = estado.procuraduria_modo
            if modo == "caido":
                return self.responder(503, pagina("Servicio no disponible", "<p>Intente más tarde.</p>"))
            if modo == "waf":
                return self.responder(403, pagina("Request blocked", "<p>The requested URL was rejected. Support ID: 0000000000.</p>"))
            if modo == "incidentes":
                return self.responder(200, pagina("Formulario de atención de incidentes", (
                    "<form method=\"post\" action=\"incidentes\"><label>Describa el incidente</label>"
                    "<textarea name=\"txtIncidente\"></textarea><input type=\"submit\" name=\"btnEnviarIncidente\" value=\"Enviar\"></form>")))
            sid, sesion, nueva = self.sesion()
            sesion.clear()
            self.responder(200, pagina("Consulta de antecedentes", (
                "<form method=\"post\" action=\"consulta-de-antecedentes.aspx\">"
                f"<input type=\"hidden\" name=\"__VIEWSTATE\" value=\"{secrets.token_hex(6)}\">"
                "<p>Términos de uso: ¿acepta?</p>"
                "<input type=\"radio\" id=\"rbAcepto\" name=\"rblAcepto\" value=\"1\"><label for=\"rbAcepto\">Acepto</label>"
                "<input type=\"radio\" id=\"rbNoAcepto\" name=\"rblAcepto\" value=\"0\"><label for=\"rbNoAcepto\">No acepto</label>"
                "<input type=\"submit\" id=\"continuarBtn\" name=\"continuarBtn\" value=\"Continuar\"></form>")), cookie=nueva or sid)

        def procuraduria_post(self, datos):
            modo = estado.procuraduria_modo
            if modo == "caido":
                return self.responder(503, pagina("Servicio no disponible", "<p>Intente más tarde.</p>"))
            sid, sesion, nueva = self.sesion()
            if "continuarBtn" in datos:
                if datos.get("rblAcepto") != "1":
                    return self.responder(200, pagina("Consulta de antecedentes", "<p id=\"lblMensaje\">Debe aceptar los términos.</p>"), cookie=nueva)
                sesion["acepto"] = True
                sesion["pregunta"] = estado.siguiente_pregunta()
                estado.consultas["preguntas"].append(sesion["pregunta"]["texto"])
                return self.responder(200, self.formulario_procuraduria(sesion, {}), cookie=nueva)
            if not sesion.get("acepto"):
                return self.responder(200, pagina("Consulta de antecedentes", "<p id=\"lblMensaje\">Sesión sin términos aceptados.</p>"), cookie=nueva)
            if "ibRefrescar.x" in datos or "ibRefrescar" in datos:
                sesion["pregunta"] = estado.siguiente_pregunta()
                estado.consultas["preguntas"].append(sesion["pregunta"]["texto"])
                return self.responder(200, self.formulario_procuraduria(sesion, datos), cookie=nueva)
            nombre, numero, tipo = datos.get("txtNombre", ""), datos.get("txtNumID", ""), datos.get("ddlTipoID", "1")
            esperada = respuesta_esperada(sesion["pregunta"], nombre, numero)
            estado.consultas["procuraduria"].append({"tipo": tipo, "numero": numero, "respuesta": datos.get("txtRespuestaPregunta", "")})
            if estado.captcha_rechaza or datos.get("txtRespuestaPregunta", "").strip().lower() != esperada.lower():
                sesion["pregunta"] = estado.siguiente_pregunta()
                estado.consultas["preguntas"].append(sesion["pregunta"]["texto"])
                return self.responder(200, self.formulario_procuraduria(
                    sesion, datos, "<span id=\"lblMensaje\">La respuesta a la pregunta es incorrecta.</span>"), cookie=nueva)
            registro = estado.procuraduria_padron.get((tipo, numero))
            if registro is None or registro.get("sin_nombre"):
                bloque = "<span id=\"lblMensaje\">No se encontró información para el documento consultado.</span>"
            else:
                estado_texto = ("El ciudadano presenta antecedentes" if registro.get("antecedentes")
                                else "El ciudadano no presenta antecedentes")
                bloque = ("<div id=\"divDatosCiudadano\"><h2>Datos del ciudadano</h2>"
                          f"<p>Nombre: <span id=\"lblNombre\">{html.escape(registro['nombre'])}</span></p>"
                          f"<p>Estado: <span id=\"lblEstado\">{estado_texto}</span></p></div>")
            self.responder(200, self.formulario_procuraduria(sesion, datos, bloque), cookie=nueva)

        def formulario_procuraduria(self, sesion, valores, extra=""):
            opciones = "".join(f"<option value=\"{c}\"{' selected' if valores.get('ddlTipoID') == c else ''}>{html.escape(t)}</option>"
                               for c, t in TIPOS_PROCURADURIA)
            v = lambda campo: html.escape(valores.get(campo, ""))  # noqa: E731
            return pagina("Consulta de antecedentes", (
                "<form method=\"post\" action=\"consulta-de-antecedentes.aspx\">"
                f"<input type=\"hidden\" name=\"__VIEWSTATE\" value=\"{secrets.token_hex(6)}\">"
                f"<label>Nombre</label><input type=\"text\" id=\"txtNombre\" name=\"txtNombre\" value=\"{v('txtNombre')}\">"
                f"<label>Tipo de documento</label><select id=\"ddlTipoID\" name=\"ddlTipoID\">{opciones}</select>"
                f"<label>Número</label><input type=\"text\" id=\"txtNumID\" name=\"txtNumID\" value=\"{v('txtNumID')}\">"
                f"<label>Correo</label><input type=\"text\" id=\"txtCorreoEle\" name=\"txtCorreoEle\" value=\"{v('txtCorreoEle')}\">"
                "<label>Observaciones</label><textarea id=\"txtObservaciones\" name=\"txtObservaciones\"></textarea>"
                "<input type=\"image\" id=\"ibRefrescar\" name=\"ibRefrescar\" src=\"/Media/Image/refresh.png\" alt=\"Refrescar pregunta\">"
                f"<p>Pregunta: <span id=\"lblPregunta\">{html.escape(sesion['pregunta']['texto'])}</span></p>"
                "<input type=\"text\" id=\"txtRespuestaPregunta\" name=\"txtRespuestaPregunta\" value=\"\">"
                "<input type=\"submit\" id=\"btnExportar\" name=\"btnExportar\" value=\"Consultar\">"
                f"</form><div id=\"resultado\">{extra}</div>"))

        # ---------- Policía ----------
        def policia_get(self, ruta):
            if estado.policia_modo == "caido":
                return self.responder(503, pagina("Servicio no disponible", "<p>Intente más tarde.</p>"))
            sid, sesion, nueva = self.sesion()
            sesion.clear()
            self.responder(200, pagina("Consulta de antecedentes judiciales", (
                "<form id=\"formAcepta\" method=\"post\" action=\"/policia/WebJudicial/index.xhtml\">"
                f"<input type=\"hidden\" name=\"javax.faces.ViewState\" value=\"{secrets.token_hex(8)}\">"
                "<p>Términos de uso: ¿acepta?</p>"
                "<input type=\"radio\" id=\"aceptaOption\" name=\"aceptaOption\" value=\"true\"><label for=\"aceptaOption\">Acepto</label>"
                "<input type=\"radio\" name=\"aceptaOption\" value=\"false\"><label>No acepto</label>"
                "<input type=\"submit\" id=\"continuarBtn\" name=\"continuarBtn\" value=\"Continuar\"></form>")), cookie=nueva or sid)

        def policia_post(self, ruta, datos):
            if estado.policia_modo == "caido":
                return self.responder(503, pagina("Servicio no disponible", "<p>Intente más tarde.</p>"))
            sid, sesion, nueva = self.sesion()
            if "continuarBtn" in datos:
                if datos.get("aceptaOption") != "true":
                    return self.responder(200, pagina("Consulta de antecedentes judiciales", "<p>Debe aceptar los términos.</p>"), cookie=nueva)
                sesion["acepto"] = True
                return self.responder(200, self.formulario_policia(), cookie=nueva)
            if not sesion.get("acepto"):
                return self.responder(200, pagina("Consulta de antecedentes judiciales", "<p>Sesión sin términos aceptados.</p>"), cookie=nueva)
            numero = datos.get("cedulaInput", "")
            estado.consultas["policia"].append({"cedula": numero, "recaptcha": "recaptchaCheck" in datos})
            if estado.policia_modo == "cuota":
                return self.responder(200, self.formulario_policia(), cookie=nueva)
            if "recaptchaCheck" not in datos:
                return self.responder(200, self.formulario_policia("<div id=\"msgCaptcha\">Debe verificar que no es un robot.</div>"), cookie=nueva)
            if estado.policia_modo == "reto":
                return self.responder(200, pagina("Verificación adicional", (
                    "<div id=\"retoImagenes\"><p>Seleccione todas las imágenes con semáforos.</p>"
                    "<p>Este reto lo resuelve una persona.</p></div>")), cookie=nueva)
            nombre = estado.policia_padron.get(numero)
            if nombre is None:
                return self.responder(200, self.formulario_policia("<div id=\"msgResultado\">No se encontraron registros para el documento.</div>"), cookie=nueva)
            self.responder(200, pagina("Resultado de la consulta", (
                "<table id=\"resultado\"><tr><td>Apellidos y Nombres:</td>"
                f"<td id=\"nombreResultado\">{html.escape(nombre)}</td></tr></table>")), cookie=nueva)

        def formulario_policia(self, extra=""):
            captcha = ("<div id=\"msgCaptcha\">Este sitio supera la cuota gratuita de reCAPTCHA. "
                       "Para uso comercial, habilite la facturación.</div>" if estado.policia_modo == "cuota" else
                       "<div class=\"g-recaptcha\" id=\"recaptcha\"><label>"
                       "<input type=\"checkbox\" id=\"recaptcha-anchor\" name=\"recaptchaCheck\" value=\"1\"> No soy un robot</label></div>")
            return pagina("Consulta de antecedentes judiciales", (
                "<form id=\"formConsulta\" method=\"post\" action=\"/policia/WebJudicial/antecedentes.xhtml\">"
                f"<input type=\"hidden\" name=\"javax.faces.ViewState\" value=\"{secrets.token_hex(8)}\">"
                "<label>Tipo de documento</label><select id=\"cedulaTipo\" name=\"cedulaTipo\"><option value=\"cc\" selected>Cédula de Ciudadanía</option></select>"
                "<label>Número de documento</label><input type=\"text\" id=\"cedulaInput\" name=\"cedulaInput\">"
                f"{captcha}<input type=\"submit\" id=\"j_idt17\" name=\"j_idt17\" value=\"Consultar\"></form>{extra}"))

    class Servidor(ThreadingHTTPServer):
        def handle_error(self, request, client_address):  # Chrome corta conexiones ociosas: no es un fallo del clon
            pass

    servidor = Servidor(("127.0.0.1", puerto), Manejador)
    servidor.daemon_threads = True
    return servidor


class DoblePortales:
    def __init__(self):
        self.estado = Estado()
        self._servidor = None

    def iniciar(self, puerto=0):
        self._servidor = crear_servidor(self.estado, puerto)
        self.puerto = self._servidor.server_address[1]
        threading.Thread(target=self._servidor.serve_forever, daemon=True).start()
        return self

    @property
    def url(self):
        return f"http://127.0.0.1:{self.puerto}"

    def detener(self):
        if self._servidor:
            self._servidor.shutdown()
            self._servidor.server_close()
            self._servidor = None


if __name__ == "__main__":
    import sys
    doble = DoblePortales().iniciar(int(sys.argv[1]) if len(sys.argv) > 1 else 8766)
    doble.estado.configurar({"policia_padron": {"1000000001": "LOPEZ RUIZ MARIA FERNANDA"},
                             "procuraduria_padron": {("1", "1000000001"): {"nombre": "MARIA FERNANDA LOPEZ RUIZ"}}})
    print(f"Clones de portales en {doble.url}/policia/WebJudicial/index.xhtml y {doble.url}/procuraduria/consulta-de-antecedentes.aspx")
    threading.Event().wait()
