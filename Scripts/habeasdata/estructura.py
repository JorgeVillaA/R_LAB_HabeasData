"""Creación de la estructura de carpetas en ejecución (anexo Trycore V1.0, R-02): la crea el bot al arrancar."""

CLAVES_FIJAS = ("Configuracion", "Temporales", "Documentos", "Scripts")
CLAVES_POR_FECHA = ("LogsSistema", "LogsAuditoria", "CapturasProceso", "CapturasError", "Reportes")


def carpeta_fechada(cfg, clave, fecha):
    return cfg.ruta(clave) / f"{fecha:%Y}" / f"{fecha:%m}"


def crear_estructura(cfg, fecha):
    creadas = {}
    for clave in CLAVES_FIJAS:
        destino = cfg.ruta(clave)
        destino.mkdir(parents=True, exist_ok=True)
        creadas[clave] = destino
    for clave in CLAVES_POR_FECHA:
        destino = carpeta_fechada(cfg, clave, fecha)
        destino.mkdir(parents=True, exist_ok=True)
        creadas[clave] = destino
    return creadas
