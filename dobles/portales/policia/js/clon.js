/* Conducta del clon de WebJudicial (Policía Nacional).
 *
 * Reemplaza el ajax de PrimeFaces/JSF del portal real por lógica local:
 *   - index.html        : habilita «Enviar» sólo al marcar «Acepto» y pasa al formulario.
 *   - antecedentes.html : casilla reCAPTCHA visual (sin Google), validación de campos
 *                         y bloque «Apellidos y Nombres:» en la misma página.
 *
 * Los ids y names son los del portal real: aceptaOption / continuarBtn / cedulaTipo /
 * cedulaInput / g-recaptcha-response / javax.faces.ViewState.
 * Datos 100 % sintéticos: el nombre que devuelve el clon es un marcador de prueba.
 */
(function () {
  "use strict";

  function $(sel, raiz) { return (raiz || document).querySelector(sel); }
  function $$(sel, raiz) { return Array.prototype.slice.call((raiz || document).querySelectorAll(sel)); }

  /* ------------------------------------------------------------------ */
  /* Paso 1 — términos de uso                                            */
  /* ------------------------------------------------------------------ */
  function pasoTérminos() {
    var boton = $("#continuarBtn");
    var radios = $$("input[name='aceptaOption']");
    if (!boton || !radios.length) { return false; }

    function sincronizar() {
      var acepto = $("input[name='aceptaOption'][value='true']");
      var marcado = !!(acepto && acepto.checked);
      boton.disabled = !marcado;
      boton.classList.toggle("ui-state-disabled", !marcado);
      boton.setAttribute("aria-disabled", marcado ? "false" : "true");
    }

    radios.forEach(function (r) { r.addEventListener("change", sincronizar); });
    sincronizar();

    boton.addEventListener("click", function (ev) {
      ev.preventDefault();
      if (boton.disabled) { return; }
      window.location.href = "antecedentes.html";
    });
    return true;
  }

  /* ------------------------------------------------------------------ */
  /* reCAPTCHA v2 visual (casilla)                                       */
  /* ------------------------------------------------------------------ */
  var RETO_IMAGENES = false;

  function montarRecaptcha() {
    var casilla = $("#recaptchaCheckbox");
    if (!casilla) { return; }
    casilla.addEventListener("click", function () {
      if (casilla.getAttribute("aria-checked") === "true") { return; }
      casilla.classList.add("recaptcha-checkbox-loading");
      window.setTimeout(function () {
        casilla.classList.remove("recaptcha-checkbox-loading");
        casilla.setAttribute("aria-checked", "true");
        var respuesta = $("#g-recaptcha-response");
        var control = $("#recaptchaCheck");
        if (respuesta) { respuesta.value = "clon-local-no-verificado"; }
        if (control) { control.checked = true; }
      }, 550);
    });
    casilla.addEventListener("keydown", function (ev) {
      if (ev.key === " " || ev.key === "Enter") { ev.preventDefault(); casilla.click(); }
    });
  }

  /* ------------------------------------------------------------------ */
  /* Mensajes estilo JSF (ui-messages)                                   */
  /* ------------------------------------------------------------------ */
  function mensaje(texto) {
    var contenedor = $("#j_idt10");
    if (!contenedor) { return; }
    contenedor.innerHTML = '<div class="ui-messages-error ui-corner-all" role="alert">' +
      '<span class="ui-messages-error-icon">!</span>' +
      '<ul><li><span class="ui-messages-error-summary">' + texto + "</span></li></ul></div>";
  }

  function limpiarMensajes() {
    var contenedor = $("#j_idt10");
    if (contenedor) { contenedor.innerHTML = ""; }
  }

  /* ------------------------------------------------------------------ */
  /* Paso 2 — formulario de consulta                                     */
  /* ------------------------------------------------------------------ */
  function nombreSintetico(numero) {
    var final = numero.replace(/\D/g, "").slice(-1);
    if (final === "") { return "DEMO PRUEBA CIUDADANO SINTETICO"; }
    var apellidos = ["DEMO", "PRUEBA", "SINTETICO", "MUESTRA", "FICTICIO", "EJEMPLO", "TESTIGO", "LABORATORIO", "PATRON", "ENSAYO"];
    var nombres = ["CIUDADANO", "USUARIO", "PERSONA", "TITULAR", "CONSULTA", "REGISTRO", "DOCUMENTO", "IDENTIDAD", "VERIFICACION", "CONTROL"];
    var i = parseInt(final, 10);
    return "APELLIDO " + apellidos[i] + " NOMBRE " + nombres[i];
  }

  function pasoFormulario() {
    var boton = $("#j_idt17");
    var tipo = $("#cedulaTipo");
    var numero = $("#cedulaInput");
    if (!boton || !numero) { return false; }

    boton.addEventListener("click", function (ev) {
      ev.preventDefault();
      limpiarMensajes();
      $("#resultadoAntecedentes").style.display = "none";

      var valor = (numero.value || "").replace(/\s/g, "");
      if (!valor) {
        mensaje("Número de documento: Valor requerido.");
        numero.focus();
        return;
      }
      if ((tipo.value === "cc" || tipo.value === "cx") && !/^\d+$/.test(valor)) {
        mensaje("Número de documento: Valor no válido.");
        numero.focus();
        return;
      }
      var respuesta = $("#g-recaptcha-response");
      if (!respuesta || !respuesta.value) {
        mensaje("Debe verificar que no es un robot.");
        return;
      }
      if (/modo=cuota/.test(window.location.search)) {
        mensaje("Este sitio supera la cuota gratuita de reCAPTCHA. Intente más tarde.");
        return;
      }

      var nombre = nombreSintetico(valor);
      var registra = parseInt(valor.slice(-1), 10) % 2 === 1;
      $("#lblNombre").textContent = nombre;
      $("#lblDocumento").textContent = "C.C. " + valor;
      $("#lblResultado").textContent = registra
        ? "El documento presenta antecedentes judiciales."
        : "El documento no registra antecedentes judiciales.";
      $("#lblDetalle").textContent = registra
        ? "Registro sintético de prueba (Ley 2455 / datos de laboratorio)."
        : "";
      $("#resultadoAntecedentes").style.display = "block";
    });
    return true;
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (pasoTérminos()) { return; }
    montarRecaptcha();
    pasoFormulario();
  });
})();
