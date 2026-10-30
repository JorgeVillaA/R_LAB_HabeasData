# Decisiones y alcance del lab — R_LAB_HabeasData

> **Fuente única de verdad** de lo decidido en este laboratorio. Si una duda no está aquí, se pregunta a Villa y se añade aquí antes de seguir. Nada de esto se reabre sin una decisión explícita nueva.

## Alcance en una página

| En el lab | Fuera del lab |
|---|---|
| EP-001: HU-002 (selección de radicados), HU-003 (lectura y normalización), HU-004 (validación de campos) | HU-001 (login → se reescribe como token; insumo para el PO) |
| EP-002: HU-006 (Policía), HU-007 (Procuraduría), HU-008 (matching de nombres) | HU-005 y HU-009 (Cobra sin endpoints) — **stubs declarados** |
| EP-006: HU-026a (captcha de pregunta, al servicio de HU-007) | HU-026b (capitales), HU-020/021/022/025 (playbook y componentes) |
| EP-003: HU-010 (duplicados), HU-011 (registro en base) | HU-012 a HU-018, HU-027 a HU-032 (notificación, cierre, RCC, reporte) |
| Escritura de comentario en Zeus → doble de escritura | Envío al ciudadano, firma, QR, aprobación de Jefatura |
| Base local NocoDB + tabla `Transacciones` | NocoDB de CISA |
| Modo fixture (determinista, sin red) y modo real (API Zeus QA + portales reales) | Cobra, portales de pago, servicios externos reales |

**Qué demuestra el lab:** que un agente puede construir RPA con el flujo Trycore (spec ejecutable → TDD → banco determinista → verificación), sobre un alcance real recortado. **Qué no demuestra:** la integración de escritura con CISA ni la operación productiva por limitación del lab , ya que la meta era tomar una fracción pequeña de lo que se tenia para evaluar la capacidad agentica en el desarrollo rpa e2e.



## Registro de decisiones


