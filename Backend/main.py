"""Punto de entrada del Sistema de Gestión Logística y Distribución.

Se ejecuta como módulo, desde la carpeta que contiene Backend/:

    python -m Backend.main                # menú interactivo
    python -m Backend.main --resumen      # imprime el estado y termina
    python -m Backend.main --db otra.db   # usa otra base de datos

La primera inicialización carga tres registros de cada entidad desde schema.sql.
Los siguientes arranques conservan los datos sin reponerlos.
"""

import argparse
from pathlib import Path

from .consola import ejecutar_menu, mostrar_flota, mostrar_inventario, mostrar_pedidos
from .persistencia import InventarioSQLite

RUTA_DB_POR_DEFECTO = Path(__file__).with_name("logistica.db")


def cargar_datos_base(inventario):
    """Carga los valores de schema.sql una sola vez e informa el resultado.

    Args:
        inventario (InventarioSQLite): Sesión abierta, fuera de una transacción.

    Returns:
        bool: True si se insertaron valores; False si ya se inicializó o había datos.

    Raises:
        ValueError: La sesión tiene una transacción activa.
        sqlite3.Error: Falló la carga; se revierten sus cambios.
    """
    cargado = inventario.cargar_datos_base()
    if cargado:
        print("Datos base iniciales cargados.")
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
    """Abre la base, inicializa sus valores una sola vez y lanza el programa.

    La conexión se cierra al salir, incluso ante errores.

    Args:
        argv (list[str] | None): Argumentos; None usa los de sys.argv.
    """
    argumentos = _leer_argumentos(argv)
    with InventarioSQLite(argumentos.db) as inventario:
        cargar_datos_base(inventario)
        if argumentos.resumen:
            mostrar_inventario(inventario)
            mostrar_pedidos(inventario)
            mostrar_flota(inventario)
        else:
            print("--- SISTEMA DE GESTIÓN LOGÍSTICA ---")
            ejecutar_menu(inventario)


if __name__ == "__main__":
    main()
