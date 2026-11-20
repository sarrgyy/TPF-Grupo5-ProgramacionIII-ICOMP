"""Puente entre la API Python y el motor de reglas SWI-Prolog."""
import json
import shutil
import subprocess
from pathlib import Path

RUTA_REGLAS = Path(__file__).with_name("razonamiento.pl")


class PrologNoDisponible(RuntimeError):
    """Señala que SWI-Prolog no está instalado o no se puede ejecutar."""


def recomendar_vehiculos(volumen_pedido, vehiculos):
    """Consulta Prolog y devuelve vehículos disponibles ordenados por ajuste.

    Prolog aplica las reglas de disponibilidad, conductor, ausencia de pedido
    activo y capacidad. Entre los compatibles prioriza el menor espacio sobrante.
    """
    ejecutable = shutil.which("swipl")
    if ejecutable is None:
        raise PrologNoDisponible(
            "No se encontró SWI-Prolog. Instalalo y asegurate de que 'swipl' "
            "esté disponible en PATH."
        )

    entrada = {
        "volumen_pedido": float(volumen_pedido),
        "vehiculos": [
            {
                "patente": v.patente,
                "capacidad_maxima": float(v.capacidad_maxima),
                "estado": v.estado,
                "tiene_conductor": v.conductor_asignado is not None,
                "tiene_pedido_activo": v.pedido_asignado is not None,
            }
            for v in vehiculos
        ],
    }
    try:
        proceso = subprocess.run(
            [ejecutable, "-q", "-s", str(RUTA_REGLAS), "-g", "main", "-t", "halt"],
            input=json.dumps(entrada), text=True, capture_output=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise PrologNoDisponible(f"No se pudo ejecutar SWI-Prolog: {error}") from error

    if proceso.returncode != 0:
        detalle = proceso.stderr.strip() or "Error desconocido en el motor Prolog."
        raise PrologNoDisponible(detalle)
    try:
        resultado = json.loads(proceso.stdout)
    except json.JSONDecodeError as error:
        raise PrologNoDisponible("Prolog devolvió una respuesta no válida.") from error
    return resultado
