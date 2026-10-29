"""Cliente de la API de Zeus, implementado contra el contrato REAL «CamposAdicionalesXRadicadoHabeasData».

- OAuth 2.0 client credentials contra Keycloak (realm git_cisa); token de 300 s sin refresh: ante un 401 se pide
  uno nuevo y se repite la llamada una vez (manual de consumo, §3.1).
- OData v4 sobre el endpoint: $filter, $select, $first, $orderby; consulta individual por IDRADICADO.
- Modo `fixture` (por defecto): el mismo cliente contra el doble local, solo para el banco determinista y las
  pruebas reproducibles sin red. Modo `real`: contra qaservices.cisa.gov.co.
- El cliente de LECTURA solo consulta. Las escrituras (comentario en Gestión → Detalle, transiciones de estado) son
  endpoints transaccionales aún sin entregar: viven aparte (`EscrituraComentario`) y nunca se simulan como si existieran.
- Salvaguardas del modo real (bloqueos explícitos, nunca se enmascaran): el client_secret sale SOLO del Administrador
  de credenciales de Windows; sin secreto o sin autorización de uso declarada no hay llamada de red.
- Fallos de conexión o 5xx: NUMERO_REINTENTOS_SISTEMA reintentos con backoff (cada reintento queda en el log).
- Los secretos no van en código, JSON, fixtures, variables del robot ni logs (en modo fixture, las credenciales del doble salen del entorno).
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from . import credenciales

APLICATIVO = "Zeus API"
MODOS = ("fixture", "real")


class ErrorZeus(Exception):
    def __init__(self, mensaje, estado=None):
        super().__init__(mensaje)
        self.estado = estado


class ErrorSolicitud(ErrorZeus):
    """400: parámetro OData mal formulado, campo inexistente o cuerpo inválido."""


class ErrorNoAutenticado(ErrorZeus):
    """401 que persiste tras renovar el token, o credenciales de cliente rechazadas."""


class ErrorPermiso(ErrorZeus):
    """403: el token carece de roles para la entidad."""


class ErrorNoEncontrado(ErrorZeus):
    """404: IDRADICADO inexistente o URL errada."""


class ErrorNoDisponible(ErrorZeus):
    """Sin conexión o 5xx tras agotar los reintentos del sistema."""


class ErrorBloqueo(ErrorZeus):
    """Falta algo externo para operar contra la API real (client_secret, autorización de uso, endpoint)."""


class ClienteZeus:
    def __init__(self, cfg, registro, entorno=None, dormir=time.sleep, lector_secreto=credenciales.leer_secreto):
        self.cfg = cfg
        self.lector_secreto = lector_secreto
        self.registro = registro
        self.entorno = os.environ if entorno is None else entorno
        self.dormir = dormir
        self.token = None
        zeus = cfg.proceso["ZeusApi"]
        self.modo = zeus["Modo"]
        if self.modo not in MODOS:
            raise ValueError(f"ZeusApi.Modo debe ser uno de {MODOS}, no {self.modo!r}")
        self.ajustes = zeus[{"fixture": "Fixture", "real": "Real"}[self.modo]]
        self.reintentos = int(cfg.maestro["NUMERO_REINTENTOS_SISTEMA"])
        self.backoff = zeus["BackoffSegundos"]
        self.timeout = zeus["TimeoutSegundos"]

    # ---- salvaguardas del modo real ----
    def _verificar_autorizacion(self):
        if self.modo != "real":
            return
        variable = self.ajustes["AutorizacionEnv"]
        if self.entorno.get(variable) != "1":
            raise ErrorBloqueo(
                f"BLOQUEO: falta la autorización de uso de la API real de Zeus (variable {variable}=1); no se realiza ninguna llamada")

    # ---- transporte ----
    def _enviar(self, metodo, url, cuerpo=None, cabeceras=None):
        """Una llamada con reintentos de sistema. Devuelve (estado_http, objeto_json)."""
        ultimo = None
        for intento in range(self.reintentos + 1):
            if intento:
                self.registro.auditoria(f"Reintento {intento}/{self.reintentos} de {metodo} en {APLICATIVO}: {ultimo}", APLICATIVO)
                self.dormir(self.backoff[min(intento - 1, len(self.backoff) - 1)])
            peticion = urllib.request.Request(url, data=cuerpo, method=metodo, headers=cabeceras or {})
            try:
                with urllib.request.urlopen(peticion, timeout=self.timeout) as respuesta:
                    return respuesta.status, self._json(respuesta.read())
            except urllib.error.HTTPError as error:
                if error.code < 500:
                    return error.code, self._json(error.read())
                ultimo = f"HTTP {error.code}"
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                ultimo = f"sin conexión ({type(error).__name__})"
        raise ErrorNoDisponible(f"{APLICATIVO} no disponible tras {self.reintentos} reintentos: {ultimo}")

    @staticmethod
    def _json(datos):
        try:
            return json.loads(datos.decode("utf-8")) if datos else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}

    # ---- autenticación ----
    def _credenciales(self):
        if self.modo == "real":
            cliente = self.ajustes["ClientId"]
            target = self.ajustes["CredencialTarget"]
            secreto = self.lector_secreto(target)
            if not secreto:
                raise ErrorBloqueo(
                    f"BLOQUEO: falta el client_secret de Keycloak en el Administrador de credenciales de Windows (credencial {target}); se pide por canal seguro, nunca en el repo")
            return cliente, secreto
        cliente = self.entorno.get(self.ajustes["ClientIdEnv"])
        secreto = self.entorno.get(self.ajustes["ClientSecretEnv"])
        if not cliente or not secreto:
            raise ErrorNoAutenticado("Credenciales del doble no definidas en el entorno", 401)
        return cliente, secreto

    def renovar_token(self):
        self._verificar_autorizacion()
        cliente, secreto = self._credenciales()
        forma = urllib.parse.urlencode(
            {"grant_type": "client_credentials", "client_id": cliente, "client_secret": secreto}).encode("ascii")
        estado, cuerpo = self._enviar("POST", self.ajustes["UrlToken"], forma,
                                      {"Content-Type": "application/x-www-form-urlencoded"})
        if estado != 200 or "access_token" not in cuerpo:
            raise ErrorNoAutenticado(f"El servidor de tokens rechazó las credenciales (HTTP {estado})", estado)
        self.token = cuerpo["access_token"]
        self.registro.auditoria(f"Token OAuth obtenido (vigencia {cuerpo.get('expires_in', 'NO APLICA')} s)", APLICATIVO)

    def _autorizada(self, metodo, url, cuerpo=None, tipo=None):
        """Llamada autenticada; ante 401 renueva el token y reintenta una sola vez."""
        self._verificar_autorizacion()
        for vuelta in range(2):
            if self.token is None:
                self.renovar_token()
            cabeceras = {"Authorization": f"Bearer {self.token}"}
            if tipo:
                cabeceras["Content-Type"] = tipo
            estado, cuerpo_respuesta = self._enviar(metodo, url, cuerpo, cabeceras)
            if estado == 401 and vuelta == 0:
                self.registro.auditoria("401 recibido: se solicita un token nuevo", APLICATIVO)
                self.token = None
                continue
            return self._traducir(estado, cuerpo_respuesta)
        raise ErrorNoAutenticado("401 persistente tras renovar el token", 401)  # pragma: no cover

    @staticmethod
    def _traducir(estado, cuerpo):
        if estado in (200, 201):
            return cuerpo
        mensaje = (cuerpo.get("error") or {}).get("message", f"HTTP {estado}") if isinstance(cuerpo, dict) else f"HTTP {estado}"
        errores = {400: ErrorSolicitud, 401: ErrorNoAutenticado, 403: ErrorPermiso, 404: ErrorNoEncontrado}
        raise errores.get(estado, ErrorZeus)(mensaje, estado)

    # ---- operaciones ----
    def url_consulta(self, filtro=None, select=None, first=None, orderby=None):
        """URL de consulta tal como la documenta el manual (parámetros OData con espacios codificados)."""
        parametros = []
        if filtro:
            parametros.append(("$filter", filtro))
        if select:
            parametros.append(("$select", ",".join(select)))
        if first is not None:
            parametros.append(("$first", str(first)))
        if orderby:
            parametros.append(("$orderby", orderby))
        url = self.ajustes["UrlBase"]
        if parametros:
            url += "?" + urllib.parse.urlencode(parametros, quote_via=urllib.parse.quote, safe="$,")
        return url

    def consultar(self, filtro=None, select=None, first=None, orderby=None):
        return self._autorizada("GET", self.url_consulta(filtro, select, first, orderby))["value"]

    def url_radicado(self, id_radicado):
        return f"{self.ajustes['UrlBase']}/IDRADICADO/{urllib.parse.quote(str(id_radicado))}"

    def radicado(self, id_radicado):
        valores = self._autorizada("GET", self.url_radicado(id_radicado))["value"]
        return valores[0] if valores else None


class EscrituraComentario:
    """Comentario en Gestión → Detalle. Contrato SUPUESTO del lab, solo contra el doble (C-09): en modo real no
    existe endpoint entregado y se reporta como bloqueo en lugar de simularlo."""

    def __init__(self, cliente):
        self.cliente = cliente

    def comentar(self, id_radicado, detalle):
        url = self.cliente.ajustes["UrlComentario"]
        if not url:
            raise ErrorBloqueo(
                "BLOQUEO: el endpoint de escritura del comentario (Gestión → Detalle) no está entregado por IT de CISA (C-09)")
        cuerpo = json.dumps({"IDRADICADO": str(id_radicado), "Detalle": detalle}, ensure_ascii=False).encode("utf-8")
        return self.cliente._autorizada("POST", url, cuerpo, "application/json")
