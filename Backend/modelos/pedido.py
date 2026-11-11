#La clase pedido para una empresa con la informacion necesaria.
class Pedido:
    def __init__(self, id_pedido, cliente, destino, prioridad = 1):
        """
        Inicializa un nuevo pedido.
        :param prioridad: 1 (Normal), 2 (Urgente), 3 (Crítica)
        """
        self.id_pedido = id_pedido
        self.cliente = cliente
        self.destino = destino
        self.prioridad = prioridad
        self.estado = "Pendiente"  # Estados: Pendiente, Asignado, En Camino, Entregado
        self.productos = []        # Lista para almacenar los productos del pedido
        self.volumen_total = 0.0   # Fundamental para el posterior control de capacidad de vehículos

    def agregar_producto(self, producto, cantidad, volumen_unitario):
        """
        Agrega un producto al pedido y actualiza el volumen total.
        """
        item = {
            "producto": producto,
            "cantidad": cantidad
        }
        self.productos.append(item)
        self.volumen_total += (cantidad * volumen_unitario)
        print(f"Producto '{producto}' agregado. Volumen total del pedido {self.id_pedido}: {self.volumen_total}")

    def actualizar_estado(self, nuevo_estado):
        """
        Modifica el estado actual del pedido.
        """
        estados_validos = ["Pendiente", "Asignado", "En Camino", "Entregado"]
        if nuevo_estado in estados_validos:
            self.estado = nuevo_estado
            #print(f"El pedido {self.id_pedido} ahora está: {self.estado}")
        else:
            print(f"Error: '{nuevo_estado}' no es un estado válido.")
