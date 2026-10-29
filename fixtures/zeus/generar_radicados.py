"""Genera fixtures/zeus/radicados.json: radicados 100 % sintéticos, uno por borde de EP-001.

Ejecutar desde la raíz del repositorio:  python fixtures/zeus/generar_radicados.py
Nombres inventados, cédulas ficticias, correos en dominio .invalid. Cero PII.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "dobles" / "zeus_api"))
from campos import CAMPOS  # noqa: E402

EXCLUSION = "EXCLUSION DE DATOS"
AUSENTE = "NO APORTA"

# Valores base: cada radicado sobreescribe lo que le interesa.
BASE = {
    "EstadoActual": "PENDIENTE REALIZAR GESTION EN BASE DE DATOS DE COBRANZA",
    "TIPOLOGIADEPQR": "PETICION",
    "PQRCORRESPONDEA": EXCLUSION,
    "TIPODEIDENTIFICACION": "CEDULA DE CIUDADANIA",
    "CANALCONTACTOHABEAS": "CORREO ELECTRONICO",
    "FECHADERECEPCION": "21/08/2026",
    "ENTIDADORIGINADORA": "NO APLICA",
    "ESCLIENTEREITERATIVO": "NO",
    "MEDIODEENVIORESPUESTAHABEAS": "CORREO ELECTRONICO",
}

# (IDRADICADO, borde, sobreescrituras)
CASOS = [
    (900001, "completo: correo + celular", {
        "Alias": "CASO COMPLETO", "NOMBREDELCLIENTE": "MARIA FERNANDA LOPEZ RUIZ",
        "NOIDENTIFICACIONDELCLIENTE": "1000000001",
        "CORREOELECTRONICOPARAEXCLUSION": "maria.lopez@ejemplo.invalid", "TELEFONODECONTACTO": "3101234567"}),
    (900002, "sin ningun canal", {
        "Alias": "SIN CANAL", "NOMBREDELCLIENTE": "JUAN PABLO ARIAS SOTO",
        "NOIDENTIFICACIONDELCLIENTE": "1000000002",
        "CORREOELECTRONICOPARAEXCLUSION": AUSENTE, "TELEFONODECONTACTO": AUSENTE}),
    (900003, "solo correo", {
        "Alias": "SOLO CORREO", "NOMBREDELCLIENTE": "ANA LUCIA MORA PEREZ",
        "NOIDENTIFICACIONDELCLIENTE": "1000000003",
        "CORREOELECTRONICOPARAEXCLUSION": "ana.mora@ejemplo.invalid", "TELEFONODECONTACTO": AUSENTE}),
    (900004, "solo celular", {
        "Alias": "SOLO CELULAR", "NOMBREDELCLIENTE": "CARLOS ANDRES RIOS DIAZ",
        "NOIDENTIFICACIONDELCLIENTE": "1000000004",
        "CORREOELECTRONICOPARAEXCLUSION": AUSENTE, "TELEFONODECONTACTO": "3209876543"}),
    (900005, "telefono fijo (7 digitos)", {
        "Alias": "FIJO", "NOMBREDELCLIENTE": "LAURA SOFIA VEGA NIETO",
        "NOIDENTIFICACIONDELCLIENTE": "1000000005",
        "CORREOELECTRONICOPARAEXCLUSION": AUSENTE, "TELEFONODECONTACTO": "4441234"}),
    (900006, "telefono sin clasificar (10 digitos que no inician en 3)", {
        "Alias": "SIN CLASIFICAR", "NOMBREDELCLIENTE": "PEDRO LUIS CANO MEJIA",
        "NOIDENTIFICACIONDELCLIENTE": "1000000006",
        "CORREOELECTRONICOPARAEXCLUSION": AUSENTE, "TELEFONODECONTACTO": "2101234567"}),
    (900007, "varios valores separados por /", {
        "Alias": "MULTIVALOR", "NOMBREDELCLIENTE": "SOFIA ELENA RAMOS TORO",
        "NOIDENTIFICACIONDELCLIENTE": "1000000007",
        "CORREOELECTRONICOPARAEXCLUSION": "sofia.a@ejemplo.invalid/sofia.b@ejemplo.invalid",
        "TELEFONODECONTACTO": "3101234567/3209876543/4441234"}),
    (900008, "con radicado padre", {
        "Alias": "CON PADRE", "NOMBREDELCLIENTE": "DIEGO ALEJANDRO PINTO LEAL",
        "NOIDENTIFICACIONDELCLIENTE": "1000000008", "RadicadoPadre": "800001",
        "CORREOELECTRONICOPARAEXCLUSION": "diego.pinto@ejemplo.invalid", "TELEFONODECONTACTO": AUSENTE}),
    (900009, "nombre en blanco", {
        "Alias": "NOMBRE EN BLANCO", "NOMBREDELCLIENTE": "   ",
        "NOIDENTIFICACIONDELCLIENTE": "1000000009",
        "CORREOELECTRONICOPARAEXCLUSION": "anonimo@ejemplo.invalid", "TELEFONODECONTACTO": AUSENTE}),
    (900010, "tipo de identificacion ausente", {
        "Alias": "SIN TIPO ID", "NOMBREDELCLIENTE": "VALERIA ISABEL CRUZ ORTIZ",
        "TIPODEIDENTIFICACION": AUSENTE, "NOIDENTIFICACIONDELCLIENTE": "1000000010",
        "CORREOELECTRONICOPARAEXCLUSION": "valeria.cruz@ejemplo.invalid", "TELEFONODECONTACTO": AUSENTE}),
    (900011, "numero de identificacion ausente", {
        "Alias": "SIN NUMERO ID", "NOMBREDELCLIENTE": "ANDRES FELIPE SILVA RUEDA",
        "NOIDENTIFICACIONDELCLIENTE": AUSENTE,
        "CORREOELECTRONICOPARAEXCLUSION": "andres.silva@ejemplo.invalid", "TELEFONODECONTACTO": AUSENTE}),
    (900012, "tipologia ajena (no es exclusion)", {
        "Alias": "AJENO", "PQRCORRESPONDEA": "HABEAS DATA - NO APLICA", "NOMBREDELCLIENTE": "RAUL EDUARDO PAEZ BRAVO",
        "NOIDENTIFICACIONDELCLIENTE": "1000000012",
        "CORREOELECTRONICOPARAEXCLUSION": "raul.paez@ejemplo.invalid", "TELEFONODECONTACTO": "3151112233"}),
    (900013, "NIT de 10 digitos, razon social", {
        "Alias": "NIT", "TIPODEIDENTIFICACION": "NIT", "NOMBREDELCLIENTE": "INVERSIONES LAB DEMO S A S",
        "NOIDENTIFICACIONDELCLIENTE": "9000000013",
        "CORREOELECTRONICOPARAEXCLUSION": "contacto@lab-demo.invalid", "TELEFONODECONTACTO": AUSENTE}),
    (900014, "nombre con apellidos primero", {
        "Alias": "NOMBRE INVERTIDO", "NOMBREDELCLIENTE": "TORRES GALINDO NATALIA",
        "NOIDENTIFICACIONDELCLIENTE": "1000000014",
        "CORREOELECTRONICOPARAEXCLUSION": "natalia.torres@ejemplo.invalid", "TELEFONODECONTACTO": AUSENTE}),
    (900015, "campos heredados con dato, telefono de contacto ausente y correo solo en OBSERVACIONES", {
        "Alias": "HEREDADOS", "NOMBREDELCLIENTE": "MARTA CECILIA BOTERO VARGAS",
        "NOIDENTIFICACIONDELCLIENTE": "1000000015",
        "CORREOELECTRONICOPARAEXCLUSION": AUSENTE, "TELEFONODECONTACTO": AUSENTE,
        "NODECELULARPARAEXCLUSION": "3134589654", "NOFIJOPARAEXCLUSION": "2695478",
        "OBSERVACIONES": "contacto: marta.botero@ejemplo.invalid"}),
    (900016, "ausente con otra capitalizacion (No aporta)", {
        "Alias": "NO APORTA MIXTO", "NOMBREDELCLIENTE": "OSCAR IVAN LEON PRADO",
        "NOIDENTIFICACIONDELCLIENTE": "1000000016",
        "CORREOELECTRONICOPARAEXCLUSION": "No aporta", "TELEFONODECONTACTO": "3174445566"}),
]


def construir():
    registros = []
    for id_radicado, _borde, cambios in CASOS:
        registro = {campo: None for campo in CAMPOS}
        registro.update(BASE)
        registro["IDRADICADO"] = id_radicado
        registro.update(cambios)
        registros.append(registro)
    return registros


if __name__ == "__main__":
    destino = RAIZ / "fixtures" / "zeus" / "radicados.json"
    destino.write_text(json.dumps(construir(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(CASOS)} radicados escritos en {destino.name}")
