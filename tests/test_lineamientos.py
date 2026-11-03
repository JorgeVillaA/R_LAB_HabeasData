"""Test estructural de lineamientos Trycore (lo que validate_robot no ve): carpetas, JSON, logs, rutas, credenciales.

Anexo «Estructura de carpetas y manejo de logs» V1.0 (R-01..R-12) y lineamientos §13-14, §18, §22-23.
"""
import json
import re
import unittest
from pathlib import Path

from tests.soporte import PruebaConDoble, REPO
from habeasdata import ep001
from habeasdata.config import DICCIONARIOS_MAQUINA, NOMBRES, cargar
from habeasdata.registro import CAMPOS

CODIGO = [p for carpeta in ("Scripts", "dobles", "banco") for p in (REPO / carpeta).rglob("*.py")]
RUTA_ABSOLUTA = re.compile(r"""["'](?:[A-Za-z]:[\\/]|/(?:Users|home|tmp|var|opt|mnt)/)""")
COMANDOS_PROHIBIDOS = re.compile(r"pyautogui|locateOnScreen|imagesearch|mouse_event|click\(|SetCursorPos|ImageGrab", re.I)
SECRETO_EN_VALOR = re.compile(r'"(?!Url)(?:[^"]*(?:secret|password|passwd|token|apikey)[^"]*)"\s*:\s*"([^"]+)"', re.I)


class TestLineamientos(unittest.TestCase):
    def test_tres_json_de_configuracion_con_maximo_cuatro_diccionarios(self):  # §13-14, §18
        for nombre in NOMBRES:
            self.assertTrue((REPO / "Configuracion" / f"{nombre}.json").is_file(), nombre)
        maquina = json.loads((REPO / "Configuracion" / "ConfiguracionMaquina.json").read_text(encoding="utf-8"))
        self.assertLessEqual(len(maquina), 4)
        self.assertEqual(tuple(maquina), DICCIONARIOS_MAQUINA)

    def test_nada_parametrico_en_la_logica(self):  # umbrales y textos de negocio viven en la configuración
        logica = (REPO / "Scripts" / "habeasdata" / "ep001.py").read_text(encoding="utf-8")
        for literal in ('"No aporta"', "'No aporta'", '"EXCLUSION DE DATOS"', "0.80", '"3"', "10:"):
            self.assertNotIn(literal, logica, literal)

    def test_ninguna_ruta_absoluta_en_la_logica(self):  # R-01
        for codigo in CODIGO:
            for numero, linea in enumerate(codigo.read_text(encoding="utf-8").splitlines(), 1):
                self.assertIsNone(RUTA_ABSOLUTA.search(linea), f"{codigo.name}:{numero} {linea.strip()}")

    def test_la_raiz_es_una_llave_de_configuracion(self):
        maquina = json.loads((REPO / "Configuracion" / "ConfiguracionMaquina.json").read_text(encoding="utf-8"))
        self.assertIn("RutaRaiz", maquina["RutasVentanas"]["RutasProceso"])

    def test_sin_comandos_de_mouse_ni_reconocimiento_de_imagenes(self):
        for codigo in CODIGO:
            if codigo.name == "test_lineamientos.py":
                continue
            self.assertIsNone(COMANDOS_PROHIBIDOS.search(codigo.read_text(encoding="utf-8")), codigo.name)

    def test_cero_credenciales_en_json_y_fixtures(self):  # R-04
        archivos = list((REPO / "Configuracion").glob("*.json")) + list((REPO / "fixtures").rglob("*.json"))
        for archivo in archivos:
            for valor in SECRETO_EN_VALOR.findall(archivo.read_text(encoding="utf-8")):
                # Los únicos valores admitidos son NOMBRES de variables de entorno, nunca el secreto.
                self.assertRegex(valor, r"^[A-Z0-9_]+$", f"{archivo.name}: posible credencial literal")
            self.assertNotRegex(archivo.read_text(encoding="utf-8"), r"eyJ[A-Za-z0-9_-]{10,}", archivo.name)

    def test_versionado_y_navegador(self):  # §22-23 y navegador Chrome
        globales = json.loads((REPO / "Configuracion" / "ConfiguracionMaquina.json").read_text(encoding="utf-8"))["Globales"]
        self.assertEqual(globales["Version"], "V1.0.0")
        self.assertEqual(globales["Navegador"], "chrome")
        self.assertEqual(globales["Proyecto"], "R_LAB_HabeasData")

    def test_nada_suelto_en_la_raiz(self):  # R-03: ni logs, ni csv, ni json sueltos
        sueltos = [p.name for p in REPO.iterdir() if p.is_file() and p.suffix.lower() in (".log", ".csv", ".json", ".tmp")]
        self.assertEqual(sueltos, [])

    def test_gitignore_acumulables_y_versiona_configuracion(self):
        ignorado = (REPO / ".gitignore").read_text(encoding="utf-8")
        for acumulable in ("Logs/", "CapturasPantalla/", "Archivos Temporales/", "Reportes/"):
            self.assertIn(acumulable, ignorado, acumulable)
        for versionable in ("Configuracion/", "Scripts/", "Documentos/"):
            self.assertNotRegex(ignorado, rf"(?m)^/?{re.escape(versionable)}\s*$")


