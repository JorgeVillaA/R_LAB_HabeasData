"""HU-006: consultar la identidad en la Policía Nacional (clon con captcha de casilla, cuota agotada y caída)."""
import os
from unittest import mock

from tests.soporte_ep002 import PruebaIdentidad
from habeasdata import ep002
from habeasdata.portales import ClientePortales, ErrorBloqueoPortal, ErrorPortal, RevisionHumana

U = 0.80


class TestHU006(PruebaIdentidad):
    def test_happy_extrae_el_nombre_oficial_tras_apellidos_y_nombres(self):
        r = self.portales.consultar_policia("1000000001")
        self.assertEqual(r, {"resultado": "nombre", "nombre": "LOPEZ RUIZ MARIA FERNANDA"})  # apellidos y luego nombres

    def test_el_clon_replica_el_flujo_jsf_terminos_formulario_resultado(self):
        self.portales.consultar_policia("1000000001")
        consulta = self.web.estado.consultas["policia"][0]
        self.assertEqual(consulta, {"cedula": "1000000001", "recaptcha": True})

    def test_error_sin_resultado_marca_el_caso_para_la_procuraduria(self):
        self.assertEqual(self.portales.consultar_policia("1999999999")["resultado"], "sin_resultado")
        resultado = ep002.validar_identidad(dict(self.caso(900001), numero_identificacion="1000000001"), self.portales, self.captchas, U)
        self.assertEqual(resultado["via"], "policia")
        self.configurar_web(policia_padron={})  # la Policía no conoce al ciudadano: se consulta la Procuraduría
        resultado = ep002.validar_identidad(self.caso(900001), self.portales, self.captchas, U)
        self.assertEqual((resultado["resultado"], resultado["via"]), ("validada", "procuraduria"))

    def test_reborde_documento_no_cedula_omite_la_policia(self):
        self.configurar_web(reiniciar=True)
        resultado = ep002.validar_identidad(self.caso(900013), self.portales, self.captchas, U)  # NIT de 10 dígitos
        self.assertEqual(resultado["via"], "procuraduria")
        self.assertEqual(self.web.estado.consultas["policia"], [])

    def test_reborde_portal_caido_persistente_agota_reintentos_y_pasa_a_la_procuraduria(self):
        self.configurar_web(policia_modo="caido")
        with self.assertRaises(ErrorPortal):
            self.portales.consultar_policia("1000000001")
        resultado = ep002.validar_identidad(self.caso(900001), self.portales, self.captchas, U)
        self.assertEqual((resultado["resultado"], resultado["via"]), ("validada", "procuraduria"))

    def test_error_cuota_agotada_es_revision_humana_sin_resolver_ni_evadir_el_captcha(self):
        self.configurar_web(policia_modo="cuota")
        with self.assertRaises(RevisionHumana) as ctx:
            self.portales.consultar_policia("1000000001")
        self.assertIn("cuota", ctx.exception.motivo)
        resultado = ep002.validar_identidad(self.caso(900001), self.portales, self.captchas, U)
        self.assertEqual(resultado["resultado"], "revision_humana")
        self.assertTrue(all(not c["recaptcha"] for c in self.web.estado.consultas["policia"]))  # nunca marcó la casilla
        self.assertEqual(self.web.estado.consultas["procuraduria"], [])  # y no escaló a la Procuraduría

    def test_reto_de_imagenes_lo_resuelve_una_persona(self):
        self.configurar_web(policia_modo="reto")
        with self.assertRaises(RevisionHumana):
            self.portales.consultar_policia("1000000001")

    def test_modo_real_nunca_marca_la_casilla_y_se_detiene_para_la_persona(self):
        cfg = self.cfg
        cfg.proceso["Portales"]["Modo"] = "real"
        real = cfg.proceso["Portales"]["Real"]
        real["UrlPolicia"] = f"{self.web.url}/policia/WebJudicial/index.xhtml"  # clon: no se toca la red del Estado
        reloj = mock.Mock(return_value=mock.Mock(__format__=lambda s, f: "10:00"))
        portales = ClientePortales(cfg, {real["AutorizacionEnv"]: "1"}, ahora=reloj)
        with self.assertRaises(RevisionHumana) as ctx:
            portales.consultar_policia("1000000001")
        self.assertIn("persona", ctx.exception.motivo)
        self.assertEqual(self.web.estado.consultas["policia"], [])

    def test_modo_real_exige_autorizacion_y_ventana_operativa(self):
        self.cfg.proceso["Portales"]["Modo"] = "real"
        with self.assertRaises(ErrorBloqueoPortal) as ctx:
            ClientePortales(self.cfg, {})
        self.assertIn("autorización", str(ctx.exception))
        real = self.cfg.proceso["Portales"]["Real"]
        fuera = mock.Mock(return_value=mock.Mock(__format__=lambda s, f: "03:00"))
        with self.assertRaises(ErrorBloqueoPortal) as ctx:
            ClientePortales(self.cfg, {real["AutorizacionEnv"]: "1"}, ahora=fuera)
        self.assertIn("ventana operativa", str(ctx.exception))
