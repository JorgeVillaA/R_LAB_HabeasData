"""Corrida repetible (segunda ronda de la auditoría): el archivo del repositorio se suelta al terminar, `LogEjecucion` dice qué corrida
fue y cuántos pasos dio, `Parametros` cubre toda la configuración y el reporte y los logs se separan por corrida."""
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from tests.soporte import CLIENTE, SECRETO, RADICADOS, copiar_config, PruebaConDoble, REPO
from dobles.zeus_api.servidor import DobleZeus
from habeasdata import ep001, ep003, pasos
from habeasdata import repositorio as r
from habeasdata.config import cargar
from habeasdata.registro import CORRIDA_DETENIDA, CORRIDA_INTERRUMPIDA, FIN_DE_CORRIDA, Registro


class PruebaDeRobot(unittest.TestCase):
    """El robot de Studio: los pasos de `pasos.py` encadenados sobre una raíz temporal."""

    def setUp(self):
        self.doble = DobleZeus((CLIENTE, SECRETO), list(RADICADOS)).iniciar()
        self.addCleanup(self.doble.detener)
        self.raiz = Path(tempfile.mkdtemp(prefix="lab_repetible_"))
        self.addCleanup(shutil.rmtree, self.raiz, ignore_errors=True)
        copiar_config(self.raiz, self.doble.puerto)
        entorno = mock.patch.dict(os.environ, {"ZEUS_DOBLE_CLIENT_ID": CLIENTE, "ZEUS_DOBLE_CLIENT_SECRET": SECRETO})
        entorno.start()
        self.addCleanup(entorno.stop)
        self.addCleanup(pasos._soltar_repositorio)
        self.archivo = self.raiz / "Documentos" / "repositorio" / "lab.sqlite"

    def correr_hasta_el_cierre(self, estado="ok"):
        pasos.iniciar(str(self.raiz))
        self.assertTrue(pasos.repositorio()["habilitado"])
        pasos.evento("un paso cualquiera")
        return pasos.cerrar(str({"estado": estado, "avanzan": [], "casos": {}}))

    def consultar(self, sql):
        con = sqlite3.connect(self.archivo)
        try:
            return con.execute(sql).fetchall()
        finally:
            con.close()


class TestFugaDeConexion(PruebaDeRobot):
    def test_tras_cerrar_el_archivo_se_puede_mover(self):
        """El síntoma medido: el .sqlite seguía abierto por rocketbot.exe y no se podía mover ni respaldar."""
        self.assertTrue(self.correr_hasta_el_cierre()["ok"])
        destino = self.archivo.with_name("lab_respaldo.sqlite")
        self.archivo.rename(destino)  # en Windows falla con PermissionError si la conexión sigue abierta
        self.assertTrue(destino.is_file())
        self.assertFalse(self.archivo.exists())
        shutil.copy(destino, self.archivo.with_name("copia.sqlite"))
        destino.unlink()

    def test_tras_cerrar_la_sesion_no_conserva_la_conexion(self):
        self.correr_hasta_el_cierre()
        self.assertIsNone(pasos._sesion.repo)

    def test_el_archivo_queda_libre_aunque_falle_el_cierre_de_la_corrida(self):
        pasos.iniciar(str(self.raiz))
        pasos.repositorio()
        with mock.patch.object(ep003, "cerrar_corrida", side_effect=RuntimeError("falla simulada")):
            with self.assertRaises(RuntimeError):
                pasos.cerrar(str({"estado": "ok", "casos": {}}))
        self.archivo.rename(self.archivo.with_name("lab_movido.sqlite"))

    def test_corrida_detenida_tambien_suelta_el_archivo(self):
        self.correr_hasta_el_cierre("detenido")
        self.archivo.rename(self.archivo.with_name("lab_movido.sqlite"))

    def test_una_sesion_nueva_cierra_la_conexion_de_la_anterior(self):
        pasos.iniciar(str(self.raiz))
        pasos.repositorio()
        anterior = pasos._sesion.repo
        pasos.iniciar(str(self.raiz))
        self.assertIsNone(anterior.con)

    def test_cerrar_el_repositorio_es_idempotente_y_sirve_como_contexto(self):
        ruta = self.raiz / "otro.sqlite"
        with r.Repositorio(ruta) as repo:
            repo.registrar_transaccion("1", "seleccion", 1)
        repo.cerrar()
        ruta.rename(self.raiz / "otro_movido.sqlite")


