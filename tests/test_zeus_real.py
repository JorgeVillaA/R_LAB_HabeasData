"""Cliente contra el contrato REAL de Zeus (manual 2026-10-07), sin ninguna llamada de red a CISA.

Las llamadas HTTP se interceptan: lo que se prueba es lo que el cliente ENVIARÍA a qaservices.cisa.gov.co y que
las salvaguardas del modo real bloquean cuando falta secreto, autorización o endpoint.
"""
import io
import json
import tempfile
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest import mock

from tests.soporte import REPO, RELOJ_FIJO
from habeasdata import ep001
from habeasdata.config import cargar
from habeasdata.redaccion import MASCARA, resumen_seguro
from habeasdata.registro import Registro
from habeasdata.zeus import ClienteZeus, ErrorBloqueo, ErrorNoAutenticado

QA_BASE = "https://qaservices.cisa.gov.co/habeasdata/api/CamposAdicionalesXRadicadoHabeasData"
QA_TOKEN = "https://qaservices.cisa.gov.co/sso/git_cisa/token"
ENTORNO_REAL = {"ZEUS_REAL_AUTORIZADO": "1", "ZEUS_CLIENT_SECRET": "secreto-ficticio-de-prueba"}


class Respuesta(io.BytesIO):
    def __init__(self, estado, cuerpo):
        super().__init__(json.dumps(cuerpo).encode("utf-8"))
        self.status = estado

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def error_http(url, codigo, cuerpo):
    return urllib.error.HTTPError(url, codigo, "x", {}, io.BytesIO(json.dumps(cuerpo).encode("utf-8")))


