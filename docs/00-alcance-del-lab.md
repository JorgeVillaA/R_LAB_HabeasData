# Alcance del lab — R_LAB_HabeasData

> Documento de alcance del laboratorio agentizado EP-001–EP-003 (más EP-006 en lo que sirve a HU-007).
> Solo documentación de discovery: **no se construye el robot** ni se toca la configuración del arnés.
> Fuentes: (1) historias de usuario (HU) del proyecto real OP798698 (cliente CISA), carpeta `docs/04-historias/` y `docs/03-backlog/epicas.md`; (2) nota «Lab agentizado EP-001–003 — plan» del 2026-10-29; (3) **Diseño técnico v1.2** de CISA («DiseñoTécnico Habeas Data - Cisa_.docx», en adelante DT) como fuente de verdad de arquitectura, MER y parámetros; (4) nota «Estado de integración y control de cambios 01 (oct-2026)» (en adelante *nota de integración*).
> **Directriz de Villa (2026-10-29): el cliente de Zeus se implementa contra la API real** (§13); el doble local pasa a ser solo fixture offline del banco determinista.
> **Estado del plan: G0 pendiente de aprobación.** Estos documentos son insumo de F0/F2 y **no declaran G0 cerrado** (C-15).

## 1. Propósito

Demostrar con evidencia que un agente construye una rebanada real del robot `R_HabeasData` contra un contrato, cubriendo tres capas: consumo de API (interfaz de programación de aplicaciones), scraping con captcha y persistencia. El lab demuestra **método y arquitectura**, no integración con CISA. Todo corre en modo local aislado (loopback, sin VPN, sin credenciales de cliente, sin salida a internet en la corrida oficial).

Decisiones de gobierno ya tomadas (no se reabren aquí): el lab lo decide Villa; CISA solo es insumo externo opcional.

## 2. Alcance (qué se especifica)

| Épica | HU | Qué especifica | Dependencia externa → doble local |
|---|---|---|---|
| EP-001 | HU-002 | Filtro de radicados de «Exclusión de Datos» con semántica OData (protocolo abierto de datos) | API de Zeus → doble de la API |
| EP-001 | HU-003 | Extracción y normalización de datos paramétricos, clasificación de teléfono, división por `/`, radicado padre/hijo | API de Zeus → doble de la API |
| EP-001 | HU-004 | Validación de existencia de campos obligatorios; excepción de negocio 1 | API de Zeus + escritura en Zeus → doble de la API y doble de escritura |
| EP-002 | HU-006 | Consulta de identidad en la Policía Nacional (cédula) | Portal de la Policía → doble HTML |
| EP-002 | HU-007 | Consulta de identidad en la Procuraduría (resultado en línea) | Portal de la Procuraduría → doble HTML |
| EP-006 | HU-026a | Resolución del captcha de pregunta determinista, al servicio de HU-007 | Servicio externo de captchas → doble local tras la misma interfaz |
| EP-002 | HU-008 | Comparación de nombres (umbral 0.80, sin depender del orden) | Lógica pura; la escritura del comentario usa el doble de escritura |
| EP-003 | HU-010 | Búsqueda de duplicados en las bases de exclusión | NocoDB de CISA → repositorio local |
| EP-003 | HU-011 | Registro de la exclusión, cruce y eliminación en bases maestras | NocoDB de CISA → repositorio local |

Nueve historias en el alcance (HU-002, HU-003, HU-004, HU-006, HU-007, HU-008, HU-010, HU-011 y HU-026a). Ver C-01.

## 3. Fuera de alcance

