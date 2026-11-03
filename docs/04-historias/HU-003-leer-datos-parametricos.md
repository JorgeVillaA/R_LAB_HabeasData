---
id: HU-003
titulo: Leer datos paramétricos del radicado
epica: EP-001
prioridad: Must
complejidad: M
estado: lista
---
# Leer datos paramétricos del radicado

> **OpenSpec change**: `ep-001-ingesta-y-lectura-de-casos` (épica EP-001).

## 1. Declaración de la historia

Como **analista de operaciones**,
quiero **que el bot extraiga de cada radicado los datos del formulario de campos adicionales (nombre del cliente, tipo y número de identificación, fecha de recepción, correo y teléfono de contacto para exclusión) y su radicado padre cuando exista**,
para **contar con los datos del solicitante sin copiarlos manualmente**.

_Contexto_: En el origen es el paso 4 (pestaña "Campos Adicionales" de Zeus Web). **En el lab la lectura es contra el doble local de la API de Zeus.** Esta historia ya incorpora el soporte de varios valores en un mismo campo (control de cambios aprobado por el cliente el 2026-10-27, confirmado en la sesión de alineación del 2026-10-26, Temas 7-9).

## 2. Escenarios — Criterios de aceptación (Given/When/Then)

### Happy path — extracción completa
- **Dado que** un radicado del doble con campos adicionales diligenciados
- **Cuando** el bot lo lee
- **Entonces** extrae nombre del cliente, tipo y número de identificación, fecha de recepción, y los canales de contacto presentes (correo electrónico para exclusión / teléfono de contacto para exclusión)

### Error — radicado no legible
- **Dado que** el doble responde 400 para ese radicado (el formulario de campos adicionales no se puede leer)
- **Cuando** el bot intenta leerlo
- **Entonces** registra excepción de sistema y continúa con el siguiente radicado

### Reborde — canal de contacto parcial
- **Dado que** el radicado trae solo uno de los dos canales de contacto (correo o teléfono)
- **Cuando** el bot lo lee
- **Entonces** extrae el canal presente y marca como no encontrado el ausente (HU-004 exige al menos uno de los dos, no ambos)

### Reborde — clasificación del "Teléfono de Contacto"
- **Dado que** el campo "Teléfono de Contacto" viene diligenciado con "<valor>"
- **Cuando** el bot extrae el campo
- **Entonces** conserva "<valor>" tal cual y lo clasifica como "<clase>"

| valor | clase |
|---|---|
| 3101234567 (10 dígitos que inician en "3") | celular |
| 4441234 (7 dígitos) | fijo tradicional |
| 2101234567 (cualquier otro patrón) | sin clasificar: no participa del cruce de HU-010 ni de la selección de variante de plantilla de HU-012 (fuera del lab) |

### Reborde — varios valores en un mismo canal de contacto
- **Dado que** el campo "Teléfono de Contacto" y/o "Correo Electrónico para Exclusión" trae más de un valor separado por "/" sin espacios (p. ej. "3101234567/3209876543")
- **Cuando** el bot extrae el campo
- **Entonces** separa el valor por "/" y conserva cada valor individual (clasificando cada teléfono por separado según la tabla anterior), para que HU-010 y HU-011 procesen cada valor uno a uno y de forma independiente

### Reborde — radicado con radicado padre
- **Dado que** el radicado en gestión tiene un número bajo la etiqueta "Radicados padres" (distinta de "Radicados hijos") en la relación padre/hijo que expone el doble
- **Cuando** el bot consulta esa relación
- **Entonces** extrae el número del radicado padre y lo marca para uso posterior en plantillas y reporte, y sigue procesando el radicado hijo

### Reborde — radicado sin radicado padre (derivado del paso 4 del origen)
- **Dado que** el radicado no tiene información bajo "Radicados padres"
- **Cuando** el bot consulta la relación padre/hijo
- **Entonces** continúa usando el propio número del radicado en gestión (comportamiento por defecto)

## 3. Flujo de ejecución

> Sin interfaz gráfica: lectura contra el doble de la API.

- **Precondición**: un radicado de la lista de HU-002 disponible en el doble

| # | Paso (acción del bot) | Referencia |
|---|---|---|
| 1 | Leer el radicado y sus campos adicionales. | Doble de la API de Zeus (48 campos) |
| 2 | Extraer **NOMBRE DEL CLIENTE**, **TIPO DE IDENTIFICACIÓN**, **NO IDENTIFICACION DEL CLIENTE**, fecha de recepción y los canales de contacto presentes (**CORREO ELECTRÓNICO PARA EXCLUSIÓN**, **TELEFONO DE CONTACTO**; cada uno puede venir vacío o "No aporta"). Si alguno de estos dos trae varios valores separados por "/" sin espacios, separarlo y conservar cada valor. | Fixtures por borde |
| 3 | Si **TELEFONO DE CONTACTO** viene diligenciado, clasificar cada valor por dígitos (10 que inician en "3" → celular; 7 → fijo; otro → sin clasificar). | Lógica interna |
| 4 | Consultar la relación padre/hijo; si hay "Radicados padres", extraer el número y almacenarlo como variable interna; si no, usar el número propio. | Doble de la API |

