# Credenciales para correr el lab (para el revisor)

> **Nunca se guardan credenciales en este repo, en los JSON, en los logs ni en la evidencia** (lineamiento Trycore R-04/R-11). Esta nota solo dice dónde conseguirlas y cómo configurarlas.

## Qué se necesita

Para correr el lab contra la **API real de Zeus (QA)** hace falta un solo secreto: el `client_secret` de Keycloak (`client_id: app_dab_habeasdata`).

| Dónde está | Detalle |
|---|---|
| **Canal correcto** | Pedirlo a **Daniel Garavito** (arquitecto CISA) o **Amelia Escobar** (PM CISA) por canal seguro. CISA lo rotó el 07/10/2026 y lo entrega por enlace de un solo uso |
| **Correo de referencia** | Hilo «Habeas Data — Requerimientos técnicos de integración con el API de Zeus», 07/10/2026 (`Respuestas API ZEUS  20261007.pdf` en el paquete del proyecto) |
| **Dónde NO está** | El `MANUAL_CONSUMO_HABEAS_DATA.pdf` solo trae el placeholder `<CLIENT_SECRET>`; el secreto anterior (manuales del 21/09 y 28/09) **ya fue rotado** y no sirve |

## Cómo configurarlo (Administrador de credenciales de Windows)

1. Abrir el Administrador de credenciales de Windows → **Credenciales de Windows** → **Agregar credencial genérica**.
2. Dirección de red: `R_LAB_HabeasData/Zeus/QA`
3. Usuario: `app_dab_habeasdata`
4. Contraseña: el `client_secret` recibido por canal seguro.

El robot lee la credencial de ahí; si no existe, falla con un `ErrorBloqueo` explícito y **no hace ninguna llamada**. Es decir: sin secreto, el lab corre completo en modo fixture y no rompe nada.

## Requisitos adicionales para el modo real

- **Red**: acceso HTTPS a `qaservices.cisa.gov.co` (el token se pide a `/sso/git_cisa/token`).
- **Autorización**: declarar `ZEUS_REAL_AUTORIZADO=1` (variable de entorno o config) solo cuando CISA haya autorizado el uso de QA desde la máquina.
- **PII**: la API devuelve radicados reales con datos de ciudadanos. Toda evidencia que salga de una corrida en modo real debe estar redactada; el modo fixture (por defecto) no tiene este problema.

## Modos de corrida

| Modo | Necesita | Para qué sirve |
|---|---|---|
| **fixture** (por defecto) | nada externo | Corre el banco determinista completo, sin red ni secretos. Es el modo de revisión |
| **real** | secreto + red + autorización | Contra la API de QA de CISA. Misma lógica, distinta implementación de la interfaz |
