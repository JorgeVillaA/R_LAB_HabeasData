# Evidencia de EP-001 (HU-002, HU-003, HU-004) — texto

Fecha de las corridas: 2026-10-29. Datos 100 % sintéticos (fixtures de `fixtures/zeus/radicados.json`); sin PII.

## Corrección de Villa (bloqueante para DoD): el flujo debe ser explicable a cliente

La primera versión de `LabHabeasData` tenía 2 comandos raíz (`trycatch` + `log_message`) y todo el flujo dentro de un `execScriptPython` que importaba
`Scripts/habeasdata/*.py`: una caja negra. **No cumplía.** Se refactorizó así:

- **Estructura** (como `MainMonitoreoMarcas`): `trycatch` «Control de ejecución» → grupo `HU002HU003HU004 - Inicializar el Asistente` → `trycatch`
  «Proceso principal» → grupos `HU002 - Filtrar radicados de Exclusión de Datos`, `HU003 - Leer datos paramétricos` y `HU004 - Validar campos
  obligatorios` (los dos últimos dentro del `for` por radicado) → grupo `HU002HU003HU004 - Cierre y registro de ejecución`.
- **83 comandos visibles** (95 antes de la consolidación de abajo): 35 asignaciones (47 antes), 19 decisiones (`evaluateIf`), 1 bucle, 5 grupos, 2 `trycatch`, 20 pasos de componente y 1 log; cada bloque lleva
  su descripción (§6.1). Árbol completo en `flujo_LabHabeasData.md`.
- **Qué quedó en Python** (`habeasdata.pasos`, una llamada por bloque): E/S con secretos (token con el `client_secret` del Administrador de credenciales y
  consultas con Bearer), parseo y clasificación puros, y escritura de logs y reporte. Ningún bloque contiene el flujo.
- **Por qué el HTTP no es el `request` nativo**: se probó y el comando escribe cabeceras y cuerpo en el log de Studio (apareció el `client_secret` de
  prueba), lo que viola R-04 y R-11. Con el secreto real sería una fuga.
- **Equivalencia**: `banco/equivalencia_robot.py` corre cada escenario del banco con el orquestador Python y con el robot en Studio contra el mismo
  fixture: **16 de 16 equivalentes** (`banco/resultados/EP-001_equivalencia_robot.json`).
- **Banco y pruebas sin cambios**: las 16 huellas de la matriz son idénticas a las previas al refactor, en 2 corridas.
- **Pruebas de legibilidad** (`tests/test_robot_legible.py`): 9 de sus 12 comprobaciones rechazan el robot anterior.
- **Chrome**: los bloques web siguen en Chrome (`openbrowser` con `extra:{default:"chrome"}` y `openUrl` aparte, en `VerificacionVisualDobles`); `LabHabeasData` no navega.

## Consolidación de bloques con la legibilidad por delante (decisión de Villa, 2026-10-30)

| | Antes | Después |
|---|---|---|
| Comandos totales | 95 | **83** |
| `setVar` | 47 | **35** |
| `evaluateIf` / `for` / `group` / `trycatch` / `execScriptPython` / `log_message` | 19 / 1 / 5 / 2 / 20 / 1 | 19 / 1 / 5 / 2 / 20 / 1 (sin cambio: ninguna decisión pasó a Python) |
| Pasos de Studio en el escenario feliz | 300 | 266 |
| Decisiones anidadas bajo el `for` (máx.) | 4 | **2** |

Nota: la instrucción citaba 72 bloques y 30 `setVar` como punto de partida; el robot en disco tenía 95 y 47 (conteo reproducible con `python Robots/arbol_flujo.py`). El antes/después de arriba parte de lo medido.

- **`glbDicEstado`** (estado de la ejecución) reúne `estado`, `motivo_sin_casos`, `total_radicados` y `motivo_detencion` (antes 4 variables sueltas y 8 asignaciones de inicio/detención).
  «Detener» pasó de 2 asignaciones a 1 en cada una de sus 5 ramas; cada asignación que queda sigue siendo un cambio de estado con descripción propia.