| Elemento | Razón |
|---|---|
| **HU-001** (origen: «Iniciar sesión en Zeus Web») | Por la decisión de integración por API deja de ser un inicio de sesión: se reescribe como **obtención y renovación de token OAuth** (autorización abierta; el DT/nota de integración documentan OAuth 2.0 *client credentials*, token Bearer de 300 s sin refresh). La reescritura es **insumo para el PO** (propietario del producto), no trabajo del lab. En el lab el token válido es precondición implícita y el doble responde 401 si falta. |
| **HU-005** (Cobra: titular/codeudor activo) | Cobra no tiene endpoints entregados (nota de integración §3 y §4). Se declara **stub** (ver §6). |
| **HU-009** (enrutamiento gestor → agencia → coordinador) | Cobra sin endpoints. Se declara **stub** (ver §6). |
| HU-012 a HU-018, HU-027 a HU-032 (notificación, plantillas, correo, cierre, log, excepciones, reporte, ventana, RCC, Jefatura) | Envío al ciudadano, firma, código QR y aprobación de Jefatura quedan fuera del lab por el plan (§2). |
| HU-020, HU-021, HU-022, HU-025, HU-026b | Componentes reutilizables y playbook: no se construyen; HU-026b (familia «capitales») queda fuera del lab. |
| HU-023 (resiliencia de la consulta a la Policía) y HU-024 (cambios de estructura de la Procuraduría) | No se especifican como historias; su comportamiento relevante (caída persistente de la Policía → Procuraduría) se documenta dentro de HU-006 (C-04). |
| Resolución automática del captcha de la Policía (reCAPTCHA) | **Nunca se automatiza la evasión de un captcha de terceros.** Fallback humano (C-05). |
| Manual de entrega y capturas definitivas | El plan las excluye (§2). |

## 4. Dobles locales

Cada doble implementa el contrato documentado (campos, códigos de error, estructura descrita por las HU) y se versiona junto al banco. Un doble que devuelve `OK` fijo no cuenta como doble.

| Sistema real | Doble local | Contrato que debe cumplir | Qué simula |
|---|---|---|---|
| API de Zeus (lectura) | Servicio HTTP en loopback | Los **48 campos del manual**; semántica OData `$filter`, `$select`, `$first`; consulta general sin filtro (necesaria para distinguir «tipología ausente» de «bandeja vacía», C-13); códigos **200, 400 y 401** | Radicados con todos los bordes (sin canal, «No aporta», multivalor `/`, padre/hijo, NIT, nombre invertido); radicados ajenos que el filtro debe excluir |
| Escrituras en Zeus (comentario en «Gestión del radicado» → «Detalle») | Doble de escritura | Respuesta de éxito y errores documentados en la spec del doble | Aceptación del comentario y rechazo (supuesto del lab, C-09) |
| Portal de la Policía Nacional | Doble HTML | Casilla de aceptación, tipo de documento, número, **captcha de casilla**, resultado con «Apellidos y Nombres:» | Resultado con nombre, sin resultado, portal caído persistente y **cuota agotada simulada** = fallo del servicio de captcha → revisión humana (C-04, C-05). El lab **no ejercita** el marcado de la casilla del portal real |
| Portal de la Procuraduría | Doble HTML tipo formulario | Desplegable de tipo de documento, número, **captcha de pregunta determinista**, bloque «Datos del ciudadano»; **no depende del dominio** (el dominio `webcert` quedó sin efecto el 2026-10-01, C-14) | Resultado con y sin antecedentes, respuesta sin nombre, portal sin respuesta, captcha rechazado |
| Servicio externo de resolución de captchas (contratado por CISA) | **Doble local detrás de la misma interfaz** | Entrada: pregunta (+ documento/nombre cuando aplica); salida: respuesta o código de error. Familias aritmética, dígitos del documento y nombre (la familia «capitales» queda fuera) | Disponible / no disponible (C-03). El bot no calcula la respuesta |
| NocoDB de CISA | Repositorio local: **NocoDB npm 0.301.3 en loopback** | **MER de 8 tablas** (abajo); bases `Celulares` y `Correos` de **14 columnas** que arrancan con `ID CLIENTE`, `ID CODEUDOR`, sin columna `FIJO`, en datos sintéticos | Disponible / sin respuesta |

**MER del repositorio local (DT §4.6 y §5.4; C-12):**

| Tabla | Contenido | Relación |
|---|---|---|
| `Insumo` | Datos del radicado extraídos de Zeus y su estado de ejecución | 1:N con `Excepciones`; 1:1 con `Exclusion`; `Gestores` N:1 con `Insumo` |
| `Excepciones` | Cada excepción de negocio (1–4) o de sistema por radicado | N:1 con `Insumo` |
| `Exclusion` | Base centralizada de exclusiones efectivas | 1:1 con `Insumo`; 1:N con `Celulares` y `Correos` |
| `Celulares` | Bloqueo de celulares vinculado a cada exclusión (14 columnas) | N:1 con `Exclusion` |
| `Correos` | Bloqueo de correos vinculado a cada exclusión (14 columnas) | N:1 con `Exclusion` |
| `Gestores` | Relación agencia → coordinador → correo, para enrutamiento | N:1 con `Insumo` |
| `Parametros` | Parametría operativa (umbrales, ventanas, rutas) | — |
| `LogEjecucion` | Consolidado por ejecución: casos procesados, excepciones y tiempos | — |