class TestLogEjecucion(PruebaDeRobot):
    def test_la_fila_resumen_trae_el_id_de_la_corrida_y_los_pasos(self):
        self.correr_hasta_el_cierre()
        id_corrida, pasos_modulo = self.consultar("SELECT IdCorrida, Pasos FROM LogEjecucion")[0]
        self.assertRegex(id_corrida, r"^C\d{14}$")
        self.assertEqual(pasos_modulo, 4)  # iniciar, repositorio, evento y el propio cierre
        auditoria = "".join(p.read_text(encoding="utf-8") for p in (self.raiz / "Logs").rglob("*LOG_DE_AUDITORIA*.csv"))
        self.assertIn(f"[{id_corrida}] Fin de ejecución EP-001", auditoria)  # la misma corrida en la base y en el log

    def test_el_ejecutor_anota_los_comandos_de_studio_con_el_archivo_ya_libre(self):
        self.correr_hasta_el_cierre()
        id_corrida = self.consultar("SELECT IdCorrida FROM LogEjecucion")[0][0]
        self.assertEqual(r.anotar_comandos_studio(self.archivo, 1737, id_corrida), 1)
        self.assertEqual(self.consultar("SELECT ComandosStudio, Pasos FROM LogEjecucion"), [(1737, 4)])  # los de Studio no pisan los del producto

    def test_dos_corridas_dejan_dos_filas_con_ids_distintos_y_el_contador_reinicia(self):
        for hora in (9, 10):
            with mock.patch.object(pasos, "Registro", lambda cfg, h=hora: Registro(cfg, lambda: datetime(2026, 11, 3, h, 0, 0))):
                self.correr_hasta_el_cierre()
        filas = self.consultar("SELECT IdCorrida, Pasos FROM LogEjecucion ORDER BY Id")
        self.assertEqual(len(filas), 2)
        self.assertNotEqual(filas[0][0], filas[1][0])
        self.assertEqual((filas[0][1], filas[1][1]), (4, 4))

    def test_un_archivo_de_una_version_anterior_gana_las_columnas_nuevas(self):
        ruta = self.raiz / "viejo.sqlite"
        con = sqlite3.connect(ruta)
        con.execute("CREATE TABLE LogEjecucion (Id INTEGER PRIMARY KEY AUTOINCREMENT, Fecha TEXT, CasosProcesados INTEGER, "
                    "Exitosos INTEGER, NoExitosos INTEGER, Parciales INTEGER, Excepciones INTEGER, DuracionSegundos INTEGER, Detalle TEXT)")
        con.commit()
        con.close()
        with r.Repositorio(ruta) as repo:
            self.assertTrue({"IdCorrida", "Pasos", "ComandosStudio"} <= repo._columnas("LogEjecucion"))


