"""Verifica la interfaz en Chromium con servidor y base temporales."""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest

pytestmark = [pytest.mark.browser, pytest.mark.skipif(os.environ.get("RUN_BROWSER_TESTS") != "1", reason="Activar RUN_BROWSER_TESTS=1 para ejecutar Chromium")]
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def server(tmp_path):
    """Inicia Uvicorn con base temporal y detiene el proceso al finalizar.

    Espera disponibilidad con un plazo limitado y utiliza un puerto local libre.

    Args:
        tmp_path (Path): Directorio para base y registro del servidor.

    Yields:
        str: URL base del servidor temporal.
    """
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "LOGISTICA_DB": str(tmp_path / "web.db")}
    with (tmp_path / "servidor.log").open("w", encoding="utf-8") as log:
        proceso = subprocess.Popen([sys.executable, "-m", "uvicorn", "Backend.api:app", "--host", "127.0.0.1", "--port", str(port)],
                                   cwd=ROOT, env=env, stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        base = f"http://127.0.0.1:{port}"
        try:
            limite = time.monotonic() + 20
            while time.monotonic() < limite:
                if proceso.poll() is not None:
                    pytest.fail("El servidor no arrancó: " + (tmp_path / "servidor.log").read_text(encoding="utf-8"))
                try:
                    with urlopen(base + "/productos", timeout=1) as respuesta:
                        if respuesta.status == 200:
                            break
                except (URLError, TimeoutError):
                    time.sleep(0.1)
            else:
                pytest.fail("Tiempo agotado esperando al servidor")
            yield base
        finally:
            proceso.terminate()
            try:
                proceso.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proceso.kill()
                proceso.wait(timeout=5)


@pytest.fixture
def page():
    """Abre Chromium y detecta errores JavaScript de la página.

    Yields:
        Page: Pestaña de prueba; el navegador se cierra al terminar.
    """
    from playwright.sync_api import sync_playwright
    browsers = ROOT / ".venv/browsers"
    if browsers.exists():
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(browsers))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pagina = browser.new_page(viewport={"width": 1280, "height": 900})
        errores = []
        pagina.on("pageerror", lambda error: errores.append(str(error)))
        yield pagina
        browser.close()
        assert not errores, errores


def crear_borrador(page, server, identificador):
    """Completa el formulario web y espera un borrador guardado.

    Args:
        page (Page): Pestaña de Chromium.
        server (str): URL del servidor temporal.
        identificador (str): ID del nuevo pedido.
    """
    page.goto(server + "/cargas.html")
    page.get_by_label("ID del pedido", exact=True).fill(identificador)
    page.get_by_label("Cliente", exact=True).fill("Cliente de prueba")
    page.get_by_label("Destino", exact=True).fill("Av. Siempre Viva 123")
    page.get_by_label("Observaciones", exact=True).fill("Avisar al llegar")
    page.get_by_role("button", name="Guardar datos y continuar", exact=True).click()
    page.locator("#pedido-estado").filter(has_text="Borrador").wait_for()