- **Postcondición**: datos del solicitante extraídos (identificación, nombre, canales de contacto con cada valor individual, clasificación celular/fijo de cada teléfono y radicado padre si existe)

## 4. Notas técnicas

**Sustituido por modo local**: Zeus Web (pestañas "Campos Adicionales" y "Radicados padres / hijos") → doble local de la API de Zeus con los 48 campos del manual, semántica OData y códigos 200/400/401. El origen declara la relación padre/hijo "vía API Zeus"; el endpoint exacto y la correspondencia entre nombres de formulario y nombres de campo de la API están pendientes (`docs/00-alcance-del-lab.md` §10). "Formulario no carga" se traduce a la respuesta 400 del doble para ese radicado; una respuesta 401 detiene la ejecución (ver HU-002).

**Campos exactos en Zeus (origen)**: `NOMBRE DEL CLIENTE`, `TIPO DE IDENTIFICACIÓN`, `NO IDENTIFICACION DEL CLIENTE`, `CORREO ELECTRÓNICO PARA EXCLUSIÓN`, `TELEFONO DE CONTACTO`, y la fecha de recepción (nombre exacto sin confirmar). Los canales ausentes se muestran como el literal "No aporta". Los campos heredados `NO. DE CELULAR PARA EXCLUSION` y `NO. FIJO PARA EXCLUSION` no se leen. Si aparece un correo en `OBSERVACIONES`, se ignora: la única fuente de correo es el campo oficial.

**Reglas cerradas aplicadas**: "No aporta" = campo ausente; teléfono clasificado por dígitos (10 que inician en 3 = celular, 7 = fijo, otro = sin clasificar, conservado tal cual sin rechazarlo); varios valores separados por "/" sin espacios, cada uno por separado; se procesa el radicado hijo y el padre se usa en plantillas y reporte.

**Nombre sin normalización**: esta historia extrae `NOMBRE DEL CLIENTE` tal cual viene (puede traer apellidos primero, un solo nombre y un solo apellido, o una razón social). La normalización y detección de orden es de HU-008; su mecanismo sigue pendiente (C-02). **Tipo de documento no diligenciado**: el caso va a la excepción de negocio 1 en HU-004.

**Persistencia**: ni el radicado padre ni los demás datos se escriben en Zeus ni en el repositorio en este paso: son variables internas del bot durante el procesamiento (confirmado en el origen, 2026-10-20). El radicado hijo y el padre quedan trazados en el reporte de gestiones (columnas E y F del origen; las columnas del reporte para el lab las define Villa).

**Datos**: sintéticos (nombres inventados, cédulas ficticias); los fixtures cubren sin canal, "No aporta", multivalor, padre/hijo, NIT y nombre invertido.

**Modo real y fixture (directriz de Villa, 2026-10-29)**: el cliente se implementa contra el contrato real de la API (C-19); el doble local es solo fixture offline del banco. Sin `client_secret`, autorización de uso y acceso de red a QA no se ejecuta contra la API real: se reporta como bloqueo.

Contra la API real, el ejemplo del manual trae `FECHADERECEPCION` como `dd/MM/yyyy` y el literal de ausencia en mayúsculas (C-18); se conservan tal cual y la ausencia no distingue mayúsculas.

**Prioridad y complejidad**: se copian del origen (Must, M); la sustitución local no las cambia.

**Procedencia**: HU de origen `HU-003` (proyecto OP798698, cliente CISA); el 09/10/2026 CISA fijó un criterio de aceptación nuevo (varios celulares en un campo), sin aprobar esta historia en ese correo (C-08, resuelta); sesión de alineación del 26–27/10/2026, Temas 7-9 (separador "/" y también para el correo; aprobación del 2026-10-27). Pendiente del origen que sigue abierto: cómo entrega la API real un campo con más de un valor.

**Dependencias**: HU-002 · doble de la API de Zeus · reintentos y excepción de sistema (HU-018, stub).

## 5. Puntos de control

**Críticos** (detienen la ejecución del bot y generan alerta):

- No aplican en este paso (un 401 se trata como en HU-002).

**No críticos** (permiten continuar; registran en el Reporte de gestiones del Bot):

- El doble responde 400 para el radicado → excepción de sistema del caso; el bot continúa con el siguiente radicado y deja registro.
- Solo uno de los dos canales presente → extrae el presente y marca el ausente como no encontrado. (Sin ningún canal lo rechaza HU-004.)
- `TELEFONO DE CONTACTO` no clasifica como celular ni como fijo → se conserva tal cual; no participa del cruce de HU-010.
- Radicado con "Radicados padres" → se guarda su número; el bot sigue operando sobre el hijo.
- Varios valores en un campo → se separan y se extrae cada uno; no detiene el flujo.

## Checklist INVEST

- [x] **I**ndependent — solo depende de la lista de HU-002 y del doble de la API
- [x] **N**egotiable — el "cómo" de la extracción se puede negociar con el equipo
- [x] **V**aluable — entrega los datos del solicitante sin copia manual
- [x] **E**stimable — campos, reglas de clasificación y fixtures están definidos
- [x] **S**mall — extracción, clasificación y división de valores caben en 1 sprint
- [x] **T**estable — los AC (incluida la tabla de ejemplos) son verificables como tests
