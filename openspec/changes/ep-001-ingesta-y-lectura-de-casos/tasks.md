## 1. Infraestructura
- [x] 1.1 Configuración en tres JSON (`ConfiguracionMaquina`, `ConfiguracionProceso`, `Maestro_Configuracion`)
- [x] 1.2 Estructura de carpetas creada por el bot, dos logs por día de cuatro campos y reporte de gestión
- [x] 1.3 Cliente de la API de Zeus (OAuth, OData, 200/400/401/403/404) y credencial desde el Administrador de credenciales de Windows
- [x] 1.4 Redacción de PII en modo real

## 2. Historias
- [x] 2.1 HU-002 selección de radicados (filtro compuesto, lote, orden, descartados)
- [x] 2.2 HU-003 lectura y normalización (ausentes, `/`, teléfono, padre/hijo)
- [x] 2.3 HU-004 completitud y comentario de la excepción de negocio 1 (escritura separada)

## 3. Robot de Studio
- [x] 3.1 `LabHabeasData` legible a cliente (grupos por historia) y `habeasdata.pasos`
- [x] 3.2 `validate_robot` con `perfil:"trycore"` en 0 errores y 0 avisos
- [x] 3.3 `VerificacionVisualDobles` en Chrome con captura del MCP

## 4. Verificación
- [x] 4.1 Pruebas por escenario Given/When/Then y test estructural de lineamientos
- [x] 4.2 Banco determinista: 16 escenarios, dos corridas idénticas
- [x] 4.3 Equivalencia del robot de Studio con el orquestador (16 de 16)
- [x] 4.4 Mutación sobre las reglas de negocio y el contrato
