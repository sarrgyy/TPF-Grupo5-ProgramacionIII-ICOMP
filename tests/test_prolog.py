"""Pruebas de la integración de recomendaciones con Prolog."""

import shutil
from types import SimpleNamespace

import pytest

from Backend.prolog import recomendar_vehiculos


def _crear_pedido_confirmado(client):
    assert client.post("/pedidos", json={"id_pedido": "PROLOG", "cliente": "Cliente", "destino": "Destino"}).status_code == 201
    assert client.put("/pedidos/PROLOG/items", json={"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": 2}).status_code == 200
    assert client.post("/pedidos/PROLOG/confirmar").status_code == 200


def test_recomendaciones_invocan_motor_prolog(client, monkeypatch):
    """La API pasa volumen y flota al motor y devuelve sus recomendaciones."""
    import Backend.api as api
    recibido = {}

    def motor(volumen, vehiculos):
        recibido["volumen"] = volumen
        recibido["vehiculos"] = vehiculos
        return [{"patente": "AB123CD", "capacidad_maxima": 10, "espacio_restante": 9.98}]

    monkeypatch.setattr(api, "recomendar_vehiculos", motor)
    _crear_pedido_confirmado(client)
    respuesta = client.get("/pedidos/PROLOG/vehiculos-recomendados")
    assert respuesta.status_code == 200
    assert respuesta.json()["motor"] == "SWI-Prolog"
    assert respuesta.json()["recomendaciones"][0]["patente"] == "AB123CD"
    assert recibido["volumen"] == 0.008
    assert len(recibido["vehiculos"]) == 3


def test_recomendaciones_requieren_pedido_confirmado(client):
    """No se recomiendan vehículos para un borrador todavía no confirmado."""
    client.post("/pedidos", json={"id_pedido": "BORRADOR", "cliente": "Cliente", "destino": "Destino"})
    respuesta = client.get("/pedidos/BORRADOR/vehiculos-recomendados")
    assert respuesta.status_code == 409


def _vehiculo(patente, capacidad, estado="Disponible", conductor="30111222", pedido=None):
    """Crea un vehículo mínimo con los atributos que consulta el motor.

    Args:
        patente (str): Identificador del vehículo.
        capacidad (float): Capacidad máxima en m³.
        estado (str): Estado operativo del vehículo.
        conductor (str | None): DNI del conductor asignado, si lo hay.
        pedido (str | None): Pedido activo del vehículo, si lo hay.

    Returns:
        SimpleNamespace: Objeto con los campos que lee ``recomendar_vehiculos``.
    """
    return SimpleNamespace(patente=patente, capacidad_maxima=capacidad, estado=estado,
                           conductor_asignado=conductor, pedido_asignado=pedido)


@pytest.mark.skipif(shutil.which("swipl") is None, reason="SWI-Prolog no está instalado")
def test_motor_prolog_real_filtra_y_ordena_por_menor_espacio_sobrante():
    """Con SWI-Prolog real, descarta no aptos y prioriza el mejor ajuste."""
    flota = [
        _vehiculo("A1", 10),
        _vehiculo("B2", 5),
        _vehiculo("C3", 2),
        _vehiculo("D4", 8, estado="En Ruta", pedido="P-1"),
        _vehiculo("E5", 6, conductor=None),
    ]
    resultado = recomendar_vehiculos(3, flota)
    assert [r["patente"] for r in resultado] == ["B2", "A1"]
    assert [r["espacio_restante"] for r in resultado] == [2.0, 7.0]
    assert recomendar_vehiculos(50, flota) == []
