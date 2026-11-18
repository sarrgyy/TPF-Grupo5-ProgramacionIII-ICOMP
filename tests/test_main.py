"""Prueba arranque, ejemplos y migraciones usando archivos temporales."""
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

from Backend.persistencia import InventarioSQLite

ROOT = Path(__file__).resolve().parents[1]


def test_consola_carga_base_una_sola_vez(tmp_path):
    """Comprueba conteos iniciales iguales después de dos arranques de consola."""
    db = tmp_path / "vacia.db"
    for _ in range(2):
        resultado = subprocess.run([sys.executable, "-m", "Backend.main", "--db", str(db), "--resumen"],
                                   capture_output=True, text=True, cwd=ROOT, timeout=20)
        assert resultado.returncode == 0, resultado.stderr
        with InventarioSQLite(db) as inv:
            for tabla in ("productos", "depositos", "existencias", "pedidos", "pedido_items", "vehiculos", "conductores"):
                assert inv.conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0] == 3
            assert inv.conexion.execute("SELECT COUNT(*) FROM ingresos_stock").fetchone()[0] == 0


def test_ejemplo_en_memoria_sigue_siendo_ejecutable():
    """Verifica que el ejemplo sin archivos complete una entrega."""
    resultado = subprocess.run([sys.executable, "-m", "ejemplos.simulacion_en_memoria"],
                               capture_output=True, text=True, cwd=ROOT, timeout=20)
    assert resultado.returncode == 0, resultado.stderr
    assert "Entregado" in resultado.stdout


def test_arranque_y_persistencia_por_consola(tmp_path):
    """Recorre el ciclo por consola y comprueba conservación al reiniciar."""
    db = tmp_path / "consola.db"
    entradas = ["2", "3", "DEMO", "Cliente", "Destino", "1", "08:00", "12:00", "Nota",
                "5", "DEMO", "D-001", "PRD-1", "2", "7", "DEMO", "9", "DEMO", "AB123CD",
                "11", "DEMO", "12", "DEMO", "0", "0"]
    resultado = subprocess.run([sys.executable, "-m", "Backend.main", "--db", str(db)],
                               input="\n".join(entradas) + "\n", capture_output=True,
                               text=True, cwd=ROOT, timeout=20)
    assert resultado.returncode == 0, resultado.stderr
    assert "Error:" not in resultado.stdout
    with InventarioSQLite(db) as inv:
        assert inv.conexion.execute("SELECT estado FROM pedidos WHERE id_pedido='DEMO'").fetchone()[0] == "Entregado"
        assert inv.stock("D-001", "PRD-1") == 198
    for _ in range(2):
        resultado = subprocess.run([sys.executable, "-m", "Backend.main", "--db", str(db), "--resumen"],
                                   capture_output=True, text=True, cwd=ROOT, timeout=20)
        assert resultado.returncode == 0, resultado.stderr
        assert "Entregado" in resultado.stdout
    with InventarioSQLite(db) as inv:
        assert inv.stock("D-001", "PRD-1") == 198
        assert len(inv.listar_productos()) == 3


def test_migracion_conserva_datos_y_corrige_columna(tmp_path):
    """Verifica columnas horarias y conservación de las observaciones históricas."""
    db = tmp_path / "antigua.db"
    esquema = (ROOT / "Backend/schema.sql").read_text(encoding="utf-8")
    esquema = esquema.split("-- DATOS BASE", 1)[0]
    esquema = esquema.replace("    hora_inicio TEXT,\n", "").replace("    hora_fin TEXT,\n", "")
    esquema = esquema.replace("observaciones TEXT", "obvservaciones TEXT")
    with closing(sqlite3.connect(db)) as conexion:
        conexion.executescript(esquema)
        conexion.execute("INSERT INTO pedidos(id_pedido,cliente,destino,prioridad,obvservaciones) VALUES('LEGADO','C','D',1,'Conservar')")
        conexion.commit()
    with InventarioSQLite(db) as inv:
        fila = inv.conexion.execute("SELECT * FROM pedidos WHERE id_pedido='LEGADO'").fetchone()
        assert fila["observaciones"] == "Conservar"
        assert fila["hora_inicio"] is None
        assert fila["hora_fin"] is None


def test_migracion_agrega_patente_historica(tmp_path):
    """Comprueba la incorporación de patente a pedidos de una versión anterior."""
    db = tmp_path / "sin-flota-en-pedido.db"
    esquema = (ROOT / "Backend/schema.sql").read_text(encoding="utf-8").split("-- DATOS BASE", 1)[0]
    esquema = esquema.replace("    patente_vehiculo TEXT REFERENCES vehiculos(patente),\n", "")
    with closing(sqlite3.connect(db)) as c:
        c.executescript(esquema)
        c.execute("INSERT INTO pedidos(id_pedido,cliente,destino,prioridad) VALUES('LEGADO','C','D',1)")
        c.commit()
    with InventarioSQLite(db) as inv:
        assert inv.conexion.execute("SELECT patente_vehiculo FROM pedidos WHERE id_pedido='LEGADO'").fetchone()[0] is None


def test_migracion_incompatible_falla_sin_borrar_datos(tmp_path):
    """Verifica rechazo de datos incompatibles, conservación y cierre de conexión."""
    import pytest
    db = tmp_path / "incompatible.db"
    esquema = (ROOT / "Backend/schema.sql").read_text(encoding="utf-8").split("-- DATOS BASE", 1)[0]
    with closing(sqlite3.connect(db)) as c:
        c.executescript(esquema)
        c.execute("INSERT INTO vehiculos(patente,capacidad_maxima) VALUES('ABC',10)")
        for codigo in ("A", "B"):
            c.execute("INSERT INTO pedidos(id_pedido,cliente,destino,prioridad,estado,patente_vehiculo) VALUES(?,?,?,1,'Confirmado','ABC')", (codigo,"C","D"))
        c.commit()
    with pytest.raises(sqlite3.IntegrityError):
        InventarioSQLite(db)
    with closing(sqlite3.connect(db)) as c:
        assert c.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0] == 2
    # En Windows la eliminación también verifica que no quedó la conexión fallida abierta.
    db.unlink()
