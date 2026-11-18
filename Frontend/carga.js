/** @file Coordina borradores, ítems, confirmación, vehículo y despacho de pedidos. */
"use strict";

/** @param {string} id ID de un elemento. @returns {HTMLElement|null} Elemento encontrado. */
const byId = id => document.getElementById(id);
let pedido = null;
let vehiculos = [];

/**
 * Marca el paso actual y los pasos completados del recorrido integrado.
 * @param {number} actual Índice del paso: datos (0), productos (1) o confirmación (2).
 */
function mostrarPaso(actual) {
    document.querySelectorAll("#pasos-pedido li").forEach((paso, indice) => {
        if (indice === actual) paso.setAttribute("aria-current", "step");
        else paso.removeAttribute("aria-current");
        paso.classList.toggle("completado", indice < actual);
    });
}

/** Renderiza el pedido actual y habilita las acciones correspondientes a su estado. */
function mostrarPedido() {
    byId("crear-seccion").hidden = true;
    byId("pedido-detalle").hidden = false;
    byId("pedido-titulo").textContent = `Pedido ${pedido.id_pedido}`;
    byId("pedido-estado").textContent = pedido.estado;
    byId("pedido-info").textContent = `${pedido.cliente} · ${pedido.destino} · Prioridad ${pedido.prioridad}`;
    byId("vehiculo-actual").textContent = pedido.vehiculo_asignado || "Sin asignar";
    byId("volumen-total").textContent = formatVolume(pedido.volumen_total);
    byId("ver-seguimiento").href = `seguimiento.html?pedido=${encodeURIComponent(pedido.id_pedido)}`;
    byId("recuperar-id").value = pedido.id_pedido;
    byId("retomar-seccion").open = false;
    mostrarPaso(pedido.estado === "Borrador" ? 1 : 2);
    byId("item-campos").disabled = pedido.estado !== "Borrador";
    byId("confirmar-form").hidden = pedido.estado !== "Borrador";
    const sinProductos = pedido.productos.length === 0;
    const confirmar = byId("confirmar-form").querySelector("button");
    confirmar.disabled = sinProductos;
    if (sinProductos) confirmar.setAttribute("aria-describedby", "ayuda-confirmar");
    else confirmar.removeAttribute("aria-describedby");
    byId("ayuda-confirmar").hidden = !sinProductos;
    byId("sin-items").hidden = !sinProductos;
    byId("vehiculo-form").hidden = pedido.estado !== "Confirmado" || !!pedido.vehiculo_asignado;
    byId("despachar-form").hidden = pedido.estado !== "Confirmado" || !pedido.vehiculo_asignado;
    byId("cancelar-form").hidden = !["Borrador", "Confirmado"].includes(pedido.estado);
    const disponibles = vehiculos.filter(v => v.estado === "Disponible" && v.conductor_asignado && !v.pedido_asignado);
    fillSelect(byId("vehiculo"), disponibles.map(v => [v.patente,
        `${v.patente} · ${formatVolume(v.capacidad_maxima)} m³ · Conductor DNI ${v.conductor_asignado}`]),
    disponibles.length ? "Seleccioná un vehículo" : "No hay vehículos disponibles con conductor");
    byId("items-body").replaceChildren();
    pedido.productos.forEach(item => {
        const fila = document.createElement("tr");
        addCells(fila, [item.producto, item.id_deposito, item.cantidad, formatVolume(item.cantidad * item.volumen_unitario)]);
        byId("items-body").appendChild(fila);
    });
    history.replaceState(null, "", `?pedido=${encodeURIComponent(pedido.id_pedido)}`);
}

/**
 * Oculta el detalle anterior y recupera pedido y vehículos antes de mostrarlos.
 * @param {string} identificador Código del pedido persistido.
 * @returns {Promise<void>} Finaliza al actualizar el detalle y la URL recuperable.
 */
async function cargarPedido(identificador) {
    pedido = null;
    byId("pedido-detalle").hidden = true;
    try {
        [pedido, vehiculos] = await Promise.all([apiFetch(`/pedidos/${encodeURIComponent(identificador)}`), apiFetch("/vehiculos")]);
        mostrarPedido();
    } catch (error) {
        byId("crear-seccion").hidden = false;
        mostrarPaso(0);
        history.replaceState(null, "", location.pathname);
        throw error;
    }
}

