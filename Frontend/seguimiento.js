/** @file Consulta pedidos, muestra etapas y permite registrar su entrega. */
"use strict";

/** @param {string} id ID de un elemento. @returns {HTMLElement|null} Elemento encontrado. */
const byId = id => document.getElementById(id);
let pedido = null;

/**
 * Recupera el pedido y presenta su estado, ventana, notas y productos.
 * Oculta el detalle anterior durante la búsqueda y trata Cancelado por separado.
 * @param {string} codigo Identificador del pedido que se consulta.
 * @returns {Promise<void>} Finaliza con la vista y la URL actualizadas.
 */
async function buscarPedido(codigo) {
    byId("seguimiento-detalle").hidden = true;
    pedido = await apiFetch(`/pedidos/${encodeURIComponent(codigo)}`);
    byId("seguimiento-titulo").textContent = `Pedido ${pedido.id_pedido}`;
    byId("seguimiento-estado").textContent = pedido.estado;
    byId("seguimiento-info").textContent = `${pedido.cliente} · ${pedido.destino} · Prioridad ${pedido.prioridad}`;
    byId("seguimiento-ventana").textContent = pedido.hora_inicio ? `Ventana de entrega: ${pedido.hora_inicio} a ${pedido.hora_fin}` : "Sin ventana horaria";
    byId("seguimiento-observaciones").textContent = `Observaciones: ${pedido.observaciones || "Sin observaciones"}`;
    byId("seguimiento-vehiculo").textContent = `Vehículo: ${pedido.vehiculo_asignado || "Sin asignar"}`;
    byId("seguimiento-volumen").textContent = `Volumen total: ${formatVolume(pedido.volumen_total)} m³`;
    const estados = ["Borrador", "Confirmado", "Despachado", "Entregado"];
    const actual = estados.indexOf(pedido.estado);
    byId("timeline").replaceChildren();
    estados.forEach((estado, indice) => {
        const paso = document.createElement("li");
        paso.textContent = estado;
        paso.className = indice < actual ? "completado" : indice === actual ? "actual" : "";
        if (indice === actual) paso.setAttribute("aria-current", "step");
        byId("timeline").appendChild(paso);
    });
    byId("timeline").hidden = pedido.estado === "Cancelado";
    byId("cancelacion-nota").hidden = pedido.estado !== "Cancelado";
    byId("entregar-form").hidden = pedido.estado !== "Despachado";
    byId("abrir-cargas").href = `cargas.html?pedido=${encodeURIComponent(pedido.id_pedido)}`;
    byId("seguimiento-items").replaceChildren();
    pedido.productos.forEach(item => {
        const fila = document.createElement("tr");
        addCells(fila, [item.producto, item.id_deposito, item.cantidad]);
        byId("seguimiento-items").appendChild(fila);
    });
    byId("codigo-pedido").value = pedido.id_pedido;
    byId("seguimiento-detalle").hidden = false;
    history.replaceState(null, "", `?pedido=${encodeURIComponent(pedido.id_pedido)}`);
}
byId("buscar-form").addEventListener("submit", event => {
    event.preventDefault();
    runAction(event.currentTarget, () => buscarPedido(byId("codigo-pedido").value.trim()));
});
byId("entregar-form").addEventListener("submit", event => {
    event.preventDefault();
    runAction(event.currentTarget, async () => {
        const codigo = pedido.id_pedido;
        await apiFetch(`/pedidos/${encodeURIComponent(codigo)}/entregar`, { method: "POST" });
        await buscarPedido(codigo);
        showMessage("Entrega registrada. El vehículo quedó disponible.");
    });
});
const codigo = new URLSearchParams(location.search).get("pedido");
if (codigo) buscarPedido(codigo).catch(error => showMessage(error.message, "error"));
