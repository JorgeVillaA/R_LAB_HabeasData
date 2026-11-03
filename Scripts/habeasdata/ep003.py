"""EP-003 — Exclusión en el repositorio local: HU-010 (buscar duplicados) y HU-011 (registrar la exclusión).

HU-010 corre después de la completitud (HU-004) y ANTES de la identidad (HU-006/007): consulta cada valor de cada canal por
separado (llave compuesta identificación + celular, o identificación + correo). Solo el valor duplicado genera la excepción de
negocio 4; los demás continúan. HU-011 corre tras la identidad coincidente: inserta `Exclusion` y una fila por valor en
`Celulares`/`Correos` (14 columnas), cruza contra las maestras y elimina el registro de la maestra. HU-009 (Cobra) es un stub:
gestor, sucursal, ID CLIENTE/CODEUDOR, FUENTE y TIPO USUARIO salen de `habeasdata/sinteticos/stub_cobra.json`.
Cada transición se registra en `Transacciones`, incluidos los fallos.
"""
import json
import re
from pathlib import Path

from .repositorio import ErrorRepositorio, Repositorio
from .zeus import ErrorZeus

SINTETICOS = Path(__file__).resolve().parent / "sinteticos"  # datos 100 % sintéticos que viajan con los Scripts

MODULO = "EP-003"
CANALES_DEL_CASO = (("correo", "correos"), ("celular", "telefonos"))


def valores_de(caso):
    """Valores consultables por canal: cada correo y cada teléfono clasificado como celular (el fijo no tiene base de cruce)."""
    valores = [("correo", v) for v in caso.get("correos") or []]
    valores += [("celular", t["valor"]) for t in caso.get("telefonos") or [] if t["clase"] == "celular"]
    return valores


# ---------- HU-010 ----------
def buscar_duplicados(caso, repo):
    """Consulta cada valor por separado: primero la maestra (paso 1) y luego la sub-base de exclusión con llave compuesta
    (paso 2). Devuelve los valores con su resultado; `continua` es falso solo si todos los valores consultables son duplicados."""
    identificacion = caso["numero_identificacion"]
    valores = []
    for canal, valor in valores_de(caso):
        en_maestra = repo.existe_en_maestra(canal, identificacion, valor)
        duplicado = repo.existe_exclusion(canal, identificacion, valor)
        valores.append({"canal": canal, "valor": valor, "en_maestra": en_maestra, "duplicado": duplicado})
    duplicados = [v for v in valores if v["duplicado"]]
    restantes = [v for v in valores if not v["duplicado"]]
    return {"valores": valores, "duplicados": duplicados, "restantes": restantes,
            "continua": not duplicados or bool(restantes) or not valores}


def comentario_excepcion_4(resultado):
    por_canal = {}
    for v in resultado["duplicados"]:
        por_canal[v["canal"]] = por_canal.get(v["canal"], 0) + 1
    detalle = ", ".join(f"{canal}: {n} valor(es)" for canal, n in sorted(por_canal.items()))
    return ("Excepción de negocio 4 (duplicado de exclusión), revisión manual de Cartera. "
            f"Ya figura en la base de exclusión — {detalle}.")


def motivo_excepcion_4(resultado):
    """Un solo relato de la excepción 4 para el reporte, el log y `Transacciones` (parcial = los demás valores continúan)."""
    canales = ", ".join(sorted({v["canal"] for v in resultado["duplicados"]}))
    if resultado["continua"]:
        return f"excepción de negocio 4 (parcial): duplicado en {canales}, los demás valores continúan"
    return f"excepción de negocio 4: todos los valores ya excluidos ({canales})"


# ---------- HU-009 (stub) ----------
def cargar_stub(raiz_repo=SINTETICOS):
    ruta = Path(raiz_repo) / "stub_cobra.json"
    return json.loads(ruta.read_text(encoding="utf-8"))


def datos_cobra(stub, radicado):
    """Datos que en producción vienen de Cobra (HU-009): del fixture por radicado o los valores por defecto del stub."""
    return dict(stub["por_defecto"], **stub.get("por_radicado", {}).get(str(radicado), {}))


