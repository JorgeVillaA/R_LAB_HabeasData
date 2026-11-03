## ADDED Requirements

### Requirement: Búsqueda de duplicados de exclusión (HU-010)
El robot SHALL buscar, antes de la identidad, cada valor de cada canal (correo y celular) por separado: primero en la maestra y luego en la base de exclusión con llave compuesta identificación + valor; solo los valores duplicados generan la excepción de negocio 4 y los demás continúan.

#### Scenario: Sin duplicado
- **WHEN** ningún valor del caso figura en la base de exclusión
- **THEN** el caso queda sin duplicado y sigue a la validación de identidad

#### Scenario: Excepción de negocio 4 por valor
- **WHEN** la combinación identificación + celular o identificación + correo ya existe
- **THEN** el robot escribe la nota de duplicado en Gestión → Detalle, la registra en el reporte y, si todos los valores eran duplicados, el caso no sigue a identidad

#### Scenario: Varios valores en un canal
- **WHEN** el caso trae varios celulares o correos separados por «/»
- **THEN** consulta cada valor por separado y solo los que coinciden se marcan duplicados; los demás continúan

#### Scenario: Repositorio que no responde
- **WHEN** el repositorio falla en un caso
- **THEN** reintenta tres veces, marca excepción de sistema del caso y continúa con el siguiente; si ningún caso puede consultarlo, la ejecución se detiene y alerta

### Requirement: Registro de la exclusión (HU-011)
El robot SHALL registrar, tras la identidad coincidente, la fila de `Exclusion` y una fila de 14 columnas por valor en `Celulares` o `Correos`, cruzar cada valor contra su maestra y eliminar el registro de la maestra una vez confirmada la inserción.

#### Scenario: Fila insertada y maestra depurada
- **WHEN** un caso queda validado
- **THEN** quedan registradas las filas con sus 14 columnas, los valores verificados contra la maestra y el registro correspondiente eliminado de ella

#### Scenario: Contacto ya presente
- **WHEN** un contacto ya existe en la base de celulares o correos
- **THEN** se marca como ya presente y no se duplica

#### Scenario: Falla persistente al insertar o eliminar
- **WHEN** insertar falla tras tres reintentos
- **THEN** el caso queda en excepción de sistema y no se elimina nada de la maestra
- **WHEN** eliminar falla tras tres reintentos
- **THEN** la fila ya insertada se conserva, el caso queda en excepción de sistema y el bot continúa

### Requirement: Transacciones por etapa
El repositorio SHALL guardar una fila en `Transacciones` en cada transición de cada caso, incluidos los fallos, con estados 1 Sin Procesar, 2 Procesando, 3 Exitoso, 4 No Exitoso y 5 Procesado Parcialmente.

#### Scenario: Recorrido de un radicado
- **WHEN** un caso recorre las etapas
- **THEN** su recorrido completo, con estado anterior y nuevo, resultado y motivo, es consultable en orden
