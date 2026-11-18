"""Verifica operaciones locales e invariantes de todos los modelos de dominio."""
import pytest

from Backend.modelos.productos import Producto
from Backend.modelos.deposito import Deposito
from Backend.modelos.conductor import Conductor
from Backend.modelos.entrega import Entrega
from Backend.modelos.pedido import Pedido
from Backend.modelos.vehiculo import Vehiculo


def test_producto_ingreso_retiro_y_faltante():
    """Comprueba movimientos locales enteros y rechazo de un retiro insuficiente."""
    p = Producto("P", "Uno", 1, 1, 5)
    assert p.actualizar_stock(2) is True
    assert p.actualizar_stock(-7) is True
    assert p.actualizar_stock(-1) is False
    assert p.stock == 0


@pytest.mark.parametrize("cantidad", [1.5, True, "2"])
def test_producto_no_admite_stock_fraccionario_o_booleano(cantidad):
    """Verifica el rechazo de deltas locales no enteros sin cambiar el stock."""
    p = Producto("P", "Uno", 1, 1, 5)
    with pytest.raises(ValueError):
        p.actualizar_stock(cantidad)
    assert p.stock == 5


@pytest.mark.parametrize("stock", [0.5, -1, True, "5", None])
def test_producto_rechaza_stock_inicial_invalido(stock):
    """Comprueba que el stock inicial local sea un entero no negativo."""
    with pytest.raises(ValueError):
        Producto("P", "Uno", 1, 1, stock)


def test_deposito_espacio_y_ampliacion():
    """Verifica espacio disponible y cambios de capacidad compatibles con la carga."""
    d = Deposito("D", "Central", "Centro", 10)
    d.volumen_ocupado = 4
    assert d.espacio_disponible() == 6
    assert d.verificar_espacio(6) is True
    assert d.verificar_espacio(7) is False
    d.actualizar_capacidad(3)
    assert d.capacidad_maxima == 10
    d.actualizar_capacidad(20)
    assert d.espacio_disponible() == 16


@pytest.mark.parametrize("valor", [-1, float("nan"), float("inf"), True])
def test_deposito_no_admite_volumen_invalido(valor):
    """Comprueba el rechazo de medidas inválidas sin cambiar la capacidad."""
    d = Deposito("D", "Central", "Centro", 10)
    with pytest.raises(ValueError):
        d.verificar_espacio(valor)
    with pytest.raises(ValueError):
        d.actualizar_capacidad(valor)
    assert d.capacidad_maxima == 10


def test_conductor_estados_asignacion_liberacion_e_info():
    """Verifica operaciones y datos de consulta del conductor en memoria."""
    c = Conductor("123", "Ana")
    assert c.liberar_vehiculo() is False
    assert c.actualizar_estado("Inactivo") is True
    assert c.asignar_vehiculo("ABC") is False
    assert c.actualizar_estado("Inventado") is False
    assert c.estado == "Inactivo"
    c.actualizar_estado("Disponible")
    assert c.asignar_vehiculo("ABC") is True
    assert c.obtener_info()["Vehículo Asignado"] == "ABC"
    assert c.liberar_vehiculo() is True
    assert c.obtener_info()["Estado"] == "Disponible"


def test_entrega_estados_notas_e_info():
    """Comprueba estados admitidos, notas y formato de la información de entrega."""
    e = Entrega("E", "Cliente", "Destino", "08:00", "12:00")
    for estado in ("En Camino", "Fallida", "Programada", "Completada"):
        assert e.actualizar_estado(estado, "Nota") is True
        assert e.obtener_info()["Estado"] == estado
        assert e.obtener_info()["Observaciones"] == "Nota"
    assert e.actualizar_estado("Inventado", "No guardar") is False
    assert e.estado == "Completada" and e.observaciones == "Nota"
    assert e.obtener_info()["Ventana Horaria"] == "08:00 - 12:00"
    assert e.actualizar_estado("Completada") is True


