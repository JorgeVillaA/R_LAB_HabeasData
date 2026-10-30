"""EP-002: validación de identidad (HU-006 Policía, HU-007 Procuraduría con HU-026a, HU-008 comparación de nombres).

Orquestador de referencia que usa el banco (el robot de Studio lo replica con bloques visibles). Cadena del origen (C-04):
cédula → Policía; sin resultado o caída persistente → Procuraduría; cuota o reCAPTCHA → revisión humana (el bot no evade el
captcha); documento no cédula → Procuraduría; NIT con dígitos distintos de 10 → gestión manual sin consultar.
Nunca se escribe un nombre ni una identificación en los logs: solo radicado, vía, puntaje y códigos.
"""
from . import nombres
from .captcha import ErrorCaptcha
from .ep001 import ExcepcionSistemaCaso, procesar as procesar_ep001
from .portales import ClientePortales, ErrorPortal, RevisionHumana, TIPOS_PROCURADURIA
from .zeus import ErrorZeus

MODULO = "EP-002"


def tipo_normalizado(caso):
    return nombres_sin_tildes(caso.get("tipo_identificacion") or "")


def nombres_sin_tildes(texto):
    import unicodedata
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").upper().strip()


def es_cedula(caso):
    return tipo_normalizado(caso) == "CEDULA DE CIUDADANIA"


def nit_valido(numero):
    """Regla cerrada: un NIT son exactamente 10 dígitos, sin guion ni espacios."""
    return len(numero) == 10 and numero.isdigit()


def comentario_excepcion_3(verdicto, via):
    return (f"Excepción de negocio 3 (identidad no coincide), revisión manual de Cartera. Fuente: {via}. "
            f"Puntaje: {verdicto['puntaje']}. Motivo: {verdicto['motivo']}")


def validar_identidad(caso, portales, captchas, umbral):
    """Una consulta de identidad. Devuelve {"resultado", "via", "nombre_portal"?, "codigo"?, "motivo"?}.

    resultado: validada | excepcion_negocio_3 | gestion_manual | revision_humana | sin_nombre | excepcion_sistema.
    """
    numero, nombre_zeus = caso["numero_identificacion"], caso["nombre"]
    via = None
    if es_cedula(caso):
        try:
            policia = portales.consultar_policia(numero)
            via = "policia"
            if policia["resultado"] == "nombre":
                return con_veredicto(nombre_zeus, policia["nombre"], umbral, via)
        except RevisionHumana as revision:
            return {"resultado": "revision_humana", "via": "policia", "motivo": revision.motivo}
        except ErrorPortal as error:  # caída persistente de la Policía → Procuraduría (cadena del origen)
            via = "policia_caida:" + str(error)
    if tipo_normalizado(caso) == "NIT" and not nit_valido(numero):
        return {"resultado": "gestion_manual", "via": None, "motivo": "NIT con cantidad de dígitos distinta de 10: no se consulta"}
    codigo_tipo = TIPOS_PROCURADURIA.get(tipo_normalizado(caso))
    if codigo_tipo is None:
        return {"resultado": "gestion_manual", "via": None, "motivo": "tipo de documento sin consulta en la Procuraduría"}
    try:
        procuraduria = portales.consultar_procuraduria(codigo_tipo, numero, nombre_zeus, captchas)
    except ErrorCaptcha as error:
        return {"resultado": "excepcion_sistema", "via": "procuraduria", "codigo": error.codigo, "motivo": str(error)}
    except ErrorPortal as error:
        return {"resultado": "excepcion_sistema", "via": "procuraduria", "codigo": "PORTAL_NO_DISPONIBLE", "motivo": str(error)}
    if procuraduria["resultado"] == "nombre":
        return con_veredicto(nombre_zeus, procuraduria["nombre"], umbral, "procuraduria")
    if es_cedula(caso):  # ni la Policía ni la Procuraduría dieron resultado
        return {"resultado": "gestion_manual", "via": "procuraduria", "motivo": "sin resultado en Policía ni Procuraduría"}
    return {"resultado": "sin_nombre", "via": "procuraduria", "motivo": "respuesta sin nombre para documento no cédula"}


