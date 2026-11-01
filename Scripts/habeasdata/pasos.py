"""Pasos del robot LabHabeasData de Studio: cada función es UN bloque visible del flujo.

El flujo (grupos por historia, decisiones, bucle por radicado) vive en Studio, a la vista del cliente. Este módulo solo
ofrece, como un módulo de Rocketbot, lo que no debe ir en variables ni en el log de Studio o es lógica pura:
- E/S con la API (token con client_secret del Administrador de credenciales, consultas OData con Bearer): el comando
  nativo `request` escribe cabeceras y cuerpo en el log de Studio, así que no puede llevar secretos (R-04, R-11).
- Parseo y clasificación (lógica pura) y escritura de logs/reporte (anexo V1.0).
Todas devuelven un diccionario `{"ok": bool, "mensaje": str, ...}`; el robot decide con `evaluateIf`.
"""
import ast
import time

from . import ep001
from .config import cargar
from .redaccion import resumen_seguro
from .registro import Registro
from .zeus import ClienteZeus, EscrituraComentario, ErrorZeus

MODULO = ep001.MODULO


class _Sesion:
    def __init__(self, cfg):
        self.cfg = cfg
        self.registro = Registro(cfg)
        self.cliente = ClienteZeus(cfg, self.registro)
        self.escritura = EscrituraComentario(self.cliente)


class _SesionPerezosa:
    """Sesión del robot con entrada explícita: la raíz. `asegurar(raiz)` la reconstruye si no existe (prueba por bloque en
    Studio, D-21): ningún paso depende de que otro haya corrido antes en el mismo proceso."""

    def __init__(self):
        self._real = None
        self.raiz = None

    def abrir(self, raiz):
        self._real, self.raiz = _Sesion(cargar(raiz)), str(raiz)
        return self._real

    def asegurar(self, raiz):
        if self._real is None or self.raiz != str(raiz):
            self.abrir(raiz)

    def __getattr__(self, nombre):
        real = self.__dict__.get("_real")
        if real is None:
            raise RuntimeError("sesión no abierta: el bloque debe llamar a pasos.asegurar(raíz) con glbStrRutaRaiz")
        return getattr(real, nombre)


_sesion = _SesionPerezosa()


def asegurar(raiz):
    """Entrada explícita de cada bloque: abre la sesión desde la raíz si no está abierta (idempotente)."""
    _sesion.asegurar(raiz)
    return _ok()

dormir = time.sleep  # espera del reintento de la bandeja; los tests y el banco la sustituyen


def objeto(valor):
    """Un valor que llega de una variable del robot: objeto Python o su texto (repr), según el intérprete."""
    if isinstance(valor, str):
        try:
            return ast.literal_eval(valor)
        except (ValueError, SyntaxError):
            return valor
    return valor


def _ok(**datos):
    return {"ok": True, "mensaje": "", **datos}


def _fallo(mensaje, **datos):
    return {"ok": False, "mensaje": str(mensaje), **datos}


# ---------- inicialización y cierre ----------
def iniciar(raiz):
    """Carga los tres JSON, crea la estructura de carpetas y los dos logs del día, y abre la sesión."""
    _sesion.abrir(raiz)
    _sesion.registro.asegurar_archivos()
    _sesion.registro.auditoria("Inicio de ejecución EP-001", MODULO)
    return _ok(modo=_sesion.cliente.modo, lote=_sesion.cfg.proceso["SeleccionRadicados"])


def parametros():
    """Parámetros de negocio que el robot muestra en pantalla (todo sale de la configuración)."""
    cfg = _sesion.cfg
    return _ok(negocio=cfg.proceso["Negocio"], seleccion=cfg.proceso["SeleccionRadicados"],
               cadencia=cfg.proceso["CADENCIA_REINTENTO_BANDEJA_VACIA"])


def evento(texto, modulo=None):
    _sesion.registro.auditoria(texto, modulo or MODULO)
    return _ok()


def cerrar(resumen):
    """Fin de ejecución: deja el resumen sin PII en modo real."""
    resumen = objeto(resumen)
    _sesion.registro.auditoria("Fin de ejecución EP-001" + (" (detenida)" if resumen.get("estado") == "detenido" else ""), MODULO)
    return _ok(resumen=resumen_seguro(dict(resumen, casos={}), _sesion.cfg))


# ---------- HU-002 ----------
def solicitar_token():
    """OAuth client_credentials: el secreto sale del Administrador de credenciales; nunca pasa por el robot."""
    _sesion.registro.auditoria("Ingreso a la API de Zeus", "Zeus API")
    try:
        _sesion.cliente.renovar_token()
    except ErrorZeus as error:
        return _fallo(ep001.mensaje_detencion(error), detenido=True)
    return _ok()


