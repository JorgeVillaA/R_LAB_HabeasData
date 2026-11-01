"""Genera Robots/LabHabeasData.robot.json: el flujo EP-001 legible a cliente (HU-002, HU-003, HU-004).

Estructura (como MainMonitoreoMarcas): trycatch «Control de ejecución» → grupo de inicialización → trycatch
«Proceso principal» → grupos por historia → grupo de cierre. Cada bloque lleva su descripción (§6.1).
El Python (`habeasdata.pasos`) solo hace E/S con secretos, parseo y clasificación puros y escritura de logs;
las decisiones, el bucle por radicado y los contadores viven en bloques visibles de Studio.

Uso:  python Robots/generar_labhabeasdata.py   (escribe el JSON junto a este archivo)
"""
import json
from pathlib import Path

DESTINO = Path(__file__).resolve().parent / "LabHabeasData.robot.json"
P = '{glbDicParametros}'
NEG = P + '["negocio"]'
SEL = P + '["seleccion"]'

def expr(plantilla):
    """Expresión de Studio a partir de una plantilla con NEG y SEL (los diccionarios de parámetros)."""
    return plantilla.replace("NEG", NEG).replace("SEL", SEL)


FILTRO_BASE = expr("""{'base': NEG["CampoTipologia"] + " eq '" + NEG["TipologiaExclusion"] + "'", 'seleccion': NEG["CampoTipologia"] + " eq '" + NEG["TipologiaExclusion"] + "'", 'select': 'IDRADICADO,' + NEG["CampoTipologia"], 'lote': SEL["LoteMaximo"], 'orden': SEL["Orden"]}""")
AGREGA_NE = expr("""dict({locDicConsulta}, seleccion={locDicConsulta}['base'] + " and " + SEL["CampoIdentificacion"] + " ne '" + SEL["LiteralIdentificacionAusente"] + "'")""")
FILTRO_EQ = expr("""{locDicConsulta}['base'] + " and " + SEL["CampoIdentificacion"] + " eq '" + SEL["LiteralIdentificacionAusente"] + "'\"""")


def py(descripcion, *lineas):
    return {"father": "execScriptPython", "description": descripcion, "command": "\n".join(lineas)}


def paso(descripcion, variable, llamada):
    return py(descripcion, "from habeasdata import pasos", f"SetVar('{variable}', {llamada})")


def sv(descripcion, variable, expresion):
    return {"father": "setVar", "var": variable, "command": expresion, "description": descripcion}


def si(descripcion, condicion, entonces, sino=None):
    return {"father": "evaluateIf", "description": descripcion, "command": condicion, "children": entonces, "else": sino or []}


def grupo(descripcion, hijos):
    return {"father": "group", "description": descripcion, "children": hijos}


def para(descripcion, iterable, variable, hijos):
    return {"father": "for", "description": descripcion, "command": json.dumps({"iterable": iterable, "count": 0}),
            "var": variable, "children": hijos}


def detener(variable_resultado):
    """Un paso falló de forma crítica: la corrida se detiene con el motivo del paso."""
    return [sv("Marca la ejecución como detenida y guarda el motivo del paso que falló", "glbDicEstado",
               "dict({glbDicEstado}, estado='detenido', motivo_detencion=" + variable_resultado + '["mensaje"])')]


def anexar(variable, valor_expr):
    return f"{{{variable}}} + [{valor_expr}]"


