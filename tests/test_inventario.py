"""Verifica stock, capacidad, traslados y conservación transaccional de datos."""
import sqlite3

import pytest

from Backend.modelos.deposito import Deposito
from Backend.modelos.productos import Producto
from Backend.persistencia import InventarioSQLite


@pytest.mark.parametrize("campo", ["volumen", "peso", "capacidad"])
@pytest.mark.parametrize("valor", [0, -1, True, float("inf"), float("nan"), "1", pytest.param(10**400, id="entero-fuera-de-float")])
def test_medidas_invalidas_no_se_guardan(inventario, campo, valor):
    """Comprueba que cada medida inválida se rechace antes de guardar entidades."""
    with pytest.raises(ValueError):
        if campo == "capacidad":
            inventario.registrar_deposito(Deposito("MALO", "Malo", "Lugar", valor))
        else:
            inventario.registrar_producto(Producto("MALO", "Malo", valor if campo == "volumen" else 1,
                                                  valor if campo == "peso" else 1))
    assert len(inventario.listar_productos()) == len(inventario.listar_depositos()) == 1


@pytest.mark.parametrize("cantidad", [True, 1.5, "2", 2**63, -(2**63)-1])
def test_stock_rechaza_cantidad_fuera_del_contrato(inventario, cantidad):
    """Rechaza cantidades no enteras o fuera de 64 bits conservando existencias."""
    with pytest.raises(ValueError):
        inventario.actualizar_stock("D1", "P1", cantidad)
    assert inventario.stock("D1", "P1") == 200


def test_altas_duplicadas_y_textos_vacios_no_sobrescriben(inventario):
    """Comprueba integridad del catálogo ante duplicados y campos vacíos."""
    for producto in (Producto("P1", "Otro", 1, 1), Producto("", "Nombre", 1, 1), Producto("X", " ", 1, 1)):
        with pytest.raises(sqlite3.IntegrityError):
            inventario.registrar_producto(producto)
    for deposito in (Deposito("D1", "Otro", "Lugar", 1), Deposito("X", "Nombre", " ", 1)):
        with pytest.raises(sqlite3.IntegrityError):
            inventario.registrar_deposito(deposito)
    assert inventario.obtener_producto("P1").nombre == "Producto"
    assert inventario.obtener_deposito("D1").nombre == "Central"


def test_consultas_son_copias_y_volumen_se_calcula(inventario):
    """Verifica copias independientes, ocupación y total de stock entre depósitos."""
    p = inventario.obtener_producto("P1")
    p.nombre = "No guardar"
    d = inventario.obtener_deposito("D1")
    assert d.volumen_ocupado == pytest.approx(20)
    d.capacidad_maxima = 1
    assert inventario.obtener_producto("P1").nombre == "Producto"
    assert inventario.obtener_deposito("D1").capacidad_maxima == 100
    inventario.registrar_deposito(Deposito("D2", "Nuevo", "Sur", 100))
    assert inventario.stock("D2", "P1") == 0
    inventario.actualizar_stock("D2", "P1", 10)
    assert inventario.stock_total("P1") == 210


@pytest.mark.parametrize("consulta,args", [("obtener_producto", ("NO",)), ("obtener_deposito", ("NO",)),
    ("stock", ("NO", "P1")), ("stock", ("D1", "NO")), ("stock_total", ("NO",))])
def test_referencias_inexistentes_se_rechazan(inventario, consulta, args):
    """Comprueba que las consultas rechacen referencias no registradas."""
    with pytest.raises(ValueError):
        getattr(inventario, consulta)(*args)


def test_traslado_y_reversion_por_capacidad(inventario):
    """Verifica traslado válido y rollback al superar capacidad de destino."""
    inventario.registrar_deposito(Deposito("D2", "Chico", "Sur", 1))
    with pytest.raises(ValueError):
        inventario.transferir("D1", "D2", "P1", 20)
    assert inventario.stock("D1", "P1") == 200
    assert inventario.stock("D2", "P1") == 0
    inventario.transferir("D1", "D2", "P1", 10)
    assert inventario.stock("D1", "P1") == 190
    assert inventario.stock("D2", "P1") == 10
    assert inventario.stock_total("P1") == 200


