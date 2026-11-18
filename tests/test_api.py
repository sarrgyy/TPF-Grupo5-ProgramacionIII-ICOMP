"""Verifica las operaciones HTTP, persistencia y reglas de negocio de la API."""
import importlib.util
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient


def test_api_disponible():
    """Comprueba que el módulo de la API esté disponible para importar."""
    assert importlib.util.find_spec("Backend.api") is not None


def test_api_carga_tres_registros_una_sola_vez(tmp_path):
    """Comprueba los datos iniciales y sus conteos después de dos arranques."""
    from Backend.api import create_app
    db = tmp_path / "base.db"
    for _ in range(2):
        with TestClient(create_app(db)) as client:
            for ruta in ("/productos", "/depositos", "/pedidos", "/vehiculos"):
                assert len(client.get(ruta).json()) == 3
            assert client.get("/reportes/kpis").json() == {
                "pedidos_pendientes": 3, "vehiculos_asignados": 0,
                "productos_con_stock": 3, "pedidos_entregados": 0}


def test_depositos_informa_ocupacion_fisica_y_espacio_libre(client):
    """Suma todos los productos y conserva la capacidad de depósitos vacíos."""
    respuesta = client.get("/depositos")
    assert respuesta.status_code == 200
    depositos = {d["id_deposito"]: d for d in respuesta.json()}
    assert depositos["D-001"]["capacidad_maxima"] == 50
    assert depositos["D-001"]["volumen_ocupado"] == pytest.approx(3.1)
    assert depositos["D-001"]["espacio_disponible"] == pytest.approx(46.9)
    for identificador, capacidad in (("D-002", 30), ("D-003", 20)):
        assert depositos[identificador]["volumen_ocupado"] == 0
        assert depositos[identificador]["espacio_disponible"] == capacidad


def test_espacio_deposito_cambia_al_ingresar_y_despachar_no_al_reservar(client):
    """Mantiene la ocupación al reservar/cancelar y libera espacio al despachar."""
    ingreso = {"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": 5}
    assert client.post("/stock/ingresos", json=ingreso).status_code == 200
    crear_pedido(client)
    assert client.post("/pedidos/P/confirmar").status_code == 200
    deposito = client.get("/depositos").json()[0]
    assert deposito["volumen_ocupado"] == pytest.approx(3.12)
    assert deposito["espacio_disponible"] == pytest.approx(46.88)
    assert client.post("/pedidos/P/cancelar").status_code == 200
    assert client.get("/depositos").json()[0] == deposito
    crear_pedido(client, identificador="DESPACHAR")
    assert client.post("/pedidos/DESPACHAR/confirmar").status_code == 200
    assert client.put("/pedidos/DESPACHAR/vehiculo", json={"patente": "AB123CD"}).status_code == 200
    assert client.post("/pedidos/DESPACHAR/despachar").status_code == 200
    deposito = client.get("/depositos").json()[0]
    assert deposito["volumen_ocupado"] == pytest.approx(3.112)
    assert deposito["espacio_disponible"] == pytest.approx(46.888)


def test_deposito_lleno_informa_cero_libre_y_rechaza_ingreso(client):
    """Informa capacidad agotada sin cambiar los valores ante un ingreso inválido."""
    assert client.post("/productos", json={"id_producto": "GRANDE", "nombre": "Grande",
                       "volumen_unitario": 30, "peso_unitario": 1}).status_code == 201
    ingreso = {"id_deposito": "D-002", "id_producto": "GRANDE", "cantidad": 1}
    assert client.post("/stock/ingresos", json=ingreso).status_code == 200
    deposito = client.get("/depositos").json()[1]
    assert deposito["volumen_ocupado"] == 30
    assert deposito["espacio_disponible"] == 0
    assert client.post("/stock/ingresos", json=ingreso).status_code == 400
    assert client.get("/depositos").json()[1] == deposito


