/* ==========================================================================
   Orthoimagen Dental · Interfaz
   No contiene reglas de negocio: todas las validaciones y mensajes vienen de
   los módulos de Python (M1 a M8) a través de interfaz/api.py.
   ========================================================================== */
'use strict';

/* --- Puente con Python ------------------------------------------------------ */
let MODO = null; // 'webview' (app de escritorio) o 'http' (servidor de desarrollo)

function esperarPuente() {
  return new Promise((resolver) => {
    if (window.pywebview && window.pywebview.api) return resolver('webview');
    const listo = () => resolver('webview');
    window.addEventListener('pywebviewready', listo, { once: true });
    setTimeout(() => {
      window.removeEventListener('pywebviewready', listo);
      resolver(window.pywebview && window.pywebview.api ? 'webview' : 'http');
    }, 1500);
  });
}

async function api(metodo, ...args) {
  try {
    if (MODO === 'webview') return await window.pywebview.api[metodo](...args);
    const respuesta = await fetch('/api/' + metodo, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(args),
    });
    return await respuesta.json();
  } catch (error) {
    console.error(error);
    return { exito: false, mensaje: 'Error: No se pudo comunicar con el sistema. Cierre y vuelva a abrir la aplicación.' };
  }
}

/* --- Utilidades --------------------------------------------------------------- */
const $ = (selector, raiz = document) => raiz.querySelector(selector);
const $$ = (selector, raiz = document) => [...raiz.querySelectorAll(selector)];
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const aFecha = (iso) => { const [a, m, d] = iso.split('-').map(Number); return new Date(a, m - 1, d); };
const aISO = (f) => `${f.getFullYear()}-${String(f.getMonth() + 1).padStart(2, '0')}-${String(f.getDate()).padStart(2, '0')}`;
const sumarDias = (iso, n) => { const f = aFecha(iso); f.setDate(f.getDate() + n); return aISO(f); };
const fmt = (iso, opciones) => new Intl.DateTimeFormat('es-MX', opciones).format(aFecha(iso));
const mayuscula = (t) => t.charAt(0).toUpperCase() + t.slice(1);
const fechaLarga = (iso) => mayuscula(fmt(iso, { weekday: 'long', day: 'numeric', month: 'long' }));
const fechaCompleta = (iso) => mayuscula(fmt(iso, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }));
const diaCorto = (iso) => fmt(iso, { weekday: 'short' }).replace('.', '');
const mesCorto = (iso) => fmt(iso, { month: 'short' }).replace('.', '');
const dinero = (n) => n == null ? 'A consultar' : new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 }).format(n);
const primerNombre = (s) => String(s || '').replace(/^Dr\(a\)\.\s*/, 'Dr(a). ').split(' ').slice(0, s?.startsWith('Dr') ? 2 : 1).join(' ');
const iniciales = (s) => String(s || '?').split(' ').filter(Boolean).slice(0, 2).map((p) => p[0]).join('').toUpperCase();
const saludo = () => { const h = new Date().getHours(); return h < 12 ? 'Buenos días' : h < 19 ? 'Buenas tardes' : 'Buenas noches'; };
const horaCierre = () => `${String(Number(E.horarios.at(-1).slice(0, 2)) + 1).padStart(2, '0')}:00`;
const activa = (c) => c.estatus === 'Programada' || c.estatus === 'Reprogramada';

/* --- Íconos (trazo 24×24) ----------------------------------------------------- */
const RUTAS = {
  inicio: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5"/>',
  agendar: '<rect x="3" y="4.5" width="18" height="16.5" rx="3"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4M12 13v5M9.5 15.5h5"/>',
  calendario: '<rect x="3" y="4.5" width="18" height="16.5" rx="3"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4"/><path d="M7.5 13.5h2M11 13.5h2M14.5 13.5h2M7.5 17h2M11 17h2"/>',
  pacientes: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.6-3.4 3.2-5.5 6.5-5.5s5.9 2.1 6.5 5.5"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.8c1.9.7 3.2 2.5 3.5 5.2"/>',
  servicios: '<path d="M12 4.2c-1.4 0-2.1.6-3.1.6s-1.7-.6-2.6-.2c-1.3.6-1.7 2.3-1.3 4 .4 1.6 1.1 2.6 1.4 4.3.3 1.9.6 4.5 1.8 4.5 1.1 0 1.2-2 1.7-3.3.3-.9.7-1.3 1.4-1.3h1.4c.7 0 1.1.4 1.4 1.3.5 1.3.6 3.3 1.7 3.3 1.2 0 1.5-2.6 1.8-4.5.3-1.7 1-2.7 1.4-4.3.4-1.7 0-3.4-1.3-4-.9-.4-1.6.2-2.6.2s-1.7-.6-3.1-.6z"/>',
  salir: '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 16.5 14.5 12 10 7.5M14.5 12H4"/>',
  izquierda: '<path d="m14.5 6-6 6 6 6"/>',
  derecha: '<path d="m9.5 6 6 6-6 6"/>',
  reloj: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  usuario: '<circle cx="12" cy="8" r="4"/><path d="M4 21c.8-4 4-6.5 8-6.5s7.2 2.5 8 6.5"/>',
  editar: '<path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16v4z"/><path d="m13.5 6.5 4 4"/>',
  cancelar: '<circle cx="12" cy="12" r="9"/><path d="m15 9-6 6M9 9l6 6"/>',
  basura: '<path d="M4 7h16M10 11v6M14 11v6M5.5 7l1 12a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2l1-12M9 7V4.5A1.5 1.5 0 0 1 10.5 3h3A1.5 1.5 0 0 1 15 4.5V7"/>',
  buscar: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  mas: '<path d="M12 5v14M5 12h14"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  ojo: '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  ojoNo: '<path d="M10.6 5.1A10 10 0 0 1 12 5c6.4 0 10 7 10 7a17 17 0 0 1-2.2 3.2M6.6 6.6C3.8 8.4 2 12 2 12s3.6 7 10 7c1.9 0 3.6-.6 5-1.5M9.9 9.9a3 3 0 0 0 4.2 4.2M3 3l18 18"/>',
  llave: '<circle cx="8" cy="15" r="4.5"/><path d="m11.2 11.8 8.3-8.3M16.5 6.5l2.5 2.5M14 9l2 2"/>',
  alerta: '<path d="M12 3.5 2.5 20h19L12 3.5z"/><path d="M12 10v4.5M12 17.5v.01"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5v.01"/>',
  error: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.01"/>',
  estetoscopio: '<path d="M5 3v5a5 5 0 0 0 10 0V3"/><path d="M10 13v2.5a5 5 0 0 0 10 0V13"/><circle cx="20" cy="11" r="2"/>',
  telefono: '<path d="M5 3.5h3.5l1.5 4.5-2.2 1.4a11 11 0 0 0 5.8 5.8L15 13l4.5 1.5V18a2 2 0 0 1-2 2A15.5 15.5 0 0 1 3 5.5a2 2 0 0 1 2-2z"/>',
  correo: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m3.5 6.5 8.5 6.5 8.5-6.5"/>',
  escudo: '<path d="M12 3 4.5 6v5.5c0 4.6 3.2 8.4 7.5 9.5 4.3-1.1 7.5-4.9 7.5-9.5V6L12 3z"/><path d="m9 12 2 2 4-4"/>',
  rayo: '<path d="M13 2.5 4.5 13.5H12l-1 8 8.5-11H12l1-8z"/>',
  destello: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6.3 6.3l2.5 2.5M15.2 15.2l2.5 2.5M6.3 17.7l2.5-2.5M15.2 8.8l2.5-2.5"/>',
  radiografia: '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 3v18M16 3v18M8 9h8M8 15h8"/>',
  ajuste: '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>',
  sol: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  luna: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
  cerrar: '<path d="M18 6 6 18M6 6l12 12"/>',
  expediente: '<path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
  dado: '<rect x="3.5" y="3.5" width="17" height="17" rx="4"/><circle cx="8.5" cy="8.5" r="1" fill="currentColor"/><circle cx="15.5" cy="15.5" r="1" fill="currentColor"/><circle cx="15.5" cy="8.5" r="1" fill="currentColor"/><circle cx="8.5" cy="15.5" r="1" fill="currentColor"/>',
};
const icono = (nombre, clase = '') => `<svg class="${clase}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${RUTAS[nombre] || ''}</svg>`;
const DECORACION = '<svg class="acceso__decoracion" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width=".35">' + RUTAS.servicios + '</svg>';

function iconoServicio(nombre) {
  const n = nombre.toLowerCase();
  if (n.includes('radiograf')) return 'radiografia';
  if (n.includes('limpieza')) return 'destello';
  if (n.includes('ortodoncia') || n.includes('ajuste')) return 'ajuste';
  if (n.includes('valoraci')) return 'estetoscopio';
  return 'servicios';
}

/* --- Estado ----------------------------------------------------------------------- */
const E = {
  sesion: null, demo: [], horarios: [], hoy: '', vista: 'inicio',
  dentistas: [], servicios: [], pacientes: [],
  agendar: null,
  citas: { fecha: '', dentista: '', paciente: '', canceladas: true, pestana: 'proximas' },
  agendaFecha: '',
};

function agendarNuevo(paciente = null) {
  return { paciente, dentista: null, fecha: sumarDias(E.hoy, 1), hora: null, servicio: null, motivo: '', semana: 0, disponibilidad: null, cargando: false };
}

