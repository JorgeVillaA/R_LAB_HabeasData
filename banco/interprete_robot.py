"""Intérprete mínimo del JSON del robot de Studio: ejecuta `setVar`, `evaluateIf`, `for`, `group`, `trycatch`,
`log_message` y `execScriptPython` sin Studio, para que las DECISIONES del robot (las que viven en bloques visibles) se
prueben en cada corrida de la suite y no solo cuando alguien tiene Studio y el MCP.

Imita la semántica de Studio que usa este robot: `{variable}` se sustituye por el texto del valor (la cadena tal cual; el
resto con `repr`) antes de evaluar la expresión; `execScriptPython` corre con `GetVar`/`SetVar`. No sustituye a la
equivalencia en Studio (`equivalencia_robot.py`): la complementa.
"""
import json
import re
import sys

COMANDOS_WEB = ("openbrowser", "openUrl", "click_web", "sendkey_web", "waitforobject", "textObject")
SUSTITUCION = re.compile(r"\{((?:glb|loc)[A-Za-z0-9_]+)\}")


class Interprete:
    def __init__(self, robot, raiz):
        self.variables = {v["name"]: v["data"] for v in robot["vars"]}
        self.variables["glbStrRutaRaiz"] = str(raiz)
        self.comandos = robot["commands"]
        self.bloques = 0
        self.navegador = None
        self.capturadas = 0  # excepciones que tragó un trycatch: en un escenario sano deben ser 0

    def sustituir(self, texto):
        def valor(m):
            v = self.variables[m.group(1)]
            return v if isinstance(v, str) else repr(v)
        return SUSTITUCION.sub(valor, texto)

    def evaluar(self, expresion):
        return eval(self.sustituir(expresion), {"__builtins__": __builtins__})  # noqa: S307 (JSON propio del repo)

    def web(self, c):
        """Comandos web de Studio contra el navegador emulado (clones de los portales)."""
        from navegador_emulado import Navegador
        padre, orden = c["father"], c.get("command")
        if padre == "openbrowser":
            self.navegador = Navegador()
            return
        if padre == "openUrl":
            return self.navegador.abrir_url(self.sustituir(orden))
        datos = {k: (self.sustituir(v) if isinstance(v, str) else v) for k, v in orden.items()} if isinstance(orden, dict) else {}
        if padre == "click_web":
            self.navegador.clic(datos["data"])
        elif padre == "sendkey_web":
            self.navegador.escribir(datos["data"], datos["text"])
        elif padre == "waitforobject":
            self.navegador.buscar(datos["object"])
        elif padre == "textObject":
            self.variables[c["getvar"]] = self.navegador.texto(self.sustituir(orden))

    def ejecutar(self):
        self.secuencia(self.comandos)
        return self.variables

    def secuencia(self, comandos):
        for comando in comandos or []:
            self.comando(comando)

    def comando(self, c):
        self.bloques += 1
        padre = c["father"]
        if padre == "setVar":
            self.variables[c["var"]] = self.evaluar(c["command"])
        elif padre == "evaluateIf":
            self.secuencia(c.get("children") if self.evaluar(c["command"]) else c.get("else"))
        elif padre == "for":
            for elemento in self.evaluar(json.loads(c["command"])["iterable"]):
                self.variables[c["var"]] = str(elemento)
                self.secuencia(c.get("children"))
        elif padre == "group":
            self.secuencia(c.get("children"))
        elif padre == "trycatch":
            try:
                self.secuencia(c.get("children"))
            except Exception:  # noqa: BLE001 (como el trycatch de Studio)
                self.capturadas += 1
                self.secuencia(c.get("else"))
        elif padre == "log_message":
            pass
        elif padre in COMANDOS_WEB:
            self.web(c)
        elif padre == "execScriptPython":
            exec(c["command"], {"GetVar": self.variables.__getitem__, "SetVar": self.variables.__setitem__})  # noqa: S102
        else:
            raise NotImplementedError(padre)


def correr(interprete):
    """Ejecuta el robot y devuelve las variables finales; restaura los módulos `habeasdata` y el sys.path que toca el robot."""
    antes = {n: m for n, m in sys.modules.items() if n == "habeasdata" or n.startswith("habeasdata.")}
    ruta = list(sys.path)
    try:
        return interprete.ejecutar()
    finally:
        for nombre in [n for n in sys.modules if n == "habeasdata" or n.startswith("habeasdata.")]:
            del sys.modules[nombre]
        sys.modules.update(antes)
        sys.path[:] = ruta


def ejecutar_robot(robot, raiz):
    return correr(Interprete(robot, raiz))
