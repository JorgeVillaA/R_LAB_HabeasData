"""Repositorio local del lab (specs/repositorio-local.md): MER de 8 tablas + `Transacciones` + dos maestras.

Contrato único (`Repositorio`) con motor SQLite en un archivo dentro de la raíz del proceso (fallback documentado de D-07:
NocoDB npm 0.301.3 en loopback expone el mismo contrato; ver docs/REPOSITORIO-LOCAL.md). Datos 100 % sintéticos.

Reglas que impone este módulo:
- Cada operación reintenta `reintentos` veces (NUMERO_REINTENTOS_SISTEMA) y, agotados, lanza `ErrorRepositorio` (el caso
  pasa a excepción de sistema; el bot continúa con el siguiente radicado).
- `Transacciones` se escribe en cada transición, incluidos los fallos, y NO pasa por las fallas inyectadas de las demás
  operaciones: un repositorio que falla sigue dejando su fila de fallo (lección de Medidas Cautelares).
"""
import json
import sqlite3
import time
from datetime import datetime

ESTADOS = {1: "Sin Procesar", 2: "Procesando", 3: "Exitoso", 4: "No Exitoso", 5: "Procesado Parcialmente"}
COLUMNAS_CELULARES = ("ID CLIENTE", "ID CODEUDOR", "TIPO USUARIO", "IDENTIFICACION", "NOMBRE", "CELULAR", "FUENTE", "FECHA CONSULTA",
                      "ZEUS", "FECHA EXCLUSION", "Identificación Dueño Celular", "Nombre Dueño Celular", "GESTOR", "SUCURSAL")
COLUMNAS_CORREOS = ("ID CLIENTE", "ID CODEUDOR", "TIPO USUARIO", "IDENTIFICACION", "NOMBRE", "CORREO", "FUENTE", "FECHA CONSULTA",
                    "Zeus", "FECHA EXCLUSION", "IDENTIFICACIÓN DUEÑO CORREO", "NOMBRE DUEÑO CORREO", "GESTOR", "SUCURSAL")
CANALES = {"celular": ("Celulares", "MaestraCelulares", COLUMNAS_CELULARES, "CELULAR"),
           "correo": ("Correos", "MaestraCorreos", COLUMNAS_CORREOS, "CORREO")}
COLUMNAS_TRANSACCIONES = ("IdTransaccion", "RadicadoZeus", "Etapa", "EstadoAnterior", "EstadoNuevo", "FechaHora", "Resultado", "Motivo")


class ErrorRepositorio(Exception):
    """La operación falló de forma persistente (tras los reintentos)."""


def _tabla_canal(nombre, columnas):
    cuerpo = ", ".join(f'"{c}" TEXT' for c in columnas)
    return f'CREATE TABLE IF NOT EXISTS {nombre} (Id INTEGER PRIMARY KEY AUTOINCREMENT, {cuerpo})'


