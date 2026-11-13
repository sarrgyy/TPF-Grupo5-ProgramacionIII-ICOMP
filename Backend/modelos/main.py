# main.py

from deposito import deposito
from producto import Producto
from vehiculo import Vehiculo
from conductor import Conductor
from pedido import Pedido

def main():
    print("--- INICIANDO SISTEMA DE GESTIÓN LOGÍSTICA ---")
    
    # 1. Instanciación del Depósito y control de espacio
    print("\n[1] CONFIGURANDO DEPÓSITO Y STOCK INICIAL")
    deposito_central = Deposito(id_deposito="D-001", nombre="Base Bariloche", ubicacion="Ruta 40 Sur", capacidad=1000.0)
    
    # Creamos los productos
    prod_leche = Producto(id_producto="PRD-1", nombre="Cajas de Leche", volumen_unitario=0.5, peso_unitario=1.0, stock_inicial=500)
    prod_harina = Producto(id_producto="PRD-2", nombre="Bolsas de Harina", volumen_unitario=0.2, peso_unitario=0.5, stock_inicial=800)
    
    # 2. Configuración de la Flota (Vehículos y Conductores)
    print("\n[2] PREPARANDO FLOTA DE DISTRIBUCIÓN")
    furgon_1 = Vehiculo(patente="AB123CD", capacidad=20.0)
    camioneta_1 = Vehiculo(patente="EF456GH", capacidad=10.0)
    
    chofer_1 = Conductor(dni="30111222", nombre="Carlos Gómez")
    chofer_2 = Conductor(dni="31333444", nombre="Ana Silva")
    
    # Asignación de choferes a vehículos mediante intercambio de mensajes
    furgon_1.asignar_conductor(chofer_1.nombre)
    chofer_1.asignar_vehiculo(furgon_1.patente)
    
    camioneta_1.asignar_conductor(chofer_2.nombre)
    chofer_2.asignar_vehiculo(camioneta_1.patente)

    # 3. Creación y Recepción de Pedidos
    print("\n[3] INGRESANDO PEDIDOS DEL DÍA")
    pedido_01 = Pedido(id_pedido="P-100", cliente="Supermercado Sur", destino="Av. Pioneros 4500", prioridad=2)
    
    # Agregamos productos al pedido 01
    cant_leche_p1 = 20
    if prod_leche.actualizar_stock(-cant_leche_p1): 
        pedido_01.agregar_producto(prod_leche.nombre, cant_leche_p1, prod_leche.volumen_unitario)
        
    cant_harina_p1 = 30
    if prod_harina.actualizar_stock(-cant_harina_p1):
        pedido_01.agregar_producto(prod_harina.nombre, cant_harina_p1, prod_harina.volumen_unitario)

    pedido_02 = Pedido(id_pedido="P-101", cliente="Despensa Centro", destino="Mitre 200", prioridad=1)
    cant_leche_p2 = 50
    if prod_leche.actualizar_stock(-cant_leche_p2):
        pedido_02.agregar_producto(prod_leche.nombre, cant_leche_p2, prod_leche.volumen_unitario)

    # 4. Lógica Imperativa de Asignación
    print("\n[4] EJECUTANDO ALGORITMO DE ASIGNACIÓN IMPERATIVA")
    pedidos_pendientes = [pedido_01, pedido_02]
    flota_disponible = [furgon_1, camioneta_1]
    
    # Iteración clásica imperativa para coordinar operaciones
    for pedido in pedidos_pendientes:
        asignado = False
        for vehiculo in flota_disponible:
            espacio_libre = vehiculo.capacidad_maxima - vehiculo.volumen_ocupado
            if vehiculo.estado == "Disponible" and espacio_libre >= pedido.volumen_total:
                vehiculo.asignar_pedido(pedido)
                asignado = True
                break 
        
        if not asignado:
            print(f"Alerta: No se encontró vehículo con capacidad suficiente para el pedido {pedido.id_pedido}.")

    # 5. Salida de Datos y Resumen del Estado
    print("\n[5] RESUMEN DE OPERACIONES Y ESTADOS")
    print("\n--- Conductores ---")
    print(chofer_1.obtener_info())
    print(chofer_2.obtener_info())
    
    print("\n--- Inventario Final ---")
    print(f"{prod_leche.nombre}: {prod_leche.stock} unidades")
    print(f"{prod_harina.nombre}: {prod_harina.stock} unidades")

if __name__ == "__main__":
    main()