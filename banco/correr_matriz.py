"""Banco determinista: corre la matriz de escenarios de una épica contra el doble local, N veces, y compara.

Uso:  python banco/correr_matriz.py EP-001 [--corridas 2]
Por escenario: levanta un doble limpio, copia la configuración a una raíz temporal, ejecuta el robot (procesar),
verifica las expectativas y guarda el resultado normalizado. La matriz pasa si todas las expectativas se cumplen
y las N corridas producen resultados idénticos (determinismo). Salida: banco/resultados/<épica>_corrida<N>.json.

El banco valida flujo y orquestación contra dobles; NO valida la veracidad de los sistemas reales.
"""
import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for carpeta in (REPO, REPO / "Scripts", REPO / "dobles" / "zeus_api"):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

from habeasdata import ep001  # noqa: E402
from habeasdata.config import cargar  # noqa: E402
from habeasdata.registro import Registro  # noqa: E402
from habeasdata.zeus import ClienteZeus  # noqa: E402
from dobles.zeus_api.servidor import DobleZeus  # noqa: E402

CREDENCIALES = ("cliente-banco", "secreto-banco-no-real")
ENTORNO = {"ZEUS_DOBLE_CLIENT_ID": CREDENCIALES[0], "ZEUS_DOBLE_CLIENT_SECRET": CREDENCIALES[1]}
RADICADOS = json.loads((REPO / "fixtures" / "zeus" / "radicados.json").read_text(encoding="utf-8"))
RELOJ = lambda: datetime(2026, 10, 29, 9, 30, 0)  # noqa: E731


def radicados_de(especificacion):
    if especificacion == "todos":
        return list(RADICADOS)
    if especificacion == []:
        return []
    if especificacion == ["ajeno"]:
        return [dict(r, PQRCORRESPONDEA="HABEAS DATA - NO APLICA") for r in RADICADOS[:3]]
    return [r for r in RADICADOS if str(r["IDRADICADO"]) in set(especificacion)]


def mezclar(destino, cambios):
    for clave, valor in cambios.items():
        if isinstance(valor, dict) and isinstance(destino.get(clave), dict):
            mezclar(destino[clave], valor)
        else:
            destino[clave] = valor


def preparar_raiz(puerto, cambios_proceso):
    raiz = Path(tempfile.mkdtemp(prefix="banco_hd_"))
    shutil.copytree(REPO / "Configuracion", raiz / "Configuracion")
    ruta = raiz / "Configuracion" / "ConfiguracionProceso.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    for clave in ("UrlBase", "UrlToken", "UrlComentario"):
        datos["ZeusApi"]["Fixture"][clave] = datos["ZeusApi"]["Fixture"][clave].replace("8765", str(puerto))
    datos["ZeusApi"]["BackoffSegundos"] = [0]
    mezclar(datos, cambios_proceso)
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return raiz


def correr_escenario(escenario):
    especificacion = escenario["doble"]
    doble = DobleZeus(CREDENCIALES, radicados_de(especificacion["radicados"])).iniciar()
    raiz = preparar_raiz(doble.puerto, escenario.get("proceso", {}))
    try:
        doble.estado.configurar({k: v for k, v in especificacion.items() if k in ("token_ttl", "denegar", "fallas_radicado", "falla_comentario")})
        if especificacion.get("apagado"):
            doble.detener()
        cfg = cargar(raiz)
        registro = Registro(cfg, RELOJ)
        cliente = ClienteZeus(cfg, registro, ENTORNO, dormir=lambda segundos: None)
        resumen = ep001.procesar(cfg, cliente, registro)
        comentarios = sorted(c["IDRADICADO"] for c in doble.estado.comentarios)
        archivos = sorted(p.relative_to(raiz).as_posix() for p in raiz.rglob("*.csv"))
        lineas_auditoria = registro.ruta_auditoria().read_text(encoding="utf-8").count("\n")
        return resumen, comentarios, archivos, lineas_auditoria, cliente.modo
    finally:
        if not especificacion.get("apagado"):
            doble.detener()
        shutil.rmtree(raiz, ignore_errors=True)


