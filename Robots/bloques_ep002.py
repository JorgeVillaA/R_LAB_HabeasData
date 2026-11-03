"""Bloques de EP-002 (HU-006, HU-007, HU-026a, HU-008) del robot LabHabeasData: flujo legible a cliente, navegación en Chrome.

Convenciones (las mismas de EP-001): grupos por historia, cada decisión es un `evaluateIf` visible con su descripción, y el
Python (`habeasdata.pasos`) solo lee el TEXTO de la página (lógica pura), llama al servicio de captchas, compara nombres y
escribe logs. La navegación (abrir, aceptar términos, escribir, pulsar) son bloques de Chrome: `openbrowser` con
`extra:{default:"chrome"}` y `openUrl` aparte, selectores por DOM, sin mouse ni imágenes.

Máquina de estados por radicado en `locDicIdentidad["etapa"]`: inicio → policia | procuraduria → comparar → validada |
excepcion_negocio_3 | ...; cada decisión pregunta en qué etapa va el caso (así la profundidad bajo el `for` es de 2).
Política innegociable: el reCAPTCHA de la Policía no se evade: en modo real el robot se detiene (revisión humana).
"""
import json


def web_clic(descripcion, xpath):
    return {"father": "click_web", "description": descripcion, "command": {
        "data": xpath, "data_type": "xpath", "before": "0", "wait_time": "10", "after": "0", "move": "False"}}


def web_escribir(descripcion, xpath, texto):
    return {"father": "sendkey_web", "description": descripcion, "command": {
        "data": xpath, "data_type": "xpath", "wait_time": "10", "text": texto, "special": ""}}


def web_texto(descripcion, xpath, variable):
    return {"father": "textObject", "description": descripcion, "command": xpath, "option": "xpath", "getvar": variable}


def web_esperar(descripcion, xpath):
    return {"father": "waitforobject", "description": descripcion, "command": {
        "object": xpath, "option": "xpath", "wait_time": "15", "wait_for": "visible", "before": 0, "after": 0}}


INTENTOS_PORTAL = 3  # = NUMERO_REINTENTOS_SISTEMA (maestro); una prueba comprueba que coincidan