# ---------- HU-011 ----------
def fila_exclusion(caso, canal, valor, cobra, fecha_exclusion):
    tabla_columnas = {"celular": ("CELULAR", "ZEUS", "Identificación Dueño Celular", "Nombre Dueño Celular"),
                      "correo": ("CORREO", "Zeus", "IDENTIFICACIÓN DUEÑO CORREO", "NOMBRE DUEÑO CORREO")}[canal]
    col_valor, col_zeus, col_id_dueno, col_nombre_dueno = tabla_columnas
    return {"ID CLIENTE": cobra["ID CLIENTE"], "ID CODEUDOR": cobra["ID CODEUDOR"], "TIPO USUARIO": cobra["TIPO USUARIO"],
            "IDENTIFICACION": caso["numero_identificacion"], "NOMBRE": caso["nombre"], col_valor: valor, "FUENTE": cobra["FUENTE"],
            "FECHA CONSULTA": caso["fecha_recepcion"], col_zeus: caso["radicado_hijo"], "FECHA EXCLUSION": fecha_exclusion,
            col_id_dueno: caso["numero_identificacion"], col_nombre_dueno: caso["nombre"], "GESTOR": cobra["GESTOR"],
            "SUCURSAL": cobra["SUCURSAL"]}


def registrar_exclusion(caso, valores, repo, cobra, fecha_exclusion):
    """Primero se INSERTA todo (la fila de `Exclusion` siempre, y una fila por valor en `Celulares`/`Correos`; un contacto ya presente
    no se duplica). Solo cuando todas las inserciones están confirmadas se cruza cada valor contra su maestra (verificado) y se elimina
    su registro de la maestra. Una falla persistente al insertar deja las maestras intactas; al eliminar o cruzar, las filas ya
    insertadas se conservan. Devuelve el resultado con `error` y `operacion` (insertar | cruzar | eliminar) si el caso quedó en
    excepción de sistema. Sin valores de canal (p. ej. solo teléfono fijo, que no tiene tabla de canal) solo queda la fila de `Exclusion`."""
    resultado = {"exclusion": False, "insertados": [], "ya_presentes": [], "verificados": [], "eliminados": [], "error": None,
                 "operacion": None}
    try:
        repo.insertar_exclusion(caso["radicado_hijo"], caso["numero_identificacion"])
    except ErrorRepositorio as error:
        return dict(resultado, error=str(error), operacion="insertar")
    resultado["exclusion"] = True
    for v in valores:
        canal, valor = v["canal"], v["valor"]
        try:
            estado = repo.insertar_canal(canal, fila_exclusion(caso, canal, valor, cobra, fecha_exclusion))
        except ErrorRepositorio as error:
            return dict(resultado, error=str(error), operacion="insertar")
        resultado["insertados" if estado == "insertado" else "ya_presentes"].append(f"{canal}:{valor}")
    for v in valores:
        canal, valor = v["canal"], v["valor"]
        etiqueta = f"{canal}:{valor}"
        try:
            en_maestra = repo.existe_en_maestra(canal, caso["numero_identificacion"], valor)
        except ErrorRepositorio as error:
            return dict(resultado, error=str(error), operacion="cruzar")
        if en_maestra:
            resultado["verificados"].append(etiqueta)
            try:
                repo.eliminar_de_maestra(canal, caso["numero_identificacion"], valor, radicado=caso["radicado_hijo"])
            except ErrorRepositorio as error:
                return dict(resultado, error=str(error), operacion="eliminar")
            resultado["eliminados"].append(etiqueta)
    return resultado


