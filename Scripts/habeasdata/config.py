"""Carga de los tres JSON de configuración (ConfiguracionMaquina, ConfiguracionProceso, Maestro_Configuracion).

Nada paramétrico vive en la lógica: todo se lee de aquí. La raíz de ejecución es la llave
RutasVentanas.RutasProceso.RutaRaiz, resuelta contra la carpeta que contiene Configuracion/.
"""
import json
from pathlib import Path

NOMBRES = ("ConfiguracionMaquina", "ConfiguracionProceso", "Maestro_Configuracion")
DICCIONARIOS_MAQUINA = ("Globales", "Trazabilidad", "Notificaciones", "RutasVentanas")


class Config:
    def __init__(self, maquina, proceso, maestro, raiz):
        self.maquina = maquina
        self.proceso = proceso
        self.maestro = maestro
        self.raiz = raiz

    def ruta(self, clave):
        """Ruta absoluta de una carpeta declarada en RutasProceso."""
        relativa = self.maquina["RutasVentanas"]["RutasProceso"][clave]
        return self.raiz / relativa


def carpeta_base(base=None):
    if base is not None:
        return Path(base)
    return Path(__file__).resolve().parents[2]


def cargar(base=None):
    carpeta = carpeta_base(base)
    datos = {}
    for nombre in NOMBRES:
        datos[nombre] = json.loads((carpeta / "Configuracion" / f"{nombre}.json").read_text(encoding="utf-8"))
    maquina = datos["ConfiguracionMaquina"]
    ruta_raiz = maquina["RutasVentanas"]["RutasProceso"]["RutaRaiz"]
    raiz = (carpeta / ruta_raiz).resolve()
    return Config(maquina, datos["ConfiguracionProceso"], datos["Maestro_Configuracion"], raiz)
