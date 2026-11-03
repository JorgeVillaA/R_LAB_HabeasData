"""Bloques de EP-003 (HU-010 buscar duplicados, HU-011 registrar la exclusión) del robot LabHabeasData.

Mismas convenciones que EP-001/EP-002: grupos por historia, cada decisión es un `evaluateIf` visible con su descripción y el
Python (`habeasdata.pasos`) solo hace E/S con el repositorio local y escritura de logs/reporte. Cada decisión lleva su condición
completa (así la profundidad bajo el `for` por radicado se mantiene en 2). Todo se activa con `glbDicRepositorio['habilitado']`.
HU-010 corre tras la completitud (HU-004) y antes de la identidad; HU-011 tras la identidad validada.
"""


def construir(h):
    """`h` trae los constructores comunes del generador (paso, sv, si, grupo, anexar)."""
    paso, sv, si, grupo, anexar = h["paso"], h["sv"], h["si"], h["grupo"], h["anexar"]
    REPO = "{glbDicRepositorio}['habilitado'] == True"
    AVANZA = "'{locStrIdRadicado}' in {glbArrAvanzan}"
    HAY = REPO + " and " + AVANZA + " and {locDicDuplicado}['ok'] == True"

    def quita_de_identidad(descripcion):
        return sv(descripcion, "glbArrSiguenIdentidad",
                  "[x for x in {glbArrSiguenIdentidad} if x != '{locStrIdRadicado}']")

    hu010 = grupo("HU010 - Buscar duplicados de exclusión (repositorio local)", [
        sv("Resultado de duplicados del radicado (vacío al empezar)", "locDicDuplicado", "{'ok': True, 'duplicados': [], 'continua': True}"),
        sv("Resultado del comentario de duplicado (vacío al empezar)", "locDicComentarioDuplicado", "{'ok': True}"),
        si("El radicado avanzó (HU-004): busca cada valor de cada canal por separado (maestra y exclusión con llave compuesta)",
           REPO + " and " + AVANZA, [
               paso("Busca duplicados: identificación + celular en Celulares, identificación + correo en Correos", "locDicDuplicado",
                    "pasos.buscar_duplicados(GetVar('locDicCaso'))")]),
        si("El repositorio no respondió tras 3 intentos: excepción de sistema del caso (el bot continúa)",
           REPO + " and " + AVANZA + " and {locDicDuplicado}['ok'] == False", [
               paso("Registra la excepción de sistema del repositorio", "locDicEvento",
                    "pasos.registrar_duplicado_sistema(GetVar('locDicCaso'), pasos.objeto(GetVar('locDicDuplicado'))['mensaje'], 'repositorio')"),
               sv("Anota el radicado en excepciones de sistema del repositorio", "glbArrExcepcionesSistemaRepositorio",
                  anexar("glbArrExcepcionesSistemaRepositorio", "'{locStrIdRadicado}'")),
               sv("Anota el radicado en los que no pudieron consultar el repositorio", "glbArrRepositorioCaido",
                  anexar("glbArrRepositorioCaido", "'{locStrIdRadicado}'")),
               quita_de_identidad("El radicado no sigue a identidad")]),
        si("Hay valores duplicados: escribe la nota de excepción de negocio 4 en Gestión → Detalle",
           HAY + " and len({locDicDuplicado}['duplicados']) > 0", [
               paso("Comentario de la excepción de negocio 4 (revisión de Cartera)", "locDicComentarioDuplicado",
                    "pasos.comentar_duplicado(GetVar('locDicCaso'), GetVar('locDicDuplicado'))")]),
        si("La nota no se pudo registrar: excepción de sistema del caso",
           HAY + " and len({locDicDuplicado}['duplicados']) > 0 and {locDicComentarioDuplicado}['ok'] == False", [
               paso("Registra la excepción de sistema (nota de duplicado rechazada)", "locDicEvento",
                    "pasos.registrar_duplicado_sistema(GetVar('locDicCaso'), pasos.objeto(GetVar('locDicComentarioDuplicado'))['mensaje'], 'comentario')"),
               sv("Anota el radicado en excepciones de sistema del repositorio", "glbArrExcepcionesSistemaRepositorio",
                  anexar("glbArrExcepcionesSistemaRepositorio", "'{locStrIdRadicado}'")),
               quita_de_identidad("El radicado no sigue a identidad")]),
        si("La nota quedó registrada: excepción de negocio 4 (solo los valores duplicados)",
           HAY + " and len({locDicDuplicado}['duplicados']) > 0 and {locDicComentarioDuplicado}['ok'] == True", [
               paso("Registra la excepción de negocio 4 en el reporte y en Transacciones", "locDicEvento",
                    "pasos.registrar_duplicado_excepcion_4(GetVar('locDicCaso'), GetVar('locDicDuplicado'))"),
               sv("Anota el radicado en excepciones de negocio 4", "glbArrExcepcionesNegocioCuatro",
                  anexar("glbArrExcepcionesNegocioCuatro", "'{locStrIdRadicado}'"))]),
        si("Ningún valor es duplicado: sigue a la validación de identidad",
           HAY + " and len({locDicDuplicado}['duplicados']) == 0", [
               paso("Registra «sin duplicado» en Transacciones", "locDicEvento",
                    "pasos.registrar_duplicado_sin_excepcion(GetVar('locDicCaso'))")]),
        si("Todos sus valores ya estaban excluidos: no sigue a identidad",
           HAY + " and len({locDicDuplicado}['duplicados']) > 0 and {locDicComentarioDuplicado}['ok'] == True "
           "and {locDicDuplicado}['continua'] == False", [
               quita_de_identidad("El radicado no sigue a identidad")]),
    ])

    valida = REPO + " and {locDicIdentidad}['etapa'] == 'validada' and " + AVANZA
    hu011 = grupo("HU011 - Registrar la exclusión en base centralizada (repositorio local)", [
        sv("Resultado del registro de exclusión (vacío al empezar)", "locDicExclusion", "{'ok': True}"),
        si("Identidad validada: inserta la exclusión, cruza contra las maestras y elimina el registro de la maestra",
           valida, [
               paso("Registra la exclusión (Exclusion + una fila por valor en Celulares/Correos), verifica y elimina de la maestra",
                    "locDicExclusion", "pasos.registrar_exclusion(GetVar('locDicCaso'), GetVar('locDicDuplicado'))")]),
        si("Exclusión registrada", valida + " and {locDicExclusion}['ok'] == True", [
            sv("Anota el radicado en exclusiones registradas", "glbArrExclusionRegistrada",
               anexar("glbArrExclusionRegistrada", "'{locStrIdRadicado}'"))]),
        si("El repositorio falló de forma persistente: excepción de sistema del caso (el bot continúa)",
           valida + " and {locDicExclusion}['ok'] == False", [
               sv("Anota el radicado en excepciones de sistema de la exclusión", "glbArrExcepcionesSistemaExclusion",
                  anexar("glbArrExcepcionesSistemaExclusion", "'{locStrIdRadicado}'"))]),
    ])
    return hu010, hu011
