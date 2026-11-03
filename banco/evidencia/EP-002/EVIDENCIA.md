# Evidencia de EP-002 (HU-006, HU-007, HU-026a, HU-008)

Datos 100 % sintéticos. **Modo FIXTURE**: todo corrió contra los clones técnicos de los portales (`dobles/portales`), el doble del servicio de captchas y el doble de Zeus. **No se consultó ningún portal real del Estado** (ver «Bloqueos»).

## Qué se construyó
- `Scripts/habeasdata/nombres.py` (HU-008), `captcha.py` + `dobles/portales/captchas.py` (HU-026a), `portales.py` (HU-006/007, modos `fixture` y `real`), `ep002.py` (orquestador de referencia), pasos de EP-002 en `pasos.py`.
- Clones técnicos (fieles en campos, selectores y flujo; sin identidad oficial): Procuraduría (radios + `continuarBtn`, `txtNombre`, `ddlTipoID`, `txtNumID`, `txtCorreoEle`, `txtObservaciones`, `ImageButton1`, `lblPregunta`, `txtRespuestaPregunta`, `btnExportar`, bloque «Datos del ciudadano»; captcha que rota entre 4 familias con la errata «Vallle del Cauca»; WAF 403 y «formulario de atención de incidentes» de `webcert`) y Policía (JSF con `javax.faces.ViewState`, `aceptaOption`, casilla reCAPTCHA, reto de imágenes, aviso de cuota gratuita, «Apellidos y Nombres:»).
- Robot `LabHabeasData` con los grupos HU006, HU007, HU026a, HU008 y de registro, navegando en Chrome (`openbrowser` con `extra:{default:"chrome"}`, `openUrl` aparte, selectores por DOM, sin mouse ni imágenes). Árbol en `flujo_LabHabeasData.md`: 210 comandos en total (EP-001: 84 sin cambio de lógica; EP-002 añade 126, de ellos 26 comandos web de Chrome; el robot completo tiene 55 decisiones `evaluateIf`).

## Política de captchas (D-05, D-06)
- reCAPTCHA de la Policía: **el bot no lo evade**. Cuota agotada, reto de imágenes y modo real terminan en `revision_humana` (prueba `casilla_nunca_marcada` en el banco: ninguna consulta llegó con la casilla marcada). La casilla solo se marca en fixture, donde el clon la recibe «ya resuelta» (el lab no ejercita esa resolución).
- Captcha de la Procuraduría: el bot envía pregunta + documento + nombre al servicio y usa su respuesta; no la calcula (prueba estática en `test_hu026a`). Familia «capital»: el servicio responde `FAMILIA_NO_SOPORTADA`, el robot refresca la pregunta (cuenta como intento) y tras N=3 devuelve `CAPTCHA_MAX_REINTENTOS`.
- Modo real: exige `PORTALES_REAL_AUTORIZADO=1` y la ventana operativa (06:00–20:00, parametrizable); sin ellas reporta BLOQUEO. `verificar_url_procuraduria()` detecta si `webcert` devuelve el formulario de incidentes.

## Verificaciones ejecutadas
| Verificación | Resultado |
|---|---|
| `python -m unittest discover -s tests -t .` | 195 pruebas OK (incluye HU-006, HU-007, HU-026a, HU-008 y las de EP-001) |
| `python banco/correr_matriz.py EP-002 --corridas 2` | 19 escenarios, todos pasan, huellas idénticas en las 2 corridas |
| Robot (intérprete + navegador emulado) vs orquestador, 19 escenarios | equivalente (`tests/test_robot_identidad.py`); invertir la decisión de cuota → 12 fallos; cambiar el código `CAPTCHA_MAX_REINTENTOS` → 2 fallos |
| Robot en **Studio y Chrome** vs orquestador, 19 escenarios | **19 de 19 equivalentes** (`banco/resultados/EP-002_equivalencia_robot.json`, anclado al sha de la corrida) |
| `validate_robot` perfil `trycore` (`LabHabeasData`) | 0 errores, 0 avisos |
| Mutaciones del orquestador (NIT ≥ 9, cuota sin capturar, comentario 3 sin escribir) | detectadas por el banco |
| Capturas en Chrome de los dos clones | `policia_clon_chrome.png`, `procuraduria_clon_chrome.png` (datos sintéticos, sin PII) |

Escenarios del banco: happy (10 radicados), Policía sin resultado → Procuraduría, cuota agotada, reto de imágenes, Policía caída → Procuraduría, Procuraduría caída, WAF, `webcert`-incidentes, captcha rechazado por el portal, servicio de captchas caído, familia no soportada, rotación de familias, nombre no coincide (excepción 3), nombre incompleto, comentario de la excepción 3 rechazado, NIT de 9 dígitos, no cédula sin nombre, tipo sin consulta (PEP), ciudadano con antecedentes.

## Hallazgo de la corrida
Una primera corrida en Chrome dio 18 de 19: el escenario del reto de imágenes tuvo una carrera de tiempos (el robot leyó la página antes de que cargara). Corregido con `waitforobject` explícito tras cada transición; la segunda corrida dio 19 de 19.

