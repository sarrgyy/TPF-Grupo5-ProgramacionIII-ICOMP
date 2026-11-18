"""Representa pedidos y cálculos locales de su volumen total."""
from .validaciones import validar_medida


class Pedido:
    """Agrupa la cabecera de un pedido, sus productos y una entrega opcional.

    Las transiciones persistentes y las reservas se gestionan mediante
    PedidosSQLite. El repositorio agrega creado_en y vehiculo_asignado
    a las copias que devuelve para consulta.

    Attributes:
        ESTADOS (tuple[str, ...]): Estados admitidos por el modelo y SQLite.
        id_pedido (str): Identificador del pedido.
        cliente (str): Cliente destinatario.
        destino (str): Dirección de entrega.
        prioridad (int): Nivel 1 normal, 2 urgente o 3 crítico.
        estado (str): Estado actual; inicialmente Borrador.
        productos (list[dict]): Ítems; las copias SQLite incluyen sus depósitos.
        volumen_total (float): Suma del volumen de los ítems, en m³.
        entrega (Entrega | None): Condiciones y estado de entrega derivados.
        hora_inicio (str | None): Inicio de la ventana, en HH:MM.
        hora_fin (str | None): Fin de la ventana, en HH:MM.
        observaciones (str | None): Notas de la cabecera del pedido.
    """

    ESTADOS = ("Borrador", "Confirmado", "Despachado", "Entregado", "Cancelado")

    def __init__(self, id_pedido, cliente, destino, prioridad = 1):
        """Crea un borrador sin productos y valida su prioridad.

        Args:
            id_pedido (str): Identificador del pedido.
            cliente (str): Cliente destinatario.
            destino (str): Dirección de entrega.
            prioridad (int): 1 normal, 2 urgente o 3 crítico; por defecto, 1.

        Raises:
            ValueError: La prioridad no es un entero entre 1 y 3.
        """
        if type(prioridad) is not int or prioridad not in (1, 2, 3):
            raise ValueError("La prioridad debe ser 1, 2 o 3.")
        self.id_pedido = id_pedido
        self.cliente = cliente
        self.destino = destino
        self.prioridad = prioridad
        self.estado = "Borrador"
        self.productos = []
        self.volumen_total = 0.0
        self.entrega = None
        self.hora_inicio = None
        self.hora_fin = None
        self.observaciones = None

    def agregar_producto(self, producto, cantidad, volumen_unitario):
        """Agrega un ítem válido al borrador y acumula su volumen local.

        Valida los datos y el nuevo total antes de modificar el pedido.
        Esta operación en memoria no comprueba stock ni genera reservas.

        Args:
            producto (str): Nombre o referencia del producto.
            cantidad (int): Unidades enteras positivas.
            volumen_unitario (float): Volumen positivo y finito por unidad en m³.

        Raises:
            ValueError: El pedido no es Borrador, el ítem es inválido o el total
                excede el rango numérico finito.
        """
        if self.estado != "Borrador":
            raise ValueError("Solo se pueden agregar productos a un pedido Borrador.")
        if type(cantidad) is not int or cantidad <= 0:
            raise ValueError("La cantidad debe ser un entero positivo.")
        validar_medida(volumen_unitario)
        try:
            nuevo_volumen = self.volumen_total + cantidad * volumen_unitario
        except OverflowError:
            raise ValueError("El volumen total está fuera del rango permitido.") from None
        validar_medida(nuevo_volumen)
        item = {
            "producto": producto,
            "cantidad": cantidad
        }
        self.productos.append(item)
        self.volumen_total = nuevo_volumen
        print(f"Producto '{producto}' agregado. Volumen total del pedido {self.id_pedido}: {self.volumen_total}")

    def actualizar_estado(self, nuevo_estado):
        """Asigna un estado válido a este objeto en memoria.

        Las reglas de transición y los efectos sobre stock y flota pertenecen
        a PedidosSQLite; este método solo verifica el nombre del estado.

        Args:
            nuevo_estado (str): Uno de los valores de ESTADOS.

        Raises:
            ValueError: El nombre del estado no está admitido.
        """
        if nuevo_estado in self.ESTADOS:
            self.estado = nuevo_estado
        else:
            raise ValueError(f"'{nuevo_estado}' no es un estado válido.")
