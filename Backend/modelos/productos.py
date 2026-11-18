"""Define el producto y su contador de stock para operaciones en memoria."""

class Producto:
    """Representa una unidad de catálogo y un stock local de simulación.

    El stock persistente pertenece a existencias por depósito y se opera
    mediante InventarioSQLite; modificar este objeto no escribe en la base.

    Attributes:
        id_producto (str): Identificador del catálogo.
        nombre (str): Descripción visible del producto.
        volumen_unitario (float): Volumen de una unidad, en m³.
        peso_unitario (float): Peso de una unidad, en kg.
        stock (int): Cantidad local, independiente de las existencias SQLite.
    """

    def __init__(self, id_producto, nombre, volumen_unitario, peso_unitario, stock_inicial=0):
        """Inicializa los datos del catálogo y valida el stock local.

        Las medidas se validan al registrar el producto en el repositorio
        o al utilizarlas para calcular la carga de un pedido.

        Args:
            id_producto (str): Identificador del producto.
            nombre (str): Nombre del producto.
            volumen_unitario (float): Volumen por unidad en m³.
            peso_unitario (float): Peso por unidad en kg.
            stock_inicial (int): Unidades locales iniciales; por defecto, cero.

        Raises:
            ValueError: El stock inicial no es un entero no negativo.
        """
        if type(stock_inicial) is not int or stock_inicial < 0:
            raise ValueError("El stock inicial debe ser un entero no negativo.")
        self.id_producto = id_producto
        self.nombre = nombre
        self.volumen_unitario = volumen_unitario
        self.peso_unitario = peso_unitario
        self.stock = stock_inicial

    def actualizar_stock(self, cantidad):
        """Aplica un ingreso o retiro al contador local de unidades.

        Args:
            cantidad (int): Variación entera; positiva ingresa y negativa retira.

        Returns:
            bool: True si se actualizó; False si el retiro dejaría stock negativo.

        Raises:
            ValueError: La cantidad no es un entero o es un booleano.
        """
        if type(cantidad) is not int:
            raise ValueError("La cantidad debe ser un número entero.")
        if self.stock + cantidad >= 0:
            self.stock += cantidad
            operacion = "ingresadas" if cantidad > 0 else "retiradas"
            print(f"Stock actualizado: {abs(cantidad)} unidades {operacion} de '{self.nombre}'. Stock actual: {self.stock}")
            return True
        else:
            print(f"Error: No hay suficiente stock de '{self.nombre}' para retirar {abs(cantidad)} unidades. Stock actual: {self.stock}")
            return False