Según el DT, solo `Exclusion`, `Celulares` y `Correos` persisten; el resto se depura por parámetro. **Propuesta C-16 (pendiente de Villa)**: además del MER, el lab añade `MaestraCelulares` y `MaestraCorreos` (14 columnas cada una) como insumo de cruce y eliminación.

**Parámetros por defecto (DT §5.2, usados por las HU):** `UMBRAL_COINCIDENCIA_NOMBRES` = 0.80; `NUMERO_REINTENTOS_SISTEMA` = 3 con backoff; `CAPTCHA_MAX_REINTENTOS` = 3 (N parametrizable). `CADENCIA_REINTENTO_BANDEJA_VACIA` no figura en el DT: lo fija el equipo técnico (PO, origen HU-002).

Los supuestos de cada doble se registran en su spec como deuda para la integración real.

## 5. Sustituciones por modo local

| HU | Origen | En el lab |
|---|---|---|
| HU-002 | Navegar la bandeja «Por gestionar», agrupar por tipo de documento y abrir cada radicado para leer «PQR CORRESPONDE A» | Una consulta OData: `PQRCORRESPONDEA eq 'EXCLUSION DE DATOS'` contra el doble de la API, más la consulta general para distinguir ausencia de tipología de bandeja vacía |
| HU-003 | Leer la pestaña «Campos Adicionales» y «Radicados padres / hijos» en Zeus Web | Lectura de campos y de la relación padre/hijo por el doble de la API |
| HU-004 | Comentario en Zeus Web | Comentario por el doble de escritura |
| HU-006 | Portal real de la Policía y reCAPTCHA | Doble HTML con captcha de casilla y cuota agotada simulada (fallback humano) |
| HU-007 | Portal real de la Procuraduría | Doble HTML tipo formulario con captcha de pregunta determinista |
| HU-026a | Servicio de un tercero contratado por CISA | Doble local del servicio tras la misma interfaz |
| HU-008 | Comparación por primer nombre + primer apellido; comentario en Zeus | `UMBRAL_COINCIDENCIA_NOMBRES` 0.80 sin depender del orden (DT §5.2); comentario por el doble de escritura |
| HU-010, HU-011 | NocoDB de CISA | Repositorio local NocoDB 0.301.3 con el MER de 8 tablas y datos sintéticos |

## 6. Stubs declarados (HU fuera del lab que las HU del lab consumen)

| HU | Qué entrega el stub | Quién lo consume |
|---|---|---|
| HU-005 (Cobra: deudor activo) | Resultado fijo «sin obligación activa» por fixture, para que el caso llegue a duplicados | Precondición de HU-010 |
| HU-009 (enrutamiento) | `GESTOR` y `SUCURSAL` fijos por fixture | Columnas de HU-011 |
| HU-018 (reintentos x3, excepción de sistema) y HU-027 (reporte de gestiones) | Contrato mínimo: reintentar 3 veces (`NUMERO_REINTENTOS_SISTEMA`), marcar excepción de sistema y registrar el caso. Las columnas del reporte para el lab las define Villa | HU-003, HU-007, HU-010, HU-011, HU-026a |

Un stub es un contrato declarado, no una implementación: su comportamiento fijo se documenta y no se presenta como evidencia de integración (C-07).

## 7. Decisiones fijas (no se reabren)

- **Proyecto**: `R_LAB_HabeasData`. No sigue el patrón `R_<Empresa>_<Proyecto>` porque es un laboratorio propio, no una entrega de cliente; la razón queda aquí para que la revisión de código no lo devuelva como defecto de nomenclatura.
- **Raíz de ejecución**: la carpeta de este repositorio, declarada como llave de configuración `RutasProceso.RutaRaiz`; nunca hardcodeada.
- **Estructura en ejecución** (anexo Trycore V1.0; la crea el propio bot al arrancar): `Configuracion/`, `Logs/Sistema|Auditoria/YYYY/MM`, `CapturasPantalla/Proceso|Error/YYYY/MM`, `Archivos Temporales/`, `Documentos/`, `Scripts/`, `Reportes/YYYY/MM`.
- **Logs**: dos archivos por día; cuatro campos fijos, en este orden: `Ip;Fecha;AplicativoModulo;Observacion`, separados por `;`; campo faltante = `NO APLICA`; escritura en el momento del evento.
- **Configuración**: tres JSON — `ConfiguracionMaquina` (máximo 4 diccionarios), `ConfiguracionProceso` y `Maestro_Configuracion` (el «archivo maestro» del DT §5.2). Nada paramétrico en la lógica.

