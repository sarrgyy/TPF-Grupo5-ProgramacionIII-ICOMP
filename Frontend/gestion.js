/** @file Gestiona catálogo, filtros e ingresos de stock con reintentos seguros. */
"use strict";

let productos = [];
let depositos = [];
let existencias = [];
/** @param {string} id ID de un elemento. @returns {HTMLElement|null} Elemento encontrado. */
const byId = id => document.getElementById(id);

/** Muestra la capacidad física de todos los depósitos, sin filtros de productos. */
function mostrarEspacioDepositos() {
    const tabla = byId("depositos-body");
    tabla.replaceChildren();
    for (const deposito of depositos) {
        const fila = document.createElement("tr");
        addCells(fila, [deposito.nombre, formatVolume(deposito.capacidad_maxima),
            formatVolume(deposito.volumen_ocupado), formatVolume(deposito.espacio_disponible)]);
        tabla.appendChild(fila);
    }
    byId("sin-depositos").hidden = depositos.length > 0;
}

/** Muestra productos y stock del depósito según los filtros locales activos. */
function mostrarInventario() {
    const busqueda = byId("buscar-producto").value.trim().toLocaleLowerCase("es");
    const deposito = byId("filtrar-deposito").value;
    const filtrados = productos.filter(p => `${p.id_producto} ${p.nombre}`.toLocaleLowerCase("es").includes(busqueda));
    const tabla = byId("productos-body");
    tabla.replaceChildren();
    for (const p of filtrados) {
        for (const d of depositos.filter(d => !deposito || d.id_deposito === deposito)) {
            const stock = existencias.find(e => e.id_producto === p.id_producto && e.id_deposito === d.id_deposito);
            const fila = document.createElement("tr");
            addCells(fila, [p.id_producto, p.nombre, d.nombre, stock?.fisico ?? 0, stock?.reservado ?? 0,
                stock?.disponible ?? 0, formatVolume(p.volumen_unitario), p.peso_unitario]);
            tabla.appendChild(fila);
        }
    }
    byId("sin-productos").hidden = tabla.children.length > 0;
}

/**
 * Recupera catálogo, depósitos y stock; actualiza opciones, espacio y existencias.
 * @returns {Promise<void>} Finaliza cuando los datos se muestran.
 */
async function cargarInventario() {
    [productos, depositos, existencias] = await Promise.all([apiFetch("/productos"), apiFetch("/depositos"), apiFetch("/stock")]);
    fillSelect(byId("producto-ingreso"), productos.map(p => [p.id_producto, `${p.id_producto} · ${p.nombre}`]));
    const opciones = depositos.map(d => [d.id_deposito, d.nombre]);
    fillSelect(byId("deposito-ingreso"), opciones);
    fillSelect(byId("filtrar-deposito"), opciones, "Todos los depósitos");
    mostrarEspacioDepositos();
    mostrarInventario();
}
byId("buscar-producto").addEventListener("input", mostrarInventario);
byId("filtrar-deposito").addEventListener("change", mostrarInventario);
byId("alta-form").addEventListener("submit", event => {
    event.preventDefault();
    runAction(event.currentTarget, async () => {
        await apiFetch("/productos", { method: "POST", body: JSON.stringify({
            id_producto: byId("id-producto").value.trim(), nombre: byId("nombre-prod").value.trim(),
            volumen_unitario: Number(byId("volumen-prod").value), peso_unitario: Number(byId("peso-prod").value)
        }) });
        await cargarInventario();
        byId("alta-form").reset();
        showMessage("Producto registrado. Ahora podés ingresar mercadería.");
    });
});
byId("ingreso-form").addEventListener("submit", event => {
    event.preventDefault();
    runAction(event.currentTarget, async () => {
        const body = JSON.stringify({
            id_producto: byId("producto-ingreso").value, id_deposito: byId("deposito-ingreso").value,
            cantidad: Number(byId("cantidad-ingreso").value)
        });
        let pendiente = JSON.parse(sessionStorage.getItem("ingreso-pendiente") || "null");
        if (!pendiente || pendiente.body !== body) pendiente = { body, clave: crypto.randomUUID() };
        sessionStorage.setItem("ingreso-pendiente", JSON.stringify(pendiente));
        await apiFetch("/stock/ingresos", { method: "POST", body, headers: { "Idempotency-Key": pendiente.clave } });
        sessionStorage.removeItem("ingreso-pendiente");
        byId("cantidad-ingreso").value = "";
        try {
            await cargarInventario();
            showMessage("Ingreso registrado. Las existencias fueron actualizadas.");
        } catch {
            showMessage("Ingreso registrado. No se pudo actualizar la tabla; recargá para consultar las existencias.", "warning");
        }
    });
});
cargarInventario().catch(error => showMessage(error.message, "error"));
