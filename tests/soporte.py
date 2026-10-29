"""Soporte común de las pruebas: raíz temporal con la configuración del repo apuntando a un doble en puerto libre."""
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for carpeta in (REPO / "Scripts", REPO / "dobles" / "zeus_api"):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

from habeasdata.config import cargar  # noqa: E402
from habeasdata.registro import Registro  # noqa: E402
from habeasdata.zeus import ClienteZeus  # noqa: E402
from dobles.zeus_api.servidor import DobleZeus  # noqa: E402

CLIENTE, SECRETO = "cliente-de-prueba", "secreto-de-prueba-no-real"
ENTORNO = {"ZEUS_DOBLE_CLIENT_ID": CLIENTE, "ZEUS_DOBLE_CLIENT_SECRET": SECRETO}
RADICADOS = json.loads((REPO / "fixtures" / "zeus" / "radicados.json").read_text(encoding="utf-8"))
RELOJ_FIJO = lambda: datetime(2026, 10, 29, 9, 30, 0)  # noqa: E731


def copiar_config(destino, puerto):
    """Copia Configuracion/ a `destino` y apunta las URLs al doble en `puerto`."""
    carpeta = destino / "Configuracion"
    shutil.copytree(REPO / "Configuracion", carpeta)
    ruta = carpeta / "ConfiguracionProceso.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    for clave in ("UrlBase", "UrlToken", "UrlComentario"):
        datos["ZeusApi"]["Fixture"][clave] = datos["ZeusApi"]["Fixture"][clave].replace("8765", str(puerto))
    datos["ZeusApi"]["BackoffSegundos"] = [0]
    ruta.write_text(json.dumps(datos), encoding="utf-8")


class PruebaConDoble(unittest.TestCase):
    """Levanta el doble y una raíz temporal por prueba."""

    radicados = None

    def setUp(self):
        self.doble = DobleZeus((CLIENTE, SECRETO), list(self.radicados or RADICADOS)).iniciar()
        self.addCleanup(self.doble.detener)
        self.tmp = Path(tempfile.mkdtemp(prefix="lab_hd_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        copiar_config(self.tmp, self.doble.puerto)
        self.cfg = cargar(self.tmp)
        self.registro = Registro(self.cfg, RELOJ_FIJO)
        self.cliente = ClienteZeus(self.cfg, self.registro, ENTORNO, dormir=lambda s: None)

    def configurar_doble(self, **cambios):
        with self.doble.estado.bloqueo:
            self.doble.estado.configurar(cambios)

    def texto_log(self, ruta):
        return ruta.read_text(encoding="utf-8")