def consultar_odata(filtro="", select="", first=None, orderby=""):
    """GET OData con Bearer. Devuelve las filas ya proyectadas."""
    lote = int(first) if str(first or "").strip().isdigit() else None
    try:
        filas = _sesion.cliente.consultar(filtro=filtro or None, select=tuple(select.split(",")) if select else None,
                                          first=lote, orderby=orderby or None)
        ids = ep001.ids_de(filas, _sesion.cfg)
    except ErrorZeus as error:
        return _fallo(ep001.mensaje_detencion(error), detenido=True)
    return _ok(filas=filas, ids=ids)


def consultar_seleccion(consulta):
    """Consulta de HU-002 con el diccionario que armó el robot (seleccion, select, lote, orden)."""
    c = objeto(consulta)
    return consultar_odata(c["seleccion"], c["select"], c["lote"], c["orden"])


def registrar_descartados(ids):
    ep001.registrar_descartados(_sesion.registro, [str(i) for i in objeto(ids)])
    return _ok()


def reintentar_bandeja():
    """HU-002: agenda el reintento de la bandeja sin casos (espera + reconsulta, según CADENCIA_REINTENTO_BANDEJA_VACIA).
    Es solo la espera y la reconsulta con los mismos pasos de la selección; la decisión de reintentar la toma el robot."""
    try:
        lista, hechos = ep001.reintentar_bandeja(_sesion.cliente, _sesion.cfg, _sesion.registro, lambda s: dormir(s))
    except ep001.DetenerEjecucion as error:
        return _fallo(error)
    if lista is None:
        return _ok(cambia=False, reintentos=0)
    return _ok(cambia=True, reintentos=hechos, ids=lista["ids"], descartados=lista["descartados"],
               motivo=lista["motivo_sin_casos"], reintento=lista["reintento"])


def registrar_sin_casos(motivo, total):
    return _ok(reintento=ep001.registrar_sin_casos(_sesion.registro, _sesion.cfg, motivo, int(total)))


def registrar_detencion(motivo):
    """Punto de control crítico: log de errores y aviso «Detenido» (el envío del correo es HU-018, fuera del lab)."""
    _sesion.registro.error(f"Ejecución detenida: {motivo}", MODULO)
    notif = _sesion.cfg.maquina["Notificaciones"]
    return _ok(notificacion={"asunto": notif["AsuntoDetenido"], "destinatario": notif["CorreoDetenido"], "motivo": motivo})


# ---------- HU-003 ----------
def leer_radicado(id_radicado):
    """GET del radicado por IDRADICADO (consulta individual)."""
    try:
        return _ok(crudo=ep001.leer_crudo(_sesion.cliente, id_radicado, _sesion.cfg))
    except ep001.ExcepcionSistemaCaso as error:
        return _fallo(error)


def preparar_campos(lectura):
    """Lógica pura: «No aporta»/vacío = ausente; correos y teléfonos separados por «/»."""
    return ep001.preparar_campos(objeto(lectura)["crudo"], _sesion.cfg)


def clasificar_telefonos(preparado):
    """Lógica pura: celular (10 dígitos que inician en 3), fijo (7), sin clasificar."""
    return ep001.clasificar_telefonos(objeto(preparado), _sesion.cfg)


# ---------- HU-004 ----------
def comentar_excepcion_1(caso, motivos):
    """Comentario en Gestión → Detalle (doble en fixture; sin endpoint entregado en modo real, C-09)."""
    try:
        ep001.registrar_excepcion_negocio_1(_sesion.escritura, objeto(caso), objeto(motivos))
    except ep001.ExcepcionSistemaCaso as error:
        return _fallo(error)
    return _ok()


def registrar_avance(caso):
    caso = objeto(caso)
    _sesion.registro.reporte(caso["radicado_hijo"], caso["radicado_padre"], "avanza a validación de deuda", None, None)
    return _ok()


def registrar_excepcion_negocio_1(caso, motivos):
    caso, motivos = objeto(caso), objeto(motivos)
    _sesion.registro.reporte(caso["radicado_hijo"], caso["radicado_padre"], "excepción de negocio 1", "1", ", ".join(motivos))
    return _ok()


def registrar_excepcion_sistema(id_radicado, mensaje):
    _sesion.registro.error(mensaje, MODULO)
    _sesion.registro.reporte(id_radicado, None, "excepción de sistema", None, mensaje)
    return _ok()


# ---------- EP-002: identidad (HU-006, HU-007, HU-026a, HU-008) ----------
# La navegación por los portales vive en bloques de Chrome de Studio; aquí solo van la configuración, la lectura del TEXTO
# de la página (lógica pura), el servicio de captchas, la comparación de nombres y los registros.
def portales():
    """Modo, URLs y reintentos de los portales (todo sale de la configuración). En modo real exige autorización y ventana."""
    from .portales import ClientePortales, ErrorBloqueoPortal
    cfg = _sesion.cfg
    identidad = cfg.proceso.get("Identidad", {"Habilitada": True})
    if not identidad["Habilitada"]:
        return _ok(habilitada=False, modo="fixture", url_policia="", url_procuraduria="", max_captcha=0, umbral=0)
    try:
        cliente = ClientePortales(cfg)
    except ErrorBloqueoPortal as error:
        return _fallo(error, detenido=True, habilitada=True)
    a = cliente.ajustes
    return _ok(habilitada=True, modo=cliente.modo, url_policia=a["UrlPolicia"], url_procuraduria=a["UrlProcuraduria"],
               max_captcha=int(cfg.maestro["CAPTCHA_MAX_REINTENTOS"]), umbral=cfg.maestro["UMBRAL_COINCIDENCIA_NOMBRES"])