@pytest.mark.parametrize("origen,destino,cantidad", [("D1", "D1", 1), ("D1", "D2", 0), ("D1", "D2", -1), ("D1", "D2", 201)])
def test_traslado_invalido_no_retira_stock(inventario, origen, destino, cantidad):
    """Rechaza traslados inválidos sin alterar las unidades de origen."""
    inventario.registrar_deposito(Deposito("D2", "Otro", "Sur", 100))
    with pytest.raises(ValueError):
        inventario.transferir(origen, destino, "P1", cantidad)
    assert inventario.stock("D1", "P1") == 200


def test_retiro_insuficiente_y_delta_cero(inventario):
    """Comprueba el rechazo de retiro excesivo y un movimiento de cero unidades."""
    with pytest.raises(ValueError):
        inventario.actualizar_stock("D1", "P1", -201)
    assert inventario.actualizar_stock("D1", "P1", 0) == 200


def test_carga_inicial_fallida_revierte_catalogo():
    """Verifica que un duplicado durante la carga revierta todo el catálogo nuevo."""
    with InventarioSQLite(":memory:") as inv:
        with pytest.raises(sqlite3.IntegrityError):
            inv.cargar_iniciales([Producto("P", "Uno", 1, 1), Producto("P", "Dos", 1, 1)], [], [])
        assert inv.listar_productos() == []


def test_contexto_cierra_conexion_incluso_con_excepcion():
    """Comprueba que una excepción dentro de with cierre la conexión SQLite."""
    with pytest.raises(RuntimeError):
        with InventarioSQLite(":memory:") as inv:
            raise RuntimeError("salida")
    with pytest.raises(sqlite3.ProgrammingError):
        inv.conexion.execute("SELECT 1")


def test_cantidades_grandes_se_suman_con_enteros_python():
    """Verifica totales exactos que exceden el entero de 64 bits de SQLite."""
    with InventarioSQLite(":memory:") as inv:
        inv.cargar_iniciales([Producto("P", "Chico", 1e-20, 1)],
            [Deposito("A", "A", "A", 1), Deposito("B", "B", "B", 1)],
            [("A", "P", 2**63-1), ("B", "P", 1)])
        assert inv.stock_total("P") == 2**63


@pytest.mark.parametrize("entidad", ["producto", "deposito", "vehiculo"])
def test_medida_entera_grande_se_guarda_como_real(inventario, entidad):
    """Comprueba el almacenamiento REAL de una medida entera grande pero finita."""
    from Backend.flota import FlotaSQLite
    from Backend.modelos.vehiculo import Vehiculo
    medida = 2**64
    if entidad == "producto":
        inventario.registrar_producto(Producto("GRANDE", "Grande", medida, medida))
        assert inventario.obtener_producto("GRANDE").volumen_unitario == float(medida)
    elif entidad == "deposito":
        inventario.registrar_deposito(Deposito("GRANDE", "Grande", "Sur", medida))
        assert inventario.obtener_deposito("GRANDE").capacidad_maxima == float(medida)
    else:
        f = FlotaSQLite(inventario)
        f.registrar_vehiculo(Vehiculo("GRANDE", medida))
        assert f.obtener_vehiculo("GRANDE").capacidad_maxima == float(medida)


def test_carga_manual_no_reemplaza_datos_existentes(inventario):
    """Verifica que la carga manual no reponga ni reemplace datos existentes."""
    assert inventario.cargar_iniciales([Producto("OTRO", "Otro", 1, 1)], [], []) is False
    assert [p.id_producto for p in inventario.listar_productos()] == ["P1"]
    assert inventario.stock("D1", "P1") == 200