def test_espacio_disponible_no_es_negativo_por_redondeo(client, base_api):
    """Evita informar espacio negativo al llenar una capacidad decimal exacta."""
    from Backend.modelos.deposito import Deposito
    from Backend.modelos.productos import Producto
    from Backend.persistencia import InventarioSQLite
    with InventarioSQLite(base_api) as inv:
        inv.registrar_deposito(Deposito("DECIMAL", "Decimal", "Centro", 0.3))
        inv.registrar_producto(Producto("DECIMAL", "Decimal", 0.1, 1))
        inv.actualizar_stock("DECIMAL", "DECIMAL", 3)
    deposito = next(d for d in client.get("/depositos").json() if d["id_deposito"] == "DECIMAL")
    assert deposito["volumen_ocupado"] == pytest.approx(0.3)
    assert deposito["espacio_disponible"] == 0


def crear_pedido(client, identificador="P", cantidad=2, **campos):
    """Crea un borrador HTTP y establece su primer ítem de prueba.

    Args:
        client (TestClient): Cliente de la API temporal.
        identificador (str): ID del pedido de prueba.
        cantidad (int): Unidades solicitadas de PRD-1 en D-001.
        **campos: Valores opcionales adicionales de la cabecera.

    Returns:
        dict: Pedido recibido después de establecer el ítem.
    """
    respuesta = client.post("/pedidos", json={"id_pedido": identificador, "cliente": "Cliente",
                           "destino": "Destino", **campos})
    assert respuesta.status_code == 201, respuesta.text
    respuesta = client.put(f"/pedidos/{identificador}/items", json={"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": cantidad})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def stock(client, producto="PRD-1"):
    """Busca las existencias de un producto en el depósito Centro.

    Args:
        client (TestClient): Cliente de la API temporal.
        producto (str): ID de catálogo consultado.

    Returns:
        dict: Fila con stock físico, reservado y disponible.
    """
    return next(f for f in client.get("/stock").json() if f["id_deposito"] == "D-001" and f["id_producto"] == producto)


def test_circuito_http_y_stock(client):
    """Recorre el ciclo HTTP y verifica stock, reservas y entrega derivados."""
    crear_pedido(client, cantidad=201, hora_inicio="08:00", hora_fin="12:00", observaciones="Avisar")
    respuesta = client.post("/pedidos/P/confirmar")
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["faltantes"][0]["faltan"] == 1
    assert client.get("/pedidos/P").json()["estado"] == "Borrador"
    assert stock(client)["reservado"] == 0
    assert client.put("/pedidos/P/items", json={"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": 2}).status_code == 200
    assert client.post("/pedidos/P/confirmar").json()["entrega"]["estado"] == "Programada"
    assert stock(client)["disponible"] == 198
    assert client.put("/pedidos/P/vehiculo", json={"patente": "AB123CD"}).status_code == 200
    assert client.post("/pedidos/P/despachar").json()["entrega"]["estado"] == "En Camino"
    assert stock(client)["fisico"] == 198
    assert stock(client)["reservado"] == 0
    assert client.post("/pedidos/P/despachar").status_code == 400
    assert stock(client)["fisico"] == 198
    assert client.post("/pedidos/P/cancelar").status_code == 400
    assert client.post("/pedidos/P/entregar").json()["entrega"]["estado"] == "Completada"
    vehiculo = next(v for v in client.get("/vehiculos").json() if v["patente"] == "AB123CD")
    assert vehiculo["estado"] == "Disponible"
    assert vehiculo["pedido_asignado"] is None


def test_alta_y_movimiento_de_stock(client):
    """Comprueba alta, duplicados e ingresos que respetan la capacidad."""
    producto = {"id_producto": "NUEVO", "nombre": "Producto <seguro>", "volumen_unitario": 0.1, "peso_unitario": 1}
    assert client.post("/productos", json=producto).status_code == 201
    assert stock(client, "NUEVO")["fisico"] == 0
    assert client.post("/productos", json=producto).status_code == 409
    ingreso = {"id_deposito": "D-001", "id_producto": "NUEVO", "cantidad": 5}
    assert client.post("/stock/ingresos", json=ingreso).status_code == 200
    assert stock(client, "NUEVO")["disponible"] == 5
    ingreso["cantidad"] = 100000
    assert client.post("/stock/ingresos", json=ingreso).status_code == 400
    assert stock(client, "NUEVO")["fisico"] == 5


