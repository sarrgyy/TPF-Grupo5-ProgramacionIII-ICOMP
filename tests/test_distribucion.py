"""Prueba la distribución y atomicidad entre stock, pedidos y flota.

Utiliza unittest y recursos aislados de la base de uso habitual.
"""

import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

from Backend.flota import FlotaSQLite
from Backend.main import cargar_ejemplo
from Backend.modelos.conductor import Conductor
from Backend.modelos.vehiculo import Vehiculo
from Backend.pedidos import PedidosSQLite
from Backend.persistencia import InventarioSQLite


class DistribucionTests(unittest.TestCase):
    """Prueba distribución atómica entre stock, pedidos y flota."""

    def setUp(self):
        """Prepara recursos temporales y registra su cierre tras la prueba."""
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "distribucion.db"
        self.inv = InventarioSQLite(self.ruta)
        self.addCleanup(self.inv.close)
        cargar_ejemplo(self.inv)
        self.pedidos = PedidosSQLite(self.inv)
        self.flota = FlotaSQLite(self.inv)
        for patente, dni in [("V1", "C1"), ("V2", "C2")]:
            self.flota.registrar_vehiculo(Vehiculo(patente, 15 if patente == "V1" else 20))
            self.flota.registrar_conductor(Conductor(dni, dni))
            self.flota.asignar_conductor(patente, dni)
        for id_ in ("A", "B"):
            self.pedidos.crear_borrador(id_, "Cliente", "Destino")
            self.pedidos.establecer_producto(id_, "D-001", "PRD-1", 20)
            self.pedidos.establecer_producto(id_, "D-002", "PRD-1", 10)
            self.pedidos.confirmar(id_)

    def test_asignacion_reapertura_y_capacidad_exacta(self):
        """Comprueba el caso: asignacion reapertura y capacidad exacta."""
        self.pedidos.asignar_vehiculo("A", "V1")
        with InventarioSQLite(self.ruta) as inv:
            self.assertEqual(PedidosSQLite(inv).obtener_pedido("A").vehiculo_asignado, "V1")
            vehiculo = FlotaSQLite(inv).obtener_vehiculo("V1")
            self.assertEqual(vehiculo.pedido_asignado, "A")
            self.assertEqual(vehiculo.volumen_ocupado, 0)
        with self.assertRaises(ValueError):
            self.pedidos.asignar_vehiculo("B", "V1")

    def test_no_asigna_sin_conductor_ni_capacidad(self):
        """Comprueba el caso: no asigna sin conductor ni capacidad."""
        self.flota.registrar_vehiculo(Vehiculo("SIN", 100))
        self.flota.registrar_vehiculo(Vehiculo("CHICO", 10))
        self.flota.registrar_conductor(Conductor("C3", "Otro"))
        self.flota.asignar_conductor("CHICO", "C3")
        for patente in ("SIN", "CHICO", "inexistente"):
            with self.assertRaises(ValueError):
                self.pedidos.asignar_vehiculo("A", patente)
        self.flota.liberar_conductor("V1")
        self.flota.actualizar_estado_vehiculo("V1", "Mantenimiento")
        with self.assertRaises(ValueError):
            self.pedidos.asignar_vehiculo("A", "V1")

    def test_no_asigna_borrador_ni_reemplaza_vehiculo(self):
        """Comprueba el caso: no asigna borrador ni reemplaza vehiculo."""
        self.pedidos.crear_borrador("BORRADOR", "Cliente", "Destino")
        with self.assertRaises(ValueError):
            self.pedidos.asignar_vehiculo("BORRADOR", "V1")
        self.pedidos.asignar_vehiculo("A", "V1")
        with self.assertRaises(ValueError):
            self.pedidos.asignar_vehiculo("A", "V2")
        self.pedidos.liberar_vehiculo("A")
        self.pedidos.asignar_vehiculo("A", "V2")
        self.pedidos.asignar_vehiculo("B", "V1")

    def test_flota_no_puede_alterar_pedido_activo(self):
        """Comprueba el caso: flota no puede alterar pedido activo."""
        self.pedidos.asignar_vehiculo("A", "V1")
        for operacion in [
            lambda: self.flota.liberar_conductor("V1"),
            lambda: self.flota.actualizar_estado_vehiculo("V1", "Mantenimiento"),
            lambda: self.flota.actualizar_estado_vehiculo("V1", "En Ruta"),
        ]:
            with self.assertRaises(ValueError):
                operacion()

    def test_cancelacion_libera_vehiculo_y_reservas(self):
        """Comprueba el caso: cancelacion libera vehiculo y reservas."""
        self.pedidos.asignar_vehiculo("A", "V1")
        self.pedidos.cancelar("A")
        self.assertIsNone(self.flota.obtener_vehiculo("V1").pedido_asignado)
        self.assertEqual(self.inv.stock_reservado("D-001", "PRD-1"), 20)
        self.pedidos.asignar_vehiculo("B", "V1")

    def test_despacho_y_entrega_integran_stock_y_flota(self):
        """Comprueba el caso: despacho y entrega integran stock y flota."""
        with self.assertRaises(ValueError):
            self.pedidos.despachar("A")
        self.pedidos.asignar_vehiculo("A", "V1")
        self.pedidos.despachar("A")
        vehiculo = self.flota.obtener_vehiculo("V1")
        self.assertEqual((vehiculo.estado, vehiculo.volumen_ocupado), ("En Ruta", 15))
        self.assertEqual(self.inv.stock("D-001", "PRD-1"), 480)
        self.assertEqual(self.inv.stock("D-002", "PRD-1"), 90)
        for operacion in [
            lambda: self.pedidos.liberar_vehiculo("A"),
            lambda: self.flota.actualizar_estado_vehiculo("V1", "Disponible"),
            lambda: self.pedidos.despachar("A"),
        ]:
            with self.assertRaises(ValueError):
                operacion()
        self.pedidos.entregar("A")
        vehiculo = self.flota.obtener_vehiculo("V1")
        self.assertEqual((vehiculo.estado, vehiculo.volumen_ocupado), ("Disponible", 0))
        self.assertEqual(vehiculo.conductor_asignado, "C1")
        self.assertIsNone(vehiculo.pedido_asignado)
        self.assertEqual(self.pedidos.obtener_pedido("A").vehiculo_asignado, "V1")
        self.pedidos.asignar_vehiculo("B", "V1")

    def test_fallo_de_flota_revierte_despacho_y_entrega(self):
        """Comprueba el caso: fallo de flota revierte despacho y entrega."""
        self.pedidos.asignar_vehiculo("A", "V1")
        self.inv.conexion.executescript("""
            CREATE TRIGGER falla_flota BEFORE UPDATE ON vehiculos
            BEGIN SELECT RAISE(ABORT, 'falla flota'); END;
        """)
        with self.assertRaises(sqlite3.IntegrityError):
            self.pedidos.despachar("A")
        self.assertEqual(self.inv.stock("D-001", "PRD-1"), 500)
        self.assertEqual(self.pedidos.obtener_pedido("A").estado, "Confirmado")
        self.assertEqual(self.flota.obtener_vehiculo("V1").estado, "Disponible")
        self.inv.conexion.execute("DROP TRIGGER falla_flota")
        self.pedidos.despachar("A")
        self.inv.conexion.executescript("""
            CREATE TRIGGER falla_flota BEFORE UPDATE ON vehiculos
            BEGIN SELECT RAISE(ABORT, 'falla flota'); END;
        """)
        with self.assertRaises(sqlite3.IntegrityError):
            self.pedidos.entregar("A")
        self.assertEqual(self.pedidos.obtener_pedido("A").estado, "Despachado")
        self.assertEqual(self.flota.obtener_vehiculo("V1").estado, "En Ruta")

    def test_asignaciones_concurrentes_no_ocupan_mismo_vehiculo(self):
        """Comprueba el caso: asignaciones concurrentes no ocupan mismo vehiculo."""
        barrera = threading.Barrier(2)

        def asignar(id_pedido):
            """Ejecuta una asignación concurrente con conexión independiente.

            Args:
                id_pedido (str): Identificador del pedido.

            Returns:
                str: Resultado usado para contar operaciones aceptadas.
            """
            with InventarioSQLite(self.ruta) as inv:
                pedidos = PedidosSQLite(inv)
                barrera.wait(timeout=5)
                try:
                    pedidos.asignar_vehiculo(id_pedido, "V1")
                    return "asignado"
                except ValueError:
                    return "rechazado"

        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            self.assertCountEqual(list(ejecutor.map(asignar, ["A", "B"])), ["asignado", "rechazado"])

    def test_migracion_conserva_pedidos_anteriores(self):
        """Comprueba el caso: migracion conserva pedidos anteriores."""
        ruta = Path(self.temporal.name) / "anterior.db"
        with closing(sqlite3.connect(ruta)) as conexion, conexion:
            conexion.execute("""CREATE TABLE pedidos (
                id_pedido TEXT PRIMARY KEY, cliente TEXT, destino TEXT, prioridad INTEGER,
                estado TEXT, creado_en TEXT DEFAULT CURRENT_TIMESTAMP)""")
            conexion.execute("INSERT INTO pedidos (id_pedido, cliente, destino, prioridad, estado) VALUES ('ANT', 'Cliente', 'Destino', 1, 'Despachado')")
        for _ in range(2):
            with InventarioSQLite(ruta) as inv:
                self.assertIsNone(PedidosSQLite(inv).obtener_pedido("ANT").vehiculo_asignado)
        with InventarioSQLite(ruta) as inv:
            pedidos = PedidosSQLite(inv)
            pedidos.entregar("ANT")
            self.assertEqual(pedidos.obtener_pedido("ANT").estado, "Entregado")


if __name__ == "__main__":
    unittest.main()
