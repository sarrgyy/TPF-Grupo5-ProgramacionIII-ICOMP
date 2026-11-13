import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

from Backend.modelos.deposito import Deposito
from Backend.modelos.productos import Producto
from Backend.persistencia import InventarioSQLite
from Backend.pedidos import PedidosSQLite, StockInsuficiente
from Backend.flota import FlotaSQLite
from Backend.modelos.conductor import Conductor
from Backend.modelos.vehiculo import Vehiculo


class PedidosTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "pedidos.db"
        self.inv = InventarioSQLite(self.ruta)
        self.addCleanup(self.inv.close)
        self.inv.cargar_iniciales(
            [Producto("P1", "Leche", 0.5, 1), Producto("P2", "Harina", 0.2, 1)],
            [Deposito("D1", "Central", "Sur", 100), Deposito("D2", "Centro", "Norte", 100)],
            [("D1", "P1", 50), ("D2", "P1", 40), ("D1", "P2", 20)],
        )
        self.pedidos = PedidosSQLite(self.inv)
        self.pedidos.crear_borrador("A", "Cliente", "Destino", 2)

    def cargar(self, id_pedido="A"):
        self.pedidos.establecer_producto(id_pedido, "D1", "P1", 50)
        self.pedidos.establecer_producto(id_pedido, "D2", "P1", 30)

    def asignar_para_despacho(self):
        flota = FlotaSQLite(self.inv)
        flota.registrar_vehiculo(Vehiculo("V1", 100))
        flota.registrar_conductor(Conductor("C1", "Conductor"))
        flota.asignar_conductor("V1", "C1")
        self.pedidos.asignar_vehiculo("A", "V1")

    def test_borrador_editable_y_recuperable(self):
        self.cargar()
        self.pedidos.editar_borrador("A", "Nuevo cliente", "Nueva dirección", 3)
        self.pedidos.establecer_producto("A", "D1", "P1", 45)
        self.pedidos.establecer_producto("A", "D1", "P2", 2)
        self.pedidos.quitar_producto("A", "D1", "P2")
        self.inv.close()
        with InventarioSQLite(self.ruta) as inv:
            pedidos = PedidosSQLite(inv)
            pedido = pedidos.obtener_pedido("A")
            self.assertEqual((pedido.cliente, pedido.destino, pedido.prioridad),
                             ("Nuevo cliente", "Nueva dirección", 3))
            self.assertEqual(pedido.estado, "Borrador")
            self.assertEqual(len(pedido.productos), 2)
            self.assertEqual(pedido.volumen_total, 37.5)
            self.assertEqual(len(pedidos.listar_pedidos()), 1)
            self.assertEqual(inv.stock_reservado("D1", "P1"), 0)

    def test_confirmacion_reserva_varios_depositos_sin_descontar_fisico(self):
        self.cargar()
        self.pedidos.confirmar("A")
        self.assertEqual(self.inv.stock("D1", "P1"), 50)
        self.assertEqual(self.inv.stock_reservado("D1", "P1"), 50)
        self.assertEqual(self.inv.stock_disponible("D1", "P1"), 0)
        self.assertEqual(self.inv.stock_disponible("D2", "P1"), 10)
        self.assertEqual(self.inv.obtener_deposito("D1").volumen_ocupado, 29)
        with InventarioSQLite(self.ruta) as otra:
            self.assertEqual(otra.stock_reservado("D2", "P1"), 30)
            self.assertEqual(PedidosSQLite(otra).obtener_pedido("A").estado, "Confirmado")

    def test_faltantes_completos_conservan_borrador_y_no_reservan(self):
        self.pedidos.establecer_producto("A", "D1", "P1", 55)
        self.pedidos.establecer_producto("A", "D2", "P1", 42)
        self.pedidos.establecer_producto("A", "D1", "P2", 1)
        with self.assertRaises(StockInsuficiente) as error:
            self.pedidos.confirmar("A")
        self.assertEqual([f["faltan"] for f in error.exception.faltantes], [5, 2])
        self.assertEqual(self.pedidos.obtener_pedido("A").estado, "Borrador")
        self.assertEqual(self.inv.stock_reservado("D1", "P2"), 0)
        self.pedidos.establecer_producto("A", "D1", "P1", 50)
        self.pedidos.establecer_producto("A", "D2", "P1", 40)
        self.pedidos.confirmar("A")

    def test_otro_pedido_retiros_y_traslados_respetan_reservas(self):
        self.pedidos.establecer_producto("A", "D1", "P1", 45)
        self.pedidos.confirmar("A")
        self.pedidos.crear_borrador("B", "Otro", "Destino")
        self.pedidos.establecer_producto("B", "D1", "P1", 6)
        with self.assertRaises(StockInsuficiente):
            self.pedidos.confirmar("B")
        with self.assertRaises(ValueError):
            self.inv.actualizar_stock("D1", "P1", -6)
        with self.assertRaises(ValueError):
            self.inv.transferir("D1", "D2", "P1", 6)
        self.inv.transferir("D1", "D2", "P1", 5)
        self.assertEqual(self.inv.stock("D1", "P1"), 45)
        self.assertEqual(self.inv.stock("D2", "P1"), 45)

    def test_cancelar_libera_reservas_sin_cambiar_stock(self):
        self.cargar()
        self.pedidos.confirmar("A")
        self.pedidos.cancelar("A")
        self.assertEqual(self.inv.stock_disponible("D1", "P1"), 50)
        self.assertEqual(self.inv.stock("D2", "P1"), 40)
        self.assertEqual(self.pedidos.obtener_pedido("A").estado, "Cancelado")
        self.assertEqual(len(self.pedidos.obtener_pedido("A").productos), 2)

    def test_cancelar_borrador_no_libera_reservas_de_otro(self):
        self.cargar()
        self.pedidos.confirmar("A")
        self.pedidos.crear_borrador("B", "Otro", "Destino")
        self.pedidos.cancelar("B")
        self.assertEqual(self.inv.stock_reservado("D1", "P1"), 50)

    def test_solo_borradores_se_editan(self):
        self.cargar()
        self.pedidos.confirmar("A")
        for operacion in [
            lambda: self.pedidos.editar_borrador("A", "Otro", "Otro"),
            lambda: self.pedidos.establecer_producto("A", "D1", "P1", 1),
            lambda: self.pedidos.quitar_producto("A", "D1", "P1"),
        ]:
            with self.assertRaises(ValueError):
                operacion()
        self.assertEqual(self.inv.stock_reservado("D1", "P1"), 50)

    def test_despacho_completo_unico_y_entrega(self):
        self.cargar()
        self.pedidos.confirmar("A")
        self.asignar_para_despacho()
        # La reserva de otro pedido sigue vigente al despachar A.
        self.pedidos.crear_borrador("B", "Otro", "Destino")
        self.pedidos.establecer_producto("B", "D2", "P1", 5)
        self.pedidos.confirmar("B")
        self.pedidos.despachar("A")
        self.assertEqual(self.inv.stock("D1", "P1"), 0)
        self.assertEqual(self.inv.stock("D2", "P1"), 10)
        self.assertEqual(self.inv.stock_reservado("D2", "P1"), 5)
        self.assertEqual(self.inv.stock_disponible("D2", "P1"), 5)
        for operacion in [self.pedidos.despachar, self.pedidos.cancelar]:
            with self.assertRaises(ValueError):
                operacion("A")
        self.pedidos.entregar("A")
        self.assertEqual(self.pedidos.obtener_pedido("A").estado, "Entregado")
        with self.assertRaises(ValueError):
            self.pedidos.entregar("A")
        self.assertEqual(self.inv.stock("D2", "P1"), 10)

    def test_despacho_fallido_revierte_todos_los_movimientos(self):
        self.cargar()
        self.pedidos.confirmar("A")
        self.asignar_para_despacho()
        # Falla de almacenamiento real en el segundo movimiento del despacho.
        self.inv.conexion.executescript("""
            CREATE TRIGGER simular_fallo BEFORE UPDATE ON existencias
            WHEN OLD.id_deposito = 'D2'
            BEGIN SELECT RAISE(ABORT, 'fallo de almacenamiento'); END;
        """)
        with self.assertRaises(sqlite3.IntegrityError):
            self.pedidos.despachar("A")
        self.assertEqual(self.inv.stock("D1", "P1"), 50)
        self.assertEqual(self.inv.stock("D2", "P1"), 40)
        self.assertEqual(self.pedidos.obtener_pedido("A").estado, "Confirmado")
        self.assertEqual(self.inv.stock_reservado("D1", "P1"), 50)

    def test_estados_y_datos_invalidos(self):
        for operacion in [self.pedidos.confirmar, self.pedidos.despachar, self.pedidos.entregar]:
            with self.assertRaises(ValueError):
                operacion("A")
        for cantidad in [0, -1, 1.5, True, 2**63]:
            with self.subTest(cantidad=cantidad):
                with self.assertRaises(ValueError):
                    self.pedidos.establecer_producto("A", "D1", "P1", cantidad)
        for deposito, producto in [("X", "P1"), ("D1", "X")]:
            with self.assertRaises(ValueError):
                self.pedidos.establecer_producto("A", deposito, producto, 1)
        for id_, cliente, destino, prioridad in [
            ("", "Cliente", "Destino", 1), ("B", " ", "Destino", 1),
            ("B", "Cliente", "", 1), ("B", "Cliente", "Destino", 4),
            ("B", "Cliente", "Destino", True),
        ]:
            with self.assertRaises(ValueError):
                self.pedidos.crear_borrador(id_, cliente, destino, prioridad)
        with self.assertRaises(sqlite3.IntegrityError):
            self.pedidos.crear_borrador("A", "Otro", "Destino")
        with self.assertRaises(ValueError):
            self.pedidos.obtener_pedido("inexistente")

    def test_dos_conexiones_no_reservan_las_mismas_unidades(self):
        self.pedidos.establecer_producto("A", "D1", "P1", 40)
        self.pedidos.crear_borrador("B", "Otro", "Destino")
        self.pedidos.establecer_producto("B", "D1", "P1", 40)
        barrera = threading.Barrier(2)

        def confirmar(id_pedido):
            with InventarioSQLite(self.ruta) as inv:
                pedidos = PedidosSQLite(inv)
                barrera.wait(timeout=5)
                try:
                    pedidos.confirmar(id_pedido)
                    return "confirmado"
                except StockInsuficiente:
                    return "sin stock"

        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            resultados = list(ejecutor.map(confirmar, ["A", "B"]))
        self.assertCountEqual(resultados, ["confirmado", "sin stock"])
        self.assertEqual(self.inv.stock_reservado("D1", "P1"), 40)
        self.assertEqual(self.inv.stock_disponible("D1", "P1"), 10)

    def test_amplia_base_anterior_sin_perder_existencias(self):
        ruta = Path(self.temporal.name) / "anterior.db"
        esquema = (Path(__file__).resolve().parents[1] / "Backend/schema.sql").read_text(encoding="utf-8")
        # Recrea solo las tablas de la primera etapa, sin tablas de pedidos.
        with closing(sqlite3.connect(ruta)) as conexion, conexion:
            conexion.executescript(esquema.split("-- Pedidos")[0])
            conexion.execute("INSERT INTO productos VALUES ('P', 'Leche', 1, 1)")
            conexion.execute("INSERT INTO depositos VALUES ('D', 'Central', 'Sur', 100)")
            conexion.execute("INSERT INTO existencias VALUES ('D', 'P', 7)")
        with InventarioSQLite(ruta) as inv:
            self.assertEqual(inv.stock("D", "P"), 7)
            self.assertEqual(inv.stock_disponible("D", "P"), 7)
            PedidosSQLite(inv).crear_borrador("N", "Cliente", "Destino")


if __name__ == "__main__":
    unittest.main()
