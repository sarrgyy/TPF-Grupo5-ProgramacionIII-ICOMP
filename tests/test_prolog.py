"""Pruebas de la integración de recomendaciones con Prolog."""


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