INICIALIZAR = grupo("HU002HU003HU004 - Inicializar el Asistente", [
    sv("Estado de la ejecución: estado, motivo si la selección queda vacía (HU-002), total de radicados y motivo de detención",
       "glbDicEstado", "{'estado': 'ok', 'motivo_sin_casos': None, 'total_radicados': 0, 'motivo_detencion': ''}"),
    sv("Radicados seleccionados por HU-002", "glbArrIdsRadicados", "[]"),
    sv("Radicados descartados por identificación ausente (HU-002)", "glbArrIdsDescartados", "[]"),
    sv("Radicados que avanzan a la validación de deuda (HU-004)", "glbArrAvanzan", "[]"),
    sv("Radicados en excepción de negocio 1 (HU-004)", "glbArrExcepcionesNegocioUno", "[]"),
    sv("Radicados en excepción de sistema (HU-003, HU-004)", "glbArrExcepcionesSistema", "[]"),
    py("Carga los tres JSON de configuración, crea la estructura de carpetas y los dos logs del día",
       "import sys",
       "raiz = GetVar('glbStrRutaRaiz')",
       "sys.path.insert(0, raiz + '/Scripts')",
       "for nombre in [m for m in sys.modules if m == 'habeasdata' or m.startswith('habeasdata.')]:",
       "    del sys.modules[nombre]",
       "from habeasdata import pasos",
       "SetVar('glbDicInicio', pasos.iniciar(raiz))"),
    paso("Lee los parámetros de negocio de la configuración (tipología, campo, literal de ausencia, lote, orden)",
         "glbDicParametros", "pasos.parametros()"),
])

HU002 = grupo("HU002 - Filtrar radicados de Exclusión de Datos", [
    paso("Solicita el token OAuth (client_credentials, vigencia 300 s); el secreto sale del Administrador de credenciales",
         "glbDicAutenticacion", "pasos.solicitar_token()"),
    si("El token se obtuvo", '{glbDicAutenticacion}["ok"] == True', [
        sv("Arma la consulta de HU-002: filtro OData de la tipología ($filter, base de la selección), campos ($select), lote ($first) y orden ($orderby)",
           "locDicConsulta", FILTRO_BASE),
        si("Se descartan los radicados sin identificación (parámetro)", SEL + '["DescartarIdentificacionAusente"] == True', [
            sv("Agrega al filtro: identificación distinta de «NO APORTA»", "locDicConsulta", AGREGA_NE)]),
        paso("Consulta los radicados de exclusión (GET OData con $filter, $select, $first y $orderby)", "glbDicSeleccion",
             "pasos.consultar_seleccion(GetVar('locDicConsulta'))"),
        si("La consulta respondió", '{glbDicSeleccion}["ok"] == True', [
            sv("Guarda los radicados seleccionados", "glbArrIdsRadicados", '{glbDicSeleccion}["ids"]'),
            paso("Deja constancia en el log de auditoría de los radicados identificados", "locDicEvento",
                 "pasos.evento(str(len(pasos.objeto(GetVar('glbArrIdsRadicados')))) + ' radicados de exclusión identificados')"),
            si("Se descartan los radicados sin identificación (parámetro)", SEL + '["DescartarIdentificacionAusente"] == True', [
                sv("Arma el filtro de los descartados: identificación igual a «NO APORTA»", "locStrFiltroDescartados",
                   FILTRO_EQ),
                paso("Consulta los radicados descartados para no perderlos en silencio", "glbDicDescartados",
                     "pasos.consultar_odata(GetVar('locStrFiltroDescartados'), 'IDRADICADO')"),
                si("La consulta de descartados respondió", '{glbDicDescartados}["ok"] == True', [
                    sv("Guarda los radicados descartados", "glbArrIdsDescartados", '{glbDicDescartados}["ids"]'),
                    paso("Deja los descartados en el log de auditoría y en el reporte", "glbDicRegistroDescartados",
                         "pasos.registrar_descartados(GetVar('glbArrIdsDescartados'))")],
                   detener("{glbDicDescartados}")),
            ]),
            si("La selección quedó vacía y no hubo fallos", "{glbDicEstado}['estado'] == 'ok' and len({glbArrIdsRadicados}) == 0", [
                paso("Consulta el total de radicados (consulta general, sin $filter)", "glbDicGeneral",
                     "pasos.consultar_odata('', 'IDRADICADO')"),
                si("La consulta general respondió", '{glbDicGeneral}["ok"] == True', [
                    sv("Total de radicados de la consulta general", "glbDicEstado", 'dict({glbDicEstado}, total_radicados=len({glbDicGeneral}["ids"]))'),
                    si("Todos los de la tipología fueron descartados", "len({glbArrIdsDescartados}) > 0",
                       [sv("Motivo: solo descartados", "glbDicEstado", "dict({glbDicEstado}, motivo_sin_casos='solo_descartados')")],
                       [si("Hay radicados, pero ninguno de la tipología", "{glbDicEstado}[\"total_radicados\"] > 0",
                           [sv("Motivo: tipología ausente", "glbDicEstado", "dict({glbDicEstado}, motivo_sin_casos='tipologia_ausente')")],
                           [sv("Motivo: bandeja vacía", "glbDicEstado", "dict({glbDicEstado}, motivo_sin_casos='bandeja_vacia')")])]),
                    paso("Registra «0 casos» y la cadencia del reintento (CADENCIA_REINTENTO_BANDEJA_VACIA)", "glbDicSinCasos",
                         "pasos.registrar_sin_casos(pasos.objeto(GetVar('glbDicEstado'))['motivo_sin_casos'], pasos.objeto(GetVar('glbDicEstado'))['total_radicados'])")],
                   detener("{glbDicGeneral}")),
            ]),
        ], detener("{glbDicSeleccion}")),
    ], detener("{glbDicAutenticacion}")),
    si("Sigue sin casos: agenda el reintento (espera la cadencia y vuelve a consultar)",
       "{glbDicEstado}['estado'] == 'ok' and len({glbArrIdsRadicados}) == 0 and {glbDicEstado}['motivo_sin_casos'] is not None", [
        paso("Espera MinutosEntreReintentos y reconsulta, hasta MaximoReintentosDiarios o hasta que aparezcan casos "
             "(CADENCIA_REINTENTO_BANDEJA_VACIA)", "glbDicReintento", "pasos.reintentar_bandeja()"),
        si("Hubo reintentos y la consulta respondió", '{glbDicReintento}["ok"] == True and {glbDicReintento}["cambia"] == True', [
            sv("Guarda los radicados seleccionados en el reintento", "glbArrIdsRadicados", '{glbDicReintento}["ids"]'),
            sv("Guarda los descartados del último intento", "glbArrIdsDescartados", '{glbDicReintento}["descartados"]'),
            sv("Motivo con el que terminó el último intento", "glbDicEstado",
               "dict({glbDicEstado}, motivo_sin_casos={glbDicReintento}['motivo'])")]),
        si("El reintento se detuvo por una falla crítica", '{glbDicReintento}["ok"] == False', detener("{glbDicReintento}")),
    ]),
])

