---
id: HU-006
titulo: Consultar identidad en Policía Nacional
epica: EP-002
prioridad: Must
complejidad: M
estado: lista
---
# Consultar identidad en Policía Nacional

## 1. Declaración de la historia

Como **analista de operaciones**,
quiero **que el bot consulte la identidad del ciudadano en la Policía Nacional (cédula) y extraiga el nombre oficial**,
para **confirmar la identidad del ciudadano sin consultas manuales a portales**.

_Contexto_: Primer intento de validación de identidad, acotado a la consulta y extracción para cédula. **En el lab el portal es un doble HTML** con captcha de casilla y cuota agotada simulada; la cuota agotada es un fallo del servicio de captcha y su resultado es fallback humano (revisión manual). El bot **nunca** automatiza la evasión del captcha de un portal real. La cadena ante fallos de la Policía es la del origen: sin resultado o caída persistente → Procuraduría (HU-007); si esa tampoco resuelve → gestión manual.

## 2. Escenarios — Criterios de aceptación (Given/When/Then)

### Happy path — nombre extraído
- **Dado que** un documento tipo cédula, la casilla de aceptación marcada y el captcha del doble ya resuelto (el lab no ejercita esa resolución; ver §4)
- **Cuando** el bot consulta el doble de la Policía Nacional
- **Entonces** extrae el nombre oficial, que en la pantalla de resultado aparece justo después del texto "Apellidos y Nombres:", para la comparación (en orden apellidos y luego nombres)

### Error — sin resultado
- **Dado que** el doble no arroja resultado para la cédula
- **Cuando** el bot consulta
- **Entonces** marca el caso para consultar la Procuraduría

### Reborde — documento no cédula
- **Dado que** el documento no es cédula (pasaporte, PEP, cédula de extranjería, NIT)
- **Cuando** el bot evalúa el tipo de documento
- **Entonces** omite la Policía y pasa directo a la Procuraduría

### Reborde — portal caído de forma persistente (cadena del origen; HU-023 está fuera del lab)
- **Dado que** el doble de la Policía no responde de forma persistente
- **Cuando** el bot consulta y agota los reintentos (`NUMERO_REINTENTOS_SISTEMA`, por defecto 3)
- **Entonces** marca el caso para consultar la Procuraduría (HU-007)

### Error — cuota agotada simulada (fallo del servicio de captcha; añadido por el lab, ver §4)
- **Dado que** el doble de la Policía responde que la cuota del servicio de captcha está agotada
- **Cuando** el bot consulta
- **Entonces** no intenta resolver ni evadir el captcha, marca el caso para revisión humana (fallback humano), lo registra en el Reporte de gestiones del Bot y continúa con el siguiente radicado

## 3. Flujo de ejecución

> Sin interfaz propia: el bot navega el doble HTML por selectores del DOM, sin comandos de mouse ni reconocimiento de imágenes.

- **Precondición**: solicitante sin obligación activa (HU-005, stub), **no duplicado** (HU-010) y documento tipo cédula de ciudadanía.

| # | Paso (acción del bot) | Referencia |
|---|---|---|
| 1 | Abrir el doble del portal, marcar la casilla "Acepto" (Términos de Uso) y pulsar "Enviar". | Doble HTML de la Policía |
| 2 | Verificar que en "Tipo de documento" quede seleccionada "Cédula de Ciudadanía". | Doble HTML |
| 3 | Diligenciar "Número de documento" con el número de identificación a consultar. | Doble HTML |
| 4 | Con el captcha del doble ya resuelto, pulsar "Consultar". (En el proyecto real el origen marca la casilla "No soy un robot"; el lab no lo ejercita.) Si el doble indica cuota agotada, ir al punto de control de cuota. | Doble HTML (captcha de casilla) |
| 5 | Leer el resultado y extraer el nombre oficial que sigue al texto "Apellidos y Nombres:". La comparación con el nombre de Zeus es de HU-008. | Doble HTML (resultado) |

