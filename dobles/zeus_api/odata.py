"""Evaluación mínima de OData v4 para el doble: $filter (eq, ne, and), $select, $first, $orderby.

Un campo inexistente o una sintaxis mal formada levanta ErrorOData (el servidor responde 400, como el manual).
"""
import re


class ErrorOData(ValueError):
    pass


_COMPARACION = re.compile(r"^\s*([A-Za-z0-9_]+)\s+(eq|ne)\s+'((?:[^']|'')*)'\s*$")
_Y = re.compile(r"\s+and\s+", re.IGNORECASE)


def parsear_filtro(texto, campos):
    condiciones = []
    for parte in _Y.split(texto):
        m = _COMPARACION.match(parte)
        if not m:
            raise ErrorOData(f"filtro mal formado: {parte!r}")
        campo, operador, valor = m.group(1), m.group(2), m.group(3).replace("''", "'")
        if campo not in campos:
            raise ErrorOData(f"campo inexistente en $filter: {campo}")
        condiciones.append((campo, operador, valor))
    return condiciones


def cumple(registro, condiciones):
    for campo, operador, valor in condiciones:
        igual = registro.get(campo) == valor
        if (operador == "eq") != igual:
            return False
    return True


def parsear_select(texto, campos):
    elegidos = [c.strip() for c in texto.split(",") if c.strip()]
    for campo in elegidos:
        if campo not in campos:
            raise ErrorOData(f"campo inexistente en $select: {campo}")
    return elegidos


def parsear_orderby(texto, campos):
    partes = texto.split()
    if not partes or len(partes) > 2 or (len(partes) == 2 and partes[1].lower() not in ("asc", "desc")):
        raise ErrorOData(f"$orderby mal formado: {texto!r}")
    if partes[0] not in campos:
        raise ErrorOData(f"campo inexistente en $orderby: {partes[0]}")
    return partes[0], len(partes) == 2 and partes[1].lower() == "desc"


def parsear_first(texto):
    if not texto.isdigit():
        raise ErrorOData(f"$first mal formado: {texto!r}")
    return int(texto)


def aplicar(registros, parametros, campos):
    """parametros: dict con claves opcionales '$filter', '$select', '$first', '$orderby' (valores str)."""
    for clave in parametros:
        if clave not in ("$filter", "$select", "$first", "$orderby"):
            raise ErrorOData(f"parámetro OData no soportado: {clave}")
    salida = list(registros)
    if "$filter" in parametros:
        condiciones = parsear_filtro(parametros["$filter"], campos)
        salida = [r for r in salida if cumple(r, condiciones)]
    if "$orderby" in parametros:
        campo, descendente = parsear_orderby(parametros["$orderby"], campos)
        salida.sort(key=lambda r: (r.get(campo) is None, r.get(campo)), reverse=descendente)
    if "$first" in parametros:
        salida = salida[: parsear_first(parametros["$first"])]
    if "$select" in parametros:
        elegidos = parsear_select(parametros["$select"], campos)
        salida = [{c: r.get(c) for c in elegidos} for r in salida]
    return salida
