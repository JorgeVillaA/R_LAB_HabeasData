# Salud por bloque del robot `LabHabeasData`

> Práctica **experimental** D-21 (test por bloque en Studio). Generado por `python banco/salud_por_bloque.py`; **no editar a mano**. La cobertura se mide: cada escenario del banco (EP-001: 16, EP-002: 19) corre el JSON del robot en el intérprete (`banco/interprete_robot.py`) y se anota qué bloques ejecutó.

## Cómo probar un bloque solo
1. En Studio, botón de test del bloque: ejecuta `commands:[ese bloque]` con las variables actuales; `playNode` arranca desde cualquier bloque.
2. Todo bloque tiene **entrada y salida explícitas** (columnas de abajo). Los bloques `Paso (componente)` reciben la raíz (`glbStrRutaRaiz`) y llaman a `pasos.asegurar(raíz)`: reconstruyen la sesión solos, sin depender de que otro bloque haya corrido antes.
3. La lógica pura sigue en funciones probadas sin abrir Studio (`Scripts/habeasdata`, `tests/`).
4. Los bloques de Chrome necesitan los clones de portales arriba (`python dobles/portales/servidor.py 8766`) y el servicio de captchas.

## Resumen
- Bloques: **224** (Chrome: clic 9, Decisión 60, Paso (componente) 34, Bucle 2, Grupo 10, Log 1, Chrome: URL 2, Chrome: abrir 1, Chrome: escribir 4, Asignar 86, Chrome: leer texto 4, Control de errores 5, Chrome: esperar 6).
- Cubiertos por al menos un escenario: **214**; **sin cubrir: 10**.

### Huecos de cobertura (bloques sin escenario)

| Bloque | Tipo | Descripción |
|---|---|---|
| 1.1.18.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló |
| 1.2.1.2.4.3.3.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló |
| 1.2.1.2.4.4.2.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló |
| 1.2.1.3.3.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló |
| 1.2.3.1.4.8.1 | Asignar | Etapa: revisión humana (reCAPTCHA) |
| 1.2.3.1.4.10.e.1 | Asignar | Policía caída durante la consulta: se consulta la Procuraduría |
| 1.2.e.1 | Asignar | Marca fallo de sistema en el proceso principal |
| 1.2.e.2 | Asignar | Estado de la ejecución: detenido por excepción de sistema |
| 1.e.1 | Asignar | Marca fallo de sistema |
| 1.e.2 | Asignar | Observación de la excepción de sistema |

Un bloque sin escenario no tiene prueba que lo ejercite: se reporta como hueco, no se declara sano.

## Mapa

