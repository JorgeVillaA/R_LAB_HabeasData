"""Logs de auditoría y de errores (anexo V1.0) y reporte de gestión.

Dos archivos por día, cuatro campos fijos `Ip;Fecha;AplicativoModulo;Observacion` separados por `;`,
faltante = NO APLICA, escritura en el momento del evento (R-12), observación sin `;` ni secretos.
"""
import re
from datetime import datetime

from .estructura import carpeta_fechada, crear_estructura
from .redaccion import enmascarar_texto, es_real

CAMPOS = ("Ip", "Fecha", "AplicativoModulo", "Observacion")
FALTANTE = "NO APLICA"
CAMPOS_REPORTE = ("Fecha", "RadicadoZeus", "RadicadoPadre", "Resultado", "Excepcion", "Observacion")
_SECRETO = re.compile(r"(?i)(bearer\s+|client_secret=|password=|token=)\S+")


def limpiar(valor):
    """Valor de campo de log: nunca vacío, sin `;`, sin saltos de línea, sin tokens ni contraseñas."""
    if valor is None:
        return FALTANTE
    texto = _SECRETO.sub(lambda m: m.group(1) + "***", str(valor))
    texto = texto.replace(";", ",").replace("\r", " ").replace("\n", " ").strip()
    return texto or FALTANTE


class Registro:
    def __init__(self, cfg, reloj=datetime.now):
        self.cfg = cfg
        self.reloj = reloj
        traza = cfg.maquina["Trazabilidad"]
        self.prefijo = traza["PrefijoArchivo"]
        self.ip = traza["Ip"]
        self.modulo = traza["AplicativoModulo"]
        self.redactar = es_real(cfg)

    def _ruta(self, clave, etiqueta):
        ahora = self.reloj()
        carpeta = carpeta_fechada(self.cfg, clave, ahora)
        return carpeta / f"{self.prefijo}_{etiqueta}_{ahora:%Y%m%d}.csv"

    def ruta_auditoria(self):
        return self._ruta("LogsAuditoria", "LOG_DE_AUDITORIA")

    def ruta_errores(self):
        return self._ruta("LogsSistema", "LOG_DE_ERRORES")

    def ruta_reporte(self):
        return self._ruta("Reportes", "INFORMEGESTION")

    def _escribir(self, ruta, campos, encabezado):
        ruta.parent.mkdir(parents=True, exist_ok=True)
        nuevo = not ruta.exists()
        with ruta.open("a", encoding="utf-8", newline="") as salida:
            if nuevo:
                salida.write(";".join(encabezado) + "\n")
            salida.write(";".join(self._campo(c) for c in campos) + "\n")

    def _campo(self, valor):
        texto = limpiar(valor)
        return enmascarar_texto(texto) if self.redactar else texto

    def asegurar_archivos(self):
        """Arranque: estructura de carpetas y los dos logs del día (un solo log no pasa revisión, R-05)."""
        crear_estructura(self.cfg, self.reloj())
        for ruta in (self.ruta_auditoria(), self.ruta_errores()):
            if not ruta.exists():
                ruta.write_text(";".join(CAMPOS) + "\n", encoding="utf-8", newline="")

    def _evento(self, ruta, aplicativo, observacion):
        marca = f"{self.reloj():%Y-%m-%d %H:%M:%S}"
        self._escribir(ruta, (self.ip, marca, aplicativo or self.modulo, observacion), CAMPOS)

    def auditoria(self, observacion, aplicativo=None):
        self._evento(self.ruta_auditoria(), aplicativo, observacion)

    def error(self, observacion, aplicativo=None):
        self._evento(self.ruta_errores(), aplicativo, observacion)

    def reporte(self, radicado=None, padre=None, resultado=None, excepcion=None, observacion=None):
        marca = f"{self.reloj():%Y-%m-%d %H:%M:%S}"
        self._escribir(self.ruta_reporte(), (marca, radicado, padre, resultado, excepcion, observacion), CAMPOS_REPORTE)