def verificar(escenario, resumen, comentarios, archivos):
    espera, fallos = escenario["espera"], []

    def igual(nombre, real, esperado):
        if real != esperado:
            fallos.append(f"{nombre}: esperado {esperado!r}, real {real!r}")

    igual("estado", resumen["estado"], espera["estado"])
    for clave in ("avanzan", "excepciones_negocio_1", "excepciones_sistema"):
        if clave in espera:
            igual(clave, sorted(resumen[clave]), sorted(espera[clave]))
    if "motivo_sin_casos" in espera:
        igual("motivo_sin_casos", resumen["motivo_sin_casos"], espera["motivo_sin_casos"])
    if "comentarios" in espera:
        igual("comentarios", comentarios, sorted(espera["comentarios"]))
    if "reintento_minutos" in espera:
        igual("reintento_minutos", (resumen["reintento"] or {}).get("MinutosEntreReintentos"), espera["reintento_minutos"])
    if "notificacion_asunto" in espera:
        igual("notificacion_asunto", (resumen["notificacion"] or {}).get("asunto"), espera["notificacion_asunto"])
    for excluido in espera.get("avanzan_no_incluye", []):
        if excluido in resumen["avanzan"]:
            fallos.append(f"{excluido} no debía avanzar")
    for id_radicado, campos in espera.get("casos", {}).items():
        caso = resumen["casos"].get(id_radicado, {})
        for campo, valor in campos.items():
            igual(f"casos[{id_radicado}].{campo}", caso.get(campo), valor)
    # Lineamientos observables en cada escenario: dos logs y reporte, sólo CSV esperados.
    nombres = " ".join(archivos)
    if "LOG_DE_AUDITORIA" not in nombres or "LOG_DE_ERRORES" not in nombres:
        fallos.append("faltan los dos archivos de log del día")
    return fallos


def una_corrida(escenarios):
    resultados = []
    for escenario in escenarios:
        resumen, comentarios, archivos, lineas, modo = correr_escenario(escenario)
        fallos = verificar(escenario, resumen, comentarios, archivos)
        normalizado = json.dumps({"modo": modo, "resumen": resumen, "comentarios": comentarios, "archivos": archivos,
                                  "lineas_auditoria": lineas}, sort_keys=True, ensure_ascii=False, default=str)
        resultados.append({"id": escenario["id"], "modo": modo, "ramas": escenario["ramas"], "paso": not fallos, "fallos": fallos,
                           "huella": hashlib.sha256(normalizado.encode("utf-8")).hexdigest()})
    return resultados


def principal():
    analizador = argparse.ArgumentParser()
    analizador.add_argument("epica")
    analizador.add_argument("--corridas", type=int, default=2)
    argumentos = analizador.parse_args()
    escenarios = json.loads((REPO / "banco" / "escenarios" / f"{argumentos.epica}.json").read_text(encoding="utf-8"))
    corridas = [una_corrida(escenarios) for _ in range(argumentos.corridas)]
    (REPO / "banco" / "resultados").mkdir(exist_ok=True)
    for numero, resultados in enumerate(corridas, 1):
        ruta = REPO / "banco" / "resultados" / f"{argumentos.epica}_corrida{numero}.json"
        ruta.write_text(json.dumps(resultados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    todos_pasan = all(r["paso"] for corrida in corridas for r in corrida)
    huellas = [[r["huella"] for r in corrida] for corrida in corridas]
    deterministas = all(h == huellas[0] for h in huellas)
    for resultado in corridas[0]:
        print(("PASA " if resultado["paso"] else "FALLA") + f" {resultado['id']}  {'; '.join(resultado['fallos'])}")
    print(f"MODO FIXTURE (doble offline, sin red; NO es la API real de CISA)")
    print(f"escenarios: {len(escenarios)}  corridas: {len(corridas)}  todos pasan: {todos_pasan}  "
          f"determinismo (huellas idénticas entre corridas): {deterministas}")
    return 0 if todos_pasan and deterministas else 1


if __name__ == "__main__":
    sys.exit(principal())