HU003 = grupo("HU003 - Leer datos paramétricos", [
    paso("Lee el radicado por IDRADICADO (GET individual)", "locDicLectura", "pasos.leer_radicado(GetVar('locStrIdRadicado'))"),
    si("El radicado se pudo leer", '{locDicLectura}["ok"] == True', [
        paso("Limpia «No aporta» y vacíos (= ausente) y separa los valores de cada canal por «/»", "locDicPreparado",
             "pasos.preparar_campos(GetVar('locDicLectura'))"),
        paso("Clasifica cada teléfono por dígitos: celular, fijo o sin clasificar", "locDicCaso",
             "pasos.clasificar_telefonos(GetVar('locDicPreparado'))"),
    ], [
        py("Registra la excepción de sistema del radicado (log de errores y reporte)",
           "from habeasdata import pasos",
           "pasos.registrar_excepcion_sistema(GetVar('locStrIdRadicado'), pasos.objeto(GetVar('locDicLectura'))['mensaje'])"),
        sv("Anota el radicado en excepciones de sistema", "glbArrExcepcionesSistema", anexar("glbArrExcepcionesSistema", "'{locStrIdRadicado}'")),
    ]),
])


LEIDO = '{locDicLectura}["ok"] == True'


def motivo_si(descripcion, condicion, etiqueta):
    return si(descripcion, LEIDO + " and " + condicion,
              [sv("Agrega el motivo", "locArrMotivos", anexar("locArrMotivos", f"'{etiqueta}'"))])


