"""Trazabilidad del repositorio local tras la auditoría adversarial de la corrida real: las 8 tablas del MER se escriben, `Resultado`
dice la verdad, ningún caso queda abierto, el descarte y las etapas previas quedan en `Transacciones` en su instante real, y lo
que se borra de las maestras deja huella. Corrida completa del orquestador con los 15 radicados sintéticos."""
import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from tests.soporte import REPO

for carpeta in (REPO / "banco",):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

import banco_ep002 as b  # noqa: E402
from habeasdata import ep003  # noqa: E402
from habeasdata import repositorio as r  # noqa: E402

RADICADOS = [str(f["IDRADICADO"]) for f in json.loads((REPO / "fixtures" / "zeus" / "radicados.json").read_text(encoding="utf-8"))]
ESCENARIO = {"id": "TRAZABILIDAD", "doble": {"radicados": RADICADOS}, "portales": {}, "repositorio": {}}


def correr(reloj=None, con_lecturas=False):
    """Corre el orquestador y devuelve la ruta de una copia de la base (y, si se pide, cuándo se leyó cada radicado)."""
    carpeta = Path(tempfile.mkdtemp(prefix="traza_"))
    copia = carpeta / "copia.sqlite"
    original = b.instantanea_repositorio
    lecturas = []

    def guardar(raiz):
        for archivo in Path(raiz).glob("Documentos/repositorio/*.sqlite"):
            shutil.copy(archivo, copia)
        return original(raiz)

    parches = [mock.patch.object(b, "instantanea_repositorio", guardar)]
    if reloj is not None:
        parches.append(mock.patch.object(b, "RELOJ", reloj))
    if con_lecturas:
        radicado_original = b.ClienteZeus.radicado

        def radicado(cliente, id_radicado, *a, **k):
            lecturas.append((str(id_radicado), reloj()))
            return radicado_original(cliente, id_radicado, *a, **k)
        parches.append(mock.patch.object(b.ClienteZeus, "radicado", radicado))
    for p in parches:
        p.start()
    try:
        b.correr_escenario(ESCENARIO)
    finally:
        for p in parches:
            p.stop()
    return copia, lecturas


class RegistroFalso:
    def __init__(self):
        self.lineas = []

    def auditoria(self, texto, modulo):
        self.lineas.append(("auditoria", texto))

    def error(self, texto, modulo):
        self.lineas.append(("error", texto))

    def reporte(self, *campos):
        self.lineas.append(("reporte", campos))