- **Postcondición**: nombre oficial extraído; si no hay resultado o la Policía cae de forma persistente, el caso pasa a la Procuraduría (HU-007); si la cuota del captcha está agotada, el caso queda en revisión humana

## 4. Notas técnicas

**Sustituido por modo local**: el portal de la Policía Nacional (antecedentes judiciales) → **doble HTML** con casilla de aceptación, tipo de documento, número, captcha de casilla, resultado con "Apellidos y Nombres:" y **cuota agotada simulada**. Estructura y selectores definitivos en el insumo B4 del plan. El origen cita la URL real del portal, que no se usa en el lab (sin red a portales del Estado).

**Captcha (C-05, resuelta)**: sin evasión de un captcha de terceros. El doble simula la casilla y la cuota agotada, y el resultado documentado es fallback humano (el DT §3.2 declara los captchas con fallback a revisión humana). Que el bot marque la casilla "No soy un robot" es un **supuesto del proyecto real que el lab no ejercita**: en el lab el captcha del doble se entrega ya resuelto. El OCR (reconocimiento óptico de caracteres) es último recurso.

**Cadena de fallos (C-04, resuelta)**: se mantiene la del origen (HU-006/007/023): Policía sin resultado o caída persistente → Procuraduría; si la Procuraduría tampoco resuelve, o el fallo es de sistema y se agotan los reintentos → gestión manual (fallback humano). La cuota agotada simulada se trata como fallo del servicio de captcha del doble de la Policía → revisión humana. Los escenarios «caída persistente» y «cuota agotada» se añaden aquí porque HU-023 está fuera del lab.

**Personas jurídicas**: un NIT no es cédula, por lo que ya omite la Policía y pasa a la Procuraduría (regla del origen).

**Orden del nombre**: la Policía siempre devuelve apellidos y luego nombres (confirmado en el origen, 2026-10-01); el doble debe respetarlo. Datos sintéticos: nombres inventados y cédulas ficticias.

**Prioridad y complejidad**: se copian del origen (Must, M); la sustitución local no las cambia.

**Procedencia**: HU de origen `HU-006` (proyecto OP798698, cliente CISA); no cubierta por la aprobación del 09/10/2026 (solo HU-001, HU-002 y HU-004; C-08, resuelta): su lectura con los usuarios líderes de área sigue pendiente; sesión de alineación del 26–27/10/2026: no aplica a esta historia.

**Dependencias**: HU-010 (precede: la identidad se valida tras Cobra y duplicados) · doble HTML de la Policía · reintentos y reporte (HU-018 y HU-027, stub) · HU-023 fuera del lab.

## 5. Puntos de control

**Críticos** (detienen la ejecución del bot y generan alerta):

- La resiliencia del portal (captcha no resuelto tras N intentos, portal caído persistente) se controla en HU-023, fuera del lab; en el lab no se define punto crítico propio.

**No críticos** (permiten continuar; registran en el Reporte de gestiones del Bot):

- Policía sin resultado para la cédula → marca el caso para la Procuraduría y continúa.
- Documento distinto de cédula → omite la Policía y pasa a la Procuraduría.
- Portal caído de forma persistente → tras los reintentos, marca el caso para la Procuraduría y continúa.
- Cuota del captcha agotada → revisión humana (fallback humano); el bot continúa con el siguiente radicado.

## Checklist INVEST

- [x] **I**ndependent — se entrega con el doble de la Policía, sin depender de otras historias de construcción
- [x] **N**egotiable — el "cómo" (selectores, estructura del doble) se puede negociar con el equipo
- [x] **V**aluable — confirma la identidad sin consulta manual y deja explícito el camino humano
- [x] **E**stimable — los pasos del portal y los resultados del doble están definidos
- [x] **S**mall — cinco pasos y cinco escenarios caben en 1 sprint
- [x] **T**estable — cada AC se verifica contra una respuesta controlada del doble
