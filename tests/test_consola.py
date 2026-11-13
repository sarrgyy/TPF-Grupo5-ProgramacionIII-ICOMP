"""Prueba el menú con entrada real, formularios y persistencia.

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


RAIZ = Path(__file__).resolve().parents[1]


class ConsolaTests(unittest.TestCase):
    """Prueba navegación, formularios y persistencia desde la consola."""

    def setUp(self):
        """Prepara recursos temporales y registra su cierre tras la prueba."""
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "menu.db"

    def ejecutar(self, entradas, *opciones):
        """Ejecuta el programa aislado y comprueba que termine sin errores.

        Args:
            entradas (list[str]): Respuestas enviadas a la entrada estándar del
                proceso.
            opciones (str): Opciones adicionales de la línea de comandos.

        Returns:
            str: Salida estándar capturada; la espera máxima es de 15 segundos.
        """
        resultado = subprocess.run(
            [sys.executable, "-B", str(RAIZ / "Backend/main.py"), "--db", str(self.ruta), *opciones],
            input="\n".join(entradas) + ("\n" if entradas else ""),
            cwd=self.temporal.name, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=15,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertNotIn("Traceback", resultado.stdout + resultado.stderr)
        return resultado.stdout

    def test_flujo_completo_por_menu_y_reapertura(self):
        """Comprueba el caso: flujo completo por menu y reapertura."""
        self.ejecutar([
            "1",  # Inventario
            "2", "P3", "Arroz", "0,1", "1",  # Registrar producto
            "3", "D3", "Norte", "Ruta 237", "100",  # Registrar depósito
            "4", "D3", "P3", "50",  # Ingreso
            "5", "D3", "P3", "5",  # Retiro
            "6", "D3", "D-001", "P3", "10",  # Traslado
            "1", "0",
            "3",  # Flota
            "2", "V1", "40",  # Vehículo
            "3", "C1", "Carlos",  # Conductor
            "4", "V1", "C1",  # Asignación
            "1", "0",
            "2",  # Pedidos
            "3", "A", "Cliente", "Mitre 200", "",  # Borrador prioridad default
            "5", "A", "D-001", "PRD-1", "50",
            "5", "A", "D-002", "PRD-1", "30",
            "2", "A",  # Detalle
            "7", "A",  # Confirmar
            "9", "A", "V1",  # Asignar vehículo
            "10", "A",  # Liberar y volver a asignar antes del despacho
            "9", "A", "V1",
            "11", "A",  # Despachar
            "12", "A",  # Entregar
            "1", "0", "0",
        ])
        with InventarioSQLite(self.ruta) as inv:
            self.assertEqual(inv.stock("D3", "P3"), 35)
            self.assertEqual(inv.stock("D-001", "P3"), 10)
            self.assertEqual(inv.stock("D-001", "PRD-1"), 450)
            self.assertEqual(inv.stock("D-002", "PRD-1"), 70)
            self.assertEqual(PedidosSQLite(inv).obtener_pedido("A").estado, "Entregado")
            vehiculo = FlotaSQLite(inv).obtener_vehiculo("V1")
            self.assertEqual((vehiculo.estado, vehiculo.conductor_asignado), ("Disponible", "C1"))
        salida = self.ejecutar([], "--resumen")
        self.assertIn("Entregado", salida)

    def test_errores_y_cancelacion_no_cierran_ni_escriben_carga_incompleta(self):
        """Comprueba el caso: errores y cancelacion no cierran ni escriben carga incompleta."""
        salida = self.ejecutar([
            "invalida", "1",
            "2", "CANCELADO", "/volver",
            "2", "P3", "Arroz", "nan",  # Medida inválida
            "4", "D-001", "PRD-1", "1.5",  # Cantidad inválida
            "5", "D-001", "PRD-1", "999999",  # Stock insuficiente
            "2", "PRD-1", "Duplicado", "1", "1",
            "4", "D-001", "PRD-1", "2",
            "0", "0",
        ])
        self.assertIn("Error", salida)
        with InventarioSQLite(self.ruta) as inv:
            self.assertEqual(inv.stock("D-001", "PRD-1"), 502)
            self.assertEqual(len(inv.listar_productos()), 2)

    def test_borrador_rechazado_puede_corregirse_y_cancelarse(self):
        """Comprueba el caso: borrador rechazado puede corregirse y cancelarse."""
        self.ejecutar([
            "2", "3", "A", "Cliente", "Destino", "2",
            "5", "A", "D-001", "PRD-1", "501",
            "7", "A",  # Falla, conserva borrador
            "4", "A", "Nuevo cliente", "Otro destino", "3",
            "5", "A", "D-001", "PRD-1", "20",
            "5", "A", "D-001", "PRD-2", "5",
            "6", "A", "D-001", "PRD-2",
            "7", "A", "8", "A", "0", "0",
        ])
        with InventarioSQLite(self.ruta) as inv:
            pedido = PedidosSQLite(inv).obtener_pedido("A")
            self.assertEqual((pedido.estado, pedido.cliente, pedido.prioridad), ("Cancelado", "Nuevo cliente", 3))
            self.assertEqual(len(pedido.productos), 1)
            self.assertEqual(inv.stock_reservado("D-001", "PRD-1"), 0)

    def test_eof_durante_carga_cierra_sin_escribir(self):
        """Comprueba el caso: eof durante carga cierra sin escribir."""
        self.ejecutar(["1", "2", "INCOMPLETO"])
        with InventarioSQLite(self.ruta) as inv:
            self.assertEqual(len(inv.listar_productos()), 2)

    def test_liberaciones_y_estados_de_flota_desde_menu(self):
        """Comprueba el caso: liberaciones y estados de flota desde menu."""
        self.ejecutar([
            "3", "2", "V1", "20", "3", "C1", "Ana",
            "4", "V1", "C1", "5", "V1",
            "6", "V1", "3",  # Mantenimiento
            "7", "C1", "2",  # Inactivo
            "0", "0",
        ])
        with InventarioSQLite(self.ruta) as inv:
            flota = FlotaSQLite(inv)
            self.assertEqual(flota.obtener_vehiculo("V1").estado, "Mantenimiento")
            self.assertEqual(flota.obtener_conductor("C1").estado, "Inactivo")


if __name__ == "__main__":
    unittest.main()