/* --- Avisos (RF-10) ------------------------------------------------------------------ */
function avisar(mensaje) {
  if (!mensaje) return;
  const tipo = mensaje.startsWith('Error') ? 'error' : mensaje.startsWith('Aviso') ? 'aviso' : 'exito';
  const titulo = { error: 'No se pudo completar', aviso: 'Aviso', exito: 'Listo' }[tipo];
  const texto = mensaje.replace(/^(Error|Aviso):\s*/, '');
  const nodo = document.createElement('div');
  nodo.className = `aviso aviso--${tipo}`;
  nodo.innerHTML = `<div class="aviso__icono">${icono(tipo === 'exito' ? 'check' : tipo === 'error' ? 'error' : 'info')}</div>
    <div class="aviso__texto"><strong>${titulo}</strong>${esc(texto)}</div>
    <button aria-label="Cerrar">${icono('cerrar')}</button>`;
  const quitar = () => { nodo.classList.add('saliendo'); setTimeout(() => nodo.remove(), 240); };
  nodo.querySelector('button').onclick = quitar;
  $('#avisos').append(nodo);
  setTimeout(quitar, tipo === 'error' ? 7000 : 4500);
}

/* --- Ventanas modales ------------------------------------------------------------------ */
let alCerrarModal = null;
function abrirModal(html, { ancho = false, alCerrar = null } = {}) {
  alCerrarModal = alCerrar;
  $('#capa-modal').innerHTML = `<div class="fondo-modal"><div class="modal ${ancho ? 'modal--ancho' : ''}" role="dialog" aria-modal="true">${html}</div></div>`;
  const fondo = $('.fondo-modal');
  fondo.addEventListener('mousedown', (e) => { if (e.target === fondo) cerrarModal(); });
  setTimeout(() => $('.modal input:not([type=hidden]), .modal select, .modal button.boton--primario')?.focus(), 30);
  return $('.modal');
}
function cerrarModal() {
  $('#capa-modal').innerHTML = '';
  const fn = alCerrarModal; alCerrarModal = null;
  if (fn) fn();
}
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && $('.fondo-modal')) cerrarModal(); });

function confirmar({ titulo, texto, boton = 'Confirmar', peligro = false, iconoNombre = 'alerta' }) {
  return new Promise((resolver) => {
    let respuesta = false;
    abrirModal(`
      <div class="modal__cabecera">
        <div class="modal__icono ${peligro ? 'modal__icono--peligro' : ''}">${icono(iconoNombre)}</div>
        <div><h3>${esc(titulo)}</h3><p>${texto}</p></div>
      </div>
      <div class="modal__pie">
        <button class="boton" data-r="no">Volver</button>
        <button class="boton ${peligro ? 'boton--peligro' : 'boton--primario'}" data-r="si">${esc(boton)}</button>
      </div>`, { alCerrar: () => resolver(respuesta) });
    $$('.modal [data-r]').forEach((b) => b.onclick = () => { respuesta = b.dataset.r === 'si'; cerrarModal(); });
  });
}

async function conCarga(boton, tarea) {
  boton?.classList.add('cargando');
  try { return await tarea(); } finally { boton?.classList.remove('cargando'); }
}

/* ==========================================================================
   Acceso: iniciar sesión y crear cuenta (paciente nuevo)
   ========================================================================== */
function renderAcceso(modo = 'entrar') {
  $('#app').innerHTML = `
  <div class="acceso">
    <aside class="acceso__marca">
      ${DECORACION}
      <div class="logo"><div class="logo__marca"></div><div class="logo__texto"><strong>Orthoimagen Dental</strong><span>Clínica dental</span></div></div>
      <div class="acceso__mensaje">
        <span class="acceso__sobretitulo">Citas en línea</span>
        <h1>Su próxima cita,<br><em>en menos de dos minutos.</em></h1>
        <p>Consulte horarios libres en tiempo real, agende con el especialista que prefiera y administre sus citas sin llamar a la clínica.</p>
        <ul class="ventajas">
          <li><span class="ventajas__icono">${icono('calendario')}</span><div>Horarios en tiempo real<small>Solo verá los espacios realmente libres.</small></div></li>
          <li><span class="ventajas__icono">${icono('rayo')}</span><div>Cinco pasos y listo<small>Dentista, fecha, horario, servicio y confirmar.</small></div></li>
          <li><span class="ventajas__icono">${icono('escudo')}</span><div>Sus datos protegidos<small>Contraseñas cifradas y acceso por rol.</small></div></li>
        </ul>
      </div>
      <div class="acceso__pie">© 2026 Orthoimagen Dental · Sistema de citas v1.1</div>
    </aside>
    <main class="acceso__formulario"><div class="tarjeta-acceso" id="tarjeta-acceso"></div></main>
  </div>`;
  renderFormularioAcceso(modo);
}

function campoClave(id, etiqueta, autocompletar, extra = '') {
  return `<label class="campo"><span class="campo__etiqueta">${etiqueta}</span>
    <div class="entrada-con-icono">${icono('llave')}
      <input class="entrada" id="${id}" type="password" autocomplete="${autocompletar}" ${extra}>
      <button type="button" class="icono-boton ojo" data-ver="${id}" aria-label="Mostrar contraseña">${icono('ojo')}</button>
    </div></label>`;
}

function activarOjos(raiz = document) {
  $$('[data-ver]', raiz).forEach((b) => b.onclick = () => {
    const campo = $('#' + b.dataset.ver);
    const ver = campo.type === 'password';
    campo.type = ver ? 'text' : 'password';
    b.innerHTML = icono(ver ? 'ojoNo' : 'ojo');
  });
}

function renderFormularioAcceso(modo) {
  const tarjeta = $('#tarjeta-acceso');
  const pestanas = `<div class="segmentado">
      <button type="button" class="${modo === 'entrar' ? 'activo' : ''}" data-modo="entrar">Iniciar sesión</button>
      <button type="button" class="${modo === 'registro' ? 'activo' : ''}" data-modo="registro">Soy paciente nuevo</button>
    </div>`;
  if (modo === 'entrar') {
    tarjeta.innerHTML = `
      <h2>Bienvenido de nuevo</h2>
      <p>Ingrese con el usuario y la contraseña que le dio la clínica o que usted creó.</p>
      ${pestanas}
      <form class="formulario" id="form-entrar" novalidate>
        <div class="mensaje-en-linea" id="error-acceso">${icono('error')}<span></span></div>
        <label class="campo"><span class="campo__etiqueta">Usuario</span>
          <div class="entrada-con-icono">${icono('usuario')}<input class="entrada" id="usuario" autocomplete="username" placeholder="p. ej. ana.perez"></div></label>
        ${campoClave('clave', 'Contraseña', 'current-password', 'placeholder="••••••••"')}
        <button class="boton boton--primario boton--grande boton--bloque" type="submit">Entrar</button>
      </form>
      ${E.demo.length ? `<div class="separador">Accesos de demostración</div>
      <div class="demo">${E.demo.filter((d) => ['paciente01', 'recepcion01', 'dentista01'].includes(d.usuario)).map((d) => `
        <button type="button" data-demo="${esc(d.usuario)}">
          <span class="avatar avatar--chico ${d.rol === 'recepcionista' ? 'avatar--oro' : d.rol === 'dentista' ? 'avatar--tinta' : ''}">${d.rol === 'paciente' ? 'P' : d.rol === 'dentista' ? 'D' : 'R'}</span>
          <strong>${{ paciente: 'Paciente', recepcionista: 'Recepción', dentista: 'Dentista' }[d.rol]}</strong>${esc(d.usuario)}
        </button>`).join('')}</div>` : ''}`;
    $('#usuario').focus();
    $('#form-entrar').onsubmit = async (e) => {
      e.preventDefault();
      await entrar($('#usuario').value, $('#clave').value, e.submitter);
    };
    $$('[data-demo]').forEach((b) => b.onclick = () => {
      const d = E.demo.find((x) => x.usuario === b.dataset.demo);
      $('#usuario').value = d.usuario; $('#clave').value = d.contrasena;
      entrar(d.usuario, d.contrasena, $('#form-entrar button[type=submit]'));
    });
  } else {
    tarjeta.innerHTML = `
      <h2>Cree su cuenta</h2>
      <p>Regístrese una sola vez y agende su primera cita enseguida.</p>
      ${pestanas}
      <form class="formulario" id="form-registro" novalidate>
        <div class="mensaje-en-linea" id="error-acceso">${icono('error')}<span></span></div>
        <div class="fila-campos">
          <label class="campo"><span class="campo__etiqueta">Nombre(s)</span><input class="entrada" name="nombre" autocomplete="given-name"></label>
          <label class="campo"><span class="campo__etiqueta">Apellidos</span><input class="entrada" name="apellidos" autocomplete="family-name"></label>
        </div>
        <div class="fila-campos">
          <label class="campo"><span class="campo__etiqueta">Teléfono</span><input class="entrada" name="telefono" inputmode="tel" placeholder="10 dígitos" autocomplete="tel"></label>
          <label class="campo"><span class="campo__etiqueta">Nacimiento <small>opcional</small></span><input class="entrada" name="fecha_nacimiento" type="date" max="${E.hoy}"></label>
        </div>
        <label class="campo"><span class="campo__etiqueta">Correo electrónico <small>opcional</small></span><input class="entrada" name="correo" type="email" placeholder="nombre@correo.com" autocomplete="email"></label>
        <label class="campo"><span class="campo__etiqueta">Usuario</span><input class="entrada" name="usuario" placeholder="p. ej. sofia.lara" autocomplete="username"><span class="campo__ayuda">De 4 a 30 caracteres, sin espacios.</span></label>
        <div class="fila-campos">
          <div>${campoClave('reg-clave', 'Contraseña', 'new-password')}<div class="fuerza" id="fuerza"><i></i><i></i><i></i><i></i></div></div>
          ${campoClave('reg-confirmacion', 'Confirmar', 'new-password')}
        </div>
        <span class="campo__ayuda">Mínimo 8 caracteres, con letras y números.</span>
        <button class="boton boton--primario boton--grande boton--bloque" type="submit">Crear mi cuenta</button>
      </form>
      <div class="nota">${icono('info')}<span>¿Ya es paciente de la clínica pero no tiene usuario? Pida en recepción que le creen su acceso; así conserva su historial.</span></div>`;
    $('[name=nombre]').focus();
    $('#reg-clave').oninput = (e) => {
      const v = e.target.value;
      const nivel = !v ? 0 : 1 + (v.length >= 8 && /\d/.test(v) && /[a-z]/i.test(v)) + /[A-Z]/.test(v) + (/[^A-Za-z0-9]/.test(v) || v.length >= 12);
      $('#fuerza').dataset.nivel = nivel;
    };
    $('#form-registro').onsubmit = async (e) => {
      e.preventDefault();
      const datos = Object.fromEntries(new FormData(e.target));
      datos.contrasena = $('#reg-clave').value;
      datos.confirmacion = $('#reg-confirmacion').value;
      const r = await conCarga(e.submitter, () => api('crear_cuenta', datos));
      if (!r.exito) return mostrarErrorAcceso(r.mensaje);
      E.sesion = r.sesion;
      await arrancarSesion();
      avisar(r.mensaje);
    };
  }
  activarOjos(tarjeta);
  $$('[data-modo]', tarjeta).forEach((b) => b.onclick = () => renderFormularioAcceso(b.dataset.modo));
}

