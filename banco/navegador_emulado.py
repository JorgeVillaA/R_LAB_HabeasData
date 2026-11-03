"""Navegador mínimo para el intérprete del robot: emula, por HTTP, los comandos web de Studio que usa LabHabeasData
(`openbrowser`, `openUrl`, `click_web`, `sendkey_web`, `textObject`, `waitforobject`) contra los clones de los portales.

No sustituye a Chrome: sirve para que las DECISIONES del robot sobre los portales se prueben en cada corrida de la suite
(sin Studio). La verificación visual y de ejecución real en Chrome la hace Studio (`banco/equivalencia_robot.py`).
Selectores soportados: //body, //*[@id='x'], //tag[@id='x'], //select[@id='x']/option[@value='v'].
"""
import html.parser
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BLOQUES = {"p", "div", "h1", "h2", "h3", "tr", "form", "table", "li", "br", "body"}


class ElementoNoEncontrado(Exception):
    pass


class DOM(html.parser.HTMLParser):
    def __init__(self, texto):
        super().__init__()
        self.elementos, self.formularios, self.texto_total = [], [], []
        self._form, self._select, self._abiertos = None, None, []
        self.feed(texto)
        self.texto_pagina = re.sub(r"[ \t]+", " ", "".join(self.texto_total))

    def handle_starttag(self, etiqueta, atributos):
        a = dict(atributos)
        if etiqueta in BLOQUES:
            self.texto_total.append("\n")
        if etiqueta == "td":
            self.texto_total.append(" ")
        if etiqueta == "form":
            self._form = {"action": a.get("action", ""), "metodo": a.get("method", "get").lower()}
            self.formularios.append(self._form)
        elemento = {"tag": etiqueta, "id": a.get("id"), "para": a.get("for"), "name": a.get("name"), "type": (a.get("type") or "text").lower(),
                    "value": a.get("value", ""), "checked": "checked" in a, "form": self._form, "texto": [], "opciones": []}
        if etiqueta == "option" and self._select is not None:
            elemento["select"] = self._select
            self._select["opciones"].append(elemento)
            if "selected" in a:
                self._select["value"] = a.get("value", "")
        if etiqueta == "select":
            self._select = elemento
        if etiqueta in ("input", "select", "textarea", "option") or a.get("id") or a.get("for") or etiqueta in ("body", "h1"):
            self.elementos.append(elemento)
        self._abiertos.append(elemento)
        if etiqueta in ("input", "br"):
            self._abiertos.pop()

    def handle_endtag(self, etiqueta):
        if etiqueta in BLOQUES:
            self.texto_total.append("\n")
        if etiqueta == "form":
            self._form = None
        if etiqueta == "select":
            self._select = None
        for i in range(len(self._abiertos) - 1, -1, -1):
            if self._abiertos[i]["tag"] == etiqueta:
                del self._abiertos[i:]
                break

    def handle_data(self, dato):
        self.texto_total.append(dato)
        for elemento in self._abiertos:
            elemento["texto"].append(dato)


def texto_de(elemento):
    return " ".join("".join(elemento["texto"]).split())


class Navegador:
    def __init__(self):
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.url, self.dom = "", DOM("")

    def _cargar(self, url, datos=None):
        cuerpo = urllib.parse.urlencode(datos).encode("utf-8") if datos is not None else None
        try:
            with self.opener.open(urllib.request.Request(url, cuerpo), timeout=10) as r:
                self.url, texto = r.geturl(), r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:  # Chrome muestra el cuerpo de la página de error
            self.url, texto = url, error.read().decode("utf-8", "replace")
        except (urllib.error.URLError, OSError):
            self.url, texto = url, "ERR_CONNECTION_REFUSED"
        self.dom = DOM(texto)

    def abrir_url(self, url):
        self._cargar(url)

    def buscar(self, xpath):
        m = re.fullmatch(r"//select\[@id='([^']+)'\]/option\[@value='([^']*)'\]", xpath)
        if m:
            for e in self.dom.elementos:
                if e["tag"] == "option" and e.get("select", {}).get("id") == m.group(1) and e["value"] == m.group(2):
                    return e
            raise ElementoNoEncontrado(xpath)
        if xpath == "//body":
            return {"tag": "body", "texto": [self.dom.texto_pagina], "id": None, "name": None, "type": "", "value": "", "form": None}
        m = re.fullmatch(r"//\*\[((?:@id='[^']+'(?: or )?)+)\]", xpath)  # //*[@id='a' or @id='b']
        if m:
            ids = re.findall(r"@id='([^']+)'", m.group(1))
            for e in self.dom.elementos:
                if e["id"] in ids:
                    return e
            raise ElementoNoEncontrado(xpath)
        m = re.fullmatch(r"//label\[@for='([^']+)'\]", xpath)  # la etiqueta de una casilla: clic = clic sobre su control
        if m:
            for e in self.dom.elementos:
                if e["tag"] == "label" and e.get("para") == m.group(1):
                    return e
            raise ElementoNoEncontrado(xpath)
        m = re.fullmatch(r"//(\*|\w+)\[@id='([^']+)'\]", xpath)
        if m:
            for e in self.dom.elementos:
                if e["id"] == m.group(2) and (m.group(1) == "*" or e["tag"] == m.group(1)):
                    return e
        raise ElementoNoEncontrado(xpath)

    def clic(self, xpath):
        e = self.buscar(xpath)
        if e["tag"] == "label":
            e = self.buscar(f"//*[@id='{e['para']}']")
        if e["id"] == "recaptchaCheckbox":  # el servidor le pone un onclick inline que marca la casilla oculta
            for otro in self.dom.elementos:
                if otro["id"] == "recaptchaCheck":
                    otro["checked"] = True
        elif e["tag"] == "option":
            e["select"]["value"] = e["value"]
        elif e["type"] in ("radio", "checkbox"):
            if e["type"] == "radio":
                for otro in self.dom.elementos:
                    if otro["tag"] == "input" and otro["type"] == "radio" and otro["name"] == e["name"] and otro["form"] is e["form"]:
                        otro["checked"] = False
            e["checked"] = True
        elif e["type"] in ("submit", "image"):
            self._enviar(e)

    def escribir(self, xpath, texto):
        e = self.buscar(xpath)
        if e["type"] == "radio" and texto == " ":  # la barra espaciadora sobre un radio lo marca (como en Chrome)
            self.clic(xpath)
            return
        e["value"] = texto

    def _enviar(self, boton):
        formulario = boton["form"]
        if formulario is None:
            raise ElementoNoEncontrado("el botón no está en un formulario")
        datos = {}
        for e in self.dom.elementos:
            if e["form"] is not formulario or not e["name"] or e["tag"] == "option":
                continue
            if e["tag"] == "select":
                datos[e["name"]] = e["value"] or (e["opciones"][0]["value"] if e["opciones"] else "")
            elif e["type"] in ("radio", "checkbox"):
                if e["checked"]:
                    datos[e["name"]] = e["value"] or "on"
            elif e["type"] in ("submit", "image"):
                continue
            else:
                datos[e["name"]] = e["value"]
        if boton["type"] == "image":
            datos[boton["name"] + ".x"], datos[boton["name"] + ".y"] = "1", "1"
        else:
            datos[boton["name"]] = boton["value"]
        self._cargar(urllib.parse.urljoin(self.url, formulario["action"]), datos)

    def texto(self, xpath):
        return texto_de(self.buscar(xpath)) if xpath != "//body" else self.dom.texto_pagina.strip()
