"""Define las características de los productos, sin existencias globales."""


class Producto:
    """Representa las características del producto, sin stock global.

    InventarioSQLite guarda existencias por depósito y valida las medidas.

    Attributes:
        id_producto (str): Identificador del catálogo.
        nombre (str): Nombre descriptivo.
        volumen_unitario (float): Volumen de una unidad.
        peso_unitario (float): Peso registrado; aún no limita la carga.
    """

    def __init__(self, id_producto, nombre, volumen_unitario, peso_unitario):
        """Construye las características del producto sin guardar existencias.

        Args:
            id_producto (str): Identificador del producto.
            nombre (str): Nombre descriptivo.
            volumen_unitario (float): Volumen de una unidad en la unidad común
                del inventario.
            peso_unitario (float): Peso de una unidad; todavía no restringe la
                carga.
        """
        self.id_producto = id_producto
        self.nombre = nombre
        self.volumen_unitario = volumen_unitario
        self.peso_unitario = peso_unitario
