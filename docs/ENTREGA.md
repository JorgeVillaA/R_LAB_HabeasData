# Entrega del lab R_LAB_HabeasData (2026-11-01)

Producto: este repositorio, con el robot de Rocketbot Studio **dentro** (`studio/R_LAB_HabeasData/robot.db`) y todo lo necesario para
abrirlo, correrlo y verificarlo. Instrucciones de uso: `README.md`.

## Estado por épica
| Épica | Rama | Código y pruebas | Studio + Chrome | Verificación adversarial | Cierre |
|---|---|---|---|---|---|
| EP-001 (HU-002/003/004) | `feature/EP-001` | 166 tests, banco 18 × 2 | 18/18 IGUAL | CERRABLE (ronda 7) | change archivado, PR preparada (`docs/PR/EP-001.md`) |
| EP-002 (HU-006/007/008/026a) | `feature/EP-002` | banco 20 × 2 | 20/20 IGUAL | ver `docs/PR/EP-002.md` | PR preparada (incluye EP-001 y EP-003 en la misma rama) |
| EP-003 (HU-010/011) | `feature/EP-002` | banco 9 × 2 | 8/8 IGUAL + 1 omitido (solo orquestador) | ver `docs/PR/EP-003.md` | change `ep-003-exclusion-en-repositorio` listo para archivar |

Suite completa: `python -m unittest discover -s tests -t .` → 248 tests OK. `validate_robot` perfil trycore: 0 errores, 0 avisos.
Mapa de salud por bloque (`docs/SALUD-POR-BLOQUE.md`): 9 bloques sin escenario (ramas de error que ningún escenario provoca), reportados, no ocultos.

## Qué se corrigió en esta ronda para que el robot funcione en Chrome REAL
La evidencia anterior de EP-002 («20/20 en Studio») no ejercitaba la identidad (`equivalencia_robot.py` la deja deshabilitada). La prueba real
(`banco/banco_ep002.py`) daba 4/20. Causas y arreglos (todos en `dobles/portales/servidor.py`, sin tocar el HTML de los clones):
`onsubmit` de la Procuraduría llamaba a una función no servida; los recursos inexistentes reiniciaban la sesión del portal; `ui-state-disabled`
anulaba el clic de «Continuar»; el panel de texto de la Policía tapaba el radio; el bloque de resultado de la Procuraduría existía vacío y el robot
leía la página anterior. Una de las 20 pruebas falló una vez (corrida 1 = 19/20) y no se reprodujo (corrida 2 = 20/20 y la corrida de cierre 20/20).

## Qué NO se verificó / límites
- Todo contra dobles y clones locales. La API real de QA de CISA, Cobra y los portales reales no se tocaron. El endpoint de escritura del comentario es un supuesto (C-09).
- El repositorio es SQLite con el contrato de `specs/repositorio-local.md`; **NocoDB npm 0.301.3 (D-07) no se instaló** (queda como camino documentado).
- La descripción del robot en Studio se actualizó (mención a EP-003) después de las corridas de Studio; el flujo es idéntico.
- `Transacciones`: las etapas previas (selección, lectura, completitud) se anotan al llegar a HU-010, no en el instante de cada una.
- El tope diario de reintentos de HU-002 se cuenta por ejecución y la espera bloquea el robot (3 × 60 min por defecto).
- Un escenario de EP-003 (detención crítica por repositorio inaccesible) solo se compara en decisiones: la línea final del log difiere entre robot y orquestador.

## Pendiente de Villa
1. `git push` de `feature/EP-001` y `feature/EP-002` (el agente no empuja) y abrir las PR con `docs/PR/*.md`.
2. Decidir: tope diario de reintentos (por día o por ejecución), maestras `MaestraCelulares`/`MaestraCorreos` (C-16), tratamiento del teléfono fijo en HU-011, instalar NocoDB o aceptar SQLite.
3. Revisar la evidencia visual en Chrome (capturas en `banco/evidencia/`).
