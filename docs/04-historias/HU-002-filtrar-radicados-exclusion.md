---
id: HU-002
titulo: Filtrar radicados de Exclusión de Datos
epica: EP-001
prioridad: Must
complejidad: S
estado: lista
---
# Filtrar radicados de Exclusión de Datos

> **OpenSpec change**: `ep-001-ingesta-y-lectura-de-casos` (épica EP-001).

## 1. Declaración de la historia

Como **analista de operaciones**,
quiero **que el bot obtenga de la API de Zeus solo los radicados tipificados como "Exclusión de Datos"**,
para **procesar únicamente los casos que corresponden a este proceso sin revisar toda la bandeja**.

_Contexto_: En el origen esta historia navega la bandeja "Por gestionar" de Zeus Web, agrupa por tipo de documento y verifica "PQR CORRESPONDE A: EXCLUSION DE DATOS" radicado por radicado. **En el lab es un filtro OData** (protocolo abierto de datos) contra el doble local de la API de Zeus. El resultado es la lista de radicados que HU-003 a HU-011 iteran.

## 2. Escenarios — Criterios de aceptación (Given/When/Then)

### Happy path — radicados filtrados
- **Dado que** el doble de la API contiene radicados con `PQRCORRESPONDEA` igual a "EXCLUSION DE DATOS" y radicados ajenos (p. ej. de otra tipología, como "Habeas data - no aplica")
- **Cuando** el bot consulta con `$filter=PQRCORRESPONDEA eq 'EXCLUSION DE DATOS'`
- **Entonces** obtiene la lista completa de los radicados de exclusión y ninguno ajeno

### Error — filtro o campo no reconocido
- **Dado que** el doble responde 400 porque el campo o el valor del filtro no es reconocido
- **Cuando** el bot filtra
- **Entonces** no toma ningún radicado, detiene la ejecución, alerta al equipo técnico y deja registro en el log

### Error — token ausente o vencido
- **Dado que** el doble responde 401 por credencial ausente o vencida
- **Cuando** el bot filtra
- **Entonces** detiene la ejecución, alerta al equipo técnico y deja registro en el log (la obtención y renovación del token no es de esta historia)

### Error — tipología ausente
- **Dado que** el filtro devuelve una colección vacía y la consulta general del doble devuelve radicados (todos ajenos a "Exclusión de Datos")
- **Cuando** el bot compara el total de radicados con los del filtro
- **Entonces** no toma radicados ajenos, reporta que no encontró la tipología, registra "0 casos" en el reporte de gestiones de esa corrida y agenda un reintento según el parámetro `CADENCIA_REINTENTO_BANDEJA_VACIA`

### Reborde — bandeja vacía
- **Dado que** el filtro devuelve una colección vacía y la consulta general del doble también devuelve cero radicados
- **Cuando** el bot compara el total de radicados con los del filtro
- **Entonces** registra "0 casos" en el reporte de gestiones de esa corrida y agenda un reintento según el parámetro `CADENCIA_REINTENTO_BANDEJA_VACIA`

## 3. Flujo de ejecución

> Sin interfaz gráfica: el bot llama al doble de la API de Zeus en loopback.

- **Precondición**: doble de la API disponible con token válido (el token lo gestiona HU-001, fuera del lab)

| # | Paso (acción del bot) | Referencia |
|---|---|---|
| 1 | Construir la consulta con `$filter=PQRCORRESPONDEA eq 'EXCLUSION DE DATOS'` y, si corresponde, `$select` con los campos que HU-003 necesita y `$first`. | Doble de la API de Zeus (48 campos del manual) |
| 2 | Interpretar el código de respuesta: 200 → lista; 400 o 401 → punto de control crítico. | Códigos 200 / 400 / 401 |
| 3 | Si la lista viene vacía, hacer la consulta general (sin `$filter`) para distinguir tipología ausente (hay radicados, ninguno de exclusión) de bandeja vacía (no hay radicados). | Doble de la API de Zeus |
| 4 | En ambos casos vacíos, registrar "0 casos" (con el motivo que corresponda) y agendar el reintento parametrizado. | Reporte de gestiones (stub de HU-027) |
| 5 | Si hay lista, entregarla a HU-003, un radicado por vez. | — |

- **Postcondición**: lista de radicados confirmados como "Exclusión de Datos" lista para iterar

## 4. Notas técnicas

