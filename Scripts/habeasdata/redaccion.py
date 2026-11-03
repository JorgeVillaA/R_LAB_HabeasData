"""Redacción de PII para logs, resúmenes y evidencia cuando el cliente corre contra la API REAL de Zeus.

En modo fixture los datos son sintéticos y no se enmascaran. En modo real, nombre, identificación, correos y
teléfonos de los radicados no salen del proceso: ni a los logs, ni al reporte, ni a las variables del robot.
"""
import copy
import re

MASCARA = "***"
_CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_NUMERO_LARGO = re.compile(r"\d{7,}")  # cédulas, NIT y teléfonos; los radicados (6 dígitos) se conservan


def es_real(cfg):
    return cfg.proceso["ZeusApi"]["Modo"] == "real"


def enmascarar_texto(texto):
    return _NUMERO_LARGO.sub(MASCARA, _CORREO.sub(MASCARA, texto))


def caso_seguro(caso):
    seguro = copy.deepcopy(caso)
    for clave in ("nombre", "numero_identificacion"):
        if seguro.get(clave):
            seguro[clave] = MASCARA
    seguro["correos"] = [MASCARA for _ in seguro.get("correos", [])]
    seguro["telefonos"] = [{"valor": MASCARA, "clase": t["clase"]} for t in seguro.get("telefonos", [])]
    return seguro


def resumen_seguro(resumen, cfg):
    """Resumen apto para imprimir o guardar: idéntico en fixture, sin PII en modo real."""
    if not es_real(cfg):
        return resumen
    seguro = dict(resumen)
    seguro["casos"] = {id_: caso_seguro(caso) for id_, caso in resumen["casos"].items()}
    if seguro.get("notificacion"):
        seguro["notificacion"] = dict(seguro["notificacion"], motivo=enmascarar_texto(seguro["notificacion"]["motivo"]))
    return seguro
