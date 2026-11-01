"""El robot de Studio debe ser explicable a cliente: flujo visible por historia, no una caja negra de Python.

Referencia: los bots existentes (MainMonitoreoMarcas: trycatch «Control de ejecución» → grupos HUxx → trycatch
«Proceso principal»). El Python queda para E/S con secretos, parseo/clasificación puros y escritura de logs.
"""
import json
import re
import unittest

from tests.soporte import REPO
from habeasdata import ep001

ROBOT = json.loads((REPO / "Robots" / "LabHabeasData.robot.json").read_text(encoding="utf-8"))
VISUAL = json.loads((REPO / "Robots" / "VerificacionVisualDobles.robot.json").read_text(encoding="utf-8"))


def recorrer(comandos, profundidad=0):
    for comando in comandos or []:
        yield comando, profundidad
        yield from recorrer(comando.get("children"), profundidad + 1)
        yield from recorrer(comando.get("else"), profundidad + 1)


TODOS = [c for c, _ in recorrer(ROBOT["commands"])]
PYTHON = [c for c in TODOS if c["father"] == "execScriptPython"]
GRUPOS = [c["description"] for c in TODOS if c["father"] == "group"]


class TestEstructuraLegible(unittest.TestCase):
    def test_raiz_trycatch_control_de_ejecucion(self):
        raiz = ROBOT["commands"][0]
        self.assertEqual((raiz["father"], raiz["description"]), ("trycatch", "Control de ejecución"))
        self.assertTrue(raiz["else"], "el control de ejecución debe tener rama de excepción de sistema")

    def test_grupos_por_historia_con_inicializacion_y_cierre(self):
        esperados = [
            "HU002HU003HU004 - Inicializar el Asistente",
            "HU002 - Filtrar radicados de Exclusión de Datos",
            "HU003 - Leer datos paramétricos",
            "HU004 - Validar campos obligatorios",
            "HU006 - Consultar la Policía Nacional (Chrome)",
            "HU007 - Consultar la Procuraduría (Chrome)",
            "HU026a - Resolver el captcha de pregunta (servicio de captchas)",
            "HU008 - Comparar nombres (umbral 0.80, sin depender del orden)",
            "HU006HU007HU008 - Registrar el resultado de identidad",
            "HU002HU003HU004 - Cierre y registro de ejecución",
        ]
        self.assertEqual(GRUPOS, esperados)

    def test_proceso_principal_dentro_del_control(self):
        hijos = [(c["father"], c["description"]) for c in ROBOT["commands"][0]["children"]]
        self.assertEqual(hijos[1], ("trycatch", "Proceso principal"))

    def test_cada_bloque_lleva_descripcion(self):  # §6.1
        sin = [(c["father"], c.get("command", "")[:40]) for c in TODOS if not c.get("description", "").strip()]
        self.assertEqual(sin, [])

    def test_los_pasos_de_negocio_son_bloques_visibles(self):
        descripciones = " | ".join(c["description"] for c in TODOS)
        for paso in ("token OAuth", "filtro OData", "Consulta los radicados de exclusión", "Lee el radicado",
                     "Clasifica cada teléfono", "Falta el nombre del cliente", "comentario de la excepción de negocio 1"):
            self.assertIn(paso, descripciones, paso)

    def test_hay_mas_bloques_visibles_que_bloques_de_python(self):
        visibles = [c for c in TODOS if c["father"] not in ("execScriptPython",)]
        self.assertGreater(len(visibles), 2 * len(PYTHON))

    def test_el_flujo_tiene_decisiones_y_bucle_visibles(self):
        padres = [c["father"] for c in TODOS]
        self.assertGreaterEqual(padres.count("evaluateIf"), 15)
        self.assertEqual(padres.count("for"), 2)  # por radicado + intentos del captcha (HU-026a)

    def test_el_python_no_es_contenedor_del_flujo(self):
        for bloque in PYTHON:
            lineas = [l for l in bloque["command"].splitlines() if l.strip()]
            self.assertLessEqual(len(lineas), 12, bloque["description"])
            self.assertNotIn("procesar", bloque["command"], bloque["description"])
            self.assertNotIn("ep001", bloque["command"].replace("sys.modules", ""), bloque["description"])
            self.assertIsNone(re.search(r"(?m)^\s*(while|try)\b", bloque["command"]), bloque["description"])
            if not bloque["description"].startswith("Carga los tres JSON"):  # único bloque con un bucle: purga de módulos
                self.assertIsNone(re.search(r"(?m)^\s*(for|if)\b", bloque["command"]), bloque["description"])

    def test_el_python_solo_importa_los_pasos(self):
        permitidos = {"import sys", "import json", "from habeasdata import pasos"}
        for bloque in PYTHON:
            for linea in bloque["command"].splitlines():
                if linea.strip().startswith(("import ", "from ")):
                    self.assertIn(linea.strip(), permitidos, bloque["description"])

    def test_profundidad_bajo_el_for_maximo_dos_decisiones_anidadas(self):
        """Decisión de Villa: bajo el `for` por radicado, como máximo 2 niveles de control anidados (el grupo solo organiza)."""
        def maxima(comandos, nivel=0):
            mayor = nivel
            for c in comandos or []:
                sube = 1 if c["father"] in ("evaluateIf", "trycatch", "for") else 0
                mayor = max(mayor, maxima(c.get("children"), nivel + sube), maxima(c.get("else"), nivel + sube))
            return mayor
        bucle = next(c for c in TODOS if c["father"] == "for")
        self.assertLessEqual(maxima(bucle["children"]), 2)

    def test_los_contenedores_intermedios_viven_en_diccionarios_de_estado(self):
        nombres = {v["name"] for v in ROBOT["vars"]}
        self.assertIn("glbDicEstado", nombres)
        self.assertIn("locDicConsulta", nombres)
        for suelto in ("glbStrEstado", "glbStrMotivoSinCasos", "glbStrMotivoDetencion", "glbIntTotalRadicados", "locBlnLeido",
                       "locStrFiltroBase", "locStrFiltroSeleccion", "locStrSelect", "locIntLote", "locStrOrden"):
            self.assertNotIn(suelto, nombres)

    def test_tope_de_bloques_de_ep001_tras_consolidar(self):  # antes: 95 comandos, 47 setVar (EP-002 se mide aparte)
        ep002 = [c for c in ROBOT["commands"][0]["children"][1]["children"]
                 if c["father"] == "evaluateIf" or c["father"] == "group"]
        propios = [c for c, _ in recorrer(ROBOT["commands"])]
        grupos_ep002 = [g for g in TODOS if g["father"] == "group" and g["description"].split(" - ")[0] in
                        ("HU006", "HU007", "HU026a", "HU008", "HU006HU007HU008")]
        dentro = {id(x) for g in grupos_ep002 for x, _ in recorrer([g])}
        init_ep002 = 17  # listas, códigos, Chrome, portales y URLs de la inicialización + inicio y fin de la identidad
        ep001 = [c for c in propios if id(c) not in dentro]
        self.assertLessEqual(len(ep001), 84 + 9 + init_ep002)
        self.assertLessEqual([c["father"] for c in ep001].count("setVar"), 36 + 3 + 11)

    def test_los_motivos_de_incompletitud_coinciden_con_las_reglas_de_python(self):
        en_robot = []
        for comando in TODOS:
            if comando["father"] == "setVar" and comando["description"] == "Agrega el motivo":
                en_robot.append(re.search(r"\['([^']+)'\]$", comando["command"]).group(1))
        esperado = [etiqueta for _, etiqueta in ep001.OBLIGATORIOS] + ["SIN CANAL DE CONTACTO"]
        self.assertEqual(en_robot, esperado)

    def test_ninguna_ruta_ni_secreto_en_el_robot_exportado(self):
        variables = {v["name"]: v["data"] for v in ROBOT["vars"]}
        self.assertEqual(variables["glbStrRutaRaiz"], "")
        texto = json.dumps(ROBOT)
        self.assertNotRegex(texto, r"[A-Za-z]:[\\/]|client_secret|Bearer ")

    def test_los_pasos_llaman_a_los_pasos_documentados(self):
        from habeasdata import pasos
        usados = set(re.findall(r"pasos\.(\w+)\(", " ".join(c["command"] for c in PYTHON)))
        self.assertTrue(usados)
        for nombre in usados:
            self.assertTrue(callable(getattr(pasos, nombre)), nombre)


class TestChromeEnBloquesWeb(unittest.TestCase):
    def test_openbrowser_chrome_con_extra_default_y_openurl_aparte(self):
        todos = [c for c, _ in recorrer(VISUAL["commands"])]
        abrir = [c for c in todos if c["father"] == "openbrowser"]
        self.assertEqual(len(abrir), 1)
        self.assertEqual(abrir[0]["option"], "chrome")
        self.assertEqual(abrir[0]["extra"], {"default": "chrome"})
        padres = [c["father"] for c in todos]
        self.assertGreater(padres.index("openUrl"), padres.index("openbrowser"))
        self.assertTrue({c["father"] for c in todos}.isdisjoint({"use", "startfile"}))  # nada fuera de Chrome


if __name__ == "__main__":
    unittest.main()
