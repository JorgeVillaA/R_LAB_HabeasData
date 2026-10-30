# EP-001 — Verificación de la ronda 5 (independiente)

**Fecha:** 30/10/2026 · **Verificador:** agente (ronda 5, adversarial) · **Rama:** `feature/EP-001` · **HEAD:** `0959135`
**Cableado declarado:** sha `11b5619` (ancestro de HEAD, comprobado con `git merge-base --is-ancestor`).

## Qué se ejecutó en esta ronda

| Comprobación | Comando | Resultado |
|---|---|---|
| Suite completa | `python -m unittest discover -s tests -t .` | **155 pruebas OK** (104 s) |
| Banco determinista EP-001 ×2 | `python banco/correr_matriz.py EP-001 --corridas 2` | Reproducido **byte a byte** contra los artefactos guardados; ambas corridas con hash `d2b6d89fb74a` |
| Referencias de evidencia | contraste del `wiring_checklist` con `tests/` | 19 referencias `test::método` citadas: **todas existen**; 0 inexistentes |
| Tests triviales | inspección de cuerpos | 0 tautologías (`assertTrue(True)`, `pass` o cuerpos vacíos) |
| Archivos de evidencia citados | existencia en disco | `EVIDENCIA.md`, `flujo_LabHabeasData.md`, `zeus_doble_chrome_mcp.png`, `banco/resultados/EP-001_corrida*.json`: **todos presentes** |
| Cero PII | barrido de correos y documentos en `banco/`, `fixtures/`, `Logs/`, `Reportes/` | Correos solo en dominios sintéticos (`@ejemplo.invalid`, `@lab-demo.invalid`); sin documentos reales |
| Secretos en claro | barrido de `client_secret`, `password`, `Bearer` | Solo nombres de variables y credenciales sintéticas del doble (`cliente-banco` / `secreto-banco-no-real`) |
| Rutas de máquina | barrido de rutas absolutas en robot y configuración | Ninguna (`RutasProceso.RutaRaiz` es llave de configuración, D-02) |

## Qué NO se re-ejecutó en esta ronda (y por qué)

- **Equivalencia robot↔orquestador (16/16) y `validate_robot` (0/0):** requieren Rocketbot Studio en ejecución y las variables `RPA_AIO_SERVER`, `RPA_AIO_PROYECTO`, `ZEUS_DOBLE_CLIENT_ID` y `ZEUS_DOBLE_CLIENT_SECRET` del proceso de Studio. En esta ronda Studio no estaba abierto, así que se aceptan los artefactos guardados de la corrida de las 12:31, cuya reproducibilidad determinista sí quedó verificada arriba.
- **Verificación visual en Chrome** (`zeus_doble_chrome_mcp.png`): evidencia de imagen archivada; no repetida.

## Intento de refutación

Se buscaron específicamente estos fallos y **ninguno se sostuvo**: citas de tests inexistentes, tests que pasan sin aseverar, evidencia referida que no existe, datos personales reales en fixtures o evidencias, secretos en claro, rutas absolutas de la máquina en el robot exportado, y deriva entre el sha declarado y HEAD.

## Veredicto

- `wiring_verified`: **true** — 25/25 puntos del cableado con evidencia y referencias válidas; suite y banco re-ejecutados.
- `dod`: **true** — los criterios de aceptación de HU-002/003/004 y los 7 puntos de integración quedan cubiertos, con la salvedad documentada de los artefactos de Studio.

**Salvedad que llega a la revisión:** la equivalencia robot↔orquestador y `validate_robot` se apoyan en artefactos previos; para cerrarla con evidencia fresca hay que abrir Studio y repetir ambas. Queda como paso opcional antes del merge, no como bloqueo.