# Profundidad bajo el `for`: como máximo 2 decisiones anidadas (el grupo solo organiza). Por eso «el radicado quedó leído»
# acompaña a cada condición en vez de envolver todo el bloque.
HU004 = grupo("HU004 - Validar campos obligatorios", [
    sv("Lista de motivos de incompletitud (vacía al empezar cada radicado)", "locArrMotivos", "[]"),
    motivo_si("Falta el nombre del cliente", '{locDicCaso}["nombre"] is None', "NOMBRE DEL CLIENTE"),
    motivo_si("Falta el tipo de identificación", '{locDicCaso}["tipo_identificacion"] is None', "TIPO DE IDENTIFICACION"),
    motivo_si("Falta el número de identificación", '{locDicCaso}["numero_identificacion"] is None', "NUMERO DE IDENTIFICACION"),
    motivo_si("No hay ningún canal de contacto (ni correo ni teléfono)",
              'not {locDicCaso}["canal_correo"] and not {locDicCaso}["canal_telefono"]', "SIN CANAL DE CONTACTO"),
    si("El caso está completo", LEIDO + " and len({locArrMotivos}) == 0", [
        paso("Registra el avance a la validación de deuda en el reporte", "locDicResultado", "pasos.registrar_avance(GetVar('locDicCaso'))"),
        sv("Anota el radicado en los que avanzan", "glbArrAvanzan", anexar("glbArrAvanzan", "'{locStrIdRadicado}'")),
    ]),
    si("El caso está incompleto: excepción de negocio 1", LEIDO + " and len({locArrMotivos}) > 0", [
        paso("Escribe el comentario de la excepción de negocio 1 en Gestión → Detalle", "locDicComentario",
             "pasos.comentar_excepcion_1(GetVar('locDicCaso'), GetVar('locArrMotivos'))"),
        si("El comentario quedó registrado", '{locDicComentario}["ok"] == True', [
            paso("Registra la excepción de negocio 1 en el reporte", "locDicResultado",
                 "pasos.registrar_excepcion_negocio_1(GetVar('locDicCaso'), GetVar('locArrMotivos'))"),
            sv("Anota el radicado en excepciones de negocio 1", "glbArrExcepcionesNegocioUno",
               anexar("glbArrExcepcionesNegocioUno", "'{locStrIdRadicado}'")),
        ], [
            py("Registra la excepción de sistema (no se pudo escribir el comentario)",
               "from habeasdata import pasos",
               "pasos.registrar_excepcion_sistema(GetVar('locStrIdRadicado'), pasos.objeto(GetVar('locDicComentario'))['mensaje'])"),
            sv("Anota el radicado en excepciones de sistema", "glbArrExcepcionesSistema",
               anexar("glbArrExcepcionesSistema", "'{locStrIdRadicado}'")),
        ]),
    ]),
])

ITERACION = si("Hay radicados que procesar", "{glbDicEstado}['estado'] == 'ok' and len({glbArrIdsRadicados}) > 0", [
    para("Iteración por radicado de exclusión", "{glbArrIdsRadicados}", "locStrIdRadicado", [
        paso("Deja constancia del inicio del radicado en el log de auditoría", "locDicEvento",
             "pasos.evento('Inicio del radicado ' + GetVar('locStrIdRadicado'))"),
        HU003,
        HU004,
        paso("Deja constancia del fin del radicado en el log de auditoría", "locDicEvento",
             "pasos.evento('Fin del radicado ' + GetVar('locStrIdRadicado'))"),
    ]),
])