function mostrarErrorAcceso(mensaje) {
  const caja = $('#error-acceso');
  caja.classList.remove('visible'); void caja.offsetWidth;
  caja.querySelector('span').textContent = mensaje.replace(/^Error:\s*/, '');
  caja.classList.add('visible');
}

async function entrar(usuario, clave, boton) {
  const r = await conCarga(boton, () => api('iniciar_sesion', usuario, clave));
  if (!r.exito) return mostrarErrorAcceso(r.mensaje);
  E.sesion = r.sesion;
  await arrancarSesion();
}

async function arrancarSesion() {
  const [d, s] = await Promise.all([api('dentistas'), api('servicios')]);
  E.dentistas = d.dentistas || [];
  E.servicios = s.servicios || [];
  E.agendar = agendarNuevo();
  E.agendaFecha = E.hoy;
  E.citas = { fecha: '', dentista: '', paciente: '', canceladas: true, pestana: 'proximas' };
  renderArmazon();
  irA('inicio');
}

async function salir() {
  await api('cerrar_sesion');
  E.sesion = null;
  renderAcceso();
}

/* ==========================================================================
   Armazón: barra lateral y cabecera
   ========================================================================== */
const MENUS = {
  paciente: [['inicio', 'Inicio', 'inicio'], ['agendar', 'Agendar cita', 'agendar'], ['citas', 'Mis citas', 'calendario'], ['servicios', 'Servicios', 'servicios']],
  recepcionista: [['inicio', 'Panel del día', 'inicio'], ['agendar', 'Nueva cita', 'agendar'], ['citas', 'Agenda de citas', 'calendario'], ['pacientes', 'Pacientes', 'pacientes'], ['servicios', 'Servicios', 'servicios']],
  dentista: [['inicio', 'Inicio', 'inicio'], ['citas', 'Mi agenda', 'calendario'], ['servicios', 'Servicios', 'servicios']],
};

function renderArmazon() {
  const s = E.sesion;
  $('#app').innerHTML = `
  <div class="armazon">
    <aside class="lateral">
      <div class="logo"><div class="logo__marca"></div><div class="logo__texto"><strong>Orthoimagen</strong><span>Dental</span></div></div>
      <nav class="nav" id="nav">
        <div class="nav__titulo">${s.rol === 'recepcionista' ? 'Recepción' : s.rol === 'dentista' ? 'Consultorio' : 'Mi espacio'}</div>
        ${MENUS[s.rol].map(([vista, texto, ic]) => `<button data-vista="${vista}">${icono(ic)}<span>${texto}</span></button>`).join('')}
      </nav>
      <div class="lateral__pie">
        <div class="tarjeta-usuario">
          <div class="avatar">${esc(s.iniciales)}</div>
          <div class="tarjeta-usuario__datos"><strong>${esc(s.nombre)}</strong><span>${esc(s.detalle)}</span></div>
          <button class="icono-boton" id="boton-salir" title="Cerrar sesión" aria-label="Cerrar sesión">${icono('salir')}</button>
        </div>
      </div>
    </aside>
    <main class="principal" id="principal">
      <header class="cabecera" id="cabecera"></header>
      <section class="contenido" id="contenido"></section>
    </main>
  </div>`;
  $$('#nav [data-vista]').forEach((b) => b.onclick = () => irA(b.dataset.vista));
  $('#boton-salir').onclick = async () => {
    if (await confirmar({ titulo: '¿Cerrar sesión?', texto: 'Podrá volver a entrar con su usuario y contraseña.', boton: 'Cerrar sesión', iconoNombre: 'salir' })) salir();
  };
  $('#principal').addEventListener('scroll', (e) => $('#cabecera').classList.toggle('con-sombra', e.target.scrollTop > 4));
}

function cabecera(titulo, acciones = '', sobretitulo = fechaCompleta(E.hoy)) {
  $('#cabecera').innerHTML = `<div><div class="cabecera__fecha">${esc(sobretitulo)}</div><h1>${titulo}</h1></div><div class="cabecera__acciones">${acciones}</div>`;
  $$('#cabecera [data-ir]').forEach((b) => b.onclick = () => irA(b.dataset.ir));
}

const VISTAS = { inicio: vistaInicio, agendar: vistaAgendar, citas: vistaCitas, pacientes: vistaPacientes, servicios: vistaServicios };

function irA(vista) {
  E.vista = vista;
  $$('#nav [data-vista]').forEach((b) => b.classList.toggle('activo', b.dataset.vista === vista));
  $('#principal').scrollTop = 0;
  const contenido = $('#contenido');
  contenido.style.animation = 'none'; void contenido.offsetWidth; contenido.style.animation = '';
  VISTAS[vista]();
}

const botonAgendar = () => E.sesion.rol === 'dentista' ? '' :
  `<button class="boton boton--primario" data-ir="agendar">${icono('mas')}${E.sesion.rol === 'paciente' ? 'Agendar cita' : 'Nueva cita'}</button>`;

/* --- Piezas reutilizables ------------------------------------------------------------- */
function filaCita(c, { acciones = true, mostrarPaciente = false, mostrarFecha = true } = {}) {
  const puede = acciones && activa(c) && E.sesion.rol !== 'dentista' && c.fecha >= E.hoy;
  return `<div class="fila-cita ${c.estatus === 'Cancelada' ? 'cancelada' : ''}">
    <div class="fila-cita__hora">${esc(c.hora)}${mostrarFecha ? `<small>${esc(diaCorto(c.fecha))} ${esc(aFecha(c.fecha).getDate())} ${esc(mesCorto(c.fecha))}</small>` : ''}</div>
    <div style="min-width:0">
      <div class="fila-cita__titulo">${esc(mostrarPaciente ? c.paciente : c.servicio)}</div>
      <div class="fila-cita__sub">${esc(mostrarPaciente ? `${c.servicio} · ${c.dentista}` : `con ${c.dentista}`)}${c.motivo ? ' · ' + esc(c.motivo) : ''}</div>
    </div>
    <div class="fila-cita__acciones">
      <span class="insignia insignia--${esc(c.estatus)}">${esc(c.estatus)}</span>
      ${puede ? `<button class="icono-boton" title="Modificar" data-modificar="${c.id_cita}">${icono('editar')}</button>
      <button class="icono-boton icono-boton--peligro" title="Cancelar" data-cancelar="${c.id_cita}">${icono('cancelar')}</button>` : ''}
    </div>
  </div>`;
}

function vacio(iconoNombre, titulo, texto, accion = '') {
  return `<div class="vacio"><div class="vacio__icono">${icono(iconoNombre)}</div><h4>${titulo}</h4><p>${texto}</p>${accion}</div>`;
}

function indicador(valor, etiqueta, iconoNombre, variante = '') {
  return `<div class="tarjeta indicador"><div class="indicador__icono ${variante}">${icono(iconoNombre)}</div>
    <div><div class="indicador__valor">${esc(valor)}</div><div class="indicador__etiqueta">${esc(etiqueta)}</div></div></div>`;
}

function enlazarAccionesCita(raiz, citas, alTerminar) {
  $$('[data-modificar]', raiz).forEach((b) => b.onclick = () => modalModificar(citas.find((c) => c.id_cita == b.dataset.modificar), alTerminar));
  $$('[data-cancelar]', raiz).forEach((b) => b.onclick = () => cancelarCita(citas.find((c) => c.id_cita == b.dataset.cancelar), alTerminar));
  $$('[data-eliminar]', raiz).forEach((b) => b.onclick = () => eliminarCita(citas.find((c) => c.id_cita == b.dataset.eliminar), alTerminar));
}

/* ==========================================================================
   Inicio
   ========================================================================== */
