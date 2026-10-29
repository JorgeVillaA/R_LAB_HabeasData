"""Configuración (tres JSON), estructura de carpetas (R-02) y logs del anexo V1.0 (R-05..R-12)."""
import json
import re
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tests.soporte import REPO, RELOJ_FIJO
from habeasdata.config import DICCIONARIOS_MAQUINA, cargar
from habeasdata.registro import CAMPOS, CAMPOS_REPORTE, FALTANTE, Registro, limpiar


class TestConfiguracion(unittest.TestCase):
    def test_tres_json_y_maximo_cuatro_diccionarios(self):
        cfg = cargar(REPO)
        self.assertLessEqual(len(cfg.maquina), 4)
        self.assertEqual(tuple(cfg.maquina), DICCIONARIOS_MAQUINA)
        self.assertEqual(cfg.maestro["UMBRAL_COINCIDENCIA_NOMBRES"], 0.80)
        self.assertEqual(cfg.maestro["NUMERO_REINTENTOS_SISTEMA"], 3)

    def test_raiz_relativa_se_resuelve_contra_la_carpeta_del_proyecto(self):
        self.assertEqual(cargar(REPO).raiz, REPO.resolve())
        self.assertEqual(cargar(REPO).maquina["RutasVentanas"]["RutasProceso"]["RutaRaiz"], ".")


class TestEstructuraYLogs(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="lab_hd_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        (self.tmp / "Configuracion").mkdir()
        for nombre in ("ConfiguracionMaquina", "ConfiguracionProceso", "Maestro_Configuracion"):
            (self.tmp / "Configuracion" / f"{nombre}.json").write_text(
                (REPO / "Configuracion" / f"{nombre}.json").read_text(encoding="utf-8"), encoding="utf-8")
        self.cfg = cargar(self.tmp)
        self.reg = Registro(self.cfg, RELOJ_FIJO)

    def test_el_bot_crea_la_estructura_al_arrancar(self):
        self.reg.asegurar_archivos()
        for relativa in ("Logs/Sistema/2026/10", "Logs/Auditoria/2026/10", "CapturasPantalla/Proceso/2026/10",
                         "CapturasPantalla/Error/2026/10", "Archivos Temporales", "Documentos", "Scripts",
                         "Reportes/2026/10"):
            self.assertTrue((self.tmp / relativa).is_dir(), relativa)

    def test_dos_logs_por_dia_con_nombre_del_anexo(self):
        self.reg.asegurar_archivos()
        self.assertEqual(self.reg.ruta_auditoria().name, "LAB0001HDATA00_LOG_DE_AUDITORIA_20261029.csv")
        self.assertEqual(self.reg.ruta_errores().name, "LAB0001HDATA00_LOG_DE_ERRORES_20261029.csv")
        self.assertTrue(self.reg.ruta_auditoria().exists() and self.reg.ruta_errores().exists())
        self.assertEqual(self.reg.ruta_reporte().name, "LAB0001HDATA00_INFORMEGESTION_20261029.csv")

    def test_cuatro_campos_en_orden_y_separador(self):
        self.reg.asegurar_archivos()
        self.reg.auditoria("Inicio de ejecución", "Zeus API")
        lineas = self.reg.ruta_auditoria().read_text(encoding="utf-8").splitlines()
        self.assertEqual(lineas[0], ";".join(CAMPOS))
        self.assertEqual(lineas[1], "127.0.0.1;2026-10-29 09:30:00;Zeus API;Inicio de ejecución")

    def test_faltante_es_no_aplica_nunca_vacio(self):
        self.reg.auditoria(None)
        self.reg.auditoria("   ")
        datos = self.reg.ruta_auditoria().read_text(encoding="utf-8").splitlines()[1:]
        self.assertTrue(all(linea.endswith(";" + FALTANTE) for linea in datos))
        self.assertEqual(limpiar(""), FALTANTE)

    def test_observacion_sin_punto_y_coma_ni_secretos(self):
        self.reg.error("falló; Authorization: Bearer abc123 client_secret=xyz\nsegunda línea")
        linea = self.reg.ruta_errores().read_text(encoding="utf-8").splitlines()[1]
        self.assertEqual(linea.count(";"), 3)
        self.assertNotIn("abc123", linea)
        self.assertNotIn("xyz", linea)

    def test_anexa_sin_sobrescribir(self):
        self.reg.auditoria("uno")
        otro = Registro(self.cfg, RELOJ_FIJO)
        otro.auditoria("dos")
        lineas = self.reg.ruta_auditoria().read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lineas), 3)

    def test_reporte_de_gestion_con_encabezado(self):
        self.reg.reporte("900001", "800001", "avanza", None, None)
        lineas = self.reg.ruta_reporte().read_text(encoding="utf-8").splitlines()
        self.assertEqual(lineas[0], ";".join(CAMPOS_REPORTE))
        self.assertIn(";900001;800001;avanza;NO APLICA;NO APLICA", lineas[1])
