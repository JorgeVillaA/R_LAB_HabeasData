# Contrato de la API de Zeus (QA) — `CamposAdicionalesXRadicadoHabeasData`

Fuente: `Manual de Consumo: API Gesfad Campos Adicionales Flujo Habeas Data` v1.1 (septiembre 2026), CISA.
Este archivo es el contrato que el cliente del bot debe implementar. **Nada de secretos aquí**: el `client_secret` vive en el Administrador de credenciales de Windows (lineamiento R-04).

## Entornos

| Entorno | Componente | URL |
|---|---|---|
| **QA (el que usa el lab)** | URL base de la API | `https://qaservices.cisa.gov.co/habeasdata/api/CamposAdicionalesXRadicadoHabeasData` |
| QA | Token (Keycloak, realm `git_cisa`) | `https://qaservices.cisa.gov.co/sso/git_cisa/token` |
| QA | Contrato OpenAPI/Swagger | `https://qaservices.cisa.gov.co/habeasdata/api/openapi` |
| Producción | URL base | `https://services.cisa.gov.co/habeasdata/api/CamposAdicionalesXRadicadoHabeasData` (referencia; **no usar en el lab**) |

## Autenticación (OAuth 2.0 Client Credentials)

- `POST` a la URL SSO con `Content-Type: application/x-www-form-urlencoded`:
  - `grant_type=client_credentials`
  - `client_id=app_dab_habeasdata`
  - `client_secret=<del gestor de credenciales; nunca en código ni en config>`
- Respuesta 200: `access_token`, `expires_in: 300`, `refresh_expires_in: 0`, `token_type: Bearer`.
- **Ciclo de vida:** el token vive 300 s sin refresh token. El cliente pide uno nuevo cuando expire o al recibir **401**; no hay límite de tokens por cliente.
- Toda petición al recurso lleva `Authorization: Bearer <token>`.

## Consultas (OData v4 sobre el endpoint REST)

| Uso | Petición |
|---|---|
| Todos los radicados activos | `GET /api/CamposAdicionalesXRadicadoHabeasData` |
| Un radicado por clave | `GET /api/CamposAdicionalesXRadicadoHabeasData/IDRADICADO/<id>` |
| Solo Exclusión de Datos | `GET ...?$filter=PQRCORRESPONDEA eq 'EXCLUSION DE DATOS'` |
| Filtro compuesto (descarta 'NO APORTA') | `GET ...?$filter=PQRCORRESPONDEA eq 'EXCLUSION DE DATOS' and NOIDENTIFICACIONDELCLIENTE ne 'NO APORTA'` |
| Lote controlado | `GET ...?$first=25&$orderby=IDRADICADO desc` |
| Proyección mínima | `GET ...?$select=IDRADICADO,PQRCORRESPONDEA,NOIDENTIFICACIONDELCLIENTE,NOMBREDELCLIENTE,CORREOELECTRONICOPARAEXCLUSION,TELEFONODECONTACTO` |

El motor implementa OData v4 nativo: `$filter`, `$select`, `$first`, `$orderby` son soportados por el servicio.

## Respuesta

Objeto JSON con la propiedad `value` (array de radicados). Campos que devuelve cada registro (nombres exactos):

