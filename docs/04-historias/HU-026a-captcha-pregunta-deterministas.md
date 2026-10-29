---
id: HU-026a
titulo: Resolver el captcha de pregunta determinista de la Procuraduría
epica: EP-006
prioridad: Must
complejidad: S
estado: lista
---
# Resolver el captcha de pregunta determinista de la Procuraduría

## 1. Declaración de la historia

Como **analista de operaciones**,
quiero **que el bot envíe la pregunta del captcha de la Procuraduría (junto con el documento y el nombre del caso, cuando la pregunta lo requiera) al servicio externo de resolución de captchas y use la respuesta que ese servicio retorna**,
para **que la validación de identidad en la Procuraduría (HU-007) funcione sin intervención humana en la mayoría de los casos**.

_Contexto_: Split de HU-026 en el origen (2026-10-02): alcance mínimo que HU-007 necesita. En el proyecto real el servicio es de un tercero, contratado y pagado por CISA; **el bot no calcula la respuesta**. **En el lab ese servicio se sustituye por un doble local detrás de la misma interfaz** (familias aritmética, dígitos del documento y nombre), que atiende al doble HTML de la Procuraduría. La familia "capital de Colombia" y el empaquetado como componente reutilizable (HU-026b) quedan fuera del lab. El captcha rota entre familias en cada carga; reintentos por defecto N=3 (`CAPTCHA_MAX_REINTENTOS`), parametrizable.

## 2. Escenarios — Criterios de aceptación (Given/When/Then)

### Happy path — pregunta enviada al servicio y resuelta
- **Dado que** el doble de la Procuraduría presenta una pregunta de una de las familias soportadas (aritmética, documento o nombre) y, cuando la pregunta lo requiere, el documento y el nombre del caso están disponibles
- **Cuando** el bot envía la pregunta (y el documento o el nombre, cuando aplica) al servicio de resolución de captchas (en el lab, su doble local)
- **Entonces** recibe la respuesta resuelta por el servicio y la escribe en el campo del captcha

| familia | pregunta de ejemplo | dato adicional enviado al servicio | respuesta esperada |
|---|---|---|---|
| aritmética | ¿Cuánto es 5 + 3? | — | 8 |
| documento | ¿Escriba los dos últimos dígitos del documento a consultar? | documento: 12345687 | 87 |
| nombre | ¿Cuál es el primer nombre de la persona…? | nombre en Zeus: Juan Pérez | Juan |
| nombre | ¿Escriba la cantidad de letras del primer nombre…? | nombre en Zeus: Juan Pérez | 4 |

### Error — servicio no disponible
- **Dado que** el servicio de resolución de captchas (o su doble) no está disponible
- **Cuando** el bot le envía la pregunta y agota los reintentos (`NUMERO_REINTENTOS_SISTEMA`, por defecto 3)
- **Entonces** marca excepción de sistema, retorna el error `CAPTCHA_SERVICIO_NO_DISPONIBLE` y el caso se deriva a gestión manual (fallback humano; HU-007, escenario de captcha no resuelto)

### Reborde — reintentos agotados
- **Dado que** la respuesta retornada por el servicio es rechazada por el portal en cada intento
- **Cuando** el bot agota los N intentos configurados (por defecto 3)
- **Entonces** retorna `CAPTCHA_MAX_REINTENTOS` y el caso se deriva a gestión manual (fallback humano)

### Reborde — pregunta de familia no soportada (añadido por el lab, ver §4)
- **Dado que** el doble de la Procuraduría presenta una pregunta que no pertenece a las familias aritmética, documento ni nombre (p. ej. "capital de Colombia")
- **Cuando** el bot la envía al servicio (doble)
- **Entonces** no se inventa una respuesta, retorna error de familia no soportada y el caso se deriva a gestión manual (fallback humano)

## 3. Flujo de ejecución

> Lógica sin interfaz propia: la consume HU-007 dentro de la página del doble de la Procuraduría.

- **Precondición**: página del doble cargada con la pregunta del captcha visible; número de documento y nombre del caso disponibles (HU-003); servicio de resolución de captchas (doble local) disponible
- **Postcondición**: respuesta del servicio escrita en el campo del captcha, o código de error para gestión manual

