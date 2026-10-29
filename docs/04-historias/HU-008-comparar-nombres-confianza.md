---
id: HU-008
titulo: Comparar nombres (umbral 0.80, sin depender del orden)
epica: EP-002
prioridad: Must
complejidad: M
estado: lista
---
# Comparar nombres (umbral 0.80, sin depender del orden)

## 1. Declaración de la historia

Como **analista de operaciones**,
quiero **que el bot compare el nombre del portal contra el registrado en la pestaña Campos Adicionales de Zeus (HU-003) con el umbral de coincidencia `UMBRAL_COINCIDENCIA_NOMBRES` (0.80 por defecto, parametrizable), sobre el nombre normalizado y sin depender del orden de nombres y apellidos**,
para **excluir solo cuando la identidad coincide**.

_Contexto_: Validación de coincidencia; origen de la excepción de negocio 3. **Es lógica pura**: no depende de sistemas externos; solo el comentario de la excepción usa el doble de escritura de Zeus. La regla vigente es la del diseño técnico v1.2 §5.2 (umbral 0.80 de score). La regla del origen, **primer nombre + primer apellido**, se conserva como el caso que **garantiza coincidencia plena (score 1.0)**, no como el único criterio (C-02, resuelta).

## 2. Escenarios — Criterios de aceptación (Given/When/Then)

### Happy path — coincide primer nombre + primer apellido (score 1.0)
- **Dado que** Zeus registra "Juan Pérez" y el portal devuelve "Juan Pérez Gómez"
- **Cuando** el bot compara los nombres normalizados
- **Entonces** coinciden (primer nombre "Juan" + primer apellido "Pérez", aunque falte el segundo apellido), el score es 1.0 y marca la identidad como validada

### Error — excepción de negocio 3
- **Dado que** Zeus registra "Juan Pérez Gómez" y el portal devuelve "Carlos Ramírez Díaz"
- **Cuando** el bot compara los nombres normalizados
- **Entonces** el score queda por debajo del umbral, no coinciden y registra comentario (pestaña "Gestión del radicado" → campo "Detalle"; nombres no coinciden) — excepción de negocio 3 (revisión por discrepancia de identidad)

### Reborde — nombre incompleto (sin primer apellido)
- **Dado que** el portal devuelve un nombre demasiado corto para identificar primer nombre + primer apellido (p. ej. solo "Juan", sin apellido)
- **Cuando** el bot compara
- **Entonces** no puede confirmar la coincidencia y deriva a excepción de negocio 3 (revisión humana), cualquiera sea el score (regla del origen, conservada como salvaguarda)

### Reborde — orden de nombres distinto entre fuentes
- **Dado que** Zeus registra "<nombre Zeus>" y el portal devuelve "<nombre portal>"
- **Cuando** el bot compara
- **Entonces** identifica nombres y apellidos en cada fuente sin importar su orden, coinciden y marca la identidad como validada

| nombre Zeus | nombre portal | fuente |
|---|---|---|
| Juan Pérez Gómez | PEREZ GOMEZ JUAN | Policía (siempre apellidos y luego nombres) |
| Pérez Gómez Juan | Juan Pérez Gómez | Procuraduría (nombres y luego apellidos), con Zeus en orden invertido |

### Regla del umbral
- **Dado que** la comparación del nombre normalizado produce un score entre 0 y 1 y `UMBRAL_COINCIDENCIA_NOMBRES` vale 0.80
- **Cuando** el score es mayor o igual que 0.80
- **Entonces** coinciden y marca la identidad como validada; si el score es menor que 0.80, no coinciden y aplica la excepción de negocio 3

### Regla del umbral — parametrizable
- **Dado que** `UMBRAL_COINCIDENCIA_NOMBRES` se cambia a otro valor en el archivo maestro de configuración
- **Cuando** el bot compara un par de nombres cuyo score queda entre ambos valores
- **Entonces** el resultado sigue el valor configurado, sin cambios en la lógica

## 3. Flujo de ejecución

> Lógica sin interfaz propia.

- **Precondición**: nombre oficial disponible (de HU-006 o HU-007)