def clasificar_documento(caso):
    """Lógica pura: ¿cédula?, ¿NIT de exactamente 10 dígitos? y código del desplegable de la Procuraduría."""
    from . import ep002
    from .portales import TIPOS_PROCURADURIA
    caso = objeto(caso)
    numero = str(caso.get("numero_identificacion") or "")
    tipo = ep002.tipo_normalizado(caso)
    return _ok(cedula=tipo == "CEDULA DE CIUDADANIA", nit=tipo == "NIT", nit_valido=ep002.nit_valido(numero),
               codigo_tipo=TIPOS_PROCURADURIA.get(tipo), numero=numero, nombre=str(caso.get("nombre") or ""))


def leer_pagina_policia(texto):
    """Lógica pura sobre el texto visible de la página de la Policía."""
    import re
    texto = str(texto or "")
    minus = texto.lower()
    nombre = re.search(r"Apellidos y Nombres:\s*(.+)", texto)
    return _ok(cuota="supera la cuota gratuita" in minus, reto="seleccione todas las im" in minus,
               sin_resultado="no se encontraron registros" in minus, nombre=nombre.group(1).strip() if nombre else None)


def leer_pagina_procuraduria(texto):
    """Lógica pura sobre el texto visible de la página de la Procuraduría (bloque «Datos del ciudadano»)."""
    import re
    texto = str(texto or "")
    minus = texto.lower()
    # el formulario del portal fiel también tiene una etiqueta «Nombre:»: solo cuenta lo que sigue al encabezado del bloque
    bloque = texto[minus.rindex("datos del ciudadano"):] if "datos del ciudadano" in minus else ""
    nombre = re.search(r"Nombre:[ \t]*(\S.*)", bloque)
    estado = re.search(r"Estado:[ \t]*(\S.*)", bloque) if nombre else None
    return _ok(nombre=nombre.group(1).strip() if nombre else None, estado=estado.group(1).strip() if estado else None,
               incorrecta="respuesta a la pregunta es incorrecta" in minus,
               sin_nombre="no se encontr" in minus and "informaci" in minus)


def resolver_captcha(pregunta, documento, nombre):
    """HU-026a: la pregunta va al servicio de captchas; el bot no calcula la respuesta. Códigos de error del servicio."""
    from .captcha import ErrorCaptcha, ServicioCaptchas
    cfg = _sesion.cfg
    servicio = ServicioCaptchas(_ajustes_portales(cfg)["UrlCaptchas"], cfg.maestro["NUMERO_REINTENTOS_SISTEMA"],
                                cfg.proceso["Portales"]["BackoffSegundos"], cfg.proceso["Portales"]["TimeoutSegundos"])
    try:
        return _ok(respuesta=servicio.resolver(str(pregunta), str(documento), str(nombre)), codigo=None)
    except ErrorCaptcha as error:
        return _fallo(error, respuesta=None, codigo=error.codigo)


def _ajustes_portales(cfg):
    """Ajustes de URL del modo vigente, sin las comprobaciones de autorización (esas las hace `portales()`)."""
    ajustes = cfg.proceso["Portales"]
    return ajustes["Real" if ajustes["Modo"] == "real" else "Fixture"]


def comparar_nombres(nombre_zeus, nombre_portal):
    """HU-008 (lógica pura): puntaje de coincidencia contra el umbral parametrizado."""
    from . import nombres
    return _ok(**nombres.comparar(str(nombre_zeus), str(nombre_portal), _sesion.cfg.maestro["UMBRAL_COINCIDENCIA_NOMBRES"]))


def comentar_excepcion_3(caso, via, veredicto):
    from . import ep002
    from .zeus import ErrorZeus
    caso = objeto(caso)
    try:
        _sesion.escritura.comentar(caso["radicado_hijo"], ep002.comentario_excepcion_3(objeto(veredicto), via))
    except ErrorZeus as error:
        return _fallo(error)
    return _ok()


def registrar_identidad(id_radicado, caso, identidad):
    """Deja el resultado de identidad en el reporte y los logs (sin nombres ni identificaciones)."""
    from . import ep002
    caso, i = objeto(caso), objeto(identidad)
    ep002.registrar(_sesion.registro, id_radicado, caso["radicado_padre"], i["etapa"], i["via"], i["puntaje"], i["motivo"], i["codigo"])
    return _ok()