async function vistaInicio() {
  const s = E.sesion;
  const nombre = s.rol === 'recepcionista' ? 'equipo de recepción' : primerNombre(s.nombre);
  cabecera(`${saludo()}, ${esc(nombre)}`, botonAgendar());
  const contenido = $('#contenido');
  contenido.innerHTML = '<div class="cargando-bloque"></div>';
  const r = await api('resumen');
  if (!r.exito) { avisar(r.mensaje); contenido.innerHTML = ''; return; }
  const ind = r.indicadores;

  if (s.rol === 'paciente') {
    const [proxima, ...resto] = r.proximas;
    contenido.innerHTML = `
      <div class="rejilla rejilla--inicio">
        <div class="rejilla">
          ${proxima ? `
          <div class="destacada">
            <div class="destacada__etiqueta">Su próxima cita</div>
            <div class="destacada__cuerpo">
              <div class="bloque-fecha"><span>${esc(mesCorto(proxima.fecha))}</span><strong>${aFecha(proxima.fecha).getDate()}</strong><small>${esc(diaCorto(proxima.fecha))}</small></div>
              <div>
                <h2>${esc(proxima.servicio)}</h2>
                <div class="destacada__detalle">
                  <span>${icono('reloj')}${esc(proxima.hora)} h</span>
                  <span>${icono('usuario')}${esc(proxima.dentista)}</span>
                  <span>${icono('calendario')}<span>${esc(fechaLarga(proxima.fecha))}</span></span>
                </div>
              </div>
            </div>
            <div class="destacada__acciones">
              <button class="boton boton--claro" data-modificar="${proxima.id_cita}">${icono('editar')}Cambiar fecha u hora</button>
              <button class="boton" data-cancelar="${proxima.id_cita}">${icono('cancelar')}Cancelar</button>
            </div>
          </div>` : `
          <div class="tarjeta">${vacio('agendar', 'Aún no tiene citas próximas', 'Elija dentista, fecha y horario: en menos de dos minutos queda agendada.', `<button class="boton boton--primario" data-ir="agendar">${icono('mas')}Agendar mi cita</button>`)}</div>`}
          <div class="tarjeta">
            <div class="tarjeta__cabecera"><div><h3>Otras citas próximas</h3><p>Programadas o reprogramadas a partir de hoy.</p></div><button class="boton boton--chico" data-ir="citas">Ver todas</button></div>
            <div class="lista">${resto.length ? resto.map((c) => filaCita(c)).join('') : `<div class="vacio" style="padding:28px"><p style="margin:0">No tiene más citas programadas.</p></div>`}</div>
          </div>
        </div>
        <div class="rejilla">
          <div class="rejilla" style="grid-template-columns:1fr 1fr">
            ${indicador(ind.proximas, 'Citas próximas', 'calendario')}
            ${indicador(ind.historial, 'En su historial', 'expediente', 'indicador__icono--oro')}
          </div>
          <div class="tarjeta consejo">
            <div class="indicador__icono indicador__icono--info">${icono('info')}</div>
            <div><strong>¿Necesita cambiar su cita?</strong><p>Puede modificarla o cancelarla desde aquí o en “Mis citas”. Al cancelar, el horario queda libre para otro paciente.</p></div>
          </div>
          <div class="tarjeta consejo">
            <div class="indicador__icono">${icono('reloj')}</div>
            <div><strong>Horario de atención</strong><p>Citas de ${esc(E.horarios[0])} a ${esc(horaCierre())} h, en bloques de una hora. Le recomendamos llegar 10 minutos antes.</p></div>
          </div>
        </div>
      </div>`;
    enlazarAccionesCita(contenido, r.proximas, vistaInicio);
  } else if (s.rol === 'recepcionista') {
    contenido.innerHTML = `
      <div class="rejilla rejilla--indicadores">
        ${indicador(ind.hoy, 'Citas para hoy', 'calendario')}
        ${indicador(ind.manana, 'Citas para mañana', 'agendar', 'indicador__icono--info')}
        ${indicador(ind.pacientes, 'Pacientes registrados', 'pacientes', 'indicador__icono--oro')}
        ${indicador(ind.sin_acceso, 'Pacientes sin acceso', 'llave', 'indicador__icono--aviso')}
      </div>
      <div class="rejilla rejilla--inicio mt-24">
        <div class="tarjeta">
          <div class="tarjeta__cabecera"><div><h3>Agenda de hoy</h3><p>${esc(fechaLarga(E.hoy))}</p></div><button class="boton boton--chico" data-ir="citas">Abrir agenda</button></div>
          <div class="lista">${r.hoy.length ? r.hoy.map((c) => filaCita(c, { mostrarPaciente: true, mostrarFecha: false })).join('') : vacio('calendario', 'Sin citas para hoy', 'Las citas que se registren para hoy aparecerán aquí.')}</div>
        </div>
        <div class="tarjeta">
          <div class="tarjeta__cabecera"><div><h3>Próximas citas</h3><p>Las siguientes 8 en la agenda.</p></div></div>
          <div class="lista">${r.proximas.length ? r.proximas.map((c) => filaCita(c, { mostrarPaciente: true, acciones: false })).join('') : vacio('agendar', 'Agenda libre', 'No hay citas programadas a partir de hoy.')}</div>
        </div>
      </div>`;
    enlazarAccionesCita(contenido, r.hoy, vistaInicio);
  } else {
    contenido.innerHTML = `
      <div class="rejilla rejilla--3">
        ${indicador(ind.hoy, 'Pacientes hoy', 'pacientes')}
        ${indicador(ind.libres_hoy, 'Espacios libres hoy', 'reloj', 'indicador__icono--oro')}
        ${indicador(ind.manana, 'Citas para mañana', 'calendario', 'indicador__icono--info')}
      </div>
      <div class="tarjeta mt-24">
        <div class="tarjeta__cabecera"><div><h3>Su jornada de hoy</h3><p>${esc(fechaLarga(E.hoy))}</p></div><button class="boton boton--chico" data-ir="citas">Ver agenda completa</button></div>
        ${lineaDeTiempo(r.hoy, E.hoy)}
      </div>`;
  }
  $$('#contenido [data-ir]').forEach((b) => b.onclick = () => irA(b.dataset.ir));
}

/* ==========================================================================
   Agendar (RF-07, RF-02, RF-01) · 5 pasos
   ========================================================================== */
async function vistaAgendar() {
  const esRecepcion = E.sesion.rol === 'recepcionista';
  cabecera(esRecepcion ? 'Registrar una cita' : 'Agendar una cita', '', esRecepcion ? 'Recepción' : 'Cinco pasos y listo');
  if (!E.agendar) E.agendar = agendarNuevo();
  if (esRecepcion && !E.pacientes.length) E.pacientes = (await api('pacientes', '')).pacientes || [];
  renderAgendar();
  if (E.agendar.dentista && !E.agendar.disponibilidad) cargarDisponibilidad();
}

function renderAgendar() {
  const A = E.agendar;
  const esRecepcion = E.sesion.rol === 'recepcionista';
  const n = esRecepcion ? 1 : 0;
  const dentista = E.dentistas.find((d) => d.id === A.dentista);
  const servicio = E.servicios.find((s) => s.id_servicio === A.servicio);
  const inicioSemana = sumarDias(E.hoy, A.semana * 7);
  const dias = Array.from({ length: 7 }, (_, i) => sumarDias(inicioSemana, i));

  $('#contenido').innerHTML = `
  <div class="agendar">
    <div class="tarjeta">
      ${esRecepcion ? `
      <div class="paso ${A.paciente ? 'listo' : ''}">
        <div class="paso__titulo"><span class="paso__numero">1</span><div><h3>Paciente</h3><p>Busque por nombre o teléfono.</p></div>
          <button class="boton boton--chico boton--suave" id="nuevo-paciente">${icono('mas')}Paciente nuevo</button></div>
        ${A.paciente ? `<div class="paciente-elegido"><span class="avatar">${esc(A.paciente.iniciales)}</span>
            <div><strong>${esc(A.paciente.nombre)} ${esc(A.paciente.apellidos)}</strong><small>${esc(A.paciente.telefono)} · expediente ${A.paciente.id_paciente}</small></div>
            <button class="boton boton--chico" id="cambiar-paciente">Cambiar</button></div>`
          : `<div class="buscador" id="buscador"><div class="entrada-con-icono">${icono('buscar')}<input class="entrada" id="buscar-paciente" placeholder="Escriba para buscar…" autocomplete="off"></div><div class="buscador__lista" id="lista-pacientes"></div></div>`}
      </div>` : ''}
      <div class="paso ${A.dentista ? 'listo' : ''}">
        <div class="paso__titulo"><span class="paso__numero">${n + 1}</span><div><h3>Dentista</h3><p>Elija con quién desea su cita.</p></div></div>
        <div class="opciones">${E.dentistas.map((d) => `
          <button class="opcion ${A.dentista === d.id ? 'elegida' : ''}" data-dentista="${d.id}">
            <span class="avatar">${esc(d.iniciales)}</span><span><strong>${esc(d.nombre)}</strong><small>${esc(d.especialidad)}</small></span>
          </button>`).join('')}</div>
      </div>
      <div class="paso ${A.fecha ? 'listo' : ''}">
        <div class="paso__titulo"><span class="paso__numero">${n + 2}</span><div><h3>Fecha</h3><p>${A.fecha ? esc(fechaCompleta(A.fecha)) : 'Elija un día'}</p></div>
          <input type="date" class="entrada" id="otra-fecha" style="width:170px;height:34px;margin-left:auto" min="${E.hoy}" value="${A.fecha || ''}" title="Elegir otra fecha"></div>
        <div class="dias">
          <button class="icono-boton" id="semana-anterior" ${A.semana === 0 ? 'disabled style="opacity:.4"' : ''} aria-label="Semana anterior">${icono('izquierda')}</button>
          <div class="dias__lista">${dias.map((f) => `
            <button class="dia ${f === A.fecha ? 'elegido' : ''} ${f === E.hoy ? 'hoy' : ''}" data-fecha="${f}">
              <span>${f === E.hoy ? 'Hoy' : esc(diaCorto(f))}</span><strong>${aFecha(f).getDate()}</strong><small>${esc(mesCorto(f))}</small>
            </button>`).join('')}</div>
          <button class="icono-boton" id="semana-siguiente" aria-label="Semana siguiente">${icono('derecha')}</button>
        </div>
      </div>
      <div class="paso ${A.hora ? 'listo' : ''}">
        <div class="paso__titulo"><span class="paso__numero">${n + 3}</span><div><h3>Horario</h3><p>${dentista ? `Disponibilidad de ${esc(dentista.nombre)}` : 'Primero elija un dentista.'}</p></div></div>
        <div id="horarios">${renderHorarios()}</div>
      </div>
      <div class="paso ${A.servicio ? 'listo' : ''}">
        <div class="paso__titulo"><span class="paso__numero">${n + 4}</span><div><h3>Servicio</h3><p>¿Qué tratamiento necesita?</p></div></div>
        <div class="opciones">${E.servicios.map((s) => `
          <button class="opcion ${A.servicio === s.id_servicio ? 'elegida' : ''}" data-servicio="${s.id_servicio}">
            <span class="servicio__icono" style="width:38px;height:38px;border-radius:11px">${icono(iconoServicio(s.nombre))}</span>
            <span><strong>${esc(s.nombre)}</strong><small>${s.duracion_min} min</small></span>
            <span class="opcion__precio">${dinero(s.precio)}</span>
          </button>`).join('')}</div>
        <label class="campo mt-16"><span class="campo__etiqueta">Motivo de la consulta <small>opcional</small></span>
          <textarea class="entrada" id="motivo" placeholder="Cuéntenos brevemente, por ejemplo: molestia al masticar del lado derecho.">${esc(A.motivo)}</textarea></label>
      </div>
    </div>

    <aside class="tarjeta resumen">
      <div class="resumen__cabecera"><span>Resumen</span><h3>Su cita</h3></div>
      <ul class="resumen__lista">
        ${esRecepcion ? `<li>${icono('usuario')}<div><small>Paciente</small>${A.paciente ? `<strong>${esc(A.paciente.nombre)} ${esc(A.paciente.apellidos)}</strong>` : '<span class="pendiente">Sin elegir</span>'}</div></li>` : ''}
        <li>${icono('estetoscopio')}<div><small>Dentista</small>${dentista ? `<strong>${esc(dentista.nombre)}</strong>` : '<span class="pendiente">Sin elegir</span>'}</div></li>
        <li>${icono('calendario')}<div><small>Fecha</small>${A.fecha ? `<strong>${esc(fechaLarga(A.fecha))}</strong>` : '<span class="pendiente">Sin elegir</span>'}</div></li>
        <li>${icono('reloj')}<div><small>Horario</small>${A.hora ? `<strong>${esc(A.hora)} h</strong>` : '<span class="pendiente">Sin elegir</span>'}</div></li>
        <li>${icono('servicios')}<div><small>Servicio</small>${servicio ? `<strong>${esc(servicio.nombre)}</strong>` : '<span class="pendiente">Sin elegir</span>'}</div></li>
      </ul>
      <div class="resumen__total"><span>Costo estimado</span><strong>${servicio ? dinero(servicio.precio) : '—'}</strong></div>
      <div class="resumen__pie">
        <button class="boton boton--primario boton--grande boton--bloque" id="confirmar-cita">${icono('check')}Confirmar cita</button>
        <p>Podrá modificarla o cancelarla después.</p>
      </div>
    </aside>
  </div>`;

  // Eventos
  $$('[data-dentista]').forEach((b) => b.onclick = () => { A.dentista = Number(b.dataset.dentista); A.hora = null; cargarDisponibilidad(); });
  $$('[data-fecha]').forEach((b) => b.onclick = () => { A.fecha = b.dataset.fecha; A.hora = null; cargarDisponibilidad(); });
  $$('[data-servicio]').forEach((b) => b.onclick = () => { A.servicio = Number(b.dataset.servicio); renderAgendar(); });
  $('#otra-fecha').onchange = (e) => {
    if (!e.target.value) return;
    A.fecha = e.target.value; A.hora = null;
    A.semana = Math.max(0, Math.floor((aFecha(A.fecha) - aFecha(E.hoy)) / 864e5 / 7));
    cargarDisponibilidad();
  };
  $('#semana-anterior').onclick = () => { if (A.semana > 0) { A.semana--; renderAgendar(); } };
  $('#semana-siguiente').onclick = () => { A.semana++; renderAgendar(); };
  $('#motivo').oninput = (e) => { A.motivo = e.target.value; };
  enlazarHorarios();
  $('#confirmar-cita').onclick = (e) => confirmarCita(e.currentTarget);
  if (esRecepcion) enlazarBuscadorPacientes();
}

