# Evidencia de EP-001 (HU-002, HU-003, HU-004) — texto

Fecha de las corridas: 2026-10-29. Datos 100 % sintéticos (fixtures de `fixtures/zeus/radicados.json`); sin PII.

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
| `python -m unittest discover -s tests -t .` | 103 pruebas, OK (incluye una credencial temporal real en el Administrador de credenciales) |
| `python banco/correr_matriz.py EP-001 --corridas 2` | 16 escenarios; todos pasan en las 2 corridas; huellas idénticas (determinismo); modo FIXTURE declarado |
| `validate_robot` `perfil:"trycore"` — robot `LabHabeasData` | `ok: true`, 0 errores, 0 avisos |
| `validate_robot` `perfil:"trycore"` — robot `VerificacionVisualDobles` | `ok: true`, 0 errores, 0 avisos |
| `run_in_studio` robot `LabHabeasData` | `EP-001 modo=fixture estado=ok avanzan=10 excepciones_negocio_1=4 excepciones_sistema=0`; 0 errores capturados (el 5.º caso, con identificación «NO APORTA», lo descarta el filtro compuesto; C-22) |
| `run_in_studio` robot `VerificacionVisualDobles` | 7 pasos ok; `Chrome: titulo=Doble local de la API de Zeus total=16` |
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
