"""HU-026a: servicio de resolución de captchas (doble local): familias aritmética, documento y nombre; códigos de error."""
import unittest

from tests.soporte_ep002 import PruebaIdentidad
from dobles.portales import captchas as servicio
from habeasdata.captcha import ErrorCaptcha, MAX_REINTENTOS, SERVICIO_NO_DISPONIBLE, ServicioCaptchas


class TestFamiliasDelServicio(unittest.TestCase):
    """Tabla del happy path de la HU: la respuesta la calcula el servicio, no el bot."""

    def test_tabla_de_familias_de_la_historia(self):
        casos = [("¿Cuánto es 5 + 3?", None, None, "8"),
                 ("¿Cuánto es 4 X 3?", None, None, "12"),
                 ("¿Escriba los dos últimos dígitos del documento a consultar?", "12345687", None, "87"),
                 ("¿Escriba los tres primeros dígitos del documento a consultar?", "12345687", None, "123"),
                 ("¿Cuál es el primer nombre de la persona a la cual esta consultando?", None, "Juan Pérez", "Juan"),
                 ("¿Escriba la cantidad de letras del primer nombre de la persona a la cual esta consultando?", None, "Juan Pérez", "4")]
        for pregunta, documento, nombre, esperada in casos:
            with self.subTest(pregunta):
                self.assertEqual(servicio.resolver(pregunta, documento, nombre), (esperada, None))

    def test_reborde_familia_no_soportada_no_inventa_respuesta(self):
        for pregunta in ("¿Cuál es la capital de Colombia?", "¿Cuál es la capital del Vallle del Cauca?"):
            self.assertEqual(servicio.resolver(pregunta), (None, servicio.FAMILIA_NO_SOPORTADA))

    def test_dato_faltante_no_inventa_respuesta(self):
        self.assertEqual(servicio.resolver("¿Escriba los dos últimos dígitos del documento a consultar?"), (None, servicio.DATO_FALTANTE))
        self.assertEqual(servicio.resolver("¿Cuál es el primer nombre de la persona a la cual esta consultando?"),
                         (None, servicio.DATO_FALTANTE))


class TestClienteDelServicio(PruebaIdentidad):
    def test_happy_el_cliente_usa_la_respuesta_que_retorna_el_servicio(self):
        self.assertEqual(self.captchas.resolver("¿Cuánto es 5 + 3?"), "8")
        self.assertEqual(self.servicio.llamadas[-1]["pregunta"], "¿Cuánto es 5 + 3?")

    def test_el_documento_y_el_nombre_viajan_al_servicio_cuando_la_pregunta_los_requiere(self):
        self.captchas.resolver("¿Cuál es el primer nombre de la persona a la cual esta consultando?", "123", "Ana Mora")
        self.assertEqual((self.servicio.llamadas[-1]["documento"], self.servicio.llamadas[-1]["nombre"]), ("123", "Ana Mora"))

    def test_error_servicio_no_disponible_agota_reintentos_y_retorna_el_codigo(self):
        self.servicio.configurar("no_disponible")
        with self.assertRaises(ErrorCaptcha) as ctx:
            self.captchas.resolver("¿Cuánto es 5 + 3?")
        self.assertEqual(ctx.exception.codigo, SERVICIO_NO_DISPONIBLE)
        self.assertEqual(len(self.servicio.llamadas), 3)  # NUMERO_REINTENTOS_SISTEMA

    def test_familia_no_soportada_llega_como_error_sin_reintentar(self):
        with self.assertRaises(ErrorCaptcha) as ctx:
            self.captchas.resolver("¿Cuál es la capital de Colombia?")
        self.assertEqual(ctx.exception.codigo, servicio.FAMILIA_NO_SOPORTADA)
        self.assertEqual(len(self.servicio.llamadas), 1)

    def test_reborde_respuesta_rechazada_por_el_portal_en_cada_intento_es_max_reintentos(self):
        self.servicio.configurar("respuesta_erronea")
        self.configurar_web(familias=["aritmetica"])
        with self.assertRaises(ErrorCaptcha) as ctx:
            self.portales.consultar_procuraduria("1", "1000000001", "MARIA FERNANDA LOPEZ RUIZ", self.captchas)
        self.assertEqual(ctx.exception.codigo, MAX_REINTENTOS)
        self.assertEqual(len(self.web.estado.consultas["procuraduria"]), 3)  # N = 3

    def test_el_bot_no_calcula_la_respuesta(self):
        import inspect
        from habeasdata import portales
        fuente = inspect.getsource(portales)
        for prohibido in ("eval(", "int(a", "[-2:]", "split()[0]"):
            self.assertNotIn(prohibido, fuente)
