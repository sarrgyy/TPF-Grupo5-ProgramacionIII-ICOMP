//crear pedidos
const pedido1 = {
    id: 201,
    destino: "Bariloche",
    prioridad: 2,
    estado: "Pendiente"
};

const pedido2 = {
    id: 202,
    destino: "Dina Huapi",
    prioridad: 1,
    estado: "Preparando"
};

const pedido3 = {
    id: 203,
    destino: "Bolson",
    prioridad: 3,
    estado: "Pendiente"
};

const pedido4 = {
    id: 204,
    destino: "Bariloche",
    prioridad: 1,
    estado: "Entregado"
}

const pedidos = [
    pedido1,
    pedido2,
    pedido3,
    pedido4
];
//Mostrar Informacion
function mostrarPedidos(pedidos){
    for(const pedido of pedidos){
        console.log(pedido.id);
        console.log(pedido.destino);
    }
}
//Filtrar y mostrar por estado pendiente
function filtarEstado(pedidos, estado){
    const filtrados = [];
    for(const pedido of pedidos){
        if(pedido.estado === estado){
            filtrados.push(pedido);
        }
    }
    return filtrados;
}
function contarPrioridad(pedidos, prioridad){
    let contador = 0;
    for(const pedido of pedidos){
        if(pedido.prioridad === prioridad){
            contador++;
        }
    }
    console.log("Pedidos con prioridad", prioridad, ": ", contador);
}
const prioridad1 = pedidos.filter(
    pedido => pedido.prioridad === 1
);

const destinos = pedidos.map(
    pedido => pedido.destino
);
const destpend = prioridad1.map(
    pedido => pedido.destino 
);

const envios = [
    {
        id: 301,
        destino: "Bariloche",
        pesoKg: 12.5,
        tarifaKg: 800,
        estado: "Pendiente"
    },
    {
        id: 302,
        destino: "Dina Huapi",
        pesoKg: 8,
        tarifaKg: 950,
        estado: "Preparado"
    },
    {
        id: 303,
        destino: "El Bolson",
        pesoKg: 15,
        tarifaKg: 750,
        estado: "Pendiente"
    },
    {
        id: 304,
        destino: "Bariloche",
        pesoKg: 6,
        tarifaKg: 800,
        estado: "Entregado"
    }
];

const costosEnvios = envios.map(
    envio => ({ 
    id: envio.id,
    destino: envio.destino,
    costoEstimado: envio.pesoKg * envio.tarifaKg
}));

const enviosPesados = envios.filter(
    envio => envio.pesoKg >= 10
);

const pesoTotal = envios.reduce(
    (total, envio) => total + envio.pesoKg, 0
);

const ptes = envios.filter(
    envio => envio.estado === "Pendiente"
);

const pesoPendientes = ptes.reduce(
    (total, ptes) => total + ptes.pesoKg, 0
);

const vehiculos = [
    { id: 1, capacidadKg: 25, cargaActual: 0 },
    { id: 2, capacidadKg: 20, cargaActual: 0 },
    { id: 3, capacidadKg: 15, cargaActual: 0 }
];

const envioss = [
    { id: 301, pesoKg: 12.5, estado: "Pendiente" },
    { id: 302, pesoKg: 8, estado: "Preparado" },
    { id: 303, pesoKg: 15, estado: "Pendiente" },
    { id: 304, pesoKg: 6, estado: "Entregado" },
    { id: 305, pesoKg: 9, estado: "Pendiente" },
    { id: 306, pesoKg: 5, estado: "Pendiente" }
];

const pendientes = envioss.filter(
    envio => envio.estado === "Pendiente"
);

for(const pendiente of pendientes){
    for(const vehiculo of vehiculos){
        if(pendiente.pesoKg <= vehiculo.capacidadKg - vehiculo.cargaActual){
            vehiculo.cargaActual = vehiculo.cargaActual + pendiente.pesoKg;
            pendiente.estado = "Preparando";
            pendiente.vehiculoAsignado = vehiculo.id;
            break;
        }
    } 
    if(pendiente.estado === "Pendiente"){
        console.log(`No se pudo asignar el envío ${pendiente.id}`);
    }
}

function mostrarVehiculo(vehiculos){
    for(const vehiculo of vehiculos){
        console.log(`Vehículo: ${vehiculo.id}`);
        console.log(`Carga: ${vehiculo.cargaActual} kg`);
        console.log(`Capacidad máxima: ${vehiculo.capacidadKg} kg`);
        console.log(`Ocupación: ${((vehiculo.cargaActual / vehiculo.capacidadKg) * 100).toFixed(2)}%`);
    }
}
mostrarVehiculo(vehiculos);

const envs = [
    { id: 301, pesoKg: 12.5, prioridad: 2, estado: "Pendiente" },
    { id: 302, pesoKg: 8, prioridad: 1, estado: "Pendiente" },
    { id: 303, pesoKg: 15, prioridad: 1, estado: "Pendiente" },
    { id: 304, pesoKg: 6, prioridad: 3, estado: "Entregado" },
    { id: 305, pesoKg: 9, prioridad: 2, estado: "Pendiente" },
    { id: 306, pesoKg: 5, prioridad: 2, estado: "Pendiente" }
];

const pending = envs.filter(
    envio => envio.estado === "Pendiente"
);

pending.sort((a, b) => {
    if(a.prioridad !== b.prioridad){
        return a.prioridad - b.prioridad;
    }
    return b.pesoKg - a.pesoKg;
});