def test_nuevo_pedido_continua_con_productos_sin_buscar_codigo(page, server):
    """Completa los tres pasos en el mismo bloque y conserva el avance al recargar."""
    from playwright.sync_api import expect
    page.goto(server + "/cargas.html")
    flujo = page.get_by_role("region", name="Nuevo pedido", exact=True)
    expect(flujo).to_be_visible()
    expect(page.locator("#pasos-pedido [aria-current='step']")).to_have_text("1. Datos")
    expect(page.get_by_label("Código para recuperar", exact=True)).to_be_hidden()
    crear_borrador(page, server, "CONTINUO")
    expect(flujo.get_by_role("heading", name="2. Productos", exact=True)).to_be_focused()
    expect(page.locator("#pasos-pedido [aria-current='step']")).to_have_text("2. Productos")
    expect(page.get_by_role("button", name="Confirmar pedido", exact=True)).to_be_disabled()
    page.get_by_label("Producto del pedido", exact=True).select_option("PRD-1")
    page.get_by_label("Depósito de origen", exact=True).select_option("D-001")
    page.get_by_label("Cantidad total", exact=True).fill("2")
    page.get_by_role("button", name="Guardar cantidad", exact=True).click()
    expect(flujo.locator("#items-body")).to_contain_text("Pantalón")
    expect(page.get_by_role("button", name="Confirmar pedido", exact=True)).to_be_enabled()
    page.reload()
    expect(flujo.locator("#items-body")).to_contain_text("Pantalón")
    expect(page.locator("#pedido-titulo")).to_contain_text("CONTINUO")
    page.get_by_role("button", name="Confirmar pedido", exact=True).click()
    expect(page.locator("#pedido-estado")).to_have_text("Confirmado")
    expect(page.locator("#pasos-pedido [aria-current='step']")).to_have_text("3. Confirmación")
    page.get_by_role("link", name="Crear otro pedido", exact=True).click()
    expect(page.get_by_label("ID del pedido", exact=True)).to_have_value("")
    expect(page.locator("#pasos-pedido [aria-current='step']")).to_have_text("1. Datos")
    assert page.request.get(server + "/pedidos/CONTINUO").json()["estado"] == "Confirmado"


def test_alta_abre_productos_sin_consultar_otra_vez_el_pedido(page, server):
    """Usa la respuesta del alta para continuar aunque falle una consulta posterior."""
    from playwright.sync_api import expect
    page.route("**/pedidos/SIN-CONSULTA", lambda route: route.abort())
    crear_borrador(page, server, "SIN-CONSULTA")
    expect(page.get_by_label("Producto del pedido", exact=True)).to_be_visible()
    expect(page.locator("#crear-seccion")).to_be_hidden()
    expect(page.locator("#mensaje")).to_contain_text("Borrador creado")
    assert page.request.get(server + "/pedidos/SIN-CONSULTA").status == 200


def test_retomar_pedido_existente_abre_el_mismo_flujo(page, server):
    """Recupera un borrador existente desde el bloque separado y conserva su URL."""
    from playwright.sync_api import expect
    page.goto(server + "/cargas.html")
    page.get_by_text("Retomar un pedido existente", exact=True).click()
    page.get_by_label("Código para recuperar", exact=True).fill("P-002")
    page.get_by_role("button", name="Abrir pedido", exact=True).click()
    expect(page.locator("#pedido-titulo")).to_contain_text("P-002")
    expect(page.locator("#items-body")).to_contain_text("Campera")
    expect(page.get_by_label("Código para recuperar", exact=True)).to_be_hidden()
    page.reload()
    expect(page.locator("#pedido-titulo")).to_contain_text("P-002")
    expect(page.locator("#items-body")).to_contain_text("Campera")


