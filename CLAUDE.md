# CLAUDE.md

<!-- BEGIN trycore-build-harness v0.20.0 -->
## Arnés de construcción (Trycore Build Harness)

Este proyecto usa el arnés `@trycore-co/spec-build-harness` para **construir** sobre la discovery
(compañero de `@trycore/spec-product-flow`: Discovery → Construcción). Modelo de **dos loops**:

```
Inner loop (por épica EP-XXX):  DoR → OpenSpec change → TDD → journey-smoke → api/data → verificación adversarial → DoD → PR + archive
Outer loop (por release):       Release Gate (seguridad · diseño · UX · coherencia triple · arquitectura · integración)
```

- **Unidad de construcción**: la épica (`EP-XXX`). Un slice = una épica = un OpenSpec change = una rama = un PR.
- **Una sola fuente de verdad**: `.claude/state/build-state.json` (schema + protocolo en `.claude/state/README.md`).
- **Skills**: `building-a-slice` (inner loop), `releasing-a-version` (outer loop), `building-a-micro-change` (carril de mantenimiento, dos modos: `/build:bugfix` y `/build:microwork`), `openspec-*` (ciclo de changes).
- **Agentes** en `.claude/agents/build/`; **comandos** `/build:*` + `/opsx:*`; gates automatizados por **hooks** en `.claude/hooks/build/`.

### Slash commands

| Comando | Propósito |
|---|---|
| `/build:work` | Router (classify-and-act): enruta el trabajo a micro-change / slice / release |
| `/build:bugfix` | Bug: ancla al AC, reproduce ejecutando, arregla, re-ejecuta, test validado por reversión |
| `/build:microwork` | Mantenimiento sin bug (copy, config, docs, infra): cambio → verificar → test solo si cambia comportamiento → PR |
| `/build:slice` | Abre/continúa un slice (épica `EP-XXX`) — entrada del inner loop |
| `/build:release` | Corre el Release Gate (outer loop) sobre el diff acumulado de la release |
| `/build:onboard` | Parametriza el dominio del arnés (rellena el bloque de dominio de abajo) y escribe memoria |
| `/build:reflect` | Reflexión post-slice: propone aprendizajes a `CLAUDE.md` (solo con tu aprobación) |
| `/opsx:explore` `/opsx:new` `/opsx:continue` `/opsx:apply` | Ciclo OpenSpec: explorar → crear change → artefactos → implementar |
| `/opsx:verify` `/opsx:archive` `/opsx:sync` `/opsx:ff` `/opsx:bulk-archive` | Verificar, archivar, sincronizar specs |

### Reglas duras (no negociables)

1. **GitHub Flow estricto**: `main` siempre desplegable; integración solo por PR (el hook `gitflow-guard.sh` bloquea commit/push directo a `main`).
2. El enlace change↔épica va en el bloque `## Trazabilidad` del `proposal.md`, **nunca** en frontmatter YAML (rompe `openspec validate`).
3. Las dependencias se vigilan contra `.claude/config/stack-allowlist.json` (hook `stack-guard.sh`), derivado de la sección de requisitos técnicos del PRD.
4. Las revisiones pesadas (seguridad/diseño/UX/coherencia triple/arquitectura/integración) corren **una vez por release** (outer loop), no por épica.
5. **Producto completo, no MVP.** El alcance acordado se construye **entero**. **Recortar o diferir es bloqueante explícito** que requiere acuerdo del equipo — **nunca** una decisión del modelo. No se "deja para después" ni se deriva en lo complejo. La verificación es **ejecutada, no por inspección** (correr la suite, cargar la página, leer la consola).
6. **Cierre verificado, no declarado.** `dod` exige el gate `wiring_verified`: un subagente **adversarial independiente** (`wiring-adversarial-verifier`, contexto virgen) intenta refutar el slice (stubs, rutas sin cablear, AC sin test) antes de cerrar. El estado del cableado vive en disco (`wiring_checklist[]` + `progress_log[]`) para que una sesión fresca retome sin "creer que ya está".
7. **Fidelidad por verificación visual real.** Para slices con UI, el gate `fidelity` solo cierra observando la salida real vía MCP de devtools de navegador (screenshot app vs prototipo); sin verificación visual queda `false` (no "INCONCLUSO pasa").
8. **Cimiento antes que negocio y unidades pequeñas.** Las épicas de cimiento (auth, datos, arquitectura base, design-system) se construyen antes que las de negocio; una épica grande (>3 HU ó ≥3 capas) se descompone en sub-slices construidos de a uno. En proyectos **nuevos** (`project_kind: greenfield`), la **épica caparazón** (app shell: navegación, layout, homepage, login, redirecciones — gate de proyecto `foundation`) se construye y archiva **con evidencia** antes que cualquier épica de negocio; en brownfield el mecanismo es N/A.
9. Si una regla del arnés contradice la metodología Trycore (`METODOLOGIA.md`), **gana la metodología**.

### Ámbito de las reglas de evidencia

- Las reglas pesadas — **mutación obligatoria, evidencia anclada a sha, regresión con
  worktree/baseline** — aplican al **inner loop de slices** (fase tdd→dod de `building-a-slice`),
  **no** al carril `building-a-micro-change`: allí la única mutación es la reversión del fix (modo
  bugfix) y ninguna en microwork sin cambio de comportamiento; suite del módulo tocado en verde
  (las señales de escalada — forma → slice, requisito → discovery — quedan intactas).
