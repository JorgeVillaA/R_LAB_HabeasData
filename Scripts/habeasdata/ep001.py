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
                   ErrorNoEncontrado, ErrorPermiso, ErrorRespuesta, ErrorSolicitud, ErrorZeus)

MODULO = "EP-001"
CAMPOS_ESCALARES = ("IDRADICADO", "RadicadoPadre", "NOMBREDELCLIENTE", "TIPODEIDENTIFICACION", "NOIDENTIFICACIONDELCLIENTE",
                    "FECHADERECEPCION", "CORREOELECTRONICOPARAEXCLUSION", "TELEFONODECONTACTO")
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
    partes = [parte.strip() for parte in str(valor).split(separador)]
    return [parte for parte in partes if not es_ausente(parte, cfg)]


def clasificar_telefono(valor, cfg):
    valor = str(valor)
    negocio = cfg.proceso["Negocio"]
    if valor.isdigit() and len(valor) == negocio["DigitosCelular"] and valor.startswith(negocio["PrefijoCelular"]):
        return "celular"
    if valor.isdigit() and len(valor) == negocio["DigitosFijo"]:
        return "fijo"
    return "sin_clasificar"


def preparar_campos(registro_zeus, cfg):
    """HU-003 (parseo): ausentes a None, valores de cada canal separados por «/». El nombre se conserva tal cual."""
    def limpio(campo):
        valor = registro_zeus.get(campo)
        return None if es_ausente(valor, cfg) else str(valor).strip()

    hijo = str(registro_zeus["IDRADICADO"])
    padre = limpio("RadicadoPadre")
    return {
        "radicado_hijo": hijo,
        "radicado_padre": padre,
        "radicado_para_plantillas": padre or hijo,
        "nombre": limpio("NOMBREDELCLIENTE"),
        "tipo_identificacion": limpio("TIPODEIDENTIFICACION"),
        "numero_identificacion": limpio("NOIDENTIFICACIONDELCLIENTE"),
        "fecha_recepcion": limpio("FECHADERECEPCION"),
        "correos": separar_valores(registro_zeus.get("CORREOELECTRONICOPARAEXCLUSION"), cfg),
        "telefonos_valores": separar_valores(registro_zeus.get("TELEFONODECONTACTO"), cfg),
    }


def clasificar_telefonos(preparado, cfg):
    """HU-003 (clasificación): cada teléfono por dígitos; deja los indicadores de canal presente."""
    caso = {clave: valor for clave, valor in preparado.items() if clave != "telefonos_valores"}
    caso["telefonos"] = [{"valor": v, "clase": clasificar_telefono(v, cfg)} for v in preparado["telefonos_valores"]]
    caso["canal_correo"] = bool(caso["correos"])
    caso["canal_telefono"] = bool(caso["telefonos"])
    return caso


def normalizar_caso(registro_zeus, cfg):
    """HU-003: datos del solicitante tal cual vienen (sin normalizar nombre), valores separados y clasificados."""
    return clasificar_telefonos(preparar_campos(registro_zeus, cfg), cfg)


def validar_completitud(caso):
    """HU-004: solo existencia, no formato ni contenido."""
    motivos = [etiqueta for clave, etiqueta in OBLIGATORIOS if not caso.get(clave)]
    if not caso.get("canal_correo") and not caso.get("canal_telefono"):
        motivos.append("SIN CANAL DE CONTACTO")
    return {"completo": not motivos, "motivos": motivos}


# ---------- HU-002 ----------
def mensaje_detencion(error):
    """Motivo con el que una falla de la consulta detiene la corrida (punto de control crítico)."""
    if isinstance(error, ErrorSolicitud):
        return f"filtro o campo no reconocido por la API: {error}"
    if isinstance(error, ErrorBloqueo):
        return str(error)
    if isinstance(error, ErrorNoAutenticado):
        return f"sin token válido para la API de Zeus: {error}"
    return f"bandeja inaccesible: {error}"


def registrar_sin_casos(registro, cfg, motivo, total):
    """0 casos: auditoría, reporte y cadencia de reintento (parámetro, no lógica)."""
    cadencia = cfg.proceso["CADENCIA_REINTENTO_BANDEJA_VACIA"]
    registro.auditoria(f"0 casos ({motivo}); radicados en la consulta general: {total}; "
                       f"reintento en {cadencia['MinutosEntreReintentos']} min", MODULO)
    registro.reporte(None, None, "0 casos", None, motivo)
    return dict(cadencia)