## 8. Reglas de negocio cerradas (copiadas tal cual)

1. Obligatorios: nombre + tipo + número de identificación, y al menos un canal de contacto.
2. El literal «No aporta» equivale a campo ausente.
3. El teléfono se clasifica por dígitos: 10 dígitos que inician en 3 = celular; 7 dígitos = fijo; cualquier otro = sin clasificar.
4. Varios valores en un mismo campo se separan por `/` sin espacios; cada valor se trata por separado.
5. NIT (Número de Identificación Tributaria) de exactamente 10 dígitos; si no cumple, no se consulta la Procuraduría y el caso va a gestión manual.
6. Se procesa el radicado hijo; el padre se usa en plantillas y reporte.
7. Umbral de coincidencia de nombres: 0.80 (`UMBRAL_COINCIDENCIA_NOMBRES`, DT §5.2), sin depender del orden de nombres y apellidos.

**Captchas**: se resuelve el determinista; el reCAPTCHA queda como fallback humano declarado; el OCR (reconocimiento óptico de caracteres) es último recurso; sin comandos de mouse ni reconocimiento de imágenes (el scraping va por selectores del DOM).

**Datos**: 100 % sintéticos, cero PII (información personal identificable). Nombres inventados y cédulas ficticias en repositorio, fixtures, capturas y logs.

## 9. Contradicciones entre fuentes

Resumen de estado (detalle debajo):

| # | Estado | HU ajustadas |
|---|---|---|
| C-01 | Resuelta | — (alcance sin cambio) |
| C-02 | Resuelta | HU-008 |
| C-03 | Resuelta | HU-026a, HU-007 |
| C-04 | Resuelta | HU-006, HU-007 |
| C-05 | Resuelta | HU-006 |
| C-06 | Resuelta | — |
| C-07 | Resuelta | — |
| C-08 | Resuelta | Procedencia de todas las HU |
| C-09 | Resuelta para el lab (endpoint real pendiente con IT CISA) | — |
| C-10 | Resuelta | HU-011 |
| C-11 | Resuelta, con residual en C-16 | HU-010, HU-011 |
| C-12 | Resuelta | HU-010, HU-011 |
| C-13 | Resuelta | HU-002 |
| C-14 | Resuelta | HU-007 |
| C-15 | Resuelta (declarada) | — |
| C-16 | Resuelta con propuesta (**propuesta, pendiente de Villa**) | HU-010, HU-011 |
| C-17 | Resuelta para el lab | HU-003 |
| C-18 | Resuelta para el lab (confirmar con respuesta real) | HU-003, HU-004 |
| C-19 | Resuelta por directriz de Villa; **ejecución real bloqueada** | HU-002, HU-003, HU-004 |
| C-20 | Resuelta con la regla del validador (pendiente de revisión humana) | — |
| C-21 | Resuelta con el manual (avisar a Villa) | — |
| C-22 | **Abierta: decide Villa** | HU-002, HU-004 |

### C-01 — Cantidad de historias del lab — Resuelta
- **Resolución**: quedan **9 HU** (HU-002, 003, 004, 006, 007, 026a, 008, 010, 011). El plan agrupaba HU-007 y HU-026a en una sola fila de su tabla de alcance porque HU-026a existe solo al servicio de HU-007 (unidad indivisible); eso explica que la tabla del plan tenga una fila menos que HU. El alcance no cambia.
- **Evidencia**: plan del lab §2 (fila «HU-007 + HU-026a»); `epicas.md` del origen, nota de secuenciación EP-002 ↔ EP-006.
- **Residual**: el texto del plan dice «siete historias» y su tabla trae ocho filas; las fuentes no explican esa diferencia. Las métricas del plan («7 de 7») deben recalcularse sobre 9.

