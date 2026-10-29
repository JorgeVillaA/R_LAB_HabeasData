---
id: HU-004
titulo: Validar existencia de campos obligatorios
epica: EP-001
prioridad: Must
complejidad: S
estado: lista
---
# Validar existencia de campos obligatorios

## 1. Declaración de la historia

Como **analista de operaciones**,
quiero **que el bot verifique que cada caso tenga nombre del cliente, tipo y número de identificación, y al menos un canal de contacto (correo o teléfono de contacto) antes de procesarlo**,
para **recibir para revisión manual solo los casos incompletos, sin perder tiempo en los completos**.

_Contexto_: Control de completitud (Capability 1). Solo valida existencia, no formato ni contenido. Origen de la excepción de negocio 1. **En el lab el comentario se escribe en el doble de escritura de Zeus.**

## 2. Escenarios — Criterios de aceptación (Given/When/Then)

### Happy path — datos completos
- **Dado que** un caso con nombre del cliente, tipo y número de identificación, y al menos uno de los dos canales de contacto (correo electrónico o teléfono de contacto para exclusión)
- **Cuando** el bot valida completitud
- **Entonces** el caso avanza a la validación de titular/codeudor activo (HU-005, stub)

### Error — excepción de negocio 1 (identificación incompleta)
- **Dado que** un caso al que le falta el nombre del cliente, el tipo de identificación o el número de identificación
- **Cuando** el bot valida
- **Entonces** registra un comentario (pestaña "Gestión del radicado" → campo "Detalle") con el motivo (campos incompletos), para revisión manual del Área de Cartera — excepción de negocio 1

### Error — excepción de negocio 1 (sin ningún canal de contacto)
- **Dado que** un caso con nombre e identificación completos pero sin correo y sin teléfono de contacto
- **Cuando** el bot valida
- **Entonces** registra un comentario en "Gestión del radicado" → "Detalle" con el motivo (sin canal de contacto), para revisión manual del Área de Cartera — excepción de negocio 1

### Reborde — campos vacíos
- **Dado que** el campo NOMBRE DEL CLIENTE viene solo con espacios en blanco y los demás campos obligatorios están completos
- **Cuando** el bot valida existencia
- **Entonces** trata el campo como ausente y aplica la excepción de negocio 1 por identificación incompleta

### Reborde — campo con el texto literal "No aporta"
- **Dado que** un campo obligatorio o un canal de contacto trae el texto literal **"No aporta"**
- **Cuando** el bot valida existencia
- **Entonces** trata ese campo como ausente, igual que si viniera vacío o en blanco

### Error — escritura del comentario rechazada (añadido por el lab, ver §4)
- **Dado que** el doble de escritura rechaza el comentario con un error documentado (400 o 401)
- **Cuando** el bot intenta registrar la excepción de negocio 1
- **Entonces** marca excepción de sistema del caso, registra el motivo en el log y continúa con el siguiente radicado

## 3. Flujo de ejecución

- **Precondición**: datos del radicado extraídos por HU-003

| # | Paso (acción del bot) | Referencia |
|---|---|---|
| 1 | Verificar la existencia de NOMBRE DEL CLIENTE, TIPO DE IDENTIFICACIÓN y NO IDENTIFICACION DEL CLIENTE (obligatorios) y de al menos uno de CORREO ELECTRÓNICO PARA EXCLUSIÓN o TELEFONO DE CONTACTO (no valida formato ni contenido). Vacío, solo espacios y "No aporta" cuentan como ausente. | Fixtures por borde |
| 2 | Si está completo, dejar continuar; si no, registrar el comentario con el motivo en "Gestión del radicado" → "Detalle". | Doble de escritura de Zeus |

- **Postcondición**: caso completo continúa; caso incompleto → excepción de negocio 1 (comentario para revisión manual de Cartera)

## 4. Notas técnicas

**Sustituido por modo local**: la escritura del comentario en Zeus Web ("Gestión del radicado" → "Detalle") → **doble de escritura** con respuesta de éxito y errores documentados en su spec. El origen declara pendiente (con IT de CISA) el endpoint exacto de escritura para esta historia y otras (HU-005, HU-008, HU-010, etc.); el contrato del doble es por tanto un **supuesto del lab** registrado como deuda para la integración real (contradicción C-09 de `docs/00-alcance-del-lab.md`). La lectura de los datos usa el doble de la API de Zeus (códigos 200/400/401).

**Escenario añadido**: el origen no define qué hace el bot si la escritura del comentario falla; el escenario "escritura rechazada" aplica el contrato mínimo de excepción de sistema (reintentos y registro, HU-018 como stub) y requiere confirmación de Villa.

**Regla de completitud (cerrada)**: obligatorios nombre + tipo + número de identificación, y al menos un canal de contacto; no se exige un canal específico ni ambos. "No aporta" es el único literal de dato ausente de este formulario; se trata igual que vacío o en blanco. La clasificación celular/fijo (HU-003) es irrelevante aquí: solo se valida existencia.

**Excepciones de negocio → Cartera**: las cuatro excepciones de negocio (1 datos incompletos, 2 titular o codeudor activo, 3 identidad no coincidente, 4 duplicado) usan el mismo mecanismo: un comentario con el motivo en "Gestión del radicado" → "Detalle". En el lab solo se ejercitan la 1 (esta historia), la 3 (HU-008) y la 4 (HU-010); la 2 depende de HU-005 (stub).

**Sin número de identificación**: sub-caso de la excepción de negocio 1; va a gestión manual completa y no requiere una excepción propia. Sin tipo de documento: el bot no puede enrutar a Policía ni a Procuraduría y se aplica la misma excepción.

**Relación con la notificación**: pasar esta validación no garantiza notificación automática; un caso con teléfono pero sin correo lo trata la historia de notificación del origen (fuera del lab).

**Prioridad y complejidad**: se copian del origen (Must, S); la sustitución local no las cambia.

**Procedencia**: HU de origen `HU-004` (proyecto OP798698, cliente CISA); aprobada por CISA en el correo de Amelia Escobar del 09/10/2026 («Entrega Oficial Documentación funcional»; C-08, resuelta); la sesión de alineación del 26–27/10/2026 solo añadió el criterio de varios valores separados por "/" (Temas 7-9). El literal "No aporta" y la excepción para ciudadanos sin identificación vienen del origen (confirmación del 2026-10-20).

**Dependencias**: HU-003 · doble de la API y doble de escritura de Zeus · HU-005 (stub, historia siguiente).

## 5. Puntos de control

**Críticos** (detienen la ejecución del bot y generan alerta):

- No aplican en este paso.

**No críticos** (permiten continuar; registran en el Reporte de gestiones del Bot):

- Caso incompleto (sin nombre, sin tipo, sin número de identificación, o sin ningún canal de contacto) → excepción de negocio 1: comentario para revisión manual de Cartera; el bot continúa.
- Escritura del comentario rechazada → excepción de sistema del caso; el bot continúa con el siguiente radicado.

## Checklist INVEST

- [x] **I**ndependent — puede entregarse con solo los datos de HU-003 y el doble de escritura
- [x] **N**egotiable — el "cómo" se puede negociar con el equipo
- [x] **V**aluable — separa los casos incompletos para revisión manual
- [x] **E**stimable — la regla de completitud es cerrada y finita
- [x] **S**mall — cinco verificaciones de existencia caben en 1 sprint
- [x] **T**estable — los AC son verificables como tests
