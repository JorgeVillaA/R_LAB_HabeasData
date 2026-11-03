"""HU-008: comparar nombres (umbral 0.80, sin depender del orden). Un test por escenario Given/When/Then."""
import unittest

from tests import soporte  # noqa: F401  (rutas del repo)
from habeasdata import nombres

U = 0.80


class TestHU008(unittest.TestCase):
    def test_happy_primer_nombre_y_primer_apellido_aunque_falte_el_segundo(self):
        v = nombres.comparar("Juan Pérez", "Juan Pérez Gómez", U)
        self.assertEqual((v["coincide"], v["puntaje"]), (True, 1.0))

    def test_error_excepcion_de_negocio_3(self):
        v = nombres.comparar("Juan Pérez Gómez", "Carlos Ramírez Díaz", U)
        self.assertFalse(v["coincide"])
        self.assertLess(v["puntaje"], U)

    def test_reborde_nombre_incompleto_sin_apellido_va_a_excepcion_3_cualquiera_sea_el_puntaje(self):
        v = nombres.comparar("Juan", "Juan", U)
        self.assertEqual((v["coincide"], v["puntaje"]), (False, 1.0))
        self.assertEqual(nombres.comparar("Juan Pérez", "Juan", U)["motivo"], "nombre del portal incompleto")

    def test_reborde_orden_distinto_entre_fuentes(self):
        self.assertTrue(nombres.comparar("Juan Pérez Gómez", "PEREZ GOMEZ JUAN", U)["coincide"])
        self.assertTrue(nombres.comparar("Pérez Gómez Juan", "Juan Pérez Gómez", U)["coincide"])

    def test_normalizacion_tildes_mayusculas_espacios_y_particulas(self):
        self.assertEqual(nombres.normalizar("  maría  de los Ángeles  "), ["MARIA", "ANGELES"])
        self.assertTrue(nombres.comparar("MARÍA DE LOS ÁNGELES RUIZ", "maria angeles ruiz", U)["coincide"])

    def test_umbral_es_inclusivo_en_080(self):
        # 4 componentes cada uno, 4 comunes de 5 no aplica; 3 de 4 comunes → 0.75 por debajo; 4 de 5 → 0.8 coincide
        self.assertEqual(nombres.puntaje("A B C D E", "A B C D F"), 0.8)
        self.assertTrue(nombres.comparar("Ana Beto Cesar Dora Eva", "Ana Beto Cesar Dora Fabio", 0.80)["coincide"])
        self.assertFalse(nombres.comparar("Ana Beto Cesar Dora Eva", "Ana Beto Cesar Dora Fabio", 0.81)["coincide"])

    def test_umbral_parametrizable_cambia_el_resultado_sin_cambiar_la_logica(self):
        par = ("Maria Fernanda Lopez Ruiz", "Maria Lopez Ruiz Torres")
        self.assertEqual(nombres.puntaje(*par), 0.75)
        self.assertFalse(nombres.comparar(*par, 0.80)["coincide"])
        self.assertTrue(nombres.comparar(*par, 0.70)["coincide"])

    def test_vacios_nunca_coinciden(self):
        for a, b in (("", "Juan Pérez"), ("Juan Pérez", None), ("   ", "   ")):
            self.assertFalse(nombres.comparar(a, b, U)["coincide"])


if __name__ == "__main__":
    unittest.main()
