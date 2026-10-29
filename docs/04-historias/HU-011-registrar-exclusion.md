---
id: HU-011
titulo: Registrar la exclusión en base centralizada
epica: EP-003
prioridad: Must
complejidad: M
estado: lista
---
# Registrar la exclusión en base centralizada

## 1. Declaración de la historia

Como **analista de operaciones**,
quiero **que el bot registre el caso nuevo en la base de exclusión (con los canales de contacto presentes) y lo verifique contra las bases maestras de celulares y correos**,
para **que quede constancia estructurada de cada exclusión para un bloqueo efectivo**.

_Contexto_: Registro posterior a la identidad coincidente. Incluye la verificación cruzada contra la base maestra de celulares (cuando el teléfono clasifica como celular, HU-003) y la de correos, y la eliminación del registro en la base maestra. **En el lab las bases viven en el repositorio local** (NocoDB npm 0.301.3 en loopback). Esta historia ya incorpora el soporte de varios valores por campo (control de cambios aprobado el 2026-10-27, sesión de alineación del 2026-10-26, Temas 7-9).

## 2. Escenarios — Criterios de aceptación (Given/When/Then)

### Happy path — fila insertada en la base de exclusión
- **Dado que** un caso nuevo validado
- **Cuando** el bot inserta la fila de exclusión del radicado (`Exclusion`) y la fila del canal correspondiente (celular o correo) en `Celulares` o `Correos`
- **Entonces** quedan registrados `ID CLIENTE`, `ID CODEUDOR`, tipo de usuario, documento, radicado hijo, nombre, celular o correo (según la tabla), fuente, fechas, **gestor y sucursal** (resueltos por HU-009, stub), con las 14 columnas de la tabla del canal

### Happy path — contacto verificado contra bases maestras
- **Dado que** una fila ya insertada en la base de exclusión
- **Cuando** el bot cruza el correo y/o el teléfono clasificado como celular contra sus bases maestras
- **Entonces** el correo y/o el celular quedan marcados como **verificados (cruzados)**; este cruce no altera la base maestra

### Happy path — eliminación del registro en la base maestra
- **Dado que** el canal (celular y/o correo) del caso ya quedó registrado en la base de exclusión
- **Cuando** el bot confirma esa inserción
- **Entonces** localiza y elimina, en la base maestra correspondiente, el registro cuya identificación coincide con la del caso, para que no se realice más gestión con el solicitante por ese canal

### Error — operación en el repositorio falla de forma persistente
- **Dado que** la operación "<operación>" en el repositorio falla de forma persistente
- **Cuando** el bot agota los 3 reintentos
- **Entonces** marca excepción de sistema del caso y <efecto>

| operación | efecto |
|---|---|
| insertar la fila en la base de exclusión | no se elimina nada de la base maestra |
| eliminar el registro de la base maestra | la fila ya insertada en la base de exclusión se conserva y el bot continúa con el siguiente radicado |

### Reborde — varios valores en un mismo canal (una fila por valor)
- **Dado que** el caso trae más de un celular y/o más de un correo (valores separados por "/", HU-003)
- **Cuando** el bot registra la exclusión
- **Entonces** inserta una fila independiente por cada valor del canal (misma estructura de columnas) y repite, para cada valor, la verificación y la eliminación en la base maestra

### Reborde — contacto ya presente
- **Dado que** un contacto ya existe en la base de celulares/correos
- **Cuando** el bot verifica
- **Entonces** lo marca como ya presente y evita duplicarlo

## 3. Flujo de ejecución

- **Precondición**: caso validado (no deudor, no duplicado e identidad coincidente) y gestor y sucursal ya resueltos (HU-009, stub)

