
class Producto:
    """
    Representa un producto dentro del sistema de gestión logística.
    """
    
    def __init__(self, id_producto, nombre, volumen_unitario, peso_unitario, stock_inicial=0):
        """
        Inicializa un nuevo producto con su identidad y estado inicial.
        
        :param id_producto: Identificador único del producto (Identidad).
        :param nombre: Nombre descriptivo del producto.
        :param volumen_unitario: Volumen que ocupa una unidad (clave para la capacidad del vehículo).
        :param peso_unitario: Peso de una unidad (útil para restricciones de carga).
        :param stock_inicial: Cantidad disponible en el depósito al crear el producto.
        """
        self.id_producto = id_producto
        self.nombre = nombre
        self.volumen_unitario = volumen_unitario
        self.peso_unitario = peso_unitario
        self.stock = stock_inicial

    def actualizar_stock(self, cantidad):
        """
        Modifica el stock disponible del producto.         
        :param cantidad: Valor entero (positivo para ingresos, negativo para salidas).
        :return: Booleano indicando si la operación fue exitosa.
        """
        if self.stock + cantidad >= 0:
            self.stock += cantidad
            operacion = "ingresadas" if cantidad > 0 else "retiradas"
            print(f"Stock actualizado: {abs(cantidad)} unidades {operacion} de '{self.nombre}'. Stock actual: {self.stock}")
            return True
        else:
            print(f"Error: No hay suficiente stock de '{self.nombre}' para retirar {abs(cantidad)} unidades. Stock actual: {self.stock}")
            return False



        