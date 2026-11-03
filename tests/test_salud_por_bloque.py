"""D-21: el mapa de salud por bloque existe, cubre todos los bloques del robot y declara sus huecos."""
import json
import re
import unittest

from tests.soporte import REPO

ROBOT = json.loads((REPO / "Robots" / "LabHabeasData.robot.json").read_text(encoding="utf-8"))
MAPA = (REPO / "docs" / "SALUD-POR-BLOQUE.md").read_text(encoding="utf-8")


def contar(comandos):
    return sum(1 + contar(c.get("children")) + contar(c.get("else")) for c in comandos or [])


class TestSaludPorBloque(unittest.TestCase):
    def test_el_mapa_lista_todos_los_bloques_del_robot(self):
        filas = re.findall(r"^\| (\d[\d.e]*) \| [^|]+ \| ", MAPA.split("## Mapa")[1], re.M)
        self.assertEqual(len(filas), contar(ROBOT["commands"]))

    def test_el_resumen_declara_los_huecos_y_coinciden_con_la_tabla(self):
        declarados = int(re.search(r"sin cubrir: (\d+)", MAPA).group(1))
        en_mapa = MAPA.split("## Mapa")[1].count("**sin cubrir**")
        self.assertEqual(declarados, en_mapa)

    def test_todo_paso_de_componente_recibe_la_raiz_para_no_depender_de_estado_oculto(self):
        def python(comandos):
            for c in comandos or []:
                if c["father"] == "execScriptPython":
                    yield c
                yield from python(c.get("children"))
                yield from python(c.get("else"))
        sin_raiz = [c["description"] for c in python(ROBOT["commands"])
                    if "pasos.asegurar(GetVar('glbStrRutaRaiz'))" not in c["command"] and "pasos.iniciar(" not in c["command"]]
        self.assertEqual(sin_raiz, [])


if __name__ == "__main__":
    unittest.main()


class TestBloqueAislado(unittest.TestCase):
    def test_un_paso_corre_solo_sin_que_otro_haya_abierto_la_sesion(self):
        import os
        import shutil
        import tempfile
        from pathlib import Path
        from unittest import mock
        from tests.soporte import CLIENTE, SECRETO, RADICADOS, copiar_config
        from dobles.zeus_api.servidor import DobleZeus
        from habeasdata import pasos
        doble = DobleZeus((CLIENTE, SECRETO), list(RADICADOS)).iniciar()
        self.addCleanup(doble.detener)
        raiz = Path(tempfile.mkdtemp(prefix="lab_bloque_"))
        self.addCleanup(shutil.rmtree, raiz, ignore_errors=True)
        copiar_config(raiz, doble.puerto)
        pasos._sesion._real, pasos._sesion.raiz = None, None  # proceso nuevo: ningún bloque corrió antes
        with mock.patch.dict(os.environ, {"ZEUS_DOBLE_CLIENT_ID": CLIENTE, "ZEUS_DOBLE_CLIENT_SECRET": SECRETO}):
            with self.assertRaises(RuntimeError):  # sin la raíz explícita, el paso lo dice en vez de usar estado oculto
                pasos.parametros()
            pasos.asegurar(str(raiz))
            self.assertEqual(pasos.parametros()["negocio"]["TipologiaExclusion"], "EXCLUSION DE DATOS")
            self.assertTrue(pasos.solicitar_token()["ok"])
