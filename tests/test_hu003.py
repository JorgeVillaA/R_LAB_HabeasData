"""HU-003 — Leer datos paramétricos del radicado (un test por escenario de la HU)."""
import unittest

from tests.soporte import PruebaConDoble, REPO, RADICADOS
from habeasdata import ep001
from habeasdata.config import cargar


class TestReglasPuras(unittest.TestCase):
    cfg = cargar(REPO)

    def test_ausente_vacio_blanco_y_no_aporta_sin_distinguir_mayusculas(self):
        for valor in (None, "", "   ", "No aporta", "NO APORTA", "no aporta"):
            self.assertTrue(ep001.es_ausente(valor, self.cfg), repr(valor))
        self.assertFalse(ep001.es_ausente("No aplica", self.cfg))  # no es otro literal de ausencia

    def test_clasificacion_de_telefono_por_digitos(self):  # tabla de la HU
        casos = {"3101234567": "celular", "4441234": "fijo", "2101234567": "sin_clasificar",
                 "310123456": "sin_clasificar", "31012345678": "sin_clasificar", "3101234AB7": "sin_clasificar"}
        for valor, clase in casos.items():
            self.assertEqual(ep001.clasificar_telefono(valor, self.cfg), clase, valor)

    def test_separar_por_barra_sin_espacios(self):
        self.assertEqual(ep001.separar_valores("a@x.invalid/b@x.invalid", self.cfg), ["a@x.invalid", "b@x.invalid"])
        self.assertEqual(ep001.separar_valores("3101234567", self.cfg), ["3101234567"])
        self.assertEqual(ep001.separar_valores("No aporta", self.cfg), [])
        self.assertEqual(ep001.separar_valores("3101234567//3209876543/", self.cfg), ["3101234567", "3209876543"])


class TestHU003(PruebaConDoble):
    def leer(self, id_radicado):
        return ep001.extraer(self.cliente, self.cfg, id_radicado)

    def test_happy_path_extraccion_completa(self):
        caso = self.leer("900001")
        self.assertEqual(caso["nombre"], "MARIA FERNANDA LOPEZ RUIZ")
        self.assertEqual(caso["tipo_identificacion"], "CEDULA DE CIUDADANIA")
        self.assertEqual(caso["numero_identificacion"], "1000000001")
        self.assertEqual(caso["fecha_recepcion"], "21/08/2026")
        self.assertEqual(caso["correos"], ["maria.lopez@ejemplo.invalid"])
        self.assertEqual(caso["telefonos"], [{"valor": "3101234567", "clase": "celular"}])
        self.assertTrue(caso["canal_correo"] and caso["canal_telefono"])

    def test_error_formulario_no_carga_es_excepcion_de_sistema_del_caso(self):
        self.configurar_doble(fallas_radicado={"900001": 400})
        with self.assertRaises(ep001.ExcepcionSistemaCaso):
            self.leer("900001")

    def test_error_formulario_no_carga_continua_con_el_siguiente(self):
        self.configurar_doble(fallas_radicado={"900001": 400})
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertIn("900001", resumen["excepciones_sistema"])
        self.assertIn("900003", resumen["avanzan"])  # el siguiente sigue procesándose

    def test_reborde_canal_parcial_solo_correo(self):
        caso = self.leer("900003")
        self.assertTrue(caso["canal_correo"])
        self.assertFalse(caso["canal_telefono"])
        self.assertEqual(caso["telefonos"], [])

    def test_reborde_canal_parcial_solo_telefono(self):
        caso = self.leer("900004")
        self.assertFalse(caso["canal_correo"])
        self.assertEqual(caso["correos"], [])
        self.assertEqual(caso["telefonos"][0]["clase"], "celular")

    def test_reborde_clasificacion_del_telefono(self):
        self.assertEqual(self.leer("900001")["telefonos"][0]["clase"], "celular")
        self.assertEqual(self.leer("900005")["telefonos"], [{"valor": "4441234", "clase": "fijo"}])
        self.assertEqual(self.leer("900006")["telefonos"], [{"valor": "2101234567", "clase": "sin_clasificar"}])

    def test_reborde_varios_valores_en_un_canal(self):
        caso = self.leer("900007")
        self.assertEqual(caso["correos"], ["sofia.a@ejemplo.invalid", "sofia.b@ejemplo.invalid"])
        self.assertEqual([t["clase"] for t in caso["telefonos"]], ["celular", "celular", "fijo"])

    def test_reborde_radicado_con_padre(self):
        caso = self.leer("900008")
        self.assertEqual((caso["radicado_hijo"], caso["radicado_padre"]), ("900008", "800001"))
        self.assertEqual(caso["radicado_para_plantillas"], "800001")

    def test_reborde_radicado_sin_padre_usa_el_propio(self):
        caso = self.leer("900001")
        self.assertIsNone(caso["radicado_padre"])
        self.assertEqual(caso["radicado_para_plantillas"], "900001")

    def test_campos_heredados_y_observaciones_no_se_leen(self):
        caso = self.leer("900015")
        self.assertEqual((caso["correos"], caso["telefonos"]), ([], []))
        self.assertFalse(caso["canal_correo"] or caso["canal_telefono"])

    def test_nombre_se_extrae_tal_cual_sin_normalizar(self):
        self.assertEqual(self.leer("900014")["nombre"], "TORRES GALINDO NATALIA")
        self.assertEqual(self.leer("900013")["nombre"], "INVERSIONES LAB DEMO S A S")

    def test_no_aporta_en_canal_y_dato_presente_en_el_otro(self):
        caso = self.leer("900016")
        self.assertEqual(caso["correos"], [])
        self.assertEqual(caso["telefonos"][0]["valor"], "3174445566")

    def test_radicado_inexistente_es_excepcion_de_sistema_del_caso(self):
        with self.assertRaises(ep001.ExcepcionSistemaCaso):
            self.leer("1")

    def test_todos_los_fixtures_tienen_borde_cubierto(self):
        self.assertEqual(len(RADICADOS), 16)
