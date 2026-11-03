/* Conducta del clon de la Procuraduría (consulta de antecedentes, ASP.NET WebForms).
 *
 * Reemplaza los postbacks del portal real por lógica local:
 *   paso 1  términos  → rbAcepto / continuarBtn
 *   paso 2  consulta  → txtNombre, ddlTipoID, txtNumID, txtCorreoEle, txtObservaciones,
 *                       lblPregunta + ImageButton1 (refresco) + txtRespuestaPregunta,
 *                       btnExportar
 *   paso 3  resultado → bloque «Datos del ciudadano» (lblNombre / lblEstado) en la misma página
 *
 * La pregunta del captcha rota entre las cuatro familias del portal real (aritmética,
 * capital de Colombia, contextual del documento, contextual del nombre) y conserva la
 * errata conocida «Capital del Vallle del Cauca». Datos 100 % sintéticos.
 */
(function () {
  "use strict";

  function $(id) { return document.getElementById(id); }

  function sinTildes(texto) {
    return (texto || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
  }

  /* ---------------------------------------------------------------- */
  /* Captcha de pregunta                                              */
  /* ---------------------------------------------------------------- */
  var FAMILIAS = ["aritmetica", "capital", "documento", "nombre"];
  var preguntaActual = null;

  function nuevaPregunta(indice) {
    var familia = FAMILIAS[indice % FAMILIAS.length];
    var n = indice;
    if (familia === "aritmetica") {
      var a = 2 + (n % 7), b = 3 + ((n * 2) % 6), op = (n % 2 === 0) ? "+" : "X";
      return {
        familia: familia,
        texto: "¿Cuánto es " + a + " " + op + " " + b + "?",
        esperadas: [String(op === "+" ? a + b : a * b)]
      };
    }
    if (familia === "capital") {
      var cual = n % 2 === 1;   // la errata del portal real
      return cual
        ? { familia: familia, texto: "¿Cuál es la Capital del Vallle del Cauca?", esperadas: ["cali", "santiago de cali"] }
        : { familia: familia, texto: "¿Cuál es la capital de Colombia?", esperadas: ["bogota", "bogota d.c.", "bogota dc"] };
    }
    if (familia === "documento") {
      var primeros = (n % 2 === 0);
      return {
        familia: familia,
        texto: primeros ? "¿Escriba los tres primeros dígitos del documento a consultar?"
                        : "¿Escriba los dos últimos dígitos del documento a consultar?",
        lados: primeros ? ["primeros", 3] : ["ultimos", 2]
      };
    }
    var cantidad = (n % 2 === 1);
    return {
      familia: familia,
      texto: cantidad
        ? "¿Escriba la cantidad de letras del primer nombre de la persona a la cual esta consultando?"
        : "¿Cuál es el primer nombre de la persona a la cual esta consultando?",
      cantidad: cantidad
    };
  }

  var contadorPreguntas = 0;

  function pintarPregunta() {
    preguntaActual = nuevaPregunta(contadorPreguntas++);
    var lbl = $("lblPregunta");
    if (lbl) { lbl.textContent = preguntaActual.texto; }
  }

  function respuestaEsperada() {
    var p = preguntaActual;
    var numero = ($("txtNumID") || {}).value || "";
    var nombre = ($("txtNombre") || {}).value || "";
    if (p.esperadas) { return p.esperadas; }
    if (p.lados) {
      var digitos = numero.replace(/\D/g, "");
      return [p.lados[0] === "primeros" ? digitos.slice(0, p.lados[1]) : digitos.slice(-p.lados[1])];
    }
    var primero = (nombre.trim().split(/\s+/)[0] || "");
    return [p.cantidad ? String(primero.length) : primero];
  }

  function captchaCorrecto() {
    var escrita = sinTildes(($("txtRespuestaPregunta") || {}).value || "");
    if (!escrita) { return false; }
    var esperadas = respuestaEsperada().map(sinTildes);
    if (preguntaActual.familia === "aritmetica" || preguntaActual.familia === "capital") {
      return esperadas.indexOf(escrita) >= 0;
    }
    return esperadas.indexOf(escrita) >= 0;
  }

  /* ---------------------------------------------------------------- */
  /* Pasos                                                            */
  /* ---------------------------------------------------------------- */
  function pasoTérminos() {
    var continuar = $("continuarBtn");
    var acepto = $("rbAcepto");
    var noAcepto = $("rbNoAcepto");
    if (!continuar || !acepto) { return false; }

    function sincronizar() {
      continuar.disabled = !acepto.checked;
      $("lblMensajeTerminos").textContent = "";
    }
    acepto.addEventListener("change", sincronizar);
    if (noAcepto) { noAcepto.addEventListener("change", sincronizar); }
    sincronizar();

    continuar.addEventListener("click", function (ev) {
      ev.preventDefault();
      if (!acepto.checked) {
        $("lblMensajeTerminos").textContent = "Debe aceptar los términos para continuar.";
        return;
      }
      $("pnlTerminos").style.display = "none";
      $("pnlConsulta").style.display = "block";
      pintarPregunta();
    });
    return true;
  }

  function nombreSintetico(numero) {
    var apellidos = ["DEMO", "PRUEBA", "SINTETICO", "MUESTRA", "FICTICIO", "EJEMPLO", "TESTIGO", "LABORATORIO", "PATRON", "ENSAYO"];
    var nombres = ["CIUDADANO", "USUARIO", "PERSONA", "TITULAR", "CONSULTA", "REGISTRO", "DOCUMENTO", "IDENTIDAD", "VERIFICACION", "CONTROL"];
    var final = (numero.replace(/\D/g, "").slice(-1) || "0");
    var i = parseInt(final, 10) || 0;
    // el portal entrega nombres y luego apellidos
    return nombres[i] + " " + apellidos[i];
  }

  function mostrarMensaje(texto) {
    $("divDatosCiudadano").style.display = "none";
    $("lblMensaje").textContent = texto;
  }

  function consultar() {
    var tipo = $("ddlTipoID").value;
    var numero = ($("txtNumID").value || "").replace(/\s/g, "");
    var correo = ($("txtCorreoEle").value || "").trim();

    if (tipo === "-1") { return mostrarMensaje("Seleccione un tipo de documento."); }
    if (!numero) { return mostrarMensaje("Escriba un número de identificación"); }
    if ((tipo === "1" || tipo === "2") && !/^\d+$/.test(numero)) {
      return mostrarMensaje("El campo número de identificación debe ser númerico.");
    }
    if (correo && !/^\w+([-+.'_]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/.test(correo)) {
      return mostrarMensaje("El formato del correo electronico no es correcto.");
    }
    if (!captchaCorrecto()) {
      $("lblMensaje").textContent = "La respuesta a la pregunta es incorrecta.";
      $("divDatosCiudadano").style.display = "none";
      pintarPregunta();   // el portal entrega una pregunta nueva tras el fallo
      $("txtRespuestaPregunta").value = "";
      return;
    }

    if (tipo !== "1") {
      // documento no-cédula: el portal responde sin el bloque con el nombre
      return mostrarMensaje("No se encontró información para el documento consultado.");
    }

    $("lblMensaje").textContent = "";
    $("lblNombre").textContent = nombreSintetico(numero);
    $("lblEstado").textContent = (parseInt(numero.slice(-1), 10) % 2 === 1)
      ? "El ciudadano presenta antecedentes"
      : "El ciudadano no presenta antecedentes";
    $("divDatosCiudadano").style.display = "block";
  }

  function pasoConsulta() {
    var boton = $("btnExportar");
    if (!boton) { return; }
    boton.addEventListener("click", function (ev) {
      ev.preventDefault();
      consultar();
    });
    var refresco = $("ImageButton1");
    if (refresco) {
      refresco.addEventListener("click", function (ev) {
        ev.preventDefault();
        pintarPregunta();
        $("txtRespuestaPregunta").value = "";
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    pasoTérminos();
    pasoConsulta();
  });
})();
