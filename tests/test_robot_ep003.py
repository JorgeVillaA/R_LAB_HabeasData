"""El robot de Studio (HU-010 y HU-011 con repositorio local) ejecutado sin Studio equivale al orquestador de referencia en cada
escenario de EP-003: mismas listas, mismo rastro (reporte, errores, auditoría, comentarios) y las mismas tablas y transacciones
del repositorio. La ejecución real en Chrome la verifica Studio (python banco/banco_ep002.py EP-003)."""
import json
import sys
import unittest

from tests.soporte import REPO

for carpeta in (REPO / "banco",):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

import banco_ep002 as b  # noqa: E402

ESCENARIOS = json.loads((REPO / "banco" / "escenarios" / "EP-003.json").read_text(encoding="utf-8"))


class TestRobotEP003(unittest.TestCase):
    def test_el_robot_equivale_al_orquestador_en_cada_escenario(self):
        for esc in ESCENARIOS:
            if esc.get("solo_orquestador"):
                continue
            with self.subTest(esc["id"]):
                resumen, comentarios, *_ = b.correr_escenario(esc)
                esperado = b.vista_de_resumen(resumen, comentarios)
                obtenido, capturadas = b.correr_escenario(esc, robot=True)
                self.assertEqual(obtenido, esperado)
                self.assertEqual(capturadas, 0)

    def test_la_deteccion_critica_se_prueba_en_el_orquestador(self):
        (esc,) = [e for e in ESCENARIOS if e.get("solo_orquestador")]
        resumen, comentarios, *_ = b.correr_escenario(esc)
        self.assertEqual(resumen["estado"], "detenido")
        self.assertEqual(resumen["notificacion"]["asunto"], "Detenido")
        self.assertEqual(resumen["validadas"], [])
        # el robot toma la misma decisión (el rastro difiere solo en la línea final «Fin de ejecución EP-001», por eso no se compara)
        vista, capturadas = b.correr_escenario(esc, robot=True)
        self.assertEqual((vista["estado"], vista["validadas"], vista["excepciones_sistema_repositorio"], capturadas),
                         ("detenido", [], ["900001"], 0))


if __name__ == "__main__":
    unittest.main()
