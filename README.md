# R_LAB_HabeasData — laboratorio del robot RPA de Habeas Data

Rebanada real del robot `R_HabeasData` (proyecto OP798698, cliente CISA) construida con agentes y verificada de punta a punta en
**modo local aislado**: ningún sistema de CISA, datos 100 % sintéticos. El **entregable es este repositorio**: contiene el robot
de Rocketbot Studio (`studio/R_LAB_HabeasData/robot.db`), el código de apoyo, los dobles locales, el banco de pruebas y la evidencia.

| Épica | Historias | Qué hace el robot |
|---|---|---|
| EP-001 | HU-002, HU-003, HU-004 | Filtra radicados de «Exclusión de Datos» en Zeus (agenda el reintento si la bandeja está vacía), lee los datos del caso y valida los campos obligatorios |
| EP-002 | HU-006, HU-007, HU-008, HU-026a | Valida la identidad en la Policía y la Procuraduría (en Chrome), con captcha de pregunta resuelto por el servicio, y compara nombres (umbral 0.80) |
| EP-003 | HU-010, HU-011 | Busca duplicados en el repositorio local, escribe la excepción de negocio 4 y registra la exclusión (con cruce y baja en las bases maestras) |

## Cómo abrir y correr el robot en Rocketbot Studio
1. Instala/abre Rocketbot Studio (licencia vigente). Copia la carpeta `studio/R_LAB_HabeasData/` dentro de la carpeta de proyectos de
   Studio (en esta máquina: `C:\Users\<usuario>\Documents\rocketbot\`), o apunta Studio a ella.
2. Abre el proyecto `R_LAB_HabeasData` y el robot `LabHabeasData`. El flujo está en **grupos por historia** (HU002, HU003, HU004,
   HU010, HU006, HU007, HU026a, HU008, HU011, cierre) con una descripción por bloque; cada bloque se puede probar solo
   (`docs/SALUD-POR-BLOQUE.md`).
3. Variable `glbStrRutaRaiz`: ruta de la carpeta de este repo (la raíz de ejecución; el robot crea `Logs/`, `Reportes/`, `Documentos/`).
4. Levanta los dobles (otra terminal): `python dobles/zeus_api/servidor.py` (API de Zeus), `python dobles/portales/servidor.py 8766`
   (clones de la Policía y la Procuraduría) y el servicio de captchas (`dobles/portales/captchas.py`). El robot **corre en Chrome**.
5. Ejecuta el robot. Resultado: logs en `Logs/Auditoria` y `Logs/Sistema`, reporte en `Reportes/AAAA/MM`, repositorio en
   `Documentos/repositorio/lab.sqlite`.

## Correr el banco y la suite (sin Studio)
- Todo en uno: `.\arrancar_lab.ps1` (comprueba prerequisitos, corre la suite y la matriz del banco dos veces por épica).
- Suite: `python -m unittest discover -s tests -t .`
- Banco determinista (dos corridas con huellas idénticas): `python banco/correr_matriz.py EP-001|EP-002|EP-003 --corridas 2`
- Equivalencia del robot en **Studio + Chrome** contra el orquestador de referencia (necesita Studio abierto y
  `RPA_AIO_SERVER`/`RPA_AIO_PROYECTO`): `python banco/equivalencia_robot.py EP-001`, `python banco/banco_ep002.py` (EP-002) y
  `python banco/banco_ep002.py EP-003`.
- Validación de lineamientos: `validate_robot` con perfil `trycore` (0 errores, 0 avisos).

## Modo real (opcional, API de QA de CISA)
Por defecto todo corre en `fixture`. El modo `real` exige la credencial `R_LAB_HabeasData/Zeus/QA` en el Administrador de credenciales
de Windows y `ZEUS_REAL_AUTORIZADO=1`; sin ellas se reporta como bloqueo. Ver `docs/CREDENCIALES.md`.

## Qué está simulado y qué no
- Se simulan solo el **captcha de CISA** (clones de portales y servicio de captchas) y la **base de datos** (repositorio local SQLite
  con el MER de 8 tablas + `Transacciones` + `MaestraCelulares`/`MaestraCorreos`; NocoDB queda como camino documentado, mismo contrato).
- El doble de Zeus es fixture del banco: no es evidencia de revisión contra la API real. El endpoint de escritura del comentario es
  un supuesto del lab (C-09).
- Decisiones y alcance: `docs/DECISIONES.md`, `docs/00-alcance-del-lab.md`. Contrato del repositorio: `specs/repositorio-local.md`.

## Pendiente de Villa
`git push` de las ramas (el agente no empuja), decisión sobre el tope diario de reintentos de HU-002 (hoy por ejecución), visto bueno
de las maestras `MaestraCelulares`/`MaestraCorreos` (C-16) y del tratamiento del teléfono fijo en HU-011 (sin columna `FIJO`).
Detalle en `docs/ENTREGA.md`.
