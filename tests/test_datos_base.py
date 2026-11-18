"""Verifica la carga SQL inicial, su atomicidad y su ejecución única."""
import sqlite3
from pathlib import Path
from contextlib import closing

from Backend.persistencia import InventarioSQLite
from Backend.pedidos import PedidosSQLite
from Backend.flota import FlotaSQLite

SCHEMA = Path(__file__).resolve().parents[1] / "Backend/schema.sql"


def comprobar_base(conexion):
    """Comprueba conteos, asignaciones y claves foráneas de la base inicial.

    Args:
        conexion (sqlite3.Connection): Conexión que contiene los valores de schema.sql.
    """
    for tabla in ("productos", "depositos", "conductores", "vehiculos", "pedidos", "pedido_items", "existencias"):
        assert conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0] == 3, tabla
    assert conexion.execute("SELECT COUNT(*) FROM vehiculos WHERE dni_conductor IS NOT NULL AND estado='Disponible'").fetchone()[0] == 3
    assert conexion.execute("SELECT COUNT(*) FROM pedidos WHERE estado='Borrador'").fetchone()[0] == 3
    assert not conexion.execute("PRAGMA foreign_key_check").fetchall()


def test_schema_directo_crea_tres_de_cada_entidad():
    """Comprueba el conjunto inicial al ejecutar el schema completo directamente."""
    with closing(sqlite3.connect(":memory:")) as c:
        c.executescript(SCHEMA.read_text(encoding="utf-8"))
        comprobar_base(c)


def test_base_se_carga_una_vez_y_no_repone_stock(tmp_path):
    """Verifica que reabrir conserve un retiro y una cancelación ya guardados."""
    db = tmp_path / "base.db"
    with InventarioSQLite(db) as inv:
        assert inv.cargar_datos_base() is True
        comprobar_base(inv.conexion)
        inv.actualizar_stock("D-001", "PRD-1", -1)
        PedidosSQLite(inv).cancelar("P-001")
    with InventarioSQLite(db) as inv:
        assert inv.cargar_datos_base() is False
        assert inv.stock("D-001", "PRD-1") == 199
        assert PedidosSQLite(inv).obtener_pedido("P-001").estado == "Cancelado"
        assert len(inv.listar_productos()) == 3


def test_schema_repetido_no_recrea_producto_eliminado():
    """Comprueba que repetir el schema no regenere un producto eliminado."""
    with closing(sqlite3.connect(":memory:")) as c:
        sql = SCHEMA.read_text(encoding="utf-8")
        c.executescript(sql)
        comprobar_base(c)
        c.execute("DELETE FROM pedido_items WHERE id_producto='PRD-1'")
        c.execute("DELETE FROM existencias WHERE id_producto='PRD-1'")
        c.execute("DELETE FROM productos WHERE id_producto='PRD-1'")
        c.commit()
        c.executescript(sql)
        assert c.execute("SELECT COUNT(*) FROM productos WHERE id_producto='PRD-1'").fetchone()[0] == 0


def test_carga_no_modifica_una_base_con_datos_propios(inventario):
    """Verifica que la inicialización respete un catálogo existente del usuario."""
    assert inventario.cargar_datos_base() is False
    assert [p.id_producto for p in inventario.listar_productos()] == ["P1"]
    assert inventario.stock("D1", "P1") == 200


def test_error_en_carga_revierte_datos_y_permite_reintentar():
    """Comprueba reversión completa y reintento de una carga SQL fallida."""
    import pytest
    with InventarioSQLite(":memory:") as inv:
        inv.conexion.execute("""CREATE TRIGGER impedir_carga BEFORE INSERT ON conductores
            BEGIN SELECT RAISE(ABORT, 'fallo simulado'); END""")
        with pytest.raises(sqlite3.IntegrityError):
            inv.cargar_datos_base()
        assert inv.listar_productos() == []
        assert inv.listar_depositos() == []
        inv.conexion.execute("DROP TRIGGER impedir_carga")
        assert inv.cargar_datos_base() is True
        comprobar_base(inv.conexion)


def test_pedidos_iniciales_pueden_completar_el_circuito():
    """Verifica que los tres pedidos iniciales puedan entregarse correctamente."""
    with InventarioSQLite(":memory:") as inv:
        inv.cargar_datos_base()
        p = PedidosSQLite(inv)
        f = FlotaSQLite(inv)
        for pedido, vehiculo in zip(p.listar_pedidos(), f.listar_vehiculos(), strict=True):
            p.confirmar(pedido.id_pedido)
            p.asignar_vehiculo(pedido.id_pedido, vehiculo.patente)
            p.despachar(pedido.id_pedido)
            p.entregar(pedido.id_pedido)
            assert p.obtener_pedido(pedido.id_pedido).entrega.estado == "Completada"
            assert f.obtener_vehiculo(vehiculo.patente).estado == "Disponible"
        assert inv.stock("D-001", "PRD-1") == 195
        assert inv.stock("D-002", "PRD-2") == 97
        assert inv.stock("D-003", "PRD-3") == 290


def test_carga_no_confirma_transacciones_ajenas():
    """Comprueba que inicializar no confirme una transacción del llamador."""
    import pytest
    with InventarioSQLite(":memory:") as inv:
        inv.conexion.execute("BEGIN")
        inv.conexion.execute("INSERT INTO productos VALUES ('PROPIO','Propio',1,1)")
        with pytest.raises(ValueError, match="transacción"):
            inv.cargar_datos_base()
        assert inv.conexion.in_transaction
        inv.conexion.rollback()
        assert inv.listar_productos() == []


def test_restriccion_adicional_no_se_silencia_ni_deja_carga_parcial():
    """Verifica rollback ante restricciones adicionales sin omitir inserciones."""
    import pytest
    with InventarioSQLite(":memory:") as inv:
        inv.conexion.execute("CREATE UNIQUE INDEX un_solo_estado ON vehiculos(estado)")
        with pytest.raises(sqlite3.IntegrityError):
            inv.cargar_datos_base()
        assert inv.listar_productos() == []
        assert inv.listar_depositos() == []
        assert FlotaSQLite(inv).listar_vehiculos() == []
