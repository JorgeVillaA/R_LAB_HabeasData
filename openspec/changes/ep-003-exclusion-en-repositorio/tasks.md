## 1. Componentes
- [x] 1.1 `repositorio`: MER de 8 tablas, `Transacciones`, maestras, reintentos x3 y consultas de revisión
- [x] 1.2 `ep003`: HU-010 (duplicados por valor) y HU-011 (inserción, cruce, eliminación) con el stub de Cobra
- [x] 1.3 Integración en el orquestador (`ep002.procesar` con repositorio) y detención crítica

## 2. Robot de Studio
- [x] 2.1 Grupos HU010 y HU011 en el bucle por radicado, con pasos que reconstruyen su sesión (D-21)
- [x] 2.2 `validate_robot` con `perfil:"trycore"` en 0 errores y 0 avisos

## 3. Verificación
- [x] 3.1 Pruebas por escenario Given/When/Then (HU-010, HU-011, repositorio)
- [x] 3.2 Banco: 9 escenarios, dos corridas idénticas
- [x] 3.3 Robot (intérprete) equivalente al orquestador en 8 de 9 (la detención crítica solo compara decisiones)
- [x] 3.4 Robot en Studio y Chrome equivalente al orquestador en 8 de 9 (la novena se omite por la línea final del log)