ESQUEMA = [
    "CREATE TABLE IF NOT EXISTS Insumo (RadicadoZeus TEXT PRIMARY KEY, RadicadoPadre TEXT, TipoIdentificacion TEXT, "
    "Identificacion TEXT, Estado INTEGER, FechaRecepcion TEXT, Actualizado TEXT, Nombre TEXT, Correos TEXT, Telefonos TEXT)",
    "CREATE TABLE IF NOT EXISTS Excepciones (Id INTEGER PRIMARY KEY AUTOINCREMENT, RadicadoZeus TEXT, TipoExcepcion TEXT, "
    "Detalle TEXT, FechaHora TEXT)",
    "CREATE TABLE IF NOT EXISTS Exclusion (Id INTEGER PRIMARY KEY AUTOINCREMENT, RadicadoZeus TEXT UNIQUE, Identificacion TEXT, "
    "FechaExclusion TEXT)",
    _tabla_canal("Celulares", COLUMNAS_CELULARES),
    _tabla_canal("Correos", COLUMNAS_CORREOS),
    "CREATE TABLE IF NOT EXISTS Gestores (Id INTEGER PRIMARY KEY AUTOINCREMENT, RadicadoZeus TEXT, Gestor TEXT, Agencia TEXT, "
    "Coordinador TEXT, Correo TEXT, FechaAsignacion TEXT, Motivo TEXT)",
    "CREATE TABLE IF NOT EXISTS Parametros (Clave TEXT PRIMARY KEY, Valor TEXT, Actualizado TEXT)",
    "CREATE TABLE IF NOT EXISTS LogEjecucion (Id INTEGER PRIMARY KEY AUTOINCREMENT, Fecha TEXT, CasosProcesados INTEGER, "
    "Exitosos INTEGER, NoExitosos INTEGER, Parciales INTEGER, Excepciones INTEGER, DuracionSegundos INTEGER, Detalle TEXT)",
    # tabla ligera: qué se borró de las maestras y cuándo (la corrida es reconstruible)
    "CREATE TABLE IF NOT EXISTS AuditoriaMaestras (Id INTEGER PRIMARY KEY AUTOINCREMENT, RadicadoZeus TEXT, Tabla TEXT, "
    "Identificacion TEXT, Valor TEXT, FilaEliminada TEXT, FechaHora TEXT)",
    "CREATE TABLE IF NOT EXISTS Transacciones (IdTransaccion INTEGER PRIMARY KEY AUTOINCREMENT, RadicadoZeus TEXT, Etapa TEXT, "
    "EstadoAnterior INTEGER, EstadoNuevo INTEGER, FechaHora TEXT, Resultado TEXT, Motivo TEXT)",
    _tabla_canal("MaestraCelulares", COLUMNAS_CELULARES),
    _tabla_canal("MaestraCorreos", COLUMNAS_CORREOS),
]
TABLAS = ("Insumo", "Excepciones", "Exclusion", "Celulares", "Correos", "Gestores", "Parametros", "LogEjecucion")
# columnas que un archivo creado por una versión anterior no tiene: se añaden al abrirlo (los datos previos se conservan)
ADICIONES = {"Insumo": (("Nombre", "TEXT"), ("Correos", "TEXT"), ("Telefonos", "TEXT")),
             "Gestores": (("RadicadoZeus", "TEXT"), ("FechaAsignacion", "TEXT"), ("Motivo", "TEXT")),
             "Parametros": (("Actualizado", "TEXT"),),
             "LogEjecucion": (("Exitosos", "INTEGER"), ("NoExitosos", "INTEGER"), ("Parciales", "INTEGER"),
                              ("DuracionSegundos", "INTEGER"))}
RENOMBRES = {"Excepciones": (("Tipo", "TipoExcepcion"), ("Fecha", "FechaHora"))}