CIERRE = grupo("HU002HU003HU004 - Cierre y registro de ejecución", [
    si("La ejecución se detuvo", "{glbDicEstado}['estado'] == 'detenido'", [
        paso("Registra la detención en el log de errores y prepara el aviso «Detenido»", "glbDicDetencion",
             "pasos.registrar_detencion(pasos.objeto(GetVar('glbDicEstado'))['motivo_detencion'])"),
        sv("Asunto del aviso que se enviará al equipo técnico", "glbStrAsuntoAviso", '{glbDicDetencion}["notificacion"]["asunto"]')]),
    py("Cierra la ejecución y deja el resumen sin PII (en modo real los datos personales se enmascaran)",
       "import json",
       "from habeasdata import pasos",
       "o = pasos.objeto",
       "detencion = o(GetVar('glbDicDetencion')) if pasos.objeto(GetVar('glbDicEstado'))['estado'] == 'detenido' else {}",
       "resumen = {'estado': o(GetVar('glbDicEstado'))['estado'], 'modo': o(GetVar('glbDicInicio'))['modo'],",
       "           'avanzan': o(GetVar('glbArrAvanzan')), 'excepciones_negocio_1': o(GetVar('glbArrExcepcionesNegocioUno')),",
       "           'excepciones_sistema': o(GetVar('glbArrExcepcionesSistema')),",
       "           'descartados_identificacion_ausente': o(GetVar('glbArrIdsDescartados')),",
       "           'motivo_sin_casos': o(GetVar('glbDicEstado'))['motivo_sin_casos'], 'notificacion': detencion.get('notificacion')}",
       "SetVar('glbStrResumen', json.dumps(pasos.cerrar(resumen)['resumen'], ensure_ascii=False, default=str))"),
    sv("Observación final de la corrida", "glbStrObservaciones",
       "'EP-001 modo=' + {glbDicInicio}[\"modo\"] + ' estado=' + {glbDicEstado}['estado'] + ' avanzan=' + str(len({glbArrAvanzan})) + "
       "' excepciones_negocio_1=' + str(len({glbArrExcepcionesNegocioUno})) + ' excepciones_sistema=' + str(len({glbArrExcepcionesSistema}))"),
    sv("El proceso terminó sin detenerse", "glbBlnEstadoProceso", "{glbDicEstado}['estado'] == 'ok'"),
])

CONTROL = {"father": "trycatch", "description": "Control de ejecución", "children": [
    INICIALIZAR,
    {"father": "trycatch", "description": "Proceso principal", "children": [HU002, ITERACION], "else": [
        sv("Marca fallo de sistema en el proceso principal", "glbBlnEstadoSistema", "False"),
        sv("Estado de la ejecución: detenido por excepción de sistema", "glbDicEstado", "dict({glbDicEstado}, estado='detenido', motivo_detencion='Excepción de sistema en el proceso principal')"),
    ]},
    CIERRE,
], "else": [
    sv("Marca fallo de sistema", "glbBlnEstadoSistema", "False"),
    sv("Observación de la excepción de sistema", "glbStrObservaciones", "'Excepcion de sistema en EP-001'"),
]}

VARIABLES = [("glbBlnEstadoSistema", "True"), ("glbBlnEstadoProceso", "True"), ("glbStrObservaciones", ""),
             ("glbIntReintentos", "3"), ("glbIntReintentosLogin", "3"), ("glbStrRutaRaiz", ""), ("glbStrResumen", ""),
             ("glbDicEstado", ""),
             ("glbDicInicio", ""), ("glbDicParametros", ""), ("glbDicAutenticacion", ""), ("glbDicSeleccion", ""),
             ("glbDicDescartados", ""), ("glbDicRegistroDescartados", ""), ("glbDicGeneral", ""), ("glbDicSinCasos", ""),
             ("glbDicDetencion", ""), ("glbDicReintento", ""), ("glbStrAsuntoAviso", ""), 
             ("glbArrIdsRadicados", ""), ("glbArrIdsDescartados", ""), ("glbArrAvanzan", ""),
             ("glbArrExcepcionesNegocioUno", ""), ("glbArrExcepcionesSistema", ""),
             ("locStrIdRadicado", ""), ("locDicConsulta", ""), ("locStrFiltroDescartados", ""),
             ("locDicLectura", ""), ("locDicPreparado", ""), ("locDicCaso", ""), ("locDicComentario", ""),
             ("locDicResultado", ""), ("locDicEvento", ""), ("locArrMotivos", "")]

ROBOT = {
    "name": "LabHabeasData",
    "description": ("Tarea principal EP-001: HU-002 filtrar radicados de Exclusión de Datos, HU-003 leer datos paramétricos y "
                    "HU-004 validar campos obligatorios, contra la API de Zeus (QA) o su fixture offline. "
                    "Desarrollador: Trycore Lab. Fecha: 2026-10-29. Version V1.0.0"),
    "vars": [{"name": nombre, "data": dato} for nombre, dato in VARIABLES],
    "commands": [CONTROL, {"father": "log_message", "option": "info", "command": "{glbStrObservaciones}",
                           "description": "Traza final de la ejecución"}],
}

if __name__ == "__main__":
    DESTINO.write_text(json.dumps(ROBOT, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"escrito {DESTINO.name}: {len(json.dumps(ROBOT))} caracteres")
