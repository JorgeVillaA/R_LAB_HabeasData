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
import os
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

PNG_1X1 = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
TIPOS_PROCURADURIA = [("1", "Cédula de ciudadanía"), ("2", "Nit"), ("3", "Pasaporte"), ("4", "Tarjeta de identidad"),
                      ("5", "Cédula extranjería")]
FAMILIAS = ("aritmetica", "capital", "documento", "nombre")
PIE = "<p>Clon técnico del lab R_LAB_HabeasData: datos sintéticos, sin identidad oficial.</p>"

# ---------- front fiel (clones extraídos del front real de los portales, 2026-10-30) ----------
RAIZ_CLON = os.path.dirname(os.path.abspath(__file__))
TIPOS_ARCHIVO = {".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8",
                 ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
                 ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf",
                 ".svg": "image/svg+xml", ".map": "application/json", ".html": "text/html; charset=utf-8"}


def clon_html(portal, archivo):
    """HTML del clon fiel (front extraído del portal real)."""
    with open(os.path.join(RAIZ_CLON, portal, archivo), encoding="utf-8") as fh:
        return fh.read()


def con_texto(base, id_, texto):
    """Rellena el contenido textual del elemento con ese id (se escapa el texto)."""
    return con_html(base, id_, html.escape(texto or ""))


def con_html(base, id_, trozo):
    """Rellena el contenido del elemento con ese id, sin escapar (para HTML ya armado).
    Busca el cierre que balancea la etiqueta (el contenido tiene divs anidados)."""
    m = re.search(r'<(\w+)[^>]*\bid="%s"[^>]*>' % re.escape(id_), base)
    if not m:
        return base
    etiqueta = m.group(1)
    inicio = m.end()
    patron_apertura = re.compile(r'<%s\b' % etiqueta, re.I)
    patron_cierre = re.compile(r'</%s\s*>' % etiqueta, re.I)
    nivel, pos = 1, inicio
    while True:
        cierre = patron_cierre.search(base, pos)
        if not cierre:
            return base
        apertura = patron_apertura.search(base, pos)
        if apertura and apertura.start() < cierre.start():
            nivel += 1
            pos = apertura.end()
            continue
        nivel -= 1
        if nivel == 0:
            return base[:inicio] + trozo + base[cierre.start():]
        pos = cierre.end()


def con_visible(base, id_, visible=True):
    """Quita (o pone) display:none del elemento con ese id."""
    def ajusta(m):
        etiqueta = m.group(0)
        if visible:
            etiqueta = re.sub(r"display\s*:\s*none\s*;?", "", etiqueta)
        elif "display:none" not in etiqueta.replace(" ", ""):
            etiqueta = etiqueta[:-1] + ' style="display:none;">'
        return etiqueta
    return re.sub(r'<\w+[^>]*\bid="%s"[^>]*>' % re.escape(id_), ajusta, base, count=1)


def con_valor(base, campo, valor):
    """Rellena el value de un input por su id (para repintar el formulario)."""
    patron = re.compile(r'(<input[^>]*\bid="%s"[^>]*\bvalue=")([^"]*)(")' % re.escape(campo))
    if not patron.search(base):
        return base
    return patron.sub(lambda m: m.group(1) + html.escape(valor or "") + m.group(3), base, count=1)


def con_oculto(base, campo, valor):
    """Rellena el value de un input hidden por su name (ViewState, etc.)."""
    patron = re.compile(r'(<input[^>]*\bname="%s"[^>]*\bvalue=")([^"]*)(")' % re.escape(campo))
    if not patron.search(base):
        return base
    return patron.sub(lambda m: m.group(1) + html.escape(valor or "") + m.group(3), base, count=1)