@pytest.mark.parametrize("cantidad", [0, -1, 1.5, True, "2", 2**63])
def test_http_rechaza_cantidades_invalidas(client, cantidad):
    """Rechaza cada cantidad inválida sin modificar existencias."""
    respuesta = client.post("/stock/ingresos", json={"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": cantidad})
    assert respuesta.status_code == 422
    assert stock(client)["fisico"] == 200


@pytest.mark.parametrize("extra", [{"cliente": " "}, {"prioridad": True}, {"prioridad": 4},
                                    {"hora_inicio": "08:00"}, {"hora_inicio": "12:00", "hora_fin": "08:00"},
                                    {"id_pedido": "id/con/barra"}])
def test_http_rechaza_cabecera_invalida(client, extra):
    """Comprueba que una cabecera inválida no deje un pedido persistido."""
    respuesta = client.post("/pedidos", json={"id_pedido": "P", "cliente": "Cliente", "destino": "Destino", **extra})
    assert respuesta.status_code in (400, 422)
    assert client.get("/pedidos").json() == []


def test_cancelar_y_recurso_inexistente(client):
    """Verifica liberación de reservas y respuesta para pedidos inexistentes."""
    crear_pedido(client, observaciones="Sin horario")
    assert client.get("/pedidos/P").json()["observaciones"] == "Sin horario"
    assert client.post("/pedidos/P/confirmar").status_code == 200
    assert client.post("/pedidos/P/cancelar").json()["estado"] == "Cancelado"
    assert stock(client)["reservado"] == 0
    assert client.post("/pedidos/P/confirmar").status_code == 400
    for metodo, ruta in [("get", "/pedidos/NO-EXISTE"), ("post", "/pedidos/NO-EXISTE/confirmar")]:
        assert getattr(client, metodo)(ruta).status_code == 404


def test_no_confirma_vacio_ni_despacha_sin_vehiculo(client):
    """Rechaza confirmación vacía y despacho sin vehículo preservando el stock."""
    assert client.post("/pedidos", json={"id_pedido": "P", "cliente": "C", "destino": "D"}).status_code == 201
    assert client.post("/pedidos/P/confirmar").status_code == 400
    assert client.put("/pedidos/P/items", json={"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": 1}).status_code == 200
    assert client.post("/pedidos/P/confirmar").status_code == 200
    assert client.post("/pedidos/P/despachar").status_code == 400
    assert stock(client)["fisico"] == 200


def test_prioridad_kpis_y_estaticos(client):
    """Comprueba orden de prioridad, indicadores y acceso a páginas públicas."""
    crear_pedido(client, "NORMAL", prioridad=1)
    crear_pedido(client, "URGENTE", prioridad=3)
    assert [p["id_pedido"] for p in client.get("/pedidos").json()] == ["URGENTE", "NORMAL"]
    kpis = client.get("/reportes/kpis").json()
    assert kpis["pedidos_pendientes"] == 2
    assert kpis["vehiculos_asignados"] == 0
    assert kpis["productos_con_stock"] == 4
    assert kpis["pedidos_entregados"] == 0
    for ruta in ("/", "/index.html", "/gestion.html", "/cargas.html", "/seguimiento.html", "/styles.css", "/docs"):
        assert client.get(ruta).status_code == 200
    assert client.get("/../Backend/schema.sql").status_code == 404


def test_http_persiste_al_reiniciar(base_api):
    """Verifica reservas y claves de ingreso después de reiniciar la API."""
    from Backend.api import create_app
    db = base_api
    with TestClient(create_app(db, cargar_base=False)) as primero:
        crear_pedido(primero)
        assert primero.post("/pedidos/P/confirmar").status_code == 200
        assert primero.post("/stock/ingresos", json={"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": 5},
                            headers={"Idempotency-Key": "persistente"}).status_code == 200
    with TestClient(create_app(db, cargar_base=False)) as segundo:
        assert segundo.get("/pedidos/P").json()["estado"] == "Confirmado"
        assert stock(segundo)["reservado"] == 2
        assert len(segundo.get("/productos").json()) == 4
        assert segundo.post("/stock/ingresos", json={"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": 5},
                            headers={"Idempotency-Key": "persistente"}).status_code == 200
        assert stock(segundo)["fisico"] == 205


