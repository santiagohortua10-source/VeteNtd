/* Utilidades compartidas por la página principal y el portal de clientes. */

// Crea un elemento. Los textos se insertan con textContent (nunca innerHTML): los nombres los escriben usuarios.
function el(etiqueta, atributos, ...hijos) {
    const nodo = document.createElement(etiqueta);
    for (const [clave, valor] of Object.entries(atributos || {})) {
        if (valor === false || valor === null || valor === undefined) continue;
        if (clave === 'class') nodo.className = valor;
        else if (clave.startsWith('on')) nodo.addEventListener(clave.slice(2), valor);
        else nodo.setAttribute(clave, valor === true ? '' : valor);
    }
    nodo.append(...hijos.filter(h => h !== null && h !== undefined && h !== false));
    return nodo;
}

// Llamada a la API. Siempre devuelve { ok, status, data } (nunca lanza excepción).
async function api(url, metodo = 'GET', cuerpo = null) {
    try {
        const res = await fetch(url, {
            method: metodo,
            headers: cuerpo ? { 'Content-Type': 'application/json' } : {},
            body: cuerpo ? JSON.stringify(cuerpo) : undefined
        });
        // Sesión vencida en el panel de administración: vuelve al ingreso
        if (res.status === 401 && location.pathname === '/equipo') { location.href = '/cliente'; }
        const data = await res.json();
        return { ok: res.ok && data.estado === 'exito', status: res.status, data };
    } catch (err) {
        return { ok: false, status: 0, data: { estado: 'error', mensaje: 'No se pudo conectar con el servidor.' } };
    }
}

// Aviso flotante que desaparece solo.
function aviso(mensaje, tipo = 'exito') {
    let caja = document.getElementById('avisos');
    if (!caja) {
        caja = el('div', { id: 'avisos', class: 'avisos', role: 'status', 'aria-live': 'polite' });
        document.body.appendChild(caja);
    }
    const nodo = el('div', { class: 'aviso ' + (tipo === 'error' ? 'error' : '') }, mensaje);
    caja.appendChild(nodo);
    setTimeout(() => nodo.remove(), tipo === 'error' ? 6000 : 4500);
}

// ---------- Campana de notificaciones ----------
// `base` es la ruta de la API: '/api/notificaciones' (equipo) o '/api/cliente/notificaciones' (cliente).
const ICONOS_NOTIF = {
    cita_agendada: '📅', cita_cancelada: '🚫', reserva_creada: '🛒', stock_bajo: '⚠️',
    sin_cupos: '⛔', servicio_actualizado: '✏️', servicio_eliminado: '🗑️', compra_realizada: '🛍️'
};

function iniciarNotificaciones(base) {
    const panel = document.getElementById('panel');
    const badge = document.getElementById('badge');
    const lista = document.getElementById('lista-notif');

    function pintarBadge(n) {
        badge.textContent = n > 99 ? '99+' : n;
        badge.classList.toggle('oculto', n === 0);
    }

    function pintar(datos) {
        lista.replaceChildren();
        if (datos.length === 0) {
            lista.appendChild(el('div', { class: 'panel-vacio' }, 'No tienes notificaciones'));
            return;
        }
        datos.forEach(function (n) {
            const d = n.datos || {};
            const cuerpo = el('div', null,
                el('div', { class: 'n-titulo' }, n.titulo),
                el('div', { class: 'n-msg' }, n.mensaje),
                // Si la notificación es de una cita, se destaca el DÍA en que será el servicio
                d.dia_texto ? el('div', { class: 'n-dia' }, `📅 ${d.dia_texto.charAt(0).toUpperCase() + d.dia_texto.slice(1)} · ${d.hora_texto}`) : null,
                el('div', { class: 'n-fecha' }, 'Recibida el ' + new Date(n.fecha).toLocaleString('es-CO',
                    { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }))
            );
            const fila = el('div', { class: 'notif ' + n.prioridad + (n.leida ? '' : ' no-leida') },
                el('div', { class: 'n-icono' }, ICONOS_NOTIF[n.tipo] || '🔔'), cuerpo);
            fila.addEventListener('click', async function () {
                if (n.leida) return;
                await api(`${base}/${n.id}/leer`, 'PATCH');
                refrescar();
            });
            lista.appendChild(fila);
        });
    }

    async function refrescar() {
        const r = await api(`${base}?limite=20`);
        if (r.ok) { pintarBadge(r.data.no_leidas); pintar(r.data.datos); }
    }

    document.getElementById('btn-campana').addEventListener('click', function () {
        panel.classList.toggle('activo');
        if (panel.classList.contains('activo')) refrescar();
    });
    document.addEventListener('click', function (e) {          // clic fuera = cerrar
        if (!e.target.closest('.campana-wrap')) panel.classList.remove('activo');
    });
    document.getElementById('btn-leer-todas').addEventListener('click', async function () {
        await api(`${base}/leer-todas`, 'PATCH');
        refrescar();
    });

    setInterval(function () { if (!document.hidden) refrescar(); }, 10000);
    refrescar();
    return refrescar;      // para llamarla justo después de agendar, reservar, etc.
}