# ---------- siembra del repositorio sintético ----------
def sembrar_desde_fixtures(repo, carpeta_fixtures=SINTETICOS):
    """Carga en el repositorio las maestras y las bases de exclusión sintéticas de `habeasdata/sinteticos/`."""
    base = Path(carpeta_fixtures)
    for canal, archivo_maestra, archivo_exclusion in (("celular", "maestra_celulares.json", "exclusion_celulares.json"),
                                                       ("correo", "maestra_correos.json", "exclusion_correos.json")):
        repo.sembrar(canal, json.loads((base / archivo_maestra).read_text(encoding="utf-8")), maestra=True)
        repo.sembrar(canal, json.loads((base / archivo_exclusion).read_text(encoding="utf-8")), maestra=False)


# ---------- apertura del repositorio de la corrida ----------
_SECRETO = re.compile(r"(?i)(secret|password|clave|bearer|accesstoken)")


def _aplanar(valor, prefijo=""):
    """Hojas de un JSON de configuración como (ruta con puntos, valor)."""
    if isinstance(valor, dict):
        for clave, hijo in valor.items():
            yield from _aplanar(hijo, f"{prefijo}.{clave}" if prefijo else str(clave))
    else:
        yield prefijo, valor


def parametros_de_la_corrida(cfg):
    """TODOS los parámetros operativos vigentes en la corrida (specs/repositorio-local.md: ventana, umbral, rutas…): las hojas de los
    tres JSON de configuración con su valor efectivo (Maestro sin prefijo, Proceso por su ruta, Máquina con `Maquina.`), más la raíz
    efectiva. Un valor cuyo nombre sea de un secreto no se guarda (los `*Env` y `*Target` solo nombran la variable o la credencial)."""
    parametros = dict(_aplanar(cfg.maestro))
    parametros.update(_aplanar(cfg.proceso))
    parametros.update(_aplanar(cfg.maquina, "Maquina"))
    parametros["Maquina.RutaRaizEfectiva"] = str(cfg.raiz)
    return {clave: (valor if isinstance(valor, str) else json.dumps(valor, ensure_ascii=False)) for clave, valor in parametros.items()
            if not (_SECRETO.search(clave.rsplit(".", 1)[-1]) and not clave.endswith(("Env", "Target")))}


def abrir_repositorio(cfg, dormir=None, reloj=None):
    """Repositorio de la corrida: archivo dentro de `Documentos` de la raíz (ninguna ruta absoluta en la lógica), sembrado con los
    datos sintéticos la primera vez. Los reintentos salen de NUMERO_REINTENTOS_SISTEMA."""
    ajustes = cfg.proceso["Repositorio"]
    carpeta = cfg.ruta("Documentos") / ajustes["Carpeta"]
    carpeta.mkdir(parents=True, exist_ok=True)
    existente = (carpeta / ajustes["Archivo"]).exists()
    argumentos = {k: v for k, v in (("dormir", dormir), ("reloj", reloj)) if v is not None}
    repo = Repositorio(carpeta / ajustes["Archivo"], reintentos=cfg.maestro["NUMERO_REINTENTOS_SISTEMA"], **argumentos)
    if not existente and ajustes.get("SembrarSinteticos", True):
        sembrar_desde_fixtures(repo)
    repo.guardar_parametros(parametros_de_la_corrida(cfg))
    repo.fallas.update(ajustes.get("Fallas", {}))  # simula «el repositorio no responde» (null = falla persistente)
    return repo


# ---------- pasos de EP-003 (los usan igual el orquestador y el robot de Studio) ----------
# Cada función es UN paso visible del robot; el orquestador las encadena y así comparten rastro, reporte y transacciones.
# Una fila de `Transacciones` = una transición con información (nunca un marcador de inicio vacío) y se escribe en el instante en
# que ocurre la etapa. `Resultado` = `fallo` cuando el estado nuevo es 4. Toda excepción deja su fila en `Excepciones` y el caso que
# pasa a gestión manual, la suya en `Gestores` (gestor y agencia del stub de Cobra, HU-009; «SIN ASIGNAR» si no hay dato).
SIN_ASIGNAR = "SIN ASIGNAR"


