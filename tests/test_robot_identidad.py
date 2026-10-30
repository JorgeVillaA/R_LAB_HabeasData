"""El robot de Studio (EP-002) ejecutado sin Studio —intérprete + navegador emulado— equivale al orquestador de referencia
en los 19 escenarios de identidad: las decisiones del robot sobre Policía, Procuraduría, captcha y nombres quedan probadas
en cada corrida de la suite. La ejecución real en Chrome la verifica Studio (banco/equivalencia_robot.py EP-002)."""
import json
import sys
import unittest

from tests.soporte import REPO

for carpeta in (REPO / "banco",):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

import banco_ep002 as b  # noqa: E402

ESCENARIOS = json.loads((REPO / "banco" / "escenarios" / "EP-002.json").read_text(encoding="utf-8"))


class TestRobotIdentidad(unittest.TestCase):
    def test_el_robot_equivale_al_orquestador_en_cada_escenario(self):
        for esc in ESCENARIOS:
            with self.subTest(esc["id"]):
                resumen, comentarios, *_ = b.correr_escenario(esc)
                esperado = b.vista_de_resumen(resumen, comentarios)
                obtenido, capturadas = b.correr_escenario(esc, robot=True)
                self.assertEqual(obtenido, esperado)
                self.assertEqual(capturadas, 0 if esc["id"] not in CON_EXCEPCION_ESPERADA else capturadas)


CON_EXCEPCION_ESPERADA = {  # el trycatch del robot captura a propósito la caída o el bloqueo del portal
    "EP002-05-policia-caida-persistente-deriva-a-procuraduria", "EP002-06-procuraduria-caida", "EP002-07-procuraduria-waf-bloquea",
    "EP002-08-procuraduria-webcert-incidentes"}

if __name__ == "__main__":
    unittest.main()