### C-02 — Regla de coincidencia de nombres (HU-008) — Resuelta
- **Resolución**: manda el DT §5.2: `UMBRAL_COINCIDENCIA_NOMBRES` = **0.80**, parametrizable, sobre el nombre normalizado y sin depender del orden de nombres y apellidos. La regla del origen «primer nombre + primer apellido» queda como el caso que **garantiza coincidencia plena (score 1.0)**, no como el único criterio.
- **Evidencia**: DT §5.2 (parámetro y valor por defecto 0.80; «umbral de score para considerar coincidencia de identidad») y tabla `Parametros` (`UmbralCoincidenciaNombres`, ajustable en caliente); nota de integración §5 (regla «nombres sin depender del orden»). La formulación «sobre el nombre normalizado» proviene de la decisión del coordinador, no del texto literal del DT.
- **Residual**: la métrica de similitud y la normalización siguen siendo el insumo B3 del plan; se verifica contra los ejemplos de HU-008.

### C-03 — Quién resuelve el captcha de pregunta — Resuelta
- **Resolución**: HU-026a describe un **servicio externo de resolución de captchas contratado por CISA**; el bot no calcula la respuesta. En el lab se sustituye por un **doble local detrás de la misma interfaz** (familias aritmética, dígitos del documento y nombre; «capitales» fuera). Si el servicio (o su doble) no está disponible → excepción de sistema con reintentos y, agotados, gestión manual.
- **Evidencia**: origen HU-026a §1 y §4 (corrección del 2026-10-20); DT §3.2 (captchas con fallback a revisión humana), §5.2 (`CAPTCHA_MAX_REINTENTOS` = 3) y §6.1 (3 reintentos con backoff).
- **Residual**: el origen asignaba al servicio la interpretación del «primer nombre» en nombres compuestos; el doble debe fijar una regla en el corpus B2 y las fuentes no la definen.

### C-04 — Fallo de la Policía — Resuelta
- **Resolución**: se mantiene la cadena del origen: Policía sin resultado o caída persistente → consultar la **Procuraduría** (HU-006/007/023). Si la Procuraduría tampoco resuelve, o el fallo es de sistema y se agotan los reintentos → **gestión manual** (fallback humano). La «cuota agotada simulada» entra como **fallo del servicio de captcha del doble de la Policía → revisión humana**.
- **Evidencia**: origen HU-006 §3 (postcondición) y HU-007 §3 (precondición); DT §3.2 restricción 7 (captchas con fallback a revisión humana) y §6.1.

### C-05 — Captcha de la Policía — Resuelta
- **Resolución**: sin evasión de un captcha de terceros. El doble de la Policía simula casilla y cuota agotada; el resultado documentado es **fallback humano**. Lo del origen («el bot marca la casilla del reCAPTCHA») queda registrado como **supuesto del proyecto real que el lab no ejercita**.
- **Evidencia**: DT §3.2 restricción 7 (reCAPTCHA v2 de la Policía con fallback a revisión humana); plan §7; origen HU-006 §3 paso 4.

### C-06 — Ámbito del repositorio local — Resuelta
- **Resolución**: el repositorio local es **NocoDB npm 0.301.3 en loopback** (decisión de Villa, 29/10). SQLite con el mismo contrato de repositorio queda solo como fallback documentado, no como camino de construcción.
- **Evidencia**: decisión de Villa del 29/10 (encargo de construcción); plan §9 y §10 (alternativa SQLite).

### C-07 — «Dobles, no stubs» vs. stubs — Resuelta
- **Resolución**: los **dobles implementan contrato** (es lo que se prueba y lo que mide la fidelidad); los **stubs** son solo HU-005 y HU-009 (Cobra, fuera de alcance) y se declaran como tales en §6. Los stubs se excluyen de cualquier métrica de fidelidad de dobles.
- **Evidencia**: plan §2 («dobles, no stubs que devuelven OK»); nota de integración §3 y §4 (Cobra sin ningún endpoint entregado).

### C-08 — Procedencia «aprobación de CISA del 09/10/2026» — Resuelta
- **Resolución**: la aprobación del 09/10/2026 viene del **correo de Amelia Escobar (CISA) «Entrega Oficial Documentación funcional»**, no de las HU. Aprobó **HU-001, HU-002 y HU-004**. Las demás historias del lab no están cubiertas por esa aprobación: HU-003 recibió el 09/10 un criterio de aceptación nuevo (varios celulares por campo), refinado y aprobado el 26–27/10; las lecturas de EP-002 en adelante con los usuarios líderes de área siguen pendientes. Cada HU cita su procedencia real.
- **Evidencia**: nota de integración §6 (aprobación del 09/10), §6.1 (sesión del 26/10, aprobada el 27/10) y §9 pendiente 8.