def cerrar_en_excepcion(repo, id_radicado, etapa, tipo, motivo, stub=None, derivar=True):
    """Cierra el caso en 4 (No Exitoso) con su excepción (1, 3, 4, sistema o gestion_manual) y lo deriva a gestión manual."""
    repo.registrar_transaccion(id_radicado, etapa, 4, "fallo", motivo, excepcion=tipo)
    if derivar:
        cobra = datos_cobra(stub or cargar_stub(), id_radicado)
        repo.derivar_a_gestion(id_radicado, cobra.get("GESTOR") or SIN_ASIGNAR, cobra.get("SUCURSAL") or SIN_ASIGNAR,
                               SIN_ASIGNAR, SIN_ASIGNAR, f"excepción {tipo}: {motivo}")


def seleccionado(repo, id_radicado):
    """HU-002: el bot toma el radicado de la bandeja de exclusión."""
    repo.abrir_insumo(id_radicado)
    repo.registrar_transaccion(id_radicado, "seleccion", 1, "ok", "seleccionado de la bandeja de exclusión de Zeus")


def leido(repo, id_radicado):
    """HU-003: el radicado se leyó de Zeus."""
    repo.registrar_transaccion(id_radicado, "lectura", 2, "ok", "radicado leído de Zeus")


def descartado(repo, id_radicado):
    """HU-002: identificación ausente. Es una transición 1 → 4 como cualquier otra (una sola vez por corrida)."""
    if repo.estado_en_corrida(id_radicado) is not None:
        return
    repo.abrir_insumo(id_radicado)
    repo.registrar_transaccion(id_radicado, "seleccion", 1, "ok", "en la bandeja de exclusión con identificación ausente")
    repo.registrar_transaccion(id_radicado, "seleccion", 4, "fallo", "descartado: identificación ausente, sin gestión del bot")


def campos_completos(repo, caso):
    """HU-004: el caso pasa la completitud y sigue a duplicados e identidad."""
    repo.upsert_insumo(caso)
    repo.registrar_transaccion(caso["radicado_hijo"], "validacion_campos", 2, "ok", "campos obligatorios completos, continúa a duplicados e identidad")


def datos_incompletos(repo, caso, motivos, stub=None):
    """HU-004: excepción de negocio 1."""
    repo.upsert_insumo(caso)
    cerrar_en_excepcion(repo, caso["radicado_hijo"], "validacion_campos", "1",
                        "excepción de negocio 1: datos incompletos (" + ", ".join(motivos) + ")", stub)


def excepcion_sistema_caso(repo, id_radicado, mensaje, stub=None):
    """Falla de sistema al leer el radicado (etapa lectura) o al escribir su comentario (etapa validación de campos)."""
    etapa = "lectura" if repo.estado_en_corrida(id_radicado) in (None, 1) else "validacion_campos"
    cerrar_en_excepcion(repo, id_radicado, etapa, "sistema", f"excepción de sistema: {mensaje}", stub)


def duplicados_inicio(registro, id_radicado):
    registro.auditoria(f"Inicio de duplicados del radicado {id_radicado}", MODULO)


def duplicados_sistema(registro, repo, id_radicado, padre, mensaje, stub=None):
    registro.error(f"Repositorio no respondió en duplicados del radicado {id_radicado}: {mensaje}", MODULO)
    registro.reporte(id_radicado, padre, "excepción de sistema", None, "repositorio no responde: duplicados")
    cerrar_en_excepcion(repo, id_radicado, "duplicados", "sistema", f"el repositorio no respondió tras {repo.reintentos} intentos", stub)
    registro.auditoria(f"Fin de duplicados del radicado {id_radicado}: excepcion_sistema", MODULO)


def duplicados_comentario_fallido(registro, repo, id_radicado, padre, mensaje, stub=None):
    registro.error(f"No se pudo registrar el comentario del radicado {id_radicado}: {mensaje}", MODULO)
    registro.reporte(id_radicado, padre, "excepción de sistema", None, "comentario de duplicado no registrado")
    cerrar_en_excepcion(repo, id_radicado, "duplicados", "sistema", "comentario de duplicado rechazado por Zeus", stub)
    registro.auditoria(f"Fin de duplicados del radicado {id_radicado}: excepcion_sistema", MODULO)


