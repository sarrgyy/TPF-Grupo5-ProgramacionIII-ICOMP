"""Demostración sin archivos: python -m ejemplos.simulacion_en_memoria.

Usa SQLite :memory: y las mismas reglas que la consola y la API.
"""
from Backend.consola import mostrar_flota, mostrar_pedidos
from Backend.main import cargar_datos_base
from Backend.pedidos import PedidosSQLite
from Backend.persistencia import InventarioSQLite


def main():
    """Ejecuta el circuito hasta Entregado en SQLite en memoria y muestra el resumen."""
    with InventarioSQLite(":memory:") as inv:
        cargar_datos_base(inv)
        pedidos = PedidosSQLite(inv)
        pedidos.crear_borrador("DEMO", "Cliente de demostración", "Centro, Bariloche")
        pedidos.establecer_producto("DEMO", "D-001", "PRD-1", 2)
        pedidos.confirmar("DEMO")
        pedidos.asignar_vehiculo("DEMO", "AB123CD")
        pedidos.despachar("DEMO")
        pedidos.entregar("DEMO")
        mostrar_pedidos(inv)
        mostrar_flota(inv)


if __name__ == "__main__":
    main()
