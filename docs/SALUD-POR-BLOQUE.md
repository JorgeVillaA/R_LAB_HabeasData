# Salud por bloque del robot `LabHabeasData`

> Práctica **experimental** D-21 (test por bloque en Studio). Generado por `python banco/salud_por_bloque.py`; **no editar a mano**. La cobertura se mide: cada escenario del banco (EP-001: 18, EP-002: 20, EP-003: 8) corre el JSON del robot en el intérprete (`banco/interprete_robot.py`) y se anota qué bloques ejecutó.

## Cómo probar un bloque solo
1. En Studio, botón de test del bloque: ejecuta `commands:[ese bloque]` con las variables actuales; `playNode` arranca desde cualquier bloque.
2. Todo bloque tiene **entrada y salida explícitas** (columnas de abajo). Los bloques `Paso (componente)` reciben la raíz (`glbStrRutaRaiz`) y llaman a `pasos.asegurar(raíz)`: reconstruyen la sesión solos, sin depender de que otro bloque haya corrido antes.
3. La lógica pura sigue en funciones probadas sin abrir Studio (`Scripts/habeasdata`, `tests/`).
4. Los bloques de Chrome necesitan los clones de portales arriba (`python dobles/portales/servidor.py 8766`) y el servicio de captchas.

## Resumen
- Bloques: **273** (Chrome: clic 9, Decisión 74, Paso (componente) 47, Bucle 2, Grupo 12, Log 1, Chrome: URL 2, Chrome: abrir 1, Chrome: escribir 4, Asignar 106, Chrome: leer texto 4, Control de errores 5, Chrome: esperar 6).
- Cubiertos por al menos un escenario: **264**; **sin cubrir: 9**.

### Huecos de cobertura (bloques sin escenario)

| Bloque | Tipo | Descripción |
|---|---|---|
| 1.1.25.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló |
| 1.2.1.2.4.3.3.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló |
| 1.2.1.2.4.4.2.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló |
| 1.2.4.1.5.8.1 | Asignar | Etapa: revisión humana (reCAPTCHA) |
| 1.2.4.1.5.10.e.1 | Asignar | Policía caída durante la consulta: se consulta la Procuraduría |
| 1.2.e.1 | Asignar | Marca fallo de sistema en el proceso principal |
| 1.2.e.2 | Asignar | Estado de la ejecución: detenido por excepción de sistema |
| 1.e.1 | Asignar | Marca fallo de sistema |
| 1.e.2 | Asignar | Observación de la excepción de sistema |

Un bloque sin escenario no tiene prueba que lo ejercite: se reporta como hueco, no se declara sano.

## Mapa

