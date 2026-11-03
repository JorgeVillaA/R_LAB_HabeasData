"""Contrato del doble de la API de Zeus (manual de consumo, 2026-10-07): token, OData y códigos de error."""
import json
import urllib.error
import urllib.parse
import urllib.request

from tests.soporte import CLIENTE, SECRETO, PruebaConDoble
from campos import CAMPOS, CAMPOS_MANUAL

BASE = "/habeasdata/api/CamposAdicionalesXRadicadoHabeasData"


class PruebaDoble(PruebaConDoble):
    def llamar(self, metodo, ruta, cuerpo=None, token=None, tipo=None):
        cabeceras = {}
        if token:
            cabeceras["Authorization"] = f"Bearer {token}"
        if tipo:
            cabeceras["Content-Type"] = tipo
        peticion = urllib.request.Request(self.doble.url + ruta, data=cuerpo, method=metodo, headers=cabeceras)
        try:
            with urllib.request.urlopen(peticion, timeout=5) as r:
                return r.status, json.loads(r.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")

    def token(self, cliente=CLIENTE, secreto=SECRETO):
        forma = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": cliente,
                                        "client_secret": secreto}).encode()
        return self.llamar("POST", "/sso/git_cisa/token", forma, tipo="application/x-www-form-urlencoded")

    def get(self, consulta="", ruta=BASE):
        estado, cuerpo = self.token()
        self.assertEqual(estado, 200)
        sufijo = ("?" + urllib.parse.urlencode(consulta, quote_via=urllib.parse.quote)) if consulta else ""
        return self.llamar("GET", ruta + sufijo, token=cuerpo["access_token"])


class TestToken(PruebaDoble):
    def test_token_de_300_segundos_sin_refresh(self):
        estado, cuerpo = self.token()
        self.assertEqual(estado, 200)
        self.assertEqual(cuerpo["expires_in"], 300)
        self.assertEqual(cuerpo["refresh_expires_in"], 0)
        self.assertEqual(cuerpo["token_type"], "Bearer")

    def test_credenciales_invalidas_401(self):
        self.assertEqual(self.token(secreto="otro")[0], 401)

    def test_sin_token_401(self):
        self.assertEqual(self.llamar("GET", BASE)[0], 401)

    def test_token_expirado_401(self):
        self.configurar_doble(token_ttl=0)
        estado, cuerpo = self.token()
        self.assertEqual(self.llamar("GET", BASE, token=cuerpo["access_token"])[0], 401)

    def test_token_invalidado_401(self):
        _, cuerpo = self.token()
        self.configurar_doble(invalidar_tokens=True)
        self.assertEqual(self.llamar("GET", BASE, token=cuerpo["access_token"])[0], 401)

    def test_sin_roles_403(self):
        self.configurar_doble(denegar=True)
        self.assertEqual(self.get()[0], 403)


class TestOData(PruebaDoble):
    def test_consulta_general_devuelve_value(self):
        estado, cuerpo = self.get()
        self.assertEqual(estado, 200)
        self.assertEqual(len(cuerpo["value"]), len(self.doble.estado.radicados))

    def test_cada_registro_trae_los_campos_del_manual(self):
        self.assertEqual(len(CAMPOS_MANUAL), 51)
        _, cuerpo = self.get()
        for registro in cuerpo["value"]:
            self.assertEqual(set(registro), set(CAMPOS))

    def test_filter_eq_solo_exclusion(self):
        _, cuerpo = self.get({"$filter": "PQRCORRESPONDEA eq 'EXCLUSION DE DATOS'"})
        tipologias = {r["PQRCORRESPONDEA"] for r in cuerpo["value"]}
        self.assertEqual(tipologias, {"EXCLUSION DE DATOS"})
        self.assertEqual(len(cuerpo["value"]), len(self.doble.estado.radicados) - 1)

    def test_filter_compuesto_con_ne(self):
        _, cuerpo = self.get({"$filter": "PQRCORRESPONDEA eq 'EXCLUSION DE DATOS' and NOIDENTIFICACIONDELCLIENTE ne 'NO APORTA'"})
        self.assertTrue(all(r["NOIDENTIFICACIONDELCLIENTE"] != "NO APORTA" for r in cuerpo["value"]))
        self.assertNotIn(900011, [r["IDRADICADO"] for r in cuerpo["value"]])

    def test_select_proyecta_columnas(self):
        _, cuerpo = self.get({"$select": "IDRADICADO,NOMBREDELCLIENTE"})
        self.assertEqual(set(cuerpo["value"][0]), {"IDRADICADO", "NOMBREDELCLIENTE"})

    def test_first_y_orderby(self):
        _, cuerpo = self.get({"$first": "3", "$orderby": "IDRADICADO desc"})
        ids = [r["IDRADICADO"] for r in cuerpo["value"]]
        self.assertEqual(ids, sorted(ids, reverse=True))
        self.assertEqual(len(ids), 3)

    def test_campo_inexistente_400(self):
        self.assertEqual(self.get({"$filter": "NOEXISTE eq 'x'"})[0], 400)
        self.assertEqual(self.get({"$select": "NOEXISTE"})[0], 400)

    def test_sintaxis_mal_formada_400(self):
        self.assertEqual(self.get({"$filter": "PQRCORRESPONDEA igual 'x'"})[0], 400)
        self.assertEqual(self.get({"$first": "abc"})[0], 400)

    def test_parametro_no_soportado_400(self):
        self.assertEqual(self.get({"$expand": "x"})[0], 400)

    def test_individual_200_y_404(self):
        estado, cuerpo = self.get(ruta=BASE + "/IDRADICADO/900001")
        self.assertEqual(estado, 200)
        self.assertEqual(cuerpo["value"][0]["IDRADICADO"], 900001)
        self.assertEqual(self.get(ruta=BASE + "/IDRADICADO/1")[0], 404)

    def test_falla_inyectada_por_radicado(self):
        self.configurar_doble(fallas_radicado={"900001": 400})
        self.assertEqual(self.get(ruta=BASE + "/IDRADICADO/900001")[0], 400)

    def test_pagina_de_estado_html(self):
        with urllib.request.urlopen(self.doble.url + "/_doble/", timeout=5) as r:
            html = r.read().decode("utf-8")
        self.assertIn("Doble local de la API de Zeus", html)
        self.assertIn("id='radicados'", html)


class TestComentario(PruebaDoble):
    RUTA = "/habeasdata/api/GestionRadicado/Comentario"

    def publicar(self, cuerpo, con_token=True):
        token = self.token()[1]["access_token"] if con_token else None
        return self.llamar("POST", self.RUTA, json.dumps(cuerpo).encode(), token=token, tipo="application/json")

    def test_comentario_aceptado_201(self):
        estado, cuerpo = self.publicar({"IDRADICADO": "900002", "Detalle": "motivo"})
        self.assertEqual((estado, cuerpo["registrado"]), (201, True))
        self.assertEqual(self.doble.estado.comentarios, [{"IDRADICADO": "900002", "Detalle": "motivo"}])

    def test_errores_documentados(self):
        self.assertEqual(self.publicar({"IDRADICADO": "900002"})[0], 400)
        self.assertEqual(self.publicar({"IDRADICADO": "1", "Detalle": "x"})[0], 404)
        self.assertEqual(self.publicar({"IDRADICADO": "900002", "Detalle": "x"}, con_token=False)[0], 401)

    def test_falla_inyectada(self):
        self.configurar_doble(falla_comentario=400)
        self.assertEqual(self.publicar({"IDRADICADO": "900002", "Detalle": "x"})[0], 400)
