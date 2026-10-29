---
id: HU-007
titulo: Consultar la Procuraduría (resultado en línea)
epica: EP-002
prioridad: Must
complejidad: M
estado: lista
---
# Consultar la Procuraduría (resultado en línea)

## 1. Declaración de la historia

Como **analista de operaciones**,
quiero **que el bot consulte la Procuraduría (resolviendo su captcha de pregunta) y obtenga el resultado de identidad leyendo la respuesta en línea, sin requerir la descarga del PDF**,
para **obtener el soporte de identidad para documentos no cubiertos por la Policía de la forma más ágil**.

_Contexto_: Fallback de la validación de identidad, acotado a la consulta, la resolución del captcha y la **lectura del resultado en línea**. Tras responder el captcha y pulsar "Consultar", la misma página muestra el bloque **"Datos del ciudadano"** con el nombre y el estado de antecedentes; el nombre se lee de ahí, sin descargar ningún documento. **En el lab el portal es un doble HTML tipo formulario** con captcha de pregunta determinista, que resuelve HU-026a (unidad indivisible con esta historia).

## 2. Escenarios — Criterios de aceptación (Given/When/Then)

### Happy path — resultado en línea
- **Dado que** un documento sin resultado en la Policía (o no cédula) y el captcha de pregunta resuelto
- **Cuando** el bot completa la consulta ante el doble de la Procuraduría
- **Entonces** obtiene el nombre y el estado de antecedentes del bloque "Datos del ciudadano" en la misma página, sin descargar ningún documento

### Error — captcha no resuelto
- **Dado que** el captcha de pregunta no se resuelve tras N intentos (por defecto 3, `CAPTCHA_MAX_REINTENTOS`)
- **Cuando** el bot consulta
- **Entonces** marca excepción de sistema y deriva el caso a gestión manual (fallback humano) para reproceso

### Error — portal caído (sistema)
- **Dado que** el doble de la Procuraduría no responde de forma persistente
- **Cuando** el bot consulta y agota los reintentos (`NUMERO_REINTENTOS_SISTEMA`, por defecto 3)
- **Entonces** marca excepción de sistema y deriva el caso a gestión manual (fallback humano)

### Reborde — el ciudadano presenta antecedentes
- **Dado que** la consulta devuelve el bloque "Datos del ciudadano" con el nombre y el estado "El ciudadano presenta antecedentes"
- **Cuando** el bot lee el resultado
- **Entonces** extrae igualmente el nombre para la comparación de identidad (el estado de antecedentes no altera la validación de identidad de este proceso)

### Reborde — respuesta sin nombre para documento no-cédula
- **Dado que** el documento consultado no es cédula de ciudadanía (cédula de extranjería o pasaporte) y el doble responde sin el bloque "Datos del ciudadano" con el nombre
- **Cuando** el bot lee el resultado
- **Entonces** registra el caso en el Reporte de gestiones del Bot y continúa con el siguiente radicado, igual que un fallo de sistema puntual

### Excepción — NIT con cantidad de dígitos distinta de 10
- **Dado que** el documento del peticionario es NIT y el número de documento no tiene exactamente 10 dígitos (sin guion ni espacios)
- **Cuando** el bot va a consultar la Procuraduría
- **Entonces** no realiza la consulta y deriva el radicado a gestión manual

## 3. Flujo de ejecución

> Sin interfaz propia: el bot navega el doble HTML por selectores del DOM, sin comandos de mouse ni reconocimiento de imágenes.

- **Precondición**: Policía sin resultado, documento distinto de cédula, o Policía caída de forma persistente (derivación desde HU-006; cadena C-04). La cuota agotada del captcha de la Policía **no** llega aquí: va a revisión humana

| # | Paso (acción del bot) | Referencia |
|---|---|---|
| 1 | Si el documento es NIT, verificar que tenga exactamente 10 dígitos; si no, derivar a gestión manual y no consultar. | Regla cerrada del NIT |
| 2 | Abrir el formulario del doble, seleccionar en el desplegable el tipo de documento del peticionario y diligenciar el número. | Doble HTML de la Procuraduría |
| 3 | Resolver el captcha de pregunta variable (HU-026a) y pulsar "Consultar". | HU-026a |
| 4 | Leer, en la misma página, el bloque "Datos del ciudadano" (nombre, en orden nombres y luego apellidos) y el estado de antecedentes. **No se descarga ningún documento.** | Doble HTML (resultado) |

