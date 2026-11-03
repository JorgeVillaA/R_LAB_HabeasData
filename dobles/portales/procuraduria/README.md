# Doble visual — Procuraduría General de la Nación, consulta de antecedentes

Clon local del formulario de consulta de antecedentes para pruebas del bot de
`R_LAB_HabeasData`. Se armó con lo que el portal **sí** entrega hoy: sus hojas de estilo,
sus imágenes y el marcado real del formulario (mismos `name`/`id` de control), más los
pasos que el portal ya no sirve y que se reconstruyeron según HU-007.

## Bloqueos del portal (evidencia, 2026-10-30)

| URL | Respuesta | Evidencia |
|---|---|---|
| `https://apps.procuraduria.gov.co/webcert/consulta-de-antecedentes.aspx` | **302** → `/WEBCERT/Error.aspx?aspxerrorpath=/webcert/consulta-de-antecedentes.aspx` | `HTTP/1.1 302 Found`, `Server: Microsoft-IIS/10.0`, `X-Powered-By: ASP.NET`, `Content-Length: 189`. La página final (12.211 caracteres) dice «Formulario de atención de incidentes» / «Disculpe las molestias, se ha presentado un problema técnico». |
| `https://apps.procuraduria.gov.co/webcert/` | **403** | `403 - Forbidden: Access is denied.` |
| `https://www.procuraduria.gov.co/Pages/consulta-de-antecedentes.aspx` | **200 con bloqueo** | Página del WAF: «The URL you requested has been blocked» / «La página que consulta no se encuentra disponible», `ID Referencia: 20000051`, `ID Mensaje` (cambia en cada petición; p. ej. `037781095779`), `Server: Microsoft-IIS/10.0` + `X-SharePointHealthScore`. |
| Wayback Machine | sin copias utilizables | `web.archive.org/cdx` devuelve `[]` para esa ruta y `archive.org/wayback/available` responde `429 Too Many Requests`. |

Las cabeceras y los textos exactos quedaron guardados en `evidencia/`
(`headers-consulta-de-antecedentes.txt`, `headers-webcert-raiz.txt`, `headers-www-block.txt`,
`www-pagina-bloqueada.txt`, `error-incidentes.txt`).

Consecuencia: del portal real se obtuvieron **CSS, imágenes y el formulario**, pero no la
pantalla de términos, ni el bloque «Datos del ciudadano», ni los textos exactos del captcha.

## Cómo se recorre

```bash
# desde dobles/portales
python -m http.server 8765 --bind 127.0.0.1
# http://127.0.0.1:8765/procuraduria/index.html
```

También funciona con `file://`. Todo el flujo vive en una sola página, como el postback
de ASP.NET: términos → formulario → resultado.

## Flujo y selectores

1. **Términos**: `#rbAcepto` / `#rbNoAcepto` (`name="rblAcepto"`) habilitan
   `#continuarBtn` (arranca `disabled`).
2. **Formulario** (`form#form1`, `action="consulta-de-antecedentes.aspx"`):
   `#txtNombre`, `#ddlTipoID` (`-1`, `1` Cédula de ciudadanía, `2` Nit, `3` Pasaporte,
   `4` Tarjeta de identidad, `5` Cédula extranjeria), `#txtNumID` (`maxlength=15`),
   `#txtCorreoEle`, `#txtObservaciones`, `#lblPregunta`, `#ImageButton1`
   (`src="Media/Image/refresh.png"`, refresca la pregunta), `#txtRespuestaPregunta`,
   `#btnExportar` («Consultar»).
3. **Resultado** en la misma página: `#divDatosCiudadano` → `<h2>Datos del ciudadano</h2>`,
   `#lblNombre` (nombres y luego apellidos) y `#lblEstado`. Los mensajes de error salen en
   `#lblMensaje`.
