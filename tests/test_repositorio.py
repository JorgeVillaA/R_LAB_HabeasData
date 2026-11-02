"""Repositorio local (specs/repositorio-local.md): MER de 8 tablas + Transacciones + maestras, reintentos y consultas de revisión."""
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tests.soporte import REPO  # noqa: F401  (deja el sys.path de Scripts/ listo)
from habeasdata import repositorio as r


def fila_canal(canal, identificacion, valor):
    base = {"ID CLIENTE": "C-1", "ID CODEUDOR": "D-1", "TIPO USUARIO": "TITULAR", "IDENTIFICACION": identificacion,
            "NOMBRE": "NOMBRE SINTETICO", "FUENTE": "FUENTE-A", "FECHA CONSULTA": "21/08/2026", "GESTOR": "G-1", "SUCURSAL": "S-1"}
    base[r.CANALES[canal][3]] = valor
    return base


class PruebaRepositorio(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="repo_hd_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = r.Repositorio(self.tmp / "lab.sqlite", reintentos=3, dormir=lambda s: None, reloj=lambda: datetime(2026, 11, 1, 9, 0, 0))
        self.addCleanup(self.repo.cerrar)


class TestEsquema(PruebaRepositorio):
    def test_el_mer_de_8_tablas_mas_transacciones_y_maestras_existe(self):
        existentes = {f[0] for f in self.repo.con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for tabla in r.TABLAS + ("Transacciones", "MaestraCelulares", "MaestraCorreos"):
            self.assertIn(tabla, existentes)

    def test_celulares_y_correos_tienen_las_14_columnas_y_ninguna_fijo(self):
        for tabla, esperadas in (("Celulares", r.COLUMNAS_CELULARES), ("Correos", r.COLUMNAS_CORREOS),
                                 ("MaestraCelulares", r.COLUMNAS_CELULARES), ("MaestraCorreos", r.COLUMNAS_CORREOS)):
            columnas = [f[1] for f in self.repo.con.execute(f"PRAGMA table_info({tabla})") if f[1] != "Id"]
            self.assertEqual(columnas, list(esperadas), tabla)
            self.assertEqual(len(columnas), 14)
            self.assertNotIn("FIJO", [c.upper() for c in columnas])
        self.assertEqual(r.COLUMNAS_CELULARES[:2], ("ID CLIENTE", "ID CODEUDOR"))

    def test_transacciones_tiene_las_columnas_del_contrato(self):
        columnas = tuple(f[1] for f in self.repo.con.execute("PRAGMA table_info(Transacciones)"))
        self.assertEqual(columnas, r.COLUMNAS_TRANSACCIONES)


class TestLlaveCompuesta(PruebaRepositorio):
    def test_la_exclusion_se_busca_por_identificacion_y_valor_no_solo_por_identificacion(self):
        self.repo.sembrar("celular", [fila_canal("celular", "1000000001", "3101234567")], maestra=False)
        self.assertTrue(self.repo.existe_exclusion("celular", "1000000001", "3101234567"))
        self.assertFalse(self.repo.existe_exclusion("celular", "1000000001", "3209999999"))  # misma identificación, otro celular
        self.assertFalse(self.repo.existe_exclusion("celular", "1000000002", "3101234567"))  # mismo celular, otra identificación

    def test_correos_y_celulares_son_tablas_independientes(self):
        self.repo.sembrar("correo", [fila_canal("correo", "1000000001", "a@ejemplo.invalid")], maestra=False)
        self.assertTrue(self.repo.existe_exclusion("correo", "1000000001", "a@ejemplo.invalid"))
        self.assertFalse(self.repo.existe_exclusion("celular", "1000000001", "a@ejemplo.invalid"))

    def test_la_maestra_es_distinta_de_la_base_de_exclusion(self):
        self.repo.sembrar("celular", [fila_canal("celular", "1000000001", "3101234567")], maestra=True)
        self.assertTrue(self.repo.existe_en_maestra("celular", "1000000001", "3101234567"))
        self.assertFalse(self.repo.existe_exclusion("celular", "1000000001", "3101234567"))


class TestInsercionYEliminacion(PruebaRepositorio):
    def test_insertar_canal_no_duplica_un_contacto_ya_presente(self):
        fila = fila_canal("celular", "1000000001", "3101234567")
        self.assertEqual(self.repo.insertar_canal("celular", fila), "insertado")
        self.assertEqual(self.repo.insertar_canal("celular", fila), "ya_presente")
        self.assertEqual(self.repo.contar("Celulares"), 1)

    def test_eliminar_de_maestra_borra_solo_el_registro_de_esa_identificacion_y_valor(self):
        self.repo.sembrar("correo", [fila_canal("correo", "1000000001", "a@ejemplo.invalid"),
                                     fila_canal("correo", "1000000002", "a@ejemplo.invalid")], maestra=True)
        self.assertEqual(self.repo.eliminar_de_maestra("correo", "1000000001", "a@ejemplo.invalid"), 1)
        self.assertEqual(self.repo.contar("MaestraCorreos"), 1)
        self.assertEqual(self.repo.eliminar_de_maestra("correo", "1000000001", "a@ejemplo.invalid"), 0)  # ya no está

    def test_exclusion_por_radicado_es_idempotente(self):
        self.repo.insertar_exclusion("900001", "1000000001")
        self.repo.insertar_exclusion("900001", "1000000001")
        self.assertEqual(self.repo.contar("Exclusion"), 1)


class TestReintentos(PruebaRepositorio):
    def test_una_falla_transitoria_se_recupera_dentro_de_los_3_intentos(self):
        self.repo.fallas["buscar_exclusion_celular"] = 2
        self.assertFalse(self.repo.existe_exclusion("celular", "1", "2"))
        self.assertEqual(self.repo.intentos["buscar_exclusion_celular"], 3)

    def test_una_falla_persistente_agota_los_3_reintentos_y_lanza_error(self):
        self.repo.fallas["insertar_celular"] = None
        with self.assertRaises(r.ErrorRepositorio):
            self.repo.insertar_canal("celular", fila_canal("celular", "1", "2"))
        self.assertEqual(self.repo.intentos["insertar_celular"], 3)
        self.assertEqual(self.repo.contar("Celulares"), 0)

    def test_los_reintentos_salen_de_la_configuracion_no_de_la_logica(self):
        repo = r.Repositorio(self.tmp / "otra.sqlite", reintentos=5, dormir=lambda s: None)
        self.addCleanup(repo.cerrar)
        repo.fallas["buscar_maestra_correo"] = None
        with self.assertRaises(r.ErrorRepositorio):
            repo.existe_en_maestra("correo", "1", "x")
        self.assertEqual(repo.intentos["buscar_maestra_correo"], 5)


class TestTransacciones(PruebaRepositorio):
    def test_cada_transicion_guarda_estado_anterior_y_nuevo(self):
        self.repo.registrar_transaccion("900001", "seleccion", 1)
        self.repo.registrar_transaccion("900001", "duplicados", 2)
        self.repo.registrar_transaccion("900001", "registro", 3)
        self.assertEqual(self.repo.recorrido("900001"), [("seleccion", None, 1, "ok", "NO APLICA"), ("duplicados", 1, 2, "ok", "NO APLICA"),
                                                         ("registro", 2, 3, "ok", "NO APLICA")])

    def test_un_fallo_deja_su_fila_aunque_el_repositorio_este_caido(self):  # lección de Medidas Cautelares
        self.repo.fallas["buscar_exclusion_correo"] = None
        self.repo.registrar_transaccion("900002", "duplicados", 2)
        with self.assertRaises(r.ErrorRepositorio):
            self.repo.existe_exclusion("correo", "1", "x")
        self.repo.registrar_transaccion("900002", "duplicados", 4, "fallo", "el repositorio no respondió; excepción de sistema")
        self.assertEqual(self.repo.transiciones_fallidas(), [("900002", "duplicados", "el repositorio no respondió, excepción de sistema")])

    def test_consultas_de_revision(self):
        self.repo.registrar_transaccion("900001", "seleccion", 1)
        self.repo.registrar_transaccion("900001", "registro", 3)
        self.repo.registrar_transaccion("900002", "seleccion", 1)
        self.repo.registrar_transaccion("900002", "duplicados", 4, "fallo", "x")
        self.repo.registrar_transaccion("900003", "seleccion", 1)
        self.assertEqual(self.repo.etapa_actual_por_caso(), [("900001", "registro", 3), ("900002", "duplicados", 4), ("900003", "seleccion", 1)])
        self.assertEqual(self.repo.conteo_por_estado(), {"Exitoso": 1, "No Exitoso": 1, "Sin Procesar": 1})

    def test_los_cinco_estados_del_lineamiento(self):
        self.assertEqual(r.ESTADOS, {1: "Sin Procesar", 2: "Procesando", 3: "Exitoso", 4: "No Exitoso", 5: "Procesado Parcialmente"})


class TestFilasDeFalloEnTransacciones(PruebaRepositorio):
    """Regla dura: cada paso de falla de EP-003 deja su fila `fallo` (no solo lo prueba la matriz del banco)."""

    class RegistroFalso:
        def __init__(self):
            self.lineas = []

        def auditoria(self, texto, modulo):
            self.lineas.append(("auditoria", texto))

        def error(self, texto, modulo):
            self.lineas.append(("error", texto))

        def reporte(self, *campos):
            self.lineas.append(("reporte", campos))

    def test_duplicados_sistema_y_comentario_fallido_dejan_su_fila_de_fallo(self):
        from habeasdata import ep003
        registro = self.RegistroFalso()
        ep003.duplicados_sistema(registro, self.repo, "900001", None, "x")
        ep003.duplicados_comentario_fallido(registro, self.repo, "900002", None, "x")
        self.assertEqual([(t[0], t[1]) for t in self.repo.transiciones_fallidas()], [("900001", "duplicados"), ("900002", "duplicados")])
        self.assertEqual(self.repo.estado_de("900001"), 4)

    def test_exclusion_del_caso_con_falla_deja_su_fila_de_fallo_y_estado_4(self):
        from habeasdata import ep003
        self.repo.fallas["insertar_exclusion"] = None
        caso = {"radicado_hijo": "900001", "radicado_padre": None, "nombre": "N", "numero_identificacion": "1", "tipo_identificacion": "CC",
                "fecha_recepcion": "21/08/2026", "correos": [], "telefonos": []}
        resultado = ep003.exclusion_del_caso(self.RegistroFalso(), self.repo, caso, [], ep003.cargar_stub(), "01/11/2026")
        self.assertEqual(resultado["operacion"], "insertar")
        self.assertEqual(self.repo.transiciones_fallidas()[0][:2], ("900001", "registro_exclusion"))
        self.assertEqual(self.repo.estado_de("900001"), 4)


class TestReintentosDeLaConfiguracion(unittest.TestCase):
    def test_abrir_repositorio_usa_NUMERO_REINTENTOS_SISTEMA_del_maestro(self):
        import json
        from habeasdata import ep003
        from habeasdata.config import cargar
        from tests.soporte import copiar_config
        tmp = Path(tempfile.mkdtemp(prefix="repo_cfg_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        copiar_config(tmp, 8765)
        cfg = cargar(tmp)
        cfg.maestro["NUMERO_REINTENTOS_SISTEMA"] = 5
        repo = ep003.abrir_repositorio(cfg, dormir=lambda s: None)
        self.addCleanup(repo.cerrar)
        repo.fallas["buscar_maestra_correo"] = None
        with self.assertRaises(r.ErrorRepositorio):
            repo.existe_en_maestra("correo", "1", "x")
        self.assertEqual(repo.intentos["buscar_maestra_correo"], 5)
        self.assertEqual(json.loads(json.dumps(cfg.proceso["Repositorio"]))["Motor"], "sqlite")


if __name__ == "__main__":
    unittest.main()