| # | Decisión | Por qué | Quién |
|---|---|---|---|
| D-01 | El proyecto se llama `R_LAB_HabeasData` (no `R_<Empresa>_<Proyecto>`) | Es un lab propio, no una entrega de cliente; la razón se escribe para que la revisión no lo devuelva como defecto | Villa, 29/10 |
| D-02 | La raíz del bot es la carpeta de este repo, declarada como llave de configuración (`RutasProceso.RutaRaiz`) | La máquina no tiene unidad D:; en un lab todo vive junto al código | Villa, 29/10 |
| D-03 | **API de Zeus: se usa la ORIGINAL** (QA). El doble queda como fixture offline del banco | Se quiere probar la integración real de lectura | Villa, 29/10 |
| D-04 | **Portales del Estado: modo real disponible**; los dobles son fixture del banco | Ídem | Villa, 29/10 |
| D-05 | El **reCAPTCHA v2 de la Policía no se automatiza**: human-in-the-loop o revisión manual | No se evaden sistemas anti-bot de terceros; el diseño de CISA ya declara ese fallback | Regla del lab |
| D-06 | El captcha de pregunta de la Procuraduría lo resuelve **la interfaz del servicio contratado por CISA** (en el lab, su doble) | HU-026a: el bot no calcula la respuesta; se integra con el paquete que CISA ya pagó | Documentación del proyecto |
| D-07 | Repositorio local: **NocoDB npm 0.301.3 en loopback** (SQLite como fallback con el mismo contrato) | Sin Docker en la máquina; mismo motor que el NocoDB de CISA | Villa, 29/10 |
| D-08 | El repositorio lleva la tabla **`Transacciones`**: una fila por paso de cada caso, escrita en cada transición **incluidos los fallos** | Que se pueda ver dónde se quedó cada caso; lección de Medidas Cautelares | Villa, 29/10 |
| D-09 | Los clones de portales son **fieles técnicamente** (mismos campos, selectores, flujo) y **no visuales** (sin logotipos ni identidad oficial) | Máximo realismo útil sin impersonar sitios del Estado | Villa, 29/10 |
| D-10 | El flujo del robot en Studio debe ser **explicable a cliente** (grupos por HU, decisiones visibles, descripciones) | Como los bots ya construidos; nada de cajas negras de Python | Villa, 29/10 |
| D-11 | **Chrome** para construir, ejecutar y revisar (con captura como evidencia) | Requisito del cliente y del lineamiento; verificación visual real | Villa, 29/10 |
| D-12 | Logs según el **anexo V1.0**: dos archivos por día, 4 campos `Ip;Fecha;AplicativoModulo;Observacion`, `NO APLICA` en faltantes | El anexo del proyecto manda sobre el lineamiento base (11 campos) | Precedencia del estándar |
| D-13 | Sin `$select` por lote: se conservan los campos completos | Para no perder el escenario «formulario no carga» de HU-003 | Supuesto de Ares, vetable |
| D-14 | Entrega: **repo** a **Diana** (líder técnico), con informe, nota de credenciales y `arrancar_lab.ps1`; corre con **API real** | Definido para la revisión | Villa, 29/10 |
| D-15 | **Cero PII**: datos sintéticos en todo; evidencia redactada en modo real | Ley 1581 y regla del lab | Regla del lab |
| D-16 | `git push` lo hace **Villa a mano** (el agente lo tiene denegado) | Regla de seguridad del usuario | Villa |
| D-17 | `MaestraCelulares` / `MaestraCorreos` (14 columnas) como bases de cruce de HU-010/011 | El MER del diseño no trae maestras separadas | Propuesta, **pendiente de Villa** |
| D-18 | **Limpieza de bots de prueba**: todo bot o proyecto de pruebas se borra al terminar de usarse (`delete_robot` o carpeta del proyecto), dejando solo el robot del proyecto activo. La poda se hace con copia de respaldo previa y listado exacto (nunca con comodines) | La lista de proyectos/bots se llena de rastro y estorba el trabajo | Villa, 30/10 |
| D-19 | Los clones de portales son **visualmente idénticos**: se extrae el front-end real (HTML, CSS, imágenes) de los portales y se replica hasta que se vea igual, verificando con captura. Siguen siendo dobles locales (loopback, sin publicar) y con PII redactada | Que el doble sea indistinguible del portal real para el bot y para la revisión | Villa, 30/10 |
| D-20 | Las tareas de extracción/mecánicas se delegan a **subagentes con modelo barato** (`delegation.model` = `deepseek-v4.1-flash` vía `opencode-go`, verificado con sonda) | Coste: los hijos llevan la mayoría de los tokens. Nota: la cuenta de Nous está sin créditos (los modelos de Nous fallan para hijos) | Villa, 30/10 |
| D-21 | **Práctica experimental de mantenimiento: test por bloque en Studio.** Todo bloque del robot debe poder ejecutarse solo (el botón de test del bloque ejecuta `commands:[ese bloque]` con las variables actuales, y `playNode` permite arrancar desde cualquier bloque). Cada bloque queda con entrada/salida explícita y sin estado oculto; la lógica pura va en funciones testeables sin abrir Studio. Además se mantiene un mapa **salud por bloque** (qué escenario del banco cubre cada bloque) | Es una opción más para mantenimiento/soporte: permite diagnosticar y reparar un bloque sin correr el robot entero, y ver la salud de cada pieza sin leer todo el flujo. Se adopta como **experimento**: se mide si reduce tiempo de soporte y se decide si se mantiene | Villa, 30/10 |
| D-22 | **HU-002 — opción A: se implementa el reintento de bandeja vacía.** Si la consulta inicial devuelve la bandeja sin casos, el robot **reintenta** según la política definida en vez de confiar solo en la cadencia de ejecución del orquestador. Se descarta la opción B (firmar que la cadencia basta) | El verificador adversarial bloqueó HU-002 por este hueco: con cadencia como única defensa, un caso publicado después de la ventana se pierde sin rastro. El reintento deja evidencia de la espera y cubre el escenario | Villa, 30/10 (respuesta al reporte de las 14:30) |

## Lo que está definido del servicio de captchas (para no volver a preguntarlo)

- **Contratado y pagado por CISA** (paquete activo para Policía y Procuraduría), confirmado por la PM el 29/07 y por CISA en el checklist técnico (ítem 15).
- **3 reintentos** por página (documento de Amelia, 27/08, §3.4.1).
- **Consumo estimado** (kick-off, 11/08): 250 casos/mes; 370 casos (QA + primer mes) → **1.480 captchas** óptimo / **4.440** crítico.
- **Interfaz**: envía pregunta (+ documento/nombre cuando aplica) → devuelve respuesta; códigos `CAPTCHA_SERVICIO_NO_DISPONIBLE` y `CAPTCHA_MAX_REINTENTOS`; fallback humano al fallar.
- **Lo único que falta**: la ruta/URL del servicio (la tabla QA/PRODUCTIVO está vacía en el documento de Amelia), el proveedor y la credencial. Lo cierra **Comercial ↔ CISA**.

## Reglas del lab (innegociables)

1. Nada se declara verde sin ejecutar.
2. Datos sintéticos; cero PII en repos, logs, fixtures o capturas.
3. Cada dependencia externa va detrás de una interfaz con doble que implementa el contrato real (campos, códigos de error, HTML descrito); un `OK` fijo no cuenta.
4. Toda contradicción entre fuentes se numera (C-NN), se documenta y se resuelve con evidencia o se escala a Villa. Nunca en silencio.
5. Las decisiones son de Villa; el agente propone y construye; CISA solo cuenta como insumo externo opcional.
6. Si algo falla en un ensayo, se cambia a la ruta verificada y el bloqueo se documenta con evidencia dura; no se depura en vivo.