- **Presupuesto de mutación**: obligatoria solo para los tests que sostienen un item de
  `wiring_checklist[]` (AC de HU, puntos de integración); opcional para tests auxiliares.
  Alternativa al ciclo manual: mutación automatizada acotada a los ficheros cambiados, con el
  reporte como evidencia.
- **Dos clases de evidencia**: la **determinista** (runners sin LLM) se re-ancla a HEAD; la **viva**
  (corridas contra el LLM real del proyecto) se ancla al último commit que tocó el módulo medido
  (`anchored_at.sha`; `head_at_run` informativo) y solo se regenera cuando cambió el código que mide.
  Detalle operativo: `.claude/skills/building-a-slice/references/evidence-budget.md`.

### Autonomía y puntos de parada

**Continúa sin preguntar** cuando el siguiente paso es el que calcula `slice-ops.sh next-step`, o
cuando la clasificación del carril es clara. Pon las notas de estado en el mismo mensaje que la
siguiente acción, no en un mensaje aparte.

**Para y pregunta** solo ante: (a) cualquier acción irreversible — push forzado, `reset --hard`,
borrado de datos, migración destructiva, escritura fuera del repositorio; (b) recortar o diferir
alcance, que es la regla dura de producto completo y nunca es decisión del modelo; (c) los cuatro carve-outs sobre
documentos de discovery.

**Ningún gate se salta.** Esta sección regula cuándo interrumpir a una persona, no qué verificar.

**Paradas propias del proyecto:** añádelas en el bloque de convenciones de este mismo fichero, no
aquí. Esta sección se reescribe entera en cada actualización del arnés; aquel bloque sobrevive.

### Cómo reportar (gana sobre cualquier otro formato de cierre)

Escribe para alguien que **no tiene tu contexto de sesión**.

**Si no hay decisión que tomar, nada quedó sin verificar y la tarea fue corta:** dos líneas y
«No necesito nada de ti». No uses el formato largo.

**En cualquier otro caso, en este orden:**

1. **Lo que necesito de ti.** La decisión como pregunta, con 2-3 opciones, el coste de cada una y
   tu recomendación. Si no hay decisión pero sí un riesgo, ponlo aquí.
2. **Resumen.** Una o dos frases: qué se hizo y si salió bien o mal.
3. **Qué significa.** El impacto para el producto o la persona usuaria, sin jerga interna.
4. **Riesgo ahora mismo.** Sí o no, y por qué. ¿Hay algo roto o expuesto en este momento?
5. **Qué cambió en disco.** Ficheros tocados, si se commiteó, y **cómo se deshace**. Obligatorio
   siempre que hubo escritura.
6. **Pendiente o no verificado.** Lo que no se probó, y lo que se probó **solo contra dobles,
   mocks o fixtures**. Nunca lo escondas: aquí la ausencia de evidencia no es evidencia de que
   no haya problemas.

**Reglas de escritura.** Un término interno (gate, slice, DoR, arnés, caparazón) se explica en
media frase **la primera vez en la conversación**, no en cada mensaje. Cada número dice qué
significa. El detalle técnico (rutas, sha, cifras de corrida) va al final y ocupa como mucho tres
líneas; si hace falta más, va a un fichero y aquí solo la ruta.

### Bloque de dominio (lo resuelve `/build:onboard`)

Estos puntos de extensión los leen los agentes `security-reviewer`, `stack-guardian`,
`data-consistency-checker`, `ux-krug-reviewer`, `simple-design-reviewer` y `ux-fidelity-reviewer`:

- **PRD técnico (fuente del stack)**: {{PRD_TECH_PATH}}
- **Capa de servicios externos / IA (frontera)**: {{EXTERNAL_SERVICE_LAYER}}
- **Lógica que debe ser determinista (no-IA)**: {{DETERMINISTIC_LAYER}}
- **Categorías de datos sensibles / PII reguladas**: {{SENSITIVE_DATA_CATEGORIES}}
- **Secretos server-side**: {{SERVER_SIDE_SECRETS}}
- **Decisiones de alto impacto que exigen explicabilidad UX**: {{HIGH_STAKES_DECISIONS}}
- **Fuente de diseño / referencia visual**: {{DESIGN_SOURCE}} (si no existe fuente aún, `/build:prototype` puede generarla en `docs/05-prototipo/`; la confirmación sigue siendo humana)

(Si aparecen como `{{...}}`, ejecuta `/build:onboard` para parametrizarlos.)

### Requisitos

- `openspec` CLI instalado (`npm i -g @fission-ai/openspec`) — lo usan `/opsx:*` y las skills `openspec-*`.
- `python3` y `git` disponibles — los usan los hooks de `.claude/hooks/build/`.
- Verifica con `trycore-build doctor`.

<!-- END trycore-build-harness -->

<!-- BEGIN trycore-build-learnings -->
## Convenciones aprendidas (mantenido por /build:reflect)

<!-- /build:reflect propone aquí viñetas concretas (convención nueva o error recurrente) tras cerrar un slice; se agregan SOLO con tu aprobación. Revísalas en PR como cualquier cambio de equipo. -->
<!-- END trycore-build-learnings -->

<!-- A partir de aquí, el equipo del proyecto puede agregar instrucciones específicas del cliente. -->
