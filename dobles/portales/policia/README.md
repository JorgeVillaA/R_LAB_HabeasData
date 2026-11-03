# Doble visual — Policía Nacional, consulta de antecedentes judiciales

Clon local del front-end de **WebJudicial** para pruebas del bot de `R_LAB_HabeasData`.
Se construyó a partir del HTML, CSS, JS e imágenes **reales** capturados con un navegador
el 2026-10-30 (`https://antecedentes.policia.gov.co:7005/WebJudicial/`).

## Cómo se recorre

```bash
# desde dobles/portales
python -m http.server 8765 --bind 127.0.0.1
# http://127.0.0.1:8765/policia/index.html
```

También funciona abriendo `index.html` con `file://` (todas las rutas son relativas).

| Paso | Archivo | Equivalente real |
|---|---|---|
| Términos de uso | `index.html` | `/WebJudicial/index.xhtml` |
| Formulario y resultado | `antecedentes.html` | `/WebJudicial/antecedentes.xhtml` |

## Flujo y selectores

1. `input[name="aceptaOption"][value="true"]` (ids `aceptaOption:0` / `aceptaOption:1`,
   «No Acepto» viene marcado) → habilita `#continuarBtn` (el botón arranca en
   `disabled` + `ui-state-disabled`, igual que en el portal).
2. `#cedulaTipo` (`cc`, `cx`, `pa`, `dp`), `#cedulaInput`, casilla reCAPTCHA
   (`#recaptchaCheckbox`, token en `#g-recaptcha-response`, control `#recaptchaCheck`).
3. `#j_idt17` («Consultar») → bloque de resultado en la misma página con
   `Apellidos y Nombres:`, `Documento:` y `Resultado:` (`#resultadoAntecedentes`).
4. Estado JSF disponible: `javax.faces.ViewState`, `form` oculto, `formAntecedentes`.

Datos 100 % sintéticos: el nombre sale de un patrón fijo («APELLIDO X NOMBRE Y») y el
resultado depende de la paridad del último dígito del documento. No hay datos de personas.

`?modo=cuota` en la URL reproduce el aviso «Este sitio supera la cuota gratuita de
reCAPTCHA» en lugar del resultado.

## Fidelidad completa

- `index.html` y `antecedentes.html`: markup real copiado del DOM (cabecera, navegación,
  modal «Ley Ángel», panel de términos, panel PrimeFaces del formulario, pie con logos).
- CSS real: `bootstrap.css`, `plugins.css`, `roboto-webfont.css`, `style.css`,
  `responsive.css`, `theme.css` (PrimeFaces Aristo) y `components.css` (PrimeFaces 7.0).
- JS real: jQuery 3.3.1, Bootstrap, Modernizr, `plugins.js`, `main.js`.
- Imágenes reales: `logo_pol.png`, `dijin.png`, `logo.png`, logos de Presidencia,
  MinDefensa, Colombia Compra y GOV.CO, `homebg.jpg` (fondo de cabecera), `bg.png`,
  `preloading.gif`, `favicon.ico`. Fuentes Roboto y FontAwesome.
- Verificación: se midieron posición, tamaño, fuente, color, fondo y borde de 12 bloques
  de cada página en el portal real y en el clon, con la misma ventana (1264×569).
  Resultado: **0 diferencias** y la misma altura de scroll (846 px en términos, 730 px en
  el formulario). Capturas comparadas con `capture_screenshot`.

## Aproximaciones (y por qué)

- **reCAPTCHA v2**: el original es un `iframe` de Google. Aquí es una casilla local con el
  aspecto del widget v2 (logo descargado de `gstatic`) que se marca al hacer clic y escribe
  un token ficticio; no valida contra Google ni escala a reto de imágenes.
- **Ajax JSF**: el `PrimeFaces.ab(...)` de los `onclick` se sustituyó por `js/clon.js`
  (habilitar «Enviar», navegar al formulario, validar y pintar el resultado).
- **Bloque de resultado**: no se pudo capturar del portal real (haría falta resolver un
  reCAPTCHA real). Se reconstruyó con el panel PrimeFaces y los textos documentados
  («Apellidos y Nombres:») en `#resultadoAntecedentes`.
- **ViewState**: valores sintéticos (base64 aleatorio) en lugar de tokens vivos.
- **Enlaces** «Contáctenos» y «Preguntas Frecuentes» apuntan a `#` (no se clonaron).
- **Título**: el portal real sirve `Policía Nacional de Colombia`; el prefijo `🐴` que
  aparecía en la captura era una inyección del navegador usado para extraer, no del sitio.
- Los `url(...)` de las hojas de estilo se reescribieron de `../images/` a `../img/` para
  respetar la estructura de carpetas del clon; el resto del CSS está intacto.

## Nota de uso

Doble de laboratorio. No se consultó el portal con documentos de personas reales y no se
automatiza la evasión del reCAPTCHA: en modo real ese paso lo resuelve una persona.
