"""Inventario persistente y simulación opcional de distribución."""

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Backend.modelos.conductor import Conductor
from Backend.modelos.deposito import Deposito
from Backend.modelos.pedido import Pedido
from Backend.modelos.productos import Producto
from Backend.modelos.vehiculo import Vehiculo
from Backend.persistencia import InventarioSQLite
from Backend.pedidos import PedidosSQLite
from Backend.flota import FlotaSQLite


RUTA_DB = Path(__file__).resolve().with_name("logistica.db")


def cargar_ejemplo(inventario):
    return inventario.cargar_iniciales(
        [Producto("PRD-1", "Cajas de Leche", 0.5, 1.0),
         Producto("PRD-2", "Bolsas de Harina", 0.2, 0.5)],
        [Deposito("D-001", "Base Bariloche", "Ruta 40 Sur", 1000.0),
         Deposito("D-002", "Depósito Centro", "Mitre 100", 500.0)],
        [("D-001", "PRD-1", 500), ("D-001", "PRD-2", 800),
         ("D-002", "PRD-1", 100)],
    )


def mostrar_inventario(inventario):
    productos = inventario.listar_productos()
    for deposito in inventario.listar_depositos():
        print(f"\n{deposito.id_deposito} — {deposito.nombre}")
        print(f"Volumen ocupado: {deposito.volumen_ocupado:g} / {deposito.capacidad_maxima:g}")
        for producto in productos:
            cantidad = inventario.stock(deposito.id_deposito, producto.id_producto)
            reservado = inventario.stock_reservado(deposito.id_deposito, producto.id_producto)
            print(f"  {producto.id_producto} — {producto.nombre}: físico: {cantidad}, "
                  f"reservado: {reservado}, disponible: {cantidad - reservado}")
    print("\n--- Totales por producto ---")
    for producto in productos:
        print(f"{producto.nombre}: {inventario.stock_total(producto.id_producto)} unidades")


def simular_pedidos(inventario):
    print("\n--- SIMULACIÓN: no modifica el inventario guardado ---")
    try:
        inventario.obtener_deposito("D-001")
        productos = {id_: inventario.obtener_producto(id_) for id_ in ("PRD-1", "PRD-2")}
    except ValueError:
        print("La simulación necesita el depósito D-001 y los productos PRD-1 y PRD-2.")
        return
    stock_simulado = {id_: inventario.stock_disponible("D-001", id_) for id_ in productos}
    flota = [Vehiculo("AB123CD", 20.0), Vehiculo("EF456GH", 10.0)]
    conductores = [Conductor("30111222", "Carlos Gómez"),
                   Conductor("31333444", "Ana Silva")]
    for vehiculo, conductor in zip(flota, conductores):
        vehiculo.asignar_conductor(conductor.nombre)
        conductor.asignar_vehiculo(vehiculo.patente)

    escenarios = [
        (Pedido("P-100", "Supermercado Sur", "Av. Pioneros 4500", 2),
         [("PRD-1", 20), ("PRD-2", 30)]),
        (Pedido("P-101", "Despensa Centro", "Mitre 200", 1), [("PRD-1", 50)]),
    ]
    for pedido, items in escenarios:
        if any(stock_simulado[id_] < cantidad for id_, cantidad in items):
            print(f"Stock insuficiente para simular el pedido {pedido.id_pedido}.")
            continue
        for id_, cantidad in items:
            producto = productos[id_]
            stock_simulado[id_] -= cantidad
            pedido.agregar_producto(producto.nombre, cantidad, producto.volumen_unitario)
        for vehiculo in flota:
            espacio = vehiculo.capacidad_maxima - vehiculo.volumen_ocupado
            if vehiculo.estado == "Disponible" and espacio >= pedido.volumen_total:
                vehiculo.asignar_pedido(pedido)
                break
        else:
            print(f"Alerta: No se encontró vehículo con capacidad suficiente para el pedido {pedido.id_pedido}.")
    print("\n--- Stock disponible simulado de D-001 (sin guardar) ---")
    for id_, cantidad in stock_simulado.items():
        print(f"{productos[id_].nombre}: {cantidad} unidades")
    print("\n--- Conductores de la simulación ---")
    for conductor in conductores:
        print(conductor.obtener_info())


def mostrar_flota(inventario):
    flota = FlotaSQLite(inventario)
    print("\n--- Vehículos guardados ---")
    vehiculos = flota.listar_vehiculos()
    if not vehiculos:
        print("No hay vehículos guardados.")
    for vehiculo in vehiculos:
        conductor = vehiculo.conductor_asignado or "sin asignar"
        print(f"{vehiculo.patente}: {vehiculo.estado}, "
              f"capacidad: {vehiculo.capacidad_maxima:g}, conductor DNI: {conductor}, "
              f"pedido activo: {vehiculo.pedido_asignado or 'ninguno'}, "
              f"carga: {vehiculo.volumen_ocupado:g}")
    print("\n--- Conductores guardados ---")
    conductores = flota.listar_conductores()
    if not conductores:
        print("No hay conductores guardados.")
    for conductor in conductores:
        print(f"{conductor.dni} — {conductor.nombre}: {conductor.estado}, "
              f"vehículo: {conductor.vehiculo_asignado or 'sin asignar'}")


def main():
    parser = argparse.ArgumentParser(description="Inventario logístico persistente en SQLite.")
    parser.add_argument("--db", type=Path, default=RUTA_DB, help="Ruta del archivo SQLite.")
    parser.add_argument("--simular-pedidos", action="store_true",
                        help="Ejecuta la demo logística sin modificar las existencias guardadas.")
    opciones = parser.parse_args()
    with InventarioSQLite(opciones.db) as inventario:
        print("--- SISTEMA DE GESTIÓN LOGÍSTICA ---")
        print(f"Base de datos: {opciones.db.resolve()}")
        if cargar_ejemplo(inventario):
            print("Inventario vacío: se cargaron los datos de ejemplo.")
        else:
            print("Se recuperó el inventario guardado.")
        mostrar_inventario(inventario)
        print("\n--- Pedidos guardados ---")
        pedidos = PedidosSQLite(inventario).listar_pedidos()
        if not pedidos:
            print("No hay pedidos guardados.")
        for pedido in pedidos:
            print(f"{pedido.id_pedido} — {pedido.cliente}: {pedido.estado}, "
                  f"volumen: {pedido.volumen_total:g}, "
                  f"vehículo: {pedido.vehiculo_asignado or 'sin asignar'}")
        mostrar_flota(inventario)
        if opciones.simular_pedidos:
            simular_pedidos(inventario)


if __name__ == "__main__":
    main()