def habilitada(base, id_):
    """Habilita el elemento con ese id (el JS del clon lo habilitaba; aquí la lógica la manda el servidor): quita `disabled`,
    `aria-disabled` y la clase `ui-state-disabled` (que trae `pointer-events:none` y haría que Chrome rechace el clic)."""
    def ajusta(m):
        etiqueta = re.sub(r'\s+(?:disabled="disabled"|aria-disabled="true")', "", m.group(0))
        return re.sub(r'\s+ui-state-disabled', "", etiqueta)
    return re.sub(r'<\w+[^>]*\bid="%s"[^>]*>' % re.escape(id_), ajusta, base, count=1)


def sin_manejador_de_clic(base, id_):
    """Quita el onclick del elemento con ese id (el original cancela el envío con `return false`)."""
    return re.sub(r'(<\w+[^>]*\bid="%s"[^>]*?)\s+onclick="[^"]*"' % re.escape(id_), lambda m: m.group(1), base, count=1)


def sin_manejador_de_envio(base, id_):
    """Quita el onsubmit del formulario con ese id: llama a `WebForm_OnSubmit()` del JS original, que aquí no se sirve; en Chrome
    la función inexistente cancelaría el envío."""
    return re.sub(r'(<form[^>]*\bid="%s"[^>]*?)\s+onsubmit="[^"]*"' % re.escape(id_), lambda m: m.group(1), base, count=1)


MARCA_RECAPTCHA = ("document.getElementById('recaptchaCheck').checked=true;"
                   "document.getElementById('g-recaptcha-response').value='clon-local-no-verificado';"
                   "this.setAttribute('aria-checked','true');")


# Sin el JS de maquetación del portal, el panel de texto (#j_idt8, 248 px) se solapa con el radio de aceptación y Chrome rechaza el clic
# («element click intercepted»): se sube el bloque de aceptación sobre el panel. Solo cambia el orden de apilado, no el aspecto.
CAPA_DE_TERMINOS = "<style>#j_idt11{position:relative;z-index:5}</style>"


