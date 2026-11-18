"""Punto de entrada del Sistema de Gestión Logística y Distribución.

Se ejecuta como módulo, desde la carpeta que contiene Backend/:

    python -m Backend.main                # menú interactivo
    python -m Backend.main --resumen      # imprime el estado y termina
    python -m Backend.main --db otra.db   # usa otra base de datos

En la primera ejecución, con la base vacía, se cargan datos de demostración.
Las siguientes ejecuciones conservan lo guardado y no repiten la carga.
"""

import argparse
from pathlib import Path

from .consola import ejecutar_menu, mostrar_flota, mostrar_inventario, mostrar_pedidos
from .flota import FlotaSQLite
from .modelos.conductor import Conductor
from .modelos.deposito import Deposito
from .modelos.productos import Producto
from .modelos.vehiculo import Vehiculo
from .persistencia import InventarioSQLite

RUTA_DB_POR_DEFECTO = Path(__file__).with_name("logistica.db")


def cargar_datos_demo(inventario):
    """Carga productos, depósitos, existencias y flota si la base está vacía.

    Volumen en metros cúbicos y peso en kilogramos. Cada parte se carga solo
    si todavía no hay datos de su tipo, así que es seguro llamarla siempre.

    Args:
        inventario (InventarioSQLite): Sesión abierta que se reutiliza.

    Returns:
        bool: True si se cargaron datos de demostración; False si ya había.
    """
    productos = [
        Producto("PRD-1", "Pantalón", 0.004, 0.5),
        Producto("PRD-2", "Campera", 0.008, 0.9),
        Producto("PRD-3", "Remera", 0.002, 0.2),
        Producto("PRD-4", "Buzo Space Monochrome", 0.006, 0.6),
    ]
    depositos = [
        Deposito("D-001", "Depósito Centro", "Centro, Bariloche", 50.0),
        Deposito("D-002", "Depósito Melipal", "Melipal, Bariloche", 30.0),
        Deposito("D-003", "Depósito Dina Huapi", "Dina Huapi", 20.0),
    ]
    existencias = [
        ("D-001", "PRD-1", 200), ("D-001", "PRD-2", 100),
        ("D-001", "PRD-3", 300), ("D-001", "PRD-4", 150),
        ("D-002", "PRD-1", 100), ("D-002", "PRD-3", 200),
        ("D-003", "PRD-4", 80),
    ]
    cargado = inventario.cargar_iniciales(productos, depositos, existencias)

    flota = FlotaSQLite(inventario)
    if not flota.listar_vehiculos() and not flota.listar_conductores():
        for patente, capacidad in (("AB123CD", 3.0), ("EF456GH", 2.5), ("IJ789KL", 20.0)):
            flota.registrar_vehiculo(Vehiculo(patente, capacidad))
        for dni, nombre in (("28555111", "Juan Pérez"), ("30111222", "Carlos Gómez"),
                            ("31333444", "Ana Silva")):
            flota.registrar_conductor(Conductor(dni, nombre))
        flota.asignar_conductor("AB123CD", "28555111")
        flota.asignar_conductor("EF456GH", "30111222")
        flota.asignar_conductor("IJ789KL", "31333444")
        cargado = True

    if cargado:
        print("Datos de demostración cargados.")
    return cargado


def _leer_argumentos(argv):
    """Interpreta los argumentos de la línea de comandos.

    Args:
        argv (list[str] | None): Argumentos; None usa los de sys.argv.

    Returns:
        argparse.Namespace: Atributos db (ruta) y resumen (bool).
    """
    parser = argparse.ArgumentParser(
        prog="python -m Backend.main",
        description="Sistema de Gestión Logística y Distribución.",
    )
    parser.add_argument("--db", default=RUTA_DB_POR_DEFECTO,
                        help="archivo SQLite a usar (por defecto, Backend/logistica.db)")
    parser.add_argument("--resumen", action="store_true",
                        help="imprime inventario, pedidos y flota, y termina")
    return parser.parse_args(argv)


def main(argv=None):
    """Abre la base, prepara los datos de demostración y lanza el programa.

    La conexión se cierra al salir, incluso ante errores.

    Args:
        argv (list[str] | None): Argumentos; None usa los de sys.argv.
    """
    argumentos = _leer_argumentos(argv)
    with InventarioSQLite(argumentos.db) as inventario:
        cargar_datos_demo(inventario)
        if argumentos.resumen:
            mostrar_inventario(inventario)
            mostrar_pedidos(inventario)
            mostrar_flota(inventario)
        else:
            print("--- SISTEMA DE GESTIÓN LOGÍSTICA ---")
            ejecutar_menu(inventario)


if __name__ == "__main__":
    main()
