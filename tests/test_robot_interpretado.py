"""Las decisiones del robot de Studio (bloques visibles) se prueban sin Studio: el JSON del robot se ejecuta con el
intérprete de `banco/interprete_robot.py` y su resultado debe ser igual al del orquestador Python en los 16 escenarios.
Cierra el hallazgo del verificador adversarial: invertir una decisión en el robot debe romper la suite."""
import json
import os
import sys
import unittest
from unittest import mock

from tests.soporte import REPO, ENTORNO

for carpeta in (REPO / "banco",):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

import equivalencia_robot as eq  # noqa: E402

ESCENARIOS = json.loads((REPO / "banco" / "escenarios" / "EP-001.json").read_text(encoding="utf-8"))


class TestRobotInterpretado(unittest.TestCase):
    def test_robot_equivale_al_orquestador_en_cada_escenario(self):
        with mock.patch.dict(os.environ, ENTORNO):
            for esc in ESCENARIOS:
                with self.subTest(esc["id"]):
                    vista_py, vista_robot, _, capturadas = eq.escenario(esc, eq.ejecutar_robot_interpretado)
                    self.assertEqual(vista_py, vista_robot)  # incluye el motivo de la detención, no solo el asunto
                    self.assertEqual(capturadas, 0, "un trycatch tragó una excepción: el robot reventó en vez de decidir")

    def test_el_json_del_robot_coincide_con_su_generador(self):
        sys.path.insert(0, str(REPO / "Robots"))
        import generar_labhabeasdata as gen
        self.assertEqual(json.loads(json.dumps(gen.ROBOT)),
                         json.loads((REPO / "Robots" / "LabHabeasData.robot.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