## Diferencias de diseño robot ↔ orquestador (declaradas)
- Reintentos con backoff ante caída de un portal: el orquestador los hace (3); el robot deriva en el primer fallo de Chrome (el `trycatch` captura). El resultado es el mismo en el banco; la política de reintentos del portal en Studio queda como mejora (HU-023 está fuera del lab).
- Estructura inesperada de los portales: en el robot la detecta el `trycatch` (selector ausente); en el orquestador, el parser.

## Bloqueos y pendientes (no verificado)
1. **Portales reales**: sin autorización explícita (`PORTALES_REAL_AUTORIZADO`), sin comprobar la red ni la URL vigente de la Procuraduría (`webcert` devuelve hoy el formulario de incidentes y la página principal está tras un WAF según la inspección de Villa). El modo real está construido y **no se ejecutó**.
2. Servicio de captchas real: falta la ruta/URL, el proveedor y la credencial (Comercial ↔ CISA); en el lab es el doble local.
3. Insumos B3 (métrica de nombres) y B2 (regla del «primer nombre»): propuestos por el agente, **a aprobar por Villa**.
4. Filas de `Transacciones` (D-08) y `MaestraCelulares/MaestraCorreos` (D-17): EP-003; hoy el rastro de EP-002 va al reporte de gestión y a los logs.
5. Reintentos de portal caído en el robot (ver arriba).

---

## Tarea 3.4 — re-ejecución del 2026-10-30 (HEAD `e60f992`). NO está verde

Corrección de nota: la fila «Robot en Studio y Chrome vs orquestador: 19 de 19» de arriba es de `e9d83e2` (antes del cambio al front fiel de `b830846`) y **no vale para el HEAD actual**. Ese artefacto sigue en el historial de git.

| Verificación (HEAD `e60f992`) | Resultado |
|---|---|
| `python -m unittest discover -s tests -t .` | 200 pruebas, OK (`EP-002_suite.log`) |
| `validate_robot` perfil `trycore` (`LabHabeasData`) | 0 errores, 0 avisos |
| `python banco/banco_ep002.py` (robot en Studio y Chrome vs orquestador, 20 escenarios) | **4 de 20 equivalentes** (06, 10, 16, 18); `EP-002_equivalencia_robot.json`, `EP-002_corrida_studio.log` |
| `python banco/equivalencia_robot.py EP-002` | 20 de 20, pero **no ejercita EP-002**: fuerza `Identidad.Habilitada=false` y compara solo el flujo de EP-001 (`EP-002_equivalencia_flujo_EP001_sin_identidad.json`). No es evidencia de 3.4 |

Hallazgos de la corrida:
1. **Credenciales del doble**: `feature/EP-002` no tenía el fallback a configuración (estaba en `fffdce6` de `feature/EP-001`); sin él, Studio detenía la corrida con «Credenciales del doble no definidas». Traído por cherry-pick (`e60f992`). `banco_ep002.py` ahora inyecta el par sintético en la configuración temporal.
2. **Defecto del clon** (corregido): en `dobles/portales/servidor.py` tres regex tenían un byte 0x08 literal en lugar de `\b` (introducido en `b830846`). `sin_manejador_de_clic`, `habilitada` y la marca de la casilla del clon de la Policía nunca coincidían: el botón de refresco conservaba `onclick="return false"` y Chrome fallaba con «element not interactable» (`EP-002_equivalencia_robot_FALLO_pre_correccion_regex.json`).
3. **Causa abierta**: con el clon corregido siguen fallando 16 escenarios en Studio y Chrome. En la traza, el envío de la consulta a la Procuraduría responde «Sesión sin términos aceptados» (la sesión del clon no conserva `acepto` en Chrome) y la lectura de `lblPregunta` falla después. Por HTTP directo (urllib) con las mismas peticiones que Chrome el clon responde bien, y las corridas sueltas en Chrome dieron resultados distintos entre sí. No se determinó si el fallo está en el clon, en el robot o en el estado de Chrome/Studio. Se probaron dos cambios al robot (espera tras el refresco y una espera de resultado distinguible): no cambiaron el resultado y rompían 11 pruebas del navegador emulado, así que se revirtieron.

Pendiente: diagnosticar la causa abierta con el navegador a la vista (capturas del MCP de Chrome) antes de marcar la tarea 3.4 en `tasks.md`.

## Corrección de evidencia (2026-11-01)
- La nota anterior «20/20 en Studio» salía de `banco/equivalencia_robot.py EP-002`, que ejecuta con la identidad deshabilitada y solo compara la parte de EP-001: NO probaba la identidad. La prueba real es `python banco/banco_ep002.py` (robot en Studio + Chrome contra los clones).
- Resultado real antes de los arreglos: 4/20 (el robot terminaba «detenido» en Chrome). Causas halladas con la traza de Studio y corregidas en `dobles/portales/servidor.py`: `onsubmit` de la Procuraduría llamaba a una función no servida; recursos inexistentes reiniciaban la sesión del portal; `ui-state-disabled` anulaba el clic de «Continuar»; el panel de texto de la Policía tapaba el radio; el bloque de resultado de la Procuraduría existía vacío y el robot leía la página anterior.
- Tras los arreglos: corrida 1 = 19/20 (EP002-20 distinto una vez, no reproducible), corrida 2 = 20/20 IGUAL. La corrida final de cierre se repite sobre el HEAD definitivo.