| # | Paso (acción del bot) | Referencia |
|---|---|---|
| 1 | Insertar la fila de exclusión del radicado (`Exclusion`) y, en `Celulares` o `Correos` según el canal, una fila de 14 columnas con `ID CLIENTE`, `ID CODEUDOR`, `TIPO USUARIO`, documento, radicado hijo, nombre del cliente tal cual lo extrajo HU-003, celular o correo, fuente, fecha de consulta (= fecha de creación del radicado), fecha de exclusión, gestor y sucursal (los datos que vienen de Cobra, de los fixtures de los stubs HU-005/HU-009). Con varios valores, una fila independiente por valor. | Repositorio local: `Exclusion`, `Celulares`, `Correos` |
| 2 | Si el teléfono clasifica como **celular**, verificarlo contra la base maestra de celulares (cruce; no escribe en la maestra). Si clasifica como **fijo**, no hay base maestra. Con varios celulares, repetir por cada uno. | Repositorio local: base maestra de celulares (`MaestraCelulares`/`MaestraCorreos`, propuesta C-16 pendiente de Villa) |
| 3 | Si hay correo, verificarlo contra la base maestra de correos (cruce). Con varios correos, repetir por cada uno. | Repositorio local: base maestra de correos (`MaestraCelulares`/`MaestraCorreos`, propuesta C-16 pendiente de Villa) |
| 4 | Confirmada la inserción, eliminar en la base maestra correspondiente el registro cuya identificación coincide con la del caso. Con varios valores, repetir por cada uno. | Repositorio local: base maestra (`MaestraCelulares`/`MaestraCorreos`, propuesta C-16 pendiente de Villa) |

- **Postcondición**: fila de `Exclusion` y fila(s) en `Celulares`/`Correos` (una por valor), con gestor y sucursal; canales verificados; registro(s) correspondiente(s) en la base maestra eliminado(s)

## 4. Notas técnicas

**Sustituido por modo local**: NocoDB de CISA → **repositorio local**: NocoDB npm 0.301.3 en loopback con el **MER de 8 tablas** del diseño técnico v1.2 §4.6 (`Insumo`, `Excepciones`, `Exclusion`, `Celulares`, `Correos`, `Gestores`, `Parametros`, `LogEjecucion`; `Exclusion` 1:N `Celulares`/`Correos`; C-12, resuelta) y datos sintéticos. HU-009 (Cobra, sin endpoints) → **stub declarado** que entrega `GESTOR` y `SUCURSAL` por fixture. "Falla persistente" se simula haciendo que el repositorio local falle la operación. Ajuste respecto de la versión anterior de esta historia: la inserción deja de ser una única fila en "la base de exclusión" y pasa a una fila de `Exclusion` más una fila por valor en `Celulares` o `Correos`, que es la relación del MER.

**Estructura de las tablas `Celulares` y `Correos` (C-11, resuelta; sesión de alineación del 2026-10-26, Tema 10)**: dos tablas separadas por canal, de **14 columnas** cada una, que arrancan con `ID CLIENTE`, `ID CODEUDOR`, sin columna `FIJO`:
- Base de celular: `ID CLIENTE`, `ID CODEUDOR`, `TIPO USUARIO`, `IDENTIFICACION`, `NOMBRE`, `CELULAR`, `FUENTE`, `FECHA CONSULTA`, `ZEUS`, `FECHA EXCLUSION`, `Identificación Dueño Celular`, `Nombre Dueño Celular`, `GESTOR`, `SUCURSAL`.
- Base de correo: `ID CLIENTE`, `ID CODEUDOR`, `TIPO USUARIO`, `IDENTIFICACION`, `NOMBRE`, `CORREO`, `FUENTE`, `FECHA CONSULTA`, `Zeus`, `FECHA EXCLUSION`, `IDENTIFICACIÓN DUEÑO CORREO`, `NOMBRE DUEÑO CORREO`, `GESTOR`, `SUCURSAL`.

Las estructuras previas del origen quedan **superadas**: las 12 columnas del archivo de ejemplo `SOPORTES.xlsx` para celular y cualquier lectura de una sola base con correo, celular y fijo en la misma fila. Los nombres de columna de las dos listas se conservan tal como los registra el origen.