function renderHorarios() {
  const A = E.agendar;
  if (!A.dentista || !A.fecha) return `<div class="campo__ayuda">Elija un dentista y una fecha para ver los horarios.</div>`;
  if (A.cargando || !A.disponibilidad) return '<div class="cargando-bloque" style="padding:24px"></div>';
  const disp = A.disponibilidad;
  if (!disp.exito) return `<div class="mensaje-en-linea visible">${icono('error')}<span>${esc(disp.mensaje.replace(/^Error:\s*/, ''))}</span></div>`;
  const libres = new Set(disp.libres);
  const grupo = (titulo, ic, horas) => horas.length ? `<div class="horarios__grupo">
      <div class="horarios__etiqueta">${icono(ic)}${titulo}</div>
      <div class="horarios__lista">${horas.map((h) => `<button class="horario ${A.hora === h ? 'elegido' : ''}" data-hora="${h}" ${libres.has(h) ? '' : 'disabled title="No disponible"'}>${h}</button>`).join('')}</div>
    </div>` : '';
  return `${!disp.libres.length ? `<div class="mensaje-en-linea visible" style="background:var(--aviso-suave);color:var(--aviso);border-color:#f6e2c2;margin-bottom:14px">${icono('info')}<span>${esc((disp.mensaje || '').replace(/^Aviso:\s*/, ''))}</span></div>` : ''}
    ${grupo('Mañana', 'sol', E.horarios.filter((h) => h < '13:00'))}
    ${grupo('Tarde', 'luna', E.horarios.filter((h) => h >= '13:00'))}
    <div class="horarios__leyenda"><span><i></i>Libre</span><span><i class="ocupado"></i>No disponible</span><span><i class="elegido"></i>Elegido</span></div>`;
}

function enlazarHorarios() {
  $$('[data-hora]').forEach((b) => b.onclick = () => { E.agendar.hora = b.dataset.hora; renderAgendar(); });
}

async function cargarDisponibilidad() {
  const A = E.agendar;
  A.cargando = true; A.disponibilidad = null;
  renderAgendar();
  if (!A.dentista || !A.fecha) { A.cargando = false; return; }
  const consulta = `${A.dentista}|${A.fecha}`;
  A.consulta = consulta;
  const r = await api('disponibilidad', A.dentista, A.fecha);
  if (E.agendar !== A || A.consulta !== consulta) return;
  A.cargando = false; A.disponibilidad = r;
  if (E.vista === 'agendar') renderAgendar();
}

function enlazarBuscadorPacientes() {
  const A = E.agendar;
  $('#nuevo-paciente').onclick = () => modalPaciente((p) => { A.paciente = p; renderAgendar(); });
  if (A.paciente) { $('#cambiar-paciente').onclick = () => { A.paciente = null; renderAgendar(); $('#buscar-paciente')?.focus(); }; return; }
  const entrada = $('#buscar-paciente');
  const caja = $('#buscador');
  const pintar = () => {
    const q = entrada.value.trim().toLowerCase();
    const encontrados = E.pacientes.filter((p) => `${p.nombre} ${p.apellidos} ${p.telefono}`.toLowerCase().includes(q)).slice(0, 8);
    $('#lista-pacientes').innerHTML = (encontrados.length ? encontrados.map((p) => `
      <button class="buscador__opcion" data-paciente="${p.id_paciente}"><span class="avatar avatar--chico">${esc(p.iniciales)}</span>
        <span><strong>${esc(p.nombre)} ${esc(p.apellidos)}</strong><small>${esc(p.telefono)}${p.nombre_usuario ? ' · ' + esc(p.nombre_usuario) : ''}</small></span></button>`).join('')
      : '<div class="campo__ayuda" style="padding:10px">Sin coincidencias.</div>') +
      `<button class="buscador__opcion" data-paciente-nuevo>${icono('mas')}<span><strong>Registrar paciente nuevo</strong><small>${q ? 'Con los datos que escribió' : 'Abrir el formulario de alta'}</small></span></button>`;
    $$('[data-paciente]').forEach((b) => b.onmousedown = (e) => { e.preventDefault(); A.paciente = E.pacientes.find((p) => p.id_paciente == b.dataset.paciente); renderAgendar(); });
    $('[data-paciente-nuevo]').onmousedown = (e) => { e.preventDefault(); modalPaciente((p) => { A.paciente = p; renderAgendar(); }); };
  };
  entrada.onfocus = () => { caja.classList.add('abierto'); pintar(); };
  entrada.oninput = pintar;
  entrada.onblur = () => setTimeout(() => caja.classList.remove('abierto'), 120);
}

async function confirmarCita(boton) {
  const A = E.agendar;
  const datos = { fecha: A.fecha || '', hora: A.hora || '', dentista: A.dentista || '', servicio: A.servicio || '', motivo: A.motivo };
  if (E.sesion.rol === 'recepcionista') datos.paciente = A.paciente ? A.paciente.id_paciente : '';
  const r = await conCarga(boton, () => api('registrar_cita', datos));
  if (!r.exito) {
    avisar(r.mensaje);
    if (r.mensaje.includes('no está disponible')) { A.hora = null; cargarDisponibilidad(); }
    return;
  }
  const dentista = E.dentistas.find((d) => d.id === A.dentista);
  const servicio = E.servicios.find((s) => s.id_servicio === A.servicio);
  const paciente = A.paciente;
  E.agendar = agendarNuevo();
  abrirModal(`
    <div class="modal__cuerpo" style="text-align:center;padding-top:28px">
      <div class="exito-animado">${icono('check')}</div>
      <div><h3 style="font-size:22px">¡Cita confirmada!</h3><p style="color:var(--tenue);margin:6px 0 0">Folio ${r.id_cita} · ${E.sesion.rol === 'paciente' ? 'Le esperamos.' : 'Registrada en la agenda.'}</p></div>
      <div class="recibo" style="text-align:left">
        ${paciente ? `<div><span>Paciente</span><strong>${esc(paciente.nombre)} ${esc(paciente.apellidos)}</strong></div>` : ''}
        <div><span>Fecha</span><strong>${esc(fechaLarga(datos.fecha))}</strong></div>
        <div><span>Hora</span><strong>${esc(datos.hora)} h</strong></div>
        <div><span>Dentista</span><strong>${esc(dentista?.nombre)}</strong></div>
        <div><span>Servicio</span><strong>${esc(servicio?.nombre)} · ${dinero(servicio?.precio)}</strong></div>
      </div>
    </div>
    <div class="modal__pie" style="justify-content:center">
      <button class="boton" id="otra-cita">Agendar otra</button>
      <button class="boton boton--primario" id="ver-citas">${E.sesion.rol === 'paciente' ? 'Ver mis citas' : 'Ver agenda'}</button>
    </div>`);
  $('#otra-cita').onclick = () => { cerrarModal(); irA('agendar'); };
  $('#ver-citas').onclick = () => { cerrarModal(); irA('citas'); };
}