| Bloque | Tipo | Qué hace | Entrada | Salida | Escenarios del banco |
|---|---|---|---|---|---|
| 1 | Control de errores | Control de ejecución | — | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1 | Grupo | HU002HU003HU004 - Inicializar el Asistente | — | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.1 | Asignar | Estado de la ejecución: estado, motivo si la selección queda vacía (HU-002), total de radicados y motivo de detención | — | glbDicEstado | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.2 | Asignar | Radicados seleccionados por HU-002 | — | glbArrIdsRadicados | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.3 | Asignar | Radicados descartados por identificación ausente (HU-002) | — | glbArrIdsDescartados | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.4 | Asignar | Radicados que avanzan a la validación de deuda (HU-004) | — | glbArrAvanzan | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.5 | Asignar | Radicados en excepción de negocio 1 (HU-004) | — | glbArrExcepcionesNegocioUno | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.6 | Asignar | Radicados en excepción de sistema (HU-003, HU-004) | — | glbArrExcepcionesSistema | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.7 | Paso (componente) | Carga los tres JSON de configuración, crea la estructura de carpetas y los dos logs del día | glbStrRutaRaiz | glbDicInicio | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.8 | Paso (componente) | Lee los parámetros de negocio de la configuración (tipología, campo, literal de ausencia, lote, orden) | glbStrRutaRaiz | glbDicParametros | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.9 | Asignar | Radicados con identidad validada (HU-008) | — | glbArrValidadas | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.10 | Asignar | Radicados en excepción de negocio 3 (HU-008) | — | glbArrExcepcionesNegocioTres | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.11 | Asignar | Radicados en revisión humana (HU-006) | — | glbArrRevisionHumana | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.12 | Asignar | Radicados con respuesta sin nombre (HU-007) | — | glbArrSinNombre | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.13 | Asignar | Radicados derivados a gestión manual (HU-006, HU-007, HU-026a) | — | glbArrGestionManual | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.14 | Asignar | Radicados en excepción de sistema de identidad | — | glbArrExcepcionesSistemaIdentidad | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.15 | Asignar | Códigos de error de identidad por radicado | — | glbDicCodigos | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.16 | Asignar | Radicados que siguen a la validación de identidad (tras HU-004 y HU-010) | — | glbArrSiguenIdentidad | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.17 | Asignar | Radicados en excepción de negocio 4 (HU-010) | — | glbArrExcepcionesNegocioCuatro | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.18 | Asignar | Radicados en excepción de sistema del repositorio (HU-010) | — | glbArrExcepcionesSistemaRepositorio | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.19 | Asignar | Radicados que no pudieron consultar el repositorio (HU-010) | — | glbArrRepositorioCaido | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.20 | Asignar | Radicados con la exclusión registrada (HU-011) | — | glbArrExclusionRegistrada | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.21 | Asignar | Radicados en excepción de sistema de la exclusión (HU-011) | — | glbArrExcepcionesSistemaExclusion | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.22 | Paso (componente) | Lee si el repositorio local está habilitado y lo abre (Repositorio.Habilitado) | glbStrRutaRaiz | glbDicRepositorio | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.23 | Asignar | Chrome aún no está abierto | — | glbBlnChromeAbierto | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.24 | Paso (componente) | Lee el modo, las URL de los portales y los reintentos del captcha; en modo real exige autorización y ventana operativa | glbStrRutaRaiz | glbDicPortales | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.25 | Decisión | Los portales no se pueden usar (falta autorización o ventana operativa) | glbDicPortales | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.25.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicEstado, glbDicPortales | glbDicEstado | **sin cubrir** |
| 1.1.26 | Asignar | URL del portal de la Policía | glbDicPortales | glbStrUrlPolicia | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.1.27 | Asignar | URL del portal de la Procuraduría | glbDicPortales | glbStrUrlProcuraduria | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2 | Control de errores | Proceso principal | — | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.1 | Grupo | HU002 - Filtrar radicados de Exclusión de Datos | — | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.1.1 | Paso (componente) | Solicita el token OAuth (client_credentials, vigencia 300 s); el secreto sale del Administrador de credenciales | glbStrRutaRaiz | glbDicAutenticacion | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.1.2 | Decisión | El token se obtuvo | glbDicAutenticacion | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.1.2.1 | Asignar | Arma la consulta de HU-002: filtro OData de la tipología ($filter, base de la selección), campos ($select), lote ($first) y orden ($orderby) | glbDicParametros | locDicConsulta | E1-01, E1-02, E1-03, E1-04 (+42) |
| 1.2.1.2.2 | Decisión | Se descartan los radicados sin identificación (parámetro) | glbDicParametros | — | E1-01, E1-02, E1-03, E1-04 (+42) |
| 1.2.1.2.2.1 | Asignar | Agrega al filtro: identificación distinta de «NO APORTA» | glbDicParametros, locDicConsulta | locDicConsulta | E1-01, E1-02, E1-03, E1-04 (+41) |
| 1.2.1.2.3 | Paso (componente) | Consulta los radicados de exclusión (GET OData con $filter, $select, $first y $orderby) | glbStrRutaRaiz, locDicConsulta | glbDicSeleccion | E1-01, E1-02, E1-03, E1-04 (+42) |
| 1.2.1.2.4 | Decisión | La consulta respondió | glbDicSeleccion | — | E1-01, E1-02, E1-03, E1-04 (+42) |
| 1.2.1.2.4.1 | Asignar | Guarda los radicados seleccionados | glbDicSeleccion | glbArrIdsRadicados | E1-01, E1-02, E1-03, E1-08 (+39) |
| 1.2.1.2.4.2 | Paso (componente) | Deja constancia en el log de auditoría de los radicados identificados | glbArrIdsRadicados, glbStrRutaRaiz | locDicEvento | E1-01, E1-02, E1-03, E1-08 (+39) |
| 1.2.1.2.4.3 | Decisión | Se descartan los radicados sin identificación (parámetro) | glbDicParametros | — | E1-01, E1-02, E1-03, E1-08 (+39) |
| 1.2.1.2.4.3.1 | Asignar | Arma el filtro de los descartados: identificación igual a «NO APORTA» | glbDicParametros, locDicConsulta | locStrFiltroDescartados | E1-01, E1-02, E1-03, E1-08 (+38) |
| 1.2.1.2.4.3.2 | Paso (componente) | Consulta los radicados descartados para no perderlos en silencio | glbStrRutaRaiz, locStrFiltroDescartados | glbDicDescartados | E1-01, E1-02, E1-03, E1-08 (+38) |
| 1.2.1.2.4.3.3 | Decisión | La consulta de descartados respondió | glbDicDescartados | — | E1-01, E1-02, E1-03, E1-08 (+38) |
| 1.2.1.2.4.3.3.1 | Asignar | Guarda los radicados descartados | glbDicDescartados | glbArrIdsDescartados | E1-01, E1-02, E1-03, E1-08 (+38) |
| 1.2.1.2.4.3.3.2 | Paso (componente) | Deja los descartados en el log de auditoría y en el reporte | glbArrIdsDescartados, glbStrRutaRaiz | glbDicRegistroDescartados | E1-01, E1-02, E1-03, E1-08 (+38) |
| 1.2.1.2.4.3.3.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicDescartados, glbDicEstado | glbDicEstado | **sin cubrir** |
| 1.2.1.2.4.4 | Decisión | La selección quedó vacía y no hubo fallos | glbArrIdsRadicados, glbDicEstado | — | E1-01, E1-02, E1-03, E1-08 (+39) |
| 1.2.1.2.4.4.1 | Paso (componente) | Consulta el total de radicados (consulta general, sin $filter) | glbStrRutaRaiz | glbDicGeneral | E1-02, E1-03, E1-16, E1-17 (+1) |
| 1.2.1.2.4.4.2 | Decisión | La consulta general respondió | glbDicGeneral | — | E1-02, E1-03, E1-16, E1-17 (+1) |
| 1.2.1.2.4.4.2.1 | Asignar | Total de radicados de la consulta general | glbDicEstado, glbDicGeneral | glbDicEstado | E1-02, E1-03, E1-16, E1-17 (+1) |
| 1.2.1.2.4.4.2.2 | Decisión | Todos los de la tipología fueron descartados | glbArrIdsDescartados | — | E1-02, E1-03, E1-16, E1-17 (+1) |
| 1.2.1.2.4.4.2.2.1 | Asignar | Motivo: solo descartados | glbDicEstado | glbDicEstado | E1-16 |
| 1.2.1.2.4.4.2.2.e.1 | Decisión | Hay radicados, pero ninguno de la tipología | glbDicEstado | — | E1-02, E1-03, E1-17, E1-18 |
| 1.2.1.2.4.4.2.2.e.1.1 | Asignar | Motivo: tipología ausente | glbDicEstado | glbDicEstado | E1-03 |
| 1.2.1.2.4.4.2.2.e.1.e.1 | Asignar | Motivo: bandeja vacía | glbDicEstado | glbDicEstado | E1-02, E1-17, E1-18 |
| 1.2.1.2.4.4.2.3 | Paso (componente) | Registra «0 casos» y la cadencia del reintento (CADENCIA_REINTENTO_BANDEJA_VACIA) | glbDicEstado, glbStrRutaRaiz | glbDicSinCasos | E1-02, E1-03, E1-16, E1-17 (+1) |
| 1.2.1.2.4.4.2.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicEstado, glbDicGeneral | glbDicEstado | **sin cubrir** |
| 1.2.1.2.4.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicEstado, glbDicSeleccion | glbDicEstado | E1-04, E1-05, E1-06 |
| 1.2.1.2.e.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicAutenticacion, glbDicEstado | glbDicEstado | E1-07 |
| 1.2.1.3 | Decisión | Sigue sin casos: agenda el reintento (espera la cadencia y vuelve a consultar) | glbArrIdsRadicados, glbDicEstado | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.1.3.1 | Paso (componente) | Espera MinutosEntreReintentos y reconsulta, hasta MaximoReintentosDiarios o hasta que aparezcan casos (CADENCIA_REINTENTO_BANDEJA_VACIA) | glbStrRutaRaiz | glbDicReintento | E1-02, E1-03, E1-16, E1-17 (+1) |
| 1.2.1.3.2 | Decisión | Hubo reintentos y la consulta respondió | glbDicReintento | — | E1-02, E1-03, E1-16, E1-17 (+1) |
| 1.2.1.3.2.1 | Asignar | Guarda los radicados seleccionados en el reintento | glbDicReintento | glbArrIdsRadicados | E1-02, E1-03, E1-16, E1-17 |
| 1.2.1.3.2.2 | Asignar | Guarda los descartados del último intento | glbDicReintento | glbArrIdsDescartados | E1-02, E1-03, E1-16, E1-17 |
| 1.2.1.3.2.3 | Asignar | Motivo con el que terminó el último intento | glbDicEstado, glbDicReintento | glbDicEstado | E1-02, E1-03, E1-16, E1-17 |
| 1.2.1.3.3 | Decisión | El reintento se detuvo por una falla crítica | glbDicReintento | — | E1-02, E1-03, E1-16, E1-17 (+1) |
| 1.2.1.3.3.1 | Asignar | Marca la ejecución como detenida y guarda el motivo del paso que falló | glbDicEstado, glbDicReintento | glbDicEstado | E1-18 |
| 1.2.2 | Decisión | La identidad está habilitada y la selección terminó bien: deja constancia de su inicio | glbDicEstado, glbDicPortales | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.2.1 | Paso (componente) | Deja constancia del inicio de la validación de identidad en el log de auditoría | glbDicPortales, glbStrRutaRaiz | locDicEvento | EP002-01, EP002-02, EP002-03, EP002-04 (+25) |
| 1.2.3 | Decisión | El repositorio está habilitado y la selección terminó bien: deja constancia del inicio de la búsqueda de duplicados | glbDicEstado, glbDicRepositorio | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.3.1 | Paso (componente) | Deja constancia del inicio de la búsqueda de duplicados (EP-003) | glbStrRutaRaiz | locDicEvento | EP003-01, EP003-02, EP003-03, EP003-04 (+5) |
| 1.2.4 | Decisión | Hay radicados que procesar | glbArrIdsRadicados, glbDicEstado | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.4.1 | Bucle | Iteración por radicado de exclusión | glbArrIdsRadicados | locStrIdRadicado | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.1 | Paso (componente) | Deja constancia del inicio del radicado en el log de auditoría | glbStrRutaRaiz, locStrIdRadicado | locDicEvento | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.2 | Grupo | HU003 - Leer datos paramétricos | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.2.1 | Paso (componente) | Lee el radicado por IDRADICADO (GET individual) | glbStrRutaRaiz, locStrIdRadicado | locDicLectura | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.2.2 | Decisión | El radicado se pudo leer | locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.2.2.1 | Paso (componente) | Limpia «No aporta» y vacíos (= ausente) y separa los valores de cada canal por «/» | glbStrRutaRaiz, locDicLectura | locDicPreparado | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.2.2.2 | Paso (componente) | Clasifica cada teléfono por dígitos: celular, fijo o sin clasificar | glbStrRutaRaiz, locDicPreparado | locDicCaso | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.2.2.e.1 | Paso (componente) | Registra la excepción de sistema del radicado (log de errores y reporte) | glbStrRutaRaiz, locDicLectura, locStrIdRadicado | — | E1-08, E1-09 |
| 1.2.4.1.2.2.e.2 | Asignar | Anota el radicado en excepciones de sistema | glbArrExcepcionesSistema, locStrIdRadicado | glbArrExcepcionesSistema | E1-08, E1-09 |
| 1.2.4.1.3 | Grupo | HU004 - Validar campos obligatorios | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.3.1 | Asignar | Lista de motivos de incompletitud (vacía al empezar cada radicado) | — | locArrMotivos | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.3.2 | Decisión | Falta el nombre del cliente | locDicCaso, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.3.2.1 | Asignar | Agrega el motivo | locArrMotivos | locArrMotivos | E1-01, E1-08, E1-09, E1-10 (+4) |
| 1.2.4.1.3.3 | Decisión | Falta el tipo de identificación | locDicCaso, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.3.3.1 | Asignar | Agrega el motivo | locArrMotivos | locArrMotivos | E1-01, E1-08, E1-09, E1-10 (+4) |
| 1.2.4.1.3.4 | Decisión | Falta el número de identificación | locDicCaso, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.3.4.1 | Asignar | Agrega el motivo | locArrMotivos | locArrMotivos | E1-14 |
| 1.2.4.1.3.5 | Decisión | No hay ningún canal de contacto (ni correo ni teléfono) | locDicCaso, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.3.5.1 | Asignar | Agrega el motivo | locArrMotivos | locArrMotivos | E1-01, E1-08, E1-09, E1-10 (+5) |
| 1.2.4.1.3.6 | Decisión | El caso está completo | locArrMotivos, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.3.6.1 | Paso (componente) | Registra el avance a la validación de deuda en el reporte | glbStrRutaRaiz, locDicCaso | locDicResultado | E1-01, E1-08, E1-09, E1-10 (+34) |
| 1.2.4.1.3.6.2 | Asignar | Anota el radicado en los que avanzan | glbArrAvanzan, locStrIdRadicado | glbArrAvanzan | E1-01, E1-08, E1-09, E1-10 (+34) |
| 1.2.4.1.3.6.3 | Asignar | Anota el radicado en los que siguen a identidad | glbArrSiguenIdentidad, locStrIdRadicado | glbArrSiguenIdentidad | E1-01, E1-08, E1-09, E1-10 (+34) |
| 1.2.4.1.3.7 | Decisión | El caso está incompleto: excepción de negocio 1 | locArrMotivos, locDicLectura | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.3.7.1 | Paso (componente) | Escribe el comentario de la excepción de negocio 1 en Gestión → Detalle | glbStrRutaRaiz, locArrMotivos, locDicCaso | locDicComentario | E1-01, E1-08, E1-09, E1-10 (+5) |
| 1.2.4.1.3.7.2 | Decisión | El comentario quedó registrado | locDicComentario | — | E1-01, E1-08, E1-09, E1-10 (+5) |
| 1.2.4.1.3.7.2.1 | Paso (componente) | Registra la excepción de negocio 1 en el reporte | glbStrRutaRaiz, locArrMotivos, locDicCaso | locDicResultado | E1-01, E1-08, E1-09, E1-13 (+3) |
| 1.2.4.1.3.7.2.2 | Asignar | Anota el radicado en excepciones de negocio 1 | glbArrExcepcionesNegocioUno, locStrIdRadicado | glbArrExcepcionesNegocioUno | E1-01, E1-08, E1-09, E1-13 (+3) |
| 1.2.4.1.3.7.2.e.1 | Paso (componente) | Registra la excepción de sistema (no se pudo escribir el comentario) | glbStrRutaRaiz, locDicComentario, locStrIdRadicado | — | E1-10, E1-11 |
| 1.2.4.1.3.7.2.e.2 | Asignar | Anota el radicado en excepciones de sistema | glbArrExcepcionesSistema, locStrIdRadicado | glbArrExcepcionesSistema | E1-10, E1-11 |
| 1.2.4.1.4 | Grupo | HU010 - Buscar duplicados de exclusión (repositorio local) | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.1 | Asignar | Resultado de duplicados del radicado (vacío al empezar) | — | locDicDuplicado | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.2 | Asignar | Resultado del comentario de duplicado (vacío al empezar) | — | locDicComentarioDuplicado | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.3 | Decisión | Repositorio habilitado: deja en Transacciones las etapas previas del radicado (selección, lectura, completitud) | glbDicRepositorio | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.3.1 | Paso (componente) | Registra las transacciones previas del radicado | glbArrAvanzan, glbArrExcepcionesNegocioUno, glbStrRutaRaiz, locDicCaso, locStrIdRadicado | locDicEvento | EP003-01, EP003-02, EP003-03, EP003-04 (+5) |
| 1.2.4.1.4.4 | Decisión | El radicado avanzó (HU-004): busca cada valor de cada canal por separado (maestra y exclusión con llave compuesta) | glbArrAvanzan, glbDicRepositorio, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.4.1 | Paso (componente) | Busca duplicados: identificación + celular en Celulares, identificación + correo en Correos | glbStrRutaRaiz, locDicCaso | locDicDuplicado | EP003-01, EP003-02, EP003-03, EP003-04 (+5) |
| 1.2.4.1.4.5 | Decisión | El repositorio no respondió tras 3 intentos: excepción de sistema del caso (el bot continúa) | glbArrAvanzan, glbDicRepositorio, locDicDuplicado, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.5.1 | Paso (componente) | Registra la excepción de sistema del repositorio | glbStrRutaRaiz, locDicCaso, locDicDuplicado | locDicEvento | EP003-04, EP003-05 |
| 1.2.4.1.4.5.2 | Asignar | Anota el radicado en excepciones de sistema del repositorio | glbArrExcepcionesSistemaRepositorio, locStrIdRadicado | glbArrExcepcionesSistemaRepositorio | EP003-04, EP003-05 |
| 1.2.4.1.4.5.3 | Asignar | Anota el radicado en los que no pudieron consultar el repositorio | glbArrRepositorioCaido, locStrIdRadicado | glbArrRepositorioCaido | EP003-04, EP003-05 |
| 1.2.4.1.4.5.4 | Asignar | El radicado no sigue a identidad | glbArrSiguenIdentidad, locStrIdRadicado | glbArrSiguenIdentidad | EP003-04, EP003-05 |
| 1.2.4.1.4.6 | Decisión | Hay valores duplicados: escribe la nota de excepción de negocio 4 en Gestión → Detalle | glbArrAvanzan, glbDicRepositorio, locDicDuplicado, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.6.1 | Paso (componente) | Comentario de la excepción de negocio 4 (revisión de Cartera) | glbStrRutaRaiz, locDicCaso, locDicDuplicado | locDicComentarioDuplicado | EP003-02, EP003-03, EP003-09 |
| 1.2.4.1.4.7 | Decisión | La nota no se pudo registrar: excepción de sistema del caso | glbArrAvanzan, glbDicRepositorio, locDicComentarioDuplicado, locDicDuplicado, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.7.1 | Paso (componente) | Registra la excepción de sistema (nota de duplicado rechazada) | glbStrRutaRaiz, locDicCaso, locDicComentarioDuplicado | locDicEvento | EP003-09 |
| 1.2.4.1.4.7.2 | Asignar | Anota el radicado en excepciones de sistema del repositorio | glbArrExcepcionesSistemaRepositorio, locStrIdRadicado | glbArrExcepcionesSistemaRepositorio | EP003-09 |
| 1.2.4.1.4.7.3 | Asignar | El radicado no sigue a identidad | glbArrSiguenIdentidad, locStrIdRadicado | glbArrSiguenIdentidad | EP003-09 |
| 1.2.4.1.4.8 | Decisión | La nota quedó registrada: excepción de negocio 4 (solo los valores duplicados) | glbArrAvanzan, glbDicRepositorio, locDicComentarioDuplicado, locDicDuplicado, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.8.1 | Paso (componente) | Registra la excepción de negocio 4 en el reporte y en Transacciones | glbStrRutaRaiz, locDicCaso, locDicDuplicado | locDicEvento | EP003-02, EP003-03 |
| 1.2.4.1.4.8.2 | Asignar | Anota el radicado en excepciones de negocio 4 | glbArrExcepcionesNegocioCuatro, locStrIdRadicado | glbArrExcepcionesNegocioCuatro | EP003-02, EP003-03 |
| 1.2.4.1.4.9 | Decisión | Ningún valor es duplicado: sigue a la validación de identidad | glbArrAvanzan, glbDicRepositorio, locDicDuplicado, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.9.1 | Paso (componente) | Registra «sin duplicado» en Transacciones | glbStrRutaRaiz, locDicCaso | locDicEvento | EP003-01, EP003-04, EP003-06, EP003-07 (+1) |
| 1.2.4.1.4.10 | Decisión | Todos sus valores ya estaban excluidos: no sigue a identidad | glbArrAvanzan, glbDicRepositorio, locDicComentarioDuplicado, locDicDuplicado, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.4.10.1 | Asignar | El radicado no sigue a identidad | glbArrSiguenIdentidad, locStrIdRadicado | glbArrSiguenIdentidad | EP003-02 |
| 1.2.4.1.5 | Grupo | HU006 - Consultar la Policía Nacional (Chrome) | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.1 | Asignar | Estado de la identidad del radicado (empieza en «inicio») | — | locDicIdentidad | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.2 | Decisión | El radicado avanzó (HU-004) y la identidad está habilitada: prepara los datos del caso | glbArrSiguenIdentidad, glbDicPortales, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.2.1 | Paso (componente) | Deja constancia del inicio de la identidad del radicado en el log de auditoría | glbStrRutaRaiz, locStrIdRadicado | locDicEvento | EP002-01, EP002-02, EP002-03, EP002-04 (+22) |
| 1.2.4.1.5.2.2 | Paso (componente) | Clasifica el documento: cédula, NIT de 10 dígitos y código del tipo en la Procuraduría | glbStrRutaRaiz, locDicCaso | locDicDocumento | EP002-01, EP002-02, EP002-03, EP002-04 (+22) |
| 1.2.4.1.5.2.3 | Asignar | Número de documento a consultar | locDicDocumento | locStrDocumento | EP002-01, EP002-02, EP002-03, EP002-04 (+22) |
| 1.2.4.1.5.2.4 | Asignar | Nombre del caso en Zeus (la pregunta del captcha puede requerirlo) | locDicDocumento | locStrNombre | EP002-01, EP002-02, EP002-03, EP002-04 (+22) |
| 1.2.4.1.5.2.5 | Asignar | Código del tipo de documento en el desplegable de la Procuraduría | locDicDocumento | locStrCodigoTipo | EP002-01, EP002-02, EP002-03, EP002-04 (+22) |
| 1.2.4.1.5.3 | Decisión | Avanzó a identidad y el documento es cédula de ciudadanía: empieza por la Policía | glbArrSiguenIdentidad, glbDicPortales, locDicDocumento, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.3.1 | Asignar | Etapa: consulta en la Policía | locDicIdentidad | locDicIdentidad | EP002-01, EP002-02, EP002-03, EP002-04 (+17) |
| 1.2.4.1.5.4 | Decisión | Avanzó a identidad y el documento no es cédula: va directo a la Procuraduría | glbArrSiguenIdentidad, glbDicPortales, locDicDocumento, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.4.1 | Asignar | Etapa: consulta en la Procuraduría | locDicIdentidad | locDicIdentidad | EP002-01, EP002-02, EP002-03, EP002-04 (+10) |
| 1.2.4.1.5.5 | Decisión | Hay que usar un portal y Chrome aún no está abierto | glbBlnChromeAbierto, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.5.1 | Chrome: abrir | Abre Chrome (el robot corre en Chrome) | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+22) |
| 1.2.4.1.5.5.2 | Asignar | Chrome quedó abierto | — | glbBlnChromeAbierto | EP002-01, EP002-02, EP002-03, EP002-04 (+22) |
| 1.2.4.1.5.6 | Control de errores | Policía: abre el portal y acepta los términos | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.6.1 | Decisión | Consulta en la Policía | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.6.1.1 | Chrome: URL | Abre el portal de la Policía | glbStrUrlPolicia | — | EP002-01, EP002-02, EP002-03, EP002-04 (+17) |
| 1.2.4.1.5.6.1.2 | Chrome: esperar | Espera la página de términos | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+17) |
| 1.2.4.1.5.6.1.3 | Chrome: clic | Marca «Acepto» los términos de uso | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+16) |
| 1.2.4.1.5.6.1.4 | Chrome: clic | Pulsa «Continuar» | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+16) |
| 1.2.4.1.5.6.1.5 | Chrome: esperar | Espera el formulario de consulta | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+16) |
| 1.2.4.1.5.6.1.6 | Chrome: leer texto | Lee el texto de la página (aviso de cuota, si lo hay) | — | locStrTexto | EP002-01, EP002-02, EP002-03, EP002-04 (+16) |
| 1.2.4.1.5.6.1.7 | Paso (componente) | Lee el texto de la página de la Policía | glbStrRutaRaiz, locStrTexto | locDicPagina | EP002-01, EP002-02, EP002-03, EP002-04 (+16) |
| 1.2.4.1.5.6.e.1 | Asignar | Policía caída o con estructura inesperada: se consulta la Procuraduría | locDicIdentidad | locDicIdentidad | EP002-05 |
| 1.2.4.1.5.7 | Decisión | Cuota agotada del reCAPTCHA de la Policía: el bot no lo evade, queda en revisión humana | locDicIdentidad, locDicPagina | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.7.1 | Asignar | Etapa: revisión humana (cuota agotada) | locDicIdentidad | locDicIdentidad | EP002-03 |
| 1.2.4.1.5.8 | Decisión | Modo real: el reCAPTCHA v2 lo resuelve una persona; el bot se detiene | glbDicPortales, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.8.1 | Asignar | Etapa: revisión humana (reCAPTCHA) | locDicIdentidad | locDicIdentidad | **sin cubrir** |
| 1.2.4.1.5.9 | Decisión | Modo fixture: el clon entrega el captcha ya resuelto (el lab no ejercita la resolución) | glbDicPortales, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.9.1 | Chrome: clic | Marca la casilla del clon «No soy un robot» | — | — | EP002-01, EP002-02, EP002-04, EP002-06 (+15) |
| 1.2.4.1.5.10 | Control de errores | Policía: consulta la cédula | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.10.1 | Decisión | Consulta en la Policía | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.10.1.1 | Chrome: escribir | Escribe el número de cédula | locStrDocumento | — | EP002-01, EP002-02, EP002-04, EP002-06 (+15) |
| 1.2.4.1.5.10.1.2 | Chrome: clic | Pulsa «Consultar» | — | — | EP002-01, EP002-02, EP002-04, EP002-06 (+15) |
| 1.2.4.1.5.10.1.3 | Chrome: esperar | Espera la respuesta de la Policía | — | — | EP002-01, EP002-02, EP002-04, EP002-06 (+15) |
| 1.2.4.1.5.10.1.4 | Chrome: leer texto | Lee el texto del resultado | — | locStrTexto | EP002-01, EP002-02, EP002-04, EP002-06 (+15) |
| 1.2.4.1.5.10.1.5 | Paso (componente) | Lee el texto del resultado de la Policía | glbStrRutaRaiz, locStrTexto | locDicPagina | EP002-01, EP002-02, EP002-04, EP002-06 (+15) |
| 1.2.4.1.5.10.e.1 | Asignar | Policía caída durante la consulta: se consulta la Procuraduría | locDicIdentidad | locDicIdentidad | **sin cubrir** |
| 1.2.4.1.5.11 | Decisión | El reCAPTCHA escaló a un reto de imágenes: lo resuelve una persona | locDicIdentidad, locDicPagina | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.11.1 | Asignar | Etapa: revisión humana (reto de imágenes) | locDicIdentidad | locDicIdentidad | EP002-04 |
| 1.2.4.1.5.12 | Decisión | La Policía devolvió el nombre oficial (apellidos y luego nombres) | locDicIdentidad, locDicPagina | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.12.1 | Asignar | Etapa: comparar nombres (HU-008) | locDicIdentidad, locDicPagina | locDicIdentidad | EP002-01, EP002-07, EP002-08, EP002-13 (+9) |
| 1.2.4.1.5.13 | Decisión | La Policía no devolvió resultado: se consulta la Procuraduría | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.5.13.1 | Asignar | Etapa: consulta en la Procuraduría | locDicIdentidad | locDicIdentidad | EP002-02, EP002-06, EP002-12, EP002-19 (+1) |
| 1.2.4.1.6 | Grupo | HU007 - Consultar la Procuraduría (Chrome) | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.6.1 | Asignar | Página de la Procuraduría (aún sin leer) | — | locDicPaginaProc | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.6.2 | Decisión | NIT con cantidad de dígitos distinta de 10: gestión manual, no se consulta | locDicDocumento, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.6.2.1 | Asignar | Etapa: gestión manual (NIT inválido) | locDicIdentidad | locDicIdentidad | EP002-16 |
| 1.2.4.1.6.3 | Decisión | Tipo de documento sin consulta en la Procuraduría: gestión manual | locDicDocumento, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.6.3.1 | Asignar | Etapa: gestión manual (tipo sin consulta) | locDicIdentidad | locDicIdentidad | EP002-18 |
| 1.2.4.1.6.4 | Control de errores | Procuraduría: abre el portal y acepta los términos | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.6.4.1 | Decisión | Consulta en la Procuraduría | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.6.4.1.1 | Chrome: URL | Abre el portal de la Procuraduría | glbStrUrlProcuraduria | — | EP002-01, EP002-02, EP002-03, EP002-04 (+11) |
| 1.2.4.1.6.4.1.2 | Chrome: esperar | Espera la página de términos | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+11) |
| 1.2.4.1.6.4.1.3 | Chrome: clic | Marca «Acepto» los términos | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+8) |
| 1.2.4.1.6.4.1.4 | Chrome: clic | Pulsa «Continuar» | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+8) |
| 1.2.4.1.6.4.1.5 | Chrome: esperar | Espera la pregunta del captcha | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+8) |
| 1.2.4.1.6.4.e.1 | Asignar | Procuraduría caída, bloqueada o con estructura inesperada: excepción de sistema | locDicIdentidad | locDicIdentidad | EP002-06, EP002-07, EP002-08 |
| 1.2.4.1.7 | Grupo | HU026a - Resolver el captcha de pregunta (servicio de captchas) | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.7.1 | Asignar | Intentos permitidos (CAPTCHA_MAX_REINTENTOS) | glbDicPortales | locArrIntentos | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.7.2 | Bucle | Intento de resolver el captcha | locArrIntentos | locIntIntento | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.7.2.1 | Decisión | Lee la pregunta y la envía al servicio de captchas (el bot no calcula la respuesta) | locDicIdentidad | — | EP002-01, EP002-02, EP002-03, EP002-04 (+25) |
| 1.2.4.1.7.2.1.1 | Chrome: leer texto | Lee la pregunta del captcha | — | locStrPregunta | EP002-01, EP002-02, EP002-03, EP002-04 (+8) |
| 1.2.4.1.7.2.1.2 | Paso (componente) | Envía pregunta, documento y nombre al servicio de captchas | glbStrRutaRaiz, locStrDocumento, locStrNombre, locStrPregunta | locDicCaptcha | EP002-01, EP002-02, EP002-03, EP002-04 (+8) |
| 1.2.4.1.7.2.1.3 | Asignar | Respuesta que retornó el servicio | locDicCaptcha | locStrRespuesta | EP002-01, EP002-02, EP002-03, EP002-04 (+8) |
| 1.2.4.1.7.2.2 | Decisión | El servicio respondió: diligencia el formulario y consulta | locDicCaptcha, locDicIdentidad | — | EP002-01, EP002-02, EP002-03, EP002-04 (+25) |
| 1.2.4.1.7.2.2.1 | Chrome: escribir | Escribe el nombre | locStrNombre | — | EP002-01, EP002-02, EP002-03, EP002-04 (+6) |
| 1.2.4.1.7.2.2.2 | Chrome: clic | Elige el tipo de documento en el desplegable | locStrCodigoTipo | — | EP002-01, EP002-02, EP002-03, EP002-04 (+6) |
| 1.2.4.1.7.2.2.3 | Chrome: escribir | Escribe el número de documento | locStrDocumento | — | EP002-01, EP002-02, EP002-03, EP002-04 (+6) |
| 1.2.4.1.7.2.2.4 | Chrome: escribir | Escribe la respuesta del captcha | locStrRespuesta | — | EP002-01, EP002-02, EP002-03, EP002-04 (+6) |
| 1.2.4.1.7.2.2.5 | Chrome: clic | Pulsa «Consultar» | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+6) |
| 1.2.4.1.7.2.2.6 | Chrome: esperar | Espera la respuesta de la Procuraduría | — | — | EP002-01, EP002-02, EP002-03, EP002-04 (+6) |
| 1.2.4.1.7.2.2.7 | Chrome: leer texto | Lee el texto del resultado | — | locStrTexto | EP002-01, EP002-02, EP002-03, EP002-04 (+6) |
| 1.2.4.1.7.2.2.8 | Paso (componente) | Lee el bloque «Datos del ciudadano» | glbStrRutaRaiz, locStrTexto | locDicPaginaProc | EP002-01, EP002-02, EP002-03, EP002-04 (+6) |
| 1.2.4.1.7.2.3 | Decisión | El servicio no puede resolver esta pregunta: pide otra con el botón de refresco (cuenta como intento) | locDicCaptcha, locDicIdentidad | — | EP002-01, EP002-02, EP002-03, EP002-04 (+25) |
| 1.2.4.1.7.2.3.1 | Chrome: clic | Pulsa el botón de refresco de la pregunta | — | — | EP002-02, EP002-05, EP002-09, EP002-11 (+1) |
| 1.2.4.1.7.2.4 | Decisión | Servicio de captchas no disponible tras los reintentos: excepción de sistema | locDicCaptcha, locDicIdentidad | — | EP002-01, EP002-02, EP002-03, EP002-04 (+25) |
| 1.2.4.1.7.2.4.1 | Asignar | Etapa: excepción de sistema (servicio de captchas) | locDicIdentidad | locDicIdentidad | EP002-10 |
| 1.2.4.1.7.2.5 | Decisión | La Procuraduría devolvió el nombre (bloque «Datos del ciudadano») | locDicIdentidad, locDicPaginaProc | — | EP002-01, EP002-02, EP002-03, EP002-04 (+25) |
| 1.2.4.1.7.2.5.1 | Asignar | Etapa: comparar nombres (HU-008) | locDicIdentidad, locDicPaginaProc | locDicIdentidad | EP002-01, EP002-02, EP002-03, EP002-04 (+3) |
| 1.2.4.1.7.2.6 | Decisión | Respuesta sin nombre y el documento es cédula: ni Policía ni Procuraduría dieron resultado, gestión manual | locDicDocumento, locDicIdentidad, locDicPaginaProc | — | EP002-01, EP002-02, EP002-03, EP002-04 (+25) |
| 1.2.4.1.7.2.6.1 | Asignar | Etapa: gestión manual (sin resultado) | locDicIdentidad | locDicIdentidad | EP002-20 |
| 1.2.4.1.7.2.7 | Decisión | Respuesta sin nombre para un documento no cédula: se registra y continúa | locDicDocumento, locDicIdentidad, locDicPaginaProc | — | EP002-01, EP002-02, EP002-03, EP002-04 (+25) |
| 1.2.4.1.7.2.7.1 | Asignar | Etapa: sin nombre (continúa) | locDicIdentidad | locDicIdentidad | EP002-17 |
| 1.2.4.1.7.3 | Decisión | Captcha no resuelto tras los intentos permitidos: excepción de sistema y gestión manual | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.7.3.1 | Asignar | Etapa: excepción de sistema (CAPTCHA_MAX_REINTENTOS) | locDicIdentidad | locDicIdentidad | EP002-09, EP002-11 |
| 1.2.4.1.8 | Grupo | HU008 - Comparar nombres (umbral 0.80, sin depender del orden) | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.8.1 | Decisión | Compara el nombre de Zeus con el del portal (normalizado, sin depender del orden) | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.8.1.1 | Paso (componente) | Calcula el puntaje y lo compara con UMBRAL_COINCIDENCIA_NOMBRES | glbStrRutaRaiz, locDicIdentidad, locStrNombre | locDicVeredicto | EP002-01, EP002-02, EP002-03, EP002-04 (+15) |
| 1.2.4.1.8.2 | Decisión | El puntaje alcanza el umbral: la identidad queda validada | locDicIdentidad, locDicVeredicto | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.8.2.1 | Asignar | Etapa: identidad validada | locDicIdentidad, locDicVeredicto | locDicIdentidad | EP002-01, EP002-02, EP002-03, EP002-04 (+11) |
| 1.2.4.1.8.3 | Decisión | El puntaje no alcanza el umbral o el nombre es incompleto: excepción de negocio 3 | locDicIdentidad, locDicVeredicto | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.8.3.1 | Asignar | Etapa: excepción de negocio 3 | locDicIdentidad, locDicVeredicto | locDicIdentidad | EP002-13, EP002-14, EP002-15, EP003-08 |
| 1.2.4.1.8.4 | Decisión | Escribe el comentario de la excepción de negocio 3 en Gestión → Detalle | locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.8.4.1 | Paso (componente) | Comentario de la excepción de negocio 3 (revisión de Cartera) | glbStrRutaRaiz, locDicCaso, locDicIdentidad, locDicVeredicto | locDicComentarioIdentidad | EP002-13, EP002-14, EP002-15, EP003-08 |
| 1.2.4.1.8.5 | Decisión | El comentario no se pudo registrar: excepción de sistema | locDicComentarioIdentidad, locDicIdentidad | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.8.5.1 | Asignar | Etapa: excepción de sistema (comentario no registrado) | locDicComentarioIdentidad, locDicIdentidad | locDicIdentidad | EP002-15 |
| 1.2.4.1.9 | Grupo | HU006HU007HU008 - Registrar el resultado de identidad | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.9.1 | Decisión | Deja el resultado de identidad en el reporte y los logs | glbArrSiguenIdentidad, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.9.1.1 | Paso (componente) | Registra el resultado de identidad (sin nombres ni identificaciones) | glbStrRutaRaiz, locDicCaso, locDicIdentidad, locStrIdRadicado | locDicEvento | EP002-01, EP002-02, EP002-03, EP002-04 (+22) |
| 1.2.4.1.9.2 | Decisión | Resultado «validada» | glbArrSiguenIdentidad, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.9.2.1 | Asignar | Anota el radicado en identidad validada | glbArrValidadas, locStrIdRadicado | glbArrValidadas | EP002-01, EP002-02, EP002-03, EP002-04 (+11) |
| 1.2.4.1.9.3 | Decisión | Resultado «excepcion_negocio_3» | glbArrSiguenIdentidad, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.9.3.1 | Asignar | Anota el radicado en excepciones de negocio 3 | glbArrExcepcionesNegocioTres, locStrIdRadicado | glbArrExcepcionesNegocioTres | EP002-13, EP002-14, EP003-08 |
| 1.2.4.1.9.4 | Decisión | Resultado «revision_humana» | glbArrSiguenIdentidad, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.9.4.1 | Asignar | Anota el radicado en revisión humana | glbArrRevisionHumana, locStrIdRadicado | glbArrRevisionHumana | EP002-03, EP002-04 |
| 1.2.4.1.9.5 | Decisión | Resultado «sin_nombre» | glbArrSiguenIdentidad, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.9.5.1 | Asignar | Anota el radicado en respuesta sin nombre | glbArrSinNombre, locStrIdRadicado | glbArrSinNombre | EP002-17 |
| 1.2.4.1.9.6 | Decisión | Resultado «gestion_manual» | glbArrSiguenIdentidad, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.9.6.1 | Asignar | Anota el radicado en gestión manual | glbArrGestionManual, locStrIdRadicado | glbArrGestionManual | EP002-16, EP002-18, EP002-20 |
| 1.2.4.1.9.7 | Decisión | Resultado «excepcion_sistema»: el caso va a gestión manual | glbArrSiguenIdentidad, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.9.7.1 | Asignar | Anota el radicado en excepciones de sistema de identidad | glbArrExcepcionesSistemaIdentidad, locStrIdRadicado | glbArrExcepcionesSistemaIdentidad | EP002-06, EP002-07, EP002-08, EP002-09 (+3) |
| 1.2.4.1.9.7.2 | Asignar | Anota el radicado en gestión manual | glbArrGestionManual, locStrIdRadicado | glbArrGestionManual | EP002-06, EP002-07, EP002-08, EP002-09 (+3) |
| 1.2.4.1.9.7.3 | Asignar | Guarda el código de error del radicado | glbDicCodigos, locDicIdentidad, locStrIdRadicado | glbDicCodigos | EP002-06, EP002-07, EP002-08, EP002-09 (+3) |
| 1.2.4.1.10 | Grupo | HU011 - Registrar la exclusión en base centralizada (repositorio local) | — | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.10.1 | Asignar | Resultado del registro de exclusión (vacío al empezar) | — | locDicExclusion | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.10.2 | Decisión | Identidad validada: inserta la exclusión, cruza contra las maestras y elimina el registro de la maestra | glbArrAvanzan, glbDicRepositorio, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.10.2.1 | Paso (componente) | Registra la exclusión (Exclusion + una fila por valor en Celulares/Correos), verifica y elimina de la maestra | glbStrRutaRaiz, locDicCaso, locDicDuplicado | locDicExclusion | EP003-01, EP003-03, EP003-04, EP003-06 (+1) |
| 1.2.4.1.10.3 | Decisión | Exclusión registrada | glbArrAvanzan, glbDicRepositorio, locDicExclusion, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.10.3.1 | Asignar | Anota el radicado en exclusiones registradas | glbArrExclusionRegistrada, locStrIdRadicado | glbArrExclusionRegistrada | EP003-01, EP003-03, EP003-04 |
| 1.2.4.1.10.4 | Decisión | El repositorio falló de forma persistente: excepción de sistema del caso (el bot continúa) | glbArrAvanzan, glbDicRepositorio, locDicExclusion, locDicIdentidad, locStrIdRadicado | — | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.4.1.10.4.1 | Asignar | Anota el radicado en excepciones de sistema de la exclusión | glbArrExcepcionesSistemaExclusion, locStrIdRadicado | glbArrExcepcionesSistemaExclusion | EP003-06, EP003-07 |
| 1.2.4.1.11 | Paso (componente) | Deja constancia del fin del radicado en el log de auditoría | glbStrRutaRaiz, locStrIdRadicado | locDicEvento | E1-01, E1-08, E1-09, E1-10 (+35) |
| 1.2.5 | Decisión | El repositorio está habilitado y la selección terminó bien: deja constancia del fin de la búsqueda y del registro | glbDicEstado, glbDicRepositorio | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.5.1 | Paso (componente) | Deja constancia del fin de la búsqueda de duplicados (EP-003) | glbStrRutaRaiz | locDicEvento | EP003-01, EP003-02, EP003-03, EP003-04 (+5) |
| 1.2.5.2 | Paso (componente) | Deja constancia del inicio del registro de exclusión (EP-003) | glbStrRutaRaiz | locDicEvento | EP003-01, EP003-02, EP003-03, EP003-04 (+5) |
| 1.2.5.3 | Paso (componente) | Deja constancia del fin del registro de exclusión (EP-003) | glbStrRutaRaiz | locDicEvento | EP003-01, EP003-02, EP003-03, EP003-04 (+5) |
| 1.2.6 | Decisión | Ningún caso pudo consultar el repositorio: punto de control crítico, se detiene la ejecución | glbArrAvanzan, glbArrRepositorioCaido, glbDicEstado, glbDicRepositorio | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.6.1 | Asignar | Estado de la ejecución: detenido, repositorio inaccesible para todos los casos | glbDicEstado | glbDicEstado | EP003-05 |
| 1.2.7 | Decisión | La identidad está habilitada y la selección terminó bien: deja constancia de su fin | glbDicEstado, glbDicPortales | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.2.7.1 | Paso (componente) | Deja constancia del fin de la validación de identidad en el log de auditoría | glbStrRutaRaiz | locDicEvento | EP002-01, EP002-02, EP002-03, EP002-04 (+24) |
| 1.2.e.1 | Asignar | Marca fallo de sistema en el proceso principal | — | glbBlnEstadoSistema | **sin cubrir** |
| 1.2.e.2 | Asignar | Estado de la ejecución: detenido por excepción de sistema | glbDicEstado | glbDicEstado | **sin cubrir** |
| 1.3 | Grupo | HU002HU003HU004 - Cierre y registro de ejecución | — | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.3.1 | Decisión | La ejecución se detuvo | glbDicEstado | — | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.3.1.1 | Paso (componente) | Registra la detención en el log de errores y prepara el aviso «Detenido» | glbDicEstado, glbStrRutaRaiz | glbDicDetencion | E1-04, E1-05, E1-06, E1-07 (+2) |
| 1.3.1.2 | Asignar | Asunto del aviso que se enviará al equipo técnico | glbDicDetencion | glbStrAsuntoAviso | E1-04, E1-05, E1-06, E1-07 (+2) |
| 1.3.2 | Paso (componente) | Cierra la ejecución y deja el resumen sin PII (en modo real los datos personales se enmascaran) | glbArrAvanzan, glbArrExcepcionesNegocioUno, glbArrExcepcionesSistema, glbArrIdsDescartados, glbDicDetencion, glbDicEstado, glbDicInicio, glbStrRutaRaiz | glbStrResumen | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.3.3 | Asignar | Observación final de la corrida | glbArrAvanzan, glbArrExcepcionesNegocioUno, glbArrExcepcionesSistema, glbDicEstado, glbDicInicio | glbStrObservaciones | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.3.4 | Asignar | El proceso terminó sin detenerse | glbDicEstado | glbBlnEstadoProceso | E1-01, E1-02, E1-03, E1-04 (+43) |
| 1.e.1 | Asignar | Marca fallo de sistema | — | glbBlnEstadoSistema | **sin cubrir** |
| 1.e.2 | Asignar | Observación de la excepción de sistema | — | glbStrObservaciones | **sin cubrir** |
| 2 | Log | Traza final de la ejecución | glbStrObservaciones | — | E1-01, E1-02, E1-03, E1-04 (+43) |

Escenarios: `E001-NN` = banco EP-001 (`banco/escenarios/EP-001.json`), `EP002-NN` = banco EP-002, `EP003-NN` = banco EP-003.