4. Estado WebForms presente: `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, `__EVENTVALIDATION`,
   `__EVENTTARGET`, `__EVENTARGUMENT`, `__doPostBack`, `WebForm_OnSubmit` y los
   `RequiredFieldValidator`/`CompareValidator`/`CustomValidator` con sus textos.

### Captcha de pregunta

Rota entre las cuatro familias del portal, con la errata conocida:

- aritmética — «¿Cuánto es 7 X 3?»
- capital — «¿Cuál es la capital de Colombia?» / «¿Cuál es la Capital del **Vallle** del Cauca?»
- contextual del documento — «¿Escriba los tres primeros / dos últimos dígitos del documento a consultar?»
- contextual del nombre — «¿Cuál es el primer nombre…?» / «¿Escriba la cantidad de letras…?»

Al fallar se muestra «La respuesta a la pregunta es incorrecta.» y se entrega una pregunta
nueva, como el portal. Ojo: el servicio de captchas del lab (`dobles/portales/captchas.py`)
no resuelve la familia «capital» (`FAMILIA_NO_SOPORTADA`); esos casos van a gestión manual.

### Datos sintéticos

- Tipo `1` (cédula): nombre de patrón fijo y estado según paridad del último dígito
  («presenta» si es impar, «no presenta» si es par).
- Otros tipos: respuesta sin el bloque con el nombre («No se encontró información para el
  documento consultado»), igual que el reborde documentado en HU-007.

## Fidelidad completa

- Hojas de estilo reales del portal: `Media/Style/Certificado.css` y
  `Media/Style/jquery.realperson.css` (aquí `css/`), sin cambios salvo la ruta de las
  imágenes (`../Image/` → `../img/`).
- Imágenes reales: `Media/Image/refresh.png`, `cabezote.jpg` (cabecera del portal),
  `DiscapacidadOn.png`, `DiscapacidadOff.png`.
- Marcado del formulario copiado de la página real: mismas filas, mismos `name`/`id`,
  `class="TextBox"`, `class="ComboBox"`, `class="Botones"`, `celda_fondo_lbl` / `celda_fondo`,
  misma errata «Correo Eletronico:».
- Medición contra la página real servida hoy (`Error.aspx`, que usa el mismo armazón y CSS):
  coinciden fuente, tamaño, colores y geometría de `body`, `divContenedorPGN`,
  `divContenidoPGN` (x=50, ancho 1149), `p.titulo1` (Georgia 18 px negrita `#004891`),
  `input.TextBox` (Arial 13.3 px, borde `2px inset #30608F`), `select.ComboBox` y
  `input.Botones` (120×25, borde `2px solid #30608F`).

## Aproximaciones (y por qué)

- **Pantalla de términos**: no observable (el portal solo sirve la página de incidentes).
  Se reconstruyó con el texto de condiciones, radios `rbAcepto`/`rbNoAcepto` y
  `continuarBtn` — los ids que ya usa el doble del lab.
- **Bloque «Datos del ciudadano»**: no observable. Reconstruido con `h2`, `#lblNombre` y
  `#lblEstado`, según HU-007 y el doble existente.
- **Textos del captcha**: los documentados en HU-007/`captchas.py`; la redacción exacta del
  portal no se pudo verificar.
- **`.divBanner`** con `cabezote.jpg`: el CSS real del portal define esa banda de 80 px; la
  página de incidentes no la pinta, así que el clon la incluye como parte del armazón.
- **Scripts del portal**: `Media/Scripts/jquery.js` y `jquery.realperson.js` devuelven
  **404** en el propio servidor, así que el comportamiento se implementó en `js/clon.js`
  (sin jQuery).
- **Duplicado `Media/Image/refresh.png`**: se conserva esa ruta porque es la que usa el
  `src` original; `img/refresh.png` es la copia que sigue la estructura del clon.
- **Validador de correo**: el portal real lo exige; aquí solo se valida el formato si el
  campo viene diligenciado, para no bloquear el flujo del bot (HU-007 no lo diligencia).

## Nota de uso

Doble de laboratorio con datos sintéticos. No reemplaza al portal: no genera certificados,
no consulta registros reales y el pie de página lo declara.
