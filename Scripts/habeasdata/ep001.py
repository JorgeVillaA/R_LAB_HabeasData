"""EP-001 — Ingesta y lectura de casos: HU-002 (filtrar), HU-003 (leer datos paramétricos), HU-004 (completitud).

Reglas de negocio cerradas (no se reabren):
- «No aporta» (sin distinguir mayúsculas, C-18) = campo ausente; vacío o en blanco también.
- Teléfono por dígitos: 10 que inician en 3 = celular; 7 = fijo; otro = sin clasificar (se conserva tal cual).
- Varios valores en un campo, separados por «/» sin espacios: cada uno por separado.
- Obligatorios: nombre + tipo + número de identificación, y al menos un canal de contacto.
- Se procesa el radicado hijo; el padre se usa en plantillas y reporte.
Los umbrales, textos y separadores salen de la configuración, no de la lógica.
"""
import json
import sys

from .config import cargar
from .redaccion import resumen_seguro
from .registro import Registro
from .zeus import (APLICATIVO, ClienteZeus, EscrituraComentario, ErrorBloqueo, ErrorNoAutenticado, ErrorNoDisponible,
                   ErrorNoEncontrado, ErrorPermiso, ErrorSolicitud, ErrorZeus)

MODULO = "EP-001"
OBLIGATORIOS = (("nombre", "NOMBRE DEL CLIENTE"), ("tipo_identificacion", "TIPO DE IDENTIFICACION"),
                ("numero_identificacion", "NUMERO DE IDENTIFICACION"))


class DetenerEjecucion(Exception):
    """Punto de control crítico: se detiene la corrida y se alerta (correo «Detenido»)."""


class ExcepcionSistemaCaso(Exception):
    """Fallo de sistema acotado a un radicado: se registra y se continúa con el siguiente."""


# ---------- reglas puras ----------
def es_ausente(valor, cfg):
    if valor is None:
        return True
    texto = str(valor).strip()
    return texto == "" or texto.casefold() == cfg.proceso["Negocio"]["TextoAusente"].casefold()


def separar_valores(valor, cfg):
    if es_ausente(valor, cfg):
        return []
    separador = cfg.proceso["Negocio"]["SeparadorValores"]
    return [parte.strip() for parte in str(valor).split(separador) if parte.strip()]


def clasificar_telefono(valor, cfg):
    negocio = cfg.proceso["Negocio"]
    if valor.isdigit() and len(valor) == negocio["DigitosCelular"] and valor.startswith(negocio["PrefijoCelular"]):
        return "celular"
    if valor.isdigit() and len(valor) == negocio["DigitosFijo"]:
        return "fijo"
    return "sin_clasificar"


def normalizar_caso(registro_zeus, cfg):
    """HU-003: datos del solicitante tal cual vienen (sin normalizar nombre), valores separados y clasificados."""
    def limpio(campo):
        valor = registro_zeus.get(campo)
        return None if es_ausente(valor, cfg) else str(valor).strip()

    hijo = str(registro_zeus["IDRADICADO"])
    padre = limpio("RadicadoPadre")
    correos = separar_valores(registro_zeus.get("CORREOELECTRONICOPARAEXCLUSION"), cfg)
    telefonos = [{"valor": v, "clase": clasificar_telefono(v, cfg)}
                 for v in separar_valores(registro_zeus.get("TELEFONODECONTACTO"), cfg)]
    return {
        "radicado_hijo": hijo,
        "radicado_padre": padre,
        "radicado_para_plantillas": padre or hijo,
        "nombre": limpio("NOMBREDELCLIENTE"),
        "tipo_identificacion": limpio("TIPODEIDENTIFICACION"),
        "numero_identificacion": limpio("NOIDENTIFICACIONDELCLIENTE"),
        "fecha_recepcion": limpio("FECHADERECEPCION"),
        "correos": correos,
        "telefonos": telefonos,
        "canal_correo": bool(correos),
        "canal_telefono": bool(telefonos),
    }


def validar_completitud(caso):
    """HU-004: solo existencia, no formato ni contenido."""
    motivos = [etiqueta for clave, etiqueta in OBLIGATORIOS if not caso.get(clave)]
    if not caso["canal_correo"] and not caso["canal_telefono"]:
        motivos.append("SIN CANAL DE CONTACTO")
    return {"completo": not motivos, "motivos": motivos}


# ---------- HU-002 ----------
def filtrar_exclusion(cliente, cfg, registro):
    """HU-002. Selección según el contrato QA: tipología de exclusión, descartando identificación ausente ('NO APORTA'),
    por lotes ($first) y en orden ($orderby). Los descartados se cuentan y se reportan: no se pierden en silencio."""
    negocio, seleccion = cfg.proceso["Negocio"], cfg.proceso["SeleccionRadicados"]
    base = f"{negocio['CampoTipologia']} eq '{negocio['TipologiaExclusion']}'"
    campo_id, literal = seleccion["CampoIdentificacion"], seleccion["LiteralIdentificacionAusente"]
    descartar = seleccion["DescartarIdentificacionAusente"]
    filtro = f"{base} and {campo_id} ne '{literal}'" if descartar else base
    try:
        filas = cliente.consultar(filtro=filtro, select=("IDRADICADO", negocio["CampoTipologia"]),
                                  first=seleccion["LoteMaximo"], orderby=seleccion["Orden"])
        descartados = []
        if descartar:
            descartados = [str(f["IDRADICADO"]) for f in cliente.consultar(
                filtro=f"{base} and {campo_id} eq '{literal}'", select=("IDRADICADO",))]
        if filas:
            return {"ids": [str(f["IDRADICADO"]) for f in filas], "descartados": descartados,
                    "motivo_sin_casos": None, "reintento": None}
        total = len(cliente.consultar(select=("IDRADICADO",)))
    except ErrorSolicitud as error:
        raise DetenerEjecucion(f"filtro o campo no reconocido por la API: {error}") from error
    except ErrorBloqueo as error:
        raise DetenerEjecucion(str(error)) from error
    except ErrorNoAutenticado as error:
        raise DetenerEjecucion(f"sin token válido para la API de Zeus: {error}") from error
    except (ErrorPermiso, ErrorNoDisponible, ErrorNoEncontrado) as error:
        raise DetenerEjecucion(f"bandeja inaccesible: {error}") from error
    motivo = "solo_descartados" if descartados else ("tipologia_ausente" if total else "bandeja_vacia")
    cadencia = cfg.proceso["CADENCIA_REINTENTO_BANDEJA_VACIA"]
    registro.auditoria(f"0 casos ({motivo}); radicados en la consulta general: {total}; "
                       f"reintento en {cadencia['MinutosEntreReintentos']} min", MODULO)
    registro.reporte(None, None, "0 casos", None, motivo)
    return {"ids": [], "descartados": descartados, "motivo_sin_casos": motivo, "reintento": dict(cadencia)}