class TestCorridaCompleta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ruta, _ = correr()
        cls.carpeta = ruta.parent
        cls.con = sqlite3.connect(ruta)

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        shutil.rmtree(cls.carpeta, ignore_errors=True)

    def q(self, sql, *args):
        return self.con.execute(sql, args).fetchall()

    def test_blocker_1_excepciones_se_escribe_por_cada_excepcion(self):
        tipos = dict(self.q("SELECT TipoExcepcion, COUNT(*) FROM Excepciones GROUP BY TipoExcepcion"))
        self.assertEqual(tipos, {"1": 4, "4": 2})
        columnas = [f[1] for f in self.q("PRAGMA table_info(Excepciones)")]
        self.assertEqual(columnas, ["Id", "RadicadoZeus", "TipoExcepcion", "Detalle", "FechaHora"])
        self.assertEqual(self.q("SELECT COUNT(*) FROM Excepciones WHERE Detalle IS NULL OR Detalle = 'NO APLICA'")[0][0], 0)

    def test_blocker_2_las_8_tablas_del_mer_tienen_filas(self):
        for tabla in r.TABLAS:
            self.assertGreater(self.q(f"SELECT COUNT(*) FROM {tabla}")[0][0], 0, tabla)
        self.assertEqual(self.q("SELECT Valor FROM Parametros WHERE Clave = 'UMBRAL_COINCIDENCIA_NOMBRES'"), [("0.8",)])
        total, exitosos, no_exitosos, parciales, excepciones = self.q(
            "SELECT CasosProcesados, Exitosos, NoExitosos, Parciales, Excepciones FROM LogEjecucion")[0]
        self.assertEqual((total, exitosos, no_exitosos, parciales, excepciones), (15, 6, 6, 3, 6))
        self.assertEqual(self.q("SELECT COUNT(*) FROM Gestores WHERE Gestor IS NULL OR Agencia IS NULL")[0][0], 0)

    def test_blocker_3_ningun_caso_queda_abierto_al_cerrar_la_corrida(self):
        abiertos = self.q("SELECT RadicadoZeus FROM Transacciones WHERE IdTransaccion IN (SELECT MAX(IdTransaccion) FROM Transacciones "
                          "GROUP BY RadicadoZeus) AND EstadoNuevo IN (1, 2)")
        self.assertEqual(abiertos, [])

    def test_blocker_4_resultado_fallo_solo_cuando_el_estado_es_4(self):
        self.assertEqual(self.q("SELECT COUNT(*) FROM Transacciones WHERE (EstadoNuevo = 4) != (Resultado = 'fallo')")[0][0], 0)
        self.assertGreater(self.q("SELECT COUNT(*) FROM Transacciones WHERE Resultado = 'fallo'")[0][0], 0)

    def test_mayor_6_insumo_guarda_nombre_contacto_y_el_estado_final_real(self):
        ultimo = dict(self.q("SELECT RadicadoZeus, EstadoNuevo FROM Transacciones WHERE IdTransaccion IN "
                             "(SELECT MAX(IdTransaccion) FROM Transacciones GROUP BY RadicadoZeus)"))
        self.assertEqual(dict(self.q("SELECT RadicadoZeus, Estado FROM Insumo")), ultimo)
        self.assertEqual({3, 4, 5}, set(ultimo.values()))
        nombre, correos, telefonos = self.q("SELECT Nombre, Correos, Telefonos FROM Insumo WHERE RadicadoZeus = '900007'")[0]
        self.assertTrue(nombre and correos and telefonos)

    def test_mayor_7_el_descartado_aparece_en_transacciones_e_insumo(self):
        self.assertEqual(self.q("SELECT Etapa, EstadoAnterior, EstadoNuevo, Resultado FROM Transacciones WHERE RadicadoZeus = '900011' ORDER BY IdTransaccion"),
                         [("seleccion", None, 1, "ok"), ("seleccion", 1, 4, "fallo")])
        self.assertEqual(self.q("SELECT Estado FROM Insumo WHERE RadicadoZeus = '900011'"), [(4,)])

    def test_mayor_8_ninguna_fila_de_relleno(self):
        self.assertEqual(self.q("SELECT COUNT(*) FROM Transacciones WHERE Motivo = 'NO APLICA' OR Motivo IS NULL")[0][0], 0)
        self.assertEqual(self.q("SELECT COUNT(*) FROM Transacciones WHERE Etapa LIKE '%inicio%'")[0][0], 0)

    def test_mayor_9_el_duplicado_parcial_cuenta_lo_mismo_en_base_y_los_valores_restantes_se_registran(self):
        motivo = self.q("SELECT Motivo FROM Transacciones WHERE RadicadoZeus = '900007' AND Etapa = 'duplicados'")[0][0]
        self.assertTrue(motivo.startswith("excepción de negocio 4 (parcial)"))
        self.assertEqual(self.q("SELECT Estado FROM Insumo WHERE RadicadoZeus = '900007'"), [(5,)])
        self.assertEqual(self.q("SELECT COUNT(*) FROM Exclusion WHERE RadicadoZeus = '900007'")[0][0], 1)
        self.assertGreater(self.q("SELECT COUNT(*) FROM Celulares WHERE ZEUS = '900007'")[0][0], 0)  # el valor NO duplicado sí se registró

    def test_mayor_10_lo_que_se_borra_de_las_maestras_deja_huella(self):
        borrados = self.q("SELECT RadicadoZeus, Tabla, Valor, FilaEliminada FROM AuditoriaMaestras")
        self.assertEqual(len(borrados), 9)
        for radicado, tabla, valor, fila in borrados:
            self.assertTrue(radicado and valor in fila)
            self.assertIn(tabla, ("MaestraCelulares", "MaestraCorreos"))

    def test_menor_14_el_puntaje_de_identidad_queda_en_la_base(self):
        motivos = [f[0] for f in self.q("SELECT Motivo FROM Transacciones WHERE Etapa = 'identidad'")]
        self.assertTrue(motivos)
        self.assertTrue(all("puntaje" in m for m in motivos), motivos)

    def test_menor_15_la_corrida_alcanza_el_estado_5(self):
        self.assertGreater(self.q("SELECT COUNT(*) FROM Insumo WHERE Estado = 5")[0][0], 0)


class TestMomentoRealDeCadaEtapa(unittest.TestCase):
    def test_blocker_5_cada_lectura_se_anota_antes_de_leer_el_siguiente_radicado(self):
        reloj_actual = [datetime(2026, 11, 2, 8, 0, 0)]

        def reloj():  # cada consulta al reloj avanza un segundo: el orden de las filas es el orden real de los hechos
            reloj_actual[0] += timedelta(seconds=1)
            return reloj_actual[0]

        ruta, lecturas = correr(reloj, con_lecturas=True)
        self.addCleanup(shutil.rmtree, ruta.parent, ignore_errors=True)
        con = sqlite3.connect(ruta)
        self.addCleanup(con.close)
        leidos = [(i, t.strftime("%Y-%m-%d %H:%M:%S")) for i, t in lecturas]
        ids = [i for i, _ in leidos]
        for posicion, (radicado, momento_lectura) in enumerate(leidos):
            fila = con.execute("SELECT FechaHora FROM Transacciones WHERE RadicadoZeus = ? AND Etapa = 'lectura' AND EstadoNuevo = 2 "
                               "ORDER BY IdTransaccion LIMIT 1", (radicado,)).fetchone()
            if fila is None:
                continue  # la lectura falló: su fila es de sistema
            self.assertGreaterEqual(fila[0], momento_lectura, radicado)
            if posicion + 1 < len(ids):  # y antes de que el bot lea el radicado siguiente (no se anota en bloque al llegar a HU-010)
                self.assertLess(fila[0], leidos[posicion + 1][1], f"{radicado} se anotó después de leer {ids[posicion + 1]}")

    def test_las_etapas_previas_ya_no_se_anotan_en_bloque(self):
        self.assertFalse(hasattr(ep003, "registrar_previas"))


