"""Provee sesiones y escenarios SQLite temporales para aislar las pruebas."""
import pytest

from Backend.flota import FlotaSQLite
from Backend.modelos.conductor import Conductor
from Backend.modelos.deposito import Deposito
from Backend.modelos.productos import Producto
from Backend.modelos.vehiculo import Vehiculo
from Backend.persistencia import InventarioSQLite


@pytest.fixture
def client(base_api):
    """Abre un cliente HTTP sobre el escenario temporal de la API.

    El cliente inicia y detiene el ciclo de vida de FastAPI sin cargar los ejemplos SQL.

    Args:
        base_api (Path): Archivo SQLite preparado para esta prueba.

    Yields:
        TestClient: Cliente HTTP con recursos administrados por el contexto.
    """
    from fastapi.testclient import TestClient
    from Backend.api import create_app
    with TestClient(create_app(base_api, cargar_base=False)) as cliente:
        yield cliente


@pytest.fixture
def base_api(tmp_path):
    """Prepara un escenario HTTP independiente de los valores iniciales SQL.

    Args:
        tmp_path (Path): Directorio temporal exclusivo de la prueba.

    Returns:
        Path: Archivo api.db con catálogo, existencias y flota de prueba.
    """
    ruta = tmp_path / "api.db"
    with InventarioSQLite(ruta) as inv:
        inv.cargar_iniciales(
            [Producto("PRD-1", "Pantalón", 0.004, 0.5), Producto("PRD-2", "Campera", 0.008, 0.9),
             Producto("PRD-3", "Remera", 0.002, 0.2), Producto("PRD-4", "Buzo", 0.006, 0.6)],
            [Deposito("D-001", "Centro", "Centro", 50), Deposito("D-002", "Melipal", "Melipal", 30),
             Deposito("D-003", "Dina Huapi", "Dina Huapi", 20)],
            [("D-001", "PRD-1", 200), ("D-001", "PRD-2", 100),
             ("D-001", "PRD-3", 300), ("D-001", "PRD-4", 150)],
        )
        f = FlotaSQLite(inv)
        for patente, capacidad, dni in (("AB123CD", 3, "28555111"), ("EF456GH", 2.5, "30111222"), ("IJ789KL", 20, "31333444")):
            f.registrar_vehiculo(Vehiculo(patente, capacidad))
            f.registrar_conductor(Conductor(dni, "Conductor de prueba"))
            f.asignar_conductor(patente, dni)
    return ruta


@pytest.fixture
def inventario():
    """Abre inventario y flota en memoria para una prueba.

    Yields:
        InventarioSQLite: Sesión con P1, D1, 200 unidades y un vehículo con conductor.
    """
    with InventarioSQLite(":memory:") as inv:
        inv.cargar_iniciales(
            [Producto("P1", "Producto", 0.1, 1.0)],
            [Deposito("D1", "Central", "Centro", 100.0)],
            [("D1", "P1", 200)],
        )
        flota = FlotaSQLite(inv)
        flota.registrar_vehiculo(Vehiculo("AA123BB", 30.0))
        flota.registrar_conductor(Conductor("123", "Ana"))
        flota.asignar_conductor("AA123BB", "123")
        yield inv
