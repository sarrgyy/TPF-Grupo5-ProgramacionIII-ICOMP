"""Comprueba reservas, stock y recursos durante el ciclo persistente de pedidos."""
import sqlite3

import pytest

from Backend.flota import FlotaSQLite
from Backend.pedidos import PedidosSQLite, StockInsuficiente


def borrador(inv, identificador="P", cantidad=2):
    """Crea un pedido con un ítem para probar sus transiciones persistentes.

    Args:
        inv (InventarioSQLite): Sesión temporal compartida.
        identificador (str): ID del nuevo borrador.
        cantidad (int): Unidades de P1 solicitadas desde D1.

    Returns:
        PedidosSQLite: Repositorio de la sesión con el pedido preparado.
    """
    p = PedidosSQLite(inv)
    p.crear_borrador(identificador, "Cliente", "Destino")
    p.establecer_producto(identificador, "D1", "P1", cantidad)
    return p


def test_faltantes_conservan_borrador(inventario):
    """Verifica faltantes completos sin perder ítems ni crear reservas parciales."""
    p = borrador(inventario, cantidad=201)
    with pytest.raises(StockInsuficiente) as error:
        p.confirmar("P")
    assert error.value.faltantes[0]["faltan"] == 1
    assert p.obtener_pedido("P").estado == "Borrador"
    assert p.obtener_pedido("P").productos[0]["cantidad"] == 201
    assert inventario.stock_reservado("D1", "P1") == 0


def test_cancelar_libera_reservas(inventario):
    """Comprueba que cancelar libere reservas sin descontar stock físico."""
    p = borrador(inventario)
    p.confirmar("P")
    assert inventario.stock_reservado("D1", "P1") == 2
    p.cancelar("P")
    assert inventario.stock_reservado("D1", "P1") == 0
    assert inventario.stock("D1", "P1") == 200


def test_vehiculo_no_admite_dos_pedidos(inventario):
    """Verifica la exclusión de dos pedidos activos sobre el mismo vehículo."""
    p = borrador(inventario)
    p.confirmar("P")
    borrador(inventario, "Q")
    p.confirmar("Q")
    p.asignar_vehiculo("P", "AA123BB")
    with pytest.raises(ValueError):
        p.asignar_vehiculo("Q", "AA123BB")
    assert p.obtener_pedido("Q").vehiculo_asignado is None


def test_despacho_descuenta_una_vez(inventario):
    """Comprueba descuento único de stock y paso del vehículo a En Ruta."""
    p = borrador(inventario)
    p.confirmar("P")
    p.asignar_vehiculo("P", "AA123BB")
    p.despachar("P")
    assert inventario.stock("D1", "P1") == 198
    assert inventario.stock_reservado("D1", "P1") == 0
    assert FlotaSQLite(inventario).obtener_vehiculo("AA123BB").estado == "En Ruta"
    with pytest.raises(ValueError):
        p.despachar("P")
    assert inventario.stock("D1", "P1") == 198


def test_entrega_libera_vehiculo(inventario):
    """Verifica que entregar finalice el pedido y libere el vehículo."""
    p = borrador(inventario)
    p.confirmar("P")
    p.asignar_vehiculo("P", "AA123BB")
    p.despachar("P")
    p.entregar("P")
    vehiculo = FlotaSQLite(inventario).obtener_vehiculo("AA123BB")
    assert p.obtener_pedido("P").estado == "Entregado"
    assert vehiculo.estado == "Disponible"
    assert vehiculo.pedido_asignado is None


def test_reservas_protegen_retiros(inventario):
    """Comprueba que un retiro no consuma unidades reservadas."""
    p = borrador(inventario, cantidad=199)
    p.confirmar("P")
    with pytest.raises(ValueError):
        inventario.actualizar_stock("D1", "P1", -2)
    assert inventario.stock("D1", "P1") == 200


def test_fallo_de_despacho_revierte_toda_la_transaccion(inventario):
    """Verifica rollback de stock, reservas y estado ante un fallo de despacho."""
    p = borrador(inventario)
    p.confirmar("P")
    p.asignar_vehiculo("P", "AA123BB")
    inventario.conexion.execute("""CREATE TRIGGER impedir_ruta BEFORE UPDATE OF estado ON vehiculos
        WHEN NEW.estado = 'En Ruta' BEGIN SELECT RAISE(ABORT, 'fallo simulado'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        p.despachar("P")
    assert p.obtener_pedido("P").estado == "Confirmado"
    assert inventario.stock("D1", "P1") == 200
    assert inventario.stock_reservado("D1", "P1") == 2


@pytest.mark.parametrize("cantidad", [0, -1, 1.5, True, 2**63])
def test_items_invalidos_no_se_guardan(inventario, cantidad):
    """Comprueba el rechazo de cantidades inválidas sin guardar ítems."""
    p = PedidosSQLite(inventario)
    p.crear_borrador("P", "Cliente", "Destino")
    with pytest.raises(ValueError):
        p.establecer_producto("P", "D1", "P1", cantidad)
    assert p.obtener_pedido("P").productos == []
