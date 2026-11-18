"""Prueba formularios, navegación y manejo de errores de la consola."""
import pytest

from Backend.consola import MenuConsola, ejecutar_menu, mostrar_flota, mostrar_inventario, mostrar_pedidos
from Backend.pedidos import PedidosSQLite
from Backend.persistencia import InventarioSQLite


def entradas(monkeypatch, respuestas):
    """Sustituye la entrada de terminal por respuestas ordenadas de prueba.

    Args:
        monkeypatch (pytest.MonkeyPatch): Reemplazos restaurados al finalizar.
        respuestas (list[str]): Respuestas que consume cada llamada a input.
    """
    iterator = iter(respuestas)
    monkeypatch.setattr("builtins.input", lambda _mensaje: next(iterator))


@pytest.mark.parametrize("valor", ["abc", "0", "-1", "1.5", "4"])
def test_enteros_invalidos(inventario, monkeypatch, valor):
    """Comprueba el rechazo de enteros mal formados o fuera del rango permitido."""
    entradas(monkeypatch, [valor])
    with pytest.raises(ValueError):
        MenuConsola(inventario)._entero("Cantidad", maximo=3)


@pytest.mark.parametrize("valor", ["0", "-1", "nan", "inf", "texto"])
def test_medidas_invalidas(inventario, monkeypatch, valor):
    """Verifica el rechazo de medidas no positivas, no finitas o no numéricas."""
    entradas(monkeypatch, [valor])
    with pytest.raises(ValueError):
        MenuConsola(inventario)._medida("Volumen")


def test_valores_opcionales_decimal_y_estado(inventario, monkeypatch):
    """Comprueba opcionales, valores por defecto, coma decimal y elección de estado."""
    entradas(monkeypatch, ["", "", "1,5", "2", " "])
    m = MenuConsola(inventario)
    assert m._opcional("Nota") is None
    assert m._entero("Prioridad", defecto=1) == 1
    assert m._medida("Medida") == 1.5
    assert m._estado(("Disponible", "Inactivo")) == "Inactivo"
    with pytest.raises(ValueError):
        m._texto("Obligatorio")


def test_menu_cancelacion_y_errores_no_cierran_sesion(inventario, monkeypatch, capsys):
    """Verifica que errores y cancelación permitan seguir usando el menú."""
    entradas(monkeypatch, ["inventado", "1", "2", "/volver", "2", "P1", "Otro", "1", "1",
                            "2", "NUEVO", "Nombre", "no-numero", "0", "0"])
    ejecutar_menu(inventario)
    salida = capsys.readouterr().out
    assert "opción inválida" in salida and "Carga cancelada" in salida
    assert "ya existe" in salida and "número positivo" in salida
    assert len(inventario.listar_productos()) == 1


def test_menus_inventario_flota_y_consultas(inventario, monkeypatch):
    """Recorre altas, movimientos, flota y consultas mediante entradas de consola."""
    entradas(monkeypatch, ["1", "2", "P2", "Segundo", "0.2", "1", "3", "D2", "Sur", "Sur", "10",
        "4", "D2", "P2", "5", "5", "D2", "P2", "2", "6", "D2", "D1", "P2", "1", "1", "0",
        "3", "2", "ZZZ", "5", "3", "456", "Luis", "4", "ZZZ", "456", "5", "ZZZ",
        "6", "ZZZ", "3", "7", "456", "2", "1", "0", "2", "1", "2", "NO", "0", "0"])
    ejecutar_menu(inventario)
    assert inventario.stock("D2", "P2") == 2
    assert inventario.stock("D1", "P2") == 1


@pytest.mark.parametrize("interrupcion", [EOFError, KeyboardInterrupt])
def test_eof_y_control_c_conservan_sesion(inventario, monkeypatch, capsys, interrupcion):
    """Verifica una salida limpia ante EOF o Ctrl+C sin perder datos guardados."""
    def interrumpir(_mensaje):
        """Simula el cierre o la interrupción de la entrada de consola.

        Args:
            _mensaje (str): Solicitud de entrada, sin uso en esta simulación.
        """
        raise interrupcion
    monkeypatch.setattr("builtins.input", interrumpir)
    ejecutar_menu(inventario)
    assert "Sesión finalizada" in capsys.readouterr().out
    assert inventario.stock("D1", "P1") == 200


def test_error_de_acceso_sqlite_no_muestra_traceback(inventario, monkeypatch, capsys):
    """Comprueba el mensaje de acceso ante una conexión SQLite cerrada."""
    inventario.close()
    entradas(monkeypatch, ["1", "1", "0", "0"])
    ejecutar_menu(inventario)
    assert "no se pudo acceder" in capsys.readouterr().out


def test_detalle_borrador_muestra_horarios_notas_y_vacio(inventario, monkeypatch, capsys):
    """Comprueba los datos opcionales y el detalle de un borrador sin ítems."""
    p = PedidosSQLite(inventario)
    p.crear_borrador("P", "Cliente", "Destino", hora_inicio="08:00", hora_fin="12:00", observaciones="Nota")
    entradas(monkeypatch, ["P"])
    MenuConsola(inventario)._detalle_pedido()
    texto = capsys.readouterr().out
    assert "08:00 - 12:00" in texto and "Nota" in texto and "Sin productos" in texto


def test_consultas_vacias_y_detalle_con_items(inventario, monkeypatch, capsys):
    """Verifica consultas vacías y representación de cantidades en un pedido."""
    with InventarioSQLite(":memory:") as vacio:
        mostrar_flota(vacio)
        mostrar_inventario(vacio)
        mostrar_pedidos(vacio)
    assert "No hay vehículos" in capsys.readouterr().out
    p = PedidosSQLite(inventario)
    p.crear_borrador("P", "Cliente", "Destino")
    p.establecer_producto("P", "D1", "P1", 2)
    entradas(monkeypatch, ["P"])
    MenuConsola(inventario)._detalle_pedido()
    assert "2 unidades" in capsys.readouterr().out