**Sustituido por modo local**: Zeus Web y su bandeja "Por gestionar" → doble local de la API de Zeus con los 48 campos del manual, semántica OData (`$filter`, `$select`, `$first`) y códigos 200/400/401. El filtro por `PQRCORRESPONDEA` reemplaza las dos etapas del origen (agrupar por tipo de documento y verificar el campo en cada radicado): la comparación exacta del campo ya descarta los subtipos ajenos que el origen obligaba a revisar uno por uno. El doble debe incluir esos subtipos ajenos para que el filtro se pruebe de verdad.

**"Tipología ausente" vs. "bandeja vacía" (C-13, resuelta)**: el origen distingue ambos casos con la navegación de la bandeja. En OData los dos devuelven colección vacía, así que se distinguen por **doble consulta**: el total de radicados que devuelve la consulta general frente a los del filtro. Ambos casos registran "0 casos" y agendan reintento según `CADENCIA_REINTENTO_BANDEJA_VACIA` (parametrizable por el equipo técnico, según el PO). Ajuste respecto de la versión anterior de esta historia: ya no se traduce "tipología ausente" al código 400; el 400 queda para filtro o campo no reconocido.

**Bandeja vacía**: el bot reintenta en otro horario del día; no finaliza sin error registrando solo "0 casos". La cadencia y el número de reintentos diarios son parámetro técnico (`CADENCIA_REINTENTO_BANDEJA_VACIA`), en `ConfiguracionProceso`; ningún valor va en la lógica. Cadencia parametrizable confirmada por el PO en el origen (2026-09-30).

**Paginación**: el origen declara que el listado no tiene paginación. La semántica exacta de `$first` en el manual queda por confirmar (pendiente en `00-alcance-del-lab.md` §10).

**Modo real y fixture (directriz de Villa, 2026-10-29)**: el cliente se implementa contra el contrato real de la API (C-19); el doble local es solo fixture offline del banco. Sin `client_secret`, autorización de uso y acceso de red a QA no se ejecuta contra la API real: se reporta como bloqueo.

**Selección según el contrato QA (`specs/api-zeus-qa.md`)**: `PQRCORRESPONDEA eq 'EXCLUSION DE DATOS' and NOIDENTIFICACIONDELCLIENTE ne 'NO APORTA'`, con `$first` (lote) y `$orderby=IDRADICADO desc`. Los radicados descartados por identificación ausente se cuentan, se reportan y no se gestionan; si el descarte se desactiva, HU-004 los lleva a la excepción de negocio 1 (C-22, decide Villa). El `client_secret` sale solo del Administrador de credenciales de Windows.

**Prioridad y complejidad**: se copian del origen (Must, S); la sustitución local no las cambia.

**Procedencia**: HU de origen `HU-002` (proyecto OP798698, cliente CISA); aprobada por CISA en el correo de Amelia Escobar del 09/10/2026 («Entrega Oficial Documentación funcional»; C-08, resuelta); sesión de alineación del 26–27/10/2026: no aplica a esta historia. El origen confirma (2026-10-01) que la identificación se hará vía API de Zeus y (2026-09-29) que su documentación está disponible.

**Dependencias**: HU-001 (token OAuth, fuera del lab) · doble de la API de Zeus · framework de reintentos y reporte (HU-018 y HU-027 como stub).

## 5. Puntos de control

**Críticos** (detienen la ejecución del bot y generan alerta):

- La API responde 400 (campo o filtro no reconocido) o 401 (sin token válido) → detiene la ejecución, alerta al equipo técnico y deja registro en el log.

**No críticos** (permiten continuar; registran en el Reporte de gestiones del Bot):

- Tipología ausente o bandeja vacía (filtro vacío) → registra "0 casos" en el reporte de la corrida y agenda un reintento según `CADENCIA_REINTENTO_BANDEJA_VACIA`.

## Checklist INVEST

- [x] **I**ndependent — puede entregarse sin depender de otras historias (solo del doble de la API)
- [x] **N**egotiable — el "cómo" (campos de `$select`, uso de `$first`) se puede negociar con el equipo
- [x] **V**aluable — entrega la lista de casos a procesar, sin revisar toda la bandeja
- [x] **E**stimable — el contrato del doble (campos, `$filter`, códigos) es conocido
- [x] **S**mall — una consulta y tres códigos de respuesta caben en 1 sprint
- [x] **T**estable — los AC son verificables como tests contra el doble
