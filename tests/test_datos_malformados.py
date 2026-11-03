"""Frontera con la API de Zeus: respuestas malformadas se tratan como excepción acotada, nunca abortan la corrida.

Hallazgos del data-consistency-checker (invariantes 1, 2 y 3): registro sin IDRADICADO, cuerpo sin `value`,
valores fantasma («None»), canal falso con «No aporta/…» y tipos no escalares.
"""
from unittest import mock

from tests.soporte import PruebaConDoble, RADICADOS, REPO
from habeasdata import ep001, pasos
from habeasdata.config import cargar
from habeasdata.zeus import ClienteZeus, ErrorRespuesta


class TestRegistroMalformado(PruebaConDoble):
    def con_radicados(self, *radicados):
        self.configurar_doble(radicados=list(radicados))

    def test_registro_sin_idradicado_es_excepcion_de_sistema_del_caso(self):
        malo = {k: v for k, v in RADICADOS[0].items() if k != "IDRADICADO"}
        with mock.patch.object(self.cliente, "radicado", return_value=malo):
            with self.assertRaises(ep001.ExcepcionSistemaCaso):
                ep001.extraer(self.cliente, self.cfg, "900001")

    def test_idradicado_nulo_o_vacio_no_genera_un_radicado_fantasma(self):
        for valor in (None, "", "   ", "No aporta"):
            malo = dict(RADICADOS[0], IDRADICADO=valor)
            with mock.patch.object(self.cliente, "radicado", return_value=malo):
                with self.assertRaises(ep001.ExcepcionSistemaCaso, msg=repr(valor)):
                    ep001.extraer(self.cliente, self.cfg, "900001")

    def test_respuesta_que_no_es_un_registro_es_excepcion_de_sistema(self):
        for malo in (None, [], "texto", 5):
            with mock.patch.object(self.cliente, "radicado", return_value=malo):
                with self.assertRaises(ep001.ExcepcionSistemaCaso, msg=repr(malo)):
                    ep001.extraer(self.cliente, self.cfg, "900001")

    def test_campos_con_tipo_no_escalar_se_rechazan(self):
        for campo, valor in (("TELEFONODECONTACTO", ["3001234567"]), ("NOMBREDELCLIENTE", {"x": 1}),
                             ("CORREOELECTRONICOPARAEXCLUSION", ["a@b.invalid"]), ("TIPODEIDENTIFICACION", True),
                             ("NOIDENTIFICACIONDELCLIENTE", 3001234567.0)):
            malo = dict(RADICADOS[0], **{campo: valor})
            with mock.patch.object(self.cliente, "radicado", return_value=malo):
                with self.assertRaises(ep001.ExcepcionSistemaCaso, msg=campo):
                    ep001.extraer(self.cliente, self.cfg, "900001")

    def test_identificacion_numerica_entera_se_acepta(self):
        bueno = dict(RADICADOS[0], NOIDENTIFICACIONDELCLIENTE=1000000001)
        with mock.patch.object(self.cliente, "radicado", return_value=bueno):
            self.assertEqual(ep001.extraer(self.cliente, self.cfg, "900001")["numero_identificacion"], "1000000001")

    def test_una_fila_malformada_no_aborta_la_corrida(self):
        malo = {k: v for k, v in RADICADOS[2].items() if k != "IDRADICADO"}
        original = self.cliente.radicado

        def radicado(id_radicado):
            return malo if str(id_radicado) == "900003" else original(id_radicado)

        with mock.patch.object(self.cliente, "radicado", side_effect=radicado):
            resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertEqual(resumen["estado"], "ok")
        self.assertIn("900003", resumen["excepciones_sistema"])
        self.assertIn("900001", resumen["avanzan"])