# ---------- HU-003 ----------
def extraer(cliente, cfg, id_radicado):
    try:
        crudo = cliente.radicado(id_radicado)
    except (ErrorSolicitud, ErrorNoEncontrado, ErrorNoDisponible, ErrorPermiso, ErrorZeus) as error:
        raise ExcepcionSistemaCaso(f"no se pudo leer el radicado {id_radicado}: {error}") from error
    if crudo is None:
        raise ExcepcionSistemaCaso(f"no se pudo leer el radicado {id_radicado}: respuesta vacía")
    return normalizar_caso(crudo, cfg)


# ---------- HU-004 ----------
def registrar_excepcion_negocio_1(escritura, caso, motivos):
    detalle = "Excepción de negocio 1 (datos incompletos), revisión manual de Cartera. Motivo: " + ", ".join(motivos)
    try:
        escritura.comentar(caso["radicado_hijo"], detalle)
    except ErrorZeus as error:
        raise ExcepcionSistemaCaso(f"no se pudo registrar el comentario del radicado {caso['radicado_hijo']}: {error}") from error


# ---------- orquestación ----------
def procesar(cfg=None, cliente=None, registro=None, escritura=None):
    cfg = cfg or cargar()
    registro = registro or Registro(cfg)
    cliente = cliente or ClienteZeus(cfg, registro)
    escritura = escritura or EscrituraComentario(cliente)
    registro.asegurar_archivos()
    registro.auditoria("Inicio de ejecución EP-001", MODULO)
    resumen = {"estado": "ok", "modo": cliente.modo, "avanzan": [], "excepciones_negocio_1": [],
               "excepciones_sistema": [], "descartados_identificacion_ausente": [], "casos": {},
               "motivo_sin_casos": None, "reintento": None, "notificacion": None}
    registro.auditoria("Ingreso a la API de Zeus", APLICATIVO)
    try:
        lista = filtrar_exclusion(cliente, cfg, registro)
    except DetenerEjecucion as error:
        registro.error(f"Ejecución detenida: {error}", MODULO)
        notif = cfg.maquina["Notificaciones"]
        resumen.update(estado="detenido", notificacion={
            "asunto": notif["AsuntoDetenido"], "destinatario": notif["CorreoDetenido"], "motivo": str(error)})
        registro.auditoria("Fin de ejecución EP-001 (detenida)", MODULO)
        return resumen
    resumen["motivo_sin_casos"], resumen["reintento"] = lista["motivo_sin_casos"], lista["reintento"]
    resumen["descartados_identificacion_ausente"] = lista["descartados"]
    for id_descartado in lista["descartados"]:
        registro.auditoria(f"Radicado {id_descartado} descartado por identificación ausente (sin gestión del bot)", MODULO)
        registro.reporte(id_descartado, None, "descartado: identificación ausente", None, "sin gestión del bot")
    registro.auditoria(f"{len(lista['ids'])} radicados de exclusión identificados", MODULO)
    for id_radicado in lista["ids"]:
        registro.auditoria(f"Inicio del radicado {id_radicado}", MODULO)
        try:
            caso = extraer(cliente, cfg, id_radicado)
            veredicto = validar_completitud(caso)
            resumen["casos"][id_radicado] = caso
            if veredicto["completo"]:
                resumen["avanzan"].append(id_radicado)
                registro.reporte(id_radicado, caso["radicado_padre"], "avanza a validación de deuda", None, None)
            else:
                registrar_excepcion_negocio_1(escritura, caso, veredicto["motivos"])
                resumen["excepciones_negocio_1"].append(id_radicado)
                registro.reporte(id_radicado, caso["radicado_padre"], "excepción de negocio 1", "1",
                                 ", ".join(veredicto["motivos"]))
        except ExcepcionSistemaCaso as error:
            resumen["excepciones_sistema"].append(id_radicado)
            registro.error(str(error), MODULO)
            registro.reporte(id_radicado, None, "excepción de sistema", None, str(error))
        registro.auditoria(f"Fin del radicado {id_radicado}", MODULO)
    registro.auditoria("Fin de ejecución EP-001", MODULO)
    return resumen


def principal():
    cfg = cargar()
    resumen = procesar(cfg)
    print(json.dumps(resumen_seguro(resumen, cfg), ensure_ascii=False, indent=2, default=str))
    return 0 if resumen["estado"] == "ok" else 2


if __name__ == "__main__":
    sys.exit(principal())
