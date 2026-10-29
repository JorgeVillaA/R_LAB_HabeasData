## Why

EP-001 es la puerta de entrada del robot R_HabeasData: sin una ingesta confiable de los radicados de «Exclusión de Datos» no hay proceso. El lab necesita demostrar, con evidencia ejecutada, que el robot consulta la API de Zeus, lee y normaliza los datos del solicitante y separa los casos incompletos para revisión manual.

## What Changes

- Cliente de lectura de la API de Zeus (`CamposAdicionalesXRadicadoHabeasData`) contra el contrato QA: OAuth `client_credentials` con token de 300 s renovado ante 401, OData (`$filter`, `$select`, `$first`, `$orderby`) y consulta individual por `IDRADICADO`; el `client_secret` solo sale del Administrador de credenciales de Windows.
- HU-002: selección de radicados de exclusión (filtro compuesto, lote y orden; descartados por identificación ausente contados y reportados).
- HU-003: extracción y normalización (ausentes, valores separados por `/`, clasificación de teléfono, radicado padre/hijo).
- HU-004: validación de campos obligatorios y comentario de la excepción de negocio 1 (escritura aparte; sin endpoint real entregado).
- Robot de Studio legible a cliente (grupos por historia) y componente `habeasdata.pasos`; configuración en tres JSON; logs y reporte del anexo V1.0.
- Banco determinista (16 escenarios, 2 corridas) con el doble de Zeus como fixture offline, y comparador robot-contra-orquestador.

## Capabilities

### New Capabilities
- `ingesta-radicados`: selección, lectura y validación de completitud de radicados de Exclusión de Datos.

### Modified Capabilities
(ninguna)

## Supuestos vetables por Villa

- **Campos completos en la consulta**: la extracción lee el radicado completo por `IDRADICADO` (sin `$select` por lote) para conservar el escenario «formulario no carga» de HU-003. El paso 3 de `specs/api-zeus-qa.md` pedía `$select`; se documenta como supuesto.
- **C-22**: se sigue el filtro compuesto de la spec (descarta identificación `NO APORTA`); la decisión de mantener el descarte es de Villa.
- **Contrato de escritura del comentario**: supuesto del lab, solo contra el doble (C-09).

## Impact

- Código: `Scripts/habeasdata/`, `dobles/zeus_api/`, `Robots/`, `Configuracion/`, `banco/`, `tests/`, `fixtures/`.
- Dependencias: ninguna (solo biblioteca estándar de Python).
- Sin ejecución contra la API real: faltan `client_secret`, autorización de uso y acceso de red a QA.

## Trazabilidad

- Épica: EP-001 — Ingesta y lectura de casos (`docs/03-backlog/epicas.md`).
- HU cubiertas: HU-002, HU-003, HU-004 (`docs/04-historias/`).
- Fuera de esta épica: HU-001 (token OAuth, insumo para el PO), HU-005 y HU-009 (stubs de Cobra).
