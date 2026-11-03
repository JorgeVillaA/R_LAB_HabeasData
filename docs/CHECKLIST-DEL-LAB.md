# Checklist del lab — R_LAB_HabeasData

**Qué es:** laboratorio controlado que reproduce el robot de Habeas Data (exclusión de datos de clientes CISA) sobre dobles locales y un repositorio SQLite propio.
**Versión verificada:** commit `496bf5d` en `main` · 2026-11-03.
**Regla de evidencia:** todo artefacto lleva commit, fecha y comando; un artefacto sin procedencia no cuenta como prueba.

---

## 1. Alcance: lo que el lab SÍ hace

| Épica | Historias de usuario | Qué resuelve |
|---|---|---|
| **EP-001** | HU-002, HU-003, HU-004 | Filtra los radicados de «EXCLUSION DE DATOS» en Zeus, lee y normaliza los campos, valida completitud y registra excepciones de negocio 1 |
| **EP-002** | HU-006, HU-007, HU-008, HU-026a | Valida identidad en Policía y Procuraduría (con captcha), compara nombres por similitud con umbral configurable |
| **EP-003** | HU-010, HU-011 | Cruza contra las maestras para detectar duplicados y registra la exclusión (tabla `Exclusion` + contactos) |

**9 historias de usuario** documentadas en `docs/04-historias/`.

## 2. Fuera de alcance (declarado, no oculto)

| Hueco | Por qué |
|---|---|
| **Cobra (HU-005, HU-009)** | Stub: los datos de gestor, sucursal, ID cliente/codeudor salen de `Scripts/habeasdata/sinteticos/stub_cobra.json`. El flujo **no tiene etapa de deuda** |
| **API original de Zeus** | Nunca se consumió. Todo corrió en modo `fixture` contra el doble local (falta `client_secret` en Credential Manager) |
| **Portales reales de Policía/Procuraduría** | Se usan clones locales con los selectores reales (`dobles/portales/`) |
| **reCAPTCHA real** | El captcha determinista de la Procuraduría sí está implementado; el reCAPTCHA de la Policía se resuelve con un servicio simulado. Nada de evasión |
| **Escritura del comentario en Zeus** | Endpoint asumido (contradicción C-09 del alcance), no confirmado contra el servicio real |
| **Envío al ciudadano / firma** | Fuera del proceso del robot: el bot no decide validez ni notifica |

## 3. Inventario: lo que existe hoy

### Código y robot
- `Scripts/habeasdata/` — 15 módulos: `ep001`, `ep002`, `ep003`, `pasos`, `repositorio`, `registro`, `zeus`, `portales`, `captcha`, `nombres`, `config`, `credenciales`, `estructura`, `redaccion`, `sinteticos/`
- `Robots/LabHabeasData.robot.json` — **315 comandos**, 70 variables, flujo legible por bloques (EP-001 → EP-002 → EP-003)
- `studio/R_LAB_HabeasData/robot.db` — robot empaquetado dentro del repo, abre en Rocketbot Studio
- `Robots/VerificacionVisualDobles.robot.json` — robot auxiliar de verificación de los clones

### Especificaciones
- `specs/api-zeus-qa.md` — contrato de la API (OData, 48 campos, token 300 s, filtro de exclusión)
- `specs/portales-reales.md` — selectores y flujo de Policía y Procuraduría
- `specs/repositorio-local.md` — MER del repositorio (13 tablas, estados 1–5)

### Banco de pruebas determinista
- **59 escenarios**: EP-001 = 18, EP-002 = 25, EP-003 = 16
- `banco/resultados/` — corridas y equivalencias robot↔orquestador con procedencia
- `banco/evidencia/corrida-limpia/CORRIDA-LIMPIA.json` — corrida doble sobre base nueva: `verde: true`, 0 fallos

