## ADDED Requirements

### Requirement: Consulta de identidad en la Policía (HU-006)
El robot SHALL consultar la Policía para documentos de cédula de ciudadanía y extraer el nombre que sigue a «Apellidos y Nombres:». El robot SHALL NOT evadir el reCAPTCHA: ante cuota agotada, reto de imágenes o modo real, el caso queda en revisión humana.

#### Scenario: Nombre extraído
- **WHEN** la cédula tiene resultado
- **THEN** el robot lee el nombre oficial (apellidos y luego nombres) y lo compara (HU-008)

#### Scenario: Sin resultado o portal caído
- **WHEN** la Policía no devuelve resultado o no responde tras los reintentos
- **THEN** el robot consulta la Procuraduría

#### Scenario: Cuota agotada o reto de imágenes
- **WHEN** el portal informa cuota agotada del reCAPTCHA o escala a un reto de imágenes
- **THEN** el caso queda en revisión humana, se registra y el robot continúa con el siguiente radicado

### Requirement: Consulta de la Procuraduría (HU-007)
El robot SHALL consultar la Procuraduría para documentos que no son cédula o como fallback, leer el bloque «Datos del ciudadano» en línea y derivar a gestión manual los NIT de dígitos distintos de 10 sin consultar.

#### Scenario: Resultado en línea
- **WHEN** el captcha se resuelve y el portal responde
- **THEN** el robot obtiene el nombre y el estado de antecedentes de la misma página, y el estado no altera la validación

#### Scenario: Portal caído, bloqueado o con estructura distinta
- **WHEN** la Procuraduría no responde, la bloquea el WAF o devuelve el formulario de atención de incidentes
- **THEN** el robot marca excepción de sistema `PORTAL_NO_DISPONIBLE` y deriva a gestión manual

#### Scenario: NIT inválido
- **WHEN** el NIT no tiene exactamente 10 dígitos
- **THEN** el robot no consulta y deriva a gestión manual

### Requirement: Captcha de pregunta determinista (HU-026a)
El robot SHALL enviar la pregunta (más documento y nombre cuando aplica) al servicio de captchas y usar su respuesta; el robot SHALL NOT calcularla.

#### Scenario: Respuesta rechazada o familia no soportada
- **WHEN** el portal rechaza la respuesta o el servicio no soporta la familia en N=3 intentos
- **THEN** el robot retorna `CAPTCHA_MAX_REINTENTOS` y deriva a gestión manual

#### Scenario: Servicio no disponible
- **WHEN** el servicio no responde tras los reintentos
- **THEN** el robot retorna `CAPTCHA_SERVICIO_NO_DISPONIBLE` y deriva a gestión manual

### Requirement: Comparación de nombres (HU-008)
El robot SHALL comparar el nombre de Zeus con el del portal normalizados y sin depender del orden, con el umbral `UMBRAL_COINCIDENCIA_NOMBRES` del archivo maestro.

#### Scenario: Coincidencia
- **WHEN** el puntaje es mayor o igual que el umbral
- **THEN** la identidad queda validada

#### Scenario: Excepción de negocio 3
- **WHEN** el puntaje es menor que el umbral o el nombre del portal es incompleto
- **THEN** el robot escribe el comentario en Gestión → Detalle y registra la excepción de negocio 3
