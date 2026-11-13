"""Menú de texto y consultas del sistema logístico."""

import math
import sqlite3

from .flota import FlotaSQLite
from .pedidos import PedidosSQLite
from .modelos.conductor import Conductor
from .modelos.deposito import Deposito
from .modelos.productos import Producto
from .modelos.vehiculo import Vehiculo


def mostrar_inventario(inventario):
    productos = inventario.listar_productos()
    for deposito in inventario.listar_depositos():
        print(f"\n{deposito.id_deposito} — {deposito.nombre}")
        print(f"Volumen ocupado: {deposito.volumen_ocupado:g} / {deposito.capacidad_maxima:g}")
        for producto in productos:
            cantidad = inventario.stock(deposito.id_deposito, producto.id_producto)
            reservado = inventario.stock_reservado(deposito.id_deposito, producto.id_producto)
            print(f"  {producto.id_producto} — {producto.nombre}: físico: {cantidad}, "
                  f"reservado: {reservado}, disponible: {cantidad - reservado}")
    print("\n--- Totales por producto ---")
    for producto in productos:
        print(f"{producto.id_producto} — {producto.nombre}: "
              f"{inventario.stock_total(producto.id_producto)} unidades, "
              f"volumen unitario: {producto.volumen_unitario:g}, peso unitario: {producto.peso_unitario:g}")


def mostrar_flota(inventario):
    flota = FlotaSQLite(inventario)
    print("\n--- Vehículos guardados ---")
    vehiculos = flota.listar_vehiculos()
    if not vehiculos:
        print("No hay vehículos guardados.")
    for vehiculo in vehiculos:
        conductor = vehiculo.conductor_asignado or "sin asignar"
        print(f"{vehiculo.patente}: {vehiculo.estado}, "
              f"capacidad: {vehiculo.capacidad_maxima:g}, conductor DNI: {conductor}, "
              f"pedido activo: {vehiculo.pedido_asignado or 'ninguno'}, "
              f"carga: {vehiculo.volumen_ocupado:g}")
    print("\n--- Conductores guardados ---")
    conductores = flota.listar_conductores()
    if not conductores:
        print("No hay conductores guardados.")
    for conductor in conductores:
        print(f"{conductor.dni} — {conductor.nombre}: {conductor.estado}, "
              f"vehículo: {conductor.vehiculo_asignado or 'sin asignar'}")


def mostrar_pedidos(inventario):
    print("\n--- Pedidos guardados ---")
    pedidos = PedidosSQLite(inventario).listar_pedidos()
    if not pedidos:
        print("No hay pedidos guardados.")
    for pedido in pedidos:
        print(f"{pedido.id_pedido} — {pedido.cliente}: {pedido.estado}, "
              f"volumen: {pedido.volumen_total:g}, "
              f"vehículo: {pedido.vehiculo_asignado or 'sin asignar'}")


class _CargaCancelada(Exception):
    pass