| # | Paso (acción del bot) | Referencia |
|---|---|---|
| 1 | Normalizar (acentos, mayúsculas, espacios) y separar nombres y apellidos de ambos nombres (Zeus y portal), sin depender del orden. | Insumo B3 (mecanismo de normalización) |
| 2 | Calcular el score de coincidencia (1.0 si coinciden primer nombre y primer apellido) y compararlo con `UMBRAL_COINCIDENCIA_NOMBRES`. | Archivo maestro `Maestro_Configuracion` (DT §5.2) |
| 3 | Si coincide, validar la identidad; si no, escribir el comentario de la excepción de negocio 3. | Doble de escritura de Zeus |

- **Postcondición**: identidad coincide → continúa al registro (HU-011); no coincide → excepción de negocio 3

## 4. Notas técnicas

**Sustituido por modo local**: la comparación no tiene dependencia externa en el origen ni en el lab. Solo cambia el destino del comentario de la excepción de negocio 3: Zeus Web → **doble de escritura** (contrato supuesto del lab, C-09, abierta).

**Regla de nombres (C-02, resuelta)**: manda el diseño técnico v1.2 §5.2, que define `UMBRAL_COINCIDENCIA_NOMBRES` con valor por defecto 0.80 («umbral de score para considerar coincidencia de identidad»); el DT §5.4 lo replica en la tabla `Parametros` como `UmbralCoincidenciaNombres`, ajustable en caliente. La nota de integración §5 recoge la regla «nombres sin depender del orden». Ajuste respecto de la versión anterior de esta historia, que seguía la regla del origen como criterio único: ahora la coincidencia por primer nombre + primer apellido es el caso de score 1.0 y el criterio general es el umbral. El score se calcula sobre el nombre normalizado; esa formulación proviene de la decisión del coordinador, no del texto literal del DT.

**Pendiente de implementación (insumo B3)**: la métrica de similitud, el tratamiento de tildes, partículas y segundo nombre, y la razón social los produce el agente y los aprueba Villa. **Criterio de aceptación de B3**: todo ejemplo de esta historia (que viene del origen) debe dar el resultado indicado; si la métrica elegida contradice alguno, se devuelve a Villa en lugar de ajustar el ejemplo. La regla para persona jurídica (razón social) sigue pendiente de definir con el PO y no tiene escenario.

**Parametrización**: el umbral vive en el archivo maestro de configuración (`Maestro_Configuracion`), nunca en la lógica; el espejo `UmbralCoincidenciaNombres` de la tabla `Parametros` del MER (C-12) permite ajustarlo sin tocar archivos.

**Variabilidad del nombre por fuente (origen)**: la Policía siempre devuelve apellidos y luego nombres; la Procuraduría, nombres y luego apellidos; Zeus (`NOMBRE DEL CLIENTE`) no está garantizado en un orden fijo y puede ser una razón social.

**Mecanismo reutilizable (origen)**: el origen declara que Trycore aportará un mecanismo de coincidencia independiente del orden; su empaquetado (HU-021) está fuera del lab y HU-008 no depende de él.

**Prioridad y complejidad**: se copian del origen (Must, M); la sustitución local no las cambia.

**Procedencia**: HU de origen `HU-008` (proyecto OP798698, cliente CISA); no cubierta por la aprobación del 09/10/2026 (solo HU-001, HU-002 y HU-004; C-08, resuelta): su lectura con los usuarios líderes de área sigue pendiente; sesión de alineación del 26–27/10/2026: no aplica a esta historia. El umbral 0.80 proviene del diseño técnico v1.2 §5.2.

**Dependencias**: HU-006 y HU-007 (nombre oficial) · HU-003 (nombre de Zeus) · doble de escritura de Zeus.

## 5. Puntos de control

**Críticos** (detienen la ejecución del bot y generan alerta):

- No aplican en este paso.

**No críticos** (permiten continuar; registran en el Reporte de gestiones del Bot):

- Score menor que el umbral, o nombre del portal demasiado corto → excepción de negocio 3: comentario en "Gestión del radicado" → "Detalle" para revisión manual de Cartera; el bot continúa.

## Checklist INVEST

- [x] **I**ndependent — lógica pura; solo necesita dos nombres de entrada
- [x] **N**egotiable — la métrica y la normalización se negocian dentro de B3
- [x] **V**aluable — evita excluir a la persona equivocada
- [x] **E**stimable — los ejemplos del origen y el umbral acotan el trabajo
- [x] **S**mall — una comparación parametrizada cabe en 1 sprint
- [x] **T**estable — ejemplos y umbral verificables como tests sin sistemas externos
