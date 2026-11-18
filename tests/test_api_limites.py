"""Prueba límites HTTP, cuerpos inválidos y acceso seguro a recursos."""
import pytest


@pytest.mark.parametrize("campos", [{"id_producto": ""}, {"id_producto": "A/B"}, {"id_producto": 1},
    {"nombre": " "}, {"nombre": "x"*201}, {"volumen_unitario": 0}, {"volumen_unitario": -1},
    {"volumen_unitario": "1"}, {"peso_unitario": True}, {"peso_unitario": 0},
    {"peso_unitario": None}, {"extra": "no admitido"}, pytest.param({"peso_unitario": 10**400}, id="medida-inmensa")])
def test_producto_invalido_no_modifica_catalogo(client, campos):
    """Rechaza campos de producto inválidos sin modificar el catálogo."""
    datos = {"id_producto": "N", "nombre": "Nombre", "volumen_unitario": 1, "peso_unitario": 1}
    assert client.post("/productos", json={**datos, **campos}).status_code == 422
    assert len(client.get("/productos").json()) == 4


@pytest.mark.parametrize("campos", [{"cliente": None}, {"prioridad": 1.0}, {"observaciones": "x"*2001},
    {"hora_inicio": True}, {"hora_inicio": "9:00", "hora_fin": "12:00"},
    {"hora_inicio": "08:00", "hora_fin": "08:00"}, {"destino": "x"*201}])
def test_pedido_invalido_no_deja_cabecera(client, campos):
    """Comprueba el rechazo de tipos, límites y ventanas de una cabecera inválida."""
    r = client.post("/pedidos", json={"id_pedido": "P", "cliente": "Cliente", "destino": "Destino", **campos})
    assert r.status_code in (400, 422)
    assert client.get("/pedidos").json() == []


@pytest.mark.parametrize("cuerpo", ["null", "[]", '"texto"', "{", "{}"])
def test_cuerpos_invalidos_se_informan_como_422(client, cuerpo):
    """Comprueba mensajes de validación ante JSON inválido o estructura incorrecta."""
    r = client.post("/pedidos", content=cuerpo, headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    assert "mensaje" in r.json()["detail"]


@pytest.mark.parametrize("accion", ["confirmar", "cancelar", "despachar", "entregar"])
def test_todas_las_transiciones_de_pedido_inexistente_devuelven_404(client, accion):
    """Verifica la respuesta 404 de cada transición sobre un pedido inexistente."""
    assert client.post(f"/pedidos/NO/{accion}").status_code == 404


@pytest.mark.parametrize("tipo", ["items", "vehiculo"])
def test_put_inexistente_no_crea_pedido(client, tipo):
    """Comprueba que modificar un recurso inexistente no cree una cabecera."""
    datos = {"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": 1} if tipo == "items" else {"patente": "AB123CD"}
    assert client.put(f"/pedidos/NO/{tipo}", json=datos).status_code == 404
    assert client.get("/pedidos").json() == []


@pytest.mark.parametrize("clave", ["", " ", "x"*101])
def test_clave_ingreso_invalida_no_suma_stock(client, clave):
    """Rechaza claves de ingreso inválidas sin sumar unidades."""
    r = client.post("/stock/ingresos", json={"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": 1}, headers={"Idempotency-Key": clave})
    assert r.status_code in (400, 422)
    fila = next(s for s in client.get("/stock").json() if s["id_deposito"] == "D-001" and s["id_producto"] == "PRD-1")
    assert fila["fisico"] == 200


def test_texto_sql_se_trata_como_dato(client):
    """Comprueba que los textos con sintaxis SQL no ejecuten instrucciones."""
    nombre = "O'Brian'); DROP TABLE productos; --"
    assert client.post("/productos", json={"id_producto": "SEGURO", "nombre": nombre, "volumen_unitario": 1, "peso_unitario": 1}).status_code == 201
    assert client.get("/productos").json()[-1]["nombre"] == nombre
    assert len(client.get("/productos").json()) == 5
    assert client.get("/pedidos/NO%27%20OR%201%3D1--").status_code == 404


@pytest.mark.parametrize("ruta", ["/Backend/schema.sql", "/Backend/logistica.db", "/%2e%2e/Backend/schema.sql", "/.git/config"])
def test_servidor_estatico_no_expone_backend_ni_git(client, ruta):
    """Verifica que rutas directas o relativas no expongan archivos internos."""
    assert client.get(ruta).status_code == 404


def test_stock_incluye_combinaciones_sin_existencias(client):
    """Comprueba parejas con stock cero y la relación entre sus tres cantidades."""
    filas = client.get("/stock").json()
    assert len(filas) == 12
    for fila in filas:
        assert fila["disponible"] == fila["fisico"] - fila["reservado"]
        assert fila["fisico"] >= 0
