// Mercadito — frontend PWA (HTML/JS simple, sin frameworks ni build step)

// En local, frontend (5500) y backend (8000) corren en puertos distintos.
// En produccion ambos quedan en el mismo dominio (ver mount de
// StaticFiles en app/main.py), asi que se usa el mismo origen (string
// vacio = rutas relativas, sin CORS de por medio).
const ES_LOCAL = location.hostname === "127.0.0.1" || location.hostname === "localhost";
const API_BASE_URL = ES_LOCAL && location.port === "5500" ? "http://127.0.0.1:8000" : "";
const TOKEN_KEY = "mercadito_token";

let productosCache = [];
let listaActualId = null;

// ---------- API ----------

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

async function api(path, { method = "GET", body, form = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;

  let payload = undefined;
  if (body !== undefined) {
    if (form) {
      headers["Content-Type"] = "application/x-www-form-urlencoded";
      payload = new URLSearchParams(body).toString();
    } else {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
  }

  const res = await fetch(API_BASE_URL + path, { method, headers, body: payload });

  if (res.status === 401) {
    cerrarSesion();
    throw new Error("Sesion expirada, vuelve a iniciar sesion");
  }

  if (!res.ok) {
    let detalle = res.statusText;
    try {
      const data = await res.json();
      detalle = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch (_) {
      // sin cuerpo JSON, se queda con el statusText
    }
    throw new Error(detalle);
  }

  if (res.status === 204) return null;
  return res.json();
}

// ---------- Sesion ----------

async function iniciarSesion(email, password) {
  const data = await api("/auth/login", { method: "POST", form: true, body: { username: email, password } });
  localStorage.setItem(TOKEN_KEY, data.access_token);
  await cargarUsuarioActual();
  mostrarApp();
  navegar("dashboard");
}

async function cargarUsuarioActual() {
  const usuario = await api("/auth/me");
  document.getElementById("usuario-actual").textContent = usuario.nombre;
}

function cerrarSesion() {
  localStorage.removeItem(TOKEN_KEY);
  document.getElementById("app-header").hidden = true;
  ocultarTodasLasVistas();
  document.getElementById("vista-login").hidden = false;
}

function mostrarApp() {
  document.getElementById("app-header").hidden = false;
}

// ---------- Navegacion ----------

function ocultarTodasLasVistas() {
  document.querySelectorAll("#app-main > section").forEach((s) => (s.hidden = true));
}

async function navegar(ruta) {
  ocultarTodasLasVistas();
  document.getElementById("vista-" + ruta).hidden = false;

  if (ruta === "dashboard") await cargarDashboard();
  if (ruta === "productos") await cargarProductos();
  if (ruta === "compras") await cargarVistaCompras();
  if (ruta === "listas") await cargarListas();
  if (ruta === "pendientes") await cargarPendientes();
  if (ruta === "precios") await cargarPrecios();
  if (ruta === "prediccion") await cargarPrediccion();
}

// ---------- Dashboard ----------

async function cargarDashboard() {
  const resumen = await api("/purchases/resumen");
  const diferencia = resumen.total_mes - resumen.total_mes_anterior;
  const signo = diferencia >= 0 ? "+" : "";

  document.getElementById("resumen-tarjetas").innerHTML = `
    <div class="tarjeta">
      <span class="tarjeta-label">Gasto de este mes</span>
      <span class="tarjeta-valor">$${resumen.total_mes.toLocaleString()}</span>
    </div>
    <div class="tarjeta">
      <span class="tarjeta-label">Mes anterior</span>
      <span class="tarjeta-valor">$${resumen.total_mes_anterior.toLocaleString()}</span>
      <span class="tarjeta-detalle">${signo}$${diferencia.toLocaleString()} vs. este mes</span>
    </div>
  `;

  document.querySelector("#tabla-categoria tbody").innerHTML = resumen.por_categoria
    .map((c) => `<tr><td>${c.nombre}</td><td>$${c.total.toLocaleString()}</td></tr>`)
    .join("");

  document.querySelector("#tabla-tienda tbody").innerHTML = resumen.por_tienda
    .map((t) => `<tr><td>${t.nombre}</td><td>$${t.total.toLocaleString()}</td></tr>`)
    .join("");
}

// ---------- Productos ----------

async function cargarProductos() {
  productosCache = await api("/products/");
  document.querySelector("#tabla-productos tbody").innerHTML = productosCache
    .map((p) => `<tr><td>${p.nombre}</td><td>${p.unidad_default || ""}</td></tr>`)
    .join("");
}

function llenarSelectProductos(select) {
  select.innerHTML =
    '<option value="">-- elegir producto --</option>' +
    productosCache.map((p) => `<option value="${p.id}">${p.nombre}</option>`).join("");
}

// ---------- Compras ----------

async function cargarVistaCompras() {
  if (productosCache.length === 0) productosCache = await api("/products/");
  llenarSelectProductos(document.getElementById("compra-producto"));
  document.getElementById("compra-fecha").value = new Date().toISOString().slice(0, 10);

  const compras = await api("/purchases/");
  document.querySelector("#tabla-compras tbody").innerHTML = compras
    .map((c) => {
      const producto = productosCache.find((p) => p.id === c.product_id);
      return `<tr>
        <td>${c.fecha}</td>
        <td>${producto ? producto.nombre : c.product_id}</td>
        <td>${c.cantidad}</td>
        <td>$${c.precio_total.toLocaleString()}</td>
        <td>${c.tienda || ""}</td>
        <td>${c.origen}</td>
      </tr>`;
    })
    .join("");
}

// ---------- Listas de compra ----------

async function cargarListas() {
  document.getElementById("lista-detalle-panel").hidden = true;
  document.getElementById("listas-panel").hidden = false;
  document.getElementById("lista-fecha").value = new Date().toISOString().slice(0, 10);

  const listas = await api("/shopping-lists/");
  document.querySelector("#tabla-listas tbody").innerHTML = listas
    .map(
      (l) => `<tr>
        <td>${l.fecha_creacion}</td>
        <td>${l.tienda || "-"}</td>
        <td>${l.presupuesto ? "$" + l.presupuesto.toLocaleString() : "-"}</td>
        <td>${l.estado}</td>
        <td><button data-abrir-lista="${l.id}">Abrir</button></td>
      </tr>`
    )
    .join("");
}

async function abrirListaDetalle(listaId) {
  if (productosCache.length === 0) productosCache = await api("/products/");
  listaActualId = listaId;
  document.getElementById("listas-panel").hidden = true;
  document.getElementById("lista-detalle-panel").hidden = false;
  document.getElementById("cerrar-lista-resultado").textContent = "";
  await refrescarListaDetalle();
}

async function refrescarListaDetalle() {
  const lista = await api("/shopping-lists/" + listaActualId);

  document.getElementById("lista-detalle-titulo").textContent =
    "Lista del " + lista.fecha_creacion + (lista.tienda ? " — " + lista.tienda : "");
  document.getElementById("lista-detalle-info").textContent =
    "Estado: " + lista.estado + (lista.presupuesto ? " · Presupuesto de referencia: $" + lista.presupuesto.toLocaleString() : "");

  const formItem = document.getElementById("form-item");
  const botonCerrar = document.getElementById("btn-cerrar-lista");
  const estaAbierta = lista.estado === "abierta";
  formItem.hidden = !estaAbierta;
  botonCerrar.hidden = !estaAbierta;

  llenarSelectProductos(document.getElementById("item-producto"));

  document.querySelector("#tabla-items tbody").innerHTML = lista.items
    .map((item) => {
      const producto = productosCache.find((p) => p.id === item.product_id);
      const nombreProducto = producto ? producto.nombre : "(sin producto)";

      if (item.confirmado) {
        return `<tr>
          <td>${nombreProducto}</td>
          <td>${item.cantidad_planeada ?? "-"}</td>
          <td>${item.precio_esperado ? "$" + item.precio_esperado.toLocaleString() : "-"}</td>
          <td>Confirmado: ${item.cantidad_confirmada} x $${item.precio_confirmado.toLocaleString()}</td>
        </tr>`;
      }

      if (!estaAbierta) {
        return `<tr>
          <td>${nombreProducto}</td>
          <td>${item.cantidad_planeada ?? "-"}</td>
          <td>${item.precio_esperado ? "$" + item.precio_esperado.toLocaleString() : "-"}</td>
          <td>Sin confirmar</td>
        </tr>`;
      }

      return `<tr>
        <td>${nombreProducto}</td>
        <td>${item.cantidad_planeada ?? "-"}</td>
        <td>${item.precio_esperado ? "$" + item.precio_esperado.toLocaleString() : "-"}</td>
        <td>
          <form class="form-confirmar" data-item-id="${item.id}">
            <input type="number" step="0.01" name="cantidad" placeholder="Cant." value="${item.cantidad_planeada ?? ""}" required>
            <input type="number" step="0.01" name="precio" placeholder="Precio" value="${item.precio_esperado ?? ""}" required>
            <button type="submit">Confirmar</button>
          </form>
        </td>
      </tr>`;
    })
    .join("");
}

// ---------- Pendientes ----------

async function cargarPendientes() {
  if (productosCache.length === 0) productosCache = await api("/products/");
  const pendientes = await api("/shopping-lists/pendientes");
  document.querySelector("#tabla-pendientes tbody").innerHTML = pendientes
    .map((item) => {
      const producto = productosCache.find((p) => p.id === item.product_id);
      return `<tr>
        <td>${producto ? producto.nombre : item.product_id}</td>
        <td>${item.cantidad_planeada ?? "-"}</td>
        <td>${item.precio_esperado ? "$" + item.precio_esperado.toLocaleString() : "-"}</td>
      </tr>`;
    })
    .join("");
}

// ---------- Comparacion de precios ----------

async function cargarPrecios() {
  const comparaciones = await api("/purchases/comparacion-precios");
  document.querySelector("#tabla-precios tbody").innerHTML = comparaciones
    .map((c) => {
      const precios = Object.entries(c.precios_por_tienda)
        .map(([tienda, precio]) => `${tienda}: $${precio.toLocaleString()}`)
        .join(" · ");
      return `<tr>
        <td>${c.producto_nombre || c.product_id}</td>
        <td>${precios}</td>
        <td>${c.diferencia_porcentual}%</td>
      </tr>`;
    })
    .join("");
}

// ---------- Prediccion ----------

async function cargarPrediccion() {
  if (productosCache.length === 0) productosCache = await api("/products/");
  const predicciones = await api("/predictions/reabastecimiento");
  document.querySelector("#tabla-prediccion tbody").innerHTML = predicciones
    .map((p) => {
      const producto = productosCache.find((prod) => prod.id === p.product_id);
      return `<tr>
        <td>${producto ? producto.nombre : p.product_id}</td>
        <td>${p.promedio_dias_entre_compras} dias</td>
        <td>${p.dias_desde_ultima_compra} dias</td>
        <td class="estado-${p.estado}">${p.estado.replace("_", " ")}</td>
      </tr>`;
    })
    .join("");
}

// ---------- Eventos ----------

document.getElementById("form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("login-error");
  errorEl.hidden = true;
  try {
    await iniciarSesion(
      document.getElementById("login-email").value,
      document.getElementById("login-password").value
    );
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
  }
});

document.getElementById("form-registro").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("registro-error");
  errorEl.hidden = true;
  try {
    await api("/auth/register", {
      method: "POST",
      body: {
        nombre: document.getElementById("registro-nombre").value,
        email: document.getElementById("registro-email").value,
        password: document.getElementById("registro-password").value,
      },
    });
    await iniciarSesion(document.getElementById("registro-email").value, document.getElementById("registro-password").value);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
  }
});

