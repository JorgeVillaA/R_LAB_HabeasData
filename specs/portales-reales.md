# Portales del Estado — modo real (decisión de Villa, 29/10)

EP-002 consulta los **portales reales** de la Policía Nacional y la Procuraduría. Los dobles locales quedan como fixture offline del banco determinista, igual que con la API de Zeus: el banco corre reproducible sin red, y el modo real va contra los sitios de verdad.

## Portales

| Portal | URL operativa | Qué se consulta |
|---|---|---|
| Policía Nacional — antecedentes | `https://antecedentes.policia.gov.co:7005/WebJudicial/` | Nombre asociado a la cédula de ciudadanía (aceptar términos, tipo de documento, número, consultar) |
| Procuraduría — consulta de antecedentes | `https://apps.procuraduria.gov.co/webcert/consulta-de-antecedentes.aspx` | Nombre en el bloque «Datos del ciudadano» (se lee en línea, sin descargar PDF) |

Nota: el dominio `webcert` quedó sin efecto el 01/10/2026; la URL de arriba es la documentada como vigente en HU-007 §4. Verificarla antes de la primera corrida real.

## Política de captchas (innegociable)

| Caso | Qué se hace |
|---|---|
| **Procuraduría — captcha de pregunta determinista** (aritmética, dígitos del documento, nombre) | Lo resuelve el componente del lab (equivalente al servicio externo contratado por CISA en HU-026a). Es una pregunta de negocio, no un sistema anti-bot |
| **Policía — reCAPTCHA v2 («No soy un robot»)** | **NO se automatiza su evasión.** El bot se detiene y lo resuelve **una persona** (human-in-the-loop), o se deriva el caso a revisión manual. Es lo que declara el propio diseño de CISA: `componentes con fallback a revisión humana` |
| Cuota agotada / portal caído / sin respuesta | Excepción de sistema con reintentos (3 con backoff); agotados, gestión manual y registro en la tabla `Transacciones` |

## Requisitos del modo real

1. **Red** a los dos portales (son públicos, sin credenciales).
2. **PII**: los resultados traen datos de personas reales → toda evidencia redactada; la captura de pantalla se toma del doble o se recorta antes de compartirla.
3. **Ventana operativa**: los portales del Estado tienen disponibilidad limitada; el lab respeta la ventana parametrizada y no fuerza corridas fuera de ella.
4. **Trazabilidad**: cada consulta real deja fila en `Transacciones` (etapa, resultado, motivo), incluidos los fallos y los casos que pasaron por revisión humana.

## Modos de corrida (actualizados)

| Modo | Zeus | Portales del Estado | Para qué |
|---|---|---|---|
| `fixture` (por defecto) | doble | dobles | Banco determinista, sin red. Revisión y CI |
| `real` | API de QA de CISA | portales reales | Integración de verdad; exige red, credencial de Zeus y PII redactada |