class MenuConsola:
    def __init__(self, inventario):
        self.inventario = inventario
        self.pedidos = PedidosSQLite(inventario)
        self.flota = FlotaSQLite(inventario)

    @staticmethod
    def _entrada(mensaje):
        valor = input(mensaje + ": ").strip()
        if valor == "/volver":
            raise _CargaCancelada
        return valor

    def _texto(self, mensaje):
        valor = self._entrada(mensaje)
        if not valor:
            raise ValueError("El dato no puede estar vacío.")
        return valor

    def _entero(self, mensaje, maximo=2**63 - 1, defecto=None):
        texto = self._entrada(mensaje)
        if not texto and defecto is not None:
            return defecto
        try:
            valor = int(texto)
        except ValueError:
            raise ValueError("Ingresá una cantidad entera positiva.") from None
        if not 1 <= valor <= maximo:
            raise ValueError(f"Ingresá un entero entre 1 y {maximo}.")
        return valor

    def _medida(self, mensaje):
        try:
            valor = float(self._entrada(mensaje).replace(",", "."))
        except ValueError:
            raise ValueError("Ingresá un número positivo, usando coma o punto decimal.") from None
        if not math.isfinite(valor) or valor <= 0:
            raise ValueError("La medida debe ser positiva y finita.")
        return valor

    def _estado(self, estados):
        opciones = ", ".join(f"{i} {estado}" for i, estado in enumerate(estados, 1))
        return estados[self._entero(f"Estado ({opciones})", maximo=len(estados)) - 1]

    @staticmethod
    def _guardar(funcion, *argumentos):
        funcion(*argumentos)
        print("Operación guardada.")

    def _menu(self, titulo, opciones):
        while True:
            print(f"\n--- {titulo} ---")
            for numero, (nombre, _) in enumerate(opciones, 1):
                print(f"{numero}. {nombre}")
            print("0. " + ("Salir" if titulo == "Menú principal" else "Volver"))
            opcion = input("Elegí una opción: ").strip()
            if opcion == "0":
                return
            if opcion not in {str(i) for i in range(1, len(opciones) + 1)}:
                print("Error: opción inválida.")
                continue
            try:
                opciones[int(opcion) - 1][1]()
            except _CargaCancelada:
                print("Carga cancelada; no se guardó esta operación.")
            except ValueError as error:
                print(f"Error: {error}")
            except sqlite3.IntegrityError:
                print("Error: el identificador ya existe o los datos no son válidos.")
            except sqlite3.Error:
                print("Error: no se pudo acceder a los datos. Intentá nuevamente.")

    def principal(self):
        print("En cualquier carga podés escribir /volver para cancelarla.")
        self._menu("Menú principal", [
            ("Inventario", self.inventario_menu),
            ("Pedidos", self.pedidos_menu),
            ("Flota", self.flota_menu),
        ])

    def inventario_menu(self):
        inv = self.inventario
        self._menu("Inventario", [
            ("Consultar inventario y productos", lambda: mostrar_inventario(inv)),
            ("Registrar producto", lambda: self._guardar(inv.registrar_producto, Producto(
                self._texto("ID del producto"), self._texto("Nombre"),
                self._medida("Volumen unitario"), self._medida("Peso unitario")))),
            ("Registrar depósito", lambda: self._guardar(inv.registrar_deposito, Deposito(
                self._texto("ID del depósito"), self._texto("Nombre"),
                self._texto("Ubicación"), self._medida("Capacidad máxima")))),
            ("Ingresar mercadería", lambda: self._guardar(inv.actualizar_stock,
                self._texto("ID del depósito"), self._texto("ID del producto"), self._entero("Cantidad a ingresar"))),
            ("Retirar mercadería", lambda: self._guardar(inv.actualizar_stock,
                self._texto("ID del depósito"), self._texto("ID del producto"), -self._entero("Cantidad a retirar"))),
            ("Trasladar mercadería", lambda: self._guardar(inv.transferir,
                self._texto("ID del depósito origen"), self._texto("ID del depósito destino"),
                self._texto("ID del producto"), self._entero("Cantidad a trasladar"))),
        ])

    def _cabecera_pedido(self, funcion):
        self._guardar(funcion, self._texto("ID del pedido"), self._texto("Cliente"),
                      self._texto("Destino"), self._entero("Prioridad 1 a 3 [1]", maximo=3, defecto=1))

    def _detalle_pedido(self):
        pedido = self.pedidos.obtener_pedido(self._texto("ID del pedido"))
        print(f"{pedido.id_pedido} — {pedido.cliente}: {pedido.estado}")
        print(f"Destino: {pedido.destino}; prioridad: {pedido.prioridad}; "
              f"vehículo: {pedido.vehiculo_asignado or 'sin asignar'}")
        if not pedido.productos:
            print("Sin productos.")
        for item in pedido.productos:
            print(f"{item['id_deposito']} — {item['id_producto']} ({item['producto']}): "
                  f"{item['cantidad']} unidades")
        print(f"Volumen total: {pedido.volumen_total:g}")

    def pedidos_menu(self):
        p = self.pedidos
        self._menu("Pedidos", [
            ("Listar pedidos", lambda: mostrar_pedidos(self.inventario)),
            ("Consultar detalle", self._detalle_pedido),
            ("Crear borrador", lambda: self._cabecera_pedido(p.crear_borrador)),
            ("Editar datos del borrador", lambda: self._cabecera_pedido(p.editar_borrador)),
            ("Establecer producto y cantidad por depósito", lambda: self._guardar(p.establecer_producto,
                self._texto("ID del pedido"), self._texto("ID del depósito"),
                self._texto("ID del producto"), self._entero("Cantidad total a solicitar de este depósito"))),
            ("Quitar producto de un depósito", lambda: self._guardar(p.quitar_producto,
                self._texto("ID del pedido"), self._texto("ID del depósito"), self._texto("ID del producto"))),
            ("Confirmar y reservar mercadería", lambda: self._guardar(p.confirmar, self._texto("ID del pedido"))),
            ("Cancelar pedido", lambda: self._guardar(p.cancelar, self._texto("ID del pedido"))),
            ("Asignar vehículo", lambda: self._guardar(p.asignar_vehiculo,
                self._texto("ID del pedido"), self._texto("Patente del vehículo"))),
            ("Liberar vehículo del pedido", lambda: self._guardar(p.liberar_vehiculo, self._texto("ID del pedido"))),
            ("Despachar pedido completo", lambda: self._guardar(p.despachar, self._texto("ID del pedido"))),
            ("Marcar pedido entregado", lambda: self._guardar(p.entregar, self._texto("ID del pedido"))),
        ])

    def flota_menu(self):
        f = self.flota
        self._menu("Flota", [
            ("Consultar vehículos y conductores", lambda: mostrar_flota(self.inventario)),
            ("Registrar vehículo", lambda: self._guardar(f.registrar_vehiculo, Vehiculo(
                self._texto("Patente"), self._medida("Capacidad máxima de volumen")))),
            ("Registrar conductor", lambda: self._guardar(f.registrar_conductor, Conductor(
                self._texto("DNI"), self._texto("Nombre")))),
            ("Asignar conductor a vehículo", lambda: self._guardar(f.asignar_conductor,
                self._texto("Patente"), self._texto("DNI del conductor"))),
            ("Liberar conductor del vehículo", lambda: self._guardar(f.liberar_conductor, self._texto("Patente"))),
            ("Cambiar estado del vehículo", lambda: self._guardar(f.actualizar_estado_vehiculo,
                self._texto("Patente"), self._estado(("Disponible", "En Ruta", "Mantenimiento")))),
            ("Cambiar estado del conductor", lambda: self._guardar(f.actualizar_estado_conductor,
                self._texto("DNI"), self._estado(("Disponible", "Inactivo")))),
        ])


def ejecutar_menu(inventario):
    try:
        MenuConsola(inventario).principal()
    except (EOFError, KeyboardInterrupt):
        print("\nSesión finalizada. Se conservan las operaciones ya guardadas.")