/**
 * Muestra el pedido devuelto por la operación y actualiza la flota disponible.
 * Un fallo posterior de flota conserva el pedido guardado y su URL recuperable.
 * @param {string} sufijo Operación relativa a /pedidos/{id}/.
 * @param {string} method Método HTTP, normalmente POST o PUT.
 * @param {Object|null} body Datos JSON; null para transiciones sin cuerpo.
 * @param {string} mensaje Aviso mostrado después de guardar el pedido.
 * @returns {Promise<void>} Finaliza con el pedido actualizado y un aviso de resultado.
 * @throws {Error} Rechaza si falla la operación persistente.
 */
async function modificar(sufijo, method, body, mensaje) {
    pedido = await apiFetch(`/pedidos/${encodeURIComponent(pedido.id_pedido)}/${sufijo}`, {
        method, ...(body ? { body: JSON.stringify(body) } : {})
    });
    let errorFlota = false;
    try { vehiculos = await apiFetch("/vehiculos"); }
    catch { vehiculos = []; errorFlota = true; }
    mostrarPedido();
    showMessage(errorFlota ? `${mensaje} No se pudo actualizar la flota; recargá para consultar los vehículos.` : mensaje,
        errorFlota ? "warning" : "success");
}
byId("pedido-form").addEventListener("submit", event => {
    event.preventDefault();
    runAction(event.currentTarget, async () => {
        const datos = {
            id_pedido: byId("id-pedido").value.trim(), cliente: byId("cliente").value.trim(),
            destino: byId("destino").value.trim(), prioridad: Number(byId("prioridad").value),
            hora_inicio: byId("hora-inicio").value || null, hora_fin: byId("hora-fin").value || null,
            observaciones: byId("observaciones").value.trim() || null
        };
        pedido = await apiFetch("/pedidos", { method: "POST", body: JSON.stringify(datos) });
        byId("pedido-form").reset();
        mostrarPedido();
        showMessage("Borrador creado. Agregá los productos del pedido.");
        byId("productos-titulo").focus();
    });
});
byId("recuperar-form").addEventListener("submit", event => {
    event.preventDefault();
    runAction(event.currentTarget, async () => {
        await cargarPedido(byId("recuperar-id").value.trim());
        showMessage("Pedido recuperado.");
    });
});
byId("item-form").addEventListener("submit", event => {
    event.preventDefault();
    runAction(event.currentTarget, () => modificar("items", "PUT", {
        id_producto: byId("producto-pedido").value, id_deposito: byId("deposito-pedido").value,
        cantidad: Number(byId("cantidad-pedido").value)
    }, "Cantidad guardada."));
});
byId("vehiculo-form").addEventListener("submit", event => {
    event.preventDefault();
    runAction(event.currentTarget, () => modificar("vehiculo", "PUT", { patente: byId("vehiculo").value }, "Vehículo asignado."));
});
for (const [operacion, mensaje] of [["confirmar", "Pedido confirmado. Stock reservado."],
    ["despachar", "Pedido despachado. Stock descontado."], ["cancelar", "Pedido cancelado. Reservas liberadas."]]) {
    byId(`${operacion}-form`).addEventListener("submit", event => {
        event.preventDefault();
        runAction(event.currentTarget, () => modificar(operacion, "POST", null, mensaje));
    });
}
/**
 * Carga los selectores y recupera el pedido indicado en la URL, si existe.
 * @returns {Promise<void>} Finaliza al preparar la pantalla.
 */
async function iniciar() {
    const codigo = new URLSearchParams(location.search).get("pedido");
    const [productos, depositos] = await Promise.all([apiFetch("/productos"), apiFetch("/depositos")]);
    fillSelect(byId("producto-pedido"), productos.map(p => [p.id_producto, `${p.id_producto} · ${p.nombre}`]));
    fillSelect(byId("deposito-pedido"), depositos.map(d => [d.id_deposito, d.nombre]));
    if (codigo) await cargarPedido(codigo);
}
iniciar().catch(error => showMessage(error.message, "error"));