/* ==========================================================================
   Citas: mis citas (paciente), agenda (recepción) y agenda del día (dentista)
   ========================================================================== */
function vistaCitas() {
  ({ paciente: citasPaciente, recepcionista: citasRecepcion, dentista: citasDentista })[E.sesion.rol]();
}

async function citasPaciente() {
  cabecera('Mis citas', botonAgendar());
  const contenido = $('#contenido');
  contenido.innerHTML = '<div class="cargando-bloque"></div>';
  const r = await api('citas');
  if (!r.exito) { avisar(r.mensaje); return; }
  const proximas = r.citas.filter((c) => activa(c) && c.fecha >= E.hoy);
  const historial = r.citas.filter((c) => !proximas.includes(c)).reverse();
  const lista = E.citas.pestana === 'proximas' ? proximas : historial;
  contenido.innerHTML = `
    <div class="fila entre" style="margin-bottom:16px">
      <div class="pestanas">
        <button data-pestana="proximas" class="${E.citas.pestana === 'proximas' ? 'activo' : ''}">Próximas <b>${proximas.length}</b></button>
        <button data-pestana="historial" class="${E.citas.pestana === 'historial' ? 'activo' : ''}">Historial <b>${historial.length}</b></button>
      </div>
    </div>
    <div class="tarjeta"><div class="lista">${lista.length ? lista.map((c) => filaCita(c)).join('')
      : E.citas.pestana === 'proximas'
        ? vacio('agendar', 'No tiene citas próximas', 'Cuando agende una cita aparecerá aquí con su fecha, hora y dentista.', `<button class="boton boton--primario" id="vacio-agendar">${icono('mas')}Agendar cita</button>`)
        : vacio('expediente', 'Su historial está vacío', 'Aquí verá sus citas pasadas y canceladas.')}</div></div>`;
  $$('[data-pestana]').forEach((b) => b.onclick = () => { E.citas.pestana = b.dataset.pestana; citasPaciente(); });
  $('#vacio-agendar')?.addEventListener('click', () => irA('agendar'));
  enlazarAccionesCita(contenido, r.citas, citasPaciente);
}

async function citasRecepcion() {
  cabecera('Agenda de citas', botonAgendar());
  const F = E.citas;
  if (!E.pacientes.length) E.pacientes = (await api('pacientes', '')).pacientes || [];
  const contenido = $('#contenido');
  contenido.innerHTML = `
    <div class="tarjeta">
      <div class="filtros">
        <label class="campo"><span class="campo__etiqueta">Día</span><input type="date" class="entrada" id="f-fecha" value="${esc(F.fecha)}"></label>
        <label class="campo"><span class="campo__etiqueta">Dentista</span><select class="entrada" id="f-dentista"><option value="">Todos</option>${E.dentistas.map((d) => `<option value="${d.id}" ${F.dentista == d.id ? 'selected' : ''}>${esc(d.nombre)}</option>`).join('')}</select></label>
        <label class="campo campo--ancho"><span class="campo__etiqueta">Paciente</span><select class="entrada" id="f-paciente"><option value="">Todos</option>${E.pacientes.map((p) => `<option value="${p.id_paciente}" ${F.paciente == p.id_paciente ? 'selected' : ''}>${esc(p.nombre)} ${esc(p.apellidos)}</option>`).join('')}</select></label>
        <div class="fila" style="height:42px;align-self:flex-end;gap:6px">
          <button class="boton boton--chico" id="f-hoy">Hoy</button>
          <button class="boton boton--chico" id="f-manana">Mañana</button>
          <button class="boton boton--chico boton--fantasma" id="f-limpiar">Limpiar</button>
        </div>
        <div class="filtros__fin"><label class="interruptor"><input type="checkbox" id="f-canceladas" ${F.canceladas ? 'checked' : ''}><i></i>Mostrar canceladas</label></div>
      </div>
      <div id="tabla-citas"><div class="cargando-bloque"></div></div>
    </div>`;
  const recargar = () => cargarTablaCitas();
  $('#f-fecha').onchange = (e) => { F.fecha = e.target.value; recargar(); };
  $('#f-dentista').onchange = (e) => { F.dentista = e.target.value; recargar(); };
  $('#f-paciente').onchange = (e) => { F.paciente = e.target.value; recargar(); };
  $('#f-canceladas').onchange = (e) => { F.canceladas = e.target.checked; recargar(); };
  $('#f-hoy').onclick = () => { F.fecha = E.hoy; $('#f-fecha').value = F.fecha; recargar(); };
  $('#f-manana').onclick = () => { F.fecha = sumarDias(E.hoy, 1); $('#f-fecha').value = F.fecha; recargar(); };
  $('#f-limpiar').onclick = () => { Object.assign(F, { fecha: '', dentista: '', paciente: '' }); citasRecepcion(); };
  recargar();
}

async function cargarTablaCitas() {
  const F = E.citas;
  const r = await api('citas', { fecha: F.fecha, dentista: F.dentista, paciente: F.paciente });
  const caja = $('#tabla-citas');
  if (!caja) return;
  if (!r.exito) { caja.innerHTML = vacio('alerta', 'Revise los filtros', esc(r.mensaje.replace(/^Error:\s*/, ''))); return; }
  const citas = r.citas.filter((c) => F.canceladas || c.estatus !== 'Cancelada');
  if (!citas.length) { caja.innerHTML = vacio('calendario', 'No hay citas con estos filtros', 'Pruebe con otro día, dentista o paciente, o registre una cita nueva.'); return; }
  caja.innerHTML = `
    <table class="tabla">
      <thead><tr><th>Folio</th><th>Fecha y hora</th><th>Paciente</th><th>Dentista</th><th>Servicio</th><th>Estatus</th><th style="text-align:right">Acciones</th></tr></thead>
      <tbody>${citas.map((c) => {
        const editable = activa(c) && c.fecha >= E.hoy;
        return `<tr class="${c.estatus === 'Cancelada' ? 'cancelada' : ''}">
          <td><span class="folio">#${c.id_cita}</span></td>
          <td><strong>${esc(c.hora)}</strong> <span class="tenue">· ${esc(diaCorto(c.fecha))} ${aFecha(c.fecha).getDate()} ${esc(mesCorto(c.fecha))}</span></td>
          <td><div class="persona"><span class="avatar avatar--chico">${esc(iniciales(c.paciente))}</span><div>${esc(c.paciente)}${c.motivo ? `<small>${esc(c.motivo)}</small>` : ''}</div></div></td>
          <td>${esc(c.dentista)}</td>
          <td class="tenue">${esc(c.servicio)}</td>
          <td><span class="insignia insignia--${esc(c.estatus)}">${esc(c.estatus)}</span></td>
          <td><div class="acciones">
            ${editable ? `<button class="icono-boton" title="Modificar" data-modificar="${c.id_cita}">${icono('editar')}</button>
            <button class="icono-boton" title="Cancelar" data-cancelar="${c.id_cita}">${icono('cancelar')}</button>` : ''}
            <button class="icono-boton icono-boton--peligro" title="Eliminar definitivamente" data-eliminar="${c.id_cita}">${icono('basura')}</button>
          </div></td></tr>`;
      }).join('')}</tbody>
    </table>
    <div class="pie-tabla"><span>${citas.length} cita${citas.length === 1 ? '' : 's'}</span><span>${citas.filter(activa).length} activas</span></div>`;
  enlazarAccionesCita(caja, citas, cargarTablaCitas);
}

function lineaDeTiempo(citas, fecha) {
  const porHora = Object.fromEntries(citas.map((c) => [c.hora, c]));
  const ahora = new Date().toTimeString().slice(0, 5);
  return `<div class="linea-tiempo">${E.horarios.map((h, i) => {
    const c = porHora[h];
    const siguiente = E.horarios[i + 1] || '24:00';
    const esAhora = fecha === E.hoy && ahora >= h && ahora < siguiente;
    return `<div class="franja ${esAhora ? 'ahora' : ''}"><div class="franja__hora">${h}</div><div class="franja__ranura">${c
      ? `<div class="franja__cita ${c.estatus === 'Reprogramada' ? 'reprogramada' : ''}"><span class="avatar avatar--chico">${esc(iniciales(c.paciente))}</span>
          <div><strong>${esc(c.paciente)}</strong><small>${esc(c.servicio)}${c.motivo ? ' · ' + esc(c.motivo) : ''}</small></div>
          <span class="insignia insignia--${esc(c.estatus)}">${esc(c.estatus)}</span></div>`
      : `<div class="franja__libre">Libre</div>`}</div></div>`;
  }).join('')}</div>`;
}