**`ID CLIENTE` e `ID CODEUDOR` (C-10, resuelta)**: manda la sesión del 2026-10-26 (Tema 10): todas las bases las llevan y siempre vienen diligenciadas. Queda **superada** la instrucción previa del origen (PO, 2026-09-30) de que el bot las deja vacías. En el lab el bot las diligencia con valores del fixture de los stubs HU-005/HU-009; de dónde salen en producción sigue pendiente con IT CISA, igual que `FUENTE` y `TIPO USUARIO`.

**Columna `ZEUS`**: guarda el **radicado hijo**; el padre se usa solo en plantillas y reporte (confirmado en el origen, 2026-10-20). **`FUENTE`, `TIPO USUARIO` y datos del dueño del canal**: en el origen vienen de Cobra (campos exactos sin confirmar); en el lab, de los fixtures de HU-009 y del catálogo de `FUENTE` inventado (insumo B6). `FECHA CONSULTA` es la fecha de creación del radicado; no existe columna `COORDINADOR`.

**Datos no ubicados**: cuando el canal nunca apareció en las bases maestras, el bot no toca el repositorio (ni inserta en exclusión ni elimina en la maestra). El registro aplica solo a "Datos Excluidos".

**Eliminación en la base maestra (C-16, abierta)**: es la maestra de HU-010, distinta de las tablas que reciben la inserción. El MER de 8 tablas no trae una tabla maestra separada, así que su ubicación y columnas están por definir; las estructuras de 7 y 9 columnas que documentaba el origen quedan superadas por el Tema 10. Los escenarios de esta historia no dependen de esa decisión.

**Canal fijo**: se registra en la base de exclusión sin lista maestra propia; el origen confirma (2026-09-30) que no se ha presentado en la práctica.

**Reglas cerradas aplicadas**: varios valores separados por "/" sin espacios, una fila por cada uno (confirmado en el origen, 2026-10-27); teléfono clasificado por dígitos; se procesa el radicado hijo.

**Datos**: 100 % sintéticos, cero PII.

**Prioridad y complejidad**: se copian del origen (Must, M); la sustitución local no las cambia.

**Procedencia**: HU de origen `HU-011` (proyecto OP798698, cliente CISA); no cubierta por la aprobación del 09/10/2026 (solo HU-001, HU-002 y HU-004; C-08, resuelta): su lectura con los usuarios líderes de área sigue pendiente; sesión de alineación del 26–27/10/2026, Temas 7-10 (varios valores por canal; estructura de 14 columnas).

**Dependencias**: HU-003 · HU-008 · HU-009 (stub) · HU-010 (maestras) · repositorio local · reintentos y excepción de sistema (HU-018, stub).

## 5. Puntos de control

**Críticos** (detienen la ejecución del bot y generan alerta):

- No aplican en este paso.

**No críticos** (permiten continuar; registran en el Reporte de gestiones del Bot):

- La inserción falla de forma persistente → excepción de sistema (reintenta x3); registra y continúa; no se elimina nada de la maestra.
- Un contacto ya existe → lo marca como presente y evita duplicarlo.
- La eliminación en la base maestra falla de forma persistente → excepción de sistema (reintenta x3); la fila ya insertada se conserva y el bot continúa con el siguiente radicado.
- Canal con varios valores → una fila por valor y verificación/eliminación por cada uno; no detiene el flujo.

## Checklist INVEST

- [x] **I**ndependent — puede entregarse con el repositorio local y fixtures de HU-009
- [x] **N**egotiable — el "cómo" se puede negociar con el equipo
- [x] **V**aluable — deja constancia estructurada para un bloqueo efectivo
- [x] **E**stimable — estructura de 14 columnas, pasos y efectos de falla definidos
- [x] **S**mall — inserción, cruce y eliminación por canal caben en 1 sprint
- [x] **T**estable — los AC (incluida la tabla de fallas) son verificables como tests
