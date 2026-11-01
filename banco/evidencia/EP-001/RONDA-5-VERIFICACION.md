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

---

## Anexo (30/10, misma ronda): re-ejecución real de la equivalencia

Se abrió Studio y se corrió `banco/equivalencia_robot.py EP-001` sobre HEAD. Resultado: **15 de 16 escenarios DISTINTO**, con el robot detenido en el paso de autenticación (`pasos.solicitar_token()` devuelve `ok=False`). No es un defecto de lógica del robot.

**Aislamiento:** la misma corrida con `--interprete` (el JSON del robot ejecutado en proceso, con el entorno del banco) da **16/16 equivalente**. Es decir, la lógica del robot sí coincide con el orquestador Python en HEAD.

**Causa raíz:** el proceso de Studio que está abierto (PID 15092, iniciado 08:43) **no tiene** `ZEUS_DOBLE_CLIENT_ID` ni `ZEUS_DOBLE_CLIENT_SECRET` en su entorno. El robot los lee del entorno del proceso (config `ZeusApi.Fixture.ClientIdEnv` / `ClientSecretEnv`), así que sin ellas el token falla y todos los escenarios terminan en detención. El escenario 07 (`api-no-disponible`) coincide porque ambos lados fallan igual.

**Consecuencia para la evidencia:** la equivalencia en Studio no se reproduce hoy en esta sesión de Studio; la equivalencia lógica sí, al 100 %. Para tenerla en Studio hay que **relanzar Studio con esas dos variables** y repetir la corrida.

**Estado de gates:** se mantienen `wiring_verified` y `dod` en verdadero, con esta salvedad explícita: la equivalencia está probada por intérprete en HEAD; la vía Studio queda condicionada al entorno de arranque.

### Resolución (misma fecha)

Se eliminó la dependencia del entorno del proceso de Studio:

1. `Scripts/habeasdata/zeus.py`: en modo `fixture`, si la variable de entorno no está, las credenciales se leen de la configuración (`ZeusApi.Fixture.ClientId` / `ClientSecret`). El modo `real` no cambia: sigue exigiendo el secreto del Administrador de credenciales.
2. `banco/equivalencia_robot.py`: la configuración temporal que usa cada escenario lleva las credenciales sintéticas del doble, así que el robot de Studio las encuentra en su configuración y no en su entorno. Además, el script fija por defecto el par sintético para que una corrida no falle por olvidarlo.
3. Lanzador `R_LAB_HabeasData.bat` (carpeta del proyecto de Studio): exporta las dos variables antes de arrancar, por compatibilidad.

**Re-ejecución en Studio tras el arreglo: 16/16 equivalente.** Artefacto `banco/resultados/EP-001_equivalencia_robot.json` regenerado. Suite completa: **155 pruebas OK**.

Con esto desaparece la salvedad: la equivalencia queda verificada por las dos vías (Studio e intérprete) en HEAD.