async function citasDentista() {
  const fecha = E.agendaFecha || E.hoy;
  cabecera('Mi agenda', `
    <div class="navegador-dia">
      <button class="icono-boton" id="dia-anterior" aria-label="Día anterior" style="border:1px solid var(--linea);background:#fff">${icono('izquierda')}</button>
      <div class="navegador-dia__fecha">${esc(fechaCompleta(fecha))}</div>
      <button class="icono-boton" id="dia-siguiente" aria-label="Día siguiente" style="border:1px solid var(--linea);background:#fff">${icono('derecha')}</button>
      <button class="boton boton--chico" id="dia-hoy" ${fecha === E.hoy ? 'disabled' : ''}>Hoy</button>
    </div>`, 'Consultorio');
  $('#dia-anterior').onclick = () => { E.agendaFecha = sumarDias(fecha, -1); citasDentista(); };
  $('#dia-siguiente').onclick = () => { E.agendaFecha = sumarDias(fecha, 1); citasDentista(); };
  $('#dia-hoy').onclick = () => { E.agendaFecha = E.hoy; citasDentista(); };
  const contenido = $('#contenido');
  const r = await api('citas', { fecha });
  if (!r.exito) { avisar(r.mensaje); return; }
  contenido.innerHTML = `<div class="tarjeta">
    <div class="tarjeta__cabecera"><div><h3>${r.citas.length ? `${r.citas.length} paciente${r.citas.length === 1 ? '' : 's'} agendado${r.citas.length === 1 ? '' : 's'}` : 'Día sin citas'}</h3>
      <p>${r.citas.length ? `Primera cita a las ${esc(r.citas[0].hora)} h` : 'Todos los horarios están libres.'}</p></div></div>
    ${lineaDeTiempo(r.citas, fecha)}</div>`;
}

/* --- Modificar, cancelar y eliminar ------------------------------------------------------ */
async function modalModificar(cita, alTerminar) {
  const esRecepcion = E.sesion.rol === 'recepcionista';
  const estado = { dentista: cita.id_odontologo, fecha: cita.fecha, hora: cita.hora };
  abrirModal(`
    <div class="modal__cabecera">
      <div class="modal__icono">${icono('editar')}</div>
      <div><h3>Modificar cita #${cita.id_cita}</h3><p>${esc(cita.paciente)} · ${esc(cita.servicio)}</p></div>
      <button class="icono-boton" data-cerrar aria-label="Cerrar">${icono('cerrar')}</button>
    </div>
    <div class="modal__cuerpo">
      <div class="fila-campos">
        ${esRecepcion ? `<label class="campo"><span class="campo__etiqueta">Dentista</span><select class="entrada" id="m-dentista">${E.dentistas.map((d) => `<option value="${d.id}" ${d.id === cita.id_odontologo ? 'selected' : ''}>${esc(d.nombre)}</option>`).join('')}</select></label>`
          : `<div class="campo"><span class="campo__etiqueta">Dentista</span><div class="entrada" style="display:flex;align-items:center;background:var(--superficie-2)">${esc(cita.dentista)}</div></div>`}
        <label class="campo"><span class="campo__etiqueta">Fecha</span><input type="date" class="entrada" id="m-fecha" min="${E.hoy}" value="${cita.fecha}"></label>
      </div>
      <div class="campo"><span class="campo__etiqueta">Horario</span><div id="m-horarios"><div class="cargando-bloque" style="padding:16px"></div></div></div>
      <label class="campo"><span class="campo__etiqueta">Servicio</span><select class="entrada" id="m-servicio">${E.servicios.map((s) => `<option value="${s.id_servicio}" ${s.id_servicio === cita.id_servicio ? 'selected' : ''}>${esc(s.nombre)} · ${s.duracion_min} min</option>`).join('')}</select></label>
      <label class="campo"><span class="campo__etiqueta">Motivo <small>opcional</small></span><input class="entrada" id="m-motivo" value="${esc(cita.motivo || '')}"></label>
      <div class="mensaje-en-linea" id="m-error">${icono('error')}<span></span></div>
    </div>
    <div class="modal__pie"><button class="boton" data-cerrar>Cerrar</button><button class="boton boton--primario" id="m-guardar">${icono('check')}Guardar cambios</button></div>`, { ancho: true });
  $$('[data-cerrar]').forEach((b) => b.onclick = cerrarModal);

  const pintarHorarios = async () => {
    const caja = $('#m-horarios');
    caja.innerHTML = '<div class="cargando-bloque" style="padding:16px"></div>';
    const r = await api('disponibilidad', estado.dentista, estado.fecha, cita.id_cita);
    if (!$('#m-horarios')) return;
    if (!r.exito) { caja.innerHTML = `<div class="campo__ayuda" style="color:var(--error)">${esc(r.mensaje.replace(/^Error:\s*/, ''))}</div>`; return; }
    const libres = new Set(r.libres);
    if (!libres.has(estado.hora)) estado.hora = null;
    caja.innerHTML = `<div class="horarios__lista">${E.horarios.map((h) => `<button class="horario ${estado.hora === h ? 'elegido' : ''}" data-mhora="${h}" ${libres.has(h) ? '' : 'disabled'}>${h}</button>`).join('')}</div>`;
    $$('[data-mhora]').forEach((b) => b.onclick = () => { estado.hora = b.dataset.mhora; $$('[data-mhora]').forEach((x) => x.classList.toggle('elegido', x === b)); });
  };
  if (esRecepcion) $('#m-dentista').onchange = (e) => { estado.dentista = Number(e.target.value); pintarHorarios(); };
  $('#m-fecha').onchange = (e) => { estado.fecha = e.target.value; pintarHorarios(); };
  pintarHorarios();

  $('#m-guardar').onclick = async (e) => {
    const cambios = { fecha: estado.fecha, hora: estado.hora || '', servicio: $('#m-servicio').value, motivo: $('#m-motivo').value };
    if (esRecepcion) cambios.dentista = estado.dentista;
    const r = await conCarga(e.currentTarget, () => api('modificar_cita', cita.id_cita, cambios));
    if (!r.exito) {
      const caja = $('#m-error');
      caja.classList.remove('visible'); void caja.offsetWidth;
      caja.querySelector('span').textContent = r.mensaje.replace(/^Error:\s*/, '');
      caja.classList.add('visible');
      return;
    }
    cerrarModal(); avisar(r.mensaje); alTerminar?.();
  };
}

async function cancelarCita(cita, alTerminar) {
  const ok = await confirmar({
    titulo: '¿Cancelar esta cita?',
    texto: `${esc(cita.servicio)} con ${esc(cita.dentista)}, <span>${esc(fechaLarga(cita.fecha))}</span> a las ${esc(cita.hora)} h. El horario quedará libre y la cita seguirá en el historial.`,
    boton: 'Sí, cancelar cita', peligro: true, iconoNombre: 'cancelar',
  });
  if (!ok) return;
  const r = await api('cancelar_cita', cita.id_cita);
  avisar(r.mensaje);
  if (r.exito) alTerminar?.();
}

async function eliminarCita(cita, alTerminar) {
  const ok = await confirmar({
    titulo: 'Eliminar definitivamente',
    texto: `Se borrará la cita #${cita.id_cita} de ${esc(cita.paciente)} (${esc(cita.fecha)} · ${esc(cita.hora)} h). <strong>Esta acción no se puede deshacer.</strong> Si solo quiere liberar el horario, mejor cancélela.`,
    boton: 'Eliminar cita', peligro: true, iconoNombre: 'basura',
  });
  if (!ok) return;
  const r = await api('eliminar_cita', cita.id_cita);
  avisar(r.mensaje);
  if (r.exito) alTerminar?.();
}

/* ==========================================================================
   Pacientes (recepción)
   ========================================================================== */
let temporizadorBusqueda = null;
async function vistaPacientes() {
  cabecera('Pacientes', `<button class="boton boton--primario" id="alta-paciente">${icono('mas')}Nuevo paciente</button>`);
  $('#alta-paciente').onclick = () => modalPaciente(() => vistaPacientes());
  $('#contenido').innerHTML = `
    <div class="tarjeta">
      <div class="filtros">
        <label class="campo campo--ancho" style="width:360px"><span class="campo__etiqueta">Buscar</span>
          <div class="entrada-con-icono">${icono('buscar')}<input class="entrada" id="buscar" placeholder="Nombre, teléfono o usuario"></div></label>
        <div class="filtros__fin campo__ayuda">Los pacientes sin acceso pueden atenderse por teléfono o en recepción.</div>
      </div>
      <div id="tabla-pacientes"><div class="cargando-bloque"></div></div>
    </div>`;
  $('#buscar').oninput = (e) => { clearTimeout(temporizadorBusqueda); temporizadorBusqueda = setTimeout(() => cargarPacientes(e.target.value), 180); };
  cargarPacientes('');
}

async function cargarPacientes(busqueda) {
  const r = await api('pacientes', busqueda);
  if (!busqueda) E.pacientes = r.pacientes || [];
  const caja = $('#tabla-pacientes');
  if (!caja) return;
  if (!r.exito) { avisar(r.mensaje); return; }
  if (!r.pacientes.length) { caja.innerHTML = vacio('pacientes', busqueda ? 'Sin coincidencias' : 'Aún no hay pacientes', busqueda ? 'Revise la ortografía o busque por teléfono.' : 'Registre al primer paciente con el botón “Nuevo paciente”.'); return; }
  caja.innerHTML = `
    <table class="tabla">
      <thead><tr><th>Paciente</th><th>Teléfono</th><th>Expediente</th><th>Acceso al sistema</th><th style="text-align:right">Acciones</th></tr></thead>
      <tbody>${r.pacientes.map((p) => `<tr>
        <td><div class="persona"><span class="avatar avatar--chico">${esc(p.iniciales)}</span><div><strong>${esc(p.nombre)} ${esc(p.apellidos)}</strong><small>${esc(p.correo || 'Sin correo')}</small></div></div></td>
        <td>${esc(p.telefono)}</td>
        <td><span class="folio">#${p.id_paciente}</span></td>
        <td>${p.nombre_usuario ? `<span class="insignia insignia--Programada">${esc(p.nombre_usuario)}</span>` : '<span class="insignia insignia--Reprogramada">Sin acceso</span>'}</td>
        <td><div class="acciones">
          <button class="boton boton--chico boton--suave" data-agendar="${p.id_paciente}">${icono('agendar')}Agendar</button>
          <button class="icono-boton" title="${p.nombre_usuario ? 'Restablecer contraseña' : 'Crear acceso'}" data-acceso="${p.id_paciente}">${icono('llave')}</button>
        </div></td></tr>`).join('')}</tbody>
    </table>
    <div class="pie-tabla"><span>${r.pacientes.length} paciente${r.pacientes.length === 1 ? '' : 's'}</span><span>${r.pacientes.filter((p) => !p.nombre_usuario).length} sin acceso</span></div>`;
  $$('[data-agendar]', caja).forEach((b) => b.onclick = () => { E.agendar = agendarNuevo(r.pacientes.find((p) => p.id_paciente == b.dataset.agendar)); irA('agendar'); });
  $$('[data-acceso]', caja).forEach((b) => b.onclick = () => modalAcceso(r.pacientes.find((p) => p.id_paciente == b.dataset.acceso)));
}

