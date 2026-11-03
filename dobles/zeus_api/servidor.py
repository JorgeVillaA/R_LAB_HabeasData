"""Doble local de la API de Zeus (lectura OData + escritura de comentario). Solo biblioteca estándar.

Contrato de lectura: manual de consumo «CamposAdicionalesXRadicadoHabeasData» (2026-10-07): OAuth 2.0 client
credentials, token de 300 s sin refresh, OData v4 ($filter, $select, $first, $orderby), respuesta {"value": [...]},
códigos 200/400/401/403/404.
Contrato de escritura (comentario en Gestión → Detalle): SUPUESTO DEL LAB (C-09), no del manual.
Credenciales: nunca en el repositorio; se reciben por argumento y el arranque por línea de comandos las lee del entorno.
"""
import argparse
import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

try:
    from .campos import CAMPOS
    from . import odata
except ImportError:  # ejecución directa como script
    from campos import CAMPOS
    import odata

RAIZ_API = "/habeasdata/api/CamposAdicionalesXRadicadoHabeasData"
RUTA_TOKEN = "/sso/git_cisa/token"
RUTA_COMENTARIO = "/habeasdata/api/GestionRadicado/Comentario"
DATOS_POR_DEFECTO = Path(__file__).resolve().parents[2] / "fixtures" / "zeus" / "radicados.json"


class Estado:
    def __init__(self, credenciales, radicados, reloj=time.monotonic):
        self.credenciales = credenciales
        self.radicados = radicados
        self.reloj = reloj
        self.bloqueo = threading.Lock()
        self.tokens = {}
        self.token_ttl = 300
        self.denegar = False
        self.fallas_radicado = {}
        self.falla_comentario = None
        self.comentarios = []
        self.contadores = {"tokens": 0, "consultas": 0, "comentarios": 0}
        self.programado = None  # cambio del doble que ocurre tras N consultas (p. ej. casos que llegan mientras el bot espera)

    def programar(self, tras, cambios):
        """Aplica `cambios` justo antes de atender la consulta N+1; `reiniciar` restaura el estado de origen y lo vuelve a armar."""
        self.programado = {"tras": int(tras), "cambios": dict(cambios), "aplicado": False,
                           "origen": {"radicados": list(self.radicados), "denegar": self.denegar}}

    def aplicar_programado_si_toca(self):
        p = self.programado
        if p and not p["aplicado"] and self.contadores["consultas"] + 1 > p["tras"]:
            p["aplicado"] = True
            self._aplicar(p["cambios"])

    def emitir_token(self):
        token = secrets.token_hex(16)
        self.tokens[token] = self.reloj() + self.token_ttl
        self.contadores["tokens"] += 1
        return token

    def token_valido(self, token):
        vence = self.tokens.get(token)
        return vence is not None and self.reloj() < vence

    def configurar(self, cambios):
        if "cambio_tras_consultas" in cambios:
            self.programar(cambios["cambio_tras_consultas"]["tras"], cambios["cambio_tras_consultas"]["cambios"])
        self._aplicar(cambios)

    def _aplicar(self, cambios):
        if "token_ttl" in cambios:
            self.token_ttl = int(cambios["token_ttl"])
        if cambios.get("invalidar_tokens"):
            self.tokens.clear()
        if "denegar" in cambios:
            self.denegar = bool(cambios["denegar"])
        if "fallas_radicado" in cambios:
            self.fallas_radicado = {str(k): int(v) for k, v in cambios["fallas_radicado"].items()}
        if "falla_comentario" in cambios:
            self.falla_comentario = cambios["falla_comentario"]
        if "radicados" in cambios:
            self.radicados = list(cambios["radicados"])
        if cambios.get("reiniciar"):
            if self.programado:
                self.programado["aplicado"] = False
                self._aplicar(self.programado["origen"])
            self.comentarios.clear()
            self.contadores.update({"tokens": 0, "consultas": 0, "comentarios": 0})


