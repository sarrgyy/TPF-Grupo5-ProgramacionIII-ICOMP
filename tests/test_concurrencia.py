"""Comprueba exclusión de recursos e inicialización ante operaciones simultáneas."""
from concurrent.futures import ThreadPoolExecutor

from Backend.persistencia import InventarioSQLite
from Backend.pedidos import PedidosSQLite


def test_ocho_inicializaciones_crean_una_sola_base(tmp_path):
    """Comprueba una única carga con ocho conexiones que inician simultáneamente."""
    db = tmp_path / "simultanea.db"
    def inicializar(_):
        """Intenta inicializar la base compartida desde una conexión independiente.

        Args:
            _ (int): Índice del trabajador; no altera el escenario.

        Returns:
            bool: True únicamente para la conexión que cargó los valores.
        """
        with InventarioSQLite(db) as inv:
            return inv.cargar_datos_base()
    with ThreadPoolExecutor(max_workers=8) as pool:
        resultados = list(pool.map(inicializar, range(8)))
    assert resultados.count(True) == 1
    with InventarioSQLite(db) as inv:
        for tabla in ("productos", "depositos", "conductores", "vehiculos", "pedidos", "pedido_items", "existencias"):
            assert inv.conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0] == 3
        assert inv.conexion.execute("SELECT COUNT(*) FROM inicializaciones").fetchone()[0] == 1


def test_dos_asignaciones_simultaneas_no_comparten_vehiculo(base_api):
    """Verifica exclusión de vehículo ante dos asignaciones concurrentes."""
    with InventarioSQLite(base_api) as inv:
        p = PedidosSQLite(inv)
        for codigo in ("A", "B"):
            p.crear_borrador(codigo, "C", "D")
            p.establecer_producto(codigo, "D-001", "PRD-1", 100)
            p.confirmar(codigo)
    def asignar(codigo):
        """Intenta ocupar el vehículo compartido desde otra conexión.

        Args:
            codigo (str): ID del pedido que compite por el vehículo.

        Returns:
            bool: True si obtuvo el vehículo; False si la regla de exclusión lo rechazó.
        """
        with InventarioSQLite(base_api) as inv:
            try:
                PedidosSQLite(inv).asignar_vehiculo(codigo, "AB123CD")
                return True
            except ValueError:
                return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(asignar, ["A", "B"])) == [False, True]
    with InventarioSQLite(base_api) as inv:
        assert inv.conexion.execute("SELECT COUNT(*) FROM pedidos WHERE patente_vehiculo='AB123CD'").fetchone()[0] == 1
        assert inv.stock_reservado("D-001", "PRD-1") == 200