def test_confirmaciones_concurrentes_no_sobrevenden(client):
    """Comprueba que dos confirmaciones simultáneas no reserven más que el stock."""
    crear_pedido(client, "A", 150)
    crear_pedido(client, "B", 150)
    with ThreadPoolExecutor(max_workers=2) as pool:
        respuestas = list(pool.map(lambda p: client.post(f"/pedidos/{p}/confirmar"), ["A", "B"]))
    assert sorted(r.status_code for r in respuestas) == [200, 409]
    assert stock(client)["reservado"] == 150
    assert stock(client)["disponible"] == 50


def test_reintento_ingreso_con_misma_clave_no_duplica(client):
    """Verifica que ingresos concurrentes con la misma clave se apliquen una vez."""
    datos = {"id_deposito": "D-001", "id_producto": "PRD-1", "cantidad": 5}
    headers = {"Idempotency-Key": "ingreso-uno"}
    with ThreadPoolExecutor(max_workers=2) as pool:
        respuestas = list(pool.map(lambda _: client.post("/stock/ingresos", json=datos, headers=headers), range(2)))
    assert all(r.status_code == 200 for r in respuestas)
    assert stock(client)["fisico"] == 205
    assert client.post("/stock/ingresos", json={**datos, "cantidad": 6}, headers=headers).status_code == 409
    assert stock(client)["fisico"] == 205


def test_referencias_creadas_en_consola_son_operables(client, tmp_path):
    """Comprueba referencias con espacios registradas fuera de la API."""
    from Backend.persistencia import InventarioSQLite
    from Backend.modelos.productos import Producto
    from Backend.modelos.deposito import Deposito
    from Backend.modelos.vehiculo import Vehiculo
    from Backend.modelos.conductor import Conductor
    from Backend.flota import FlotaSQLite
    with InventarioSQLite(tmp_path / "api.db") as inv:
        inv.registrar_producto(Producto("REP UNO", "Repuesto", 0.1, 1))
        inv.registrar_deposito(Deposito("DEP SUR", "Sur", "Sur", 100))
        f = FlotaSQLite(inv)
        f.registrar_vehiculo(Vehiculo("AB 123 CD", 20))
        f.registrar_conductor(Conductor("777", "Chofer"))
        f.asignar_conductor("AB 123 CD", "777")
    datos = {"id_deposito": "DEP SUR", "id_producto": "REP UNO", "cantidad": 2}
    assert client.post("/stock/ingresos", json=datos).status_code == 200
    assert client.post("/pedidos", json={"id_pedido": "P", "cliente": "C", "destino": "D"}).status_code == 201
    assert client.put("/pedidos/P/items", json=datos).status_code == 200
    assert client.post("/pedidos/P/confirmar").status_code == 200
    assert client.put("/pedidos/P/vehiculo", json={"patente": "AB 123 CD"}).status_code == 200


def test_volumen_desbordado_no_corrompe_listado(client):
    """Rechaza un volumen infinito antes de guardar el ítem o romper el listado."""
    assert client.post("/productos", json={"id_producto": "ENORME", "nombre": "Grande", "volumen_unitario": 1e308, "peso_unitario": 1}).status_code == 201
    assert client.post("/pedidos", json={"id_pedido": "P", "cliente": "C", "destino": "D"}).status_code == 201
    respuesta = client.put("/pedidos/P/items", json={"id_deposito": "D-001", "id_producto": "ENORME", "cantidad": 2})
    assert respuesta.status_code == 400
    assert client.get("/pedidos/P").json()["productos"] == []
    assert client.get("/pedidos").status_code == 200


def test_kpi_stock_no_desborda_al_sumar_depositos(client, tmp_path):
    """Verifica conteos con existencias cuyo total supera el entero SQLite."""
    from Backend.persistencia import InventarioSQLite
    from Backend.modelos.productos import Producto
    with InventarioSQLite(tmp_path / "api.db") as inv:
        inv.registrar_producto(Producto("PEQUENO", "Pequeño", 1e-20, 1))
        inv.actualizar_stock("D-001", "PEQUENO", 2**63 - 1)
        inv.actualizar_stock("D-002", "PEQUENO", 1)
    assert client.get("/reportes/kpis").json()["productos_con_stock"] == 5
