# Evidencia de EP-002 (HU-006, HU-007, HU-026a, HU-008)

Datos 100 % sintéticos. **Modo FIXTURE**: todo corrió contra los clones técnicos de los portales (`dobles/portales`), el doble del servicio de captchas y el doble de Zeus. **No se consultó ningún portal real del Estado** (ver «Bloqueos»).

## Qué se construyó
- `Scripts/habeasdata/nombres.py` (HU-008), `captcha.py` + `dobles/portales/captchas.py` (HU-026a), `portales.py` (HU-006/007, modos `fixture` y `real`), `ep002.py` (orquestador de referencia), pasos de EP-002 en `pasos.py`.
- Clones técnicos (fieles en campos, selectores y flujo; sin identidad oficial): Procuraduría (radios + `continuarBtn`, `txtNombre`, `ddlTipoID`, `txtNumID`, `txtCorreoEle`, `txtObservaciones`, `ibRefrescar`, `lblPregunta`, `txtRespuestaPregunta`, `btnExportar`, bloque «Datos del ciudadano»; captcha que rota entre 4 familias con la errata «Vallle del Cauca»; WAF 403 y «formulario de atención de incidentes» de `webcert`) y Policía (JSF con `javax.faces.ViewState`, `aceptaOption`, casilla reCAPTCHA, reto de imágenes, aviso de cuota gratuita, «Apellidos y Nombres:»).
- Robot `LabHabeasData` con los grupos HU006, HU007, HU026a, HU008 y de registro, navegando en Chrome (`openbrowser` con `extra:{default:"chrome"}`, `openUrl` aparte, selectores por DOM, sin mouse ni imágenes). Árbol en `flujo_LabHabeasData.md`: 210 comandos en total (EP-001: 84 sin cambio de lógica; EP-002 añade 126, de ellos 21 bloques de Chrome y 55 decisiones `evaluateIf` en total del robot).

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