- **`locDicConsulta`** reúne filtro base, filtro de selección, `$select`, `$first` y `$orderby` de HU-002 (antes 5 variables y 6 asignaciones).
- **`locBlnLeido` eliminado**: «el radicado quedó leído» se lee de `locDicLectura["ok"]` (antes 2 asignaciones).
- **Las cinco listas de resultados siguen separadas** (`glbArr*`): el MCP recorta cada variable a 120 caracteres y la equivalencia con el orquestador compara las listas completas; meterlas en un diccionario las truncaría. Es un límite de la herramienta de verificación, no de legibilidad.
- **Profundidad bajo el `for`**: HU-004 tenía hasta 4 decisiones anidadas (leído → completo → comentario registrado). Se aplanó: «el radicado quedó leído» acompaña a cada condición y «caso completo» / «caso incompleto» son dos decisiones hermanas; queda un máximo de 2 niveles de control (el `group` solo organiza). El motor ejecuta hoy solo secuencias, `for`, `evaluateIf`, `trycatch`, `break` y `group` (licencia de desarrollo), así que «tarea nombrada» no era ejecutable y no hizo falta.
- **Verificado**: pruebas (`test_profundidad_bajo_el_for…`, `test_los_contenedores_intermedios…`, `test_tope_de_bloques…`), `validate_robot` perfil trycore 0 errores / 0 avisos, y `python banco/equivalencia_robot.py EP-001`: **16 de 16 escenarios equivalentes** entre el robot de Studio y el orquestador.
- Defecto del arnés de equivalencia corregido: la raíz temporal de cada corrida no llevaba `Scripts/` (dependía de un módulo ya importado en el Studio); ahora se copia.

## Verificación adversarial independiente (ronda 1 → corrección)

Veredicto de la ronda 1: **REFUTADO** (el verificador invirtió dos decisiones dentro del robot de Studio y ni la suite ni el banco lo notaron).

| # | Hallazgo | Corrección |
|---|---|---|
| 1 ALTA | Decisiones del robot sin test ejecutable | `banco/interprete_robot.py` ejecuta el JSON del robot sin Studio; `tests/test_robot_interpretado.py` exige igualdad con el orquestador en los 16 escenarios. Validado por reversión: invertir «tipología ausente» → 1 fallo; invertir «falta el nombre» → 9 fallos |
| 2 ALTA | Evidencia de equivalencia no reproducible ni anclada | el artefacto `EP-001_equivalencia_robot.json` lleva `head_at_run`; la corrida en Studio se repitió tras los arreglos (16/16) |
| 3 MEDIA | Consulta general: el robot pasaba por `ids_de` y el orquestador no | `ep001.py` usa `ids_de`; `test_consulta_general_con_fila_sin_idradicado_detiene_igual_que_el_robot` (falla sin el arreglo) |
| 4 BAJA | `FILTRO_EQ` sin uso | ahora lo usa el filtro de descartados |
| 5 BAJA | Detención por excepción del proceso principal sin motivo | el robot fija `motivo_detencion='Excepción de sistema en el proceso principal'` |
| 6 | `NO APORTA` vs `NO APLICA` en los logs | sin cambio: el anexo V1.0 (decisión fija) manda `NO APLICA`; `NO APORTA` es el literal de dato ausente de Zeus |

Tras la corrección: 147 pruebas OK; matriz 16 × 2 verde con huellas idénticas; equivalencia en Studio 16/16; `validate_robot` trycore 0/0.

## Alcance de lo verificado

- **Modo FIXTURE.** Todo lo de abajo corrió contra el doble offline de la API de Zeus, que solo sirve de fixture del banco
  determinista. **No se ejecutó nada contra la API real de CISA.**
- El cliente (`Scripts/habeasdata/zeus.py`) está implementado contra el contrato real `CamposAdicionalesXRadicadoHabeasData`
  (OAuth client credentials, token de 300 s con renovación ante 401, OData `$filter/$select/$first/$orderby`, consulta
  individual por `IDRADICADO`). Sus URLs y su forma de pedir token se prueban sin red en `tests/test_zeus_real.py`.

## Bloqueos para operar contra la API real (QA)