### C-09 — Endpoints de escritura en Zeus — Resuelta para el lab
- **Resolución**: para el lab, el contrato de escritura lo **define el doble local** (aceptación y errores documentados en su spec). El endpoint real de escritura sigue como pendiente del proyecto con IT de CISA y **no bloquea el lab**; cada supuesto del doble queda registrado como deuda para la integración real.
- **Evidencia**: nota de integración §3 (endpoints transaccionales de Zeus pendientes); origen HU-004 §4 (pendiente transversal).

### C-10 — Columnas `ID CLIENTE` / `ID CODEUDOR` — Resuelta
- **Resolución**: manda la sesión de alineación del 26/10/2026 (Tema 10): todas las bases arrancan con `ID CLIENTE`, `ID CODEUDOR` y siempre vienen diligenciadas; la instrucción previa («el bot las deja vacías», PO 2026-09-30) queda **superada**. En el lab el bot las diligencia con valores del fixture de los stubs HU-005/HU-009 (el origen de esos datos en producción sigue pendiente con IT CISA, igual que `FUENTE` y `TIPO USUARIO`).
- **Evidencia**: nota de integración §6.1 (Tema 10); origen HU-011 §4.

### C-11 — Número de columnas de las bases — Resuelta (con residual en C-16)
- **Resolución**: manda la sesión del 26/10 (Tema 10): las bases de celulares y de correos tienen **14 columnas**, arrancan con `ID CLIENTE`, `ID CODEUDOR` y ninguna trae columna `FIJO`. Las versiones previas del origen (12 columnas en `SOPORTES.xlsx`; 7 y 9 columnas en HU-010 §4) quedan superadas.
- **Evidencia**: nota de integración §6.1 (Tema 10); origen HU-011 §4 (lista de las 14 columnas por canal).

### C-12 — MER de 8 tablas — Resuelta
- **Resolución**: el MER del lab es el del DT §4.6: `Insumo`, `Excepciones`, `Exclusion`, `Celulares`, `Correos`, `Gestores`, `Parametros`, `LogEjecucion`, con las relaciones de la tabla de §4 (Insumo 1:N Excepciones, Insumo 1:1 Exclusion, Exclusion 1:N Celulares/Correos, Gestores N:1 Insumo).
- **Evidencia**: DT §4.6 y §5.4; nota de integración §1.

### C-13 — «Tipología ausente» vs. «bandeja vacía» (HU-002) — Resuelta
- **Resolución**: en OData ambas devuelven colección vacía; se distinguen por **doble consulta** (total de radicados que devuelve la consulta general vs. los del filtro). Ambos casos registran «0 casos» en el reporte y agendan reintento según `CADENCIA_REINTENTO_BANDEJA_VACIA`, parametrizable por el equipo técnico (según el PO).
- **Evidencia**: origen HU-002 §4 (cadencia parametrizable, PO 2026-09-30).

### C-14 — Portal de la Procuraduría — Resuelta
- **Resolución**: el dominio `webcert` quedó sin efecto el 2026-10-01. El doble se modela sobre la forma documentada en HU-007 (formulario con desplegable de tipo de documento, número, captcha de pregunta y bloque «Datos del ciudadano»), sin depender del dominio.
- **Evidencia**: origen HU-007 §4 (URL confirmada el 2026-10-01).

### C-15 — Estado del plan — Resuelta (declarada)
- **Resolución**: el plan sigue en **G0 pendiente**; estos documentos son insumo de F0/F2 y no declaran G0 cerrado.
- **Evidencia**: plan del lab, bitácora de gates (G0 «pendiente»).

### C-16 — Bases maestras frente al MER de 8 tablas — Resuelta con propuesta (pendiente de Villa)
- **Problema**: el MER del diseño tiene `Celulares` y `Correos` como bases de bloqueo ligadas a `Exclusion` (1:N), pero HU-010 (cruce) y HU-011 (verificación y eliminación) necesitan cruzar contra **bases maestras**.
- **Propuesta (pendiente de Villa)**: en el lab se añaden **dos tablas maestras locales**, `MaestraCelulares` y `MaestraCorreos`, de **14 columnas** cada una (misma estructura de HU-011 §4), como insumo de cruce, **sin tocar las 8 tablas del diseño**. El repositorio local queda con 10 tablas: las 8 del MER más las dos maestras.
- **Evidencia**: DT §4.6 (relaciones del MER); origen HU-010 §3 y HU-011 §3 (cruce y eliminación en base maestra); nota de integración §6.1 (Tema 10).

