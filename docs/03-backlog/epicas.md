# Épicas — Lab R_LAB_HabeasData (proceso Habeas Data, modo local aislado)

> Subconjunto del proyecto real OP798698 (cliente CISA) que el lab especifica. Los IDs de épica y de historia (HU) se conservan del origen para mantener la trazabilidad; no se renumera.
> Fuente: `docs/03-backlog/epicas.md` del proyecto de origen y plan del lab del 2026-10-29. Alcance, dobles y contradicciones: `docs/00-alcance-del-lab.md`.
> Cada historia que depende de un sistema externo lo declara como «Sustituido por modo local».

## Objetivos del PRD (referencia heredada del origen)

El lab no tiene PRD propio; usa los objetivos del proyecto real solo para trazar.

- **O1** — Reducir el tiempo de gestión por caso de ~20–29 min a < 3 min.
- **O2** — Reducir la tasa de error manual de 2–3 % a < 0.5 %.
- **O4** — Absorber ~250 solicitudes/mes sin incrementar la nómina.
- **O5** — Trazabilidad 360° con registro timestamped en el 100 % de los casos.
- **O6** — Establecer un playbook RPA (automatización robótica de procesos) reutilizable (≥ 3 componentes reutilizados).

(O3 pertenece a épicas fuera del lab y no se traza aquí.)

## Mapa de trazabilidad (Épica × Objetivo, según el origen)

| Épica | O1 | O2 | O4 | O5 | O6 |
|---|:--:|:--:|:--:|:--:|:--:|
| EP-001 — Ingesta y lectura de casos | ✓ |  | ✓ |  |  |
| EP-002 — Validación transaccional e identidad | ✓ | ✓ |  |  |  |
| EP-003 — Registro centralizado y enrutamiento |  | ✓ |  | ✓ |  |
| EP-006 — Estandarización y reutilización (playbook RPA) |  |  | ✓ |  | ✓ |

El lab **no demuestra O6**: solo especifica HU-026a, un componente, mientras el objetivo pide ≥ 3. EP-006 se incluye porque HU-007 no funciona sin HU-026a.

## Secuencia de ejecución del flujo (del origen)

HU-002 → HU-003 → HU-004 → *(HU-005, stub)* → HU-010 → HU-006 → HU-007 (consume HU-026a) → HU-008 → *(HU-009, stub)* → HU-011.

La agrupación por épica es funcional, no cronológica: HU-010 (EP-003) corre **antes** de la identidad de EP-002 y HU-011 (EP-003) corre **después**. Es la dependencia cruzada EP-002 ↔ EP-003 del origen.

---

## EP-001 — Ingesta y lectura de casos

**Resumen**: El bot identifica los radicados de «Exclusión de Datos», lee sus datos paramétricos (documento, nombres, correo/teléfono, radicado padre) y valida que existan los campos obligatorios. En el origen lo hace navegando Zeus Web; **en el lab lo hace contra un doble local de la API de Zeus**, con filtro OData y códigos 200/400/401.

**Justificación**: Es la puerta de entrada del proceso; sin una ingesta confiable no hay automatización. Habilita el ahorro de tiempo (O1) y la capacidad de absorber el volumen sin más personal (O4).

**Objetivos del PRD**: O1, O4.

**Capabilities incluidas**:
- C1 — Extracción, lectura y control de completitud.

**OpenSpec change**: `ep-001-ingesta-y-lectura-de-casos`.

**Historias del lab** (3 HU):
- HU-002 — Filtrar los radicados de «Exclusión de Datos» (filtro OData). **Must**, S.
- HU-003 — Leer los datos paramétricos del radicado. **Must**, M.
- HU-004 — Validar la existencia de los campos obligatorios (excepción de negocio 1). **Must**, S.

**Fuera del lab**: HU-001 (en el origen, inicio de sesión en Zeus Web; por la integración por API se reescribe como obtención de token OAuth, insumo para el PO).

**Sustituido por modo local**: Zeus Web y API de Zeus → doble de la API (48 campos del manual, `$filter`, `$select`, `$first`, códigos 200/400/401) y doble de escritura para el comentario de HU-004.

**Métrica de éxito (origen)**: 100 % de los radicados con tipificación «Exclusión de Datos» son detectados y leídos por ejecución, sin intervención manual. **Criterio en el lab**: se verifica contra los radicados sintéticos del doble, incluidos los ajenos que el filtro debe excluir.

---

## EP-002 — Validación transaccional e identidad

**Resumen**: Sobre cada caso con datos completos y no duplicado, el bot valida la identidad en los portales del Estado (Policía Nacional para cédula; Procuraduría para otros documentos o como fallback, con resolución de captcha y lectura del nombre en línea, sin descargar PDF) y compara el nombre oficial con el registro de Zeus. **En el lab los portales son dobles HTML**; la comparación es lógica pura.

**Justificación**: Concentra la lógica que elimina el error humano de validación (O2) y comprime el tiempo de gestión (O1). Aquí nacen las excepciones de negocio 3 (identidad no coincidente) y la derivación de NIT inválido a gestión manual.