class TestSeparacionYTipos(PruebaConDoble):
    def test_las_partes_ausentes_no_son_canal(self):
        self.assertEqual(ep001.separar_valores("No aporta/3001234567", self.cfg), ["3001234567"])
        self.assertEqual(ep001.separar_valores("a@x.invalid/NO APORTA", self.cfg), ["a@x.invalid"])
        self.assertEqual(ep001.separar_valores("No aporta/NO APORTA", self.cfg), [])

    def test_canal_falso_no_cuenta_como_presente(self):
        registro = dict(RADICADOS[0], CORREOELECTRONICOPARAEXCLUSION="No aporta/NO APORTA", TELEFONODECONTACTO="No aporta/")
        caso = ep001.normalizar_caso(registro, self.cfg)
        self.assertFalse(caso["canal_correo"] or caso["canal_telefono"])

    def test_la_normalizacion_es_determinista(self):
        self.assertEqual(ep001.normalizar_caso(RADICADOS[6], self.cfg), ep001.normalizar_caso(dict(RADICADOS[6]), self.cfg))

    def test_validar_completitud_tolera_un_caso_sin_indicadores_de_canal(self):
        veredicto = ep001.validar_completitud({"nombre": "A", "tipo_identificacion": "B", "numero_identificacion": "1"})
        self.assertEqual(veredicto["motivos"], ["SIN CANAL DE CONTACTO"])

    def test_clasificar_telefono_tolera_un_entero(self):
        self.assertEqual(ep001.clasificar_telefono(3101234567, self.cfg), "celular")


class TestCuerpoSinValue(PruebaConDoble):
    def test_cuerpo_200_sin_value_es_error_de_respuesta(self):
        with mock.patch.object(ClienteZeus, "_autorizada", return_value={}):
            with self.assertRaises(ErrorRespuesta):
                self.cliente.consultar()

    def test_value_que_no_es_lista_o_con_filas_no_dict_es_error_de_respuesta(self):
        for cuerpo in ({"value": "x"}, {"value": None}, {"value": [1, 2]}):
            with mock.patch.object(ClienteZeus, "_autorizada", return_value=cuerpo):
                with self.assertRaises(ErrorRespuesta, msg=repr(cuerpo)):
                    self.cliente.consultar()

    def test_la_seleccion_detiene_la_corrida_con_motivo_en_vez_de_abortar(self):
        with mock.patch.object(ClienteZeus, "_autorizada", return_value={}):
            with self.assertRaises(ep001.DetenerEjecucion):
                ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)

    def test_fila_de_seleccion_sin_idradicado_detiene_la_corrida(self):
        with mock.patch.object(ClienteZeus, "_autorizada", return_value={"value": [{"PQRCORRESPONDEA": "x"}]}):
            with self.assertRaises(ep001.DetenerEjecucion):
                ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)

    def test_el_paso_del_robot_devuelve_fallo_no_excepcion(self):
        with mock.patch.dict("os.environ", {"ZEUS_DOBLE_CLIENT_ID": "cliente-de-prueba",
                                            "ZEUS_DOBLE_CLIENT_SECRET": "secreto-de-prueba-no-real"}):
            pasos.iniciar(str(self.tmp))
        with mock.patch.object(ClienteZeus, "_autorizada", return_value={}):
            resultado = pasos.consultar_odata("PQRCORRESPONDEA eq 'x'", "IDRADICADO")
        self.assertEqual((resultado["ok"], resultado["detenido"]), (False, True))


class TestConsultaGeneralMalformada(PruebaConDoble):
    def test_consulta_general_con_fila_sin_idradicado_detiene_igual_que_el_robot(self):
        """Hallazgo del verificador: la consulta general pasa por `ids_de` en el orquestador y en el paso del robot."""
        self.configurar_doble(radicados=[])
        general = [{"PQRCORRESPONDEA": "OTRA"}]
        original = self.cliente.consultar

        def consultar(**kw):
            return general if kw.get("filtro") is None else original(**kw)

        with mock.patch.object(self.cliente, "consultar", side_effect=consultar):
            resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertEqual(resumen["estado"], "detenido")
