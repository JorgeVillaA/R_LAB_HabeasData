# ingesta-radicados Specification

## Purpose
TBD - created by archiving change ep-001-ingesta-y-lectura-de-casos. Update Purpose after archive.

## Requirements

### Requirement: Selección de radicados de Exclusión de Datos (HU-002)
El robot SHALL seleccionar de la API de Zeus los radicados cuya tipología es «EXCLUSION DE DATOS», descartando los de identificación «NO APORTA», por lotes y en orden descendente de `IDRADICADO`, y SHALL contar y reportar los descartados.

#### Scenario: Radicados filtrados
- **WHEN** existen radicados de exclusión y radicados ajenos
- **THEN** el robot obtiene solo los de exclusión con identificación presente y reporta los descartados

#### Scenario: Filtro o campo no reconocido
- **WHEN** la API responde 400
- **THEN** el robot detiene la ejecución, alerta y deja registro en el log

#### Scenario: Token ausente o vencido
- **WHEN** la API responde 401 y la renovación del token también falla
- **THEN** el robot detiene la ejecución y alerta

#### Scenario: Tipología ausente o bandeja vacía
- **WHEN** el filtro no devuelve radicados
- **THEN** el robot distingue por consulta general entre tipología ausente, bandeja vacía y solo descartados, registra «0 casos» y AGENDA el reintento: espera MinutosEntreReintentos y reconsulta hasta MaximoReintentosDiarios o hasta que aparezcan casos (CADENCIA_REINTENTO_BANDEJA_VACIA)

### Requirement: Lectura de datos paramétricos (HU-003)
El robot SHALL leer cada radicado por `IDRADICADO` y extraer nombre, tipo y número de identificación, fecha de recepción, correos y teléfonos, tratando «No aporta» y vacíos como ausentes, separando por «/» cada valor, clasificando cada teléfono por dígitos y conservando el radicado padre cuando exista.

#### Scenario: Extracción completa
- **WHEN** el radicado trae todos sus campos
- **THEN** el robot extrae los datos y los canales presentes

#### Scenario: Clasificación del teléfono
- **WHEN** el teléfono trae 10 dígitos que inician en 3, 7 dígitos u otro patrón
- **THEN** lo clasifica como celular, fijo o sin clasificar y conserva el valor tal cual

#### Scenario: Varios valores en un canal
- **WHEN** un canal trae valores separados por «/»
- **THEN** el robot conserva cada valor por separado

#### Scenario: Radicado con padre
- **WHEN** el radicado tiene radicado padre
- **THEN** el robot lo guarda para plantillas y reporte y sigue procesando el hijo

#### Scenario: Radicado no legible
- **WHEN** la lectura del radicado falla
- **THEN** el robot registra excepción de sistema y continúa con el siguiente radicado

### Requirement: Validación de campos obligatorios (HU-004)
El robot SHALL verificar que cada caso tenga nombre, tipo y número de identificación y al menos un canal de contacto, y SHALL registrar un comentario con el motivo en Gestión → Detalle cuando falte alguno (excepción de negocio 1).

#### Scenario: Datos completos
- **WHEN** el caso tiene los obligatorios y un canal
- **THEN** avanza a la validación de deuda

#### Scenario: Identificación incompleta
- **WHEN** falta nombre, tipo o número de identificación, o el valor es vacío, en blanco o «No aporta»
- **THEN** el robot registra el comentario de la excepción de negocio 1

#### Scenario: Sin ningún canal de contacto
- **WHEN** no hay correo ni teléfono
- **THEN** el robot registra el comentario de la excepción de negocio 1

#### Scenario: Escritura rechazada
- **WHEN** la escritura del comentario falla
- **THEN** el robot registra excepción de sistema y continúa