### C-17 — Cantidad de campos de la API de Zeus — Resuelta para el lab
- **Problema**: el plan y la nota de integración hablan de 48 campos; el ejemplo de respuesta del manual de consumo (2026-10-07) trae **51 propiedades**, y la nota de integración suma 10 campos de «Detalles» agregados el 2026-10-15 que el manual no documenta.
- **Resolución**: el doble y los fixtures implementan las 51 propiedades del manual más las 10 de «Detalles» (estas últimas, forma supuesta del lab). La métrica de fidelidad se mide contra las 51 del manual.
- **Evidencia**: manual de consumo §5; nota de integración §2.

### C-18 — Literal de ausencia y formato de fecha en la API — Resuelta para el lab (confirmar con una respuesta real)
- **Problema**: las HU usan el literal «No aporta»; el manual filtra con `'NO APORTA'` en mayúsculas. La nota de integración dice que `FECHADERECEPCION` es `yyyy-MM-dd`; el ejemplo del manual trae `dd/MM/yyyy`.
- **Resolución**: la comparación del literal de ausencia no distingue mayúsculas (regla cerrada intacta); la fecha se conserva tal cual viene, sin convertirla.
- **Evidencia**: manual de consumo §4.3 y §5; nota de integración §2.

### C-19 — Modo local aislado frente a la API real — Resuelta por directriz de Villa; ejecución real bloqueada
- **Problema**: el plan y las reglas de construcción dejaban fuera todo sistema de CISA.
- **Resolución**: directriz de Villa (2026-10-29): el cliente se implementa contra el contrato real `CamposAdicionalesXRadicadoHabeasData`; el doble local queda como fixture offline del banco. El repositorio trae `ZeusApi.Modo = "fixture"` por defecto y el modo `real` apunta a QA con salvaguardas.
- **Bloqueos para ejecutar contra la API real**: (1) `client_secret` rotado, por canal seguro; (2) autorización de uso; (3) acceso de red a `qaservices.cisa.gov.co`, no verificado; (4) endpoint de escritura del comentario (C-09). Detalle en `banco/evidencia/EP-001/EVIDENCIA.md`.

### C-20 — Nombre de la tarea principal — Resuelta con la regla del validador (pendiente de revisión humana)
- **Problema**: el lineamiento pide la tarea principal con el nombre del proyecto (`R_LAB_HabeasData`); `validate_robot` con `perfil:"trycore"` exige §7.1 PascalCase sin guiones bajos.
- **Resolución**: el proyecto de Studio sigue llamándose `R_LAB_HabeasData` y la tarea principal es `LabHabeasData`.
- **Evidencia**: salida de `validate_robot`: «debe ser PascalCase descriptivo, sin guiones bajos ni especiales».

### C-21 — Nombre de un campo en `specs/api-zeus-qa.md` — Resuelta con el manual (avisar a Villa)
- **Problema**: la spec lista `EVIDENCIADLARESPUESTAENVIADA`; el manual de consumo (2026-10-07) trae `EVIDENCIADELARESPUESTAENVIADA`.
- **Resolución**: el doble y los fixtures usan el nombre del manual, que es la fuente de la spec. EP-001 no consume ese campo, así que no hay efecto funcional; la spec parece tener un error tipográfico.

### C-22 — El filtro compuesto de la spec frente a HU-004 — **Abierta: decide Villa**
- **Problema**: `specs/api-zeus-qa.md` manda seleccionar con `... and NOIDENTIFICACIONDELCLIENTE ne 'NO APORTA'`. HU-004 (y el origen) mandan que un radicado sin número de identificación vaya a la excepción de negocio 1 con comentario para Cartera. Con el filtro compuesto esos radicados **nunca llegan al bot** y Cartera no recibe el comentario.
- **Tratamiento provisional**: se sigue la spec (`SeleccionRadicados.DescartarIdentificacionAusente = true`) y los descartados **no se pierden en silencio**: se cuentan con una consulta complementaria y quedan en el log de auditoría, el reporte y el resumen. Con `false` el flujo vuelve al de HU-004 (cubierto por pruebas y por el escenario EP001-14 del banco).
- **Decide**: Villa, entre (a) mantener el descarte y asumir que esos radicados se gestionan manualmente fuera del bot, o (b) desactivar el descarte para que HU-004 los comente.

