/** @file Comunicación HTTP y utilidades DOM compartidas por las pantallas. */
"use strict";

/**
 * Consulta la API y convierte fallos HTTP o de conexión en errores legibles.
 * @param {string} path Ruta del mismo servidor, por ejemplo /productos.
 * @param {RequestInit} [options={}] Método, encabezados y cuerpo de fetch.
 * @returns {Promise<Object|Array>} Datos JSON de una respuesta exitosa.
 * @throws {Error} Rechaza la promesa; puede incluir la lista faltantes.
 */
window.apiFetch = async function (path, options = {}) {
    let response;
    try {
        response = await fetch(path, { ...options, headers: { "Content-Type": "application/json", ...options.headers } });
    } catch {
        throw new Error("No se pudo conectar con el servidor. Revisá la conexión y volvé a intentar.");
    }
    let data;
    try { data = await response.json(); }
    catch { throw new Error("El servidor no devolvió una respuesta válida."); }
    if (!response.ok) {
        const detail = data.detail;
        const error = new Error(detail?.mensaje || (typeof detail === "string" ? detail : "No se pudo completar la operación."));
        error.faltantes = detail?.faltantes || [];
        throw error;
    }
    return data;
};

/**
 * Presenta un aviso como texto y actualiza su rol de accesibilidad.
 * @param {string} text Mensaje que se muestra en la página.
 * @param {string} [type="success"] Tipo success, error o warning.
 */
window.showMessage = function (text, type = "success") {
    const box = document.getElementById("mensaje");
    box.textContent = text;
    box.className = `message message--${type}`;
    box.setAttribute("role", type === "error" ? "alert" : "status");
    box.hidden = false;
};

/**
 * Bloquea envíos repetidos del formulario mientras ejecuta una operación.
 * Conserva el estado previo de los botones y muestra cualquier error recibido.
 * @param {HTMLFormElement} form Formulario que origina la operación.
 * @param {function(): Promise<void>} action Operación asíncrona de la pantalla.
 * @returns {Promise<void>} Finaliza tras restaurar los controles.
 */
window.runAction = async function (form, action) {
    if (form.dataset.busy) return;
    form.dataset.busy = "true";
    const buttons = [...form.querySelectorAll("button")];
    const states = buttons.map(button => button.disabled);
    buttons.forEach(button => { button.disabled = true; });
    document.getElementById("mensaje").hidden = true;
    try { await action(); }
    catch (error) { showMessage(error.message, "error"); }
    finally {
        buttons.forEach((button, index) => { button.disabled = states[index]; });
        delete form.dataset.busy;
    }
};

/**
 * Reconstruye opciones seguras y conserva la selección si sigue disponible.
 * @param {HTMLSelectElement} select Selector que se actualiza.
 * @param {Array<[string, string]>} entries Pares de valor y etiqueta visible.
 * @param {string} [placeholder="Seleccioná una opción"] Texto de la opción vacía.
 */
window.fillSelect = function (select, entries, placeholder = "Seleccioná una opción") {
    const previous = select.value;
    select.replaceChildren(new Option(placeholder, ""));
    entries.forEach(([value, label]) => select.add(new Option(label, value)));
    if (entries.some(([value]) => value === previous)) select.value = previous;
};

/**
 * Agrega celdas usando textContent para mostrar los datos como texto.
 * @param {HTMLTableRowElement} row Fila de destino.
 * @param {Array<unknown>} values Valores de celdas; null y undefined usan un guion.
 */
window.addCells = function (row, values) {
    values.forEach(value => {
        const cell = document.createElement("td");
        cell.textContent = value ?? "—";
        row.appendChild(cell);
    });
};
/**
 * Formatea volumen con separadores argentinos y hasta seis decimales.
 * @param {number} value Volumen expresado en m³.
 * @returns {string} Valor listo para mostrar, sin unidad añadida.
 */
window.formatVolume = value => Number(value).toLocaleString("es-AR", { maximumFractionDigits: 6 });