| # | Falta | Cómo se manifiesta | Quién lo resuelve |
|---|---|---|---|
| 1 | `client_secret` de Keycloak (rotado; canal seguro) en el Administrador de credenciales de Windows, credencial `R_LAB_HabeasData/Zeus/QA`. **No existe** en esta máquina (se listaron solo nombres) | `ErrorBloqueo` «falta el client_secret… en el Administrador de credenciales»; no hay llamada | IT de CISA / Villa |
| 2 | Autorización de uso de la API (variable `ZEUS_REAL_AUTORIZADO=1`, que declara que existe) | `ErrorBloqueo` «falta la autorización de uso…»; no hay llamada | Villa / CISA |
| 3 | Acceso de red a `qaservices.cisa.gov.co` | **No verificado**: no se probó la conexión sin autorización | IT de CISA |
| 4 | Endpoint de escritura del comentario (Gestión → Detalle); C-09 | `ErrorBloqueo` «endpoint … no está entregado»; el caso queda como excepción de sistema | IT de CISA |

## Verificaciones ejecutadas

| Verificación | Resultado |
|---|---|
| `python -m unittest discover -s tests -t .` | 126 pruebas, OK (incluye una credencial temporal real en el Administrador de credenciales) |
| `python banco/correr_matriz.py EP-001 --corridas 2` | 16 escenarios; todos pasan en las 2 corridas; huellas idénticas (determinismo); modo FIXTURE declarado |
| `validate_robot` `perfil:"trycore"` — robot `LabHabeasData` (83 comandos) | `ok: true`, 0 errores, 0 avisos |
| `validate_robot` `perfil:"trycore"` — robot `VerificacionVisualDobles` | `ok: true`, 0 errores, 0 avisos |
| `run_in_studio` robot `LabHabeasData` (266 pasos) | `EP-001 modo=fixture estado=ok avanzan=10 excepciones_negocio_1=4 excepciones_sistema=0`; 0 errores capturados (el 5.º caso, con identificación «NO APORTA», lo descarta el filtro compuesto; C-22) |
| `run_in_studio` robot `VerificacionVisualDobles` | 7 pasos ok; `Chrome: titulo=Doble local de la API de Zeus total=16` |
| `python banco/equivalencia_robot.py EP-001` | 16 escenarios: robot de Studio equivalente al orquestador Python en todos |
| Captura con el MCP `rpa-aio` | `zeus_doble_chrome_mcp.png`: Chrome (aviso «software automatizado… está controlando Chrome» = Studio) con el doble renderizado |
| Mutación (9 mutantes sobre reglas de negocio y contrato) | 9 de 9 detectados por las pruebas (corrida previa a la refactorización de modos) |

Entorno: Rocketbot Studio 2026.04.07 (licencia de desarrollo, vence 2026-11-03); Chrome 156.0.8078.48; chromedriver 156.0.8078.73; Python 3.12.10.

## Hallazgos de la corrida

1. **Defecto del doble, corregido**: respondía los errores inyectados de `POST` sin leer el cuerpo y a veces provocaba reinicios de conexión
   y reintentos; la prueba de determinismo lo detectó (corridas con huellas distintas). Se corrigió leyendo siempre el cuerpo.
2. **Studio conserva el intérprete entre ejecuciones**: un módulo `habeasdata` cacheado rompió la corrida tras cambiar la configuración
   (`KeyError: 'UrlBase'`). El robot ahora descarga el paquete de `sys.modules` antes de importarlo.
3. **`openbrowser` solo con `extra:{default:"chrome"}` no navegaba** (`Webbrowser default not load`); funciona con el formato nativo
   `{"url":…,"id_driver":"","profile":""}` más `extra:{default:"chrome"}` y `openUrl` aparte.
4. La captura de pantalla completa del MCP puede mostrar contenido ajeno al lab: la primera captura se borró y la evidencia vigente se
   tomó con Chrome maximizado al frente.

## Lo que NO está verificado

- Ejecución contra la API real (bloqueos 1 a 4).
- C-22: si el descarte de radicados sin identificación debe mantenerse (decide Villa).
- Gates del arnés posteriores a las pruebas: DoR, change de OpenSpec, `wiring_verified` por el verificador adversarial independiente y DoD.
- Retención de logs (el anexo no fija un plazo en las fuentes leídas).
- Envío de los correos «Detenido»/«Urgente» (solo se registra la intención en el resumen; es HU-018, fuera del lab).