document.getElementById("btn-salir").addEventListener("click", cerrarSesion);

document.getElementById("main-nav").addEventListener("click", (e) => {
  const ruta = e.target.dataset.ruta;
  if (ruta) navegar(ruta);
});

document.getElementById("form-producto").addEventListener("submit", async (e) => {
  e.preventDefault();
  await api("/products/", {
    method: "POST",
    body: {
      nombre: document.getElementById("producto-nombre").value,
      unidad_default: document.getElementById("producto-unidad").value || null,
    },
  });
  document.getElementById("form-producto").reset();
  await cargarProductos();
});

document.getElementById("form-compra").addEventListener("submit", async (e) => {
  e.preventDefault();
  await api("/purchases/", {
    method: "POST",
    body: {
      product_id: document.getElementById("compra-producto").value,
      fecha: document.getElementById("compra-fecha").value,
      cantidad: parseFloat(document.getElementById("compra-cantidad").value),
      precio_unitario: parseFloat(document.getElementById("compra-precio-unitario").value) || null,
      precio_total: parseFloat(document.getElementById("compra-precio-total").value),
      tienda: document.getElementById("compra-tienda").value || null,
      origen: "manual",
    },
  });
  document.getElementById("form-compra").reset();
  await cargarVistaCompras();
});

document.getElementById("form-lista").addEventListener("submit", async (e) => {
  e.preventDefault();
  await api("/shopping-lists/", {
    method: "POST",
    body: {
      fecha_creacion: document.getElementById("lista-fecha").value,
      presupuesto: parseFloat(document.getElementById("lista-presupuesto").value) || null,
      tienda: document.getElementById("lista-tienda").value || null,
    },
  });
  document.getElementById("form-lista").reset();
  await cargarListas();
});

