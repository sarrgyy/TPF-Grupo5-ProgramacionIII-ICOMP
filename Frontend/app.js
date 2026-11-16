const productos = [
    { id: 1, nombre: "Caja estándar", stock: 45 },
    { id: 2, nombre: "Pallet electrónico", stock: 10 },
    { id: 3, nombre: "Caja reforzada", stock: 28 }
];

function mostrarProductos(productos){
    const tabla = document.getElementById("productos-body");
    tabla.innerHTML = "";
    for(const producto of productos){
        const fila = document.createElement("tr");
        let disponibilidad;
        if(producto.stock > 0){
            disponibilidad = "Disponible";
        } else {
            disponibilidad = "Sin Stock";
        }
        fila.innerHTML= `
            <td>${producto.id}</td>
            <td>${producto.nombre}</td>
            <td>${producto.stock}</td>
            <td>${disponibilidad}
        `;
        tabla.appendChild(fila);
    }
}

mostrarProductos(productos);

function buscarProductos(productos, busqueda){
    const filtrado = productos.filter(
        producto => productos.nombre === busqueda
    );
    const contiene = filtrado.includes(
        
    )
}