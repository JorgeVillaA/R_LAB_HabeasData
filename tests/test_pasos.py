"""Pasos del robot (habeasdata.pasos): cada uno es un bloque de Studio. Se encadenan como lo hace el robot."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.soporte import CLIENTE, SECRETO, RADICADOS, copiar_config
from dobles.zeus_api.servidor import DobleZeus
from habeasdata import pasos


class PruebaPasos(unittest.TestCase):
    def setUp(self):
        self.doble = DobleZeus((CLIENTE, SECRETO), list(RADICADOS)).iniciar()
        self.addCleanup(self.doble.detener)
        self.raiz = Path(tempfile.mkdtemp(prefix="lab_pasos_"))
        self.addCleanup(shutil.rmtree, self.raiz, ignore_errors=True)
        copiar_config(self.raiz, self.doble.puerto)
        entorno = mock.patch.dict(os.environ, {"ZEUS_DOBLE_CLIENT_ID": CLIENTE, "ZEUS_DOBLE_CLIENT_SECRET": SECRETO})
        entorno.start()
        self.addCleanup(entorno.stop)
        self.inicio = pasos.iniciar(str(self.raiz))


class TestPasos(PruebaPasos):
    def test_iniciar_crea_la_estructura_y_declara_el_modo(self):
        self.assertEqual((self.inicio["ok"], self.inicio["modo"]), (True, "fixture"))
        self.assertTrue((self.raiz / "Logs" / "Auditoria").is_dir())

    def test_parametros_salen_de_la_configuracion(self):
        parametros = pasos.parametros()
        self.assertEqual(parametros["negocio"]["TipologiaExclusion"], "EXCLUSION DE DATOS")
        self.assertEqual(parametros["seleccion"]["Orden"], "IDRADICADO desc")

    def test_token_y_consulta_odata(self):
        self.assertTrue(pasos.solicitar_token()["ok"])
        resultado = pasos.consultar_odata("PQRCORRESPONDEA eq 'EXCLUSION DE DATOS'", "IDRADICADO", "3", "IDRADICADO desc")
        self.assertEqual(resultado["ids"], ["900016", "900015", "900014"])

    def test_token_rechazado_detiene(self):
        with mock.patch.dict(os.environ, {"ZEUS_DOBLE_CLIENT_SECRET": "otro"}):
            pasos.iniciar(str(self.raiz))
            resultado = pasos.solicitar_token()
        self.assertEqual((resultado["ok"], resultado["detenido"]), (False, True))

    def test_consulta_con_campo_inexistente_detiene_con_el_motivo(self):
        pasos.solicitar_token()
        resultado = pasos.consultar_odata("NOEXISTE eq 'x'")
        self.assertFalse(resultado["ok"])
        self.assertIn("no reconocido", resultado["mensaje"])

    def test_consulta_con_fila_sin_idradicado_detiene_en_el_paso_del_robot(self):
        pasos.solicitar_token()
        with mock.patch.object(pasos._sesion.cliente, "consultar", return_value=[{"PQRCORRESPONDEA": "OTRA"}]):
            resultado = pasos.consultar_odata("")
        self.assertEqual((resultado["ok"], resultado["detenido"]), (False, True))

    def test_la_detencion_deja_el_motivo_en_el_log_de_errores_y_en_el_aviso(self):
        resultado = pasos.registrar_detencion("motivo-de-prueba-xyz")
        self.assertEqual(resultado["notificacion"]["motivo"], "motivo-de-prueba-xyz")
        texto = "".join(p.read_text(encoding="utf-8") for p in (self.raiz / "Logs" / "Sistema").rglob("*ERRORES*.csv"))
        self.assertIn("motivo-de-prueba-xyz", texto)

    def test_leer_preparar_y_clasificar_como_los_bloques_del_robot(self):
        pasos.solicitar_token()
        lectura = pasos.leer_radicado("900007")
        preparado = pasos.preparar_campos(str(lectura))  # el robot entrega el texto de la variable
        self.assertEqual(preparado["telefonos_valores"], ["3101234567", "3209876543", "4441234"])
        caso = pasos.clasificar_telefonos(str(preparado))
        self.assertEqual([t["clase"] for t in caso["telefonos"]], ["celular", "celular", "fijo"])
        self.assertTrue(caso["canal_correo"] and caso["canal_telefono"])

    def test_radicado_inexistente_devuelve_fallo_sin_excepcion(self):
        pasos.solicitar_token()
        lectura = pasos.leer_radicado("1")
        self.assertFalse(lectura["ok"])
        self.assertIn("no se pudo leer el radicado 1", lectura["mensaje"])

    def test_comentario_de_excepcion_1_llega_al_doble(self):
        pasos.solicitar_token()
        caso = pasos.clasificar_telefonos(pasos.preparar_campos(pasos.leer_radicado("900002")))
        self.assertTrue(pasos.comentar_excepcion_1(str(caso), "['SIN CANAL DE CONTACTO']")["ok"])
        self.assertEqual(self.doble.estado.comentarios[0]["IDRADICADO"], "900002")

    def test_cierre_devuelve_resumen_y_deja_fin_en_el_log(self):
        resumen = {"estado": "ok", "avanzan": ["1"], "casos": {}}
        self.assertTrue(pasos.cerrar(str(resumen))["ok"])
        auditoria = "".join(p.read_text(encoding="utf-8") for p in (self.raiz / "Logs").rglob("*LOG_DE_AUDITORIA*.csv"))
        self.assertIn("Fin de ejecución EP-001", auditoria)

    def test_objeto_interpreta_el_texto_de_una_variable_del_robot(self):
        self.assertEqual(pasos.objeto("{'a': None, 'b': [1, 2]}"), {"a": None, "b": [1, 2]})
        self.assertEqual(pasos.objeto("bandeja_vacia"), "bandeja_vacia")
        self.assertEqual(pasos.objeto({"ya": "objeto"}), {"ya": "objeto"})


if __name__ == "__main__":
    unittest.main()