def duplicados_excepcion_4(registro, repo, id_radicado, padre, resultado, stub=None):
    motivo = motivo_excepcion_4(resultado)  # el mismo texto en el reporte, el log y la base
    registro.reporte(id_radicado, padre, "excepción de negocio 4", "4", motivo)
    if resultado["continua"]:
        repo.registrar_transaccion(id_radicado, "duplicados", 2, "ok", motivo, excepcion="4")
    else:
        cerrar_en_excepcion(repo, id_radicado, "duplicados", "4", motivo, stub)
    registro.auditoria(f"Fin de duplicados del radicado {id_radicado}: {motivo}", MODULO)


def duplicados_sin_excepcion(registro, repo, id_radicado):
    repo.registrar_transaccion(id_radicado, "duplicados", 2, "ok", "sin duplicado")
    registro.auditoria(f"Fin de duplicados del radicado {id_radicado}: sin_duplicado", MODULO)


def exclusion_del_caso(registro, repo, caso, valores, stub, fecha_exclusion):
    """HU-011 de un radicado: inserta, cruza y elimina; deja reporte, log de errores y la transacción del resultado."""
    id_radicado, padre = caso["radicado_hijo"], caso["radicado_padre"]
    registro.auditoria(f"Inicio del registro de exclusión del radicado {id_radicado}", MODULO)
    resultado = registrar_exclusion(caso, valores, repo, datos_cobra(stub, id_radicado), fecha_exclusion)
    if resultado["error"]:
        registro.error(f"Repositorio falló al {resultado['operacion']} la exclusión del radicado {id_radicado}", MODULO)
        registro.reporte(id_radicado, padre, "excepción de sistema", None, f"repositorio falla: {resultado['operacion']} exclusión")
        cerrar_en_excepcion(repo, id_radicado, "registro_exclusion", "sistema", f"falla persistente al {resultado['operacion']}", stub)
    else:
        parcial = repo.parcial(id_radicado)
        sin_canal = not valores
        registro.reporte(id_radicado, padre, "exclusión registrada", None,
                         f"filas: {len(resultado['insertados'])}; ya presentes: {len(resultado['ya_presentes'])}; "
                         f"verificados en maestra: {len(resultado['verificados'])}; eliminados de maestra: {len(resultado['eliminados'])}"
                         + ("; solo la fila de Exclusion (sin celular ni correo: el fijo no tiene tabla de canal)" if sin_canal else ""))
        motivo = ("solo la fila de Exclusion: sin celular ni correo (el fijo no tiene tabla de canal)" if sin_canal else
                  "registro parcial (hubo valores duplicados)" if parcial else "exclusión registrada")
        repo.registrar_transaccion(id_radicado, "registro_exclusion", 5 if (parcial or sin_canal) else 3, "ok", motivo)
    registro.auditoria(f"Fin del registro de exclusión del radicado {id_radicado}", MODULO)
    return resultado


def transaccion_identidad(repo, id_radicado, etiqueta, via=None, puntaje=None, motivo=None, codigo=None, stub=None):
    """Resultado de identidad (EP-002) → transición. Validada: el caso sigue (2). Sin nombre (documento no cédula): sigue sin
    comparar nombre y queda cerrado como Procesado Parcialmente (5), pendiente de Villa. Las demás ramas cierran en 4 con su excepción."""
    if etiqueta == "validada":
        repo.registrar_transaccion(id_radicado, "identidad", 2, "ok", f"identidad validada ({via}, puntaje {puntaje})")
    elif etiqueta == "sin_nombre":
        repo.registrar_transaccion(id_radicado, "identidad", 5, "ok",
                                   f"respuesta sin nombre ({via}): el caso continúa sin comparar el nombre, Procesado Parcialmente")
    elif etiqueta == "excepcion_negocio_3":
        cerrar_en_excepcion(repo, id_radicado, "identidad", "3",
                            f"excepción de negocio 3: identidad no coincide ({via}, puntaje {puntaje}): {motivo}", stub)
    elif etiqueta == "revision_humana":
        cerrar_en_excepcion(repo, id_radicado, "identidad", "gestion_manual", f"revisión humana (fallback): {motivo}", stub)
    elif etiqueta == "gestion_manual":
        cerrar_en_excepcion(repo, id_radicado, "identidad", "gestion_manual", f"gestión manual: {motivo}", stub)
    else:
        cerrar_en_excepcion(repo, id_radicado, "identidad", "sistema", f"excepción de sistema en la identidad ({codigo})", stub)  # el código es el mismo en robot y orquestador; el texto del portal no


