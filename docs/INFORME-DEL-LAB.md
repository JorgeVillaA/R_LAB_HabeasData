# Informe del lab — R_LAB_HabeasData

**Para:** Diana Lorena Páez Rodríguez (líder técnico)
**De:** Villa (construcción agentizada) · **Fecha:** 29/10/2026
**Repo:** `github.com/JorgeVillaA/R_LAB_HabeasData`

## Qué es esto

Un laboratorio que demuestra **cómo se construye un bot RPA con agentes** (flujo Trycore: spec ejecutable → TDD → banco determinista → verificación), sobre una rebanada real del proyecto Habeas Data (CISA). El entregable no es el robot final: es la **evidencia de que el método funciona**.

## Cómo se corre (2 minutos)

```powershell
cd <carpeta del repo>
.\arrancar_lab.ps1            # modo fixture: sin secretos, sin red, corre en cualquier máquina
.\arrancar_lab.ps1 -Modo real # contra la API de QA de CISA (requiere credencial, ver docs/CREDENCIALES.md)
```

El script comprueba prereqs (Python, Node, Rocketbot Studio), levanta los dobles locales y NocoDB, corre la matriz del banco dos veces y deja la evidencia en `banco/evidencia/`. Para ver el flujo del robot: abrir `R_LAB_HabeasData` en Rocketbot Studio (proyecto en `Documents/rocketbot/R_LAB_HabeasData`).

## Qué prueba y qué no

| Prueba | No prueba |
|---|---|
| Construcción agentizada del flujo completo de EP-001 (HU-002/003/004) | La integración de **escritura** en Zeus (endpoint no entregado por CISA) |
| Consumo de la API de Zeus por contrato real (lectura, OData, token) | Cobra (sin endpoints: HU-005 y HU-009 son stubs declarados) |
| Lineamientos Trycore verificados: `validate_robot` 0/0, carpetas, logs de 4 campos, tres JSON | Los portales del Estado reales (Policía/Procuraduría van con dobles; el captcha de terceros no se evade) |
| Determinismo: 16 escenarios × 2 corridas con huella idéntica | El rendimiento ni la operación productiva |

## Métricas del método (lo que hace esto evidencia, no demo)

| Métrica | Valor |
|---|---|
| Tests | 103 en verde (`unittest`) |
| Escenarios del banco | 16, dos corridas idénticas (determinismo probado) |
| `validate_robot` perfil Trycore | 0 errores, 0 avisos |
| Flujo en Studio | Legible a cliente: grupos por HU, decisiones visibles, descripción por bloque (72 bloques, en consolidación) |
| Lineamientos | Logs `LAB0001HDATA00_*` con los 4 campos del anexo, `NO APLICA` en faltantes, escritura en el momento del evento |

## Decisiones y contradicciones

20 contradicciones entre las fuentes (C-01…C-20) documentadas en `docs/00-alcance-del-lab.md` con su resolución y evidencia. Ninguna resuelta en silencio. Las decisiones de alcance y modo son de Villa; CISA solo cuenta como insumo.

## Bloqueos abiertos

1. **`client_secret`** de la API de QA (ver `docs/CREDENCIALES.md`) — sin él, el modo real no corre.
2. **Endpoints de escritura de Zeus** sin entregar por IT CISA (comentario, reasignación, cierre) — HU-004 deja su comentario de excepción como stub declarado.
3. **Cobra sin endpoints** (HU-005, HU-009 fuera del alcance del lab).

## Dónde mirar

- `docs/00-alcance-del-lab.md` — alcance, dobles, contradicciones
- `docs/03-backlog/epicas.md` y `docs/04-historias/` — épicas y 9 HU
- `specs/api-zeus-qa.md` — contrato de la API (del manual de CISA)
- `banco/evidencia/` — evidencia cruda de las corridas
- `Scripts/habeasdata/` — lógica pura (matching, clasificación, E/S con API)