## 10. Pendientes que este documento no cierra

- C-16: la propuesta de las dos tablas maestras espera la aprobación de Villa; el endpoint real de escritura en Zeus (C-09) sigue con IT CISA.
- **Diccionario de los 48 campos** de la API de Zeus: está en el paquete del 29/10 y no estaba entre las fuentes leídas. La nota de integración §2 confirma nombres de la API sin separadores (`NOMBREDELCLIENTE`, `TIPODEIDENTIFICACION`, `NOIDENTIFICACIONDELCLIENTE`, `CORREOELECTRONICOPARAEXCLUSION`, `TELEFONODECONTACTO`, `FECHADERECEPCION`, `RadicadoPadre`/`RadicadosHijos`) frente a los nombres de formulario que usan las HU; la correspondencia completa y la semántica exacta de `$first` quedan por confirmar.
- Métrica de similitud y normalización de nombres (B3); corpus de captchas (B2) y regla del «primer nombre» en nombres compuestos; selectores de los dobles HTML (B4); fixtures por borde (B5); catálogo de `FUENTE` y datos de las tablas (B6).
- Columnas del Reporte de gestiones para el lab (las define Villa).
- Reescritura de HU-001 como token OAuth (insumo para el PO).

## 11. Procedencia

Cada historia de `docs/04-historias/` indica en «Notas técnicas» su HU de origen y su procedencia real (C-08): aprobación del 09/10/2026 solo para HU-002 y HU-004; sesión de alineación del 26–27/10/2026 cuando aplica. Las confirmaciones puntuales citadas conservan la fecha con que figuran en el origen. Para arquitectura, MER y parámetros, la fuente de verdad es el DT v1.2.

## 12. Directriz de verificación en Chrome (Villa)

Directriz de Villa para la construcción, que se suma a las reglas del lab:

- **Todo lo web se construye y se revisa en Chrome.** Los robots abren el navegador con `openbrowser` y `extra:{default:"chrome"}`.
- **Cada doble local con interfaz** (portal de la Policía, portal de la Procuraduría, formularios con captcha) se abre en Chrome y se verifica visualmente (estructura HTML, formularios, captcha); la **captura queda como evidencia por cada doble**.
- **Revisión con el MCP `rpa-aio`**: `screenshot`, `get_run_log`, `run_in_studio` y `validate_robot`. Si el MCP no está conectado en la sesión, se invoca por stdio.
- **Reparto de la verificación**: la funcional la da el banco determinista; la visual la da Chrome. **Sin verificación visual real no se declara verde** (equivalente al gate `fidelity` del arnés).
- Las capturas siguen la regla de datos: solo sintéticos, cero PII.

## 13. API real de Zeus y fixture offline (directriz de Villa, 2026-10-29)

- **Cliente real, doble como fixture.** `Scripts/habeasdata/zeus.py` habla el contrato real: OAuth 2.0 client credentials (`app_dab_habeasdata`, realm `git_cisa`), token de 300 s con renovación ante 401, OData v4 y consulta individual por `IDRADICADO`. El doble de `dobles/zeus_api/` solo alimenta el banco determinista y las pruebas sin red.
- **Modos.** `ConfiguracionProceso.ZeusApi.Modo`: `fixture` (por defecto, el que usa el banco, declarado en cada resultado) o `real` (QA de CISA).
- **Contrato.** El cliente implementa `specs/api-zeus-qa.md` (QA, extraído del manual v1.1). Solo consulta: la escritura del comentario vive en `EscrituraComentario`, separada, y en modo real no existe endpoint entregado, así que se reporta como bloqueo y no se simula.
- **Secreto.** El `client_secret` sale **solo** del Administrador de credenciales de Windows (credencial `R_LAB_HabeasData/Zeus/QA`, nombre declarado en configuración; el valor nunca). Sin él, o sin `ZEUS_REAL_AUTORIZADO=1`, el cliente se detiene antes de cualquier llamada de red.
- **PII real.** En modo real, logs, reporte y resumen del robot enmascaran nombre, identificación, correos y teléfonos; toda evidencia con radicados reales debe redactarse.
- **Navegador.** Toda navegación web del robot corre en Chrome: `openbrowser` con `extra:{default:"chrome"}` y `openUrl` aparte; la ejecución se verifica con `run_in_studio` y captura del MCP. Cualquier ejecución en otro navegador o sin ventana es defecto.
