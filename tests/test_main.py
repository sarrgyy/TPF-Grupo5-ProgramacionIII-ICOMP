"""Prueba el arranque, resúmenes y simulación del punto de entrada.

Utiliza unittest y recursos aislados de la base de uso habitual.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from Backend.persistencia import InventarioSQLite
from Backend.pedidos import PedidosSQLite
from Backend.flota import FlotaSQLite
from Backend.modelos.conductor import Conductor
from Backend.modelos.vehiculo import Vehiculo


RAIZ = Path(__file__).resolve().parents[1]


class MainTests(unittest.TestCase):
    """Prueba arranque, consultas y simulación desde procesos aislados."""

    def setUp(self):
        """Prepara recursos temporales y registra su cierre tras la prueba."""
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "inventario.db"

    def ejecutar(self, *opciones, script=None):
        """Ejecuta el programa aislado y comprueba que termine sin errores.

        Args:
            script (pathlib.Path o None): Acceso alternativo; None usa
                Backend/main.py. Por defecto: None.
            opciones (str): Opciones adicionales de la línea de comandos.

        Returns:
            str: Salida estándar capturada; la espera máxima es de 15 segundos.
        """
        if "--simular-pedidos" not in opciones:
            opciones = (*opciones, "--resumen")
        resultado = subprocess.run(
            [sys.executable, "-B", str(script or RAIZ / "Backend/main.py"),
             "--db", str(self.ruta), *opciones],
            cwd=self.temporal.name, capture_output=True, text=True,
            encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=15,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        return resultado.stdout

    def test_dos_arranques_conservan_stock_modificado(self):
        """Comprueba el caso: dos arranques conservan stock modificado."""
        self.ejecutar()
        with InventarioSQLite(self.ruta) as inv:
            self.assertEqual(len(inv.listar_depositos()), 2)
            self.assertEqual(inv.stock("D-001", "PRD-1"), 500)
            inv.actualizar_stock("D-001", "PRD-1", -7)
        salida = self.ejecutar()
        self.assertIn("493", salida)
        with InventarioSQLite(self.ruta) as inv:
            self.assertEqual(inv.stock("D-001", "PRD-1"), 493)
            self.assertEqual(inv.stock("D-002", "PRD-1"), 100)

    def test_simulacion_no_descuenta_stock_persistido(self):
        """Comprueba el caso: simulacion no descuenta stock persistido."""
        salida = self.ejecutar("--simular-pedidos")
        self.assertIn("P-100", salida)
        self.assertIn("P-101", salida)
        with InventarioSQLite(self.ruta) as inv:
            self.assertEqual(inv.stock("D-001", "PRD-1"), 500)
            self.assertEqual(inv.stock("D-001", "PRD-2"), 800)

    def test_acceso_anterior_delega_al_main_actual(self):
        """Comprueba el caso: acceso anterior delega al main actual."""
        self.ejecutar(script=RAIZ / "Backend/modelos/main.py")
        with InventarioSQLite(self.ruta) as inv:
            self.assertEqual(inv.stock_total("PRD-1"), 600)

    def test_muestra_stock_reservado_y_pedido_guardado(self):
        """Comprueba el caso: muestra stock reservado y pedido guardado."""
        self.ejecutar()
        with InventarioSQLite(self.ruta) as inv:
            pedidos = PedidosSQLite(inv)
            pedidos.crear_borrador("MANUAL-1", "Cliente", "Destino")
            pedidos.establecer_producto("MANUAL-1", "D-001", "PRD-1", 20)
            pedidos.confirmar("MANUAL-1")
            flota = FlotaSQLite(inv)
            flota.registrar_vehiculo(Vehiculo("ENVIO-1", 20))
            flota.registrar_conductor(Conductor("ENVIO-C", "Conductor"))
            flota.asignar_conductor("ENVIO-1", "ENVIO-C")
            pedidos.asignar_vehiculo("MANUAL-1", "ENVIO-1")
        salida = self.ejecutar()
        self.assertIn("reservado: 20", salida)
        self.assertIn("disponible: 480", salida)
        self.assertIn("MANUAL-1", salida)
        self.assertIn("Confirmado", salida)
        self.assertIn("vehículo: ENVIO-1", salida)
        self.assertIn("pedido activo: MANUAL-1", salida)

    def test_muestra_asignacion_guardada_sin_reemplazarla(self):
        """Comprueba el caso: muestra asignacion guardada sin reemplazarla."""
        self.ejecutar()
        with InventarioSQLite(self.ruta) as inv:
            flota = FlotaSQLite(inv)
            self.assertEqual(flota.listar_vehiculos(), [])
            flota.registrar_vehiculo(Vehiculo("MANUAL-V", 25))
            flota.registrar_conductor(Conductor("123", "Conductor manual"))
            flota.asignar_conductor("MANUAL-V", "123")
        salida = self.ejecutar()
        self.assertIn("MANUAL-V", salida)
        self.assertIn("Conductor manual", salida)
        self.assertIn("Asignado", salida)
        with InventarioSQLite(self.ruta) as inv:
            self.assertEqual(FlotaSQLite(inv).obtener_conductor("123").vehiculo_asignado, "MANUAL-V")


if __name__ == "__main__":
    unittest.main()