`IDRADICADO`, `Alias`, `EstadoActual`, `RadicadoPadre`, `RadicadosHijos`, `TIPOLOGIADEPQR`, `PQRCORRESPONDEA`, `CORREOELECTRONICOPARAEXCLUSION`, `NODECELULARPARAEXCLUSION`, `NOFIJOPARAEXCLUSION`, `TIPODEIDENTIFICACION`, `NOIDENTIFICACIONDELCLIENTE`, `NOMBREDELCLIENTE`, `CANALCONTACTOHABEAS`, `FECHADERECEPCION`, `MUNICIPIOCIUDADYODEPARTAMENTODERESIDENCIA`, `ENTIDADORIGINADORA`, `TELEFONODECONTACTO`, `CIUDADOMUNICIPIODECONTACTO`, `TELEFONOADICIONAL`, `ESCLIENTEREITERATIVO`, `NUMERODETRANSACCIONESRELACIONADAS`, `OBSERVACIONES`, `SEREQUIEREATENCIONPRIORITARIA`, `PRESENTAALGUNTIPODEDISCAPACIDAD`, `INDIQUEELTIPODEDISCAPACIDAD`, `POBLACIONCONDERECHOAATENCIONPREFERENCIAL`, `REQUIEREMARCACIONDEREACLAMOENTRAMITE`, `PETICIONCORRESPONDEAREVISIONBASESCOBRANZA`, `REQUIEREINFORMACIONADICIONALHABEAS`, `MEDIODEENVIORESPUESTAHABEAS`, `NUMERORADICADOSERVICIOCORRESPONDENCIA`, `EVIDENCIASOLICITUDINFORMACION`, `REQUIEREGESTIONDEOTROPROCESO`, `REQUIERECONCEPTOJURIDICO`, `FECHADESOLICITUDDEINFORMACION`, `SEREQUIEREAPROBACIONDATACREDITO`, `REQUIEREINFORMACIONADICIONALPETICIONARIO`, `SERECIBEINFORMACIONDELCLIENTE`, `LAINFORMACIONSEENCUENTRACORRECTA`, `EVIDENCIARECEPCIONINFORMACIONCLIENTE`, `FECHADERECEPCIONINFORMACIONCLIENTE`, `CUALESELCANALDERESPUESTAHABEAS`, `SEINCUMPLIOALGUNREQUISITOPORPARTEDECISA`, `APLICARESERVADEINFORMACIONCOMERCIAL`, `SETRASLADOSOLICITUDPORINEXISTENCIA`, `LASOLICITUDCONTIENEPRESCRIPCION`, `REQUIEREELIMINARMARCARECLAMO`, `RESPUESTAAFAVORDELCLIENTE`, `EVIDENCIADLARESPUESTAENVIADA`, `FECHADEENVIODERESPUESTAHABEAS`.

Ejemplo de registro con **valores sintéticos** (los del manual real traen datos de personas; no copiarlos):

```json
{
  "value": [
    {
      "IDRADICADO": 719031,
      "Alias": "EJEMPLO SINTETICO",
      "EstadoActual": "RADICAR Y ASIGNAR REQUERIMIENTO",
      "RadicadoPadre": null,
      "RadicadosHijos": null,
      "TIPOLOGIADEPQR": "PETICIÓN",
      "PQRCORRESPONDEA": "EXCLUSION DE DATOS",
      "CORREOELECTRONICOPARAEXCLUSION": "persona.ejemplo@example.invalid",
      "NODECELULARPARAEXCLUSION": "3100000000",
      "NOFIJOPARAEXCLUSION": "2000000",
      "TIPODEIDENTIFICACION": "CÉDULA DE CIUDADANIA",
      "NOIDENTIFICACIONDELCLIENTE": "1000000000",
      "NOMBREDELCLIENTE": "NOMBRE SINTETICO EJEMPLO",
      "CANALCONTACTOHABEAS": "CORREO ELECTRÓNICO",
      "FECHADERECEPCION": "21/08/2026",
      "TELEFONODECONTACTO": "3100000000",
      "OBSERVACIONES": null
    }
  ]
}
```

## Códigos de estado

| Código | Significado | Causa | Acción |
|---|---|---|---|
| 200 | OK | Consulta correcta | Procesar `value` |
| 400 | Bad Request | Parámetro OData mal formado (campo inexistente) | Revisar nombres en `$select`/`$filter` |
| 401 | Unauthorized | Token ausente, expirado (>300 s) o firma inválida | Pedir nuevo token al SSO |
| 403 | Forbidden | Token sin roles para la entidad | Revisar permisos del cliente en Keycloak |
| 404 | Not Found | `IDRADICADO` inexistente o URL errada | Validar el número de radicado |

## Alcance del servicio (importante para las HU)

El servicio **solo consulta y extrae** los campos de radicados activos sin gestión finalizada. Las transiciones de estado ("Continuar", registro de preguntas, carga de adjuntos, finalización) corresponden a los endpoints transaccionales del aplicativo central de Zeus, **aún sin entregar**: el cliente de lectura no debe suplirlos ni simularlos como si existieran.

## Cómo lo consume el bot

1. Token con `client_credentials` desde el gestor de credenciales (300 s, renovar en 401).
2. Selección de radicados: `$filter=PQRCORRESPONDEA eq 'EXCLUSION DE DATOS' and NOIDENTIFICACIONDELCLIENTE ne 'NO APORTA'`, con `$first` para lotes y `$orderby=IDRADICADO desc`.
3. Extracción: `$select` con los campos que las HU consumen (identificación, nombre, canales, fecha de recepción, padre/hijo, estado).
4. El resto del flujo (validaciones, matching, registro) opera sobre esos datos, contra los dobles locales.
