"""HU-007: consultar la Procuraduría (clon: términos, formulario, captcha de pregunta rotativo, bloque «Datos del ciudadano»)."""
from tests.soporte_ep002 import PruebaIdentidad
from habeasdata import ep002
from habeasdata.captcha import MAX_REINTENTOS, SERVICIO_NO_DISPONIBLE
from habeasdata.portales import ErrorPortal

U = 0.80
NOMBRE = "MARIA FERNANDA LOPEZ RUIZ"


class TestHU007(PruebaIdentidad):
    def test_happy_nombre_y_estado_del_bloque_datos_del_ciudadano_en_la_misma_pagina(self):
        r = self.portales.consultar_procuraduria("1", "1000000001", NOMBRE, self.captchas)
        self.assertEqual((r["resultado"], r["nombre"], r["antecedentes"]), ("nombre", NOMBRE, False))

    def test_el_clon_rota_entre_las_cuatro_familias_y_el_bot_las_atiende_o_refresca(self):
        for _ in range(4):
            self.portales.consultar_procuraduria("1", "1000000001", NOMBRE, self.captchas)
        preguntas = " | ".join(self.web.estado.consultas["preguntas"])
        for familia in ("Cuánto es", "capital", "dígitos del documento", "primer nombre"):
            self.assertIn(familia, preguntas)

    def test_la_errata_real_del_portal_se_replica(self):
        self.configurar_web(familias=["capital"])
        with self.assertRaises(Exception):
            self.portales.consultar_procuraduria("1", "1000000001", NOMBRE, self.captchas)
        self.assertIn("Capital del Vallle del Cauca".lower(), " ".join(self.web.estado.consultas["preguntas"]).lower().replace("¿cuál es la ", ""))

    def test_pregunta_de_familia_no_soportada_se_trata_como_captcha_no_resuelto(self):
        self.configurar_web(familias=["capital"])
        from habeasdata.captcha import ErrorCaptcha
        with self.assertRaises(ErrorCaptcha) as ctx:
            self.portales.consultar_procuraduria("1", "1000000001", NOMBRE, self.captchas)
        self.assertEqual(ctx.exception.codigo, MAX_REINTENTOS)
        self.assertEqual(self.web.estado.consultas["procuraduria"], [])  # nunca se envió una respuesta inventada

    def test_error_captcha_no_resuelto_tras_n_intentos_es_excepcion_de_sistema_y_gestion_manual(self):
        self.configurar_web(captcha_rechaza=True)
        r = ep002.validar_identidad(self.caso(900013), self.portales, self.captchas, U)
        self.assertEqual((r["resultado"], r["codigo"]), ("excepcion_sistema", MAX_REINTENTOS))

    def test_error_servicio_de_captchas_caido_es_excepcion_de_sistema(self):
        self.servicio.configurar("no_disponible")
        r = ep002.validar_identidad(self.caso(900013), self.portales, self.captchas, U)
        self.assertEqual((r["resultado"], r["codigo"]), ("excepcion_sistema", SERVICIO_NO_DISPONIBLE))

    def test_error_portal_caido_agota_reintentos(self):
        self.configurar_web(procuraduria_modo="caido")
        with self.assertRaises(ErrorPortal):
            self.portales.consultar_procuraduria("1", "1000000001", NOMBRE, self.captchas)
        r = ep002.validar_identidad(self.caso(900013), self.portales, self.captchas, U)
        self.assertEqual((r["resultado"], r["codigo"]), ("excepcion_sistema", "PORTAL_NO_DISPONIBLE"))

    def test_realidad_waf_bloquea_la_pagina_principal(self):
        self.configurar_web(procuraduria_modo="waf")
        with self.assertRaises(ErrorPortal) as ctx:
            self.portales.consultar_procuraduria("1", "1000000001", NOMBRE, self.captchas)
        self.assertIn("WAF", str(ctx.exception))

    def test_realidad_webcert_devuelve_el_formulario_de_atencion_de_incidentes(self):
        self.configurar_web(procuraduria_modo="incidentes")
        with self.assertRaises(ErrorPortal) as ctx:
            self.portales.consultar_procuraduria("1", "1000000001", NOMBRE, self.captchas)
        self.assertIn("incidentes", str(ctx.exception))
        self.assertEqual(self.portales.verificar_url_procuraduria(), {"http": 200, "formulario_esperado": False, "incidentes": True})

    def test_la_verificacion_de_url_ve_el_formulario_cuando_es_el_esperado(self):
        self.assertEqual(self.portales.verificar_url_procuraduria(), {"http": 200, "formulario_esperado": True, "incidentes": False})

    def test_reborde_ciudadano_con_antecedentes_igual_se_extrae_el_nombre(self):
        self.configurar_web(procuraduria_padron={("1", "1000000001"): {"nombre": NOMBRE, "antecedentes": True}})
        r = self.portales.consultar_procuraduria("1", "1000000001", NOMBRE, self.captchas)
        self.assertEqual((r["nombre"], r["antecedentes"]), (NOMBRE, True))
        v = ep002.validar_identidad(self.caso(900001), self.portales, self.captchas, U)
        self.assertIn(v["resultado"], ("validada",))

    def test_reborde_respuesta_sin_nombre_para_no_cedula_se_registra_y_continua(self):
        self.configurar_web(procuraduria_padron={("2", "9000000013"): {"nombre": "X", "sin_nombre": True}})
        r = ep002.validar_identidad(self.caso(900013), self.portales, self.captchas, U)
        self.assertEqual(r["resultado"], "sin_nombre")

    def test_excepcion_nit_con_digitos_distintos_de_10_no_consulta(self):
        for numero in ("900000013", "90000000130", "900000001-3"):
            self.configurar_web(reiniciar=True)
            caso = dict(self.caso(900013), numero_identificacion=numero)
            r = ep002.validar_identidad(caso, self.portales, self.captchas, U)
            self.assertEqual(r["resultado"], "gestion_manual", numero)
            self.assertEqual(self.web.estado.consultas["procuraduria"], [], numero)

    def test_tipo_de_documento_sin_consulta_va_a_gestion_manual(self):
        caso = dict(self.caso(900001), tipo_identificacion="PEP")
        self.assertEqual(ep002.validar_identidad(caso, self.portales, self.captchas, U)["resultado"], "gestion_manual")
