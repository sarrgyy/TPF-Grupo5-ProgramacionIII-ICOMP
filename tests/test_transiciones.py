"""Verifica transiciones por estado y pedidos con múltiples depósitos."""
import pytest

from Backend.flota import FlotaSQLite
from Backend.modelos.vehiculo import Vehiculo
from Backend.modelos.conductor import Conductor
from Backend.modelos.deposito import Deposito
from Backend.modelos.productos import Producto
from Backend.pedidos import StockInsuficiente
from Backend.pedidos import PedidosSQLite

PERMITIDOS = {
    "confirmar": {"Borrador"}, "cancelar": {"Borrador", "Confirmado"},
    "despachar": {"Confirmado"}, "entregar": {"Despachado"},
    "editar": {"Borrador"}, "item": {"Borrador"}, "quitar": {"Borrador"},
    "liberar": {"Confirmado"},
}


@pytest.mark.parametrize("estado", ["Borrador", "Confirmado", "Despachado", "Entregado", "Cancelado"])
@pytest.mark.parametrize("accion", list(PERMITIDOS))
def test_matriz_completa_de_transiciones(inventario, estado, accion):
    """Verifica la operación para cada estado y preserva datos si se rechaza."""
    p = PedidosSQLite(inventario)
    p.crear_borrador("P", "Cliente", "Destino")
    p.establecer_producto("P", "D1", "P1", 2)
    if estado in ("Confirmado", "Despachado", "Entregado"):
        p.confirmar("P")
        p.asignar_vehiculo("P", "AA123BB")
    if estado in ("Despachado", "Entregado"):
        p.despachar("P")
    if estado == "Entregado":
        p.entregar("P")
    if estado == "Cancelado":
        p.cancelar("P")
    operaciones = {
        "confirmar": lambda: p.confirmar("P"), "cancelar": lambda: p.cancelar("P"),
        "despachar": lambda: p.despachar("P"), "entregar": lambda: p.entregar("P"),
        "editar": lambda: p.editar_borrador("P", "Nuevo", "Otro", 3, "09:00", "12:00", "Nota"),
        "item": lambda: p.establecer_producto("P", "D1", "P1", 3),
        "quitar": lambda: p.quitar_producto("P", "D1", "P1"),
        "liberar": lambda: p.liberar_vehiculo("P"),
    }
    if estado in PERMITIDOS[accion]:
        operaciones[accion]()
    else:
        antes = [tuple(f) for f in inventario.conexion.execute("SELECT * FROM pedidos")]
        stock = inventario.stock("D1", "P1")
        with pytest.raises(ValueError):
            operaciones[accion]()
        assert [tuple(f) for f in inventario.conexion.execute("SELECT * FROM pedidos")] == antes
        assert inventario.stock("D1", "P1") == stock


def test_editar_reemplazar_quitar_y_consultar(inventario):
    """Comprueba edición de cabecera e ítems, consulta y eliminación del detalle."""
    p = PedidosSQLite(inventario)
    p.crear_borrador("P", "Cliente", "Destino")
    p.establecer_producto("P", "D1", "P1", 2)
    p.establecer_producto("P", "D1", "P1", 4)
    p.editar_borrador("P", "Nuevo", "Otra dirección", 3, "09:00", "12:00", "Nota")
    pedido = p.obtener_pedido("P")
    assert (pedido.cliente, pedido.destino, pedido.prioridad, pedido.observaciones) == ("Nuevo", "Otra dirección", 3, "Nota")
    assert pedido.productos[0]["cantidad"] == 4
    assert pedido.volumen_total == pytest.approx(0.4)
    p.quitar_producto("P", "D1", "P1")
    assert p.obtener_pedido("P").productos == []
    with pytest.raises(ValueError):
        p.quitar_producto("P", "D1", "P1")


