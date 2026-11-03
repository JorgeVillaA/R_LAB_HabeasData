"""Genera banco/escenarios/EP-002.json (la matriz de identidad). Uso: python banco/escenarios/generar_ep002.py"""
import json
from pathlib import Path

TODOS = ["900001", "900003", "900004", "900005", "900006", "900007", "900008", "900013", "900014", "900016"]
CEDULAS = [i for i in TODOS if i != "900013"]


def esc(id_, ramas, radicados, espera, portales=None, servicio=None, doble=None):
    resultado = {"id": f"EP002-{id_}", "ramas": ramas, "doble": {"radicados": radicados, **(doble or {})},
                 "portales": portales or {}, "espera": {"identidad": True, "estado": "ok", **espera}}
    if servicio:
        resultado["servicio"] = servicio
    return resultado


ESCENARIOS = [
    esc("01-happy-todos", ["HU-006 nombre extraído", "HU-007 NIT por Procuraduría", "HU-008 coincide (incluye orden distinto)", "HU-026a familias"],
        TODOS, {"validadas": TODOS, "vias": {"900001": "policia", "900013": "procuraduria"}, "casilla_nunca_marcada": False}),
    esc("02-policia-sin-resultado-deriva-a-procuraduria", ["HU-006 sin resultado → HU-007"], TODOS,
        {"validadas": TODOS, "vias": {"900001": "procuraduria"}}, {"vaciar_policia": True}),
    esc("03-policia-cuota-agotada-revision-humana", ["HU-006 cuota agotada: fallback humano"], TODOS,
        {"revision_humana": CEDULAS, "validadas": ["900013"], "casilla_nunca_marcada": True}, {"policia_modo": "cuota"}),
    esc("04-policia-reto-de-imagenes-revision-humana", ["HU-006 reCAPTCHA escala a reto: persona"], TODOS,
        {"revision_humana": CEDULAS, "validadas": ["900013"]}, {"policia_modo": "reto"}),
    esc("05-policia-caida-persistente-deriva-a-procuraduria", ["HU-006 portal caído → HU-007"], TODOS,
        {"validadas": TODOS, "vias": {"900001": "procuraduria"}}, {"policia_modo": "caido"}),
    esc("06-procuraduria-caida", ["HU-007 portal caído: excepción de sistema y gestión manual"], ["900001", "900013"],
        {"gestion_manual": ["900001", "900013"], "excepciones_sistema_identidad": ["900001", "900013"],
         "codigos": {"900001": "PORTAL_NO_DISPONIBLE", "900013": "PORTAL_NO_DISPONIBLE"}},
        {"procuraduria_modo": "caido", "vaciar_policia": True}),
    esc("07-procuraduria-waf-bloquea", ["Realidad: WAF bloquea la página principal"], ["900001", "900013"],
        {"validadas": ["900001"], "gestion_manual": ["900013"], "excepciones_sistema_identidad": ["900013"],
         "codigos": {"900013": "PORTAL_NO_DISPONIBLE"}}, {"procuraduria_modo": "waf"}),
    esc("08-procuraduria-webcert-incidentes", ["Realidad: webcert devuelve el formulario de atención de incidentes"], ["900001", "900013"],
        {"validadas": ["900001"], "gestion_manual": ["900013"], "excepciones_sistema_identidad": ["900013"],
         "codigos": {"900013": "PORTAL_NO_DISPONIBLE"}}, {"procuraduria_modo": "incidentes"}),
    esc("09-captcha-rechazado-por-el-portal", ["HU-026a reintentos agotados: CAPTCHA_MAX_REINTENTOS"], ["900013"],
        {"gestion_manual": ["900013"], "excepciones_sistema_identidad": ["900013"], "codigos": {"900013": "CAPTCHA_MAX_REINTENTOS"}},
        {"captcha_rechaza": True}),
    esc("10-servicio-de-captchas-no-disponible", ["HU-026a servicio caído: CAPTCHA_SERVICIO_NO_DISPONIBLE"], ["900013"],
        {"gestion_manual": ["900013"], "excepciones_sistema_identidad": ["900013"], "codigos": {"900013": "CAPTCHA_SERVICIO_NO_DISPONIBLE"}},
        servicio="no_disponible"),
    esc("11-familia-no-soportada-capital", ["HU-026a familia no soportada → captcha no resuelto"], ["900013"],
        {"gestion_manual": ["900013"], "excepciones_sistema_identidad": ["900013"], "codigos": {"900013": "CAPTCHA_MAX_REINTENTOS"}},
        {"familias": ["capital"]}),
    esc("12-rotacion-de-familias", ["HU-026a aritmética, documento y nombre rotan; capital se refresca"],
        ["900001", "900003", "900004", "900005"], {"validadas": ["900001", "900003", "900004", "900005"]}, {"vaciar_policia": True}),
    esc("13-nombre-no-coincide-excepcion-3", ["HU-008 excepción de negocio 3 con comentario"], ["900001"],
        {"excepciones_negocio_3": ["900001"], "comentarios": ["900001"]}, {"padron_policia": {"1000000001": "RAMIREZ DIAZ CARLOS"}}),
    esc("14-nombre-incompleto-excepcion-3", ["HU-008 sin primer apellido"], ["900001"],
        {"excepciones_negocio_3": ["900001"], "comentarios": ["900001"]}, {"padron_policia": {"1000000001": "MARIA"}}),
    esc("15-comentario-3-rechazado", ["HU-008 comentario no registrado: excepción de sistema"], ["900001"],
        {"excepciones_sistema_identidad": ["900001"], "gestion_manual": ["900001"], "codigos": {"900001": "COMENTARIO_NO_REGISTRADO"},
         "comentarios": []},
        {"padron_policia": {"1000000001": "RAMIREZ DIAZ CARLOS"}}, doble={"falla_comentario": 400}),
    esc("16-nit-con-9-digitos-no-consulta", ["HU-007 NIT ≠ 10 dígitos → gestión manual sin consultar"], ["900013"],
        {"gestion_manual": ["900013"], "excepciones_sistema_identidad": [], "consultas_maximas": {"procuraduria": 0, "policia": 0}},
        doble={"campos": {"900013": {"NOIDENTIFICACIONDELCLIENTE": "900000013"}}}),
    esc("17-no-cedula-sin-nombre-continua", ["HU-007 respuesta sin nombre, no cédula: registra y continúa"], ["900013", "900001"],
        {"sin_nombre": ["900013"], "validadas": ["900001"]}, {"sin_nombre": [["2", "9000000013"]]}),
    esc("18-tipo-de-documento-sin-consulta", ["Realidad: PEP no tiene consulta en la Procuraduría"], ["900013"],
        {"gestion_manual": ["900013"], "consultas_maximas": {"procuraduria": 0}},
        doble={"campos": {"900013": {"TIPODEIDENTIFICACION": "PEP"}}}),
    esc("20-cedula-sin-resultado-en-ninguna-fuente", ["HU-007 cédula sin resultado en Policía ni Procuraduría → gestión manual"], ["900001"],
        {"gestion_manual": ["900001"], "excepciones_sistema_identidad": []},
        {"vaciar_policia": True, "sin_nombre": [["1", "1000000001"]]}),
    esc("19-ciudadano-con-antecedentes-igual-valida", ["HU-007 con antecedentes: el estado no altera la identidad"], ["900001"],
        {"validadas": ["900001"]}, {"vaciar_policia": True, "con_antecedentes": [["1", "1000000001"]]}),
]

if __name__ == "__main__":
    destino = Path(__file__).resolve().parents[1] / "escenarios" / "EP-002.json"
    destino.write_text(json.dumps(ESCENARIOS, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{destino.name}: {len(ESCENARIOS)} escenarios")
