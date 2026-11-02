## Why

EP-002 concentra la lógica que elimina el error humano de validación de identidad (O2): consulta la Policía Nacional (cédula) y la Procuraduría (otros documentos o fallback), resuelve el captcha de pregunta de la Procuraduría con el servicio de captchas (HU-026a) y compara el nombre oficial con el de Zeus (HU-008). Origen de la excepción de negocio 3.

## What Changes

- HU-006: consulta de la Policía en Chrome (términos, cédula, casilla reCAPTCHA que el bot NO evade: en modo real o con cuota agotada o reto de imágenes el caso queda en revisión humana); sin resultado o caída persistente deriva a la Procuraduría.
- HU-007: consulta de la Procuraduría (términos, formulario, bloque «Datos del ciudadano» en línea); NIT con dígitos distintos de 10 y tipos sin consulta van a gestión manual sin consultar; portal caído, WAF o `webcert` con el formulario de incidentes son excepción de sistema.
- HU-026a: servicio de captchas (interfaz del contratado por CISA; en el lab su doble) con familias aritmética, documento y nombre; `CAPTCHA_SERVICIO_NO_DISPONIBLE` y `CAPTCHA_MAX_REINTENTOS` (N=3); la familia «capital» no se resuelve y se refresca la pregunta.
- HU-008: comparación de nombres normalizados sin depender del orden, umbral `UMBRAL_COINCIDENCIA_NOMBRES` (0.80) del archivo maestro; excepción de negocio 3 con comentario en Zeus.
- Clones técnicos de los portales (`dobles/portales`: fieles en campos y flujo, sin identidad oficial) y dos modos (`fixture` por defecto, `real` con autorización, ventana operativa y verificación de URL).
- Robot de Studio: grupos por HU con navegación en Chrome; banco de 19 escenarios; comparador robot-contra-orquestador (intérprete con navegador emulado en la suite y Studio+Chrome en la corrida real).

## Capabilities

### New Capabilities
- `validacion-identidad`: consulta de identidad en portales del Estado, captcha y comparación de nombres.

### Modified Capabilities
(ninguna)

## Supuestos vetables por Villa

- **Insumo B3 (métrica de nombres)**: Dice sobre componentes del nombre normalizado (sin tildes, mayúsculas, sin partículas); garantía de 1.0 si todos los componentes del nombre más corto (≥ 2) están en el otro; portal con un solo componente va a excepción 3. Lo produce el agente; lo aprueba Villa.
- **Regla del «primer nombre»** del doble de captchas: primer componente en el orden recibido (nombres y luego apellidos).
- **Casilla del reCAPTCHA en fixture**: el clon la recibe marcada por quien consulta; es un fixture, no una resolución de captcha (D-05).
- **PEP**: HU-006 manda el PEP directo a la Procuraduría, pero su desplegable no trae ese tipo; el lab lo deriva a gestión manual (escenario 18). **Pendiente de decisión de Villa.**
- **Reintentos al abrir un portal**: el robot reintenta 3 veces (= `NUMERO_REINTENTOS_SISTEMA`) con bloques visibles por intento y espera `Portales.BackoffSegundos`.
- **Ruta del servicio de captchas**: pendiente de Comercial ↔ CISA; en el lab, el doble local detrás de la misma interfaz.

## Impact

- Código: `Scripts/habeasdata/` (`nombres`, `captcha`, `portales`, `ep002`, `pasos`), `dobles/portales/`, `Robots/`, `Configuracion/`, `banco/`, `tests/`.
- Dependencias: ninguna (solo biblioteca estándar de Python).
- Sin consulta a los portales reales: faltan autorización de uso, red y la verificación de la URL vigente de la Procuraduría.

## Trazabilidad

- Épica: EP-002 — Validación transaccional e identidad (`docs/03-backlog/epicas.md`).
- Historias: HU-006, HU-007, HU-008, HU-026a (EP-006, indivisible con HU-007)
- Documentos de las HU: `docs/04-historias/`.
- Fuera de esta épica: HU-005 (stub de Cobra), HU-023 y HU-024 (resiliencia y estructura de portales), HU-010/HU-011 (EP-003).
