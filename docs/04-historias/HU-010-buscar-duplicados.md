---
id: HU-010
titulo: Buscar duplicados de exclusión
epica: EP-003
prioridad: Must
complejidad: M
estado: lista
---
# Buscar duplicados de exclusión

## 1. Declaración de la historia

Como **analista de operaciones**,
quiero **que el bot busque en las bases de exclusión si la identificación, combinada con el celular o el correo del caso, ya fue excluida antes**,
para **evitar reprocesar y volver a excluir a alguien ya gestionado**.

_Contexto_: Origen de la excepción de negocio 4. Corre después de la validación financiera (HU-005, stub) y **antes** de la validación de identidad (HU-006/HU-007). **En el lab las bases viven en el repositorio local** (NocoDB npm 0.301.3 en loopback). Esta historia ya incorpora el soporte de varios valores en un mismo campo (control de cambios aprobado por el cliente el 2026-10-27, confirmado en la sesión de alineación del 2026-10-26, Temas 7-9).

## 2. Escenarios — Criterios de aceptación (Given/When/Then)

### Happy path — sin duplicado
- **Dado que** la identificación del caso, combinada con el celular presente (si lo hay) y/o el correo presente (si lo hay), NO existe en la sub-base de exclusión correspondiente ("Exclusión celulares" y/o "Exclusión correos")
- **Cuando** el bot busca
- **Entonces** marca el caso como sin duplicado y disponible para la validación de identidad

### Error — excepción de negocio 4
- **Dado que** la combinación identificación + celular YA existe en "Exclusión celulares", o la combinación identificación + correo YA existe en "Exclusión correos" (según el canal presente en el caso)
- **Cuando** el bot busca
- **Entonces** registra nota de duplicado (pestaña "Gestión del radicado" → campo "Detalle") y lo registra en el reporte de gestión del bot — excepción de negocio 4

### Reborde — varios valores en un mismo canal (exclusión parcial)
- **Dado que** el caso trae más de un celular y/o más de un correo (valores separados por "/", HU-003)
- **Cuando** el bot busca duplicados
- **Entonces** consulta cada valor por separado contra la sub-base de exclusión correspondiente y marca como duplicado (excepción de negocio 4) únicamente los valores que efectivamente coincidan, dejando los demás continuar al siguiente paso del proceso

### Error — repositorio no responde
- **Dado que** el repositorio local no responde en un caso puntual
- **Cuando** el bot busca el duplicado
- **Entonces** reintenta x3 y marca excepción de sistema del caso; el bot continúa con el siguiente radicado

## 3. Flujo de ejecución

- **Precondición**: solicitante sin obligación activa como titular ni codeudor (HU-005, stub)

| # | Paso (acción del bot) | Referencia |
|---|---|---|
| 1 | Si hay correo, buscarlo en la base maestra de correos. Si hay teléfono clasificado como **celular** (HU-003), buscarlo en la base maestra de celulares. Si está clasificado como **fijo**, no hay base maestra contra la cual cruzarlo. Si el canal trae varios valores, repetir la búsqueda por cada valor. | Repositorio local: bases maestras (`MaestraCelulares`/`MaestraCorreos`, propuesta C-16 pendiente de Villa) |
| 2 | Consultar la sub-base de exclusión del canal presente con **llave compuesta**: identificación + celular en "Exclusión celulares"; identificación + correo en "Exclusión correos". Si el caso tiene ambos canales, se consultan las dos sub-bases, cada una con su llave. Cada valor se consulta de forma independiente. | Repositorio local: tablas `Celulares` y `Correos` (14 columnas) |
| 3 | Si alguna combinación ya figura como excluida: registrar la nota de duplicado en "Gestión del radicado" → "Detalle" y en el reporte de gestión del bot (excepción de negocio 4). Si ninguna es duplicado, continuar a la validación de identidad. El criterio se evalúa **por valor**: solo el valor duplicado genera la excepción; los demás continúan. | Doble de escritura de Zeus |

- **Postcondición**: caso no duplicado continúa a la validación de identidad; duplicado → nota para revisión manual de Cartera (excepción de negocio 4)

## 4. Notas técnicas