class BaseReal(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="lab_hd_real_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        (self.tmp / "Configuracion").mkdir()
        for nombre in ("ConfiguracionMaquina", "Maestro_Configuracion"):
            (self.tmp / "Configuracion" / f"{nombre}.json").write_text(
                (REPO / "Configuracion" / f"{nombre}.json").read_text(encoding="utf-8"), encoding="utf-8")
        proceso = json.loads((REPO / "Configuracion" / "ConfiguracionProceso.json").read_text(encoding="utf-8"))
        proceso["ZeusApi"]["Modo"] = "real"
        (self.tmp / "Configuracion" / "ConfiguracionProceso.json").write_text(json.dumps(proceso), encoding="utf-8")
        self.cfg = cargar(self.tmp)
        self.registro = Registro(self.cfg, RELOJ_FIJO)

    def cliente(self, entorno):
        return ClienteZeus(self.cfg, self.registro, entorno, dormir=lambda s: None)


class TestContratoReal(BaseReal):
    def test_urls_y_cliente_del_manual(self):
        real = self.cfg.proceso["ZeusApi"]["Real"]
        self.assertEqual((real["UrlBase"], real["UrlToken"]), (QA_BASE, QA_TOKEN))
        self.assertEqual(real["ClientId"], "app_dab_habeasdata")
        self.assertEqual(real["Ambiente"], "QA")

    def test_el_modo_por_defecto_del_repo_es_fixture(self):
        self.assertEqual(cargar(REPO).proceso["ZeusApi"]["Modo"], "fixture")

    def test_consultas_odata_como_en_el_manual(self):
        c = self.cliente(ENTORNO_REAL)
        decodificar = lambda url: urllib.parse.unquote(url)  # noqa: E731
        self.assertEqual(decodificar(c.url_consulta(filtro="PQRCORRESPONDEA eq 'EXCLUSION DE DATOS'")),
                         QA_BASE + "?$filter=PQRCORRESPONDEA eq 'EXCLUSION DE DATOS'")
        self.assertEqual(decodificar(c.url_consulta(first=25, orderby="IDRADICADO desc")),
                         QA_BASE + "?$first=25&$orderby=IDRADICADO desc")
        self.assertEqual(decodificar(c.url_consulta(select=("IDRADICADO", "PQRCORRESPONDEA"))),
                         QA_BASE + "?$select=IDRADICADO,PQRCORRESPONDEA")
        self.assertEqual(c.url_radicado(958797), QA_BASE + "/IDRADICADO/958797")
        self.assertEqual(c.url_consulta(), QA_BASE)

    def test_token_se_pide_como_client_credentials_y_se_renueva_ante_401(self):
        llamadas = []

        def falso(peticion, timeout=None):
            llamadas.append((peticion.get_method(), peticion.full_url, dict(peticion.header_items()), peticion.data))
            if peticion.full_url == QA_TOKEN:
                return Respuesta(200, {"access_token": f"tok{len([x for x in llamadas if x[1] == QA_TOKEN])}", "expires_in": 300})
            if len([x for x in llamadas if x[1] != QA_TOKEN]) == 1:
                raise error_http(peticion.full_url, 401, {})
            return Respuesta(200, {"value": [{"IDRADICADO": 1}]})

        with mock.patch("urllib.request.urlopen", falso):
            filas = self.cliente(ENTORNO_REAL).consultar(select=("IDRADICADO",))
        self.assertEqual(filas, [{"IDRADICADO": 1}])
        token1, dato1, token2 = llamadas[0], llamadas[1], llamadas[2]
        forma = dict(urllib.parse.parse_qsl(token1[3].decode()))
        self.assertEqual((token1[0], forma["grant_type"], forma["client_id"]), ("POST", "client_credentials", "app_dab_habeasdata"))
        self.assertEqual(token1[2]["Content-type"], "application/x-www-form-urlencoded")
        self.assertEqual(dato1[2]["Authorization"], "Bearer tok1")
        self.assertEqual(token2[1], QA_TOKEN)  # tras el 401 pidió un token nuevo
        self.assertEqual(llamadas[3][2]["Authorization"], "Bearer tok2")
        self.assertEqual(len(llamadas), 4)


class TestSalvaguardasReales(BaseReal):
    def sin_red(self):
        return mock.patch("urllib.request.urlopen", side_effect=AssertionError("no debe haber llamadas de red"))

    def test_sin_autorizacion_de_uso_no_hay_llamada(self):
        with self.sin_red():
            with self.assertRaises(ErrorBloqueo) as e:
                self.cliente({"ZEUS_CLIENT_SECRET": "x"}).consultar()
        self.assertIn("autorización de uso", str(e.exception))

    def test_sin_client_secret_no_hay_llamada(self):
        with self.sin_red():
            with self.assertRaises(ErrorBloqueo) as e:
                self.cliente({"ZEUS_REAL_AUTORIZADO": "1"}).consultar()
        self.assertIn("client_secret", str(e.exception))

    def test_el_endpoint_de_escritura_pendiente_se_reporta_no_se_inventa(self):
        with self.sin_red():
            with self.assertRaises(ErrorBloqueo) as e:
                self.cliente(ENTORNO_REAL).comentar("1", "x")
        self.assertIn("C-09", str(e.exception))

    def test_procesar_sin_secreto_se_detiene_con_bloqueo_explicito(self):
        with self.sin_red():
            resumen = ep001.procesar(self.cfg, self.cliente({"ZEUS_REAL_AUTORIZADO": "1"}), self.registro)
        self.assertEqual(resumen["estado"], "detenido")
        self.assertEqual(resumen["notificacion"]["asunto"], "Detenido")
        self.assertIn("BLOQUEO", resumen["notificacion"]["motivo"])
        self.assertIn("BLOQUEO", self.registro.ruta_errores().read_text(encoding="utf-8"))

    def test_un_modo_desconocido_se_rechaza(self):
        self.cfg.proceso["ZeusApi"]["Modo"] = "produccion"
        with self.assertRaises(ValueError):
            self.cliente(ENTORNO_REAL)


class TestRedaccionPII(BaseReal):
    CASO = {"nombre": "PERSONA REAL", "numero_identificacion": "1234567890", "correos": ["real@dominio.com"],
            "telefonos": [{"valor": "3101234567", "clase": "celular"}], "radicado_hijo": "958797"}

    def resumen(self):
        return {"estado": "ok", "avanzan": ["958797"], "casos": {"958797": dict(self.CASO)}, "notificacion": None}

    def test_en_modo_real_el_resumen_no_lleva_pii(self):
        texto = json.dumps(resumen_seguro(self.resumen(), self.cfg), ensure_ascii=False)
        for dato in ("PERSONA REAL", "1234567890", "real@dominio.com", "3101234567"):
            self.assertNotIn(dato, texto)
        self.assertIn("958797", texto)  # el radicado no es PII
        self.assertIn(MASCARA, texto)
        self.assertIn("celular", texto)

    def test_en_modo_fixture_el_resumen_queda_intacto(self):
        self.cfg.proceso["ZeusApi"]["Modo"] = "fixture"
        self.assertEqual(resumen_seguro(self.resumen(), self.cfg)["casos"]["958797"]["nombre"], "PERSONA REAL")

    def test_en_modo_real_los_logs_enmascaran_correos_y_numeros_largos(self):
        registro = Registro(self.cfg, RELOJ_FIJO)
        registro.auditoria("cliente real@dominio.com cédula 1234567890 tel 3101234567 radicado 958797")
        linea = registro.ruta_auditoria().read_text(encoding="utf-8").splitlines()[1]
        for dato in ("real@dominio.com", "1234567890", "3101234567"):
            self.assertNotIn(dato, linea)
        self.assertIn("958797", linea)
