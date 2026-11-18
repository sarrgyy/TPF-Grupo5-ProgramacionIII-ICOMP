"""Comparte validaciones de medidas entre modelos y persistencia."""
import math


def validar_medida(valor, *, permitir_cero=False):
    """Valida que una medida sea numérica, finita y del signo admitido.

    Args:
        valor (object): Número entero o flotante que se debe comprobar.
        permitir_cero (bool): Admite cero si es True; por defecto, False.

    Raises:
        ValueError: El valor es booleano, no numérico, no finito o no cumple
            el signo requerido; incluye enteros fuera del rango flotante.
    """
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError("Las medidas deben ser números finitos.")
    try:
        finito = math.isfinite(valor)
    except OverflowError:
        finito = False
    if not finito or valor < 0 or (valor == 0 and not permitir_cero):
        raise ValueError("La medida debe ser positiva y finita." if not permitir_cero else "La medida debe ser no negativa y finita.")