def con_veredicto(nombre_zeus, nombre_portal, umbral, via):
    veredicto = nombres.comparar(nombre_zeus, nombre_portal, umbral)
    return {"resultado": "validada" if veredicto["coincide"] else "excepcion_negocio_3", "via": via, "veredicto": veredicto}


def procesar(cfg, cliente, registro, escritura, portales=None, captchas=None):
    from .captcha import ServicioCaptchas
    resumen = procesar_ep001(cfg, cliente, registro, escritura)
    resumen.update(validadas=[], excepciones_negocio_3=[], gestion_manual=[], revision_humana=[], sin_nombre=[],
                   excepciones_sistema_identidad=[], via={}, codigos={})
    if resumen["estado"] != "ok":
        return resumen
    portales = portales or ClientePortales(cfg)
    ajustes = portales.ajustes
    captchas = captchas or ServicioCaptchas(ajustes["UrlCaptchas"], portales.reintentos, portales.backoff, portales.timeout,
                                            portales.dormir)
    umbral = cfg.maestro["UMBRAL_COINCIDENCIA_NOMBRES"]
    registro.auditoria(f"Inicio de la validación de identidad EP-002 (modo {portales.modo})", MODULO)
    for id_radicado in resumen["avanzan"]:
        caso = resumen["casos"][id_radicado]
        padre = caso["radicado_padre"]
        registro.auditoria(f"Inicio de la identidad del radicado {id_radicado}", MODULO)
        resultado = validar_identidad(caso, portales, captchas, umbral)
        etiqueta, via = resultado["resultado"], resultado.get("via")
        resumen["via"][id_radicado] = via
        if etiqueta == "excepcion_negocio_3":
            try:
                escritura.comentar(caso["radicado_hijo"], comentario_excepcion_3(resultado["veredicto"], via))
            except ErrorZeus as error:
                etiqueta, resultado = "excepcion_sistema", {"codigo": "COMENTARIO_NO_REGISTRADO", "motivo": str(error), "via": via}
        if etiqueta == "validada":
            resumen["validadas"].append(id_radicado)
            registro.reporte(id_radicado, padre, f"identidad validada ({via}, puntaje {resultado['veredicto']['puntaje']})")
        elif etiqueta == "excepcion_negocio_3":
            resumen["excepciones_negocio_3"].append(id_radicado)
            registro.reporte(id_radicado, padre, "excepción de negocio 3", "3",
                             f"{via}, puntaje {resultado['veredicto']['puntaje']}: {resultado['veredicto']['motivo']}")
        elif etiqueta == "revision_humana":
            resumen["revision_humana"].append(id_radicado)
            registro.reporte(id_radicado, padre, "revisión humana (fallback humano)", None, resultado["motivo"])
        elif etiqueta == "sin_nombre":
            resumen["sin_nombre"].append(id_radicado)
            registro.reporte(id_radicado, padre, "respuesta sin nombre; continúa", None, resultado["motivo"])
        elif etiqueta == "gestion_manual":
            resumen["gestion_manual"].append(id_radicado)
            registro.reporte(id_radicado, padre, "gestión manual", None, resultado["motivo"])
        else:  # excepción de sistema: el caso se deriva a gestión manual
            resumen["excepciones_sistema_identidad"].append(id_radicado)
            resumen["gestion_manual"].append(id_radicado)
            resumen["codigos"][id_radicado] = resultado["codigo"]
            registro.error(f"Radicado {id_radicado}: {resultado['codigo']}: {resultado['motivo']}", MODULO)
            registro.reporte(id_radicado, padre, "excepción de sistema; gestión manual", None, resultado["codigo"])
        registro.auditoria(f"Fin de la identidad del radicado {id_radicado}: {etiqueta}", MODULO)
    registro.auditoria("Fin de la validación de identidad EP-002", MODULO)
    return resumen