def sin_scripts(base):
    """Quita todos los <script>: la lógica del clon la manda el servidor (y se evita el JS externo)."""
    return re.sub(r"<script\b[^>]*>.*?</script>", "", base, flags=re.S)



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
            if isinstance(cuerpo, str):
                cuerpo = cuerpo.encode("utf-8")
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
            original = unquote(urlsplit(self.path).path)
            ruta = original.lower()
            estatico = self.estatico(original, ruta)
            if estatico is not None:
                return estatico
            if ruta.endswith("/media/image/refresh.png"):
                return self.responder(200, PNG_1X1, "image/png")
            if os.path.splitext(ruta)[1] not in ("", ".aspx", ".xhtml", ".html", ".htm"):
                # Un recurso que el clon no trae (fuente, imagen, mapa...) es un 404: nunca debe reiniciar la sesión del portal
                # (Chrome los pide mientras el robot trabaja y borraba los términos ya aceptados).
                return self.responder(404, pagina("No encontrado", ""))
            with estado.bloqueo:
                if ruta.endswith("/media/image/refresh.png"):
                    return self.responder(200, PNG_1X1, "image/png")
                if ruta.startswith("/procuraduria"):
                    return self.procuraduria_get(ruta)
                if ruta.startswith("/policia"):
                    return self.policia_get(ruta)
            self.responder(404, pagina("No encontrado", ""))

        def estatico(self, original, ruta):
            """Sirve los assets reales de los clones (css/js/img/fonts) con su ruta del portal."""
            for prefijo, portal in (("/policia/webjudicial/", "policia"), ("/policia/", "policia"),
                                    ("/procuraduria/", "procuraduria")):
                if ruta.startswith(prefijo):
                    relativo = original[len(prefijo):]
                    break
            else:
                return None
            if not relativo or relativo.endswith("/"):
                return None
            carpeta = os.path.join(RAIZ_CLON, portal)
            destino = os.path.normpath(os.path.join(carpeta, relativo))
            if not destino.startswith(os.path.normpath(carpeta) + os.sep):
                return None
            extension = os.path.splitext(destino)[1].lower()
            if extension not in TIPOS_ARCHIVO or not os.path.isfile(destino):
                return None
            with open(destino, "rb") as fh:
                return self.responder(200, fh.read(), TIPOS_ARCHIVO[extension])

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
            base = sin_scripts(clon_html("procuraduria", "index.html"))
            base = con_oculto(base, "__VIEWSTATE", secrets.token_hex(6))
            base = con_visible(base, "pnlTerminos", True)
            base = con_visible(base, "pnlConsulta", False)
            base = habilitada(base, "continuarBtn")
            base = sin_manejador_de_envio(base, "form1")
            self.responder(200, base, cookie=nueva or sid)

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
            if "ImageButton1.x" in datos or "ImageButton1" in datos:
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
            base = sin_scripts(clon_html("procuraduria", "index.html"))
            base = con_oculto(base, "__VIEWSTATE", secrets.token_hex(6))
            base = con_visible(base, "pnlTerminos", False)
            base = con_visible(base, "pnlConsulta", True)
            base = con_texto(base, "lblPregunta", sesion["pregunta"]["texto"])
            for campo in ("txtNombre", "txtNumID", "txtCorreoEle", "txtObservaciones"):
                base = con_valor(base, campo, valores.get(campo, ""))
            base = sin_manejador_de_clic(base, "ImageButton1")
            base = sin_manejador_de_envio(base, "form1")
            # Sin resultado todavía, el bloque va vacío: así «divDatosCiudadano o lblMensaje» solo existe en la respuesta y el robot
            # (Chrome, asíncrono) no lee por error la página anterior mientras la nueva carga.
            base = con_html(base, "divResultado", extra or "")
            return base

        # ---------- Policía ----------
        def policia_get(self, ruta):
            if estado.policia_modo == "caido":
                return self.responder(503, pagina("Servicio no disponible", "<p>Intente más tarde.</p>"))
            sid, sesion, nueva = self.sesion()
            sesion.clear()
            base = sin_scripts(clon_html("policia", "index.html"))
            base = con_oculto(base, "javax.faces.ViewState", secrets.token_hex(8))
            base = habilitada(base, "continuarBtn")
            base = base.replace("</head>", CAPA_DE_TERMINOS + "</head>", 1)
            self.responder(200, base, cookie=nueva or sid)

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
                return self.responder(200, self.formulario_policia(
                    "<div id=\"retoImagenes\"><p>Seleccione todas las imágenes con semáforos.</p>"
                    "<p>Este reto lo resuelve una persona.</p></div>"), cookie=nueva)
            nombre = estado.policia_padron.get(numero)
            if nombre is None:
                return self.responder(200, self.formulario_policia("<div id=\"msgResultado\">No se encontraron registros para el documento.</div>"), cookie=nueva)
            self.responder(200, self.formulario_policia(
                "<table id=\"resultado\"><tr><td>Apellidos y Nombres:</td>"
                f"<td id=\"nombreResultado\">{html.escape(nombre)}</td></tr></table>"), cookie=nueva)

        def formulario_policia(self, extra=""):
            base = sin_scripts(clon_html("policia", "antecedentes.html"))
            base = con_oculto(base, "javax.faces.ViewState", secrets.token_hex(8))
            base = sin_manejador_de_clic(base, "j_idt17")
            base = re.sub(r'(<span[^>]*\bid="recaptchaCheckbox")', lambda m: m.group(1) + ' onclick="%s"' % MARCA_RECAPTCHA, base, count=1)
            if estado.policia_modo == "cuota":
                base = con_html(base, "captchaAntecedentes",
                                "<div id=\"msgCaptcha\">Este sitio supera la cuota gratuita de reCAPTCHA. "
                                "Para uso comercial, habilite la facturación.</div>")
            if extra:
                base = con_html(base, "resultadoAntecedentes", extra)
                base = con_visible(base, "resultadoAntecedentes", True)
            return base

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