def test_pedido_agrega_productos_y_calcula_volumen():
    """Verifica la suma del volumen de ítems locales válidos."""
    p = Pedido("P", "C", "D")
    p.agregar_producto("Caja", 3, 0.2)
    p.agregar_producto("Bolsa", 2, 0.1)
    assert len(p.productos) == 2
    assert p.volumen_total == pytest.approx(0.8)


@pytest.mark.parametrize("cantidad,volumen", [(0, 1), (-1, 1), (True, 1), (1.5, 1),
    (1, -1), (1, 0), (1, float("nan")), (1, float("inf")), (2, 1e308),
    pytest.param(10**400, 1.0, id="cantidad-excede-float")])
def test_pedido_rechaza_items_invalidos_sin_mutar(cantidad, volumen):
    """Comprueba rechazo de ítems inválidos antes de modificar el pedido local."""
    p = Pedido("P", "C", "D")
    with pytest.raises(ValueError):
        p.agregar_producto("Caja", cantidad, volumen)
    assert p.productos == [] and p.volumen_total == 0


def test_vehiculo_conductor_estados_y_limite_de_carga():
    """Verifica relaciones locales y rechazos por estado o capacidad de vehículo."""
    v = Vehiculo("ABC", 1)
    assert not v.tiene_conductor()
    v.liberar_conductor()
    v.asignar_conductor("123")
    v.asignar_conductor("456")
    assert v.conductor_asignado == "123"
    v.liberar_conductor()
    assert not v.tiene_conductor()
    v.asignar_conductor("123")
    v.actualizar_estado("Mantenimiento")
    v.actualizar_estado("Inventado")
    assert v.estado == "Mantenimiento"
    p = Pedido("P", "C", "D")
    p.agregar_producto("Caja", 2, 1)
    p.actualizar_estado("Confirmado")
    v.asignar_pedido(p)
    assert not v.tiene_pedido(p)
    v.actualizar_estado("Disponible")
    v.asignar_pedido(p)
    assert not v.tiene_pedido(p)
    v.liberar_pedido(p)


@pytest.mark.parametrize("despachado", [False, True])
def test_liberar_modelo_conserva_flujo_y_disponibilidad(despachado):
    """Comprueba estado del pedido y disponibilidad al liberar carga local."""
    v = Vehiculo("ABC", 10)
    v.asignar_conductor("123")
    p = Pedido("P", "C", "D")
    p.agregar_producto("Caja", 2, 1)
    p.actualizar_estado("Confirmado")
    v.asignar_pedido(p)
    if despachado:
        p.actualizar_estado("Despachado")
        v.actualizar_estado("En Ruta")
    v.liberar_pedido(p)
    assert p.estado == ("Entregado" if despachado else "Confirmado")
    assert v.estado == "Disponible"
    assert not v.tiene_pedido(p) and v.volumen_ocupado == 0


def test_pedido_confirmado_no_admite_agregar_items_en_memoria():
    """Verifica que un Confirmado no cambie su volumen después de asignarse."""
    v = Vehiculo("ABC", 2)
    v.asignar_conductor("123")
    p = Pedido("P", "C", "D")
    p.agregar_producto("Caja", 1, 1)
    p.actualizar_estado("Confirmado")
    v.asignar_pedido(p)
    with pytest.raises(ValueError):
        p.agregar_producto("Otra", 3, 1)
    assert p.volumen_total == v.volumen_ocupado == 1
    v.liberar_pedido(p)
    assert v.volumen_ocupado == 0


def test_modelo_rechaza_asignar_sin_conductor():
    """Comprueba rechazo de asignación local cuando el vehículo no tiene conductor."""
    p = Pedido("P", "C", "D")
    p.actualizar_estado("Confirmado")
    v = Vehiculo("ABC", 10)
    with pytest.raises(ValueError, match="conductor"):
        v.asignar_pedido(p)
    assert v.pedidos == []