**Sustituido por modo local**: NocoDB de CISA → **repositorio local**: NocoDB npm 0.301.3 en loopback con el **MER de 8 tablas** del diseño técnico v1.2 §4.6 (`Insumo`, `Excepciones`, `Exclusion`, `Celulares`, `Correos`, `Gestores`, `Parametros`, `LogEjecucion`; C-12, resuelta) y datos sintéticos. Las sub-bases "Exclusión celulares" y "Exclusión correos" de esta historia corresponden en el MER a las tablas `Celulares` y `Correos` (14 columnas, vinculadas a `Exclusion`). La nota de duplicado en Zeus → **doble de escritura** (contrato supuesto del lab, C-09, abierta). "NocoDB no responde" se simula haciendo que el repositorio local no conteste.

**Llave de consulta (corregida en el origen, 2026-10-20)**: la base "Exclusión" se divide en dos sub-bases por canal (en el lab, `Celulares` y `Correos`); la consulta usa llave compuesta propia de cada una (identificación + celular, o identificación + correo), no solo la identificación.

**Estructura de las tablas (C-10 y C-11, resueltas)**: manda la sesión de alineación del 2026-10-26 (Tema 10): las bases de celulares y de correos tienen **14 columnas**, arrancan con `ID CLIENTE`, `ID CODEUDOR` y ninguna trae columna `FIJO`; la lista exacta por canal está en HU-011 §4 y es la que consulta esta historia (`IDENTIFICACION` + `CELULAR`, o `IDENTIFICACION` + `CORREO`). Las estructuras de 7 columnas (celulares) y 9 columnas (correos) que esta historia documentaba desde el 2026-10-01, y las 12 columnas del archivo de ejemplo del origen, quedan **superadas**. **Residual (C-16, abierta)**: el MER no tiene una tabla maestra separada, por lo que el cruce del paso 1 contra las bases maestras queda con la tabla por definir; los escenarios de esta historia (duplicado por llave compuesta) no dependen de esa decisión. `EN COBRA`, si existe en la maestra y no trae información, se deja vacía; el bot no la infiere. El cruce no depende de `NOMBRE`, cuyo formato varía.

**Canal fijo**: no hay base maestra de fijos ni se crea; el cruce queda limitado a lo ya presente en las bases de exclusión. El origen confirma (2026-09-30) que este canal no se ha presentado en solicitudes reales.

**Reglas cerradas aplicadas**: varios valores separados por "/" sin espacios, cada uno por separado; teléfono clasificado por dígitos (solo el celular participa del cruce).

**Datos**: sintéticos; `FUENTE` toma un catálogo de valores inventados (insumo B6).

**Prioridad y complejidad**: se copian del origen (Must, M); la sustitución local no las cambia.

**Procedencia**: HU de origen `HU-010` (proyecto OP798698, cliente CISA); no cubierta por la aprobación del 09/10/2026 (solo HU-001, HU-002 y HU-004; C-08, resuelta): su lectura con los usuarios líderes de área sigue pendiente; sesión de alineación del 26–27/10/2026, Temas 7-9 (varios valores por canal; aprobación del 2026-10-27) y Tema 10 (14 columnas).

**Dependencias**: HU-005 (stub, precede) · HU-003 · repositorio local · doble de escritura de Zeus · reintentos y excepción de sistema (HU-018, stub).

## 5. Puntos de control

**Críticos** (detienen la ejecución del bot y generan alerta):

- Repositorio inaccesible de forma generalizada (sin acceso a la base de exclusión para ningún caso): aplica la frontera de sistema base del framework de excepciones (HU-018, stub) → detiene la ejecución y alerta.

**No críticos** (permiten continuar; registran en el Reporte de gestiones del Bot):

- Combinación identificación + celular o identificación + correo ya existe → excepción de negocio 4: nota en "Gestión del radicado" → "Detalle" y registro en el reporte; el bot continúa.
- Repositorio no responde en un caso puntual → reintenta x3 y marca excepción de sistema del caso; continúa con el siguiente radicado.
- Canal con varios valores → se consulta cada valor por separado; solo los duplicados generan la excepción 4 (exclusión parcial).

## Checklist INVEST

- [x] **I**ndependent — puede entregarse con solo el repositorio local y los datos de HU-003
- [x] **N**egotiable — el "cómo" de la consulta se puede negociar con el equipo
- [x] **V**aluable — evita reprocesar y excluir dos veces a la misma persona
- [x] **E**stimable — llave compuesta, sub-bases y estructura de columnas definidas
- [x] **S**mall — consultas por canal y valor caben en 1 sprint
- [x] **T**estable — los AC son verificables como tests con datos sintéticos