def cerrar_corrida(repo, stub=None, detalle=None, registro=None, pasos=None):
    """Fin de la corrida: ningún caso queda abierto (un caso en 1 o 2 se cierra en 4 con su motivo) y se escribe `LogEjecucion` con el
    identificador de la corrida del registro y los pasos del módulo."""
    for id_radicado in repo.abiertos_de_la_corrida():
        cerrar_en_excepcion(repo, id_radicado, "cierre", "sistema", "el caso quedó abierto al terminar la corrida", stub)
    return repo.registrar_log_ejecucion(detalle, registro.id_corrida if registro is not None else None, pasos)


# ---------- orquestación de EP-003 dentro de la corrida ----------
def etapa_duplicados(resumen, registro, escritura, repo):
    """HU-010 sobre los radicados que avanzaron (HU-004). Devuelve (radicados que siguen a identidad, valores a registrar)."""
    resumen.update(excepciones_negocio_4=[], duplicados={}, excepciones_sistema_repositorio=[], repositorio_caido=[])
    registro.auditoria("Inicio de la búsqueda de duplicados EP-003", MODULO)
    siguen, valores = [], {}
    for id_radicado in resumen["avanzan"]:
        caso = resumen["casos"][id_radicado]
        padre = caso["radicado_padre"]
        duplicados_inicio(registro, id_radicado)
        try:
            resultado = buscar_duplicados(caso, repo)
        except ErrorRepositorio as error:
            resumen["repositorio_caido"].append(id_radicado)
            resumen["excepciones_sistema_repositorio"].append(id_radicado)
            duplicados_sistema(registro, repo, id_radicado, padre, str(error))
            continue
        if resultado["duplicados"]:
            try:
                escritura.comentar(caso["radicado_hijo"], comentario_excepcion_4(resultado))
            except ErrorZeus as error:
                resumen["excepciones_sistema_repositorio"].append(id_radicado)
                duplicados_comentario_fallido(registro, repo, id_radicado, padre, str(error))
                continue
            resumen["excepciones_negocio_4"].append(id_radicado)
            resumen["duplicados"][id_radicado] = sorted({v["canal"] for v in resultado["duplicados"]})
            duplicados_excepcion_4(registro, repo, id_radicado, padre, resultado)
        else:
            duplicados_sin_excepcion(registro, repo, id_radicado)
        if resultado["continua"]:
            siguen.append(id_radicado)
            valores[id_radicado] = resultado["restantes"]
    registro.auditoria("Fin de la búsqueda de duplicados EP-003", MODULO)
    resumen["repositorio_inaccesible"] = bool(resumen["avanzan"]) and len(resumen["repositorio_caido"]) == len(resumen["avanzan"])
    return siguen, valores


def etapa_registro(resumen, registro, repo, valores, stub, fecha_exclusion):
    """HU-011 sobre los radicados con identidad validada."""
    resumen.update(exclusion_registrada=[], excepciones_sistema_exclusion=[])
    registro.auditoria("Inicio del registro de exclusión EP-003", MODULO)
    for id_radicado in resumen["validadas"]:
        resultado = exclusion_del_caso(registro, repo, resumen["casos"][id_radicado], valores.get(id_radicado, []), stub, fecha_exclusion)
        resumen["excepciones_sistema_exclusion" if resultado["error"] else "exclusion_registrada"].append(id_radicado)
    registro.auditoria("Fin del registro de exclusión EP-003", MODULO)
