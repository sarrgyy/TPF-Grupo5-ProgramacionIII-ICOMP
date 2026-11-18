/** @file Muestra indicadores y pedidos reales en la página de Inicio. */
"use strict";

/**
 * Recupera indicadores y pedidos ordenados por la API para renderizar Inicio.
 * @returns {Promise<void>} Finaliza al actualizar las tarjetas y la tabla.
 */
async function cargarInicio() {
    const [kpis, pedidos] = await Promise.all([apiFetch("/reportes/kpis"), apiFetch("/pedidos")]);
    for (const [id, clave] of [["pendientes", "pedidos_pendientes"], ["asignados", "vehiculos_asignados"],
        ["stock", "productos_con_stock"], ["entregados", "pedidos_entregados"]]) {
        document.getElementById(`kpi-${id}`).textContent = kpis[clave];
    }
    const tabla = document.getElementById("pedidos-body");
    tabla.replaceChildren();
    pedidos.forEach(pedido => {
        const fila = document.createElement("tr");
        const codigo = document.createElement("td");
        const link = document.createElement("a");
        link.textContent = pedido.id_pedido;
        link.href = `seguimiento.html?pedido=${encodeURIComponent(pedido.id_pedido)}`;
        codigo.appendChild(link);
        fila.appendChild(codigo);
        addCells(fila, [pedido.cliente, pedido.destino, pedido.prioridad]);
        const estado = document.createElement("td");
        const badge = document.createElement("span");
        badge.textContent = pedido.estado;
        badge.className = `badge estado-${pedido.estado.toLowerCase()}`;
        estado.appendChild(badge);
        fila.appendChild(estado);
        tabla.appendChild(fila);
    });
    document.getElementById("sin-pedidos").hidden = pedidos.length > 0;
}
cargarInicio().catch(error => showMessage(error.message, "error"));
