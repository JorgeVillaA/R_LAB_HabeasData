# Repositorio local del lab — tablas y contrato

El repositorio es local (NocoDB npm 0.301.3 en loopback, SQLite interno; SQLite puro como fallback con el mismo contrato). Datos **100 % sintéticos**. Este contrato es el que consumen HU-010 y HU-011.

## Tablas (MER del diseño técnico §4.6 + la adición del 29/10)

| Tabla | Qué guarda | Relación |
|---|---|---|
| `Insumo` | Cada radicado extraído de Zeus (documento, nombres, contacto) y su estado de ejecución | 1:N con Excepciones, 1:1 con Exclusion |
| `Excepciones` | Las 4 excepciones de negocio (datos incompletos, deudor activo, identidad no coincidente, duplicado) y las de sistema, por radicado. Columnas: `RadicadoZeus`, `TipoExcepcion` (1, 3, 4, sistema, gestion_manual), `Detalle`, `FechaHora` | N:1 con Insumo |
| `Exclusion` | Base centralizada de exclusiones efectivas (documento, correo, celular, fecha) | 1:N con Celulares/Correos |
| `Celulares` | Base de bloqueo de celulares vinculada a cada exclusión | N:1 con Exclusion |
| `Correos` | Base de bloqueo de correos vinculada a cada exclusión | N:1 con Exclusion |
| `Gestores` | Relación gestor → agencia → coordinador → correo, para enrutamiento. Una fila por caso derivado a gestión manual (gestor y agencia del stub de Cobra; «SIN ASIGNAR» si no hay dato) | N:1 con Insumo |
| `Parametros` | Parámetros operativos configurables (ventana, umbral, SLA, rutas): **todas** las hojas de los tres JSON de configuración con su valor vigente en la corrida (`Clave` con puntos, `Maquina.` para la configuración de máquina) y la raíz efectiva; sin secretos. El SLA no tiene valor definido en ninguna fuente (D-31) | — |
| `LogEjecucion` | Consolidado por corrida: fecha, casos procesados, exitosos, no exitosos, parciales, excepciones, duración en segundos, `IdCorrida` (el mismo que lleva el reporte y los logs), `PasosModulo` (pasos de `pasos.py`) y `Pasos` (comandos de Studio, anotados por el ejecutor) | — |
| `AuditoriaMaestras` *(tabla ligera, propuesta)* | Fila completa que se borró de `MaestraCelulares`/`MaestraCorreos`, su radicado y la hora: la corrida es reconstruible | N:1 con Insumo |
| **`Transacciones`** *(adición del 29/10, decisión de Villa)* | **Una fila por cada paso de cada caso: el recorrido completo** | N:1 con Insumo |

## Tabla `Transacciones` (estado en cada parte del proceso)

| Columna | Contenido |
|---|---|
| `IdTransaccion` | Consecutivo |
| `RadicadoZeus` | Caso al que pertenece |
| `Etapa` | Paso del flujo (selección, lectura, validación de campos, consulta Cobra, consulta identidad, duplicados, registro, cierre…) |
| `EstadoAnterior` | Estado antes de la transición (vacío en la primera) |
| `EstadoNuevo` | Estado resultante (1 Sin Procesar, 2 Procesando, 3 Exitoso, 4 No Exitoso, 5 Procesado Parcialmente — lineamiento §17) |
| `FechaHora` | Momento de la transición (no de la carga) |
| `Resultado` | ok / fallo |
| `Motivo` | Qué ocurrió, en lenguaje de soporte; `NO APLICA` si no aplica |

**Regla dura:** se escribe en **cada transición con información, en el instante en que ocurre, incluidos los fallos** (nunca un marcador de inicio vacío). `Resultado` es `fallo` siempre que `EstadoNuevo` = 4 y `ok` en los demás. Al terminar la corrida ningún caso queda en estado 1 o 2. Un error de login, de red o de API deja su fila con `Resultado=fallo` y el motivo. Ninguna tabla conserva observaciones de corridas anteriores sin que la fila de la transición actual esté primero (lección de Medidas Cautelares: el fallo no escribía estado y la base quedaba con datos viejos).

**Consultas que debe soportar** (para revisión/auditoría):
- ¿En qué etapa se quedó cada caso de hoy?
- ¿Cuántos casos hay en cada estado?
- ¿Qué transiciones fallaron y por qué?
- Recorrido completo de un radicado (todas sus transacciones en orden).

## Una corrida, un identificador (D-29, D-32)

Cada corrida tiene un `IdCorrida` (`Cyyyymmddhhmmss`) que escriben el reporte de gestión (columna final), los logs (`[IdCorrida] ` al inicio de la observación) y `LogEjecucion`. El reporte cierra cada corrida con `FIN DE CORRIDA` o `CORRIDA DETENIDA`; una corrida que murió sin cerrar queda marcada `CORRIDA INTERRUMPIDA` por la siguiente del día. Al terminar, el robot cierra la conexión del repositorio: el archivo `.sqlite` queda libre para moverse o respaldarse.

## Bases maestras para el cruce (HU-010 / HU-011)

Además de las tablas del MER, el lab usa dos **bases maestras** con datos sintéticos (propuesta C-16, pendiente de visto bueno de Villa):

| Base | Columnas | Uso |
|---|---|---|
| `MaestraCelulares` | 14 columnas: `ID CLIENTE`, `ID CODEUDOR`, `TIPO USUARIO`, `IDENTIFICACION`, `NOMBRE`, `CELULAR`, `FUENTE`, `FECHA CONSULTA`, `ZEUS`, `FECHA EXCLUSION`, … | Cruce de duplicados (HU-010) y verificación de bloqueo (HU-011) |
| `MaestraCorreos` | 14 columnas (mismo patrón, con `CORREO` en lugar de `CELULAR`) | Ídem |

Las bases de bloqueo `Celulares`/`Correos` del MER se alimentan de la exclusión; las maestras son el universo contra el que se cruza. Ninguna trae columna `FIJO` (sesión 26/10, Tema 10).
