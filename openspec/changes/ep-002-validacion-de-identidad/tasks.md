## 1. Componentes
- [x] 1.1 `nombres` (HU-008): normalización, puntaje, umbral parametrizable
- [x] 1.2 `captcha` y doble del servicio (HU-026a): familias, códigos, reintentos
- [x] 1.3 Clones de portales (Policía JSF, Procuraduría) con fallos reales: cuota, reto, caída, WAF, webcert-incidentes
- [x] 1.4 `portales` en modo fixture y real (autorización, ventana operativa, verificación de URL)
- [x] 1.5 `ep002` orquestador de referencia y registro sin PII

## 2. Robot de Studio
- [x] 2.1 Grupos HU006, HU007, HU026a, HU008 y registro con navegación en Chrome
- [x] 2.2 `validate_robot` con `perfil:"trycore"` en 0 errores y 0 avisos

## 3. Verificación
- [x] 3.1 Pruebas por escenario Given/When/Then (HU-006, HU-007, HU-026a, HU-008)
- [x] 3.2 Banco: 19 escenarios, dos corridas idénticas
- [x] 3.3 Robot (intérprete con navegador emulado) equivalente al orquestador en los 19 escenarios
- [ ] 3.4 Robot en Studio y Chrome equivalente al orquestador (ver evidencia)
