"""Comprueba altas, estados y asignaciones persistentes de vehículos y conductores."""
import sqlite3

import pytest

from Backend.flota import FlotaSQLite
from Backend.modelos.conductor import Conductor
from Backend.modelos.vehiculo import Vehiculo
from Backend.pedidos import PedidosSQLite


def test_altas_listados_estados_y_copias(inventario):
    """Comprueba flota, estados y relaciones sin persistir cambios de una copia."""
    f = FlotaSQLite(inventario)
    f.registrar_vehiculo(Vehiculo("ZZZ", 10, "Mantenimiento"))
    f.registrar_conductor(Conductor("456", "Luis"))
    assert [v.patente for v in f.listar_vehiculos()] == ["AA123BB", "ZZZ"]
    assert len(f.listar_conductores()) == 2
    v = f.obtener_vehiculo("ZZZ")
    v.estado = "Disponible"
    assert f.obtener_vehiculo("ZZZ").estado == "Mantenimiento"
    f.actualizar_estado_vehiculo("ZZZ", "Disponible")
    f.asignar_conductor("ZZZ", "456")
    assert f.obtener_conductor("456").estado == "Asignado"
    assert f.obtener_conductor("456").vehiculo_asignado == "ZZZ"
    f.actualizar_estado_vehiculo("ZZZ", "En Ruta")
    with pytest.raises(ValueError):
        f.liberar_conductor("ZZZ")
    f.actualizar_estado_vehiculo("ZZZ", "Disponible")
    f.liberar_conductor("ZZZ")
    f.actualizar_estado_conductor("456", "Inactivo")
    with pytest.raises(ValueError):
        f.asignar_conductor("ZZZ", "456")
    f.actualizar_estado_conductor("456", "Disponible")
    f.asignar_conductor("ZZZ", "456")
    assert f.obtener_vehiculo("ZZZ").conductor_asignado == "456"


@pytest.mark.parametrize("estado", ["En Ruta", "Inventado"])
def test_alta_vehiculo_estado_invalido(inventario, estado):
    """Rechaza un estado inicial de vehículo incompatible con el registro."""
    with pytest.raises(ValueError):
        FlotaSQLite(inventario).registrar_vehiculo(Vehiculo("NUEVO", 10, estado))


@pytest.mark.parametrize("patente", ["", " ", None])
def test_patente_invalida(inventario, patente):
    """Comprueba que una patente no textual o vacía no se registre."""
    with pytest.raises(ValueError):
        FlotaSQLite(inventario).registrar_vehiculo(Vehiculo(patente, 10))


def test_altas_duplicadas_y_asignaciones_iniciales_invalidas(inventario):
    """Rechaza duplicados y entidades con asignaciones previas al alta."""
    f = FlotaSQLite(inventario)
    with pytest.raises(sqlite3.IntegrityError):
        f.registrar_conductor(Conductor("123", "Otro"))
    with pytest.raises(sqlite3.IntegrityError):
        f.registrar_vehiculo(Vehiculo("AA123BB", 10))
    c = Conductor("456", "Otro")
    c.estado = "Asignado"
    with pytest.raises(ValueError):
        f.registrar_conductor(c)
    v = Vehiculo("ZZZ", 10)
    v.pedido_asignado = "P"
    with pytest.raises(ValueError):
        f.registrar_vehiculo(v)


def test_no_se_reemplaza_conductor_ni_se_lo_duplica(inventario):
    """Verifica que una asignación no sobrescriba ni comparta conductores."""
    f = FlotaSQLite(inventario)
    f.registrar_vehiculo(Vehiculo("ZZZ", 10))
    f.registrar_conductor(Conductor("456", "Otro"))
    for patente, dni in (("AA123BB", "456"), ("ZZZ", "123")):
        with pytest.raises(ValueError):
            f.asignar_conductor(patente, dni)
    assert f.obtener_vehiculo("AA123BB").conductor_asignado == "123"
    assert f.obtener_vehiculo("ZZZ").conductor_asignado is None


def test_estados_rechazan_incompatibilidades(inventario):
    """Comprueba las restricciones de mantenimiento, ruta y conductor asignado."""
    f = FlotaSQLite(inventario)
    for estado in ("Mantenimiento", "Otro"):
        with pytest.raises(ValueError):
            f.actualizar_estado_vehiculo("AA123BB", estado)
    for estado in ("Inactivo", "Asignado"):
        with pytest.raises(ValueError):
            f.actualizar_estado_conductor("123", estado)
    f.liberar_conductor("AA123BB")
    with pytest.raises(ValueError):
        f.liberar_conductor("AA123BB")
    with pytest.raises(ValueError):
        f.actualizar_estado_vehiculo("AA123BB", "En Ruta")


@pytest.mark.parametrize("consulta", ["obtener_vehiculo", "obtener_conductor"])
def test_recursos_inexistentes(inventario, consulta):
    """Comprueba errores de consulta de vehículos y conductores inexistentes."""
    with pytest.raises(ValueError):
        getattr(FlotaSQLite(inventario), consulta)("NO")


def test_pedido_activo_protege_conductor_y_estado(inventario):
    """Verifica que un pedido activo proteja su conductor y el estado del vehículo."""
    p = PedidosSQLite(inventario)
    p.crear_borrador("P", "C", "D")
    p.establecer_producto("P", "D1", "P1", 2)
    p.confirmar("P")
    p.asignar_vehiculo("P", "AA123BB")
    f = FlotaSQLite(inventario)
    f.registrar_conductor(Conductor("456", "Otro"))
    for operacion in (lambda: f.liberar_conductor("AA123BB"),
                      lambda: f.asignar_conductor("AA123BB", "456"),
                      lambda: f.actualizar_estado_vehiculo("AA123BB", "En Ruta")):
        with pytest.raises(ValueError):
            operacion()
    p.cancelar("P")
    f.liberar_conductor("AA123BB")
    assert f.obtener_conductor("123").estado == "Disponible"
