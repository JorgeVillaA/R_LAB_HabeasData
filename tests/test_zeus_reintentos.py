"""Hallazgos de la ronda 3 del verificador: reintentos ante 5xx, redacción de tokens y `$select` en el paso del robot."""
import os
import unittest
from unittest import mock

from tests.soporte import PruebaConDoble
from tests.test_pasos import PruebaPasos
from habeasdata import pasos, registro
from habeasdata.zeus import ErrorNoDisponible


class TestReintentosAnte5xx(PruebaConDoble):
    def test_un_503_se_reintenta_n_veces_y_se_registra_cada_reintento(self):
        self.configurar_doble(fallas_radicado={"900001": 503})
        self.cliente.renovar_token()
        with self.assertRaises(ErrorNoDisponible) as ctx:
            self.cliente.radicado("900001")
        self.assertIn("tras 3 reintentos", str(ctx.exception))
        log = self.texto_log(self.registro.ruta_auditoria())
        for n in (1, 2, 3):
            self.assertIn(f"Reintento {n}/3 de GET", log)
        self.assertIn("HTTP 503", log)

    def test_un_4xx_no_se_reintenta(self):
        self.configurar_doble(fallas_radicado={"900001": 400})
        self.cliente.renovar_token()
        with self.assertRaises(Exception):
            self.cliente.radicado("900001")
        self.assertNotIn("Reintento", self.texto_log(self.registro.ruta_auditoria()))


class TestRedaccionDeTokens(unittest.TestCase):
    def test_los_tokens_y_secretos_no_llegan_al_log(self):
        for texto, esperado in (("token=abc123", "token=***"), ("Bearer eyJhbGci.x.y", "Bearer ***"),
                                ("client_secret=zzz", "client_secret=***"), ("password=p", "password=***")):
            self.assertEqual(registro.limpiar(texto), esperado)
            self.assertNotIn("abc123", registro.limpiar(texto))


class TestSelectEnElPasoDelRobot(PruebaPasos):
    def test_la_consulta_del_robot_proyecta_solo_los_campos_pedidos(self):
        pasos.solicitar_token()
        with mock.patch.object(pasos._sesion.cliente, "consultar", wraps=pasos._sesion.cliente.consultar) as consultar:
            pasos.consultar_odata("PQRCORRESPONDEA eq 'EXCLUSION DE DATOS'", "IDRADICADO,PQRCORRESPONDEA", "3", "IDRADICADO desc")
        self.assertEqual(consultar.call_args.kwargs["select"], ("IDRADICADO", "PQRCORRESPONDEA"))
        self.assertEqual((consultar.call_args.kwargs["first"], consultar.call_args.kwargs["orderby"]), (3, "IDRADICADO desc"))


if __name__ == "__main__":
    unittest.main()
