"""Pasos del robot LabHabeasData de Studio: cada función es UN bloque visible del flujo.

El flujo (grupos por historia, decisiones, bucle por radicado) vive en Studio, a la vista del cliente. Este módulo solo
ofrece, como un módulo de Rocketbot, lo que no debe ir en variables ni en el log de Studio o es lógica pura:
- E/S con la API (token con client_secret del Administrador de credenciales, consultas OData con Bearer): el comando
  nativo `request` escribe cabeceras y cuerpo en el log de Studio, así que no puede llevar secretos (R-04, R-11).
- Parseo y clasificación (lógica pura) y escritura de logs/reporte (anexo V1.0).
Todas devuelven un diccionario `{"ok": bool, "mensaje": str, ...}`; el robot decide con `evaluateIf`.
"""
import ast

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


_sesion = None


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
    global _sesion
    _sesion = _Sesion(cargar(raiz))
    _sesion.registro.asegurar_archivos()
    _sesion.registro.auditoria("Inicio de ejecución EP-001", MODULO)
    return _ok(modo=_sesion.cliente.modo, lote=_sesion.cfg.proceso["SeleccionRadicados"])


def parametros():
    """Parámetros de negocio que el robot muestra en pantalla (todo sale de la configuración)."""
    cfg = _sesion.cfg
    return _ok(negocio=cfg.proceso["Negocio"], seleccion=cfg.proceso["SeleccionRadicados"],
               cadencia=cfg.proceso["CADENCIA_REINTENTO_BANDEJA_VACIA"])


def evento(texto):
    _sesion.registro.auditoria(texto, MODULO)
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
    except ErrorZeus as error:
        return _fallo(ep001.mensaje_detencion(error), detenido=True)
    return _ok(filas=filas, ids=[str(f["IDRADICADO"]) for f in filas])


def registrar_descartados(ids):
    ep001.registrar_descartados(_sesion.registro, [str(i) for i in objeto(ids)])
    return _ok()


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
        return _ok(crudo=ep001.leer_crudo(_sesion.cliente, id_radicado))
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