**Objetivos del PRD**: O1, O2.

**Capabilities incluidas**:
- C2 — Validación transaccional, parte de identidad y coincidencia de nombres. La validación financiera (HU-005) y el control de duplicados (HU-010, alojado en EP-003) quedan fuera de esta épica.

**Historias del lab** (3 HU):
- HU-006 — Consultar la identidad en la Policía Nacional (cédula). **Must**, M.
- HU-007 — Consultar la Procuraduría (resultado en línea). **Must**, M. Consume HU-026a (EP-006).
- HU-008 — Comparar nombres (umbral 0.80, sin depender del orden). **Must**, M. Regla fijada por el diseño técnico §5.2 (C-02, resuelta).

**Fuera del lab**: HU-005 (stub: Cobra sin endpoints), HU-023 (resiliencia de la Policía), HU-024 (cambios de estructura de la Procuraduría).

**Sustituido por modo local**: portal de la Policía → doble HTML con captcha de casilla y cuota agotada simulada (resultado: fallback humano; nunca se automatiza la evasión del captcha); portal de la Procuraduría → doble HTML tipo formulario con captcha de pregunta determinista.

**Métrica de éxito (origen)**: tasa de error de validación de identidad < 0.5 %; 100 % de las coincidencias resueltas por regla parametrizada. **Criterio en el lab**: 100 % de los escenarios Given/When/Then con test verde, dos corridas idénticas.

---

## EP-003 — Registro centralizado y enrutamiento

**Resumen**: Dos operaciones de datos sobre las bases de exclusión: **(a)** la búsqueda de duplicados, que corre temprano, antes de consultar los portales; y **(b)** el registro de la exclusión con verificación y eliminación en las bases maestras de celulares y correos, que corre tras confirmar la identidad. **En el lab las bases viven en un repositorio local** (NocoDB npm 0.301.3 en loopback, MER de 8 tablas, tablas `Celulares` y `Correos` de 14 columnas, datos sintéticos).

**Justificación**: Centraliza la fuente de verdad de las exclusiones y evita reprocesos por duplicados (O2), dejando registro estructurado que soporta la trazabilidad (O5). Aquí nace la excepción de negocio 4 (duplicado).

**Objetivos del PRD**: O2, O5.

**Capabilities incluidas**:
- C3 — Registro y enrutamiento.
- Parte de C2 — control de duplicados (HU-010), alojado aquí por afinidad de datos.

**Historias del lab** (2 HU):
- HU-010 — Buscar duplicados de exclusión. **Must**, M.
- HU-011 — Registrar la exclusión en la base centralizada. **Must**, M.

**Fuera del lab**: HU-009 (enrutamiento gestor → agencia → coordinador; stub: Cobra sin endpoints). HU-011 consume sus resultados (`GESTOR`, `SUCURSAL`) como fixture.

**Sustituido por modo local**: NocoDB de CISA → repositorio local con el MER de 8 tablas del diseño técnico v1.2 §4.6; la escritura de la nota de duplicado en Zeus → doble de escritura.

**Métrica de éxito (origen)**: 0 duplicados registrados por error; 100 % de los casos nuevos con fila completa en la base de exclusión. **Criterio en el lab**: igual, sobre los datos sintéticos del repositorio local.

---

## EP-006 — Estandarización y reutilización (playbook RPA)

**Resumen**: En el origen empaqueta los componentes reutilizables del proyecto. **En el lab solo entra HU-026a**, al servicio de HU-007: la resolución del captcha de pregunta determinista de la Procuraduría (aritmética, dígitos del documento, nombre). La familia «capitales» (HU-026b) queda fuera.

**Justificación**: HU-007 (*Must*) no puede consultar la Procuraduría sin resolver su captcha; por eso HU-026a se planifica como unidad indivisible con HU-007 (nota de secuenciación EP-002 ↔ EP-006 del origen).

**Objetivos del PRD**: O4, O6 (el lab no demuestra O6; ver el mapa de trazabilidad).

**Capabilities incluidas**:
- C6 — Estandarización y reutilización, solo en lo que sirve a HU-007.

**Historias del lab** (1 HU):
- HU-026a — Resolver el captcha de pregunta determinista de la Procuraduría. **Must**, S.

**Fuera del lab**: HU-020, HU-021, HU-022, HU-025, HU-026b.

**Sustituido por modo local**: el servicio externo de resolución de captchas contratado por CISA → doble local detrás de la misma interfaz. Ver C-03 (resuelta).

**Métrica de éxito (origen)**: ≥ 3 componentes reutilizables documentados. **Criterio en el lab**: la respuesta esperada por familia y los códigos de error de HU-026a son tests verdes; la métrica del origen no se mide.

---

> **Nota de gaps**: el lab incluye 4 épicas con 9 historias (EP-001: 3, EP-002: 3, EP-003: 2, EP-006: 1); ninguna supera las 6 HU y no hay IDs duplicados. EP-004 y EP-005 del origen quedan fuera por completo. Las contradicciones entre las fuentes están en `docs/00-alcance-del-lab.md` §9.