| Bloque | Tipo | Qué hace | Entrada | Salida | Escenarios del banco |
|---|---|---|---|---|---|
| 1 | Control de errores | Control de ejecución | — | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1 | Grupo | HU002HU003HU004 - Inicializar el Asistente | — | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.1 | Asignar | Estado de la ejecución: estado, motivo si la selección queda vacía (HU-002), total de radicados y motivo de detención | — | glbDicEstado | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.2 | Asignar | Radicados seleccionados por HU-002 | — | glbArrIdsRadicados | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.3 | Asignar | Radicados descartados por identificación ausente (HU-002) | — | glbArrIdsDescartados | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.4 | Asignar | Radicados que avanzan a la validación de deuda (HU-004) | — | glbArrAvanzan | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.5 | Asignar | Radicados en excepción de negocio 1 (HU-004) | — | glbArrExcepcionesNegocioUno | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.6 | Asignar | Radicados en excepción de sistema (HU-003, HU-004) | — | glbArrExcepcionesSistema | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.7 | Paso (componente) | Carga los tres JSON de configuración, crea la estructura de carpetas y los dos logs del día | glbStrRutaRaiz | glbDicInicio | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.8 | Paso (componente) | Lee los parámetros de negocio de la configuración (tipología, campo, literal de ausencia, lote, orden) | glbStrRutaRaiz | glbDicParametros | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.9 | Asignar | Radicados con identidad validada (HU-008) | — | glbArrValidadas | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.10 | Asignar | Radicados en excepción de negocio 3 (HU-008) | — | glbArrExcepcionesNegocioTres | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.11 | Asignar | Radicados en revisión humana (HU-006) | — | glbArrRevisionHumana | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.12 | Asignar | Radicados con respuesta sin nombre (HU-007) | — | glbArrSinNombre | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.13 | Asignar | Radicados derivados a gestión manual (HU-006, HU-007, HU-026a) | — | glbArrGestionManual | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.14 | Asignar | Radicados en excepción de sistema de identidad | — | glbArrExcepcionesSistemaIdentidad | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.15 | Asignar | Códigos de error de identidad por radicado | — | glbDicCodigos | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.16 | Asignar | Chrome aún no está abierto | — | glbBlnChromeAbierto | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.17 | Paso (componente) | Lee el modo, las URL de los portales y los reintentos del captcha; en modo real exige autorización y ventana operativa | glbStrRutaRaiz | glbDicPortales | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.18 | Decisión | Los portales no se pueden usar (falta autorización o ventana operativa) | glbDicPortales | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.18.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicEstado, glbDicPortales | glbDicEstado | **sin cubrir** |
| 1.1.19 | Asignar | URL del portal de la Policía | glbDicPortales | glbStrUrlPolicia | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.1.20 | Asignar | URL del portal de la Procuraduría | glbDicPortales | glbStrUrlProcuraduria | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.2 | Control de errores | Proceso principal | — | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.2.1 | Grupo | HU002 - Filtrar radicados de Exclusión de Datos | — | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.2.1.1 | Paso (componente) | Solicita el token OAuth (client_credentials, vigencia 300 s); el secreto sale del Administrador de credenciales | glbStrRutaRaiz | glbDicAutenticacion | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.2.1.2 | Decisión | El token se obtuvo | glbDicAutenticacion | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.2.1.2.1 | Asignar | Arma la consulta de HU-002: filtro OData de la tipología ($filter, base de la selección), campos ($select), lote ($first) y orden ($orderby) | glbDicParametros | locDicConsulta | E1-01, E1-02, E1-03, E1-04 (+31) |
| 1.2.1.2.2 | Decisión | Se descartan los radicados sin identificación (parámetro) | glbDicParametros | — | E1-01, E1-02, E1-03, E1-04 (+31) |
| 1.2.1.2.2.1 | Asignar | Agrega al filtro: identificación distinta de «NO APORTA» | glbDicParametros, locDicConsulta | locDicConsulta | E1-01, E1-02, E1-03, E1-04 (+30) |
| 1.2.1.2.3 | Paso (componente) | Consulta los radicados de exclusión (GET OData con $filter, $select, $first y $orderby) | glbStrRutaRaiz, locDicConsulta | glbDicSeleccion | E1-01, E1-02, E1-03, E1-04 (+31) |
| 1.2.1.2.4 | Decisión | La consulta respondió | glbDicSeleccion | — | E1-01, E1-02, E1-03, E1-04 (+31) |
| 1.2.1.2.4.1 | Asignar | Guarda los radicados seleccionados | glbDicSeleccion | glbArrIdsRadicados | E1-01, E1-02, E1-03, E1-08 (+28) |
| 1.2.1.2.4.2 | Paso (componente) | Deja constancia en el log de auditoría de los radicados identificados | glbArrIdsRadicados, glbStrRutaRaiz | locDicEvento | E1-01, E1-02, E1-03, E1-08 (+28) |
| 1.2.1.2.4.3 | Decisión | Se descartan los radicados sin identificación (parámetro) | glbDicParametros | — | E1-01, E1-02, E1-03, E1-08 (+28) |
| 1.2.1.2.4.3.1 | Asignar | Arma el filtro de los descartados: identificación igual a «NO APORTA» | glbDicParametros, locDicConsulta | locStrFiltroDescartados | E1-01, E1-02, E1-03, E1-08 (+27) |
| 1.2.1.2.4.3.2 | Paso (componente) | Consulta los radicados descartados para no perderlos en silencio | glbStrRutaRaiz, locStrFiltroDescartados | glbDicDescartados | E1-01, E1-02, E1-03, E1-08 (+27) |
| 1.2.1.2.4.3.3 | Decisión | La consulta de descartados respondió | glbDicDescartados | — | E1-01, E1-02, E1-03, E1-08 (+27) |
| 1.2.1.2.4.3.3.1 | Asignar | Guarda los radicados descartados | glbDicDescartados | glbArrIdsDescartados | E1-01, E1-02, E1-03, E1-08 (+27) |
| 1.2.1.2.4.3.3.2 | Paso (componente) | Deja los descartados en el log de auditoría y en el reporte | glbArrIdsDescartados, glbStrRutaRaiz | glbDicRegistroDescartados | E1-01, E1-02, E1-03, E1-08 (+27) |
| 1.2.1.2.4.3.3.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicDescartados, glbDicEstado | glbDicEstado | **sin cubrir** |
| 1.2.1.2.4.4 | Decisión | La selección quedó vacía y no hubo fallos | glbArrIdsRadicados, glbDicEstado | — | E1-01, E1-02, E1-03, E1-08 (+28) |
| 1.2.1.2.4.4.1 | Paso (componente) | Consulta el total de radicados (consulta general, sin $filter) | glbStrRutaRaiz | glbDicGeneral | E1-02, E1-03, E1-16 |
| 1.2.1.2.4.4.2 | Decisión | La consulta general respondió | glbDicGeneral | — | E1-02, E1-03, E1-16 |
| 1.2.1.2.4.4.2.1 | Asignar | Total de radicados de la consulta general | glbDicEstado, glbDicGeneral | glbDicEstado | E1-02, E1-03, E1-16 |
| 1.2.1.2.4.4.2.2 | Decisión | Todos los de la tipología fueron descartados | glbArrIdsDescartados | — | E1-02, E1-03, E1-16 |
| 1.2.1.2.4.4.2.2.1 | Asignar | Motivo: solo descartados | glbDicEstado | glbDicEstado | E1-16 |
| 1.2.1.2.4.4.2.2.e.1 | Decisión | Hay radicados, pero ninguno de la tipología | glbDicEstado | — | E1-02, E1-03 |
| 1.2.1.2.4.4.2.2.e.1.1 | Asignar | Motivo: tipología ausente | glbDicEstado | glbDicEstado | E1-03 |
| 1.2.1.2.4.4.2.2.e.1.e.1 | Asignar | Motivo: bandeja vacía | glbDicEstado | glbDicEstado | E1-02 |
| 1.2.1.2.4.4.2.3 | Paso (componente) | Registra «0 casos» y la cadencia del reintento (CADENCIA_REINTENTO_BANDEJA_VACIA) | glbDicEstado, glbStrRutaRaiz | glbDicSinCasos | E1-02, E1-03, E1-16 |
| 1.2.1.2.4.4.2.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicEstado, glbDicGeneral | glbDicEstado | **sin cubrir** |
| 1.2.1.2.4.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicEstado, glbDicSeleccion | glbDicEstado | E1-04, E1-05, E1-06 |
| 1.2.1.2.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicAutenticacion, glbDicEstado | glbDicEstado | E1-07 |
| 1.2.1.3 | Decisión | Sigue sin casos: agenda el reintento (espera la cadencia y vuelve a consultar) | glbArrIdsRadicados, glbDicEstado | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.2.1.3.1 | Paso (componente) | Espera MinutosEntreReintentos y reconsulta, hasta MaximoReintentosDiarios o hasta que aparezcan casos (CADENCIA_REINTENTO_BANDEJA_VACIA) | glbStrRutaRaiz | glbDicReintento | E1-02, E1-03, E1-16 |
| 1.2.1.3.2 | Decisión | Hubo reintentos y la consulta respondió | glbDicReintento | — | E1-02, E1-03, E1-16 |
| 1.2.1.3.2.1 | Asignar | Guarda los radicados seleccionados en el reintento | glbDicReintento | glbArrIdsRadicados | E1-02, E1-03, E1-16 |
| 1.2.1.3.2.2 | Asignar | Guarda los descartados del último intento | glbDicReintento | glbArrIdsDescartados | E1-02, E1-03, E1-16 |
| 1.2.1.3.2.3 | Asignar | Motivo con el que terminó el último intento | glbDicEstado, glbDicReintento | glbDicEstado | E1-02, E1-03, E1-16 |
| 1.2.1.3.3 | Decisión | El reintento se detuvo por una falla crítica | glbDicReintento | — | E1-02, E1-03, E1-16 |
| 1.2.1.3.3.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicEstado, glbDicReintento | glbDicEstado | **sin cubrir** |
| 1.2.2 | Decisión | La identidad está habilitada y la selección terminó bien: deja constancia de su inicio | glbDicEstado, glbDicPortales | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.2.2.1 | Paso (componente) | Deja constancia del inicio de la validación de identidad en el log de auditoría | glbDicPortales, glbStrRutaRaiz | locDicEvento | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3 | Decisión | Hay radicados que procesar | glbArrIdsRadicados, glbDicEstado | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.2.3.1 | Bucle | Iteración por radicado de exclusión | glbArrIdsRadicados | locStrIdRadicado | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.1 | Paso (componente) | Deja constancia del inicio del radicado en el log de auditoría | glbStrRutaRaiz, locStrIdRadicado | locDicEvento | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.2 | Grupo | HU003 - Leer datos paramétricos | — | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.2.1 | Paso (componente) | Lee el radicado por IDRADICADO (GET individual) | glbStrRutaRaiz, locStrIdRadicado | locDicLectura | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.2.2 | Decisión | El radicado se pudo leer | locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.2.2.1 | Paso (componente) | Limpia «No aporta» y vacíos (= ausente) y separa los valores de cada canal por «/» | glbStrRutaRaiz, locDicLectura | locDicPreparado | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.2.2.2 | Paso (componente) | Clasifica cada teléfono por dígitos: celular, fijo o sin clasificar | glbStrRutaRaiz, locDicPreparado | locDicCaso | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.2.2.e.1 | Paso (componente) | Registra la excepción de sistema del radicado (log de errores y reporte) | glbStrRutaRaiz, locDicLectura, locStrIdRadicado | — | E1-08, E1-09 |
| 1.2.3.1.2.2.e.2 | Asignar | Anota el radicado en excepciones de sistema | glbArrExcepcionesSistema, locStrIdRadicado | glbArrExcepcionesSistema | E1-08, E1-09 |
| 1.2.3.1.3 | Grupo | HU004 - Validar campos obligatorios | — | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.3.1 | Asignar | Lista de motivos de incompletitud (vacía al empezar cada radicado) | — | locArrMotivos | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.3.2 | Decisión | Falta el nombre del cliente | locDicCaso, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.3.2.1 | Asignar | Agrega el motivo | locArrMotivos | locArrMotivos | E1-01, E1-08, E1-09, E1-10 (+3) |
| 1.2.3.1.3.3 | Decisión | Falta el tipo de identificación | locDicCaso, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.3.3.1 | Asignar | Agrega el motivo | locArrMotivos | locArrMotivos | E1-01, E1-08, E1-09, E1-10 (+3) |
| 1.2.3.1.3.4 | Decisión | Falta el número de identificación | locDicCaso, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.3.4.1 | Asignar | Agrega el motivo | locArrMotivos | locArrMotivos | E1-14 |
| 1.2.3.1.3.5 | Decisión | No hay ningún canal de contacto (ni correo ni teléfono) | locDicCaso, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.3.5.1 | Asignar | Agrega el motivo | locArrMotivos | locArrMotivos | E1-01, E1-08, E1-09, E1-10 (+4) |
| 1.2.3.1.3.6 | Decisión | El caso está completo | locArrMotivos, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.3.6.1 | Paso (componente) | Registra el avance a la validación de deuda en el reporte | glbStrRutaRaiz, locDicCaso | locDicResultado | E1-01, E1-08, E1-09, E1-10 (+24) |
| 1.2.3.1.3.6.2 | Asignar | Anota el radicado en los que avanzan | glbArrAvanzan, locStrIdRadicado | glbArrAvanzan | E1-01, E1-08, E1-09, E1-10 (+24) |
| 1.2.3.1.3.7 | Decisión | El caso está incompleto: excepción de negocio 1 | locArrMotivos, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.3.7.1 | Paso (componente) | Escribe el comentario de la excepción de negocio 1 en Gestión → Detalle | glbStrRutaRaiz, locArrMotivos, locDicCaso | locDicComentario | E1-01, E1-08, E1-09, E1-10 (+4) |
| 1.2.3.1.3.7.2 | Decisión | El comentario quedó registrado | locDicComentario | — | E1-01, E1-08, E1-09, E1-10 (+4) |
| 1.2.3.1.3.7.2.1 | Paso (componente) | Registra la excepción de negocio 1 en el reporte | glbStrRutaRaiz, locArrMotivos, locDicCaso | locDicResultado | E1-01, E1-08, E1-09, E1-13 (+2) |
| 1.2.3.1.3.7.2.2 | Asignar | Anota el radicado en excepciones de negocio 1 | glbArrExcepcionesNegocioUno, locStrIdRadicado | glbArrExcepcionesNegocioUno | E1-01, E1-08, E1-09, E1-13 (+2) |
| 1.2.3.1.3.7.2.e.1 | Paso (componente) | Registra la excepción de sistema (no se pudo escribir el comentario) | glbStrRutaRaiz, locDicComentario, locStrIdRadicado | — | E1-10, E1-11 |
| 1.2.3.1.3.7.2.e.2 | Asignar | Anota el radicado en excepciones de sistema | glbArrExcepcionesSistema, locStrIdRadicado | glbArrExcepcionesSistema | E1-10, E1-11 |
| 1.2.3.1.4 | Grupo | HU006 - Consultar la Policía Nacional (Chrome) | — | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.1 | Asignar | Estado de la identidad del radicado (empieza en «inicio») | — | locDicIdentidad | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.2 | Decisión | El radicado avanzó (HU-004) y la identidad está habilitada: prepara los datos del caso | glbArrAvanzan, glbDicPortales, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.2.1 | Paso (componente) | Deja constancia del inicio de la identidad del radicado en el log de auditoría | glbStrRutaRaiz, locStrIdRadicado | locDicEvento | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.4.2.2 | Paso (componente) | Clasifica el documento: cédula, NIT de 10 dígitos y código del tipo en la Procuraduría | glbStrRutaRaiz, locDicCaso | locDicDocumento | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.4.2.3 | Asignar | Número de documento a consultar | locDicDocumento | locStrDocumento | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.4.2.4 | Asignar | Nombre del caso en Zeus (la pregunta del captcha puede requerirlo) | locDicDocumento | locStrNombre | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.4.2.5 | Asignar | Código del tipo de documento en el desplegable de la Procuraduría | locDicDocumento | locStrCodigoTipo | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.4.3 | Decisión | Avanzó a identidad y el documento es cédula de ciudadanía: empieza por la Policía | glbArrAvanzan, glbDicPortales, locDicDocumento, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.3.1 | Asignar | Etapa: consulta en la Policía | locDicIdentidad | locDicIdentidad | E2-01, E2-02, E2-03, E2-04 (+11) |
| 1.2.3.1.4.4 | Decisión | Avanzó a identidad y el documento no es cédula: va directo a la Procuraduría | glbArrAvanzan, glbDicPortales, locDicDocumento, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.4.1 | Asignar | Etapa: consulta en la Procuraduría | locDicIdentidad | locDicIdentidad | E2-01, E2-02, E2-03, E2-04 (+10) |
| 1.2.3.1.4.5 | Decisión | Hay que usar un portal y Chrome aún no está abierto | glbBlnChromeAbierto, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.5.1 | Chrome: abrir | Abre Chrome (el robot corre en Chrome) | — | — | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.4.5.2 | Asignar | Chrome quedó abierto | — | glbBlnChromeAbierto | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.4.6 | Control de errores | Policía: abre el portal y acepta los términos | — | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.6.1 | Decisión | Consulta en la Policía | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.6.1.1 | Chrome: URL | Abre el portal de la Policía | glbStrUrlPolicia | — | E2-01, E2-02, E2-03, E2-04 (+11) |
| 1.2.3.1.4.6.1.2 | Chrome: esperar | Espera la página de términos | — | — | E2-01, E2-02, E2-03, E2-04 (+11) |
| 1.2.3.1.4.6.1.3 | Chrome: clic | Marca «Acepto» los términos de uso | — | — | E2-01, E2-02, E2-03, E2-04 (+10) |
| 1.2.3.1.4.6.1.4 | Chrome: clic | Pulsa «Continuar» | — | — | E2-01, E2-02, E2-03, E2-04 (+10) |
| 1.2.3.1.4.6.1.5 | Chrome: esperar | Espera el formulario de consulta | — | — | E2-01, E2-02, E2-03, E2-04 (+10) |
| 1.2.3.1.4.6.1.6 | Chrome: leer texto | Lee el texto de la página (aviso de cuota, si lo hay) | — | locStrTexto | E2-01, E2-02, E2-03, E2-04 (+10) |
| 1.2.3.1.4.6.1.7 | Paso (componente) | Lee el texto de la página de la Policía | glbStrRutaRaiz, locStrTexto | locDicPagina | E2-01, E2-02, E2-03, E2-04 (+10) |
| 1.2.3.1.4.6.e.1 | Asignar | Policía caída o con estructura inesperada: se consulta la Procuraduría | locDicIdentidad | locDicIdentidad | E2-05 |
| 1.2.3.1.4.7 | Decisión | Cuota agotada del reCAPTCHA de la Policía: el bot no lo evade, queda en revisión humana | locDicIdentidad, locDicPagina | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.7.1 | Asignar | Etapa: revisión humana (cuota agotada) | locDicIdentidad | locDicIdentidad | E2-03 |
| 1.2.3.1.4.8 | Decisión | Modo real: el reCAPTCHA v2 lo resuelve una persona; el bot se detiene | glbDicPortales, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.8.1 | Asignar | Etapa: revisión humana (reCAPTCHA) | locDicIdentidad | locDicIdentidad | **sin cubrir** |
| 1.2.3.1.4.9 | Decisión | Modo fixture: el clon entrega el captcha ya resuelto (el lab no ejercita la resolución) | glbDicPortales, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.9.1 | Chrome: clic | Marca la casilla del clon «No soy un robot» | — | — | E2-01, E2-02, E2-04, E2-06 (+9) |
| 1.2.3.1.4.10 | Control de errores | Policía: consulta la cédula | — | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.10.1 | Decisión | Consulta en la Policía | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.10.1.1 | Chrome: escribir | Escribe el número de cédula | locStrDocumento | — | E2-01, E2-02, E2-04, E2-06 (+9) |
| 1.2.3.1.4.10.1.2 | Chrome: clic | Pulsa «Consultar» | — | — | E2-01, E2-02, E2-04, E2-06 (+9) |
| 1.2.3.1.4.10.1.3 | Chrome: esperar | Espera la respuesta de la Policía | — | — | E2-01, E2-02, E2-04, E2-06 (+9) |
| 1.2.3.1.4.10.1.4 | Chrome: leer texto | Lee el texto del resultado | — | locStrTexto | E2-01, E2-02, E2-04, E2-06 (+9) |
| 1.2.3.1.4.10.1.5 | Paso (componente) | Lee el texto del resultado de la Policía | glbStrRutaRaiz, locStrTexto | locDicPagina | E2-01, E2-02, E2-04, E2-06 (+9) |
| 1.2.3.1.4.10.e.1 | Asignar | Policía caída durante la consulta: se consulta la Procuraduría | locDicIdentidad | locDicIdentidad | **sin cubrir** |
| 1.2.3.1.4.11 | Decisión | El reCAPTCHA escaló a un reto de imágenes: lo resuelve una persona | locDicIdentidad, locDicPagina | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.11.1 | Asignar | Etapa: revisión humana (reto de imágenes) | locDicIdentidad | locDicIdentidad | E2-04 |
| 1.2.3.1.4.12 | Decisión | La Policía devolvió el nombre oficial (apellidos y luego nombres) | locDicIdentidad, locDicPagina | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.12.1 | Asignar | Etapa: comparar nombres (HU-008) | locDicIdentidad, locDicPagina | locDicIdentidad | E2-01, E2-07, E2-08, E2-13 (+3) |
| 1.2.3.1.4.13 | Decisión | La Policía no devolvió resultado: se consulta la Procuraduría | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.4.13.1 | Asignar | Etapa: consulta en la Procuraduría | locDicIdentidad | locDicIdentidad | E2-02, E2-06, E2-12, E2-19 (+1) |
| 1.2.3.1.5 | Grupo | HU007 - Consultar la Procuraduría (Chrome) | — | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.5.1 | Asignar | Página de la Procuraduría (aún sin leer) | — | locDicPaginaProc | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.5.2 | Decisión | NIT con cantidad de dígitos distinta de 10: gestión manual, no se consulta | locDicDocumento, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.5.2.1 | Asignar | Etapa: gestión manual (NIT inválido) | locDicIdentidad | locDicIdentidad | E2-16 |
| 1.2.3.1.5.3 | Decisión | Tipo de documento sin consulta en la Procuraduría: gestión manual | locDicDocumento, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.5.3.1 | Asignar | Etapa: gestión manual (tipo sin consulta) | locDicIdentidad | locDicIdentidad | E2-18 |
| 1.2.3.1.5.4 | Control de errores | Procuraduría: abre el portal y acepta los términos | — | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.5.4.1 | Decisión | Consulta en la Procuraduría | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.5.4.1.1 | Chrome: URL | Abre el portal de la Procuraduría | glbStrUrlProcuraduria | — | E2-01, E2-02, E2-03, E2-04 (+11) |
| 1.2.3.1.5.4.1.2 | Chrome: esperar | Espera la página de términos | — | — | E2-01, E2-02, E2-03, E2-04 (+11) |
| 1.2.3.1.5.4.1.3 | Chrome: clic | Marca «Acepto» los términos | — | — | E2-01, E2-02, E2-03, E2-04 (+8) |
| 1.2.3.1.5.4.1.4 | Chrome: clic | Pulsa «Continuar» | — | — | E2-01, E2-02, E2-03, E2-04 (+8) |
| 1.2.3.1.5.4.1.5 | Chrome: esperar | Espera la pregunta del captcha | — | — | E2-01, E2-02, E2-03, E2-04 (+8) |
| 1.2.3.1.5.4.e.1 | Asignar | Procuraduría caída, bloqueada o con estructura inesperada: excepción de sistema | locDicIdentidad | locDicIdentidad | E2-06, E2-07, E2-08 |
| 1.2.3.1.6 | Grupo | HU026a - Resolver el captcha de pregunta (servicio de captchas) | — | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.6.1 | Asignar | Intentos permitidos (CAPTCHA_MAX_REINTENTOS) | glbDicPortales | locArrIntentos | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.6.2 | Bucle | Intento de resolver el captcha | locArrIntentos | locIntIntento | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.6.2.1 | Decisión | Lee la pregunta y la envía al servicio de captchas (el bot no calcula la respuesta) | locDicIdentidad | — | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.6.2.1.1 | Chrome: leer texto | Lee la pregunta del captcha | — | locStrPregunta | E2-01, E2-02, E2-03, E2-04 (+8) |
| 1.2.3.1.6.2.1.2 | Paso (componente) | Envía pregunta, documento y nombre al servicio de captchas | glbStrRutaRaiz, locStrDocumento, locStrNombre, locStrPregunta | locDicCaptcha | E2-01, E2-02, E2-03, E2-04 (+8) |
| 1.2.3.1.6.2.1.3 | Asignar | Respuesta que retornó el servicio | locDicCaptcha | locStrRespuesta | E2-01, E2-02, E2-03, E2-04 (+8) |
| 1.2.3.1.6.2.2 | Decisión | El servicio respondió: diligencia el formulario y consulta | locDicCaptcha, locDicIdentidad | — | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.6.2.2.1 | Chrome: escribir | Escribe el nombre | locStrNombre | — | E2-01, E2-02, E2-03, E2-04 (+6) |
| 1.2.3.1.6.2.2.2 | Chrome: clic | Elige el tipo de documento en el desplegable | locStrCodigoTipo | — | E2-01, E2-02, E2-03, E2-04 (+6) |
| 1.2.3.1.6.2.2.3 | Chrome: escribir | Escribe el número de documento | locStrDocumento | — | E2-01, E2-02, E2-03, E2-04 (+6) |
| 1.2.3.1.6.2.2.4 | Chrome: escribir | Escribe la respuesta del captcha | locStrRespuesta | — | E2-01, E2-02, E2-03, E2-04 (+6) |
| 1.2.3.1.6.2.2.5 | Chrome: clic | Pulsa «Consultar» | — | — | E2-01, E2-02, E2-03, E2-04 (+6) |
| 1.2.3.1.6.2.2.6 | Chrome: esperar | Espera la respuesta de la Procuraduría | — | — | E2-01, E2-02, E2-03, E2-04 (+6) |
| 1.2.3.1.6.2.2.7 | Chrome: leer texto | Lee el texto del resultado | — | locStrTexto | E2-01, E2-02, E2-03, E2-04 (+6) |
| 1.2.3.1.6.2.2.8 | Paso (componente) | Lee el bloque «Datos del ciudadano» | glbStrRutaRaiz, locStrTexto | locDicPaginaProc | E2-01, E2-02, E2-03, E2-04 (+6) |
| 1.2.3.1.6.2.3 | Decisión | El servicio no puede resolver esta pregunta: pide otra con el botón de refresco (cuenta como intento) | locDicCaptcha, locDicIdentidad | — | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.6.2.3.1 | Chrome: clic | Pulsa el botón de refresco de la pregunta | — | — | E2-02, E2-05, E2-09, E2-11 (+1) |
| 1.2.3.1.6.2.4 | Decisión | Servicio de captchas no disponible tras los reintentos: excepción de sistema | locDicCaptcha, locDicIdentidad | — | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.6.2.4.1 | Asignar | Etapa: excepción de sistema (servicio de captchas) | locDicIdentidad | locDicIdentidad | E2-10 |
| 1.2.3.1.6.2.5 | Decisión | La Procuraduría devolvió el nombre (bloque «Datos del ciudadano») | locDicIdentidad, locDicPaginaProc | — | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.6.2.5.1 | Asignar | Etapa: comparar nombres (HU-008) | locDicIdentidad, locDicPaginaProc | locDicIdentidad | E2-01, E2-02, E2-03, E2-04 (+3) |
| 1.2.3.1.6.2.6 | Decisión | Respuesta sin nombre y el documento es cédula: ni Policía ni Procuraduría dieron resultado, gestión manual | locDicDocumento, locDicIdentidad, locDicPaginaProc | — | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.6.2.6.1 | Asignar | Etapa: gestión manual (sin resultado) | locDicIdentidad | locDicIdentidad | E2-20 |
| 1.2.3.1.6.2.7 | Decisión | Respuesta sin nombre para un documento no cédula: se registra y continúa | locDicDocumento, locDicIdentidad, locDicPaginaProc | — | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.6.2.7.1 | Asignar | Etapa: sin nombre (continúa) | locDicIdentidad | locDicIdentidad | E2-17 |
| 1.2.3.1.6.3 | Decisión | Captcha no resuelto tras los intentos permitidos: excepción de sistema y gestión manual | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.6.3.1 | Asignar | Etapa: excepción de sistema (CAPTCHA_MAX_REINTENTOS) | locDicIdentidad | locDicIdentidad | E2-09, E2-11 |
| 1.2.3.1.7 | Grupo | HU008 - Comparar nombres (umbral 0.80, sin depender del orden) | — | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.7.1 | Decisión | Compara el nombre de Zeus con el del portal (normalizado, sin depender del orden) | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.7.1.1 | Paso (componente) | Calcula el puntaje y lo compara con UMBRAL_COINCIDENCIA_NOMBRES | glbStrRutaRaiz, locDicIdentidad, locStrNombre | locDicVeredicto | E2-01, E2-02, E2-03, E2-04 (+9) |
| 1.2.3.1.7.2 | Decisión | El puntaje alcanza el umbral: la identidad queda validada | locDicIdentidad, locDicVeredicto | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.7.2.1 | Asignar | Etapa: identidad validada | locDicIdentidad, locDicVeredicto | locDicIdentidad | E2-01, E2-02, E2-03, E2-04 (+6) |
| 1.2.3.1.7.3 | Decisión | El puntaje no alcanza el umbral o el nombre es incompleto: excepción de negocio 3 | locDicIdentidad, locDicVeredicto | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.7.3.1 | Asignar | Etapa: excepción de negocio 3 | locDicIdentidad, locDicVeredicto | locDicIdentidad | E2-13, E2-14, E2-15 |
| 1.2.3.1.7.4 | Decisión | Escribe el comentario de la excepción de negocio 3 en Gestión → Detalle | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.7.4.1 | Paso (componente) | Comentario de la excepción de negocio 3 (revisión de Cartera) | glbStrRutaRaiz, locDicCaso, locDicIdentidad, locDicVeredicto | locDicComentarioIdentidad | E2-13, E2-14, E2-15 |
| 1.2.3.1.7.5 | Decisión | El comentario no se pudo registrar: excepción de sistema | locDicComentarioIdentidad, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.7.5.1 | Asignar | Etapa: excepción de sistema (comentario no registrado) | locDicComentarioIdentidad, locDicIdentidad | locDicIdentidad | E2-15 |
| 1.2.3.1.8 | Grupo | HU006HU007HU008 - Registrar el resultado de identidad | — | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.8.1 | Decisión | Deja el resultado de identidad en el reporte y los logs | glbArrAvanzan, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.8.1.1 | Paso (componente) | Registra el resultado de identidad (sin nombres ni identificaciones) | glbStrRutaRaiz, locDicCaso, locDicIdentidad, locStrIdRadicado | locDicEvento | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.3.1.8.2 | Decisión | Resultado «validada» | glbArrAvanzan, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.8.2.1 | Asignar | Anota el radicado en identidad validada | glbArrValidadas, locStrIdRadicado | glbArrValidadas | E2-01, E2-02, E2-03, E2-04 (+6) |
| 1.2.3.1.8.3 | Decisión | Resultado «excepcion_negocio_3» | glbArrAvanzan, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.8.3.1 | Asignar | Anota el radicado en excepciones de negocio 3 | glbArrExcepcionesNegocioTres, locStrIdRadicado | glbArrExcepcionesNegocioTres | E2-13, E2-14 |
| 1.2.3.1.8.4 | Decisión | Resultado «revision_humana» | glbArrAvanzan, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.8.4.1 | Asignar | Anota el radicado en revisión humana | glbArrRevisionHumana, locStrIdRadicado | glbArrRevisionHumana | E2-03, E2-04 |
| 1.2.3.1.8.5 | Decisión | Resultado «sin_nombre» | glbArrAvanzan, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.8.5.1 | Asignar | Anota el radicado en respuesta sin nombre | glbArrSinNombre, locStrIdRadicado | glbArrSinNombre | E2-17 |
| 1.2.3.1.8.6 | Decisión | Resultado «gestion_manual» | glbArrAvanzan, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.8.6.1 | Asignar | Anota el radicado en gestión manual | glbArrGestionManual, locStrIdRadicado | glbArrGestionManual | E2-16, E2-18, E2-20 |
| 1.2.3.1.8.7 | Decisión | Resultado «excepcion_sistema»: el caso va a gestión manual | glbArrAvanzan, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.3.1.8.7.1 | Asignar | Anota el radicado en excepciones de sistema de identidad | glbArrExcepcionesSistemaIdentidad, locStrIdRadicado | glbArrExcepcionesSistemaIdentidad | E2-06, E2-07, E2-08, E2-09 (+3) |
| 1.2.3.1.8.7.2 | Asignar | Anota el radicado en gestión manual | glbArrGestionManual, locStrIdRadicado | glbArrGestionManual | E2-06, E2-07, E2-08, E2-09 (+3) |
| 1.2.3.1.8.7.3 | Asignar | Guarda el código de error del radicado | glbDicCodigos, locDicIdentidad, locStrIdRadicado | glbDicCodigos | E2-06, E2-07, E2-08, E2-09 (+3) |
| 1.2.3.1.9 | Paso (componente) | Deja constancia del fin del radicado en el log de auditoría | glbStrRutaRaiz, locStrIdRadicado | locDicEvento | E1-01, E1-08, E1-09, E1-10 (+25) |
| 1.2.4 | Decisión | La identidad está habilitada y la selección terminó bien: deja constancia de su fin | glbDicEstado, glbDicPortales | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.2.4.1 | Paso (componente) | Deja constancia del fin de la validación de identidad en el log de auditoría | glbStrRutaRaiz | locDicEvento | E2-01, E2-02, E2-03, E2-04 (+16) |
| 1.2.e.1 | Asignar | Marca fallo de sistema en el proceso principal | — | glbBlnEstadoSistema | **sin cubrir** |
| 1.2.e.2 | Asignar | Estado de la ejecución: detenido por excepción de sistema | glbDicEstado | glbDicEstado | **sin cubrir** |
| 1.3 | Grupo | HU002HU003HU004 - Cierre y registro de ejecución | — | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.3.1 | Decisión | La ejecución se detuvo | glbDicEstado | — | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.3.1.1 | Paso (componente) | Registra la detención en el log de errores y prepara el aviso «Detenido» | glbDicEstado, glbStrRutaRaiz | glbDicDetencion | E1-04, E1-05, E1-06, E1-07 |
| 1.3.1.2 | Asignar | Asunto del aviso que se enviará al equipo técnico | glbDicDetencion | glbStrAsuntoAviso | E1-04, E1-05, E1-06, E1-07 |
| 1.3.2 | Paso (componente) | Cierra la ejecución y deja el resumen sin PII (en modo real los datos personales se enmascaran) | glbArrAvanzan, glbArrExcepcionesNegocioUno, glbArrExcepcionesSistema, glbArrIdsDescartados, glbDicDetencion, glbDicEstado, glbDicInicio, glbStrRutaRaiz | glbStrResumen | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.3.3 | Asignar | Observación final de la corrida | glbArrAvanzan, glbArrExcepcionesNegocioUno, glbArrExcepcionesSistema, glbDicEstado, glbDicInicio | glbStrObservaciones | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.3.4 | Asignar | El proceso terminó sin detenerse | glbDicEstado | glbBlnEstadoProceso | E1-01, E1-02, E1-03, E1-04 (+32) |
| 1.e.1 | Asignar | Marca fallo de sistema | — | glbBlnEstadoSistema | **sin cubrir** |
| 1.e.2 | Asignar | Observación de la excepción de sistema | — | glbStrObservaciones | **sin cubrir** |
| 2 | Log | Traza final de la ejecución | glbStrObservaciones | — | E1-01, E1-02, E1-03, E1-04 (+32) |

Escenarios: `E001-NN` = banco EP-001 (`banco/escenarios/EP-001.json`), `EP002-NN` = banco EP-002.