def test_guardado_con_fallo_al_actualizar_flota_conserva_pedido_y_url(page, server):
    """Mantiene el pedido guardado y recuperable si la actualización de flota falla."""
    from playwright.sync_api import expect
    crear_borrador(page, server, "CONTEXTO")
    page.get_by_label("Producto del pedido", exact=True).select_option("PRD-1")
    page.get_by_label("Depósito de origen", exact=True).select_option("D-001")
    page.get_by_label("Cantidad total", exact=True).fill("2")
    page.route("**/vehiculos", lambda route: route.abort())
    page.get_by_role("button", name="Guardar cantidad", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("Cantidad guardada")
    expect(page.locator("#items-body")).to_contain_text("Pantalón")
    assert page.url.endswith("?pedido=CONTEXTO")
    page.unroute("**/vehiculos")
    page.reload()
    expect(page.locator("#pedido-titulo")).to_contain_text("CONTEXTO")
    expect(page.locator("#items-body")).to_contain_text("Pantalón")


def test_confirmacion_con_productos_no_anuncia_aviso_de_pedido_vacio(page, server):
    """Deja de describir como vacío un pedido que ya puede confirmarse."""
    from playwright.sync_api import expect
    page.goto(server + "/cargas.html?pedido=P-001")
    boton = page.get_by_role("button", name="Confirmar pedido", exact=True)
    expect(boton).to_be_enabled()
    expect(boton).to_have_accessible_description("")


def test_espacio_depositos_separado_de_productos_y_actualizado_al_ingresar(page, server):
    """Muestra cada depósito una vez y refresca su espacio tras un ingreso válido."""
    from playwright.sync_api import expect
    page.goto(server + "/gestion.html")
    tabla = page.get_by_role("table", name="Espacio de los depósitos", exact=True)
    centro = tabla.get_by_role("row").filter(has_text="Depósito Centro")
    expect(tabla.get_by_role("row")).to_have_count(4)
    expect(centro.get_by_role("cell")).to_have_text(["Depósito Centro", "50", "0,8", "49,2"])
    page.get_by_label("Buscar por ID o nombre", exact=True).fill("NO-EXISTE")
    page.get_by_label("Filtrar depósito", exact=True).select_option("D-002")
    expect(page.locator("#sin-productos")).to_be_visible()
    expect(tabla.get_by_role("row")).to_have_count(4)
    page.get_by_label("Producto para ingreso", exact=True).select_option("PRD-1")
    page.get_by_label("Depósito para ingreso", exact=True).select_option("D-001")
    page.get_by_label("Cantidad a ingresar", exact=True).fill("50")
    page.get_by_role("button", name="Ingresar mercadería", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("Ingreso registrado")
    expect(centro.get_by_role("cell")).to_have_text(["Depósito Centro", "50", "1", "49"])
    page.get_by_label("Cantidad a ingresar", exact=True).fill("13000")
    page.get_by_role("button", name="Ingresar mercadería", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("supera la capacidad")
    expect(centro.get_by_role("cell")).to_have_text(["Depósito Centro", "50", "1", "49"])
    page.reload()
    expect(centro.get_by_role("cell")).to_have_text(["Depósito Centro", "50", "1", "49"])
    page.set_viewport_size({"width": 375, "height": 900})
    tabla.scroll_into_view_if_needed()
    expect(centro.get_by_role("cell", name="49", exact=True)).to_be_in_viewport()


def test_circuito_completo_por_navegador(page, server):
    """Recorre alta, faltante, corrección, despacho y entrega desde la web."""
    from playwright.sync_api import expect
    page.goto(server + "/gestion.html")
    page.get_by_label("ID del producto", exact=True).fill("NUEVO")
    page.get_by_label("Nombre del producto", exact=True).fill("<img src=x onerror=alert(1)>")
    page.get_by_label("Volumen unitario (m³)", exact=True).fill("0.1")
    page.get_by_label("Peso unitario (kg)", exact=True).fill("1")
    page.get_by_role("button", name="Registrar producto", exact=True).click()
    expect(page.locator("#productos-body")).to_contain_text("<img src=x onerror=alert(1)>")
    assert page.locator("#productos-body img").count() == 0
    page.get_by_label("Producto para ingreso", exact=True).select_option("NUEVO")
    page.get_by_label("Depósito para ingreso", exact=True).select_option("D-001")
    page.get_by_label("Cantidad a ingresar", exact=True).fill("5")
    page.get_by_role("button", name="Ingresar mercadería", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("Ingreso registrado")
    crear_borrador(page, server, "WEB")
    page.get_by_label("Producto del pedido", exact=True).select_option("NUEVO")
    page.get_by_label("Depósito de origen", exact=True).select_option("D-001")
    page.get_by_label("Cantidad total", exact=True).fill("6")
    page.get_by_role("button", name="Guardar cantidad", exact=True).click()
    expect(page.locator("#items-body")).to_contain_text("6")
    page.get_by_role("button", name="Confirmar pedido", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("faltan 1")
    expect(page.locator("#pedido-estado")).to_have_text("Borrador")
    page.get_by_label("Cantidad total", exact=True).fill("4")
    page.get_by_role("button", name="Guardar cantidad", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("Cantidad guardada")
    page.reload()
    expect(page.locator("#items-body")).to_contain_text("4")
    page.get_by_role("button", name="Confirmar pedido", exact=True).click()
    expect(page.locator("#pedido-estado")).to_have_text("Confirmado")
    page.get_by_label("Vehículo disponible", exact=True).select_option("AB123CD")
    page.get_by_role("button", name="Asignar vehículo", exact=True).click()
    expect(page.locator("#vehiculo-actual")).to_have_text("AB123CD")
    page.get_by_role("button", name="Despachar pedido", exact=True).click()
    expect(page.locator("#pedido-estado")).to_have_text("Despachado")
    page.get_by_role("link", name="Ver seguimiento", exact=True).click()
    expect(page.locator("#seguimiento-estado")).to_have_text("Despachado")
    page.get_by_role("button", name="Marcar como entregado", exact=True).click()
    expect(page.locator("#seguimiento-estado")).to_have_text("Entregado")
    page.reload()
    expect(page.locator("#seguimiento-estado")).to_have_text("Entregado")
    respuesta = page.request.get(server + "/stock").json()
    fila = next(f for f in respuesta if f["id_producto"] == "NUEVO" and f["id_deposito"] == "D-001")
    assert (fila["fisico"], fila["reservado"], fila["disponible"]) == (1, 0, 1)
    page.goto(server + "/index.html")
    expect(page.locator("#kpi-entregados")).to_have_text("1")
    expect(page.locator("#pedidos-body")).to_contain_text("WEB")


def test_cancelacion_y_busqueda_inexistente(page, server):
    """Verifica cancelación y búsqueda fallida sin mostrar una entrega anterior."""
    from playwright.sync_api import expect
    crear_borrador(page, server, "CANCELAR")
    page.get_by_role("button", name="Cancelar pedido", exact=True).click()
    expect(page.locator("#pedido-estado")).to_have_text("Cancelado")
    page.get_by_role("link", name="Ver seguimiento", exact=True).click()
    expect(page.locator("#seguimiento-estado")).to_have_text("Cancelado")
    expect(page.get_by_role("button", name="Marcar como entregado", exact=True)).to_be_hidden()
    page.get_by_label("Código del pedido", exact=True).fill("INEXISTENTE")
    page.get_by_role("button", name="Buscar pedido", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("No existe")
    expect(page.locator("#seguimiento-detalle")).to_be_hidden()


def test_error_red_no_anuncia_guardado(page, server):
    """Comprueba que un fallo de red conserve el formulario y permita reintentar."""
    from playwright.sync_api import expect
    page.goto(server + "/gestion.html")
    expect(page.locator("#productos-body")).to_contain_text("PRD-1")
    page.route("**/productos", lambda route: route.abort())
    page.get_by_label("ID del producto", exact=True).fill("FALLO")
    page.get_by_label("Nombre del producto", exact=True).fill("Conservar formulario")
    page.get_by_label("Volumen unitario (m³)", exact=True).fill("1")
    page.get_by_label("Peso unitario (kg)", exact=True).fill("1")
    page.get_by_role("button", name="Registrar producto", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("conectar")
    expect(page.get_by_label("Nombre del producto", exact=True)).to_have_value("Conservar formulario")
    expect(page.get_by_role("button", name="Registrar producto", exact=True)).to_be_enabled()


def preparar_ingreso(page, server):
    """Carga Gestión y prepara un ingreso de cinco unidades.

    Args:
        page (Page): Pestaña de Chromium.
        server (str): URL del servidor temporal.
    """
    from playwright.sync_api import expect
    page.goto(server + "/gestion.html")
    expect(page.locator("#productos-body")).to_contain_text("PRD-1")
    page.get_by_label("Producto para ingreso", exact=True).select_option("PRD-1")
    page.get_by_label("Depósito para ingreso", exact=True).select_option("D-001")
    page.get_by_label("Cantidad a ingresar", exact=True).fill("5")


def test_ingreso_guardado_y_refresco_fallido_no_invita_a_duplicar(page, server):
    """Distingue un ingreso confirmado del fallo posterior al refrescar la tabla."""
    from playwright.sync_api import expect
    preparar_ingreso(page, server)
    page.route("**/stock", lambda route: route.abort())
    page.get_by_role("button", name="Ingresar mercadería", exact=True).click()
    expect(page.get_by_label("Cantidad a ingresar", exact=True)).to_have_value("")
    expect(page.locator("#mensaje")).to_contain_text("Ingreso registrado")
    expect(page.locator("#mensaje")).to_contain_text("actualizar")
    fila = next(f for f in page.request.get(server + "/stock").json() if f["id_producto"] == "PRD-1" and f["id_deposito"] == "D-001")
    assert fila["fisico"] == 205


def test_respuesta_perdida_y_reintento_de_ingreso_no_duplica(page, server):
    """Verifica el reintento de un ingreso tras perder la respuesta y recargar."""
    from playwright.sync_api import expect
    preparar_ingreso(page, server)
    def perder_respuesta(route):
        """Ejecuta el ingreso en el servidor y oculta su respuesta al navegador.

        Args:
            route (Route): Solicitud interceptada por Playwright.
        """
        route.fetch()
        route.abort()
    page.route("**/stock/ingresos", perder_respuesta, times=1)
    page.get_by_role("button", name="Ingresar mercadería", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("conectar")
    page.reload()
    # Reingresar la misma operación después de perder la respuesta y recargar.
    expect(page.locator("#productos-body")).to_contain_text("PRD-1")
    page.get_by_label("Producto para ingreso", exact=True).select_option("PRD-1")
    page.get_by_label("Depósito para ingreso", exact=True).select_option("D-001")
    page.get_by_label("Cantidad a ingresar", exact=True).fill("5")
    page.get_by_role("button", name="Ingresar mercadería", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("Ingreso registrado")
    fila = next(f for f in page.request.get(server + "/stock").json() if f["id_producto"] == "PRD-1" and f["id_deposito"] == "D-001")
    assert fila["fisico"] == 205


def test_recuperacion_fallida_oculta_pedido_anterior(page, server):
    """Comprueba que una recuperación fallida oculte las acciones del pedido previo."""
    from playwright.sync_api import expect
    crear_borrador(page, server, "ANTERIOR")
    page.get_by_text("Retomar un pedido existente", exact=True).click()
    page.get_by_label("Código para recuperar", exact=True).fill("INEXISTENTE")
    page.get_by_role("button", name="Abrir pedido", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("No existe")
    expect(page.locator("#pedido-detalle")).to_be_hidden()
    expect(page.get_by_label("ID del pedido", exact=True)).to_be_visible()
    assert page.request.get(server + "/pedidos/ANTERIOR").json()["estado"] == "Borrador"


def test_validacion_de_identificadores_en_formulario(page, server):
    """Comprueba el patrón HTML para identificadores válidos e inválidos."""
    page.goto(server + "/gestion.html")
    campo = page.get_by_label("ID del producto", exact=True)
    campo.fill("NO/VALIDO")
    assert campo.evaluate("el => el.validity.patternMismatch")
    campo.fill("SI-VALIDO_1")
    assert not campo.evaluate("el => el.validity.patternMismatch")


def test_filtros_por_nombre_y_deposito(page, server):
    """Verifica búsqueda sin distinción de mayúsculas y filtro por depósito."""
    from playwright.sync_api import expect
    page.goto(server + "/gestion.html")
    expect(page.locator("#productos-body")).to_contain_text("PRD-2")
    page.get_by_label("Buscar por ID o nombre", exact=True).fill("CAMPERA")
    page.get_by_label("Filtrar depósito", exact=True).select_option("D-002")
    expect(page.locator("#productos-body tr")).to_have_count(1)
    expect(page.locator("#productos-body")).to_contain_text("100")
    page.get_by_label("Buscar por ID o nombre", exact=True).fill("NO EXISTE")
    expect(page.locator("#sin-productos")).to_be_visible()
    expect(page.locator("#productos-body tr")).to_have_count(0)


def test_doble_envio_solo_confirma_una_vez(page, server):
    """Comprueba el bloqueo de envíos repetidos y la reserva única de stock."""
    from playwright.sync_api import expect
    page.goto(server + "/cargas.html?pedido=P-001")
    expect(page.locator("#pedido-estado")).to_have_text("Borrador")
    peticiones = []
    page.on("request", lambda r: peticiones.append(r.url) if r.method == "POST" and r.url.endswith("/confirmar") else None)
    page.locator("#confirmar-form").evaluate("form => { form.requestSubmit(); form.requestSubmit(); }")
    expect(page.locator("#pedido-estado")).to_have_text("Confirmado")
    assert len(peticiones) == 1
    expect(page.get_by_role("button", name="Guardar cantidad", exact=True)).to_be_disabled()
    expect(page.get_by_role("button", name="Cancelar pedido", exact=True)).to_be_visible()
    fila = next(s for s in page.request.get(server + "/stock").json() if s["id_deposito"] == "D-001" and s["id_producto"] == "PRD-1")
    assert fila["reservado"] == 5 and fila["fisico"] == 200


def test_busqueda_inicio_y_error_de_respuesta_invalida(page, server):
    """Verifica navegación desde Inicio y el mensaje ante una respuesta no JSON."""
    from playwright.sync_api import expect
    page.goto(server + "/index.html")
    expect(page.locator("#kpi-pendientes")).to_have_text("3")
    page.get_by_role("link", name="P-002", exact=True).click()
    expect(page.locator("#seguimiento-estado")).to_have_text("Borrador")
    expect(page.locator("#seguimiento-ventana")).to_contain_text("10:00")
    page.route("**/productos", lambda r: r.fulfill(status=200, content_type="text/plain", body="respuesta inválida"))
    page.goto(server + "/gestion.html")
    expect(page.locator("#mensaje")).to_contain_text("respuesta válida")


def test_alta_duplicada_preserva_formulario_y_catalogo(page, server):
    """Comprueba que un duplicado conserve el formulario sin sobrescribir datos."""
    from playwright.sync_api import expect
    page.goto(server + "/gestion.html")
    page.get_by_label("ID del producto", exact=True).fill("PRD-1")
    page.get_by_label("Nombre del producto", exact=True).fill("No sobrescribir")
    page.get_by_label("Volumen unitario (m³)", exact=True).fill("1")
    page.get_by_label("Peso unitario (kg)", exact=True).fill("1")
    page.get_by_role("button", name="Registrar producto", exact=True).click()
    expect(page.locator("#mensaje")).to_contain_text("ya existe")
    expect(page.get_by_label("Nombre del producto", exact=True)).to_have_value("No sobrescribir")
    assert len(page.request.get(server + "/productos").json()) == 3


@pytest.mark.parametrize("ancho", [390, 1280])
def test_layout_sin_desborde(page, server, ancho):
    """Verifica el ancho de página y captura las cuatro pantallas para revisión."""
    page.set_viewport_size({"width": ancho, "height": 900})
    salida = ROOT / "test-results"
    salida.mkdir(exist_ok=True)
    for pagina in ("index.html", "gestion.html", "cargas.html", "seguimiento.html"):
        page.goto(server + "/" + pagina)
        page.wait_for_load_state("networkidle")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), pagina
        page.screenshot(path=str(salida / f"{ancho}-{pagina}.png"), full_page=True)