class TestParametros(unittest.TestCase):
    """`Parametros` cubre TODO lo que declara el spec (ventana, umbral, rutas…): las hojas de los tres JSON de configuración."""

    def setUp(self):
        self.cfg = cargar(REPO)
        self.tmp = Path(tempfile.mkdtemp(prefix="lab_param_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def guardado(self):
        cfg = cargar(REPO)
        cfg.raiz = self.tmp
        with ep003.abrir_repositorio(cfg) as repo:
            return {f[0]: f[1] for f in repo.con.execute("SELECT Clave, Valor FROM Parametros")}

    def test_cada_hoja_de_la_configuracion_esta_en_parametros(self):
        parametros = self.guardado()
        hojas = dict(ep003._aplanar(self.cfg.maestro))
        hojas.update(ep003._aplanar(self.cfg.proceso))
        hojas.update(ep003._aplanar(self.cfg.maquina, "Maquina"))
        faltan = sorted(k for k in hojas if k not in parametros)
        self.assertEqual(faltan, [])
        self.assertGreaterEqual(len(parametros), 60)

    def test_los_que_nombra_el_spec_estan_con_su_valor_efectivo(self):
        parametros = self.guardado()
        self.assertEqual(float(parametros["UMBRAL_COINCIDENCIA_NOMBRES"]), 0.8)  # umbral
        self.assertEqual(parametros["Maquina.RutasVentanas.VentanaEjecucion"], "07:00-19:00")  # ventana
        self.assertEqual(parametros["Portales.Real.VentanaOperativa.Desde"], "06:00")
        self.assertEqual(parametros["Portales.Real.VentanaOperativa.Hasta"], "20:00")
        self.assertEqual(parametros["Maquina.RutasVentanas.RutasProceso.Documentos"], "Documentos")  # rutas
        self.assertEqual(parametros["Maquina.RutaRaizEfectiva"], str(self.tmp))
        self.assertEqual(parametros["CADENCIA_REINTENTO_BANDEJA_VACIA.MaximoReintentosDiarios"], "3")
        self.assertEqual(parametros["Portales.Modo"], "fixture")

    def test_el_valor_es_el_de_la_corrida_no_el_de_una_anterior(self):
        self.guardado()
        cfg = cargar(REPO)
        cfg.raiz = self.tmp
        cfg.maestro["UMBRAL_COINCIDENCIA_NOMBRES"] = 0.9
        with ep003.abrir_repositorio(cfg) as repo:
            self.assertEqual(repo.con.execute("SELECT Valor FROM Parametros WHERE Clave='UMBRAL_COINCIDENCIA_NOMBRES'").fetchone()[0], "0.9")

    def test_ningun_secreto_se_guarda(self):
        for clave, valor in self.guardado().items():
            self.assertNotRegex(clave.rsplit(".", 1)[-1].replace("ClientSecretEnv", "").replace("CredencialTarget", ""),
                                r"(?i)secret|password|bearer", clave)
            self.assertNotIn("secreto-", valor)


class TestSeparacionPorCorrida(PruebaConDoble):
    def registro_en(self, hora, minuto):
        return Registro(self.cfg, lambda: datetime(2026, 11, 3, hora, minuto, 0))

    def filas(self, ruta):
        return [linea.split(";") for linea in ruta.read_text(encoding="utf-8").splitlines()[1:]]

    def test_cada_fila_del_reporte_y_del_log_lleva_el_id_de_su_corrida(self):
        primera, segunda = self.registro_en(9, 17), self.registro_en(9, 18)
        self.assertNotEqual(primera.id_corrida, segunda.id_corrida)
        for registro in (primera, segunda):
            registro.asegurar_archivos()
            registro.auditoria("Inicio de ejecución EP-001")
            registro.reporte("900001", None, "campos completos")
            registro.cerrar_corrida("ok")
        reporte = self.filas(primera.ruta_reporte())
        for id_corrida in (primera.id_corrida, segunda.id_corrida):
            propias = [f for f in reporte if f[6] == id_corrida]
            self.assertEqual([f[3] for f in propias], ["campos completos", FIN_DE_CORRIDA])
        auditoria = self.filas(primera.ruta_auditoria())
        self.assertEqual([f[3].split("] ")[0] for f in auditoria], [f"[{primera.id_corrida}", f"[{segunda.id_corrida}"])
        self.assertTrue(all(len(f) == 4 for f in auditoria))  # los cuatro campos fijos del anexo se conservan

    def test_una_corrida_que_no_llego_a_su_cierre_queda_marcada_como_interrumpida(self):
        """La corrida abortada de las 09:17 le atribuía a 900001 una historia distinta a la de la buena de las 09:18."""
        abortada, buena = self.registro_en(9, 17), self.registro_en(9, 18)
        abortada.asegurar_archivos()
        abortada.reporte("900001", None, "campos completos")  # el proceso murió aquí: nunca cierra
        buena.asegurar_archivos()
        buena.reporte("900001", None, "excepción de negocio 1", "1", "SIN CANAL DE CONTACTO")
        buena.cerrar_corrida("ok")
        marcas = [f for f in self.filas(buena.ruta_reporte()) if f[3] in (CORRIDA_INTERRUMPIDA, FIN_DE_CORRIDA)]
        self.assertEqual([(f[3], f[6]) for f in marcas], [(CORRIDA_INTERRUMPIDA, abortada.id_corrida), (FIN_DE_CORRIDA, buena.id_corrida)])
        self.assertIn("no son resultado de negocio", marcas[0][5])
        self.assertEqual(sum(1 for f in self.filas(buena.ruta_reporte()) if f[3] == CORRIDA_INTERRUMPIDA), 1)

    def test_una_corrida_ya_cerrada_no_se_marca_y_la_interrumpida_se_marca_una_sola_vez(self):
        cerrada, abortada, tercera = self.registro_en(9, 10), self.registro_en(9, 11), self.registro_en(9, 12)
        cerrada.asegurar_archivos()
        cerrada.reporte("900001", None, "campos completos")
        cerrada.cerrar_corrida("ok")
        abortada.asegurar_archivos()
        abortada.reporte("900002", None, "campos completos")
        tercera.asegurar_archivos()
        self.registro_en(9, 13).asegurar_archivos()
        interrumpidas = [f[6] for f in self.filas(cerrada.ruta_reporte()) if f[3] == CORRIDA_INTERRUMPIDA]
        self.assertEqual(interrumpidas, [abortada.id_corrida])

    def test_una_corrida_detenida_cierra_con_la_marca_de_detenida(self):
        self.doble.detener()
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertEqual(resumen["estado"], "detenido")
        ultima = self.filas(self.registro.ruta_reporte())[-1]
        self.assertEqual((ultima[3], ultima[6], ultima[1]), (CORRIDA_DETENIDA, self.registro.id_corrida, "NO APLICA"))
        self.assertEqual(ultima[5], "estado detenido")

    def test_ep001_normal_cierra_con_fin_de_corrida(self):
        ep001.procesar(self.cfg, self.cliente, self.registro)
        ultima = self.filas(self.registro.ruta_reporte())[-1]
        self.assertEqual((ultima[3], ultima[6]), (FIN_DE_CORRIDA, self.registro.id_corrida))

    def test_el_cierre_se_escribe_una_sola_vez(self):
        self.registro.cerrar_corrida("ok")
        self.registro.cerrar_corrida("detenido")
        self.assertEqual([f[3] for f in self.filas(self.registro.ruta_reporte())], [FIN_DE_CORRIDA])


class TestDosCorridasSobreLaMismaBase(unittest.TestCase):
    """Tercera ronda: una segunda corrida del mismo día deja SU rastro y no hereda como propio el de la anterior."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="lab_dos_corridas_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.ruta = self.tmp / "lab.sqlite"
        self.stub = ep003.cargar_stub()

    def correr(self, id_corrida, hora, radicados=("900002", "900008")):
        reloj = lambda: datetime(2026, 11, 3, hora, 0, 0)  # noqa: E731
        with r.Repositorio(self.ruta, reloj=reloj, id_corrida=id_corrida) as repo:
            for radicado in radicados:
                repo.abrir_insumo(radicado)
                repo.registrar_transaccion(radicado, "seleccion", 1, "ok", "seleccionado")
                repo.insertar_exclusion(radicado, "1000000000")
                ep003.cerrar_en_excepcion(repo, radicado, "validacion_campos", "1", f"excepción en la corrida {id_corrida}", self.stub)
            return repo.resumen_de_corrida(id_corrida)

    def filas(self, sql):
        con = sqlite3.connect(self.ruta)
        try:
            return con.execute(sql).fetchall()
        finally:
            con.close()

    def test_gestores_guarda_una_fila_por_radicado_y_por_corrida_con_su_fecha_y_su_motivo(self):
        self.correr("C1", 9)
        self.correr("C2", 11)
        filas = self.filas("SELECT RadicadoZeus, IdCorrida, FechaAsignacion, Motivo FROM Gestores ORDER BY RadicadoZeus, IdCorrida")
        self.assertEqual(filas, [("900002", "C1", "2026-11-03 09:00:00", "excepción 1: excepción en la corrida C1"),
                                 ("900002", "C2", "2026-11-03 11:00:00", "excepción 1: excepción en la corrida C2"),
                                 ("900008", "C1", "2026-11-03 09:00:00", "excepción 1: excepción en la corrida C1"),
                                 ("900008", "C2", "2026-11-03 11:00:00", "excepción 1: excepción en la corrida C2")])

    def test_exclusion_guarda_una_fila_por_radicado_y_por_corrida_con_su_propia_fecha(self):
        self.correr("C1", 9)
        self.correr("C2", 11)
        self.assertEqual(self.filas("SELECT RadicadoZeus, IdCorrida, FechaExclusion FROM Exclusion ORDER BY RadicadoZeus, IdCorrida"),
                         [("900002", "C1", "2026-11-03 09:00:00"), ("900002", "C2", "2026-11-03 11:00:00"),
                          ("900008", "C1", "2026-11-03 09:00:00"), ("900008", "C2", "2026-11-03 11:00:00")])

    def test_dentro_de_una_corrida_no_se_duplica(self):
        self.correr("C1", 9)
        self.correr("C1", 9)  # el mismo id: es la misma corrida reintentada, no una nueva
        self.assertEqual(self.filas("SELECT COUNT(*) FROM Gestores"), [(2,)])
        self.assertEqual(self.filas("SELECT COUNT(*) FROM Exclusion"), [(2,)])

    def test_que_paso_en_la_corrida_x_devuelve_solo_lo_de_x(self):
        self.correr("C1", 9)
        segunda = self.correr("C2", 11, radicados=("900002",))
        for tabla in ("Transacciones", "Excepciones", "Exclusion", "Gestores", "Insumo"):
            self.assertTrue(segunda[tabla], tabla)
            self.assertEqual({f["IdCorrida"] for f in segunda[tabla]}, {"C2"}, tabla)
        self.assertEqual([f["RadicadoZeus"] for f in segunda["Gestores"]], ["900002"])  # 900008 solo está en C1
        with r.Repositorio(self.ruta, id_corrida="C1") as repo:
            self.assertEqual({f["RadicadoZeus"] for f in repo.resumen_de_corrida("C1")["Gestores"]}, {"900002", "900008"})

    def test_la_primera_transaccion_de_la_corrida_nueva_no_hereda_el_estado_final_de_la_anterior(self):
        self.correr("C1", 9)
        self.correr("C2", 11)
        self.assertEqual(self.filas("SELECT IdCorrida, EstadoAnterior, EstadoNuevo FROM Transacciones WHERE RadicadoZeus='900002' "
                                    "AND Etapa='seleccion' ORDER BY IdTransaccion"), [("C1", None, 1), ("C2", None, 1)])

    def test_insumo_dice_que_corrida_lo_toco_por_ultima_vez(self):
        self.correr("C1", 9)
        self.correr("C2", 11, radicados=("900002",))
        self.assertEqual(self.filas("SELECT RadicadoZeus, IdCorrida FROM Insumo ORDER BY RadicadoZeus"), [("900002", "C2"), ("900008", "C1")])

    def test_un_archivo_con_exclusion_unica_por_radicado_se_migra_sin_perder_filas(self):
        con = sqlite3.connect(self.ruta)
        con.execute("CREATE TABLE Exclusion (Id INTEGER PRIMARY KEY AUTOINCREMENT, RadicadoZeus TEXT UNIQUE, Identificacion TEXT, FechaExclusion TEXT)")
        con.execute("INSERT INTO Exclusion (RadicadoZeus, Identificacion, FechaExclusion) VALUES ('900002', '1', '2026-11-02 08:00:00')")
        con.commit()
        con.close()
        self.correr("C2", 11, radicados=("900002",))
        self.assertEqual(self.filas("SELECT RadicadoZeus, IdCorrida, FechaExclusion FROM Exclusion ORDER BY Id"),
                         [("900002", None, "2026-11-02 08:00:00"), ("900002", "C2", "2026-11-03 11:00:00")])


class TestEnrutamientoDesdeLaConfiguracion(unittest.TestCase):
    """Coordinador y correo de `Gestores` salen del stub de Cobra (configuración), no de un literal del código."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="lab_enrutamiento_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.ruta = self.tmp / "lab.sqlite"

    def gestion(self, stub, radicado="900002"):
        with r.Repositorio(self.ruta) as repo:
            ep003.cerrar_en_excepcion(repo, radicado, "validacion_campos", "1", "motivo", stub)
            return repo.con.execute("SELECT Gestor, Agencia, Coordinador, Correo FROM Gestores WHERE RadicadoZeus = ?", (radicado,)).fetchone()

    def test_la_configuracion_por_defecto_trae_coordinador_y_correo_por_sucursal(self):
        stub = ep003.cargar_stub()
        self.assertEqual(tuple(self.gestion(stub, "900002")), ("GESTOR-SINTETICO-1", "SUCURSAL-SINTETICA-1", "COORDINADOR-SINTETICO-1",
                                                               "coordinador.sintetico.1@lab.invalid"))
        self.assertEqual(tuple(self.gestion(stub, "900008")), ("GESTOR-SINTETICO-2", "SUCURSAL-SINTETICA-2", "COORDINADOR-SINTETICO-2",
                                                               "coordinador.sintetico.2@lab.invalid"))

    def test_ningun_valor_de_enrutamiento_es_un_literal_del_codigo(self):
        stub = ep003.cargar_stub()
        stub["por_defecto"].update(GESTOR="G-CAMBIADO", SUCURSAL="S-CAMBIADA", COORDINADOR="C-CAMBIADO")
        stub["por_defecto"]["CORREO COORDINADOR"] = "cambiado@lab.invalid"
        stub["coordinadores_por_sucursal"] = {}
        self.assertEqual(tuple(self.gestion(stub)), ("G-CAMBIADO", "S-CAMBIADA", "C-CAMBIADO", "cambiado@lab.invalid"))

    def test_sin_dato_de_cobra_se_usa_el_valor_declarado_en_la_configuracion(self):
        stub = ep003.cargar_stub()
        stub["sin_asignar"] = "PENDIENTE-DE-ASIGNAR"
        for clave in ("GESTOR", "SUCURSAL", "COORDINADOR", "CORREO COORDINADOR"):
            stub["por_defecto"].pop(clave)
        stub["coordinadores_por_sucursal"] = {}
        self.assertEqual(tuple(self.gestion(stub)), ("PENDIENTE-DE-ASIGNAR",) * 4)

    def test_el_codigo_no_lleva_el_literal(self):
        import inspect
        self.assertNotIn("SIN ASIGNAR", inspect.getsource(ep003))


if __name__ == "__main__":
    unittest.main()
