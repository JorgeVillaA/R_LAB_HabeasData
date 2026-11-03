"""HU-008: comparación de nombres con umbral parametrizable, sobre el nombre normalizado y sin depender del orden.

Insumo B3 (decisión del agente, a aprobar por Villa): normalizar = quitar tildes, mayúsculas, solo letras, separar por
espacios y descartar partículas (DE, DEL, LA, LAS, LOS, Y). Score = coeficiente de Dice sobre los componentes del nombre
(2·|comunes| / (|A|+|B|)), sin importar el orden. Garantía de coincidencia plena (score 1.0): primer nombre + primer
apellido de la fuente más corta presentes en la más larga (el caso del origen), es decir, todos los componentes de un
nombre de al menos dos componentes están en el otro. Un nombre del portal con un solo componente no identifica a nadie:
va a excepción de negocio 3 cualquiera sea su score.
"""
import re
import unicodedata

PARTICULAS = {"DE", "DEL", "LA", "LAS", "LOS", "Y"}


def normalizar(nombre):
    sin_tildes = unicodedata.normalize("NFKD", str(nombre or "")).encode("ascii", "ignore").decode("ascii")
    componentes = re.sub(r"[^A-Za-z ]", " ", sin_tildes).upper().split()
    return [c for c in componentes if c not in PARTICULAS]


def puntaje(a, b):
    ca, cb = normalizar(a), normalizar(b)
    if not ca or not cb:
        return 0.0
    corto, largo = (ca, cb) if len(ca) <= len(cb) else (cb, ca)
    if len(corto) >= 2 and all(c in largo for c in corto):
        return 1.0
    restantes, comunes = list(cb), 0
    for c in ca:
        if c in restantes:
            restantes.remove(c)
            comunes += 1
    return round(2 * comunes / (len(ca) + len(cb)), 4)


def comparar(nombre_zeus, nombre_portal, umbral):
    """Veredicto de HU-008: {coincide, puntaje, motivo}. `umbral` viene de UMBRAL_COINCIDENCIA_NOMBRES."""
    if len(normalizar(nombre_portal)) < 2:
        return {"coincide": False, "puntaje": puntaje(nombre_zeus, nombre_portal), "motivo": "nombre del portal incompleto"}
    valor = puntaje(nombre_zeus, nombre_portal)
    return {"coincide": valor >= float(umbral), "puntaje": valor,
            "motivo": None if valor >= float(umbral) else "puntaje por debajo del umbral"}