def construir(h):
    """`h` trae los constructores comunes del generador (py, paso, sv, si, grupo, para, anexar)."""
    paso, sv, si, grupo, para, anexar = h["paso"], h["sv"], h["si"], h["grupo"], h["para"], h["anexar"]

    def etapa(nombre):
        return f"{{locDicIdentidad}}['etapa'] == '{nombre}'"

    AVANZA = "'{locStrIdRadicado}' in {glbArrSiguenIdentidad}"
    MODO = "{glbDicPortales}['modo']"

    def pasa_a(descripcion, **campos):
        """Cambio de estado del caso en la identidad: una sola asignación visible."""
        partes = ", ".join(f"{k}={valor if isinstance(valor, Exp) else repr(valor)}" for k, valor in campos.items())
        return sv(descripcion, "locDicIdentidad", f"dict({{locDicIdentidad}}, {partes})")

    class Exp(str):
        pass

    # ---------- HU-006: Policía ----------
    hu006 = grupo("HU006 - Consultar la Policía Nacional (Chrome)", [
        sv("Estado de la identidad del radicado (empieza en «inicio»)", "locDicIdentidad",
           "{'etapa': 'inicio', 'via': None, 'puntaje': None, 'motivo': None, 'codigo': None, 'nombre_portal': None, 'abierta_policia': False, 'abierta_procuraduria': False}"),
        si("El radicado avanzó (HU-004) y la identidad está habilitada: prepara los datos del caso",
           "{glbDicPortales}['habilitada'] == True and " + AVANZA, [
               paso("Deja constancia del inicio de la identidad del radicado en el log de auditoría", "locDicEvento",
                    "pasos.evento('Inicio de la identidad del radicado ' + GetVar('locStrIdRadicado'), 'EP-002')"),
               paso("Clasifica el documento: cédula, NIT de 10 dígitos y código del tipo en la Procuraduría", "locDicDocumento",
                    "pasos.clasificar_documento(GetVar('locDicCaso'))"),
               sv("Número de documento a consultar", "locStrDocumento", "{locDicDocumento}['numero']"),
               sv("Nombre del caso en Zeus (la pregunta del captcha puede requerirlo)", "locStrNombre", "{locDicDocumento}['nombre']"),
               sv("Código del tipo de documento en el desplegable de la Procuraduría", "locStrCodigoTipo",
                  "str({locDicDocumento}['codigo_tipo'])")]),
        si("Avanzó a identidad y el documento es cédula de ciudadanía: empieza por la Policía",
           "{glbDicPortales}['habilitada'] == True and " + AVANZA + " and {locDicDocumento}['cedula'] == True",
           [pasa_a("Etapa: consulta en la Policía", etapa="policia")]),
        si("Avanzó a identidad y el documento no es cédula: va directo a la Procuraduría",
           "{glbDicPortales}['habilitada'] == True and " + AVANZA + " and {locDicDocumento}['cedula'] == False",
           [pasa_a("Etapa: consulta en la Procuraduría", etapa="procuraduria")]),
        si("Hay que usar un portal y Chrome aún no está abierto", "(" + etapa("policia") + " or " + etapa("procuraduria")
           + ") and {glbBlnChromeAbierto} == False", [
               {"father": "openbrowser", "option": "chrome", "command": json.dumps({"url": "", "id_driver": "", "profile": ""}),
                "extra": {"default": "chrome"}, "description": "Abre Chrome (el robot corre en Chrome)"},
               sv("Chrome quedó abierto", "glbBlnChromeAbierto", "True")]),
        *[{"father": "trycatch", "description": f"Policía: abre el portal y acepta los términos (intento {n} de {INTENTOS_PORTAL})", "children": [
            si(f"Consulta en la Policía (intento {n})", etapa("policia") + " and {locDicIdentidad}['abierta_policia'] == False", [
                {"father": "openUrl", "command": "{glbStrUrlPolicia}",
                 "description": "Abre el portal de la Policía"},
                web_esperar("Espera la página de términos", "//input[@id='aceptaOption:0']"),
                web_clic("Marca «Acepto» los términos de uso", "//input[@id='aceptaOption:0']"),
                web_clic("Pulsa «Continuar»", "//button[@id='continuarBtn']"),
                web_esperar("Espera el formulario de consulta", "//input[@id='cedulaInput']"),
                web_texto("Lee el texto de la página (aviso de cuota, si lo hay)", "//body", "locStrTexto"),
                paso("Lee el texto de la página de la Policía", "locDicPagina", "pasos.leer_pagina_policia(GetVar('locStrTexto'))"),
                sv("El portal abrió bien: no hace falta reintentar", "locDicIdentidad", "dict({locDicIdentidad}, abierta_policia=True)")])],
            "else": ([paso(f"Espera el backoff antes del intento {n + 1}", "locDicEvento", f"pasos.esperar_reintento_portal({n})")]
                     if n < INTENTOS_PORTAL else [])} for n in range(1, INTENTOS_PORTAL + 1)],
        si(f"La Policía no abrió tras {INTENTOS_PORTAL} intentos: se consulta la Procuraduría",
           etapa("policia") + " and {locDicIdentidad}['abierta_policia'] == False",
           [pasa_a("Policía caída o con estructura inesperada: se consulta la Procuraduría", etapa="procuraduria",
                   motivo="Policía caída o con estructura inesperada")]),
        si("Cuota agotada del reCAPTCHA de la Policía: el bot no lo evade, queda en revisión humana",
           etapa("policia") + " and {locDicPagina}['cuota'] == True",
           [pasa_a("Etapa: revisión humana (cuota agotada)", etapa="revision_humana", via="policia",
                   motivo="cuota agotada del reCAPTCHA de la Policía")]),
        si("Modo real: el reCAPTCHA v2 lo resuelve una persona; el bot se detiene",
           etapa("policia") + " and " + MODO + " == 'real'",
           [pasa_a("Etapa: revisión humana (reCAPTCHA)", etapa="revision_humana", via="policia",
                   motivo="reCAPTCHA v2 de la Policía: lo resuelve una persona (no se automatiza su evasión)")]),
        si("Modo fixture: el clon entrega el captcha ya resuelto (el lab no ejercita la resolución)",
           etapa("policia") + " and " + MODO + " == 'fixture'",
           [web_clic("Marca la casilla del clon «No soy un robot»", "//*[@id='recaptchaCheckbox']")]),
        {"father": "trycatch", "description": "Policía: consulta la cédula", "children": [
            si("Consulta en la Policía", etapa("policia"), [
                web_escribir("Escribe el número de cédula", "//input[@id='cedulaInput']", "{locStrDocumento}"),
                web_clic("Pulsa «Consultar»", "//button[@id='j_idt17']"),
                web_esperar("Espera la respuesta de la Policía",
                            "//*[@id='nombreResultado' or @id='msgResultado' or @id='retoImagenes' or @id='msgCaptcha']"),
                web_texto("Lee el texto del resultado", "//body", "locStrTexto"),
                paso("Lee el texto del resultado de la Policía", "locDicPagina", "pasos.leer_pagina_policia(GetVar('locStrTexto'))")])],
         "else": [pasa_a("Policía caída durante la consulta: se consulta la Procuraduría", etapa="procuraduria",
                         motivo="Policía caída durante la consulta")]},
        si("El reCAPTCHA escaló a un reto de imágenes: lo resuelve una persona",
           etapa("policia") + " and {locDicPagina}['reto'] == True",
           [pasa_a("Etapa: revisión humana (reto de imágenes)", etapa="revision_humana", via="policia",
                   motivo="reto de imágenes del reCAPTCHA: lo resuelve una persona")]),
        si("La Policía devolvió el nombre oficial (apellidos y luego nombres)",
           etapa("policia") + " and {locDicPagina}['nombre'] is not None",
           [pasa_a("Etapa: comparar nombres (HU-008)", etapa="comparar", via="policia",
                   nombre_portal=Exp("{locDicPagina}['nombre']"))]),
        si("La Policía no devolvió resultado: se consulta la Procuraduría", etapa("policia"),
           [pasa_a("Etapa: consulta en la Procuraduría", etapa="procuraduria", via="policia_sin_resultado")]),
    ])

    # ---------- HU-007 y HU-026a: Procuraduría ----------
    hu007 = grupo("HU007 - Consultar la Procuraduría (Chrome)", [
        sv("Página de la Procuraduría (aún sin leer)", "locDicPaginaProc", "{'nombre': None, 'sin_nombre': False}"),
        si("NIT con cantidad de dígitos distinta de 10: gestión manual, no se consulta",
           etapa("procuraduria") + " and {locDicDocumento}['nit'] == True and {locDicDocumento}['nit_valido'] == False",
           [pasa_a("Etapa: gestión manual (NIT inválido)", etapa="gestion_manual",
                   motivo="NIT con cantidad de dígitos distinta de 10: no se consulta")]),
        si("Tipo de documento sin consulta en la Procuraduría: gestión manual",
           etapa("procuraduria") + " and {locDicDocumento}['codigo_tipo'] is None",
           [pasa_a("Etapa: gestión manual (tipo sin consulta)", etapa="gestion_manual",
                   motivo="tipo de documento sin consulta en la Procuraduría")]),
        *[{"father": "trycatch", "description": f"Procuraduría: abre el portal y acepta los términos (intento {n} de {INTENTOS_PORTAL})", "children": [
            si(f"Consulta en la Procuraduría (intento {n})", etapa("procuraduria") + " and {locDicIdentidad}['abierta_procuraduria'] == False", [
                {"father": "openUrl", "command": "{glbStrUrlProcuraduria}", "description": "Abre el portal de la Procuraduría"},
                web_esperar("Espera la página de términos", "//input[@id='rbAcepto']"),
                web_clic("Marca «Acepto» los términos", "//input[@id='rbAcepto']"),
                web_clic("Pulsa «Continuar»", "//input[@id='continuarBtn']"),
                web_esperar("Espera la pregunta del captcha", "//*[@id='lblPregunta']"),
                sv("El portal abrió bien: no hace falta reintentar", "locDicIdentidad", "dict({locDicIdentidad}, abierta_procuraduria=True)")])],
            "else": ([paso(f"Espera el backoff antes del intento {n + 1}", "locDicEvento", f"pasos.esperar_reintento_portal({n})")]
                     if n < INTENTOS_PORTAL else [])} for n in range(1, INTENTOS_PORTAL + 1)],
        si(f"La Procuraduría no abrió tras {INTENTOS_PORTAL} intentos: excepción de sistema",
           etapa("procuraduria") + " and {locDicIdentidad}['abierta_procuraduria'] == False",
           [pasa_a("Procuraduría caída, bloqueada o con estructura inesperada: excepción de sistema",
                   etapa="excepcion_sistema", via="procuraduria", codigo="PORTAL_NO_DISPONIBLE",
                   motivo="Procuraduría caída, bloqueada (WAF) o con estructura inesperada")]),
    ])

    hu026a = grupo("HU026a - Resolver el captcha de pregunta (servicio de captchas)", [
        sv("Intentos permitidos (CAPTCHA_MAX_REINTENTOS)", "locArrIntentos", "list(range(1, {glbDicPortales}['max_captcha'] + 1))"),
        para("Intento de resolver el captcha", "{locArrIntentos}", "locIntIntento", [
            si("Lee la pregunta y la envía al servicio de captchas (el bot no calcula la respuesta)", etapa("procuraduria"), [
                web_texto("Lee la pregunta del captcha", "//*[@id='lblPregunta']", "locStrPregunta"),
                paso("Envía pregunta, documento y nombre al servicio de captchas", "locDicCaptcha",
                     "pasos.resolver_captcha(GetVar('locStrPregunta'), GetVar('locStrDocumento'), GetVar('locStrNombre'))"),
                sv("Respuesta que retornó el servicio", "locStrRespuesta", "str({locDicCaptcha}['respuesta'])")]),
            si("El servicio respondió: diligencia el formulario y consulta",
               etapa("procuraduria") + " and {locDicCaptcha}['ok'] == True", [
                   web_escribir("Escribe el nombre", "//input[@id='txtNombre']", "{locStrNombre}"),
                   web_clic("Elige el tipo de documento en el desplegable",
                            "//select[@id='ddlTipoID']/option[@value='{locStrCodigoTipo}']"),
                   web_escribir("Escribe el número de documento", "//input[@id='txtNumID']", "{locStrDocumento}"),
                   web_escribir("Escribe la respuesta del captcha", "//input[@id='txtRespuestaPregunta']", "{locStrRespuesta}"),
                   web_clic("Pulsa «Consultar»", "//input[@id='btnExportar']"),
                   web_esperar("Espera la respuesta de la Procuraduría", "//*[@id='divDatosCiudadano' or @id='lblMensaje']"),
                   web_texto("Lee el texto del resultado", "//body", "locStrTexto"),
                   paso("Lee el bloque «Datos del ciudadano»", "locDicPaginaProc",
                        "pasos.leer_pagina_procuraduria(GetVar('locStrTexto'))")]),
            si("El servicio no puede resolver esta pregunta: pide otra con el botón de refresco (cuenta como intento)",
               etapa("procuraduria") + " and {locDicCaptcha}['ok'] == False and {locDicCaptcha}['codigo'] != 'CAPTCHA_SERVICIO_NO_DISPONIBLE'",
               [web_clic("Pulsa el botón de refresco de la pregunta", "//input[@id='ImageButton1']")]),
            si("Servicio de captchas no disponible tras los reintentos: excepción de sistema",
               etapa("procuraduria") + " and {locDicCaptcha}['ok'] == False and {locDicCaptcha}['codigo'] == 'CAPTCHA_SERVICIO_NO_DISPONIBLE'",
               [pasa_a("Etapa: excepción de sistema (servicio de captchas)", etapa="excepcion_sistema", via="procuraduria",
                       codigo="CAPTCHA_SERVICIO_NO_DISPONIBLE", motivo="el servicio de captchas no respondió")]),
            si("La Procuraduría devolvió el nombre (bloque «Datos del ciudadano»)",
               etapa("procuraduria") + " and {locDicPaginaProc}['nombre'] is not None",
               [pasa_a("Etapa: comparar nombres (HU-008)", etapa="comparar", via="procuraduria",
                       nombre_portal=Exp("{locDicPaginaProc}['nombre']"))]),
            si("Respuesta sin nombre y el documento es cédula: ni Policía ni Procuraduría dieron resultado, gestión manual",
               etapa("procuraduria") + " and {locDicPaginaProc}['sin_nombre'] == True and {locDicDocumento}['cedula'] == True",
               [pasa_a("Etapa: gestión manual (sin resultado)", etapa="gestion_manual", via="procuraduria",
                       motivo="sin resultado en Policía ni Procuraduría")]),
            si("Respuesta sin nombre para un documento no cédula: se registra y continúa",
               etapa("procuraduria") + " and {locDicPaginaProc}['sin_nombre'] == True and {locDicDocumento}['cedula'] == False",
               [pasa_a("Etapa: sin nombre (continúa)", etapa="sin_nombre", via="procuraduria",
                       motivo="respuesta sin nombre para documento no cédula")]),
        ]),
        si("Captcha no resuelto tras los intentos permitidos: excepción de sistema y gestión manual", etapa("procuraduria"),
           [pasa_a("Etapa: excepción de sistema (CAPTCHA_MAX_REINTENTOS)", etapa="excepcion_sistema", via="procuraduria",
                   codigo="CAPTCHA_MAX_REINTENTOS", motivo="captcha no resuelto tras los intentos permitidos")]),
    ])

    # ---------- HU-008: comparar nombres ----------
    hu008 = grupo("HU008 - Comparar nombres (umbral 0.80, sin depender del orden)", [
        si("Compara el nombre de Zeus con el del portal (normalizado, sin depender del orden)", etapa("comparar"), [
            paso("Calcula el puntaje y lo compara con UMBRAL_COINCIDENCIA_NOMBRES", "locDicVeredicto",
                 "pasos.comparar_nombres(GetVar('locStrNombre'), pasos.objeto(GetVar('locDicIdentidad'))['nombre_portal'])")]),
        si("El puntaje alcanza el umbral: la identidad queda validada",
           etapa("comparar") + " and {locDicVeredicto}['coincide'] == True",
           [pasa_a("Etapa: identidad validada", etapa="validada", puntaje=Exp("{locDicVeredicto}['puntaje']"))]),
        si("El puntaje no alcanza el umbral o el nombre es incompleto: excepción de negocio 3",
           etapa("comparar") + " and {locDicVeredicto}['coincide'] == False",
           [pasa_a("Etapa: excepción de negocio 3", etapa="excepcion_negocio_3", puntaje=Exp("{locDicVeredicto}['puntaje']"),
                   motivo=Exp("{locDicVeredicto}['motivo']"))]),
        si("Escribe el comentario de la excepción de negocio 3 en Gestión → Detalle", etapa("excepcion_negocio_3"), [
            paso("Comentario de la excepción de negocio 3 (revisión de Cartera)", "locDicComentarioIdentidad",
                 "pasos.comentar_excepcion_3(GetVar('locDicCaso'), pasos.objeto(GetVar('locDicIdentidad'))['via'], GetVar('locDicVeredicto'))")]),
        si("El comentario no se pudo registrar: excepción de sistema",
           etapa("excepcion_negocio_3") + " and {locDicComentarioIdentidad}['ok'] == False",
           [pasa_a("Etapa: excepción de sistema (comentario no registrado)", etapa="excepcion_sistema",
                   codigo="COMENTARIO_NO_REGISTRADO", motivo=Exp("{locDicComentarioIdentidad}['mensaje']"))]),
    ])

    # ---------- registro del resultado ----------
    def anota(nombre_etapa, lista, descripcion):
        return si(f"Resultado «{nombre_etapa}»", etapa(nombre_etapa) + " and " + AVANZA,
                  [sv(descripcion, lista, anexar(lista, "'{locStrIdRadicado}'"))])

    registro = grupo("HU006HU007HU008 - Registrar el resultado de identidad", [
        si("Deja el resultado de identidad en el reporte y los logs", AVANZA + " and not " + etapa("inicio"), [
            paso("Registra el resultado de identidad (sin nombres ni identificaciones)", "locDicEvento",
                 "pasos.registrar_identidad(GetVar('locStrIdRadicado'), GetVar('locDicCaso'), GetVar('locDicIdentidad'))")]),
        anota("validada", "glbArrValidadas", "Anota el radicado en identidad validada"),
        anota("excepcion_negocio_3", "glbArrExcepcionesNegocioTres", "Anota el radicado en excepciones de negocio 3"),
        anota("revision_humana", "glbArrRevisionHumana", "Anota el radicado en revisión humana"),
        anota("sin_nombre", "glbArrSinNombre", "Anota el radicado en respuesta sin nombre"),
        anota("gestion_manual", "glbArrGestionManual", "Anota el radicado en gestión manual"),
        si("Resultado «excepcion_sistema»: el caso va a gestión manual", etapa("excepcion_sistema") + " and " + AVANZA, [
            sv("Anota el radicado en excepciones de sistema de identidad", "glbArrExcepcionesSistemaIdentidad",
               anexar("glbArrExcepcionesSistemaIdentidad", "'{locStrIdRadicado}'")),
            sv("Anota el radicado en gestión manual", "glbArrGestionManual", anexar("glbArrGestionManual", "'{locStrIdRadicado}'")),
            sv("Guarda el código de error del radicado", "glbDicCodigos",
               "dict({glbDicCodigos}, **{'{locStrIdRadicado}': {locDicIdentidad}['codigo']})")]),
    ])
    return [hu006, hu007, hu026a, hu008, registro]
