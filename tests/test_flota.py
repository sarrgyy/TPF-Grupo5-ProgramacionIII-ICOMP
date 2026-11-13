"""Prueba la unicidad y recuperación de las asignaciones de flota.

Utiliza unittest y recursos aislados de la base de uso habitual.
"""

import math
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

from Backend.flota import FlotaSQLite
from Backend.modelos.conductor import Conductor
from Backend.modelos.vehiculo import Vehiculo
from Backend.persistencia import InventarioSQLite


class FlotaTests(unittest.TestCase):
    """Prueba estados y asignaciones únicas de flota con SQLite real."""

    def setUp(self):
        """Prepara recursos temporales y registra su cierre tras la prueba."""
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "flota.db"
        self.inv = InventarioSQLite(self.ruta)
        self.addCleanup(self.inv.close)
        self.flota = FlotaSQLite(self.inv)
        for patente in ("V1", "V2"):
            self.flota.registrar_vehiculo(Vehiculo(patente, 20))
        for dni in ("C1", "C2"):
            self.flota.registrar_conductor(Conductor(dni, "Conductor " + dni))

    def test_asignacion_se_recupera_en_ambos_sentidos(self):
        """Comprueba el caso: asignacion se recupera en ambos sentidos."""
        self.flota.asignar_conductor("V1", "C1")
        self.inv.close()
        with InventarioSQLite(self.ruta) as inv:
            flota = FlotaSQLite(inv)
            vehiculo = flota.obtener_vehiculo("V1")
            conductor = flota.obtener_conductor("C1")
            self.assertEqual(vehiculo.capacidad_maxima, 20)
            self.assertEqual(vehiculo.conductor_asignado, "C1")
            self.assertEqual((conductor.estado, conductor.vehiculo_asignado), ("Asignado", "V1"))
            self.assertEqual(len(flota.listar_vehiculos()), 2)
            self.assertEqual(len(flota.listar_conductores()), 2)

    def test_no_reemplaza_asignaciones_existentes(self):
        """Comprueba el caso: no reemplaza asignaciones existentes."""
        self.flota.asignar_conductor("V1", "C1")
        for patente, dni in [("V1", "C2"), ("V2", "C1"), ("V1", "C1")]:
            with self.assertRaises(ValueError):
                self.flota.asignar_conductor(patente, dni)
        self.assertEqual(self.flota.obtener_vehiculo("V1").conductor_asignado, "C1")
        self.assertIsNone(self.flota.obtener_conductor("C2").vehiculo_asignado)

    def test_liberar_permite_reasignar(self):
        """Comprueba el caso: liberar permite reasignar."""
        self.flota.asignar_conductor("V1", "C1")
        self.flota.liberar_conductor("V1")
        self.assertEqual(self.flota.obtener_conductor("C1").estado, "Disponible")
        self.assertIsNone(self.flota.obtener_vehiculo("V1").conductor_asignado)
        self.flota.asignar_conductor("V2", "C1")
        self.flota.asignar_conductor("V1", "C2")
        self.assertEqual(self.flota.obtener_conductor("C1").vehiculo_asignado, "V2")

    def test_no_asigna_inactivos_ni_mantenimiento(self):
        """Comprueba el caso: no asigna inactivos ni mantenimiento."""
        self.flota.actualizar_estado_conductor("C1", "Inactivo")
        with self.assertRaises(ValueError):
            self.flota.asignar_conductor("V1", "C1")
        self.flota.actualizar_estado_vehiculo("V1", "Mantenimiento")
        with self.assertRaises(ValueError):
            self.flota.asignar_conductor("V1", "C2")
        self.flota.actualizar_estado_conductor("C1", "Disponible")
        self.flota.actualizar_estado_vehiculo("V1", "Disponible")
        self.flota.asignar_conductor("V1", "C1")

    def test_asignacion_debe_liberarse_antes_de_inactivar_o_mantener(self):
        """Comprueba el caso: asignacion debe liberarse antes de inactivar o mantener."""
        self.flota.asignar_conductor("V1", "C1")
        for operacion in [
            lambda: self.flota.actualizar_estado_conductor("C1", "Inactivo"),
            lambda: self.flota.actualizar_estado_conductor("C1", "Disponible"),
            lambda: self.flota.actualizar_estado_vehiculo("V1", "Mantenimiento"),
        ]:
            with self.assertRaises(ValueError):
                operacion()
        self.assertEqual(self.flota.obtener_conductor("C1").estado, "Asignado")

    def test_en_ruta_necesita_conductor_y_no_permite_liberarlo(self):
        """Comprueba el caso: en ruta necesita conductor y no permite liberarlo."""
        with self.assertRaises(ValueError):
            self.flota.actualizar_estado_vehiculo("V1", "En Ruta")
        self.flota.asignar_conductor("V1", "C1")
        self.flota.actualizar_estado_vehiculo("V1", "En Ruta")
        with self.assertRaises(ValueError):
            self.flota.liberar_conductor("V1")
        self.flota.actualizar_estado_vehiculo("V1", "Disponible")
        self.flota.liberar_conductor("V1")

    def test_datos_invalidos_y_duplicados(self):
        """Comprueba el caso: datos invalidos y duplicados."""
        for capacidad in (0, -1, math.nan, math.inf, True):
            with self.assertRaises(ValueError):
                self.flota.registrar_vehiculo(Vehiculo("V3", capacidad))
        for conductor in (Conductor("", "Nombre"), Conductor("C3", " ")):
            with self.assertRaises(ValueError):
                self.flota.registrar_conductor(conductor)
        with self.assertRaises(ValueError):
            self.flota.registrar_vehiculo(Vehiculo(" ", 20))
        with self.assertRaises(sqlite3.IntegrityError):
            self.flota.registrar_vehiculo(Vehiculo("V1", 40))
        with self.assertRaises(sqlite3.IntegrityError):
            self.flota.registrar_conductor(Conductor("C1", "Otro"))
        with self.assertRaises(ValueError):
            self.flota.actualizar_estado_conductor("C1", "Asignado")
        with self.assertRaises(ValueError):
            self.flota.actualizar_estado_vehiculo("V1", "Inválido")

    def test_referencias_inexistentes_no_modifican_la_asignacion(self):
        """Comprueba el caso: referencias inexistentes no modifican la asignacion."""
        for patente, dni in [("X", "C1"), ("V1", "X")]:
            with self.assertRaises(ValueError):
                self.flota.asignar_conductor(patente, dni)
        with self.assertRaises(ValueError):
            self.flota.liberar_conductor("V1")
        with self.assertRaises(ValueError):
            self.flota.obtener_conductor("X")
        self.assertIsNone(self.flota.obtener_vehiculo("V1").conductor_asignado)

    def test_rechaza_objetos_con_asignaciones_o_carga_en_memoria(self):
        """Comprueba el caso: rechaza objetos con asignaciones o carga en memoria."""
        vehiculo = Vehiculo("V3", 20)
        vehiculo.conductor_asignado = "C1"
        with self.assertRaises(ValueError):
            self.flota.registrar_vehiculo(vehiculo)
        vehiculo.conductor_asignado = None
        vehiculo.volumen_ocupado = 1
        with self.assertRaises(ValueError):
            self.flota.registrar_vehiculo(vehiculo)
        conductor = Conductor("C3", "Nombre")
        conductor.estado = "Asignado"
        with self.assertRaises(ValueError):
            self.flota.registrar_conductor(conductor)

    def test_conexiones_concurrentes_no_duplican_conductor(self):
        """Comprueba el caso: conexiones concurrentes no duplican conductor."""
        barrera = threading.Barrier(2)

        def asignar(patente):
            """Ejecuta una asignación concurrente con conexión independiente.

            Args:
                patente (str): Identificador del vehículo.

            Returns:
                str: Resultado usado para contar operaciones aceptadas.
            """
            with InventarioSQLite(self.ruta) as inv:
                flota = FlotaSQLite(inv)
                barrera.wait(timeout=5)
                try:
                    flota.asignar_conductor(patente, "C1")
                    return "asignado"
                except ValueError:
                    return "rechazado"

        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            resultados = list(ejecutor.map(asignar, ["V1", "V2"]))
        self.assertCountEqual(resultados, ["asignado", "rechazado"])

    def test_amplia_base_anterior_y_preserva_pedidos(self):
        """Comprueba el caso: amplia base anterior y preserva pedidos."""
        ruta = Path(self.temporal.name) / "anterior.db"
        esquema = (Path(__file__).resolve().parents[1] / "Backend/schema.sql").read_text(encoding="utf-8")
        with closing(sqlite3.connect(ruta)) as conexion, conexion:
            anterior = esquema.split("-- Flota")[0].replace(
                "    patente_vehiculo TEXT REFERENCES vehiculos(patente),\n", ""
            )
            conexion.executescript(anterior)
            conexion.execute("INSERT INTO pedidos (id_pedido, cliente, destino, prioridad) VALUES ('A', 'Cliente', 'Destino', 1)")
        with InventarioSQLite(ruta) as inv:
            flota = FlotaSQLite(inv)
            flota.registrar_conductor(Conductor("C", "Nombre"))
            self.assertEqual(inv.conexion.execute("SELECT estado FROM pedidos WHERE id_pedido = 'A'").fetchone()[0], "Borrador")
            self.assertEqual(flota.obtener_conductor("C").estado, "Disponible")


if __name__ == "__main__":
    unittest.main()
