## Why

EP-003 evita reprocesar y volver a excluir a quien ya fue gestionado (HU-010, origen de la excepción de negocio 4) y deja constancia estructurada de cada exclusión para un bloqueo efectivo (HU-011). En el lab las bases viven en un repositorio local con datos sintéticos.

## What Changes

- HU-010: antes de la identidad, cada valor de cada canal (correo y teléfono clasificado como celular) se busca por separado en la maestra y en la base de exclusión con llave compuesta (identificación + celular, identificación + correo). Solo el valor duplicado genera la excepción de negocio 4 (nota en Gestión → Detalle y reporte); los demás continúan. El teléfono fijo no tiene base de cruce. Repositorio que no responde: reintenta x3 y excepción de sistema del caso; si ningún caso puede consultarlo, la ejecución se detiene y alerta.
- HU-011: tras la identidad coincidente, inserta `Exclusion` y una fila de 14 columnas por valor en `Celulares`/`Correos` (no duplica un contacto ya presente), cruza cada valor contra la maestra y elimina el registro de la maestra. Una falla persistente al insertar no elimina nada; al eliminar, la fila insertada se conserva y el bot continúa.
- Repositorio local (`Scripts/habeasdata/repositorio.py`): MER de 8 tablas + `Transacciones` (una fila por transición, incluidos los fallos) + `MaestraCelulares`/`MaestraCorreos`; SQLite con el contrato de `specs/repositorio-local.md` (NocoDB queda como camino documentado, mismo contrato).
- HU-009 (Cobra) como stub: gestor, sucursal, ID CLIENTE/CODEUDOR, FUENTE y TIPO USUARIO salen de `Scripts/habeasdata/sinteticos/stub_cobra.json`.
- Robot de Studio: grupos HU010 y HU011 en el bucle por radicado; banco de 9 escenarios.

## Capabilities

### New Capabilities
- `exclusion-repositorio`: búsqueda de duplicados y registro de la exclusión en el repositorio local, con trazabilidad por transición.

### Modified Capabilities
(ninguna)

## Supuestos vetables por Villa

- **Maestras `MaestraCelulares`/`MaestraCorreos` (C-16)**: propuesta del lab, pendiente de visto bueno.
- **Teléfono fijo (HU-011)**: las tablas de canal no tienen columna `FIJO`; un caso con solo fijo deja únicamente la fila de `Exclusion` y queda «Procesado Parcialmente» (5), no «Exitoso».
- **Valores no ubicados en la maestra**: se registran igualmente en la exclusión (los AC piden una fila por valor); no hay nada que eliminar ni verificar. HU-011 §4 dice que en ese caso el bot «no toca el repositorio»: contradicción entre el AC y la nota, **pendiente de decisión de Villa**.
- **Orden de la inserción**: se insertan todas las filas primero y solo después se cruza y se elimina de las maestras (así «insertar falla → no se elimina nada» se cumple también con varios valores).
- **Etapas previas en `Transacciones`**: selección, lectura y completitud se anotan al llegar a HU-010 (no en el instante de cada una).
- **Repositorio**: SQLite en `Documentos/repositorio/lab.sqlite`; NocoDB npm 0.301.3 (D-07) no se instaló en este entorno.

## Impact

- Código: `Scripts/habeasdata/` (`repositorio`, `ep003`, `ep002`, `pasos`), `Robots/`, `Configuracion/`, `banco/`, `tests/`.
- Dependencias: ninguna (biblioteca estándar de Python, `sqlite3`).

## Trazabilidad

- Épica: EP-003 — Registro centralizado y enrutamiento (`docs/03-backlog/epicas.md`).
- Historias: HU-010, HU-011
- Documentos de las HU: `docs/04-historias/`.
- Fuera de esta épica: HU-005 y HU-009 (stubs de Cobra), HU-018 (reintentos y correos, fuera del lab).
