class Producto:
    """Características de un producto; las existencias pertenecen a cada depósito."""

    def __init__(self, id_producto, nombre, volumen_unitario, peso_unitario):
        self.id_producto = id_producto
        self.nombre = nombre
        self.volumen_unitario = volumen_unitario
        self.peso_unitario = peso_unitario