class TestIdentidadYExcepciones(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="traza_id_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = r.Repositorio(self.tmp / "lab.sqlite", dormir=lambda s: None, reloj=lambda: datetime(2026, 11, 2, 9, 0, 0))
        self.addCleanup(self.repo.cerrar)

    def tipos(self, radicado):
        return [f[0] for f in self.repo.con.execute("SELECT TipoExcepcion FROM Excepciones WHERE RadicadoZeus = ?", (radicado,))]

    def test_cada_rama_de_identidad_cierra_el_caso_y_deja_su_excepcion(self):
        esperado = {"excepcion_negocio_3": ("3", 4), "gestion_manual": ("gestion_manual", 4), "revision_humana": ("gestion_manual", 4),
                    "excepcion_sistema": ("sistema", 4)}
        for numero, (etiqueta, (tipo, estado)) in enumerate(esperado.items(), start=1):
            radicado = f"9000{numero}"
            self.repo.registrar_transaccion(radicado, "validacion_campos", 2, "ok", "campos completos")
            ep003.transaccion_identidad(self.repo, radicado, etiqueta, "policia", 0.5, "motivo", "CODIGO")
            self.assertEqual(self.repo.estado_de(radicado), estado, etiqueta)
            self.assertEqual(self.tipos(radicado), [tipo], etiqueta)
            self.assertEqual(self.repo.con.execute("SELECT COUNT(*) FROM Gestores WHERE RadicadoZeus = ?", (radicado,)).fetchone()[0], 1)

    def test_respuesta_sin_nombre_ya_no_deja_el_caso_abierto_en_2(self):
        self.repo.registrar_transaccion("900013", "validacion_campos", 2, "ok", "campos completos")
        ep003.transaccion_identidad(self.repo, "900013", "sin_nombre", "procuraduria")
        self.assertEqual(self.repo.estado_de("900013"), 5)

    def test_el_cierre_de_corrida_cierra_cualquier_caso_que_quedo_abierto(self):
        self.repo.registrar_transaccion("900099", "validacion_campos", 2, "ok", "campos completos")
        ep003.cerrar_corrida(self.repo)
        self.assertEqual(self.repo.estado_de("900099"), 4)
        self.assertEqual(self.repo.con.execute("SELECT COUNT(*) FROM Excepciones WHERE RadicadoZeus = '900099'").fetchone()[0], 1)
        self.assertEqual(self.repo.con.execute("SELECT COUNT(*) FROM LogEjecucion").fetchone()[0], 1)
        ep003.cerrar_corrida(self.repo)  # idempotente: una sola fila resumen
        self.assertEqual(self.repo.con.execute("SELECT COUNT(*) FROM LogEjecucion").fetchone()[0], 1)

    def test_una_base_creada_por_la_version_anterior_se_migra_sin_perder_filas(self):
        antigua = self.tmp / "antigua.sqlite"
        con = sqlite3.connect(antigua)
        con.execute("CREATE TABLE Excepciones (Id INTEGER PRIMARY KEY AUTOINCREMENT, RadicadoZeus TEXT, Tipo TEXT, Detalle TEXT, Fecha TEXT)")
        con.execute("INSERT INTO Excepciones (RadicadoZeus, Tipo, Detalle, Fecha) VALUES ('1','4','d','f')")
        con.commit()
        con.close()
        repo = r.Repositorio(antigua, dormir=lambda s: None)
        self.addCleanup(repo.cerrar)
        self.assertEqual(repo.con.execute("SELECT RadicadoZeus, TipoExcepcion FROM Excepciones").fetchall()[0][:], ("1", "4"))

    def test_los_valores_de_un_duplicado_parcial_usan_el_mismo_texto_en_reporte_log_y_base(self):
        registro = RegistroFalso()
        resultado = {"duplicados": [{"canal": "celular"}], "continua": True}
        ep003.duplicados_excepcion_4(registro, self.repo, "900007", None, resultado)
        motivo = ep003.motivo_excepcion_4(resultado)
        self.assertIn(("reporte", ("900007", None, "excepción de negocio 4", "4", motivo)), registro.lineas)
        self.assertTrue(any(motivo in texto for tipo, texto in registro.lineas if tipo == "auditoria"))
        self.assertEqual(self.repo.recorrido("900007"), [("duplicados", None, 2, "ok", motivo)])


if __name__ == "__main__":
    unittest.main()
