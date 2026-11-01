"""EP-003 — Exclusión en el repositorio local: HU-010 (buscar duplicados) y HU-011 (registrar la exclusión).

HU-010 corre después de la completitud (HU-004) y ANTES de la identidad (HU-006/007): consulta cada valor de cada canal por
separado (llave compuesta identificación + celular, o identificación + correo). Solo el valor duplicado genera la excepción de
negocio 4; los demás continúan. HU-011 corre tras la identidad coincidente: inserta `Exclusion` y una fila por valor en
`Celulares`/`Correos` (14 columnas), cruza contra las maestras y elimina el registro de la maestra. HU-009 (Cobra) es un stub:
gestor, sucursal, ID CLIENTE/CODEUDOR, FUENTE y TIPO USUARIO salen de `habeasdata/sinteticos/stub_cobra.json`.
Cada transición se registra en `Transacciones`, incluidos los fallos.
"""
import json
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
    return "duplicado: " + ", ".join(sorted({v["canal"] for v in resultado["duplicados"]}))


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
    """Por cada valor: inserta la fila del canal (no duplica un contacto ya presente), lo cruza contra la maestra
    (verificado = estaba en la maestra; el cruce no la altera) y, confirmada la inserción, elimina el registro de la maestra.
    Una falla persistente detiene el caso: en la inserción no se elimina nada de la maestra; en la eliminación la fila ya
    insertada se conserva. Devuelve el resultado con `error` y `operacion` si el caso quedó en excepción de sistema."""
    resultado = {"exclusion": False, "insertados": [], "ya_presentes": [], "verificados": [], "eliminados": [], "error": None,
                 "operacion": None}
    if not valores:
        return resultado
    try:
        repo.insertar_exclusion(caso["radicado_hijo"], caso["numero_identificacion"])
    except ErrorRepositorio as error:
        return dict(resultado, error=str(error), operacion="insertar")
    resultado["exclusion"] = True
    for v in valores:
        canal, valor = v["canal"], v["valor"]
        etiqueta = f"{canal}:{valor}"
        try:
            estado = repo.insertar_canal(canal, fila_exclusion(caso, canal, valor, cobra, fecha_exclusion))
        except ErrorRepositorio as error:
            return dict(resultado, error=str(error), operacion="insertar")
        resultado["insertados" if estado == "insertado" else "ya_presentes"].append(etiqueta)
        try:
            en_maestra = repo.existe_en_maestra(canal, caso["numero_identificacion"], valor)
            if en_maestra:
                resultado["verificados"].append(etiqueta)
                repo.eliminar_de_maestra(canal, caso["numero_identificacion"], valor)
                resultado["eliminados"].append(etiqueta)
        except ErrorRepositorio as error:
            return dict(resultado, error=str(error), operacion="eliminar")
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
    repo.fallas.update(ajustes.get("Fallas", {}))  # simula «el repositorio no responde» (null = falla persistente)
    return repo


# ---------- pasos de EP-003 (los usan igual el orquestador y el robot de Studio) ----------
# Cada función es UN paso visible del robot; el orquestador las encadena y así comparten rastro, reporte y transacciones.
def registrar_previas(repo, id_radicado, caso, estado):
    """Transacciones de las etapas previas (selección, lectura, completitud): estado = avanza | negocio_1 | sistema."""
    if caso is not None:
        repo.upsert_insumo(caso, 1)
    repo.registrar_transaccion(id_radicado, "seleccion", 1)
    repo.registrar_transaccion(id_radicado, "lectura", 2)
    if estado == "sistema":
        repo.registrar_transaccion(id_radicado, "lectura", 4, "fallo", "excepción de sistema al leer o escribir el radicado")
    elif estado == "negocio_1":
        repo.registrar_transaccion(id_radicado, "validacion_campos", 4, "ok", "excepción de negocio 1: datos incompletos")
    else:
        repo.registrar_transaccion(id_radicado, "validacion_campos", 2)


def duplicados_inicio(registro, repo, id_radicado):
    registro.auditoria(f"Inicio de duplicados del radicado {id_radicado}", MODULO)
    repo.registrar_transaccion(id_radicado, "duplicados", 2)


def duplicados_sistema(registro, repo, id_radicado, padre, mensaje):
    registro.error(f"Repositorio no respondió en duplicados del radicado {id_radicado}: {mensaje}", MODULO)
    registro.reporte(id_radicado, padre, "excepción de sistema", None, "repositorio no responde: duplicados")
    repo.registrar_transaccion(id_radicado, "duplicados", 4, "fallo", "el repositorio no respondió tras 3 intentos")
    registro.auditoria(f"Fin de duplicados del radicado {id_radicado}: excepcion_sistema", MODULO)