class TestLogsDeUnaCorrida(PruebaConDoble):
    """Corre el robot completo y revisa los archivos que deja (R-05..R-12)."""

    def setUp(self):
        super().setUp()
        self.resumen = ep001.procesar(self.cfg, self.cliente, self.registro)

    def lineas(self, ruta):
        return ruta.read_text(encoding="utf-8").splitlines()

    def test_dos_archivos_de_log_de_un_dia_y_reporte(self):  # R-05, R-06
        self.assertTrue(self.registro.ruta_auditoria().is_file())
        self.assertTrue(self.registro.ruta_errores().is_file())
        self.assertTrue(self.registro.ruta_reporte().is_file())
        self.assertRegex(self.registro.ruta_auditoria().name, r"^\w{14}_LOG_DE_AUDITORIA_\d{8}\.csv$")
        self.assertRegex(self.registro.ruta_errores().name, r"^\w{14}_LOG_DE_ERRORES_\d{8}\.csv$")

    def test_cuatro_campos_fijos_en_orden_nunca_vacios(self):  # R-07, R-10
        for ruta in (self.registro.ruta_auditoria(), self.registro.ruta_errores()):
            lineas = self.lineas(ruta)
            self.assertEqual(lineas[0], ";".join(CAMPOS))
            for linea in lineas[1:]:
                campos = linea.split(";")
                self.assertEqual(len(campos), 4, linea)
                self.assertTrue(all(c.strip() for c in campos), linea)

    def test_eventos_minimos_de_auditoria(self):  # R-08
        auditoria = "\n".join(self.lineas(self.registro.ruta_auditoria()))
        for evento in ("Inicio de ejecución", "Ingreso a la API de Zeus", "Inicio del radicado", "Fin del radicado",
                       "Fin de ejecución"):
            self.assertIn(evento, auditoria)

    def test_el_reintento_queda_en_el_log(self):
        self.doble.detener()
        self.registro.auditoria("marca")
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertEqual(resumen["estado"], "detenido")
        self.assertIn("Reintento 1/3", "\n".join(self.lineas(self.registro.ruta_auditoria())))

    def test_sin_secretos_ni_tokens_ni_pii_en_los_logs(self):  # R-11
        texto = "\n".join(self.lineas(self.registro.ruta_auditoria()) + self.lineas(self.registro.ruta_errores())
                          + self.lineas(self.registro.ruta_reporte()))
        self.assertNotIn("secreto-de-prueba", texto)
        self.assertNotRegex(texto, r"[0-9a-f]{32}")  # tokens del doble
        for dato in ("1000000001", "maria.lopez", "MARIA FERNANDA"):
            self.assertNotIn(dato, texto, "PII sintética en logs")

    def test_el_bot_crea_las_carpetas_fechadas(self):  # R-02
        for relativa in ("Logs/Sistema/2026/10", "Logs/Auditoria/2026/10", "Reportes/2026/10",
                         "CapturasPantalla/Proceso/2026/10", "CapturasPantalla/Error/2026/10"):
            self.assertTrue((self.cfg.raiz / relativa).is_dir(), relativa)