class Repositorio:
    def __init__(self, ruta, reintentos=3, dormir=time.sleep, reloj=datetime.now):
        self.ruta, self.reintentos, self.dormir, self.reloj = str(ruta), max(1, int(reintentos)), dormir, reloj
        self.fallas = {}  # operación -> intentos que fallan (None = falla persistente): simula «el repositorio no responde»
        self.intentos = {}  # operación -> intentos realizados (observable en los tests)
        self.con = sqlite3.connect(self.ruta, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        for sentencia in ESQUEMA:
            self.con.execute(sentencia)
        self._migrar()
        self.con.commit()
        # marca de esta corrida: lo escrito después de aquí es «de la corrida» (LogEjecucion, casos huérfanos)
        self.inicio = self.reloj()
        self.id_inicial = self.con.execute("SELECT COALESCE(MAX(IdTransaccion), 0) FROM Transacciones").fetchone()[0]
        self.id_excepciones_inicial = self.con.execute("SELECT COALESCE(MAX(Id), 0) FROM Excepciones").fetchone()[0]
        self.corrida_cerrada = False

    def _columnas(self, tabla):
        return {f[1] for f in self.con.execute(f"PRAGMA table_info({tabla})")}

    def _migrar(self):
        for tabla, pares in RENOMBRES.items():
            for viejo, nuevo in pares:
                columnas = self._columnas(tabla)
                if viejo in columnas and nuevo not in columnas:
                    self.con.execute(f"ALTER TABLE {tabla} RENAME COLUMN {viejo} TO {nuevo}")
        for tabla, adiciones in ADICIONES.items():
            for columna, tipo in adiciones:
                if columna not in self._columnas(tabla):
                    self.con.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")

    def cerrar(self):
        self.con.close()

    # ---------- núcleo: reintentos y fallas inyectadas ----------
    def _operar(self, nombre, funcion):
        ultimo = None
        for intento in range(1, self.reintentos + 1):
            self.intentos[nombre] = self.intentos.get(nombre, 0) + 1
            try:
                restantes = self.fallas.get(nombre, 0)
                if nombre in self.fallas and (restantes is None or restantes > 0):
                    if restantes is not None:
                        self.fallas[nombre] = restantes - 1
                    raise sqlite3.OperationalError(f"el repositorio no respondió ({nombre})")
                resultado = funcion()
                self.con.commit()
                return resultado
            except sqlite3.Error as error:
                self.con.rollback()
                ultimo = error
                if intento < self.reintentos:
                    self.dormir(0)
        raise ErrorRepositorio(f"{nombre} falló tras {self.reintentos} intentos: {ultimo}")

    def _ahora(self):
        return self.reloj().strftime("%Y-%m-%d %H:%M:%S")

    # ---------- siembra (datos sintéticos) ----------
    def sembrar(self, canal, filas, maestra=True):
        tabla = CANALES[canal][1 if maestra else 0]
        columnas = CANALES[canal][2]
        for fila in filas:
            self.con.execute(f'INSERT INTO {tabla} ({", ".join(chr(34) + c + chr(34) for c in columnas)}) VALUES ({", ".join("?" * len(columnas))})',
                             [str(fila.get(c, "")) for c in columnas])
        self.con.commit()

    def sembrar_gestor(self, gestor, agencia, coordinador, correo):
        self.con.execute("INSERT INTO Gestores (Gestor, Agencia, Coordinador, Correo) VALUES (?,?,?,?)", (gestor, agencia, coordinador, correo))
        self.con.commit()

    # ---------- consultas por llave ----------
    def _existe(self, tabla, identificacion, columna, valor, operacion):
        def consulta():
            fila = self.con.execute(f'SELECT 1 FROM {tabla} WHERE IDENTIFICACION = ? AND "{columna}" = ? LIMIT 1',
                                    (str(identificacion), str(valor))).fetchone()
            return fila is not None
        return self._operar(operacion, consulta)

    def existe_exclusion(self, canal, identificacion, valor):
        """HU-010: llave compuesta identificación + celular en `Celulares`, o identificación + correo en `Correos`."""
        tabla, _, _, columna = CANALES[canal]
        return self._existe(tabla, identificacion, columna, valor, "buscar_exclusion_" + canal)

    def existe_en_maestra(self, canal, identificacion, valor):
        _, tabla, _, columna = CANALES[canal]
        return self._existe(tabla, identificacion, columna, valor, "buscar_maestra_" + canal)

    # ---------- HU-011: inserción y eliminación ----------
    def insertar_exclusion(self, radicado, identificacion):
        def insertar():
            self.con.execute("INSERT OR IGNORE INTO Exclusion (RadicadoZeus, Identificacion, FechaExclusion) VALUES (?,?,?)",
                             (str(radicado), str(identificacion), self._ahora()))
        return self._operar("insertar_exclusion", insertar)

    def insertar_canal(self, canal, fila):
        """Una fila de 14 columnas en `Celulares` o `Correos`. Devuelve 'insertado' o 'ya_presente' (no duplica)."""
        tabla, _, columnas, columna = CANALES[canal]

        def insertar():
            if self.con.execute(f'SELECT 1 FROM {tabla} WHERE IDENTIFICACION = ? AND "{columna}" = ? LIMIT 1',
                                (str(fila["IDENTIFICACION"]), str(fila[columna]))).fetchone():
                return "ya_presente"
            self.con.execute(f'INSERT INTO {tabla} ({", ".join(chr(34) + c + chr(34) for c in columnas)}) VALUES ({", ".join("?" * len(columnas))})',
                             [str(fila.get(c, "")) for c in columnas])
            return "insertado"
        return self._operar("insertar_" + canal, insertar)

    def eliminar_de_maestra(self, canal, identificacion, valor, radicado=None):
        """Elimina de la maestra el registro cuya identificación (y valor del canal) coincide; devuelve cuántos borró.
        Antes de borrar deja la fila completa en `AuditoriaMaestras` (misma transacción): la corrida es reconstruible."""
        _, tabla, columnas, columna = CANALES[canal]

        def borrar():
            filas = self.con.execute(f'SELECT * FROM {tabla} WHERE IDENTIFICACION = ? AND "{columna}" = ?',
                                     (str(identificacion), str(valor))).fetchall()
            for fila in filas:
                self.con.execute("INSERT INTO AuditoriaMaestras (RadicadoZeus, Tabla, Identificacion, Valor, FilaEliminada, FechaHora) "
                                 "VALUES (?,?,?,?,?,?)",
                                 (str(radicado) if radicado else None, tabla, str(identificacion), str(valor),
                                  json.dumps({c: fila[c] for c in columnas}, ensure_ascii=False), self._ahora()))
            return self.con.execute(f'DELETE FROM {tabla} WHERE IDENTIFICACION = ? AND "{columna}" = ?',
                                    (str(identificacion), str(valor))).rowcount
        return self._operar("eliminar_maestra_" + canal, borrar)

    def contar(self, tabla):
        return self.con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]

    # ---------- Insumo y Transacciones ----------
    def abrir_insumo(self, radicado):
        """El radicado entra a la corrida: fila de `Insumo` en estado 1 (Sin Procesar), también si venía de una corrida anterior."""
        self.con.execute("INSERT INTO Insumo (RadicadoZeus, Estado, Actualizado) VALUES (?,1,?) "
                         "ON CONFLICT(RadicadoZeus) DO UPDATE SET Estado=1, Actualizado=excluded.Actualizado", (str(radicado), self._ahora()))
        self.con.commit()

    def upsert_insumo(self, caso, estado=None):
        """Datos del caso (identificación, nombre y contacto). El `Estado` solo lo mueve una transición (o `estado` explícito)."""
        valores = (caso["radicado_hijo"], caso.get("radicado_padre"), caso.get("tipo_identificacion"), caso.get("numero_identificacion"),
                   estado if estado is not None else 1, caso.get("fecha_recepcion"), self._ahora(), caso.get("nombre"),
                   ", ".join(caso.get("correos") or []), ", ".join(t["valor"] for t in caso.get("telefonos") or []))
        cambia_estado = "Estado=excluded.Estado, " if estado is not None else ""
        self.con.execute(
            "INSERT INTO Insumo (RadicadoZeus, RadicadoPadre, TipoIdentificacion, Identificacion, Estado, FechaRecepcion, Actualizado, "
            "Nombre, Correos, Telefonos) VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(RadicadoZeus) DO UPDATE SET "
            "RadicadoPadre=excluded.RadicadoPadre, TipoIdentificacion=excluded.TipoIdentificacion, Identificacion=excluded.Identificacion, "
            f"FechaRecepcion=excluded.FechaRecepcion, Nombre=excluded.Nombre, Correos=excluded.Correos, Telefonos=excluded.Telefonos, "
            f"{cambia_estado}Actualizado=excluded.Actualizado", valores)
        self.con.commit()

    def estado_de(self, radicado):
        fila = self.con.execute("SELECT EstadoNuevo FROM Transacciones WHERE RadicadoZeus = ? ORDER BY IdTransaccion DESC LIMIT 1",
                                (str(radicado),)).fetchone()
        return fila[0] if fila else None

    def estado_en_corrida(self, radicado):
        """Estado del radicado según su última transición de ESTA corrida (None si todavía no tiene ninguna)."""
        fila = self.con.execute("SELECT EstadoNuevo FROM Transacciones WHERE RadicadoZeus = ? AND IdTransaccion > ? "
                                "ORDER BY IdTransaccion DESC LIMIT 1", (str(radicado), self.id_inicial)).fetchone()
        return fila[0] if fila else None

    def parcial(self, radicado):
        """¿El radicado tuvo valores duplicados que siguieron adelante (exclusión parcial)? Lo dice su transacción de duplicados."""
        fila = self.con.execute("SELECT 1 FROM Transacciones WHERE RadicadoZeus = ? AND Etapa = 'duplicados' AND "
                                "Motivo LIKE 'excepción de negocio 4 (parcial)%' LIMIT 1", (str(radicado),)).fetchone()
        return fila is not None

    def registrar_transaccion(self, radicado, etapa, estado_nuevo, resultado="ok", motivo=None, excepcion=None):
        """Una fila por transición (con información), incluidos los fallos. Nunca se salta por las fallas inyectadas de otras
        operaciones. `Resultado` es `fallo` siempre que el estado nuevo es 4 (No Exitoso); `ok` en los demás. Con `excepcion`
        (tipo: 1, 3, 4, sistema, gestion_manual) además deja la fila en `Excepciones`. El `Estado` de `Insumo` sigue a la transición."""
        anterior = self.estado_de(radicado)
        resultado = "fallo" if int(estado_nuevo) == 4 else "ok"
        texto = (motivo or "NO APLICA").replace(";", ",")
        ahora = self._ahora()
        self.con.execute("INSERT INTO Transacciones (RadicadoZeus, Etapa, EstadoAnterior, EstadoNuevo, FechaHora, Resultado, Motivo) "
                         "VALUES (?,?,?,?,?,?,?)", (str(radicado), etapa, anterior, int(estado_nuevo), ahora, resultado, texto))
        self.con.execute("UPDATE Insumo SET Estado = ?, Actualizado = ? WHERE RadicadoZeus = ?", (int(estado_nuevo), ahora, str(radicado)))
        if excepcion:
            self.con.execute("INSERT INTO Excepciones (RadicadoZeus, TipoExcepcion, Detalle, FechaHora) VALUES (?,?,?,?)",
                             (str(radicado), str(excepcion), texto, ahora))
        self.con.commit()

    def derivar_a_gestion(self, radicado, gestor, agencia, coordinador, correo, motivo):
        """Un caso que pasa a gestión manual queda con su fila en `Gestores` (una por radicado)."""
        if self.con.execute("SELECT 1 FROM Gestores WHERE RadicadoZeus = ?", (str(radicado),)).fetchone():
            return
        self.con.execute("INSERT INTO Gestores (RadicadoZeus, Gestor, Agencia, Coordinador, Correo, FechaAsignacion, Motivo) VALUES (?,?,?,?,?,?,?)",
                         (str(radicado), gestor, agencia, coordinador, correo, self._ahora(), motivo))
        self.con.commit()

    def guardar_parametros(self, parametros):
        """Parámetros de negocio vigentes en la corrida (umbral de nombres, reintentos, cadencia…): clave → valor, sin duplicar."""
        for clave, valor in parametros.items():
            self.con.execute("INSERT INTO Parametros (Clave, Valor, Actualizado) VALUES (?,?,?) ON CONFLICT(Clave) DO UPDATE SET "
                             "Valor=excluded.Valor, Actualizado=excluded.Actualizado", (str(clave), str(valor), self._ahora()))
        self.con.commit()

    def abiertos_de_la_corrida(self):
        """Radicados con transiciones en esta corrida cuyo último estado sigue siendo 1 o 2 (nadie los cerró)."""
        return [f[0] for f in self.con.execute(
            "SELECT RadicadoZeus FROM Transacciones WHERE IdTransaccion IN (SELECT MAX(IdTransaccion) FROM Transacciones "
            "WHERE IdTransaccion > ? GROUP BY RadicadoZeus) AND EstadoNuevo IN (1, 2) ORDER BY RadicadoZeus", (self.id_inicial,))]

    def registrar_log_ejecucion(self, detalle=None):
        """Fila resumen de la corrida (una sola vez): casos, éxitos, no éxitos, parciales, excepciones y duración."""
        if self.corrida_cerrada:
            return None
        estados = [f[0] for f in self.con.execute(
            "SELECT EstadoNuevo FROM Transacciones WHERE IdTransaccion IN (SELECT MAX(IdTransaccion) FROM Transacciones "
            "WHERE IdTransaccion > ? GROUP BY RadicadoZeus)", (self.id_inicial,))]
        excepciones = self.con.execute("SELECT COUNT(*) FROM Excepciones WHERE Id > ?", (self.id_excepciones_inicial,)).fetchone()[0]
        duracion = int((self.reloj() - self.inicio).total_seconds())
        fila = (self._ahora(), len(estados), estados.count(3), estados.count(4), estados.count(5), excepciones, duracion, detalle)
        self.con.execute("INSERT INTO LogEjecucion (Fecha, CasosProcesados, Exitosos, NoExitosos, Parciales, Excepciones, "
                         "DuracionSegundos, Detalle) VALUES (?,?,?,?,?,?,?,?)", fila)
        self.con.commit()
        self.corrida_cerrada = True
        return fila

    # consultas de revisión (specs/repositorio-local.md)
    def etapa_actual_por_caso(self):
        filas = self.con.execute(
            "SELECT RadicadoZeus, Etapa, EstadoNuevo FROM Transacciones WHERE IdTransaccion IN "
            "(SELECT MAX(IdTransaccion) FROM Transacciones GROUP BY RadicadoZeus) ORDER BY RadicadoZeus").fetchall()
        return [tuple(f) for f in filas]

    def conteo_por_estado(self):
        filas = self.con.execute(
            "SELECT EstadoNuevo, COUNT(*) FROM Transacciones WHERE IdTransaccion IN "
            "(SELECT MAX(IdTransaccion) FROM Transacciones GROUP BY RadicadoZeus) GROUP BY EstadoNuevo").fetchall()
        return {ESTADOS[f[0]]: f[1] for f in filas}

    def transiciones_fallidas(self):
        return [tuple(f) for f in self.con.execute(
            "SELECT RadicadoZeus, Etapa, Motivo FROM Transacciones WHERE Resultado = 'fallo' ORDER BY IdTransaccion").fetchall()]

    def recorrido(self, radicado):
        return [tuple(f) for f in self.con.execute(
            "SELECT Etapa, EstadoAnterior, EstadoNuevo, Resultado, Motivo FROM Transacciones WHERE RadicadoZeus = ? ORDER BY IdTransaccion",
            (str(radicado),)).fetchall()]
