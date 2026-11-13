import math
import sqlite3
import tempfile
import unittest
from pathlib import Path

from Backend.modelos.deposito import Deposito
from Backend.modelos.productos import Producto
from Backend.persistencia import InventarioSQLite


class InventarioTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "inventario.db"
        self.inv = InventarioSQLite(self.ruta)
        self.addCleanup(self.inv.close)
        self.inv.registrar_producto(Producto("P1", "Leche", 0.5, 1.0))
        self.inv.registrar_deposito(Deposito("D1", "Central", "Sur", 10.0))
        self.inv.registrar_deposito(Deposito("D2", "Centro", "Norte", 2.0))

    def test_recupera_datos_y_ocupacion_al_reabrir(self):
        self.inv.actualizar_stock("D1", "P1", 8)
        self.inv.close()
        with InventarioSQLite(self.ruta) as recuperado:
            self.assertEqual(recuperado.stock("D1", "P1"), 8)
            self.assertEqual(recuperado.obtener_producto("P1").nombre, "Leche")
            deposito = recuperado.obtener_deposito("D1")
            self.assertEqual(deposito.ubicacion, "Sur")
            self.assertEqual(deposito.espacio_disponible(), 6.0)

    def test_stock_independiente_y_total(self):
        self.inv.actualizar_stock("D1", "P1", 8)
        self.inv.actualizar_stock("D2", "P1", 3)
        self.inv.actualizar_stock("D1", "P1", -2)
        self.assertEqual(self.inv.stock("D1", "P1"), 6)
        self.assertEqual(self.inv.stock("D2", "P1"), 3)
        self.assertEqual(self.inv.stock_total("P1"), 9)
        self.assertEqual(len(self.inv.listar_depositos()), 2)
        self.assertEqual(len(self.inv.listar_productos()), 1)

    def test_total_no_desborda_al_sumar_depositos_validos(self):
        for id_deposito in ("D3", "D4"):
            self.inv.registrar_deposito(Deposito(id_deposito, "Grande", "Sur", 1e20))
            self.inv.actualizar_stock(id_deposito, "P1", 2**62)
        self.assertEqual(self.inv.stock_total("P1"), 9223372036854775808)

    def test_capacidad_suma_todos_los_productos(self):
        self.inv.registrar_producto(Producto("P2", "Harina", 1.0, 0.5))
        self.inv.actualizar_stock("D2", "P1", 2)
        self.inv.actualizar_stock("D2", "P2", 1)
        self.assertEqual(self.inv.obtener_deposito("D2").espacio_disponible(), 0)
        with self.assertRaises(ValueError):
            self.inv.actualizar_stock("D2", "P1", 1)
        self.assertEqual(self.inv.stock("D2", "P1"), 2)

    def test_no_permite_stock_negativo(self):
        self.inv.actualizar_stock("D1", "P1", 2)
        with self.assertRaises(ValueError):
            self.inv.actualizar_stock("D1", "P1", -3)
        self.assertEqual(self.inv.stock("D1", "P1"), 2)
        self.inv.actualizar_stock("D1", "P1", -2)
        self.assertEqual(self.inv.stock("D1", "P1"), 0)

    def test_cero_solo_para_referencias_existentes(self):
        self.assertEqual(self.inv.stock("D1", "P1"), 0)
        for deposito, producto in [("inexistente", "P1"), ("D1", "inexistente")]:
            with self.subTest(deposito=deposito, producto=producto):
                with self.assertRaises(ValueError):
                    self.inv.stock(deposito, producto)
                with self.assertRaises(ValueError):
                    self.inv.actualizar_stock(deposito, producto, 1)
        with self.assertRaises(ValueError):
            self.inv.stock_total("inexistente")

    def test_rechaza_cantidades_fraccionarias_y_no_finitas(self):
        for cantidad in [1.5, True, "2", math.inf, math.nan]:
            with self.subTest(cantidad=cantidad):
                with self.assertRaises(ValueError):
                    self.inv.actualizar_stock("D1", "P1", cantidad)
        self.assertEqual(self.inv.stock("D1", "P1"), 0)

    def test_rechaza_medidas_invalidas(self):
        for medida in [-1, 0, math.inf, math.nan]:
            with self.subTest(medida=medida):
                with self.assertRaises(ValueError):
                    self.inv.registrar_producto(Producto("P2", "Inválido", medida, 1))
                with self.assertRaises(ValueError):
                    self.inv.registrar_producto(Producto("P2", "Inválido", 1, medida))
                with self.assertRaises(ValueError):
                    self.inv.registrar_deposito(Deposito("D3", "Inválido", "Sur", medida))

    def test_duplicados_no_sobrescriben_datos(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.inv.registrar_producto(Producto("P1", "Otro", 1, 2))
        with self.assertRaises(sqlite3.IntegrityError):
            self.inv.registrar_deposito(Deposito("D1", "Otro", "Este", 20))
        self.assertEqual(self.inv.obtener_producto("P1").nombre, "Leche")
        self.assertEqual(self.inv.obtener_deposito("D1").capacidad_maxima, 10)

    def test_traslado_actualiza_ambos_depositos(self):
        self.inv.actualizar_stock("D1", "P1", 8)
        self.inv.transferir("D1", "D2", "P1", 3)
        self.assertEqual(self.inv.stock("D1", "P1"), 5)
        self.assertEqual(self.inv.stock("D2", "P1"), 3)
        self.assertEqual(self.inv.stock_total("P1"), 8)

    def test_traslado_sin_capacidad_revierte_salida(self):
        self.inv.actualizar_stock("D1", "P1", 8)
        with self.assertRaises(ValueError):
            self.inv.transferir("D1", "D2", "P1", 5)
        self.assertEqual(self.inv.stock("D1", "P1"), 8)
        self.assertEqual(self.inv.stock("D2", "P1"), 0)

    def test_traslados_invalidos_no_modifican_stock(self):
        self.inv.actualizar_stock("D1", "P1", 2)
        for origen, destino, cantidad in [
            ("D1", "D1", 1), ("D1", "D2", 0), ("D1", "D2", -1),
            ("D1", "D2", 3), ("D1", "faltante", 1),
        ]:
            with self.subTest(origen=origen, destino=destino, cantidad=cantidad):
                with self.assertRaises(ValueError):
                    self.inv.transferir(origen, destino, "P1", cantidad)
                self.assertEqual(self.inv.stock("D1", "P1"), 2)

    def test_capacidad_decimal_exacta(self):
        self.inv.registrar_producto(Producto("P2", "Pequeño", 0.1, 1))
        self.inv.registrar_deposito(Deposito("D3", "Pequeño", "Este", 0.3))
        self.inv.actualizar_stock("D3", "P2", 3)
        with self.assertRaises(ValueError):
            self.inv.actualizar_stock("D3", "P2", 1)

    def test_carga_inicial_atomica_y_sin_reponer_stock(self):
        otra_ruta = Path(self.temporal.name) / "inicial.db"
        productos = [Producto("P1", "Leche", 0.5, 1)]
        depositos = [Deposito("D1", "Central", "Sur", 2)]
        with InventarioSQLite(otra_ruta) as inv:
            with self.assertRaises(ValueError):
                inv.cargar_iniciales(productos, depositos, [("D1", "P1", 5)])
            self.assertEqual(inv.listar_productos(), [])
            self.assertEqual(inv.listar_depositos(), [])
            self.assertTrue(inv.cargar_iniciales(productos, depositos, [("D1", "P1", 4)]))
            inv.actualizar_stock("D1", "P1", -1)
            self.assertFalse(inv.cargar_iniciales(productos, depositos, [("D1", "P1", 4)]))
            self.assertEqual(inv.stock("D1", "P1"), 3)


if __name__ == "__main__":
    unittest.main()