### Dobles (servicios simulados)
- `dobles/zeus_api/` — API de Zeus (token OAuth 300 s, OData, comentario)
- `dobles/portales/policia` y `procuraduria` — clones con front fiel
- `dobles/portales/captchas.py` — servicio de captcha

### Documentación de entrega
- `README.md` — qué es y cómo arrancarlo
- `docs/ENTREGA.md` — estado por épica, evidencia y límites
- `docs/DECISIONES.md` — D-01…D-33, fuente única de verdad (incluye D-28 resuelta con evidencia de CISA)
- `docs/00-alcance-del-lab.md` — alcance y 16 contradicciones C-01…C-16
- `docs/INFORME-DEL-LAB.md` — informe para revisión
- `docs/CREDENCIALES.md` — dónde y a quién pedir el secreto (sin valores)
- `docs/SALUD-POR-BLOQUE.md` — mapa de salud del robot bloque por bloque
- `docs/PR/EP-001.md`, `EP-002.md`, `EP-003.md` — descripciones de PR
- `arrancar_lab.ps1` — arranque en un comando, modo fixture (por defecto) o real

## 4. Estado de verificación

| Verificación | Resultado | Cómo se comprueba |
|---|---|---|
| Suite de pruebas | **293 pruebas OK** | `python -m unittest discover -s tests -t .` |
| Reglas Trycore del robot | **0 errores, 0 avisos** | `validate_robot` con perfil trycore |
| Equivalencia robot ↔ orquestador | **18/18 (EP-001)**, EP-002 y EP-003 con procedencia | `banco/equivalencia_robot.py`, `banco/banco_ep002.py` |
| Corrida limpia, dos veces sobre la misma base | **verde, 0 fallos** | `banco/corrida_limpia.py` |
| Corrida real en Studio + Chrome | **1.754 pasos, 0 errores** (2026-11-03 12:05) | `run_in_studio` sobre el robot del repo |
| Trazabilidad del repositorio | 0 casos abiertos · 13 excepciones · 13 `fallo` · id de corrida en reporte y log · 73 parámetros | consultas sobre `Documentos/repositorio/lab.sqlite` |
| Fuga de conexión | **cerrada** (la BD se puede mover al terminar sin matar Studio) | prueba manual + `corrida_limpia.py` |
| Secretos | ninguno en el repo; el secreto real vive en Windows Credential Manager | `docs/CREDENCIALES.md` |

## 5. Riesgos y huecos conocidos

1. **Sin prueba contra los sistemas reales** (Zeus QA, portales, Cobra): el contrato está implementado según la documentación, no validado contra el servicio vivo.
2. **Endpoint de comentario asumido** (C-09): si difiere del real, la excepción 1 no se registraría en Zeus.
3. **Datos sintéticos**: el lab no debe usarse con radicados reales; la API de QA devuelve PII de ciudadanos y requiere autorización de CISA y redacción estricta.
4. **Rama de deuda ausente**: un radicado con deuda no se detecta en el lab.
5. **Si matan `rocketbot.exe` a la fuerza**, el `.sqlite` puede quedar bloqueado hasta que el sistema libere el archivo (el cierre cubre fin de corrida y fallos de Python).
6. **9 bloques del robot sin escenario**: son ramas de detención crítica, documentadas en `docs/SALUD-POR-BLOQUE.md`.

## 6. Pendientes por dueño

| Pendiente | De quién |
|---|---|
| `git push` de `main` (la regla `git push*` bloquea al agente) | Villa |
| Borrar ramas ya mergeadas en origin (`feature/EP-001`, `feature/EP-002`, `fix/tercera-ronda`, `fix/d28-*`, `chore/cierre-*`) | Villa |
| Pedir el `client_secret` de Zeus QA (Daniel Garavito / Amelia Escobar, canal seguro) para el empalme | Villa |
| Autorización de CISA si se va a correr contra la API real (PII) | Villa / CISA |
| Decidir si se documenta el contrato real de Cobra para dejar el stub con su forma | Villa |