function claveSugerida() {
  const palabras = ['Sonrisa', 'Molar', 'Esmalte', 'Brillo', 'Encia', 'Perla', 'Canino'];
  return palabras[Math.floor(Math.random() * palabras.length)] + '-' + String(Math.floor(1000 + Math.random() * 9000));
}

function modalPaciente(alGuardar) {
  abrirModal(`
    <div class="modal__cabecera">
      <div class="modal__icono">${icono('pacientes')}</div>
      <div><h3>Registrar paciente nuevo</h3><p>Para clientes que llaman o acuden por primera vez.</p></div>
      <button class="icono-boton" data-cerrar aria-label="Cerrar">${icono('cerrar')}</button>
    </div>
    <form class="modal__cuerpo" id="form-paciente" novalidate>
      <div class="fila-campos">
        <label class="campo"><span class="campo__etiqueta">Nombre(s)</span><input class="entrada" name="nombre"></label>
        <label class="campo"><span class="campo__etiqueta">Apellidos</span><input class="entrada" name="apellidos"></label>
      </div>
      <div class="fila-campos">
        <label class="campo"><span class="campo__etiqueta">Teléfono</span><input class="entrada" name="telefono" placeholder="10 dígitos" inputmode="tel"></label>
        <label class="campo"><span class="campo__etiqueta">Nacimiento <small>opcional</small></span><input class="entrada" type="date" name="fecha_nacimiento" max="${E.hoy}"></label>
      </div>
      <label class="campo"><span class="campo__etiqueta">Correo <small>opcional</small></span><input class="entrada" name="correo" type="email"></label>
      <label class="interruptor" style="height:auto"><input type="checkbox" id="con-acceso"><i></i>Crear también su acceso para agendar en línea</label>
      <div class="fila-campos oculto" id="campos-acceso">
        <label class="campo"><span class="campo__etiqueta">Usuario</span><input class="entrada" name="usuario" placeholder="p. ej. hugo.mena"></label>
        <label class="campo"><span class="campo__etiqueta fila entre">Contraseña <button type="button" class="boton boton--chico boton--fantasma" id="generar" style="height:20px;padding:0 4px">${icono('dado')}Generar</button></span><input class="entrada" name="contrasena" type="text"></label>
      </div>
      <div class="mensaje-en-linea" id="p-error">${icono('error')}<span></span></div>
    </form>
    <div class="modal__pie"><button class="boton" data-cerrar>Cancelar</button><button class="boton boton--primario" id="p-guardar">${icono('check')}Registrar paciente</button></div>`, { ancho: true });
  $$('[data-cerrar]').forEach((b) => b.onclick = cerrarModal);
  const formulario = $('#form-paciente');
  $('#con-acceso').onchange = (e) => {
    $('#campos-acceso').classList.toggle('oculto', !e.target.checked);
    if (e.target.checked && !formulario.usuario.value) {
      const n = formulario.nombre.value.trim().split(' ')[0], a = formulario.apellidos.value.trim().split(' ')[0];
      if (n && a) formulario.usuario.value = `${n}.${a}`.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9._-]/g, '');
      formulario.contrasena.value = claveSugerida();
    }
  };
  $('#generar').onclick = () => { formulario.contrasena.value = claveSugerida(); };
  const guardar = async (boton) => {
    const datos = Object.fromEntries(new FormData(formulario));
    if (!$('#con-acceso').checked) { datos.usuario = ''; datos.contrasena = ''; }
    const r = await conCarga(boton, () => api('registrar_paciente', datos));
    if (!r.exito) {
      const caja = $('#p-error');
      caja.classList.remove('visible'); void caja.offsetWidth;
      caja.querySelector('span').textContent = r.mensaje.replace(/^Error:\s*/, '');
      caja.classList.add('visible');
      return;
    }
    E.pacientes = (await api('pacientes', '')).pacientes || [];
    const nuevo = E.pacientes.find((p) => p.id_paciente === r.id_paciente);
    cerrarModal();
    avisar(r.mensaje + (datos.usuario ? ` Contraseña: ${datos.contrasena}` : ''));
    alGuardar?.(nuevo);
  };
  formulario.onsubmit = (e) => { e.preventDefault(); guardar($('#p-guardar')); };
  $('#p-guardar').onclick = (e) => guardar(e.currentTarget);
}

function modalAcceso(paciente) {
  const tiene = !!paciente.nombre_usuario;
  abrirModal(`
    <div class="modal__cabecera">
      <div class="modal__icono">${icono('llave')}</div>
      <div><h3>${tiene ? 'Restablecer contraseña' : 'Crear acceso'}</h3><p>${esc(paciente.nombre)} ${esc(paciente.apellidos)} · ${esc(paciente.telefono)}</p></div>
      <button class="icono-boton" data-cerrar aria-label="Cerrar">${icono('cerrar')}</button>
    </div>
    <div class="modal__cuerpo">
      <label class="campo"><span class="campo__etiqueta">Usuario</span><input class="entrada" id="a-usuario" value="${esc(paciente.nombre_usuario || '')}" ${tiene ? 'disabled style="background:var(--superficie-2)"' : 'placeholder="p. ej. ana.perez"'}></label>
      <label class="campo"><span class="campo__etiqueta fila entre">${tiene ? 'Nueva contraseña' : 'Contraseña'} <button type="button" class="boton boton--chico boton--fantasma" id="a-generar" style="height:20px;padding:0 4px">${icono('dado')}Generar</button></span>
        <input class="entrada" id="a-clave" value="${claveSugerida()}"><span class="campo__ayuda">Entréguela al paciente; podrá usarla de inmediato.</span></label>
      <div class="mensaje-en-linea" id="a-error">${icono('error')}<span></span></div>
    </div>
    <div class="modal__pie"><button class="boton" data-cerrar>Cancelar</button><button class="boton boton--primario" id="a-guardar">${icono('check')}${tiene ? 'Restablecer' : 'Crear acceso'}</button></div>`);
  $$('[data-cerrar]').forEach((b) => b.onclick = cerrarModal);
  $('#a-generar').onclick = () => { $('#a-clave').value = claveSugerida(); };
  $('#a-guardar').onclick = async (e) => {
    const clave = $('#a-clave').value;
    const r = await conCarga(e.currentTarget, () => api('gestionar_acceso', paciente.id_paciente, $('#a-usuario').value, clave));
    if (!r.exito) {
      const caja = $('#a-error');
      caja.classList.remove('visible'); void caja.offsetWidth;
      caja.querySelector('span').textContent = r.mensaje.replace(/^Error:\s*/, '');
      caja.classList.add('visible');
      return;
    }
    cerrarModal(); avisar(`${r.mensaje} Contraseña: ${clave}`);
    if (E.vista === 'pacientes') cargarPacientes($('#buscar')?.value || '');
  };
}

/* ==========================================================================
   Servicios (RF-08)
   ========================================================================== */
async function vistaServicios() {
  cabecera('Servicios de la clínica', botonAgendar(), 'Catálogo');
  const r = await api('servicios');
  E.servicios = r.servicios || E.servicios;
  $('#contenido').innerHTML = r.servicios?.length ? `
    <div class="rejilla rejilla--3">${r.servicios.map((s) => `
      <article class="tarjeta servicio">
        <div class="servicio__icono">${icono(iconoServicio(s.nombre))}</div>
        <div><h3>${esc(s.nombre)}</h3></div>
        <p>${esc(s.descripcion || 'Consulte los detalles en recepción.')}</p>
        <div class="servicio__pie">
          <span class="insignia insignia--neutra">${icono('reloj', '')}${s.duracion_min} min</span>
          <span class="servicio__precio">${dinero(s.precio)}<small>MXN</small></span>
        </div>
      </article>`).join('')}</div>`
    : `<div class="tarjeta">${vacio('servicios', 'Catálogo vacío', esc((r.mensaje || '').replace(/^(Aviso|Error):\s*/, '')))}</div>`;
  $$('#contenido .insignia svg').forEach((s) => { s.style.width = '13px'; s.style.height = '13px'; });
}

/* ==========================================================================
   Arranque
   ========================================================================== */
(async function iniciar() {
  MODO = await esperarPuente();
  const estado = await api('estado');
  if (!estado.exito) {
    $('#app').innerHTML = `<div class="arranque" style="color:#fff;text-align:center;padding:24px"><div><div class="arranque__logo" style="margin:0 auto 18px;animation:none"></div><p>${esc(estado.mensaje)}</p></div></div>`;
    return;
  }
  Object.assign(E, { demo: estado.demo, horarios: estado.horarios, hoy: estado.hoy });
  if (estado.sesion) { E.sesion = estado.sesion; await arrancarSesion(); }
  else renderAcceso();
})();