document.querySelector("#tabla-listas tbody").addEventListener("click", (e) => {
  const listaId = e.target.dataset.abrirLista;
  if (listaId) abrirListaDetalle(listaId);
});

document.getElementById("btn-volver-listas").addEventListener("click", cargarListas);

document.getElementById("form-item").addEventListener("submit", async (e) => {
  e.preventDefault();
  await api("/shopping-lists/" + listaActualId + "/items", {
    method: "POST",
    body: {
      product_id: document.getElementById("item-producto").value,
      cantidad_planeada: parseFloat(document.getElementById("item-cantidad").value) || null,
    },
  });
  document.getElementById("form-item").reset();
  await refrescarListaDetalle();
});

document.querySelector("#tabla-items tbody").addEventListener("submit", async (e) => {
  if (!e.target.classList.contains("form-confirmar")) return;
  e.preventDefault();
  const itemId = e.target.dataset.itemId;
  const cantidad = parseFloat(e.target.cantidad.value);
  const precio = parseFloat(e.target.precio.value);

  const respuesta = await api("/shopping-lists/" + listaActualId + "/items/" + itemId + "/confirmar", {
    method: "PATCH",
    body: { cantidad_confirmada: cantidad, precio_confirmado: precio },
  });

  if (respuesta.alerta_precio) {
    const a = respuesta.alerta_precio;
    alert(
      `Aviso: en ${a.tienda_referencia} pagaste $${a.precio_referencia.toLocaleString()} por este producto ` +
        `(${a.diferencia_porcentual}% de diferencia). Solo es informativo, no bloquea nada.`
    );
  }

  await refrescarListaDetalle();
});

document.getElementById("btn-cerrar-lista").addEventListener("click", async () => {
  const resultado = await api("/shopping-lists/" + listaActualId + "/cerrar", { method: "POST" });
  document.getElementById("cerrar-lista-resultado").textContent =
    `Lista cerrada. Se crearon ${resultado.compras_creadas} compra(s) en el historial.`;
  await refrescarListaDetalle();
});

// ---------- Arranque ----------

(async function iniciar() {
  if (getToken()) {
    try {
      await cargarUsuarioActual();
      mostrarApp();
      await navegar("dashboard");
      return;
    } catch (_) {
      // token invalido o vencido, cae al login
    }
  }
  cerrarSesion();
})();