def duplicados_comentario_fallido(registro, repo, id_radicado, padre, mensaje):
    registro.error(f"No se pudo registrar el comentario del radicado {id_radicado}: {mensaje}", MODULO)
    registro.reporte(id_radicado, padre, "excepción de sistema", None, "comentario de duplicado no registrado")
    repo.registrar_transaccion(id_radicado, "duplicados", 4, "fallo", "comentario de duplicado rechazado por Zeus")
    registro.auditoria(f"Fin de duplicados del radicado {id_radicado}: excepcion_sistema", MODULO)


def duplicados_excepcion_4(registro, repo, id_radicado, padre, resultado):
    registro.reporte(id_radicado, padre, "excepción de negocio 4", "4", motivo_excepcion_4(resultado))
    if resultado["continua"]:
        repo.registrar_transaccion(id_radicado, "duplicados", 2, "ok", "duplicado parcial: los demás valores continúan")
    else:
        repo.registrar_transaccion(id_radicado, "duplicados", 4, "ok", "excepción de negocio 4: todos los valores ya excluidos")
    registro.auditoria(f"Fin de duplicados del radicado {id_radicado}: excepcion_negocio_4", MODULO)


def duplicados_sin_excepcion(registro, repo, id_radicado):
    repo.registrar_transaccion(id_radicado, "duplicados", 2, "ok", "sin duplicado")
    registro.auditoria(f"Fin de duplicados del radicado {id_radicado}: sin_duplicado", MODULO)


def exclusion_del_caso(registro, repo, caso, valores, stub, fecha_exclusion):
    """HU-011 de un radicado: inserta, cruza y elimina; deja reporte, log de errores y la transacción del resultado."""
    id_radicado, padre = caso["radicado_hijo"], caso["radicado_padre"]
    registro.auditoria(f"Inicio del registro de exclusión del radicado {id_radicado}", MODULO)
    repo.registrar_transaccion(id_radicado, "registro_exclusion", 2)
    resultado = registrar_exclusion(caso, valores, repo, datos_cobra(stub, id_radicado), fecha_exclusion)
    if resultado["error"]:
        registro.error(f"Repositorio falló al {resultado['operacion']} la exclusión del radicado {id_radicado}", MODULO)
        registro.reporte(id_radicado, padre, "excepción de sistema", None, f"repositorio falla: {resultado['operacion']} exclusión")
        repo.registrar_transaccion(id_radicado, "registro_exclusion", 4, "fallo", f"falla persistente al {resultado['operacion']}")
    else:
        parcial = repo.parcial(id_radicado)
        registro.reporte(id_radicado, padre, "exclusión registrada", None,
                         f"filas: {len(resultado['insertados'])}; ya presentes: {len(resultado['ya_presentes'])}; "
                         f"verificados en maestra: {len(resultado['verificados'])}; eliminados de maestra: {len(resultado['eliminados'])}")
        repo.registrar_transaccion(id_radicado, "registro_exclusion", 5 if parcial else 3, "ok",
                                   "registro parcial (hubo valores duplicados)" if parcial else "exclusión registrada")
    registro.auditoria(f"Fin del registro de exclusión del radicado {id_radicado}", MODULO)
    return resultado


# ---------- orquestación de EP-003 dentro de la corrida ----------
def etapa_duplicados(resumen, registro, escritura, repo):
    """HU-010 sobre los radicados que avanzaron (HU-004). Devuelve (radicados que siguen a identidad, valores a registrar)."""
    resumen.update(excepciones_negocio_4=[], duplicados={}, excepciones_sistema_repositorio=[])
    for id_radicado, caso in resumen["casos"].items():
        registrar_previas(repo, id_radicado, caso, "negocio_1" if id_radicado in resumen["excepciones_negocio_1"] else "avanza")
    for id_radicado in resumen["excepciones_sistema"]:
        registrar_previas(repo, id_radicado, None, "sistema")
    registro.auditoria("Inicio de la búsqueda de duplicados EP-003", MODULO)
    siguen, valores, fallidos = [], {}, 0
    for id_radicado in resumen["avanzan"]:
        caso = resumen["casos"][id_radicado]
        padre = caso["radicado_padre"]
        duplicados_inicio(registro, repo, id_radicado)
        try:
            resultado = buscar_duplicados(caso, repo)
        except ErrorRepositorio as error:
            fallidos += 1
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
    resumen["repositorio_inaccesible"] = bool(resumen["avanzan"]) and fallidos == len(resumen["avanzan"])
    return siguen, valores


def etapa_registro(resumen, registro, repo, valores, stub, fecha_exclusion):
    """HU-011 sobre los radicados con identidad validada."""
    resumen.update(exclusion_registrada=[], excepciones_sistema_exclusion=[])
    registro.auditoria("Inicio del registro de exclusión EP-003", MODULO)
    for id_radicado in resumen["validadas"]:
        resultado = exclusion_del_caso(registro, repo, resumen["casos"][id_radicado], valores.get(id_radicado, []), stub, fecha_exclusion)
        resumen["excepciones_sistema_exclusion" if resultado["error"] else "exclusion_registrada"].append(id_radicado)
    registro.auditoria("Fin del registro de exclusión EP-003", MODULO)