def test_asignar_sin_capacidad_o_conductor_y_liberar(inventario):
    """Verifica rechazos separados de asignación y liberación sin perder reservas."""
    p = PedidosSQLite(inventario)
    p.crear_borrador("P", "C", "D")
    p.establecer_producto("P", "D1", "P1", 200)
    p.confirmar("P")
    f = FlotaSQLite(inventario)
    f.registrar_vehiculo(Vehiculo("CHICO", 1))
    for patente in ("CHICO", "NO"):
        with pytest.raises(ValueError):
            p.asignar_vehiculo("P", patente)
    f.registrar_conductor(Conductor("456", "Otro"))
    f.asignar_conductor("CHICO", "456")
    with pytest.raises(ValueError, match="capacidad"):
        p.asignar_vehiculo("P", "CHICO")
    assert p.obtener_pedido("P").vehiculo_asignado is None
    assert inventario.stock_reservado("D1", "P1") == 200
    p.asignar_vehiculo("P", "AA123BB")
    with pytest.raises(ValueError):
        p.asignar_vehiculo("P", "AA123BB")
    p.liberar_vehiculo("P")
    assert p.obtener_pedido("P").vehiculo_asignado is None
    assert inventario.stock_reservado("D1", "P1") == 200
    with pytest.raises(ValueError):
        p.liberar_vehiculo("P")


@pytest.mark.parametrize("campo", ["id", "cliente", "destino"])
def test_cabecera_vacia_no_crea_pedido(inventario, campo):
    """Comprueba que cada texto obligatorio vacío impida crear el pedido."""
    args = ["P", "Cliente", "Destino"]
    args[["id", "cliente", "destino"].index(campo)] = " "
    with pytest.raises(ValueError):
        PedidosSQLite(inventario).crear_borrador(*args)
    assert PedidosSQLite(inventario).listar_pedidos() == []


@pytest.mark.parametrize("prioridad", [0, 4, 1.5, True])
def test_prioridad_invalida_tambien_se_rechaza_en_repositorio(inventario, prioridad):
    """Verifica que el repositorio valide la prioridad antes de persistir."""
    with pytest.raises(ValueError):
        PedidosSQLite(inventario).crear_borrador("P", "Cliente", "Destino", prioridad)
    assert PedidosSQLite(inventario).listar_pedidos() == []


def test_circuito_multideposito_reserva_y_descuenta_todos_los_items(inventario):
    """Comprueba confirmación atómica y descuento de ítems en dos depósitos."""
    inventario.registrar_producto(Producto("P2", "Segundo", 0.2, 1))
    inventario.registrar_deposito(Deposito("D2", "Segundo", "Sur", 10))
    inventario.actualizar_stock("D2", "P2", 3)
    p = PedidosSQLite(inventario)
    p.crear_borrador("P", "Cliente", "Destino")
    p.establecer_producto("P", "D1", "P1", 10)
    p.establecer_producto("P", "D2", "P2", 4)
    with pytest.raises(StockInsuficiente) as error:
        p.confirmar("P")
    assert error.value.faltantes[0]["id_producto"] == "P2"
    assert inventario.stock_reservado("D1", "P1") == inventario.stock_reservado("D2", "P2") == 0
    p.establecer_producto("P", "D2", "P2", 2)
    p.confirmar("P")
    assert inventario.stock_reservado("D1", "P1") == 10
    assert inventario.stock_reservado("D2", "P2") == 2
    p.asignar_vehiculo("P", "AA123BB")
    p.despachar("P")
    assert inventario.stock("D1", "P1") == 190
    assert inventario.stock("D2", "P2") == 1
    assert inventario.stock_reservado("D1", "P1") == inventario.stock_reservado("D2", "P2") == 0
    p.entregar("P")
    assert p.obtener_pedido("P").estado == "Entregado"


def test_entrega_de_pedido_historico_despachado_sin_vehiculo(inventario):
    """Verifica compatibilidad al entregar un pedido histórico sin vehículo."""
    with inventario._transaccion():
        inventario.conexion.execute("INSERT INTO pedidos(id_pedido,cliente,destino,prioridad,estado) VALUES('LEGADO','C','D',1,'Despachado')")
    p = PedidosSQLite(inventario)
    p.entregar("LEGADO")
    assert p.obtener_pedido("LEGADO").estado == "Entregado"
    assert inventario.stock("D1", "P1") == 200