def registrar_descartados(registro, ids):
    for id_descartado in ids:
        registro.auditoria(f"Radicado {id_descartado} descartado por identificación ausente (sin gestión del bot)", MODULO)
        registro.reporte(id_descartado, None, "descartado: identificación ausente", None, "sin gestión del bot")


def ids_de(filas, cfg):
    """Frontera: cada fila debe traer un IDRADICADO presente; si no, la respuesta no cumple el contrato."""
    ids = []
    for fila in filas:
        valor = fila.get("IDRADICADO")
        if es_ausente(valor, cfg) or isinstance(valor, (bool, float, dict, list)):
            raise ErrorRespuesta("una fila de la respuesta de Zeus no trae un IDRADICADO válido")
        ids.append(str(valor).strip())
    return ids


def filtrar_exclusion(cliente, cfg, registro):
    """HU-002. Selección según el contrato QA: tipología de exclusión, descartando identificación ausente ('NO APORTA'),
    por lotes ($first) y en orden ($orderby). Los descartados se cuentan y se reportan: no se pierden en silencio."""
    negocio, seleccion = cfg.proceso["Negocio"], cfg.proceso["SeleccionRadicados"]
    base = f"{negocio['CampoTipologia']} eq '{negocio['TipologiaExclusion']}'"
    campo_id, literal = seleccion["CampoIdentificacion"], seleccion["LiteralIdentificacionAusente"]
    descartar = seleccion["DescartarIdentificacionAusente"]
    filtro = f"{base} and {campo_id} ne '{literal}'" if descartar else base
    try:
        filas = ids_de(cliente.consultar(filtro=filtro, select=("IDRADICADO", negocio["CampoTipologia"]),
                                         first=seleccion["LoteMaximo"], orderby=seleccion["Orden"]), cfg)
        descartados = []
        if descartar:
            descartados = ids_de(cliente.consultar(
                filtro=f"{base} and {campo_id} eq '{literal}'", select=("IDRADICADO",)), cfg)
        if filas:
            return {"ids": filas, "descartados": descartados,
                    "motivo_sin_casos": None, "reintento": None}
        total = len(cliente.consultar(select=("IDRADICADO",)))
    except ErrorZeus as error:
        raise DetenerEjecucion(mensaje_detencion(error)) from error
    motivo = "solo_descartados" if descartados else ("tipologia_ausente" if total else "bandeja_vacia")
    reintento = registrar_sin_casos(registro, cfg, motivo, total)
    return {"ids": [], "descartados": descartados, "motivo_sin_casos": motivo, "reintento": reintento}


# ---------- HU-003 ----------
def validar_registro(crudo, cfg):
    """Frontera: el registro debe ser un objeto con IDRADICADO presente y campos escalares (texto o entero)."""
    if not isinstance(crudo, dict):
        return "la respuesta no es un registro"
    identificador = crudo.get("IDRADICADO")
    if isinstance(identificador, (bool, float, dict, list)) or es_ausente(identificador, cfg):
        return "el registro no trae IDRADICADO"
    for campo in CAMPOS_ESCALARES:
        valor = crudo.get(campo)
        if valor is not None and (isinstance(valor, (bool, float, dict, list, tuple, set)) or not isinstance(valor, (str, int))):
            return f"el campo {campo} trae un tipo inesperado ({type(valor).__name__})"
    return None


def leer_crudo(cliente, id_radicado, cfg):
    try:
        crudo = cliente.radicado(id_radicado)
    except (ErrorSolicitud, ErrorNoEncontrado, ErrorNoDisponible, ErrorPermiso, ErrorZeus) as error:
        raise ExcepcionSistemaCaso(f"no se pudo leer el radicado {id_radicado}: {error}") from error
    if crudo is None:
        raise ExcepcionSistemaCaso(f"no se pudo leer el radicado {id_radicado}: respuesta vacía")
    problema = validar_registro(crudo, cfg)
    if problema:
        raise ExcepcionSistemaCaso(f"no se pudo leer el radicado {id_radicado}: {problema}")
    return crudo


def extraer(cliente, cfg, id_radicado):
    return normalizar_caso(leer_crudo(cliente, id_radicado, cfg), cfg)


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
    registrar_descartados(registro, lista["descartados"])
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