## 4. Notas técnicas

**Sustituido por modo local (C-03, resuelta)**: el servicio externo de resolución de captchas contratado y pagado por CISA → **doble local detrás de la misma interfaz**, que cumple la misma función: recibe la pregunta (y el documento o el nombre cuando aplica) y retorna la respuesta o un código de error. El bot no calcula ni deriva la respuesta (corrección del origen, 2026-10-20); la interpretación de la pregunta es responsabilidad del servicio y, en el lab, de su doble. Los códigos `CAPTCHA_SERVICIO_NO_DISPONIBLE` y `CAPTCHA_MAX_REINTENTOS` se conservan. Ajuste respecto de la versión anterior de esta historia: ya no se describe un resolutor propio del bot, y la indisponibilidad del servicio pasa por reintentos y excepción de sistema antes de la gestión manual.

**Evidencia de apoyo**: DT v1.2 §3.2 (captchas con fallback a revisión humana), §5.2 (`CAPTCHA_MAX_REINTENTOS` = 3) y §6.1 (3 reintentos con backoff, `NUMERO_REINTENTOS_SISTEMA`).

**Regla del "primer nombre" sin definir**: el origen asigna al servicio la interpretación del "primer nombre" en nombres compuestos o en orden invertido. El doble debe fijar una regla y **ninguna fuente la define**: el corpus de captchas (insumo B2) la fijará; hasta entonces los casos de la familia "nombre" usan nombres en orden nombres y apellidos.

**Familias soportadas (origen, banco muestreado el 2026-07-28)**: aritmética ("¿Cuánto es A op B?", op = `+` o `X`), contextual del documento (primeros o últimos dos o tres dígitos) y contextual del nombre (primer nombre o cantidad de letras). El origen pide re-muestrear el banco en el portal vigente antes de estimar; en el lab lo cubre el corpus B2 con el doble.

**Escenario añadido**: pregunta de familia no soportada (la familia "capitales" queda fuera del lab); el nombre del código de error lo fija la spec de F2, porque el origen no lo define.

**Reglas**: captcha determinista resuelto; reCAPTCHA como fallback humano declarado; OCR último recurso; sin comandos de mouse ni reconocimiento de imágenes. Datos 100 % sintéticos.

**Costo y límite**: en el origen comparte el paquete de captcha de CISA con otras historias y se monitorea con un corte diario; en el lab no hay costo ni cuota externa.

**Prioridad y complejidad**: se copian del origen (Must, S); la sustitución local no las cambia.

**Procedencia**: HU de origen `HU-026a` (proyecto OP798698, cliente CISA); no cubierta por la aprobación del 09/10/2026 (solo HU-001, HU-002 y HU-004; C-08, resuelta): su lectura con los usuarios líderes de área sigue pendiente; sesión de alineación del 26–27/10/2026: no aplica a esta historia (la corrección del servicio externo es una confirmación del origen del 2026-10-20).

**Dependencias**: consumida por HU-007 (unidad indivisible) · HU-003 (documento y nombre) · reintentos y registro (HU-018, stub) · doble HTML de la Procuraduría · doble local del servicio de captchas.

## 5. Puntos de control

**No críticos** (permiten continuar; registran en el Reporte de gestiones del Bot):

- Servicio no disponible tras los reintentos → excepción de sistema, `CAPTCHA_SERVICIO_NO_DISPONIBLE`, gestión manual.
- Reintentos agotados → `CAPTCHA_MAX_REINTENTOS`, gestión manual.
- Familia no soportada → error de familia no soportada, gestión manual.

## Checklist INVEST

- [x] **I**ndependent — se entrega junto con HU-007, que la consume (unidad indivisible declarada)
- [x] **N**egotiable — el mecanismo de integración con el servicio (y con su doble) lo define el equipo técnico
- [x] **V**aluable — habilita la validación de identidad en la Procuraduría sin intervención humana
- [x] **E**stimable — tres familias de preguntas y dos códigos de error definidos
- [x] **S**mall — integración para tres familias cabe en 1 sprint
- [x] **T**estable — respuesta esperada por familia y códigos de error verificables como tests
