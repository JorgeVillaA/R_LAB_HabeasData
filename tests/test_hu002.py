"""HU-002 — Filtrar radicados de Exclusión de Datos (un test por escenario de la HU)."""
from tests.soporte import PruebaConDoble, RADICADOS
from habeasdata import ep001


class TestHU002(PruebaConDoble):
    def test_happy_path_radicados_filtrados_sin_ajenos(self):  # AC: radicados filtrados
        lista = ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)
        esperados = [str(r["IDRADICADO"]) for r in RADICADOS
                     if r["PQRCORRESPONDEA"] == "EXCLUSION DE DATOS" and r["NOIDENTIFICACIONDELCLIENTE"] != "NO APORTA"]
        self.assertEqual(sorted(lista["ids"]), sorted(esperados))
        self.assertNotIn("900012", lista["ids"])  # tipología ajena
        self.assertNotIn("900011", lista["ids"])  # identificación ausente: el filtro compuesto la descarta
        self.assertEqual(lista["descartados"], ["900011"])  # ... pero queda contada, no se pierde en silencio
        self.assertIsNone(lista["motivo_sin_casos"])
        self.assertIsNone(lista["reintento"])

    def test_error_filtro_o_campo_no_reconocido_detiene(self):  # AC: 400
        self.cfg.proceso["Negocio"]["CampoTipologia"] = "CAMPOINEXISTENTE"
        with self.assertRaises(ep001.DetenerEjecucion) as contexto:
            ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)
        self.assertIn("no reconocido", str(contexto.exception))

    def test_error_token_ausente_o_vencido_detiene(self):  # AC: 401 persistente
        self.configurar_doble(token_ttl=0)
        with self.assertRaises(ep001.DetenerEjecucion) as contexto:
            ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)
        self.assertIn("token", str(contexto.exception))

    def test_token_vencido_se_renueva_una_vez(self):  # contrato del manual: nuevo token ante 401
        self.cliente.renovar_token()
        self.configurar_doble(invalidar_tokens=True)
        lista = ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)
        self.assertTrue(lista["ids"])
        self.assertEqual(self.doble.estado.contadores["tokens"], 2)

    def test_error_tipologia_ausente_solo_radicados_ajenos(self):  # AC: tipología ausente (C-13)
        ajenos = [dict(r, PQRCORRESPONDEA="HABEAS DATA - NO APLICA") for r in RADICADOS[:3]]
        self.configurar_doble(radicados=ajenos)
        lista = ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)
        self.assertEqual(lista["ids"], [])
        self.assertEqual(lista["motivo_sin_casos"], "tipologia_ausente")
        self.assertEqual(lista["reintento"]["MinutosEntreReintentos"], 60)
        self.assertIn("0 casos (tipologia_ausente)", self.texto_log(self.registro.ruta_auditoria()))
        self.assertIn("0 casos", self.texto_log(self.registro.ruta_reporte()))

    def test_reborde_bandeja_vacia(self):  # AC: bandeja vacía (C-13)
        self.configurar_doble(radicados=[])
        lista = ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)
        self.assertEqual((lista["ids"], lista["motivo_sin_casos"]), ([], "bandeja_vacia"))
        self.assertEqual(lista["reintento"], self.cfg.proceso["CADENCIA_REINTENTO_BANDEJA_VACIA"])

    def test_cadencia_es_parametro_no_logica(self):
        self.configurar_doble(radicados=[])
        self.cfg.proceso["CADENCIA_REINTENTO_BANDEJA_VACIA"]["MinutosEntreReintentos"] = 15
        lista = ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)
        self.assertEqual(lista["reintento"]["MinutosEntreReintentos"], 15)

    def test_seleccion_con_lote_y_orden_descendente(self):  # contrato QA: $first + $orderby=IDRADICADO desc
        self.cfg.proceso["SeleccionRadicados"]["LoteMaximo"] = 3
        lista = ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)
        self.assertEqual(lista["ids"], ["900016", "900015", "900014"])

    def test_sin_descartar_identificacion_ausente_el_radicado_entra_a_la_lista(self):
        self.cfg.proceso["SeleccionRadicados"]["DescartarIdentificacionAusente"] = False
        lista = ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)
        self.assertIn("900011", lista["ids"])
        self.assertEqual(lista["descartados"] if "descartados" in lista else [], [])

    def test_los_descartados_quedan_en_auditoria_y_reporte(self):
        resumen = ep001.procesar(self.cfg, self.cliente, self.registro)
        self.assertEqual(resumen["descartados_identificacion_ausente"], ["900011"])
        self.assertIn("900011 descartado por identificación ausente", self.texto_log(self.registro.ruta_auditoria()))
        self.assertIn(";900011;NO APLICA;descartado: identificación ausente", self.texto_log(self.registro.ruta_reporte()))
        self.assertNotIn("900011", resumen["casos"])  # el bot no lo gestiona

    def test_solo_descartados_no_es_bandeja_vacia(self):
        solo = [dict(r, NOIDENTIFICACIONDELCLIENTE="NO APORTA") for r in RADICADOS[:2]]
        self.configurar_doble(radicados=solo)
        lista = ep001.filtrar_exclusion(self.cliente, self.cfg, self.registro)
        self.assertEqual((lista["ids"], lista["motivo_sin_casos"]), ([], "solo_descartados"))