class Manejador(BaseHTTPRequestHandler):
    server_version = "DobleZeus/1.0"

    def log_message(self, formato, *args):  # silencio: los logs del lab los escribe el robot
        pass

    @property
    def estado(self):
        return self.server.estado

    def _responder(self, codigo, cuerpo, tipo="application/json; charset=utf-8"):
        datos = cuerpo.encode("utf-8") if isinstance(cuerpo, str) else cuerpo
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _json(self, codigo, objeto):
        self._responder(codigo, json.dumps(objeto, ensure_ascii=False))

    def _error(self, codigo, mensaje):
        self._json(codigo, {"error": {"code": codigo, "message": mensaje}})

    def _autorizado(self):
        """Devuelve True si pasa; si no, ya respondió 401 o 403."""
        cabecera = self.headers.get("Authorization", "")
        token = cabecera[7:].strip() if cabecera.lower().startswith("bearer ") else ""
        if not self.estado.token_valido(token):
            self._error(401, "Token ausente, expirado o inválido")
            return False
        if self.estado.denegar:
            self._error(403, "El token carece de los roles requeridos para la entidad")
            return False
        return True

    def _cuerpo(self):
        """Cuerpo de la petición, leído una sola vez: responder sin consumirlo provoca reinicios de conexión."""
        if not hasattr(self, "_crudo"):
            largo = int(self.headers.get("Content-Length") or 0)
            self._crudo = self.rfile.read(largo).decode("utf-8") if largo else ""
        return self._crudo

    def do_GET(self):
        partes = urlsplit(self.path)
        ruta = unquote(partes.path)
        if ruta in ("/_doble", "/_doble/"):
            return self._pagina_estado()
        if ruta == "/_doble/estado":
            return self._json(200, self._resumen())
        if ruta == RAIZ_API:
            return self._consulta(partes.query)
        if ruta.startswith(RAIZ_API + "/IDRADICADO/"):
            return self._individual(ruta.rsplit("/", 1)[1])
        self._error(404, "URL no encontrada")

    def do_POST(self):
        self._cuerpo()
        ruta = urlsplit(self.path).path
        if ruta == RUTA_TOKEN:
            return self._token()
        if ruta == RUTA_COMENTARIO:
            return self._comentario()
        if ruta == "/_doble/config":
            try:
                cambios = json.loads(self._cuerpo() or "{}")
            except json.JSONDecodeError:
                return self._error(400, "JSON inválido")
            with self.estado.bloqueo:
                self.estado.configurar(cambios)
            return self._json(200, self._resumen())
        self._error(404, "URL no encontrada")

    def _token(self):
        forma = dict(parse_qsl(self._cuerpo()))
        cliente, secreto = self.estado.credenciales
        if forma.get("grant_type") != "client_credentials":
            return self._error(400, "grant_type no soportado")
        if forma.get("client_id") != cliente or not secrets.compare_digest(forma.get("client_secret", ""), secreto):
            return self._error(401, "Credenciales de cliente inválidas")
        with self.estado.bloqueo:
            token = self.estado.emitir_token()
            ttl = self.estado.token_ttl
        self._json(200, {"access_token": token, "expires_in": ttl, "refresh_expires_in": 0,
                         "token_type": "Bearer", "not-before-policy": 0,
                         "scope": "email profile custom-attributes"})

    def _consulta(self, consulta):
        with self.estado.bloqueo:
            self.estado.aplicar_programado_si_toca()
        if not self._autorizado():
            return
        parametros = dict(parse_qsl(consulta, keep_blank_values=True))
        with self.estado.bloqueo:
            self.estado.contadores["consultas"] += 1
            registros = list(self.estado.radicados)
        try:
            valores = odata.aplicar(registros, parametros, CAMPOS)
        except odata.ErrorOData as error:
            return self._error(400, str(error))
        self._json(200, {"value": valores})

    def _individual(self, id_radicado):
        if not self._autorizado():
            return
        falla = self.estado.fallas_radicado.get(id_radicado)
        if falla:
            return self._error(falla, "Falla inyectada por el escenario")
        for registro in self.estado.radicados:
            if str(registro.get("IDRADICADO")) == id_radicado:
                return self._json(200, {"value": [registro]})
        self._error(404, "IDRADICADO inexistente")

    def _comentario(self):
        if not self._autorizado():
            return
        if self.estado.falla_comentario:
            return self._error(int(self.estado.falla_comentario), "Falla inyectada por el escenario")
        try:
            cuerpo = json.loads(self._cuerpo() or "{}")
        except json.JSONDecodeError:
            return self._error(400, "JSON inválido")
        id_radicado, detalle = str(cuerpo.get("IDRADICADO", "")).strip(), str(cuerpo.get("Detalle", "")).strip()
        if not id_radicado or not detalle:
            return self._error(400, "IDRADICADO y Detalle son obligatorios")
        if not any(str(r.get("IDRADICADO")) == id_radicado for r in self.estado.radicados):
            return self._error(404, "IDRADICADO inexistente")
        with self.estado.bloqueo:
            self.estado.comentarios.append({"IDRADICADO": id_radicado, "Detalle": detalle})
            self.estado.contadores["comentarios"] += 1
        self._json(201, {"IDRADICADO": id_radicado, "registrado": True})

    def _resumen(self):
        e = self.estado
        return {"radicados": len(e.radicados), "token_ttl": e.token_ttl, "denegar": e.denegar,
                "contadores": e.contadores, "comentarios": e.comentarios,
                "fallas_radicado": e.fallas_radicado, "falla_comentario": e.falla_comentario}

    def _pagina_estado(self):
        e = self.estado
        filas = "".join(
            f"<tr><td>{r.get('IDRADICADO')}</td><td>{r.get('PQRCORRESPONDEA')}</td>"
            f"<td>{r.get('EstadoActual')}</td></tr>" for r in e.radicados)
        html = (
            "<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Doble API de Zeus (lab)</title>"
            "<style>body{font-family:sans-serif;margin:2rem}table{border-collapse:collapse}"
            "td,th{border:1px solid #888;padding:.3rem .6rem}</style></head><body>"
            "<h1 id='titulo'>Doble local de la API de Zeus</h1>"
            "<p id='aviso'>Datos 100 % sintéticos. Solo modo local aislado.</p>"
            f"<ul><li>Radicados cargados: <b id='total'>{len(e.radicados)}</b></li>"
            f"<li>Tokens emitidos: <b id='tokens'>{e.contadores['tokens']}</b></li>"
            f"<li>Consultas: <b id='consultas'>{e.contadores['consultas']}</b></li>"
            f"<li>Comentarios recibidos: <b id='comentarios'>{e.contadores['comentarios']}</b></li></ul>"
            "<table id='radicados'><tr><th>IDRADICADO</th><th>PQRCORRESPONDEA</th><th>EstadoActual</th></tr>"
            f"{filas}</table></body></html>")
        self._responder(200, html, "text/html; charset=utf-8")


