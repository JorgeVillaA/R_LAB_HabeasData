"""HU-004 — Validar existencia de campos obligatorios (un test por escenario de la HU)."""
from tests.soporte import PruebaConDoble
from habeasdata import ep001


class TestHU004(PruebaConDoble):
    def validar(self, id_radicado):
        caso = ep001.extraer(self.cliente, self.cfg, id_radicado)
        return caso, ep001.validar_completitud(caso)

    def test_happy_path_datos_completos_avanza_sin_comentario(self):
        _, veredicto = self.validar("900001")
        self.assertTrue(veredicto["completo"])
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertIn("900001", resumen["avanzan"])
        self.assertNotIn("900001", [c["IDRADICADO"] for c in self.doble.estado.comentarios])

    def test_basta_un_canal_correo_o_telefono(self):
        for id_radicado in ("900003", "900004", "900005", "900006"):
            self.assertTrue(self.validar(id_radicado)[1]["completo"], id_radicado)

    def test_error_identificacion_incompleta_tipo(self):
        _, veredicto = self.validar("900010")
        self.assertEqual(veredicto["motivos"], ["TIPO DE IDENTIFICACION"])

    def test_error_identificacion_incompleta_numero(self):
        self.assertEqual(self.validar("900011")[1]["motivos"], ["NUMERO DE IDENTIFICACION"])

    def test_error_sin_ningun_canal_de_contacto(self):
        self.assertEqual(self.validar("900002")[1]["motivos"], ["SIN CANAL DE CONTACTO"])

    def test_reborde_campo_vacio_solo_espacios_cuenta_como_ausente(self):
        self.assertEqual(self.validar("900009")[1]["motivos"], ["NOMBRE DEL CLIENTE"])

    def test_reborde_literal_no_aporta_cuenta_como_ausente(self):
        _, veredicto = self.validar("900011")  # NO APORTA en el número
        self.assertFalse(veredicto["completo"])
        caso, veredicto = self.validar("900015")  # canales en NO APORTA y heredados ignorados
        self.assertEqual(veredicto["motivos"], ["SIN CANAL DE CONTACTO"])

    def test_excepcion_de_negocio_1_deja_comentario_en_gestion_detalle(self):
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        con_comentario = {c["IDRADICADO"]: c["Detalle"] for c in self.doble.estado.comentarios}
        self.assertEqual(sorted(resumen["excepciones_negocio_1"]), sorted(con_comentario))
        self.assertEqual(sorted(con_comentario), ["900002", "900009", "900010", "900011", "900015"])
        self.assertIn("SIN CANAL DE CONTACTO", con_comentario["900002"])
        self.assertIn("Excepción de negocio 1", con_comentario["900009"])

    def test_error_escritura_rechazada_es_excepcion_de_sistema_y_continua(self):
        self.configurar_doble(falla_comentario=400)
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertEqual(resumen["excepciones_negocio_1"], [])
        self.assertIn("900002", resumen["excepciones_sistema"])
        self.assertIn("900001", resumen["avanzan"])
        self.assertIn("no se pudo registrar el comentario", self.texto_log(self.registro.ruta_errores()))

    def test_error_escritura_sin_autorizacion(self):
        self.configurar_doble(falla_comentario=401)
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertIn("900002", resumen["excepciones_sistema"])

    def test_caso_incompleto_no_avanza(self):
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertTrue(set(resumen["avanzan"]).isdisjoint(resumen["excepciones_negocio_1"]))
        self.assertNotIn("900012", resumen["avanzan"])  # tipología ajena: ni se procesa
        self.assertNotIn("900012", resumen["casos"])

    def test_ejecucion_completa_deja_logs_y_reporte(self):
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertEqual(resumen["estado"], "ok")
        auditoria = self.texto_log(self.registro.ruta_auditoria())
        for hito in ("Inicio de ejecución EP-001", "Ingreso a la API de Zeus", "Inicio del radicado 900001",
                     "Fin de ejecución EP-001"):
            self.assertIn(hito, auditoria)
        reporte = self.texto_log(self.registro.ruta_reporte())
        self.assertIn(";900008;800001;avanza", reporte)  # hijo y padre en el reporte

    def test_ejecucion_detenida_por_token_notifica_detenido(self):
        self.configurar_doble(token_ttl=0)
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertEqual(resumen["estado"], "detenido")
        self.assertEqual(resumen["notificacion"]["asunto"], "Detenido")
        self.assertIn("Ejecución detenida", self.texto_log(self.registro.ruta_errores()))
