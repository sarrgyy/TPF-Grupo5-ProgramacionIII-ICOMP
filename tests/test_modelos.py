"""Comprueba estados, prioridades y reconstrucción de las entidades del pedido."""
import pytest

from Backend.modelos.pedido import Pedido
from Backend.pedidos import PedidosSQLite
from Backend.modelos.vehiculo import Vehiculo


def test_pedido_inicia_en_borrador():
    """Comprueba el estado inicial de un pedido nuevo."""
    assert Pedido("P", "Cliente", "Destino").estado == "Borrador"


@pytest.mark.parametrize("prioridad", [0, 4, 1.5, True, "1"])
def test_prioridad_invalida_se_rechaza(prioridad):
    """Verifica el rechazo de prioridades no enteras o fuera de 1 a 3."""
    with pytest.raises(ValueError):
        Pedido("P", "Cliente", "Destino", prioridad)


def test_estados_del_modelo_coinciden_con_el_flujo():
    """Comprueba nombres de estado admitidos y rechazo de uno desconocido."""
    pedido = Pedido("P", "Cliente", "Destino")
    for estado in ("Borrador", "Confirmado", "Despachado", "Entregado", "Cancelado"):
        pedido.actualizar_estado(estado)
        assert pedido.estado == estado
    with pytest.raises(ValueError):
        pedido.actualizar_estado("Inventado")


def test_entrega_deriva_estado_y_cancelado_no_tiene_entrega(inventario):
    """Verifica la entrega derivada y su ausencia en Borrador o Cancelado."""
    p = PedidosSQLite(inventario)
    p.crear_borrador("P", "Cliente", "Destino", hora_inicio="08:00", hora_fin="12:00")
    assert p.obtener_pedido("P").entrega is None
    p.establecer_producto("P", "D1", "P1", 2)
    p.confirmar("P")
    assert p.obtener_pedido("P").entrega.estado == "Programada"
    p.asignar_vehiculo("P", "AA123BB")
    p.despachar("P")
    assert p.obtener_pedido("P").entrega.estado == "En Camino"
    p.entregar("P")
    assert p.obtener_pedido("P").entrega.estado == "Completada"
    p.crear_borrador("C", "Cliente", "Destino", hora_inicio="08:00", hora_fin="12:00")
    p.cancelar("C")
    assert p.obtener_pedido("C").entrega is None


def test_observaciones_sin_horario_se_recuperan(inventario):
    """Comprueba que las notas no dependan de una ventana horaria."""
    p = PedidosSQLite(inventario)
    p.crear_borrador("P", "Cliente", "Destino", observaciones="Tocar timbre")
    pedido = p.obtener_pedido("P")
    assert pedido.observaciones == "Tocar timbre"
    assert pedido.hora_inicio is None
    assert pedido.entrega is None


@pytest.mark.parametrize("inicio,fin", [("08:00", None), (None, "12:00"), ("25:00", "26:00"), ("12:00", "08:00")])
def test_ventana_invalida_no_guarda(inventario, inicio, fin):
    """Verifica rechazo de ventanas incompletas o inválidas sin crear cabecera."""
    p = PedidosSQLite(inventario)
    with pytest.raises(ValueError):
        p.crear_borrador("P", "Cliente", "Destino", hora_inicio=inicio, hora_fin=fin)
    assert inventario.conexion.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0] == 0


def test_asignacion_en_modelo_no_usa_estado_inexistente():
    """Comprueba que asignar en memoria conserve el estado Confirmado."""
    pedido = Pedido("P", "Cliente", "Destino")
    pedido.actualizar_estado("Confirmado")
    vehiculo = Vehiculo("ABC", 10)
    vehiculo.asignar_conductor("123")
    vehiculo.asignar_pedido(pedido)
    assert pedido.estado == "Confirmado"
    assert vehiculo.tiene_pedido(pedido)


def test_modelo_no_asigna_borrador_ni_muta_vehiculo():
    """Verifica el rechazo de un borrador sin modificar la asignación local."""
    vehiculo = Vehiculo("ABC", 10)
    vehiculo.asignar_conductor("123")
    with pytest.raises(ValueError):
        vehiculo.asignar_pedido(Pedido("P", "C", "D"))
    assert vehiculo.pedidos == []
    assert vehiculo.volumen_ocupado == 0
