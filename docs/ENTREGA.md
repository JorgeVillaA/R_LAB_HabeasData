# Entrega del lab R_LAB_HabeasData (2026-11-01)

Producto: este repositorio, con el robot de Rocketbot Studio **dentro** (`studio/R_LAB_HabeasData/robot.db`) y todo lo necesario para
abrirlo, correrlo y verificarlo. Instrucciones de uso: `README.md`.

## Estado por épica
| Épica | Rama | Código y pruebas | Studio + Chrome | Verificación adversarial | Cierre |
|---|---|---|---|---|---|
| EP-001 (HU-002/003/004) | `feature/EP-001` | banco 18 × 2 | 18/18 IGUAL | CERRABLE (ronda 7, ver `banco/evidencia/EP-001/`) | mergeada (PR #1) |
| EP-002 (HU-006/007/008/026a) | `feature/EP-002` | banco 25 × 2 | 24/24 IGUAL + 1 omitido(s) (solo orquestador o solo intérprete) | ver `docs/PR/EP-002.md` | mergeada (PR #2, incluye EP-003) |
| EP-003 (HU-010/011) | `feature/EP-002` | banco 16 × 2 | 15/15 IGUAL + 1 omitido(s) (solo orquestador o solo intérprete) | ver `docs/PR/EP-003.md` | change `ep-003-exclusion-en-repositorio` listo para archivar |

Suite completa: `python -m unittest discover -s tests -t .` → **306 tests OK** en el commit `51c6bd1` (2026-11-03T11:53:31-0500). `validate_robot` perfil trycore: 0 errores, 0 avisos (el robot no cambió desde `fc7ca76`).
Mapa de salud por bloque (`docs/SALUD-POR-BLOQUE.md`): 8 bloques sin escenario (ramas de error que ningún escenario provoca), reportados, no ocultos.

## Histórico: qué se corrigió en una ronda anterior para que el robot funcione en Chrome REAL
*(Narración de una ronda anterior: las cifras de este apartado no salen de un artefacto con procedencia y no son la evidencia vigente; la vigente está en «Verificación con procedencia».)*
La evidencia anterior de EP-002 («20/20 en Studio») no ejercitaba la identidad (`equivalencia_robot.py` la deja deshabilitada). La prueba real
(`banco/banco_ep002.py`) daba 4/20. Causas y arreglos (todos en `dobles/portales/servidor.py`, sin tocar el HTML de los clones):
`onsubmit` de la Procuraduría llamaba a una función no servida; los recursos inexistentes reiniciaban la sesión del portal; `ui-state-disabled`
anulaba el clic de «Continuar»; el panel de texto de la Policía tapaba el radio; el bloque de resultado de la Procuraduría existía vacío y el robot
leía la página anterior. Una de las 20 pruebas falló una vez (corrida 1 = 19/20) y no se reprodujo (corrida 2 = 20/20 y la corrida de cierre 20/20).

## Qué NO se verificó / límites
- Todo contra dobles y clones locales. La API real de QA de CISA, Cobra y los portales reales no se tocaron. El endpoint de escritura del comentario es un supuesto (C-09).
- El repositorio es SQLite con el contrato de `specs/repositorio-local.md`; **NocoDB npm 0.301.3 (D-07) no se instaló** (queda como camino documentado).
- La descripción del robot en Studio se actualizó (mención a EP-003) después de las corridas de Studio; el flujo es idéntico.
- `Transacciones`: cada etapa se escribe en su instante (corregido tras la auditoría, D-24). `Gestores` toma gestor y agencia del stub de Cobra; `AuditoriaMaestras` es una tabla propuesta (D-25).
- Una verificación adversarial independiente de EP-002 y EP-003 devolvió NO CERRABLE en su primera ronda (reintentos del robot ante portal caído, modo real sin prueba, umbral y comentario sin prueba de punta a punta, orden de inserción/eliminación de HU-011, fila de `Exclusion` con solo fijo). Todo eso se corrigió y se repitió la verificación (ver el hilo de la sesión).
- El tope diario de reintentos de HU-002 se cuenta por ejecución y la espera bloquea el robot (3 × 60 min por defecto).
- Un escenario de EP-003 (detención crítica por repositorio inaccesible) solo se compara en decisiones: la línea final del log difiere entre robot y orquestador.

## Pendiente de Villa
1. Las PR #1 (EP-001) y #2 (EP-002, que incluye EP-003) ya están mergeadas en `main`. El agente no empuja.
2. Decidir: tope diario de reintentos (por día o por ejecución), maestras `MaestraCelulares`/`MaestraCorreos` (C-16), teléfono fijo en HU-011 (hoy: solo la fila de `Exclusion`, «Procesado Parcialmente»), valores no ubicados en la maestra (el AC pide registrarlos, la nota de HU-011 §4 dice que el bot no toca el repositorio), PEP en HU-006 (la Procuraduría no lo trae: hoy gestión manual), instalar NocoDB o aceptar SQLite.
3. Revisar la evidencia visual en Chrome (capturas en `banco/evidencia/`).

## Verificación con procedencia (tercera ronda de la auditoría adversarial)
La auditoría tumbó la entrega anterior porque los artefactos no respaldaban lo afirmado (una «corrida limpia» con el esquema anterior a `0af7388`). Desde D-35 **un artefacto sin procedencia no es evidencia**: cada JSON de abajo lleva commit, fecha y hora, comando y hash del robot, y `cambios_sin_commit` vacío (se corrió con el árbol limpio). Commit de la evidencia: `51c6bd1`. Las cifras de rondas anteriores que no salían de ningún artefacto se retiraron de este documento.

| Qué | Resultado | Artefacto (procedencia dentro) |
|---|---|---|
| Suite completa | 306 tests OK | `2026-11-03T11:53:31-0500`, commit `51c6bd1` (salida de `python -m unittest discover -s tests -t .`) |
| Bancos deterministas, dos corridas con huellas idénticas | EP-001 18/18, EP-002 25/25, EP-003 16/16 | `banco/resultados/EP-00N_corrida1.json` y `_corrida2.json` |
| Robot en Studio con Chrome = orquestador | EP-001 18/18, EP-002 24/24, EP-003 15/15 | `banco/resultados/EP-00N_equivalencia_robot.json` (comandos: `python banco/equivalencia_robot.py EP-001`, `python banco/banco_ep002.py EP-002`, `python banco/banco_ep002.py EP-003`; variables `ZEUS_DOBLE_CLIENT_ID=lab-doble`, `ZEUS_DOBLE_CLIENT_SECRET=lab-secreto-sintetico`) |
| Corrida limpia desde base nueva, dos veces sobre la misma base, con el robot por el intérprete | ver detalle abajo | `banco/evidencia/corrida-limpia/CORRIDA-LIMPIA.json` (`python banco/corrida_limpia.py`, 2026-11-03T11:32:22-05:00) |

**Corrida limpia** (escenario `EP003-12-corrida-completa-trazabilidad`, 15 radicados sintéticos; la base `lab.sqlite` no se versiona, D-33, y se comprobó EN ella):
- Esquema: las siete tablas por corrida traen `IdCorrida`; `LogEjecucion` trae `Pasos` y `ComandosStudio`. El archivo se pudo mover al terminar cada corrida.
- `LogEjecucion` (corrida 1 / corrida 2, ids `C20261103113222` y `C20261103113224`): casos procesados 14 / 14, descartados 1 / 1, exitosos 7 / 0, no exitosos 4 / 12, parciales 3 / 2, excepciones 5 / 12, pasos del producto 413 / 307. `ComandosStudio` queda vacío porque esta corrida no pasó por Studio (lo anota el ejecutor).
- `Parametros`: 73 filas = las 72 hojas de los tres JSON de configuración más la raíz efectiva; faltan 0.
- Reporte: columna `IdCorrida` en todas las filas (38 filas de la corrida 1, 29 de la 2), cada una cerrada con `FIN DE CORRIDA`. Log de auditoría: 102 y 70 filas con prefijo `[IdCorrida]`, todas de 4 campos.
- La segunda corrida sobre la misma base no mezcla: las filas de la corrida 1 quedaron idénticas tras la 2 (`Gestores` 4, `Exclusion` 10, `Excepciones` 5, `Transacciones` 75); la 2 dejó las suyas (`Gestores` 12, `Exclusion` 2) y no hay filas sin id de corrida.
- Las cifras que cita la auditoría (13 excepciones, reporte de 53 filas) salen de la base de la auditoría, que no se versiona; aquí no se usan como evidencia.

## Qué corrigió cada ronda
- **Segunda ronda** (D-29 a D-32): conexión a `lab.sqlite` cerrada al terminar, `LogEjecucion` con id de corrida y pasos, `Parametros` con toda la configuración, reporte y logs separables por corrida.
- **D-28 resuelta (2026-11-03):** el celular y el fijo de exclusión son canal de contacto (evidencia documental de CISA en `docs/DECISIONES.md`); 900015 supera la completitud y registra su celular.
- **Tercera ronda** (D-35 a D-38): una fila por radicado y por corrida en `Gestores` y `Exclusion` (y `IdCorrida` en las demás tablas por corrida, con consulta `resumen_de_corrida`); coordinador y correo de `Gestores` desde el stub de Cobra; `Pasos` lo escribe el producto; `Descartados` aparte de los casos procesados (900011); procedencia en los artefactos.

## Límites que se mantienen
- **Un kill forzado de `rocketbot.exe` sigue dejando `lab.sqlite` bloqueado:** el cierre cubre el fin de la corrida y los fallos de Python, no la muerte del proceso.
- La corrida limpia usa el robot por el intérprete con navegador emulado, no Studio; en Studio el archivo también quedó movible (el banco lo comprueba tras cada escenario con repositorio) pero `LogEjecucion` de esas corridas no se conserva en un artefacto.
- Los coordinadores y correos de `Gestores`, el gestor y la agencia son sintéticos (stub de Cobra, D-37).
- No se repitió la verificación adversarial independiente sobre estos commits.
- Pendientes de Villa: D-31 (valor del «SLA» del spec), D-34 (regla «sin correo»), D-37 (fuente real del coordinador) y las columnas propuestas de D-30 y D-32.
