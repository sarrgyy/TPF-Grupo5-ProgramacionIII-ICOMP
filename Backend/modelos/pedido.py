"""Define el pedido de simulación y las copias de consulta persistentes.

Los métodos locales usan Pendiente, Asignado, En Camino y Entregado.
PedidosSQLite reconstruye sus propios estados y transiciones sobre copias
de este modelo. Modificar un objeto no guarda cambios en la base.
"""


class Pedido:
    """Agrupa datos del cliente y productos de un pedido en memoria.

    Attributes:
        id_pedido (str): Identificador del pedido.
        cliente (str): Nombre del cliente.
        destino (str): Dirección de entrega.
        prioridad (int): Nivel 1 normal, 2 urgente o 3 crítico.
        estado (str): Estado local o persistente de la copia consultada.
        productos (list[dict]): Ítems; SQLite también incluye depósito e id.
        volumen_total (float): Volumen acumulado de los productos.
        vehiculo_asignado (str | None): Patente cargada por la consulta persistente.
        creado_en (str): Fecha UTC agregada solo por obtener_pedido.
    """

    def __init__(self, id_pedido, cliente, destino, prioridad = 1):
        """Construye un pedido local Pendiente, sin productos ni vehículo.

        Args:
            id_pedido (str): Identificador del pedido.
            cliente (str): Nombre del cliente.
            destino (str): Dirección de entrega del pedido.
            prioridad (int): Nivel 1 normal, 2 urgente o 3 crítico. Por defecto:
                1.
        """
        self.id_pedido = id_pedido
        self.cliente = cliente
        self.destino = destino
        self.prioridad = prioridad
        self.estado = "Pendiente"
        self.productos = []
        self.volumen_total = 0.0
        self.vehiculo_asignado = None

    def agregar_producto(self, producto, cantidad, volumen_unitario):
        """Agrega un ítem local y suma volumen sin descontar stock persistente.

        Args:
            producto (str): Nombre o referencia local del producto.
            cantidad (int): Unidades; el signo y las restricciones dependen de
                la operación.
            volumen_unitario (float): Volumen de una unidad en la unidad común
                del inventario.
        """
        item = {
            "producto": producto,
            "cantidad": cantidad
        }
        self.productos.append(item)
        self.volumen_total += (cantidad * volumen_unitario)
        print(f"Producto '{producto}' agregado. Volumen total del pedido {self.id_pedido}: {self.volumen_total}")

    def actualizar_estado(self, nuevo_estado):
        """Cambia un estado de simulación admitido o imprime un error.

        Los estados persistentes Borrador, Confirmado, Despachado y Cancelado se
        gestionan mediante PedidosSQLite.

        Args:
            nuevo_estado (str): Estado solicitado para el objeto en memoria.
        """
        estados_validos = ["Pendiente", "Asignado", "En Camino", "Entregado"]
        if nuevo_estado in estados_validos:
            self.estado = nuevo_estado
        else:
            print(f"Error: '{nuevo_estado}' no es un estado válido.")