- **Postcondición**: nombre y estado de antecedentes obtenidos del resultado en línea, o caso derivado a gestión manual o fallback humano

## 4. Notas técnicas

**Sustituido por modo local**: el portal de la Procuraduría → **doble HTML tipo formulario** con desplegable de tipo de documento, número, captcha de pregunta determinista y bloque "Datos del ciudadano". El doble se modela sobre la forma documentada en esta historia (formulario con desplegable de tipo de documento, número, captcha de pregunta y bloque "Datos del ciudadano") y **no depende del dominio**: el origen declara sin efecto el dominio `webcert` desde el 2026-10-01 (C-14, resuelta). Selectores definitivos en el insumo B4. Debe cubrir: resultado con y sin antecedentes, respuesta sin nombre, captcha rechazado y portal sin respuesta. El origen cita la URL real, que no se usa en el lab.

**Captcha**: el de la Procuraduría es una pregunta en lenguaje natural variable. La resolución se delega en HU-026a, cuyo servicio externo se sustituye en el lab por un doble local tras la misma interfaz (C-03); familias aritmética, documento y nombre; la familia "capitales" (HU-026b) queda fuera del lab, por lo que una pregunta de esa familia no se resuelve y se trata como captcha no resuelto.

**Orden del nombre**: "Datos del ciudadano" siempre presenta nombres y luego apellidos (confirmado en el origen, 2026-10-01); la Policía, apellidos y luego nombres. La comparación es de HU-008.

**NIT de exactamente 10 dígitos (regla cerrada)**: si el número no tiene 10 dígitos (cualquier cantidad distinta, no solo 9), no se consulta la Procuraduría y el caso va a gestión manual. Origen: sesión de alineación, Tema 4, ratificada en la sesión 02.

**Respuesta sin nombre para documento no-cédula**: se registra en el reporte y se continúa con el siguiente radicado, sin tratarla como excepción de negocio nueva (decisión del PO en el origen, 2026-09-30).

**Dueño de la extracción del nombre**: esta historia lee el nombre y se lo entrega a HU-008 (decisión del PO en el origen, 2026-10-02). La validación de estructura de la página (HU-024) queda fuera del lab.

**Prioridad y complejidad**: se copian del origen (Must, M); la sustitución local no las cambia.

**Procedencia**: HU de origen `HU-007` (proyecto OP798698, cliente CISA); no cubierta por la aprobación del 09/10/2026 (solo HU-001, HU-002 y HU-004; C-08, resuelta): su lectura con los usuarios líderes de área sigue pendiente; sesión de alineación del 26–27/10/2026, Tema 4 (NIT de 10 dígitos).

**Dependencias**: HU-006 · HU-026a (consumida; unidad indivisible) · doble HTML de la Procuraduría · reintentos y excepción de sistema (HU-018, stub) · HU-024 fuera del lab.

## 5. Puntos de control

**Críticos** (detienen la ejecución del bot y generan alerta):

- Caída generalizada del doble (afecta a todas las consultas): aplica la frontera de sistema base del framework de excepciones (HU-018, stub) → detiene la ejecución y alerta.

**No críticos** (permiten continuar; registran en el Reporte de gestiones del Bot):

- Captcha no resuelto tras N intentos, o portal caído tras los reintentos → excepción de sistema; deriva a gestión manual (fallback humano) y continúa.
- Respuesta sin nombre para documento no-cédula → registra y continúa con el siguiente radicado.
- NIT con cantidad de dígitos distinta de 10 → no consulta; deriva a gestión manual.

## Checklist INVEST

- [x] **I**ndependent — se entrega junto con HU-026a, que consume (unidad indivisible declarada en el origen)
- [x] **N**egotiable — el "cómo" (selectores, estructura del doble) se puede negociar con el equipo
- [x] **V**aluable — da el soporte de identidad para documentos que la Policía no cubre
- [x] **E**stimable — el flujo, las reglas del NIT y los resultados del doble están definidos
- [x] **S**mall — cuatro pasos y seis escenarios caben en 1 sprint
- [x] **T**estable — cada AC se verifica contra una respuesta controlada del doble