class DobleZeus:
    """Servidor en hilo, para tests, banco y arranque por línea de comandos."""

    def __init__(self, credenciales, radicados=None, puerto=0, reloj=time.monotonic):
        if radicados is None:
            radicados = json.loads(DATOS_POR_DEFECTO.read_text(encoding="utf-8"))
        self.estado = Estado(credenciales, radicados, reloj)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
        self.httpd.estado = self.estado
        self.hilo = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def puerto(self):
        return self.httpd.server_address[1]

    @property
    def url(self):
        return f"http://127.0.0.1:{self.puerto}"

    def iniciar(self):
        self.hilo.start()
        return self

    def detener(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.hilo.join(timeout=5)


def principal():
    analizador = argparse.ArgumentParser(description="Doble local de la API de Zeus")
    analizador.add_argument("--puerto", type=int, default=8765)
    analizador.add_argument("--datos", default=str(DATOS_POR_DEFECTO))
    argumentos = analizador.parse_args()
    cliente = os.environ.get("ZEUS_DOBLE_CLIENT_ID")
    secreto = os.environ.get("ZEUS_DOBLE_CLIENT_SECRET")
    if not cliente or not secreto:
        raise SystemExit("Defina ZEUS_DOBLE_CLIENT_ID y ZEUS_DOBLE_CLIENT_SECRET en el entorno (no se guardan en el repo).")
    radicados = json.loads(Path(argumentos.datos).read_text(encoding="utf-8"))
    doble = DobleZeus((cliente, secreto), radicados, argumentos.puerto).iniciar()
    print(f"Doble de Zeus escuchando en {doble.url}", flush=True)
    try:
        doble.hilo.join()
    except KeyboardInterrupt:
        doble.detener()


if __name__ == "__main__":
    principal()
