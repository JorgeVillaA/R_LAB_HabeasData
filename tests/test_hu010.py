"""HU-010 — Buscar duplicados de exclusión (un test por escenario de la HU)."""
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tests.soporte import REPO
from habeasdata import ep003, repositorio as r


def caso(identificacion="1000000001", correos=(), celulares=(), fijos=()):
    return {"radicado_hijo": "900001", "radicado_padre": None, "nombre": "NOMBRE SINTETICO", "numero_identificacion": identificacion,
            "tipo_identificacion": "CEDULA DE CIUDADANIA", "fecha_recepcion": "21/08/2026", "correos": list(correos),
            "telefonos": [{"valor": v, "clase": "celular"} for v in celulares] + [{"valor": v, "clase": "fijo"} for v in fijos]}


class PruebaConRepositorio(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="repo_hd_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = r.Repositorio(self.tmp / "lab.sqlite", reintentos=3, dormir=lambda s: None, reloj=lambda: datetime(2026, 11, 1, 9, 0, 0))
        self.addCleanup(self.repo.cerrar)
        ep003.sembrar_desde_fixtures(self.repo)


class TestHU010(PruebaConRepositorio):
    def test_happy_path_sin_duplicado_continua_a_identidad(self):  # AC: sin duplicado
        resultado = ep003.buscar_duplicados(caso(correos=["maria.lopez@ejemplo.invalid"], celulares=["3101234567"]), self.repo)
        self.assertEqual(resultado["duplicados"], [])
        self.assertTrue(resultado["continua"])
        self.assertEqual(len(resultado["restantes"]), 2)

    def test_error_excepcion_4_por_celular_duplicado(self):  # AC: identificación + celular ya excluidos
        resultado = ep003.buscar_duplicados(caso("1000000004", celulares=["3209876543"]), self.repo)
        self.assertEqual([(v["canal"], v["duplicado"]) for v in resultado["valores"]], [("celular", True)])
        self.assertFalse(resultado["continua"])  # su único valor ya está excluido
        self.assertIn("Excepción de negocio 4", ep003.comentario_excepcion_4(resultado))

    def test_error_excepcion_4_por_correo_duplicado(self):
        resultado = ep003.buscar_duplicados(caso("1000000007", correos=["sofia.b@ejemplo.invalid"]), self.repo)
        self.assertEqual(len(resultado["duplicados"]), 1)
        self.assertEqual(ep003.motivo_excepcion_4(resultado), "excepción de negocio 4: todos los valores ya excluidos (correo)")

    def test_reborde_varios_valores_solo_el_duplicado_genera_la_excepcion(self):  # AC: exclusión parcial
        resultado = ep003.buscar_duplicados(
            caso("1000000007", correos=["sofia.a@ejemplo.invalid", "sofia.b@ejemplo.invalid"],
                 celulares=["3101234567", "3209876543"], fijos=["4441234"]), self.repo)
        self.assertEqual(sorted(v["valor"] for v in resultado["duplicados"]), ["3209876543", "sofia.b@ejemplo.invalid"])
        self.assertEqual(sorted(v["valor"] for v in resultado["restantes"]), ["3101234567", "sofia.a@ejemplo.invalid"])
        self.assertTrue(resultado["continua"])  # los demás valores continúan al siguiente paso

    def test_la_llave_es_compuesta_la_misma_identificacion_con_otro_valor_no_es_duplicado(self):
        resultado = ep003.buscar_duplicados(caso("1000000004", celulares=["3000000000"]), self.repo)
        self.assertEqual(resultado["duplicados"], [])

    def test_el_telefono_fijo_no_se_consulta(self):  # no hay base de cruce para el fijo
        resultado = ep003.buscar_duplicados(caso(fijos=["4441234"]), self.repo)
        self.assertEqual(resultado["valores"], [])
        self.assertTrue(resultado["continua"])
        self.assertNotIn("buscar_exclusion_celular", self.repo.intentos)

    def test_paso_1_consulta_la_maestra_de_cada_valor(self):
        resultado = ep003.buscar_duplicados(caso(correos=["maria.lopez@ejemplo.invalid"], celulares=["3101234567"]), self.repo)
        self.assertEqual([v["en_maestra"] for v in resultado["valores"]], [True, True])
        desconocido = ep003.buscar_duplicados(caso("1000000009", correos=["anonimo@ejemplo.invalid"]), self.repo)
        self.assertEqual([v["en_maestra"] for v in desconocido["valores"]], [False])

    def test_error_repositorio_que_no_responde_reintenta_3_veces_y_lanza_error(self):  # AC: excepción de sistema del caso
        self.repo.fallas["buscar_exclusion_correo"] = None
        with self.assertRaises(r.ErrorRepositorio):
            ep003.buscar_duplicados(caso(correos=["maria.lopez@ejemplo.invalid"]), self.repo)
        self.assertEqual(self.repo.intentos["buscar_exclusion_correo"], 3)

    def test_la_nota_de_duplicado_no_lleva_valores_de_contacto(self):  # cero PII en el comentario
        resultado = ep003.buscar_duplicados(caso("1000000004", celulares=["3209876543"]), self.repo)
        self.assertNotIn("3209876543", ep003.comentario_excepcion_4(resultado))


if __name__ == "__main__":
    unittest.main()
