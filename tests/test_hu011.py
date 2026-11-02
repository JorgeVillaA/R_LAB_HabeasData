"""HU-011 — Registrar la exclusión en base centralizada (un test por escenario de la HU, incluida la tabla de fallas)."""
import unittest

from tests.test_hu010 import PruebaConRepositorio, caso
from habeasdata import ep003, repositorio as r

COBRA = {"ID CLIENTE": "CLI-1", "ID CODEUDOR": "COD-1", "TIPO USUARIO": "TITULAR", "FUENTE": "FUENTE-SINTETICA-A",
         "GESTOR": "GESTOR-1", "SUCURSAL": "SUC-1"}


def valores(*pares):
    return [{"canal": c, "valor": v} for c, v in pares]


class TestHU011(PruebaConRepositorio):
    def registrar(self, caso_, *pares, cobra=COBRA):
        return ep003.registrar_exclusion(caso_, valores(*pares), self.repo, cobra, "01/11/2026")

    def test_happy_path_fila_en_exclusion_y_en_el_canal_con_las_14_columnas(self):  # AC: fila insertada
        c = caso(correos=["maria.lopez@ejemplo.invalid"], celulares=["3101234567"])
        res = self.registrar(c, ("celular", "3101234567"), ("correo", "maria.lopez@ejemplo.invalid"))
        self.assertTrue(res["exclusion"])
        self.assertIsNone(res["error"])
        self.assertEqual(self.repo.contar("Exclusion"), 1)
        fila = dict(self.repo.con.execute('SELECT * FROM Celulares WHERE IDENTIFICACION = ? AND ZEUS = ?', ("1000000001", "900001")).fetchone())
        for columna in r.COLUMNAS_CELULARES:
            self.assertIn(columna, fila)
        self.assertEqual((fila["ID CLIENTE"], fila["ID CODEUDOR"], fila["GESTOR"], fila["SUCURSAL"]), ("CLI-1", "COD-1", "GESTOR-1", "SUC-1"))
        self.assertEqual((fila["CELULAR"], fila["ZEUS"], fila["FECHA CONSULTA"], fila["FECHA EXCLUSION"]), ("3101234567", "900001", "21/08/2026", "01/11/2026"))
        self.assertEqual(fila["NOMBRE"], "NOMBRE SINTETICO")  # tal cual lo extrajo HU-003

    def test_zeus_guarda_el_radicado_hijo_y_no_el_padre(self):
        c = dict(caso(correos=["maria.lopez@ejemplo.invalid"]), radicado_hijo="900008", radicado_padre="800001")
        self.registrar(c, ("correo", "maria.lopez@ejemplo.invalid"))
        fila = self.repo.con.execute("SELECT Zeus FROM Correos WHERE IDENTIFICACION = '1000000001'").fetchone()
        self.assertEqual(fila[0], "900008")

    def test_contacto_verificado_contra_las_maestras_y_la_maestra_no_se_altera_al_cruzar(self):  # AC: verificado (cruzado)
        antes = self.repo.contar("MaestraCelulares")
        res = self.registrar(caso(celulares=["3101234567"]), ("celular", "3101234567"))
        self.assertEqual(res["verificados"], ["celular:3101234567"])
        self.assertEqual(self.repo.contar("MaestraCelulares"), antes - 1)  # solo la eliminación posterior, no el cruce

    def test_eliminacion_del_registro_en_la_maestra_tras_confirmar_la_insercion(self):  # AC: eliminación
        self.assertTrue(self.repo.existe_en_maestra("correo", "1000000001", "maria.lopez@ejemplo.invalid"))
        res = self.registrar(caso(correos=["maria.lopez@ejemplo.invalid"]), ("correo", "maria.lopez@ejemplo.invalid"))
        self.assertEqual(res["eliminados"], ["correo:maria.lopez@ejemplo.invalid"])
        self.assertFalse(self.repo.existe_en_maestra("correo", "1000000001", "maria.lopez@ejemplo.invalid"))

    def test_reborde_varios_valores_una_fila_por_valor_y_eliminacion_por_cada_uno(self):  # AC: una fila por valor
        c = caso("1000000007", correos=["sofia.a@ejemplo.invalid"], celulares=["3101234567"])
        otro = caso("1000000050", correos=["uno@ejemplo.invalid", "dos@ejemplo.invalid"], celulares=["3001112233", "3001112244"])
        res = self.registrar(c, ("correo", "sofia.a@ejemplo.invalid"), ("celular", "3101234567"))
        self.assertEqual(len(res["eliminados"]), 2)  # ambos estaban en las maestras
        res = self.registrar(otro, ("correo", "uno@ejemplo.invalid"), ("correo", "dos@ejemplo.invalid"),
                             ("celular", "3001112233"), ("celular", "3001112244"))
        self.assertEqual(len(res["insertados"]), 4)
        self.assertEqual(res["eliminados"], [])  # datos no ubicados en la maestra: nada que eliminar
        cuenta = lambda tabla: self.repo.con.execute(f"SELECT COUNT(*) FROM {tabla} WHERE IDENTIFICACION = '1000000050'").fetchone()[0]  # noqa: E731
        self.assertEqual((cuenta("Correos"), cuenta("Celulares")), (2, 2))  # una fila independiente por valor

    def test_reborde_contacto_ya_presente_se_marca_y_no_se_duplica(self):  # AC: contacto ya presente
        antes = self.repo.contar("Celulares")
        res = self.registrar(caso("1000000004", celulares=["3209876543"]), ("celular", "3209876543"))  # ya está en Celulares (exclusión previa)
        self.assertEqual(res["ya_presentes"], ["celular:3209876543"])
        self.assertEqual(self.repo.contar("Celulares"), antes)

    def test_error_insercion_persistente_no_elimina_nada_de_la_maestra(self):  # AC: tabla de fallas, insertar
        self.repo.fallas["insertar_celular"] = None
        antes = self.repo.contar("MaestraCelulares")
        res = self.registrar(caso(celulares=["3101234567"]), ("celular", "3101234567"))
        self.assertEqual(res["operacion"], "insertar")
        self.assertIn("3 intentos", res["error"])
        self.assertEqual(self.repo.contar("MaestraCelulares"), antes)
        self.assertEqual(self.repo.intentos["insertar_celular"], 3)

    def test_error_eliminacion_persistente_conserva_la_fila_ya_insertada(self):  # AC: tabla de fallas, eliminar
        self.repo.fallas["eliminar_maestra_correo"] = None
        res = self.registrar(caso(correos=["maria.lopez@ejemplo.invalid"]), ("correo", "maria.lopez@ejemplo.invalid"))
        self.assertEqual(res["operacion"], "eliminar")
        self.assertEqual(self.repo.contar("Correos"), 2)  # la preexistente de 900007 + la insertada, que se conserva
        self.assertTrue(self.repo.existe_exclusion("correo", "1000000001", "maria.lopez@ejemplo.invalid"))

    def test_canal_fijo_sin_valores_deja_solo_la_fila_de_exclusion(self):  # HU-011 §4: el fijo se registra en la base de exclusión
        res = ep003.registrar_exclusion(caso(fijos=["4441234"]), [], self.repo, COBRA, "01/11/2026")
        self.assertTrue(res["exclusion"])
        self.assertIsNone(res["error"])
        self.assertEqual((self.repo.contar("Exclusion"), self.repo.contar("Celulares"), self.repo.contar("Correos")), (1, 2, 1))

    def test_error_insertar_la_fila_de_exclusion_no_toca_canales_ni_maestras(self):  # AC: tabla de fallas, insertar
        self.repo.fallas["insertar_exclusion"] = None
        c = caso(correos=["maria.lopez@ejemplo.invalid"], celulares=["3101234567"])
        res = self.registrar(c, ("correo", "maria.lopez@ejemplo.invalid"), ("celular", "3101234567"))
        self.assertEqual((res["operacion"], res["exclusion"]), ("insertar", False))
        self.assertEqual((self.repo.contar("Celulares"), self.repo.contar("Correos")), (2, 1))
        self.assertEqual((self.repo.contar("MaestraCelulares"), self.repo.contar("MaestraCorreos")), (6, 9))

    def test_error_insertar_un_valor_no_elimina_nada_de_ninguna_maestra_ni_de_los_valores_ya_insertados(self):  # AC literal
        self.repo.fallas["insertar_celular"] = None
        c = caso(correos=["maria.lopez@ejemplo.invalid"], celulares=["3101234567"])
        res = self.registrar(c, ("correo", "maria.lopez@ejemplo.invalid"), ("celular", "3101234567"))
        self.assertEqual(res["operacion"], "insertar")
        self.assertEqual((self.repo.contar("MaestraCelulares"), self.repo.contar("MaestraCorreos")), (6, 9))  # nada se elimina
        self.assertEqual(res["eliminados"], [])

    def test_error_al_cruzar_con_la_maestra_se_reporta_como_cruzar_no_como_eliminar(self):
        self.repo.fallas["buscar_maestra_correo"] = None
        res = self.registrar(caso(correos=["maria.lopez@ejemplo.invalid"]), ("correo", "maria.lopez@ejemplo.invalid"))
        self.assertEqual(res["operacion"], "cruzar")
        self.assertTrue(self.repo.existe_exclusion("correo", "1000000001", "maria.lopez@ejemplo.invalid"))  # lo insertado se conserva

    def test_los_datos_de_cobra_salen_del_stub_con_valores_por_defecto(self):
        stub = ep003.cargar_stub()
        self.assertEqual(ep003.datos_cobra(stub, "900001")["GESTOR"], "GESTOR-SINTETICO-1")
        self.assertEqual(ep003.datos_cobra(stub, "900008")["TIPO USUARIO"], "CODEUDOR")


if __name__ == "__main__":
    unittest.main()
