import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import hashlib
import requests
import time
import uuid
import difflib
from pathlib import Path
from datetime import date, datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor

COL_TZ = timezone(timedelta(hours=-5))
def fecha_hoy():
    return datetime.now(COL_TZ).strftime("%Y-%m-%d")
def ahora():
    return datetime.now(COL_TZ).strftime("%I:%M %p").lstrip("0")

# ══════════════════════════════════════════════════════════════════════════════
# ÍCONOS PARA TEXTOS HTML (reemplazan emojis en alertas, recibos, tarjetas, etc.)
# ══════════════════════════════════════════════════════════════════════════════
def _svg(paths, size=14):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" '
            f'fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" '
            f'style="display:inline-block;vertical-align:-2px;margin-right:3px">{paths}</svg>')

def _dot(color, size=10):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" '
            f'style="display:inline-block;vertical-align:-1px;margin-right:4px"><circle cx="12" cy="12" r="10" fill="{color}"/></svg>')

ICO_WARN     = _svg('<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>')
ICO_CHECK    = _svg('<polyline points="20 6 9 17 4 12"/>')
ICO_CARD     = _svg('<rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>')
ICO_DOLLAR   = _svg('<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>')
ICO_REFRESH  = _svg('<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>')
ICO_RECEIPT  = _svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>')
ICO_LOCK     = _svg('<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>')
ICO_GIFT     = _svg('<polyline points="20 12 20 22 4 22 4 12"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="22" x2="12" y2="7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>')
ICO_USER     = _svg('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>')
ICO_CART     = _svg('<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>')
ICO_PACKAGE  = _svg('<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>')
ICO_TROPHY   = _svg('<circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>')
ICO_CALENDAR = _svg('<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>')
ICO_LAYERS   = _svg('<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>')
ICO_PRINTER  = _svg('<polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>')
ICO_CLIPBOARD = _svg('<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>')
ICO_NOTE     = _svg('<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>')
ICO_TRUCK    = _svg('<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>')
ICO_FACTORY  = _svg('<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>')
ICO_BULB     = _svg('<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z"/>')
ICO_FLASK    = _svg('<path d="M9 2v6.5L4.5 17a2 2 0 0 0 1.8 3h11.4a2 2 0 0 0 1.8-3L15 8.5V2"/><line x1="9" y1="2" x2="15" y2="2"/>')
ICO_DOT_RED    = _dot("#E53935")
ICO_DOT_YELLOW = _dot("#FB8C00")
ICO_DOT_GREEN  = _dot("#43A047")

st.set_page_config(
    page_title="Productos La Delicia",
    page_icon="Logo.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Meta tags PWA — permiten instalar la app sin barra de navegador
st.markdown("""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="La Delicia">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#1565C0">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SUPABASE
# ══════════════════════════════════════════════════════════════════════════════
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def _sb_error(operacion, tabla, detalle):
    st.error(f"⚠️ No se pudo {operacion} en '{tabla}': {detalle}. Revisa tu conexión e intenta de nuevo.")

def sb_get(tabla, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{tabla}"
    if params:
        url += f"?{params}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.ok:
            return r.json()
        _sb_error("leer datos", tabla, f"{r.status_code} — {r.text[:200]}")
        return []
    except requests.RequestException as e:
        _sb_error("leer datos", tabla, str(e))
        return []

def sb_post(tabla, data):
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{tabla}", headers=HEADERS, json=data, timeout=10)
        if r.ok:
            return True
        _sb_error("guardar", tabla, f"{r.status_code} — {r.text[:200]}")
        return False
    except requests.RequestException as e:
        _sb_error("guardar", tabla, str(e))
        return False

def sb_patch(tabla, filtro, data):
    try:
        r = requests.patch(f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}", headers=HEADERS, json=data, timeout=10)
        if r.ok:
            return True
        _sb_error("actualizar", tabla, f"{r.status_code} — {r.text[:200]}")
        return False
    except requests.RequestException as e:
        _sb_error("actualizar", tabla, str(e))
        return False

def sb_delete(tabla, filtro):
    try:
        r = requests.delete(f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}", headers=HEADERS, timeout=10)
        if r.ok:
            return True
        _sb_error("eliminar", tabla, f"{r.status_code} — {r.text[:200]}")
        return False
    except requests.RequestException as e:
        _sb_error("eliminar", tabla, str(e))
        return False


# ══════════════════════════════════════════════════════════════════════════════
# DATOS MAESTROS
# ══════════════════════════════════════════════════════════════════════════════
PRODUCTOS = {
    "BBQ": 9000, "Limón": 9000, "Carita Feliz": 9000, "Pollo": 9000,
    "Parrillada": 9000, "Chorizo Limón": 9000, "Mayonesa": 9000,
    "Queso": 9000, "Picante": 9000, "Almuerzo Pollo": 9000,
    "Almuerzo Limón": 9000, "Almuerzo Picante": 9000,
    "Mega": 1700, "Megaton": 5000,
    "Fósforo 70g (x10)": 14500, "Fósforo 140g": 3500,
    "Fósforo 250g": 7000, "Fósforo 500g": 14000,
}

# Precios rápidos por sabor — aparecen como botones en el carrito
PRECIOS_RAPIDOS = {
    "BBQ":           [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Limón":         [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Carita Feliz":  [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Pollo":         [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Parrillada":    [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Chorizo Limón": [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Mayonesa":      [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Queso":         [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Picante":       [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Almuerzo Pollo":   [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Almuerzo Limón":   [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Almuerzo Picante": [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Fósforo 70g (x10)": [("Mayorista", 14500), ("Minorista", 15000)],
    "Fósforo 140g":      [("Mayorista", 3500),  ("Minorista", 4000)],
    "Fósforo 500g":      [("Mayorista", 14500), ("Minorista", 15000)],
    "Mega":    [("$1.600", 1600), ("$1.700", 1700), ("$1.800", 1800)],
    "Megaton": [("$5.000", 5000), ("$5.500", 5500)],
}
SABORES_LISTA = list(PRODUCTOS.keys())
EMPLEADOS = ["Andrea", "Sofía", "Javier", "Edison", "Otro"]
VENDEDORES_FABRICA = ["Sofía", "Andrea"]
STOCK_MINIMO = 10  # alerta cuando un sabor tenga menos de esta cantidad

def fmt(n):
    return f"${int(n):,.0f}".replace(",", ".")

def tabla_facturas_html(df_canal):
    """Genera tabla HTML estilo factura electrónica: Fecha, N° comprobante, Vendedor, Cliente, Total, Estado."""
    filas = []
    for fid in df_canal["factura_id"].unique():
        if not fid:
            continue
        grupo = df_canal[df_canal["factura_id"]==fid]
        filas.append({
            "fecha":    grupo["fecha"].iloc[0],
            "factura":  fid,
            "vendedor": grupo["vendedor"].iloc[0],
            "cliente":  grupo["cliente"].iloc[0],
            "total":    grupo["total"].sum(),
        })
    if not filas:
        return None
    filas.sort(key=lambda r: (r["fecha"], r["factura"]), reverse=True)

    filas_html = "".join(f"""
        <tr>
            <td>{r['fecha']}</td>
            <td class="num-comp">FV-{r['factura']}</td>
            <td>{r['vendedor']}</td>
            <td>{r['cliente']}</td>
            <td class="total-col">{fmt(r['total'])}</td>
            <td class="estado-ok">{ICO_CHECK} Aprobado</td>
        </tr>""" for r in filas)

    return f"""
    <div class="tabla-fact-wrap">
        <table class="tabla-fact">
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>N° Comprobante</th>
                    <th>Vendedor</th>
                    <th>Cliente</th>
                    <th>Total</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>{filas_html}</tbody>
        </table>
    </div>
    """

def mostrar_facturas_seleccionables(df_canal, key_prefix):
    """Tabla con facturas; al seleccionar una fila se abre el recibo en una vista nueva."""
    filas = []
    for fid in df_canal["factura_id"].unique():
        if not fid:
            continue
        grupo = df_canal[df_canal["factura_id"]==fid]
        es_credito = bool(grupo["es_credito"].any()) if "es_credito" in grupo.columns else False
        estado = "📋 Crédito" if es_credito else "✓ Aprobado"
        filas.append({
            "Fecha": grupo["fecha"].iloc[0],
            "N° Comprobante": f"FV-{fid}",
            "Vendedor": grupo["vendedor"].iloc[0],
            "Cliente": grupo["cliente"].iloc[0],
            "Total": fmt(grupo[grupo["total"] > 0]["total"].sum()),
            "Estado": estado,
            "_fid": fid,
        })
    if not filas:
        return
    filas.sort(key=lambda r: (r["Fecha"], r["_fid"]), reverse=True)
    df_tabla = pd.DataFrame(filas)

    evento = st.dataframe(
        df_tabla.drop(columns=["_fid"]),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"tabla_sel_{key_prefix}"
    )

    if evento.selection and evento.selection.rows:
        idx = evento.selection.rows[0]
        fid_sel = df_tabla.iloc[idx]["_fid"]
        # Cargar TODOS los registros de esta factura incluyendo cambios
        todos = sb_get("ventas", f"select=*&factura_id=eq.{requests.utils.quote(fid_sel)}")
        st.session_state.recibo_a_mostrar = fid_sel
        st.session_state.recibo_canal_df = todos if todos else []
        st.session_state.vista_anterior = st.session_state.vista  # guardar de dónde venimos
        st.session_state.vista = "recibo"
        st.rerun()

def _colapsar_repetidas(s):
    """Reduce letras repetidas seguidas: 'bettos' -> 'betos'."""
    out = []
    prev = None
    for ch in s:
        if ch != prev:
            out.append(ch)
        prev = ch
    return "".join(out)

def _coincide_nombre(busqueda, nombre):
    """Compara nombres tolerando errores de tipeo (letras dobles, acentos, etc)."""
    b = _colapsar_repetidas(busqueda.strip().lower())
    n = nombre.strip().lower()
    n_col = _colapsar_repetidas(n)
    if not b:
        return True
    if b in n or b in n_col:
        return True
    palabras = n.split() + [n]
    return any(difflib.SequenceMatcher(None, b, _colapsar_repetidas(p)).ratio() >= 0.75 for p in palabras)

def _registrar_credito_manual(fecha, cliente, canal, vendedor, total, abono):
    """Guarda una deuda que ya existía antes de usar la app (sin sabor/cantidad, sin tocar inventario)."""
    estado = "pagado" if abono >= total else "pendiente"
    sb_post("creditos", {
        "fecha": fecha, "hora": ahora(), "cliente": cliente, "canal": canal,
        "vendedor": vendedor, "total": total, "pagado": abono, "estado": estado
    })

def mostrar_creditos_pendientes(canal):
    """Muestra facturas con saldo pendiente y permite registrar abonos."""
    with st.expander("➕ Cargar crédito antiguo"):
        st.caption("Para deudas que ya existían antes de usar la app. Solo el monto — no afecta el inventario.")
        col_f1, col_f2 = st.columns(2)
        fecha_cred = col_f1.date_input("Fecha de la venta", value=datetime.now(COL_TZ).date(), key=f"cred_fecha_{canal}")
        vendedor_cred = col_f2.selectbox("Vendedor", EMPLEADOS, key=f"cred_vendedor_{canal}")
        cliente_cred = st.text_input("Nombre del cliente", key=f"cred_cliente_{canal}", placeholder="Ej: Tienda Don Carlos")
        col_t, col_a = st.columns(2)
        total_cred = col_t.number_input("Total adeudado ($)", min_value=0, step=1000, key=f"cred_total_{canal}")
        abono_cred = col_a.number_input("Abono ya pagado ($)", min_value=0, max_value=int(total_cred), step=1000, key=f"cred_abono_{canal}")
        if st.button("💾 Guardar crédito", key=f"btn_cred_guardar_{canal}"):
            if not cliente_cred.strip():
                st.markdown(f'<div class="alert-low">{ICO_WARN} Escribe el nombre del cliente.</div>', unsafe_allow_html=True)
            elif total_cred <= 0:
                st.markdown(f'<div class="alert-low">{ICO_WARN} Ingresa el monto adeudado.</div>', unsafe_allow_html=True)
            else:
                _registrar_credito_manual(str(fecha_cred), cliente_cred.strip(), canal, vendedor_cred, float(total_cred), float(abono_cred))
                st.markdown(f'<div class="success-toast">{ICO_CHECK} Crédito registrado.</div>', unsafe_allow_html=True)
                time.sleep(0.3)
                st.rerun()

    # Agrupar por factura para no repetir (cada fila es un producto de la factura,
    # por eso el total hay que sumarlo entre todas las filas de la misma factura_id)
    raw = sb_get("ventas", f"select=factura_id,cliente,vendedor,total,abono,saldo&fecha=gte.2024-01-01&canal=eq.{requests.utils.quote(canal)}&saldo=gt.0")
    facturas = {}
    for r in (raw or []):
        fid = r["factura_id"]
        if not fid:
            continue
        if f"V-{fid}" not in facturas:
            facturas[f"V-{fid}"] = {
                "cliente": r["cliente"], "vendedor": r["vendedor"],
                "saldo": float(r["saldo"]), "total": 0.0, "abono": float(r["abono"]),
                "tipo": "venta", "ref": fid, "etiqueta": f"FV-{fid}",
            }
        facturas[f"V-{fid}"]["total"] += float(r["total"])

    # Créditos antiguos cargados manualmente (tabla 'creditos', sin desglose de productos)
    raw_m = sb_get("creditos", f"select=id,cliente,vendedor,total,pagado&canal=eq.{requests.utils.quote(canal)}&estado=eq.pendiente")
    for r in (raw_m or []):
        total_m = float(r["total"])
        pagado_m = float(r["pagado"] or 0)
        facturas[f"M-{r['id']}"] = {
            "cliente": r["cliente"], "vendedor": r["vendedor"],
            "saldo": max(0.0, total_m - pagado_m), "total": total_m, "abono": pagado_m,
            "tipo": "manual", "ref": r["id"], "etiqueta": "Crédito antiguo",
        }

    facturas = {k: d for k, d in facturas.items() if d["saldo"] > 0}
    if not facturas:
        return
    st.markdown(f'<div class="section-label">{ICO_CARD} Créditos pendientes de cobro</div>', unsafe_allow_html=True)
    busqueda = st.text_input("🔍 Buscar por cliente", key=f"buscar_credito_{canal}", placeholder="Ej: Don Carlos")
    if busqueda.strip():
        facturas = {k: d for k, d in facturas.items() if _coincide_nombre(busqueda, d["cliente"])}
        if not facturas:
            st.caption("No hay créditos pendientes para ese cliente.")
    for key, datos in facturas.items():
        saldo = datos["saldo"]
        st.markdown(
            f'<div class="warn-box">'
            f'<b>{datos["cliente"]}</b> · {datos["etiqueta"]}<br>'
            f'Total: {fmt(datos["total"])} · Abonado: {fmt(datos["abono"])} · '
            f'<b>Debe: {fmt(saldo)}</b>'
            f'</div>',
            unsafe_allow_html=True
        )
        col_m, col_b = st.columns([3, 1])
        nuevo_abono = col_m.number_input(
            "Abono ($)", min_value=0, max_value=int(saldo),
            value=int(saldo), step=1000, key=f"abono_pend_{key}"
        )
        if col_b.button("✅ Cobrar", key=f"btn_cobrar_{key}"):
            nuevo_saldo = max(0, saldo - nuevo_abono)
            nuevo_total_abono = datos["abono"] + nuevo_abono
            if datos["tipo"] == "venta":
                sb_patch("ventas", f"factura_id=eq.{datos['ref']}", {
                    "abono": nuevo_total_abono,
                    "saldo": nuevo_saldo
                })
            else:
                estado_nuevo = "pagado" if nuevo_saldo <= 0 else "pendiente"
                sb_patch("creditos", f"id=eq.{datos['ref']}", {
                    "pagado": nuevo_total_abono,
                    "estado": estado_nuevo
                })
            time.sleep(0.3)
            st.rerun()

def _recargar_factura(key_factura, fac):
    """Recarga una factura (fábrica o carro) desde Supabase y actualiza session_state[key_factura]."""
    registros_act = sb_get("ventas", f"select=sabor,cantidad,total&factura_id=eq.{fac['id']}")
    items_act = {}
    precios_act = {}
    for r in (registros_act or []):
        if r["cantidad"] > 0:
            items_act[r["sabor"]] = items_act.get(r["sabor"], 0) + r["cantidad"]
            precios_act[r["sabor"]] = r["total"] // r["cantidad"] if r["cantidad"] else PRODUCTOS[r["sabor"]]
        elif r["cantidad"] < 0:
            s = r["sabor"]
            if s in items_act:
                items_act[s] = max(0, items_act[s] + r["cantidad"])
                if items_act[s] == 0:
                    del items_act[s]
                    if s in precios_act:
                        del precios_act[s]
    total_act = sum(precios_act.get(s, PRODUCTOS[s]) * c for s, c in items_act.items())
    st.session_state[key_factura] = {**fac, "items": items_act, "precios": precios_act, "total": total_act}

def _stock_carro_actual():
    """Bolsas disponibles en el carro ambulante, por sabor: cargado - vendido - devuelto."""
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_cg  = ex.submit(sb_get, "cargues",      "select=sabor,cantidad")
        f_vc  = ex.submit(sb_get, "ventas",        "select=sabor,cantidad&canal=in.(Carro,Cambio,Regalo)")
        f_dev = ex.submit(sb_get, "devoluciones",  "select=sabor,cantidad")
    raw_cg, raw_vc, raw_dev = f_cg.result(), f_vc.result(), f_dev.result()
    stock = {}
    for r in (raw_cg or []):
        stock[r["sabor"]] = stock.get(r["sabor"], 0) + r["cantidad"]
    for r in (raw_vc or []):
        if r.get("cantidad", 0) > 0:
            stock[r["sabor"]] = stock.get(r["sabor"], 0) - r["cantidad"]
    for r in (raw_dev or []):
        stock[r["sabor"]] = stock.get(r["sabor"], 0) - r.get("cantidad", 0)
    return stock

def render_venta_canal(cfg, mostrar_creditos=True):
    """Flujo de venta (carrito, pago, factura, cambios) compartido entre las
    vistas 'Fábrica' y 'Carro'. cfg define lo que cambia entre canales:
    de dónde sale el stock disponible, si la venta descuenta inventario
    central, quién puede vender y qué sabores se ofrecen post-venta."""
    key_carrito = cfg["key_carrito"]
    key_precios = cfg["key_precios"]
    key_factura = cfg["key_factura"]
    canal       = cfg["canal"]
    mutar_stock = cfg["mutar_stock"]

    st.markdown(f'<div class="section-label">Nueva venta {cfg["icono"]}</div>', unsafe_allow_html=True)

    if cfg["vendedores"] is not None:
        vendedor = st.selectbox("Vendedor", cfg["vendedores"], key="venta_vendedor")
    else:
        vendedor = cfg["vendedor_fijo"]
    cliente = st.text_input("Nombre del cliente", placeholder="Ej: Tienda Don Carlos", key="venta_cliente")

    st.markdown('<div class="section-label">Agregar al carrito</div>', unsafe_allow_html=True)
    col_s, col_c = st.columns([2, 1])
    sabor = col_s.selectbox("Sabor", cfg["sabores_venta_fn"](), key="venta_sabor")

    disp_map = cfg["disponible_map_fn"]()
    en_carrito = st.session_state[key_carrito].get(sabor, 0)
    disponible = max(0, disp_map.get(sabor, 0) - en_carrito)

    cant = col_c.number_input("Bolsas", min_value=1, max_value=max(1, disponible), value=1, step=1, key="venta_cant")

    if disponible < cant:
        st.markdown(f'<div class="alert-low">{ICO_WARN} Solo hay {disponible} bolsas disponibles de {sabor}.</div>', unsafe_allow_html=True)

    if sabor in PRECIOS_RAPIDOS:
        opciones_p = [e if e.strip().startswith("$") else f"{e} — {fmt(p)}" for e, p in PRECIOS_RAPIDOS[sabor]]
        precios_p  = [p for _, p in PRECIOS_RAPIDOS[sabor]]
        sel_p = st.radio("Precio", opciones_p, horizontal=True, key=f"venta_precio_radio_{sabor}")
        precio_elegido = precios_p[opciones_p.index(sel_p)]
    else:
        precio_elegido = PRODUCTOS[sabor]

    col_add, col_clr = st.columns(2)
    if col_add.button("➕ Agregar", key="venta_btn_add", disabled=(disponible < cant)):
        st.session_state[key_carrito][sabor] = en_carrito + cant
        st.session_state[key_precios][sabor] = precio_elegido
        st.rerun()
    if col_clr.button("🗑️ Vaciar", key="venta_btn_clr"):
        st.session_state[key_carrito] = {}
        st.session_state[key_precios] = {}
        st.rerun()

    carrito = st.session_state[key_carrito]
    if carrito:
        st.markdown('<div class="section-label">Carrito actual</div>', unsafe_allow_html=True)
        st.caption("Toca cualquier celda para cambiar cantidad o precio.")

        sabores_cart = list(carrito.keys())
        df_cart = pd.DataFrame({
            "Sabor":    sabores_cart,
            "Cantidad": [carrito[s] for s in sabores_cart],
            "Precio":   [st.session_state[key_precios].get(s, PRODUCTOS[s]) for s in sabores_cart],
        })
        df_cart["Subtotal"] = df_cart["Cantidad"] * df_cart["Precio"]

        edited = st.data_editor(
            df_cart,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Sabor":    st.column_config.TextColumn("Sabor", disabled=True),
                "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1),
                "Precio":   st.column_config.NumberColumn("Precio", min_value=100, step=100),
                "Subtotal": st.column_config.NumberColumn("Subtotal", disabled=True),
            },
            key="venta_cart_editor"
        )

        if st.button("💾 Aplicar cambios al carrito", key="venta_btn_save_cart"):
            nuevo, nuevos_p = {}, {}
            for _, row in edited.iterrows():
                if pd.notna(row["Sabor"]) and row["Cantidad"] > 0:
                    nuevo[row["Sabor"]] = nuevo.get(row["Sabor"], 0) + int(row["Cantidad"])
                    nuevos_p[row["Sabor"]] = int(row["Precio"])
            st.session_state[key_carrito] = nuevo
            st.session_state[key_precios] = nuevos_p
            st.rerun()

        sabor_quitar = st.selectbox("Quitar un sabor del carrito", ["— Selecciona —"] + sabores_cart, key="venta_sel_quitar")
        if sabor_quitar != "— Selecciona —" and st.button("✕ Quitar del carrito", key="venta_btn_quitar"):
            del st.session_state[key_carrito][sabor_quitar]
            st.session_state[key_precios].pop(sabor_quitar, None)
            st.rerun()

        total_venta = float((edited["Cantidad"] * edited["Precio"]).sum())

        st.markdown('<div class="section-label">Pago del cliente</div>', unsafe_allow_html=True)
        if st.session_state.get("venta_abono_total_ref") != total_venta:
            st.session_state["venta_abono"] = int(total_venta)
            st.session_state["venta_abono_total_ref"] = total_venta
        abono = st.number_input("Abono del cliente ($)", min_value=0, value=int(total_venta), step=1000, key="venta_abono")
        if abono > 0:
            if abono >= total_venta:
                st.markdown(f'<div class="info-box">{ICO_DOLLAR} Total: <b>{fmt(total_venta)}</b> · Devolver: <b>{fmt(abono - total_venta)}</b></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="warn-box">{ICO_CLIPBOARD} Abono: <b>{fmt(abono)}</b> · Queda debiendo: <b>{fmt(total_venta - abono)}</b></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warn-box">{ICO_CLIPBOARD} Sin abono — queda debiendo: <b>{fmt(total_venta)}</b></div>', unsafe_allow_html=True)

        col_clr2, col_conf = st.columns(2)
        if col_clr2.button("🗑️ Vaciar carrito", key="venta_btn_clr2"):
            st.session_state[key_carrito] = {}
            st.session_state[key_precios] = {}
            st.rerun()

        if col_conf.button("✅ Confirmar venta", key="venta_btn_confirmar"):
            if not cliente.strip():
                st.markdown(f'<div class="alert-low">{ICO_WARN} Escribe el nombre del cliente.</div>', unsafe_allow_html=True)
            else:
                disp_check = cfg["disponible_map_fn"]()
                sin_stock = [s for s, c in carrito.items() if disp_check.get(s, 0) < c]
                if sin_stock:
                    st.markdown(f'<div class="alert-low">{ICO_WARN} Stock insuficiente: <b>{", ".join(sin_stock)}</b>. Ajusta el carrito.</div>', unsafe_allow_html=True)
                else:
                    fid = str(uuid.uuid4())[:8].upper()
                    total_confirmado = 0
                    abono_val = int(st.session_state.get("venta_abono", 0))
                    for s, c in carrito.items():
                        precio_final = st.session_state[key_precios].get(s, PRODUCTOS[s])
                        subtotal = precio_final * c
                        total_confirmado += subtotal
                        sb_post("ventas", {
                            "fecha": fecha_hoy(), "hora": ahora(), "canal": canal,
                            "vendedor": vendedor, "sabor": s, "cantidad": c,
                            "total": subtotal, "cliente": cliente.strip(),
                            "factura_id": fid, "abono": abono_val, "saldo": 0
                        })
                        if mutar_stock:
                            restar_stock(s, c)
                    saldo_final = max(0, total_confirmado - abono_val)
                    sb_patch("ventas", f"factura_id=eq.{fid}", {"abono": abono_val, "saldo": saldo_final})
                    st.session_state[key_factura] = {
                        "id": fid, "cliente": cliente.strip(), "vendedor": vendedor,
                        "items": dict(carrito), "precios": dict(st.session_state[key_precios]),
                        "total": total_confirmado, "billete": abono_val, "saldo": saldo_final,
                    }
                    st.session_state[key_carrito] = {}
                    st.session_state[key_precios] = {}
                    time.sleep(0.3)
                    st.rerun()

    # Opciones post-venta — solo si hay una factura activa en esta sesión
    if st.session_state[key_factura]:
        fac = st.session_state[key_factura]
        vuelto = fac["billete"] - fac["total"] if fac["billete"] >= fac["total"] and fac["billete"] > 0 else 0
        saldo_fac = fac.get("saldo", 0)
        msg = f'{ICO_CHECK} Venta registrada — <b>#{fac["id"]}</b> · {fac["cliente"]} · {fmt(fac["total"])}'
        if vuelto > 0:
            msg += f'<br>{ICO_DOLLAR} Devolver: <b>{fmt(vuelto)}</b>'
        if saldo_fac > 0:
            msg += f'<br>{ICO_CLIPBOARD} Queda debiendo: <b>{fmt(saldo_fac)}</b>'
        st.markdown(f'<div class="success-toast">{msg}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label">¿El cliente quiere algo más?</div>', unsafe_allow_html=True)
        tab_cambio, tab_agregar = st.tabs(["🔁 Cambiar producto", "➕ Agregar producto"])

        with tab_cambio:
            col_a, col_b = st.columns(2)
            sabores_en_fac = list(fac["items"].keys())
            sabor_out = col_a.selectbox("Devuelve", sabores_en_fac, key="venta_cambio_out")
            max_out = fac["items"].get(sabor_out, 1)
            cant_out = col_a.number_input("Cantidad que devuelve", min_value=1, max_value=max_out, value=1, step=1, key="venta_cant_out")

            # Al devolver, ese sabor vuelve a estar disponible — sumarlo temporalmente
            disp_cambio = cfg["disponible_map_fn"]()
            disp_cambio[sabor_out] = disp_cambio.get(sabor_out, 0) + cant_out
            opciones_in = cfg["sabores_post_venta_fn"](disp_cambio)
            sabor_in = col_b.selectbox("Lleva en cambio", opciones_in, key="venta_cambio_in")
            max_in = max(1, int(disp_cambio.get(sabor_in, 0)))
            cant_in = col_b.number_input("Cantidad que lleva", min_value=1, max_value=max_in, value=1, step=1, key="venta_cant_in")

            valor_out = fac["precios"].get(sabor_out, PRODUCTOS[sabor_out]) * cant_out
            valor_in  = fac["precios"].get(sabor_in,  PRODUCTOS[sabor_in])  * cant_in
            diferencia = valor_in - valor_out
            if diferencia > 0:
                st.markdown(f'<div class="warn-box">{ICO_DOLLAR} El cliente debe pagar <b>{fmt(diferencia)}</b> adicionales</div>', unsafe_allow_html=True)
            elif diferencia < 0:
                st.markdown(f'<div class="info-box">{ICO_DOLLAR} Hay que devolver <b>{fmt(abs(diferencia))}</b> al cliente</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="info-box">{ICO_CHECK} Cambio sin diferencia de valor</div>', unsafe_allow_html=True)

            if st.button("🔁 Registrar cambio", key="venta_btn_cambio"):
                sb_post("ventas", {
                    "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                    "vendedor": fac["vendedor"], "sabor": sabor_out,
                    "cantidad": -cant_out, "total": -valor_out,
                    "cliente": fac["cliente"], "factura_id": fac["id"],
                    "abono": 0, "saldo": 0
                })
                if mutar_stock:
                    agregar_stock(sabor_out, cant_out)
                sb_post("ventas", {
                    "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                    "vendedor": fac["vendedor"], "sabor": sabor_in,
                    "cantidad": cant_in, "total": valor_in,
                    "cliente": fac["cliente"], "factura_id": fac["id"],
                    "abono": 0, "saldo": 0
                })
                if mutar_stock:
                    restar_stock(sabor_in, cant_in)
                if diferencia != 0:
                    raw_saldo = sb_get("ventas", f"select=saldo&factura_id=eq.{fac['id']}&canal=eq.{canal}&limit=1")
                    saldo_actual = float(raw_saldo[0]["saldo"]) if raw_saldo else 0
                    nuevo_saldo = max(0, saldo_actual + diferencia)
                    sb_patch("ventas", f"factura_id=eq.{fac['id']}&canal=eq.{canal}", {"saldo": nuevo_saldo})
                time.sleep(0.3)
                _recargar_factura(key_factura, fac)
                st.rerun()

        with tab_agregar:
            disp_add = cfg["disponible_map_fn"]()
            opciones_add = cfg["sabores_post_venta_fn"](disp_add)
            if not opciones_add:
                st.markdown(f'<div class="warn-box">{ICO_WARN} No hay disponible para agregar.</div>', unsafe_allow_html=True)
            else:
                sabor_add = st.selectbox("Sabor a agregar", opciones_add, key="venta_add_sabor")
                max_add = max(1, int(disp_add.get(sabor_add, 0)))
                cant_add = st.number_input("Cantidad", min_value=1, max_value=max_add, value=1, step=1, key="venta_add_cant")
                precio_add = fac["precios"].get(sabor_add, PRODUCTOS[sabor_add]) * cant_add
                st.markdown(f'<div class="info-box">{ICO_PACKAGE} Disponible: <b>{max_add}</b> · {ICO_DOLLAR} A cobrar: <b>{fmt(precio_add)}</b></div>', unsafe_allow_html=True)

                if st.button("➕ Agregar a la factura", key="venta_btn_add_fac"):
                    sb_post("ventas", {
                        "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                        "vendedor": fac["vendedor"], "sabor": sabor_add,
                        "cantidad": cant_add, "total": precio_add,
                        "cliente": fac["cliente"], "factura_id": fac["id"],
                        "abono": 0, "saldo": 0
                    })
                    if mutar_stock:
                        restar_stock(sabor_add, cant_add)
                    raw_saldo2 = sb_get("ventas", f"select=saldo&factura_id=eq.{fac['id']}&canal=eq.{canal}&limit=1")
                    saldo_actual2 = float(raw_saldo2[0]["saldo"]) if raw_saldo2 else 0
                    nuevo_saldo2 = saldo_actual2 + precio_add
                    sb_patch("ventas", f"factura_id=eq.{fac['id']}&canal=eq.{canal}", {"saldo": nuevo_saldo2})
                    time.sleep(0.3)
                    _recargar_factura(key_factura, fac)
                    st.rerun()

        if st.button("🧾 Nueva venta", key="venta_btn_nueva"):
            st.session_state[key_factura] = None
            st.rerun()

    # Ventas de hoy — visible para todos desde cualquier dispositivo
    st.markdown('<div class="section-label">Ventas de hoy</div>', unsafe_allow_html=True)
    st.caption("Toca una fila para ver el recibo completo.")
    raw_fact = sb_get("ventas",
        f"select=fecha,hora,cliente,vendedor,sabor,cantidad,total,factura_id,es_credito&fecha=eq.{fecha_hoy()}&canal=eq.{canal}&order=hora.desc")
    if raw_fact:
        df_fact = pd.DataFrame(raw_fact)
        mostrar_facturas_seleccionables(df_fact, cfg["tabla_key"])
    else:
        st.caption("Aún no hay ventas registradas hoy.")

    if mostrar_creditos:
        mostrar_creditos_pendientes(canal)

CONFIG_FABRICA = {
    "canal": "Fábrica",
    "icono": ICO_FACTORY,
    "key_carrito": "carrito",
    "key_precios": "precios_carrito",
    "key_factura": "factura_guardada",
    "vendedores": VENDEDORES_FABRICA,
    "vendedor_fijo": None,
    "mutar_stock": True,
    "tabla_key": "fabrica_todos",
    "sabores_venta_fn": lambda: sabores_por_frecuencia("Fábrica"),
    "disponible_map_fn": lambda: get_inventario_completo(),
    "sabores_post_venta_fn": lambda disp: [s for s in SABORES_LISTA if disp.get(s, 0) > 0],
}

CONFIG_CARRO = {
    "canal": "Carro",
    "icono": ICO_TRUCK,
    "key_carrito": "carrito_carro",
    "key_precios": "precios_carro",
    "key_factura": "factura_carro_guardada",
    "vendedores": None,
    "vendedor_fijo": "Javier & Edison",
    "mutar_stock": False,
    "tabla_key": "carro_todos",
    "sabores_venta_fn": lambda: sabores_por_frecuencia("Carro"),
    "disponible_map_fn": lambda: _stock_carro_actual(),
    "sabores_post_venta_fn": lambda disp: [s for s, v in disp.items() if v > 0],
}

def render_recibo(registros):
    """Genera el HTML de un recibo tipo ticket consolidando originales + cambios."""
    if not registros:
        return ""
    r0 = registros[0]
    fid = r0["factura_id"]
    fecha_r = r0["fecha"]
    hora_r = r0["hora"]
    cliente_r = r0.get("cliente", "Consumidor Final") or "Consumidor Final"
    vendedor_r = r0["vendedor"]

    # Consolidar items: sumar cantidades y totales por sabor (incluyendo negativos de cambios)
    items_cons = {}
    totales_cons = {}
    for r in registros:
        s = r["sabor"]
        items_cons[s]  = items_cons.get(s, 0) + r["cantidad"]
        totales_cons[s] = totales_cons.get(s, 0) + r["total"]

    # Filtrar items con cantidad > 0 (los que quedaron después de cambios)
    items_finales = {s: c for s, c in items_cons.items() if c > 0}
    total_r = sum(totales_cons[s] for s in items_finales)

    items_partes = []
    for s, c in items_finales.items():
        total_item = totales_cons[s]
        precio_unit = fmt(total_item / c) if c else fmt(0)
        items_partes.append(
            '<div class="recibo-item">'
            f'<div class="recibo-item-nombre">{s}</div>'
            '<div class="recibo-item-detalle">'
            f'<span>{c} × {precio_unit}</span>'
            f'<span>{fmt(total_item)}</span>'
            '</div></div>'
        )
    items_html = "".join(items_partes)

    partes = [
        '<div class="recibo-wrap"><div class="recibo-ticket">',
        f'<div class="recibo-logo">{logo_html}</div>',
        '<div class="recibo-titulo">Productos La Delicia</div>',
        '<div class="recibo-sub">Factura electrónica de venta</div>',
        f'<div class="recibo-sub">No. FV-{fid}</div>',
        '<div class="recibo-linea-punteada"></div>',
        f'<div class="recibo-dato"><b>Fecha:</b> {fecha_r} · {hora_r}</div>',
        f'<div class="recibo-dato"><b>Cliente:</b> {cliente_r}</div>',
        f'<div class="recibo-dato"><b>Vendedor:</b> {vendedor_r}</div>',
        '<div class="recibo-linea-punteada"></div>',
        items_html,
        '<div class="recibo-linea-punteada"></div>',
        f'<div class="recibo-total-row"><span>TOTAL</span><span>{fmt(total_r)}</span></div>',
        '<div class="recibo-linea-punteada"></div>',
        '<div class="recibo-footer">¡Gracias por su compra!</div>',
        '</div></div>'
    ]
    return "".join(partes)

def grafica_barras_sabor(labels, valores, titulo="bolsas"):
    """Gráfica de barras horizontales con colores de La Delicia."""
    import json as _json
    altura = max(220, len(labels) * 36 + 60)
    labels_json = _json.dumps(labels, ensure_ascii=False)
    valores_json = _json.dumps(valores)
    html = f"""
    <div style="position:relative;width:100%;height:{altura}px;background:#FFFFFF;border-radius:14px;padding:12px;box-shadow:0 2px 10px rgba(21,101,192,0.10);">
        <canvas id="chartBarras" role="img" aria-label="Gráfica de {titulo} por sabor"></canvas>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
    <script>
    new Chart(document.getElementById('chartBarras'), {{
        type: 'bar',
        data: {{
            labels: {labels_json},
            datasets: [{{
                label: '{titulo}',
                data: {valores_json},
                backgroundColor: '#1565C0',
                borderRadius: 6,
                barThickness: 22
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{
                x: {{ grid: {{ color: '#DCEEFB' }}, ticks: {{ color: '#1565C0', font: {{ size: 11 }} }} }},
                y: {{ grid: {{ display: false }}, ticks: {{ color: '#0D1B2A', font: {{ size: 12, weight: '600' }} }} }}
            }}
        }}
    }});
    </script>
    """
    components.html(html, height=altura + 20)

def grafica_linea_ventas(fechas, valores):
    """Gráfica de línea para evolución de ventas en el tiempo."""
    import json as _json
    fechas_json = _json.dumps(fechas, ensure_ascii=False)
    valores_json = _json.dumps(valores)
    html = f"""
    <div style="position:relative;width:100%;height:260px;background:#FFFFFF;border-radius:14px;padding:14px;box-shadow:0 2px 10px rgba(21,101,192,0.10);">
        <canvas id="chartLinea" role="img" aria-label="Gráfica de evolución de ventas en el mes"></canvas>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
    <script>
    const ctx = document.getElementById('chartLinea').getContext('2d');
    const gradiente = ctx.createLinearGradient(0,0,0,220);
    gradiente.addColorStop(0, 'rgba(21,101,192,0.25)');
    gradiente.addColorStop(1, 'rgba(216,27,122,0.02)');
    new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: {fechas_json},
            datasets: [{{
                label: 'Ventas',
                data: {valores_json},
                borderColor: '#1565C0',
                backgroundColor: gradiente,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: '#1565C0',
                pointBorderColor: '#FFFFFF',
                pointBorderWidth: 2,
                pointRadius: 4,
                borderWidth: 2.5
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{
                x: {{ grid: {{ display: false }}, ticks: {{ color: '#1565C0', font: {{ size: 10 }}, maxRotation: 45 }} }},
                y: {{ grid: {{ color: '#DCEEFB' }}, ticks: {{ color: '#1565C0', font: {{ size: 11 }} }} }}
            }}
        }}
    }});
    </script>
    """
    components.html(html, height=280)

# ══════════════════════════════════════════════════════════════════════════════
# DB HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def init_inventario():
    data = sb_get("inventario", "select=sabor")
    if not data:
        for sabor, precio in PRODUCTOS.items():
            sb_post("inventario", {"sabor": sabor, "stock": 0, "precio": precio})

@st.cache_data(ttl=5)
def get_inventario_completo():
    """Trae todo el inventario de una sola vez, cacheado 5 segundos."""
    data = sb_get("inventario", "select=sabor,stock,precio")
    return {r["sabor"]: r["stock"] for r in data} if data else {}

def get_stock(sabor):
    inv = get_inventario_completo()
    if sabor in inv:
        return inv[sabor]
    q = requests.utils.quote(sabor)
    r = sb_get("inventario", f"select=stock&sabor=eq.{q}")
    return int(r[0]["stock"]) if r else 0

def _ajustar_stock_cas(sabor, delta, intentos=5):
    """Suma/resta stock con concurrencia optimista: el PATCH solo aplica si nadie
    más cambió el valor entre la lectura y la escritura (evita perder cambios
    cuando dos ventas del mismo sabor se registran casi al mismo tiempo)."""
    q = requests.utils.quote(sabor)
    for _ in range(intentos):
        r = sb_get("inventario", f"select=stock&sabor=eq.{q}")
        stock_actual = int(r[0]["stock"]) if r else 0
        stock_nuevo = max(0, stock_actual + delta)
        try:
            resp = requests.patch(
                f"{SUPABASE_URL}/rest/v1/inventario?sabor=eq.{q}&stock=eq.{stock_actual}",
                headers=HEADERS, json={"stock": stock_nuevo}, timeout=10
            )
            if resp.ok and resp.json():
                get_inventario_completo.clear()
                get_metricas_globales.clear()
                return True
        except Exception:
            pass
    st.error(f"⚠️ No se pudo actualizar el stock de {sabor} (conflicto de concurrencia). Intenta de nuevo.")
    return False

def agregar_stock(sabor, cantidad):
    _ajustar_stock_cas(sabor, cantidad)

def restar_stock(sabor, cantidad):
    _ajustar_stock_cas(sabor, -cantidad)

def set_stock(sabor, cantidad):
    q = requests.utils.quote(sabor)
    sb_patch("inventario", f"sabor=eq.{q}", {"stock": cantidad})
    get_inventario_completo.clear()
    get_metricas_globales.clear()

@st.cache_data(ttl=60)
def sabores_por_frecuencia(canal=None):
    """Devuelve la lista de sabores ordenada: los más vendidos en los últimos 30 días primero. Cacheado 60s."""
    limite = (datetime.now(COL_TZ) - timedelta(days=30)).strftime("%Y-%m-%d")
    params = f"select=sabor,cantidad&fecha=gte.{limite}"
    if canal:
        params += f"&canal=eq.{canal}"
    raw = sb_get("ventas", params)
    if not raw:
        return SABORES_LISTA
    conteo = {}
    for r in raw:
        conteo[r["sabor"]] = conteo.get(r["sabor"], 0) + r["cantidad"]
    usados = sorted(conteo.keys(), key=lambda s: -conteo[s])
    resto = [s for s in SABORES_LISTA if s not in conteo]
    return usados + resto

@st.cache_data(ttl=60)
def sabores_produccion_frecuente():
    """Sabores ordenados por frecuencia de producción en los últimos 30 días. Cacheado 60s."""
    limite = (datetime.now(COL_TZ) - timedelta(days=30)).strftime("%Y-%m-%d")
    raw = sb_get("produccion", f"select=sabor,cantidad&fecha=gte.{limite}")
    if not raw:
        return SABORES_LISTA
    conteo = {}
    for r in raw:
        conteo[r["sabor"]] = conteo.get(r["sabor"], 0) + r["cantidad"]
    usados = sorted(conteo.keys(), key=lambda s: -conteo[s])
    resto = [s for s in SABORES_LISTA if s not in conteo]
    return usados + resto

def limpiar_datos_viejos():
    limite = (datetime.now(COL_TZ) - timedelta(days=180)).strftime("%Y-%m-%d")
    for tabla in ["produccion", "ventas", "cargues", "devoluciones"]:
        sb_delete(tabla, f"fecha=lt.{limite}")

# ══════════════════════════════════════════════════════════════════════════════
# LOGO
# ══════════════════════════════════════════════════════════════════════════════
def get_logo_b64():
    p = Path("Logo.png")
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else None

logo_b64 = get_logo_b64()
logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" style="height:120px;object-fit:contain;margin-bottom:6px;">'
    if logo_b64 else "🍟"
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif !important;background-color:#F0F4FF !important;color:#0D1B2A !important;font-size:18px;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem;padding-bottom:3rem;max-width:500px;margin:0 auto;}
@media (min-width: 768px){
  .block-container{max-width:900px;}
  html,body{font-size:19px;}
  .brand-header p{font-size:0.95rem;}
  .metric-box .val{font-size:1.6rem;}
  .metric-box .lbl{font-size:0.8rem;}
  .section-label{font-size:0.85rem;}
  .stButton>button{font-size:1.15rem !important;padding:18px !important;}
  label,.stSelectbox label,.stNumberInput label,.stDateInput label,.stTextInput label{font-size:1rem !important;}
}
@media (min-width: 1200px){
  .block-container{max-width:1100px;}
  html,body{font-size:20px;}
  .metric-box .val{font-size:1.9rem;}
  .stButton>button{font-size:1.25rem !important;padding:20px !important;}
}
[data-baseweb="base-input"],[data-baseweb="base-input"] *,[data-baseweb="select"],[data-baseweb="select"]>div,[data-baseweb="select"]>div>div{background-color:#FFFFFF !important;color:#0D1B2A !important;border-color:#BBDEFB !important;}
[data-baseweb="base-input"] input,[data-baseweb="base-input"] textarea,input[type="number"],input[type="text"],input[type="date"]{background-color:#FFFFFF !important;color:#0D1B2A !important;-webkit-text-fill-color:#0D1B2A !important;}
[data-testid="stNumberInputStepDown"],[data-testid="stNumberInputStepUp"]{background-color:#FCE4EC !important;color:#1565C0 !important;border:none !important;border-radius:7px !important;}
[data-testid="stNumberInputStepDown"]:hover,[data-testid="stNumberInputStepUp"]:hover{background-color:#1565C0 !important;color:white !important;}
[data-baseweb="select"]>div,[data-baseweb="base-input"]{border-radius:10px !important;border:1.5px solid #BBDEFB !important;}
[data-baseweb="select"] input{caret-color:transparent !important;cursor:pointer !important;}
[data-baseweb="select"] input:focus{caret-color:transparent !important;}
[data-baseweb="select"]>div:focus-within,[data-baseweb="base-input"]:focus-within{border-color:#1565C0 !important;box-shadow:0 0 0 3px rgba(21,101,192,0.15) !important;}
[data-baseweb="popover"],[data-baseweb="popover"] *,[data-baseweb="menu"],[data-baseweb="menu"] *,ul[data-testid="stSelectboxVirtualDropdown"],ul[data-testid="stSelectboxVirtualDropdown"] *{background-color:#FFFFFF !important;color:#0D1B2A !important;}
[data-baseweb="menu"] li:hover,[role="option"]:hover,[aria-selected="true"][role="option"]{background-color:#FCE4EC !important;color:#1565C0 !important;}
[data-baseweb="calendar"],[data-baseweb="calendar"] *{background-color:#FFFFFF !important;color:#0D1B2A !important;}
[data-baseweb="calendar"] button{color:#0D1B2A !important;background-color:transparent !important;}
[data-baseweb="calendar"] button:hover{background-color:#FCE4EC !important;color:#1565C0 !important;}
[data-baseweb="calendar"] [aria-selected="true"]{background-color:#1565C0 !important;color:white !important;}
[data-baseweb="calendar"] tbody tr:last-child td{background-color:#FFFFFF !important;}
label,.stSelectbox label,.stNumberInput label,.stDateInput label,.stTextInput label{color:#1565C0 !important;font-weight:600 !important;font-size:0.85rem !important;}
.stTabs [data-baseweb="tab-list"]{background:#FFFFFF;border-radius:12px;padding:4px;gap:2px;box-shadow:0 1px 4px rgba(21,101,192,0.10);margin-bottom:16px;}
.stTabs [data-baseweb="tab"]{border-radius:10px;font-size:0.78rem;font-weight:600;padding:8px 4px;color:#7A2050 !important;flex:1;justify-content:center;background:transparent !important;}
.stTabs [aria-selected="true"]{background-color:#1565C0 !important;color:white !important;}
.brand-header{background:linear-gradient(135deg,#1565C0,#1E88E5);border-radius:0 0 22px 22px;padding:12px 20px 12px;margin:-1rem -1rem 16px -1rem;text-align:center;}
.brand-header p{color:rgba(255,255,255,0.85);font-size:0.78rem;margin:0;}
.brand-logo img{height:620px !important;margin-bottom:0 !important;}
.metric-row{display:flex;gap:9px;margin-bottom:16px;}
.metric-box{flex:1;background:#FFFFFF;border-radius:14px;padding:14px 8px;text-align:center;box-shadow:0 2px 8px rgba(21,101,192,0.12);}
.metric-box .val{font-size:1.2rem;font-weight:700;line-height:1.1;}
.metric-box .lbl{font-size:0.65rem;color:#1565C0;margin-top:3px;}
.metric-blue .val{color:#1565C0;}.metric-green .val{color:#1B9E5A;}.metric-red .val{color:#D32F2F;}.metric-yellow .val{color:#E68900;}
.alert-low{background:#FFEBEE;border-left:3px solid #D32F2F;border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:9px;font-size:0.83rem;color:#B71C1C;}
.info-box{background:#FFFFFF;border-left:3px solid #1B9E5A;border-radius:10px;padding:12px 14px;margin:8px 0 14px;font-size:0.82rem;color:#1B5E20;box-shadow:0 1px 6px rgba(0,0,0,0.05);}
.warn-box{background:#FFFFFF;border-left:3px solid #E68900;border-radius:10px;padding:12px 14px;margin:8px 0 14px;font-size:0.82rem;color:#8D6E00;box-shadow:0 1px 6px rgba(0,0,0,0.05);}
.success-toast{background:#E8F5E9;border:1px solid #A5D6A7;border-radius:12px;padding:14px 16px;text-align:center;font-weight:600;color:#1B5E20;font-size:0.95rem;margin-top:10px;}
.section-label{font-size:0.69rem;font-weight:700;text-transform:uppercase;letter-spacing:0.7px;color:#B0185F;margin:16px 0 6px;}
.stButton>button{width:100%;background:#1565C0 !important;color:white !important;-webkit-text-fill-color:white !important;border:none !important;border-radius:12px !important;padding:14px !important;font-size:1rem !important;font-weight:700 !important;cursor:pointer;margin-top:4px;box-shadow:0 4px 16px rgba(21,101,192,0.25);white-space:pre-line !important;line-height:1.4 !important;}
.stButton>button:hover{opacity:0.88;}
.st-key-btn_resumen button{
  background:linear-gradient(135deg,#FFFFFF,#EEF4FF) !important;
  color:#0D1B2A !important;
  -webkit-text-fill-color:#0D1B2A !important;
  border:none !important;
  border-radius:18px !important;
  box-shadow:0 3px 12px rgba(21,101,192,0.18) !important;
  min-height:90px !important;
  padding:18px 20px !important;
  font-size:1rem !important;
  font-weight:700 !important;
  white-space:pre-line !important;
  line-height:1.5 !important;
  text-align:left !important;
}
.st-key-btn_resumen button:hover{
  box-shadow:0 5px 16px rgba(21,101,192,0.25) !important;
  opacity:1 !important;
}

[data-testid="stMetricLabel"] p{color:#1565C0 !important;}
[data-testid="stMetricValue"]{color:#0D1B2A !important;}
.stDataFrame{border-radius:12px;overflow:hidden;font-size:0.83rem;border:1px solid #BBDEFB;}
.stCaption,small{color:#1565C0 !important;}
.stAlert{background:#F0F7FF !important;color:#0D1B2A !important;border-color:#BBDEFB !important;}
.factura-box{background:#FFFFFF;border-radius:16px;padding:16px;margin-bottom:14px;box-shadow:0 2px 10px rgba(21,101,192,0.10);}
.factura-header{font-size:0.9rem;font-weight:700;color:#1565C0;margin-bottom:8px;}
.factura-row{display:flex;justify-content:space-between;font-size:0.85rem;padding:4px 0;border-bottom:1px solid #BBDEFB;color:#0D1B2A;}
.factura-total{display:flex;justify-content:space-between;font-size:1rem;font-weight:700;color:#1B9E5A;margin-top:8px;}
.factura-cambio{font-size:0.9rem;color:#E68900;margin-top:6px;text-align:center;}
.tabla-fact-wrap{overflow-x:auto;border-radius:10px;box-shadow:0 2px 10px rgba(21,101,192,0.10);margin-bottom:14px;}
.tabla-fact{width:100%;border-collapse:collapse;font-size:0.78rem;background:#FFFFFF;}
.tabla-fact thead{background:#1565C0;}
.tabla-fact thead th{color:white;font-weight:600;padding:10px 8px;text-align:left;white-space:nowrap;}
.tabla-fact tbody td{padding:9px 8px;border-bottom:1px solid #DCEEFB;color:#0D1B2A;white-space:nowrap;}
.tabla-fact tbody tr:hover{background:#F0F7FF;}
.tabla-fact .num-comp{color:#1565C0;font-weight:600;}
.tabla-fact .estado-ok{color:#1B9E5A;font-weight:600;}
.tabla-fact .total-col{text-align:right;font-weight:600;}
.recibo-wrap{display:flex;justify-content:center;padding:20px 0;}
.recibo-ticket{background:#FFFFFF;width:100%;max-width:380px;padding:24px 20px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.12);font-family:'Courier New',monospace;}
.recibo-logo{text-align:center;margin-bottom:6px;}
.recibo-logo img{height:60px !important;}
.recibo-titulo{text-align:center;font-weight:700;font-size:1rem;color:#0D1B2A;}
.recibo-sub{text-align:center;font-size:0.78rem;color:#1565C0;}
.recibo-linea-punteada{border-top:1.5px dashed #BBDEFB;margin:12px 0;}
.recibo-dato{font-size:0.82rem;color:#0D1B2A;margin-bottom:4px;}
.recibo-item{margin-bottom:8px;}
.recibo-item-nombre{font-size:0.85rem;font-weight:600;color:#0D1B2A;}
.recibo-item-detalle{display:flex;justify-content:space-between;font-size:0.8rem;color:#1565C0;}
.recibo-total-row{display:flex;justify-content:space-between;font-size:1.05rem;font-weight:700;color:#1B9E5A;}
.recibo-footer{text-align:center;font-size:0.8rem;color:#1565C0;font-style:italic;}
div[data-testid="stRadio"] > div{display:flex;flex-wrap:wrap;gap:8px;}
div[data-testid="stRadio"] label{background:#1565C0 !important;border:2px solid #1565C0 !important;border-radius:8px !important;padding:8px 16px !important;cursor:pointer;}
div[data-testid="stRadio"] label p, div[data-testid="stRadio"] label span{color:white !important;font-weight:600 !important;}
div[data-testid="stRadio"] input[type="radio"]{accent-color:#1565C0;}
.calc-box{background:#FFFFFF;border-radius:14px;padding:14px;margin-bottom:14px;box-shadow:0 2px 10px rgba(21,101,192,0.10);}
.main-btn{background:#F0F7FF;border:1px solid #BBDEFB;border-radius:14px;padding:20px 16px;margin-bottom:10px;cursor:pointer;display:flex;align-items:center;gap:14px;}
.main-btn-icon{font-size:2rem;}
.main-btn-text{font-size:1.1rem;font-weight:700;color:#0D1B2A;}
.main-btn-sub{font-size:0.78rem;color:#1565C0;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# IMÁGENES DE FONDO DE LOS BOTONES DEL MENÚ
# ══════════════════════════════════════════════════════════════════════════════
def get_img_b64(nombre_archivo):
    p = Path(nombre_archivo)
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else None

def get_svg_b64(paths_svg, stroke):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
           f'stroke="{stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths_svg}</svg>')
    return base64.b64encode(svg.encode()).decode()

_imagenes_menu = {
    "produccion":    "Produccion.jpg",
    "carro":         "Cargue.jpg",
    "fabrica":       "Ventas_sofia_andrea.jpg",
    "materia_prima": "Materia_prima.jpg",
    "caja":          "Caja.jpg",
}

# Iconos vectoriales (reemplazan los emojis, que no siempre se ven igual en todos los dispositivos)
_iconos_svg = {
    "produccion":    '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
    "carro":         '<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
    "fabrica":       '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
    "materia_prima": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "caja":          '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "resumen":       '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
}

_css_botones_menu = ""
for _vista, _archivo in _imagenes_menu.items():
    _b64 = get_img_b64(_archivo)
    _icon_b64 = get_svg_b64(_iconos_svg[_vista], "white")
    if _b64:
        _css_botones_menu += f"""
.st-key-btn_{_vista} button{{
  background:linear-gradient(90deg,rgba(0,0,0,0.72) 0%,rgba(0,0,0,0.55) 55%,rgba(0,0,0,0.4) 100%),url("data:image/jpeg;base64,{_b64}") center/cover no-repeat !important;
  color:#FFFFFF !important;
  -webkit-text-fill-color:#FFFFFF !important;
  border:none !important;
  border-radius:18px !important;
  box-shadow:0 3px 12px rgba(21,101,192,0.25) !important;
  min-height:110px !important;
  padding:18px 20px 18px 60px !important;
  font-size:1rem !important;
  font-weight:700 !important;
  white-space:pre-line !important;
  line-height:1.5 !important;
  text-align:left !important;
  text-shadow:0 1px 3px rgba(0,0,0,0.9),0 2px 8px rgba(0,0,0,0.6) !important;
  position:relative !important;
}}
.st-key-btn_{_vista} button::before{{
  content:'';
  position:absolute;
  left:18px;
  top:50%;
  transform:translateY(-50%);
  width:28px;
  height:28px;
  background:url("data:image/svg+xml;base64,{_icon_b64}") no-repeat center/contain;
}}
.st-key-btn_{_vista} button:hover{{
  background:linear-gradient(90deg,rgba(0,0,0,0.6) 0%,rgba(0,0,0,0.42) 55%,rgba(0,0,0,0.28) 100%),url("data:image/jpeg;base64,{_b64}") center/cover no-repeat !important;
  box-shadow:0 5px 16px rgba(21,101,192,0.32) !important;
  opacity:1 !important;
}}
"""

_resumen_icon_b64 = get_svg_b64(_iconos_svg["resumen"], "#0D1B2A")
_css_botones_menu += f"""
.st-key-btn_resumen button{{
  padding-left:60px !important;
  position:relative !important;
}}
.st-key-btn_resumen button::before{{
  content:'';
  position:absolute;
  left:18px;
  top:50%;
  transform:translateY(-50%);
  width:28px;
  height:28px;
  background:url("data:image/svg+xml;base64,{_resumen_icon_b64}") no-repeat center/contain;
}}
"""

if _css_botones_menu:
    st.markdown(f"<style>{_css_botones_menu}</style>", unsafe_allow_html=True)

# Bloquear teclado virtual en los selectbox y fechas (solo permite tocar y elegir)
components.html("""
<script>
function bloquearTecladoSelects() {
    try {
        const inputs = window.parent.document.querySelectorAll('[data-baseweb="select"] input');
        inputs.forEach(function(inp) {
            inp.setAttribute('inputmode', 'none');
            inp.setAttribute('readonly', 'true');
        });
    } catch (e) {}
}
function bloquearTecladoFechas() {
    try {
        const fechas = window.parent.document.querySelectorAll('[data-testid="stDateInputField"], [data-baseweb="datepicker"] input');
        fechas.forEach(function(inp) {
            inp.setAttribute('inputmode', 'none');
            inp.setAttribute('readonly', 'true');
        });
    } catch (e) {}
}
function forzarTecladoNumerico() {
    try {
        const numeros = window.parent.document.querySelectorAll('[data-testid="stNumberInputField"]');
        numeros.forEach(function(inp) {
            inp.setAttribute('inputmode', 'numeric');
        });
    } catch (e) {}
}
bloquearTecladoSelects();
bloquearTecladoFechas();
forzarTecladoNumerico();
setInterval(bloquearTecladoSelects, 500);
setInterval(bloquearTecladoFechas, 500);
setInterval(forzarTecladoNumerico, 500);
</script>
""", height=0)

# ══════════════════════════════════════════════════════════════════════════════
# INICIALIZAR
# ══════════════════════════════════════════════════════════════════════════════
if "iniciado" not in st.session_state:
    init_inventario()
    st.session_state.iniciado = True
if "limpieza" not in st.session_state:
    limpiar_datos_viejos()
    st.session_state.limpieza = True

# Session state
defaults = {
    "es_admin": False,
    "vista": "menu",        # menu | produccion | carro | fabrica | resumen
    "vista_anterior": "resumen",
    "carrito": {},
    "precios_carrito": {},  # precio modificado por item
    "carrito_carro": {},
    "precios_carro": {},
    "factura_guardada": None,
    "factura_carro_guardada": None,
    "ok_prod": False,
    "ok_cargue": False,
    "ok_dev": False,
    "ok_mp":  False,
    "insumo_sel": None,
    "categoria_mp": None,
    "ok_stock": False,
    "mostrar_calc": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
ADMINS = dict(st.secrets["admins"])
NOMBRES_ADMIN = dict(st.secrets["admin_nombres"])

def check_login(usuario, pw):
    u = usuario.lower().strip()
    if u in ADMINS:
        return hashlib.sha256(pw.encode()).hexdigest() == ADMINS[u]
    return False

if "admin_actual" not in st.session_state:
    st.session_state.admin_actual = None

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="brand-header">
    <div class="brand-logo">{logo_html}</div>
    <p>Control de producción y ventas</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MÉTRICAS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=5)
def get_metricas_globales(fecha):
    def q_inv():   return sb_get("inventario", "select=sabor,stock")
    def q_prod():  return sb_get("produccion", f"select=cantidad&fecha=eq.{fecha}")
    def q_venta(): return sb_get("ventas",     f"select=factura_id,abono&fecha=eq.{fecha}")
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_inv   = ex.submit(q_inv)
        f_prod  = ex.submit(q_prod)
        f_venta = ex.submit(q_venta)
    return f_inv.result(), f_prod.result(), f_venta.result()

_inv, _prod, _venta = get_metricas_globales(fecha_hoy())
total_inv  = sum(r["stock"]    for r in _inv)   if _inv   else 0
total_prod = sum(r["cantidad"] for r in _prod)  if _prod  else 0

# Dinero realmente cobrado hoy — una sola vez por factura (el abono se repite
# en cada línea de una misma factura). Las ventas a crédito solo cuentan por
# lo que ya se abonó, no por el total de la venta.
_facturas_vta = {}
for r in (_venta or []):
    fid = r.get("factura_id", "")
    if fid and fid not in _facturas_vta:
        _facturas_vta[fid] = float(r.get("abono", 0) or 0)
total_vta = sum(_facturas_vta.values())

if st.session_state.es_admin:
    tarjeta_ventas = f'<div class="metric-box metric-green"><div class="val">{fmt(total_vta)}</div><div class="lbl">Ventas hoy</div></div>'
else:
    tarjeta_ventas = f'<div class="metric-box metric-green"><div class="val">{ICO_LOCK}</div><div class="lbl">Solo admin</div></div>'

st.markdown(f"""
<div class="metric-row">
    <div class="metric-box metric-blue"><div class="val">{total_inv}</div><div class="lbl">En inventario</div></div>
    <div class="metric-box metric-yellow"><div class="val">{total_prod}</div><div class="lbl">Producidas hoy</div></div>
    {tarjeta_ventas}
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ALERTA GLOBAL DE STOCK BAJO — visible en TODAS las vistas
# ══════════════════════════════════════════════════════════════════════════════
raw_inv_global = _inv
if raw_inv_global:
    agotados = [r for r in raw_inv_global if r["stock"] == 0]
    bajos_global = [r for r in raw_inv_global if 0 < r["stock"] < STOCK_MINIMO]

    if agotados:
        nombres_ag = ", ".join(r["sabor"] for r in agotados[:6])
        extra_ag = f" y {len(agotados)-6} más" if len(agotados) > 6 else ""
        st.markdown(
            f'<div class="alert-low">{ICO_DOT_RED} <b>Agotado:</b> {nombres_ag}{extra_ag}</div>',
            unsafe_allow_html=True
        )

    if bajos_global:
        nombres_bj = ", ".join(f"{r['sabor']} ({r['stock']})" for r in bajos_global[:6])
        extra_bj = f" y {len(bajos_global)-6} más" if len(bajos_global) > 6 else ""
        st.markdown(
            f'<div class="warn-box">{ICO_WARN} <b>Stock bajo:</b> {nombres_bj}{extra_bj}</div>',
            unsafe_allow_html=True
        )

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.es_admin:
    with st.expander("🔐 Acceso administrador", expanded=False):
        cu, cp = st.columns(2)
        u = cu.text_input("Usuario", placeholder="Usuario", key="lu", label_visibility="collapsed")
        p = cp.text_input("Contraseña", type="password", placeholder="Contraseña", key="lp", label_visibility="collapsed")
        if st.button("Entrar", key="btn_login"):
            if check_login(u, p):
                st.session_state.es_admin = True
                st.session_state.admin_actual = u.lower().strip()
                st.rerun()
            else:
                st.markdown(f'<div class="alert-low">{ICO_WARN} Usuario o contraseña incorrectos.</div>', unsafe_allow_html=True)
else:
    nombre_admin = NOMBRES_ADMIN.get(st.session_state.admin_actual, "Administrador")
    st.markdown(f'<div class="info-box">{ICO_CHECK} Sesión activa — <b>{nombre_admin} (Administrador)</b></div>', unsafe_allow_html=True)
    if st.button("🔒 Cerrar sesión", key="btn_logout"):
        st.session_state.es_admin = False
        st.session_state.admin_actual = None
        st.session_state.vista = "menu"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# NAVEGACIÓN — botón atrás
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista != "menu":
    if st.session_state.vista == "recibo":
        vista_volver = st.session_state.get("vista_anterior", "resumen")
        texto_volver = f"← Volver"
    else:
        vista_volver = "menu"
        texto_volver = "← Volver al menú"
    if st.button(texto_volver, key="btn_back"):
        st.session_state.vista = vista_volver
        st.rerun()
    st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# CALCULADORA (función reutilizable)
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista == "menu":
    opciones = [
        ("produccion",    "Producción",      "Registrar bolsas fabricadas"),
        ("carro",         "Edison & Javier", "Cargues y ventas del carro"),
        ("fabrica",       "Fábrica",          "Ventas de Sofía y Andrea"),
        ("materia_prima", "Materia Prima",    "Insumos y proveedores"),
        ("caja",          "Caja",              "Ingresos y egresos"),
    ]
    if st.session_state.es_admin:
        opciones.append(("resumen", "Resumen", "Ventas, facturas y exportar"))

    for vista, titulo, sub in opciones:
        with st.container():
            if st.button(f"{titulo}\n{sub}", key=f"btn_{vista}", use_container_width=True):
                st.session_state.vista = vista
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: PRODUCCIÓN
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "produccion":
    st.markdown('<div class="section-label">Registrar producción</div>', unsafe_allow_html=True)

    empleado   = st.selectbox("¿Quién registra?", EMPLEADOS, key="emp")
    sabor_p    = st.selectbox("Sabor producido", sabores_produccion_frecuente(), key="sabor_p")
    cantidad_p = st.number_input("Bolsas producidas", min_value=1, max_value=2000, value=50, step=10, key="cant_p")

    stock_act = get_stock(sabor_p)
    st.markdown(f'<div class="info-box">{ICO_PACKAGE} Stock actual de <b>{sabor_p}</b>: {stock_act} → quedará en <b>{stock_act + cantidad_p}</b></div>', unsafe_allow_html=True)

    def _registrar_produccion(empleado, sabor, cantidad):
        sb_post("produccion", {
            "fecha": fecha_hoy(), "hora": ahora(),
            "empleado": empleado, "sabor": sabor, "cantidad": cantidad
        })
        agregar_stock(sabor, cantidad)
        st.session_state.ok_prod = True
        st.session_state.confirmar_prod = False

    confirmar_prod = st.checkbox(f"Confirmo: {cantidad_p} bolsas de {sabor_p}", key="confirmar_prod")
    if st.button("✅ Registrar producción", key="btn_prod", disabled=not confirmar_prod,
                 on_click=_registrar_produccion, args=(empleado, sabor_p, cantidad_p)):
        time.sleep(0.3)
        st.rerun()

    if st.session_state.ok_prod:
        st.markdown(f'<div class="success-toast">{ICO_CHECK} ¡Producción registrada!</div>', unsafe_allow_html=True)
        st.session_state.ok_prod = False

    # Producción de un día — selector de fecha + tabla totalmente editable
    st.markdown('<div class="section-label">Consultar producción</div>', unsafe_allow_html=True)
    fecha_consulta = st.date_input(
        "Día a consultar",
        value=datetime.now(COL_TZ).date(),
        key="fecha_consulta_prod"
    )
    fecha_consulta_str = str(fecha_consulta)
    es_hoy = fecha_consulta_str == fecha_hoy()
    titulo_tabla = "Producción de hoy" if es_hoy else f"Producción del {fecha_consulta_str}"

    raw_prod = sb_get("produccion", f"select=id,fecha,hora,empleado,sabor,cantidad&fecha=eq.{fecha_consulta_str}&order=hora.desc")
    if raw_prod:
        st.markdown(f'<div class="section-label">{titulo_tabla}</div>', unsafe_allow_html=True)
        st.caption("Toca cualquier celda para editar. Luego presiona Guardar cambios.")
        df_prod = pd.DataFrame(raw_prod)
        df_edit = df_prod[["fecha","hora","empleado","sabor","cantidad"]].copy()
        df_edit.columns = ["Fecha","Hora","Empleado","Sabor","Bolsas"]

        edited = st.data_editor(
            df_edit,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha":    st.column_config.TextColumn("Fecha"),
                "Hora":     st.column_config.TextColumn("Hora"),
                "Empleado": st.column_config.SelectboxColumn("Empleado", options=EMPLEADOS),
                "Sabor":    st.column_config.SelectboxColumn("Sabor", options=SABORES_LISTA),
                "Bolsas":   st.column_config.NumberColumn("Bolsas", min_value=0, step=1),
            },
            key="prod_editor"
        )

        # Detectar cambios y guardar
        col_g, col_e = st.columns(2)
        if col_g.button("💾 Guardar cambios", key="btn_save_prod"):
            for i, row in edited.iterrows():
                orig = df_prod.iloc[i]
                cambios = {}

                fecha_orig = str(orig["fecha"])
                hora_orig  = str(orig["hora"])
                emp_orig   = str(orig["empleado"])
                sabor_orig = str(orig["sabor"])
                cant_orig  = int(orig["cantidad"])

                fecha_new  = str(row["Fecha"])
                hora_new   = str(row["Hora"])
                emp_new    = str(row["Empleado"])
                sabor_new  = str(row["Sabor"])
                cant_new   = int(row["Bolsas"])

                if fecha_new != fecha_orig:
                    cambios["fecha"] = fecha_new
                if hora_new != hora_orig:
                    cambios["hora"] = hora_new
                if emp_new != emp_orig:
                    cambios["empleado"] = emp_new
                if sabor_new != sabor_orig:
                    restar_stock(sabor_orig, cant_orig)
                    agregar_stock(sabor_new, cant_new)
                    cambios["sabor"] = sabor_new
                    cambios["cantidad"] = cant_new
                elif cant_new != cant_orig:
                    diff = cant_new - cant_orig
                    if diff > 0:
                        agregar_stock(sabor_orig, diff)
                    else:
                        restar_stock(sabor_orig, abs(diff))
                    cambios["cantidad"] = cant_new

                if cambios:
                    sb_patch("produccion", f"id=eq.{orig['id']}", cambios)
            time.sleep(1)
            st.rerun()

        # Eliminar fila seleccionada
        ids_prod = {f"{r['fecha']} {r['hora']} — {r['sabor']} ({r['cantidad']} bolsas)": r for r in raw_prod}
        sel_del = st.selectbox("Eliminar registro", ["— Selecciona —"] + list(ids_prod.keys()), key="sel_del_prod")
        if sel_del != "— Selecciona —" and col_e.button("🗑️ Eliminar", key="btn_del_prod"):
            reg_del = ids_prod[sel_del]
            sb_delete("produccion", f"id=eq.{reg_del['id']}")
            restar_stock(reg_del["sabor"], reg_del["cantidad"])
            time.sleep(0.3)
            st.rerun()
    else:
        st.info(f"No hay producción registrada el {fecha_consulta_str}.")

    # Inventario actual
    raw_inv = sb_get("inventario", "select=sabor,stock,precio&order=sabor.asc")
    if raw_inv:
        st.markdown('<div class="section-label">Inventario actual</div>', unsafe_allow_html=True)
        df_inv = pd.DataFrame(raw_inv)
        df_inv["precio"] = df_inv["precio"].apply(fmt)
        df_inv["estado"] = df_inv["stock"].apply(lambda x: "🔴 Agotado" if x==0 else ("🟡 Poco" if x<10 else "🟢 OK"))
        df_inv.columns = ["Sabor","Bolsas","Precio","Estado"]
        st.dataframe(df_inv, use_container_width=True, hide_index=True)

    # Ajuste manual
    st.markdown('<div class="section-label">Ajustar stock manualmente</div>', unsafe_allow_html=True)
    sabor_adj = st.selectbox("Sabor", SABORES_LISTA, key="sabor_adj")
    stock_adj = get_stock(sabor_adj)
    nuevo_stock = st.number_input("Stock real", min_value=0, value=stock_adj, step=1, key=f"nuevo_s_{sabor_adj}")
    if st.button("💾 Guardar ajuste", key="btn_adj"):
        set_stock(sabor_adj, nuevo_stock)
        st.session_state.ok_stock = True
        time.sleep(0.3)
        st.rerun()
    if st.session_state.ok_stock:
        st.markdown(f'<div class="success-toast">{ICO_CHECK} Stock ajustado.</div>', unsafe_allow_html=True)
        st.session_state.ok_stock = False

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: CARRO (Edison & Javier)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "carro":

    sub1, sub2, sub3, sub4, sub5 = st.tabs(["🚗 Nuevo cargue", "💵 Registrar venta", "🔄 Devolución", "🎁 Regalar", "💳 Créditos"])

    with sub1:
        st.markdown('<div class="section-label">Cargue del carro</div>', unsafe_allow_html=True)
        st.caption("Escribe la cantidad solo en los sabores que vas a cargar y presiona Registrar.")

        sabores_cg_orden = sabores_por_frecuencia("Carro")
        with st.form("form_cargue", clear_on_submit=True):
            cols_cg = st.columns(3)
            cantidades_cg = {}
            for i, sabor in enumerate(sabores_cg_orden):
                stock_s = get_stock(sabor)
                with cols_cg[i % 3]:
                    cantidades_cg[sabor] = st.number_input(
                        f"{sabor} ({stock_s} disp.)",
                        min_value=0, max_value=max(0, stock_s), value=0, step=5,
                        key=f"cg_{sabor}", disabled=(stock_s == 0)
                    )
            enviar_cg = st.form_submit_button("🚗 Registrar cargue")

        if enviar_cg:
            registrados_cg = [(s, c) for s, c in cantidades_cg.items() if c > 0]
            if not registrados_cg:
                st.warning("Ingresa al menos una cantidad para registrar.")
            else:
                for sabor, cantidad in registrados_cg:
                    sb_post("cargues", {"fecha": fecha_hoy(), "hora": ahora(), "sabor": sabor, "cantidad": cantidad})
                    restar_stock(sabor, cantidad)
                st.session_state.ok_cargue = True
                time.sleep(0.3)
                st.rerun()

        if st.session_state.ok_cargue:
            st.markdown(f'<div class="success-toast">{ICO_CHECK} Cargue registrado.</div>', unsafe_allow_html=True)
            st.session_state.ok_cargue = False

        # Lo que lleva el carro (histórico — incluye días anteriores)
        stock_carro_sub1 = _stock_carro_actual()
        pendientes_sub1 = sorted(
            ((s, v) for s, v in stock_carro_sub1.items() if v > 0),
            key=lambda x: -x[1]
        )
        if pendientes_sub1:
            st.markdown('<div class="section-label">Lo que lleva el carro ahora</div>', unsafe_allow_html=True)
            df_pend = pd.DataFrame(pendientes_sub1, columns=["Sabor", "Bolsas pendientes"])
            st.dataframe(df_pend, use_container_width=True, hide_index=True)

        # Tabla editable de cargues — consulta por fecha
        st.markdown('<div class="section-label">Consultar cargues por fecha</div>', unsafe_allow_html=True)
        fecha_consulta_cg = st.date_input(
            "Día a consultar",
            value=datetime.now(COL_TZ).date(),
            key="fecha_consulta_cg"
        )
        fecha_consulta_cg_str = str(fecha_consulta_cg)
        es_hoy_cg = fecha_consulta_cg_str == fecha_hoy()
        titulo_cg = "Cargues de hoy" if es_hoy_cg else f"Cargues del {fecha_consulta_cg_str}"

        raw_cg_full = sb_get("cargues", f"select=id,fecha,hora,sabor,cantidad&fecha=eq.{fecha_consulta_cg_str}&order=hora.desc")
        if raw_cg_full:
            st.markdown(f'<div class="section-label">{titulo_cg}</div>', unsafe_allow_html=True)
            st.caption("Toca cualquier celda para corregir un error. Luego presiona Guardar cambios.")
            df_cg_full = pd.DataFrame(raw_cg_full)
            df_cg_edit = df_cg_full[["fecha","hora","sabor","cantidad"]].copy()
            df_cg_edit.columns = ["Fecha","Hora","Sabor","Bolsas"]

            edited_cg = st.data_editor(
                df_cg_edit,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Fecha":  st.column_config.TextColumn("Fecha"),
                    "Hora":   st.column_config.TextColumn("Hora"),
                    "Sabor":  st.column_config.SelectboxColumn("Sabor", options=SABORES_LISTA),
                    "Bolsas": st.column_config.NumberColumn("Bolsas", min_value=0, step=1),
                },
                key="cargue_editor"
            )

            col_gcg, col_ecg = st.columns(2)
            if col_gcg.button("💾 Guardar cambios", key="btn_save_cg"):
                for i, row in edited_cg.iterrows():
                    orig = df_cg_full.iloc[i]
                    cambios = {}

                    fecha_orig = str(orig["fecha"])
                    hora_orig  = str(orig["hora"])
                    sabor_orig = str(orig["sabor"])
                    cant_orig  = int(orig["cantidad"])

                    fecha_new  = str(row["Fecha"])
                    hora_new   = str(row["Hora"])
                    sabor_new  = str(row["Sabor"])
                    cant_new   = int(row["Bolsas"])

                    if fecha_new != fecha_orig:
                        cambios["fecha"] = fecha_new
                    if hora_new != hora_orig:
                        cambios["hora"] = hora_new
                    if sabor_new != sabor_orig:
                        agregar_stock(sabor_orig, cant_orig)
                        restar_stock(sabor_new, cant_new)
                        cambios["sabor"] = sabor_new
                        cambios["cantidad"] = cant_new
                    elif cant_new != cant_orig:
                        diff = cant_new - cant_orig
                        if diff > 0:
                            restar_stock(sabor_orig, diff)
                        else:
                            agregar_stock(sabor_orig, abs(diff))
                        cambios["cantidad"] = cant_new

                    if cambios:
                        sb_patch("cargues", f"id=eq.{orig['id']}", cambios)
                time.sleep(1)
                st.rerun()

            ids_cg = {f"{r['fecha']} {r['hora']} — {r['sabor']} ({r['cantidad']} bolsas)": r for r in raw_cg_full}
            sel_del_cg = st.selectbox("Eliminar registro", ["— Selecciona —"] + list(ids_cg.keys()), key="sel_del_cg")
            if sel_del_cg != "— Selecciona —" and col_ecg.button("🗑️ Eliminar", key="btn_del_cg"):
                reg_del_cg = ids_cg[sel_del_cg]
                sb_delete("cargues", f"id=eq.{reg_del_cg['id']}")
                agregar_stock(reg_del_cg["sabor"], reg_del_cg["cantidad"])
                time.sleep(0.3)
                st.rerun()
        else:
            st.info(f"No hay cargues registrados el {fecha_consulta_cg_str}.")

    with sub2:
        render_venta_canal(CONFIG_CARRO, mostrar_creditos=False)

        # Papas disponibles del cargue — histórico completo
        st.markdown('<div class="section-label">Papas disponibles del cargue</div>', unsafe_allow_html=True)
        stock_carro_sub2 = _stock_carro_actual()
        disponibles_cargue = sorted(((s, v) for s, v in stock_carro_sub2.items() if v > 0), key=lambda x: -x[1])
        if disponibles_cargue:
            filas_cg = "".join(
                f'<div class="factura-row"><span>{s}</span><span><b>{int(v)} bolsas</b></span></div>'
                for s, v in disponibles_cargue
            )
            st.markdown(f'<div class="factura-box">{filas_cg}</div>', unsafe_allow_html=True)
        else:
            st.caption("No hay cargue activo hoy.")

        # Solo admin ve resumen del carro
        if st.session_state.es_admin:
            raw_resumen_carro = sb_get("ventas", f"select=total,cantidad&fecha=eq.{fecha_hoy()}&canal=eq.Carro")
            if raw_resumen_carro:
                total_carro_dia  = sum(r["total"]    for r in raw_resumen_carro if r["total"] > 0)
                bolsas_carro_dia = sum(r["cantidad"] for r in raw_resumen_carro if r["cantidad"] > 0)
                st.markdown('<div class="section-label">Resumen del día — Javier & Edison</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="factura-box">'
                    f'<div class="factura-row"><span>{ICO_CART} Bolsas vendidas hoy</span><span><b>{bolsas_carro_dia}</b></span></div>'
                    f'<div class="factura-total"><span>{ICO_DOLLAR} Total a entregar</span><span>{fmt(total_carro_dia)}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    with sub3:
        st.markdown(f'<div class="section-label">Devolución al inventario {ICO_REFRESH}</div>', unsafe_allow_html=True)
        st.caption("Registra las bolsas que regresan al inventario.")
        sabor_dev = st.selectbox("Sabor a devolver", SABORES_LISTA, key="sabor_dev")

        # Máximo a devolver = lo que cargaron de ese sabor hoy - lo ya devuelto
        raw_cg_dev = sb_get("cargues", f"select=cantidad&fecha=eq.{fecha_hoy()}&sabor=eq.{requests.utils.quote(sabor_dev)}")
        raw_dev_ya = sb_get("devoluciones", f"select=cantidad&fecha=eq.{fecha_hoy()}&sabor=eq.{requests.utils.quote(sabor_dev)}")
        max_cargado = sum(r["cantidad"] for r in raw_cg_dev) if raw_cg_dev else 500
        ya_devuelto = sum(r["cantidad"] for r in raw_dev_ya) if raw_dev_ya else 0
        max_dev = max(1, max_cargado - ya_devuelto)

        cant_dev  = st.number_input("Bolsas devueltas", min_value=1, max_value=max_dev, value=1, step=1, key="cant_dev")
        fecha_dev = st.date_input("Fecha de devolución", value=datetime.now(COL_TZ).date(), key="fecha_dev")
        st.markdown(f'<div class="info-box">{ICO_PACKAGE} Máximo a devolver de <b>{sabor_dev}</b> hoy: <b>{max_dev}</b> bolsas</div>', unsafe_allow_html=True)

        if st.button("🔄 Registrar devolución", key="btn_dev"):
            sb_post("devoluciones", {"fecha": str(fecha_dev), "sabor": sabor_dev, "cantidad": cant_dev})
            agregar_stock(sabor_dev, cant_dev)
            st.session_state.ok_dev = True
            time.sleep(0.3)
            st.rerun()

        if st.session_state.ok_dev:
            st.markdown(f'<div class="success-toast">{ICO_CHECK} Devolución registrada. Stock actualizado.</div>', unsafe_allow_html=True)
            st.session_state.ok_dev = False

    with sub4:
        st.markdown(f'<div class="section-label">Regalar bolsa {ICO_GIFT}</div>', unsafe_allow_html=True)
        st.caption("Registra las bolsas que se regalan — se descuentan del carro pero no cuentan como venta.")

        # Solo sabores disponibles en el carro (histórico)
        stock_carro_r = _stock_carro_actual()
        sabores_disp_r = [s for s, v in stock_carro_r.items() if v > 0]

        if not sabores_disp_r:
            st.markdown(f'<div class="warn-box">{ICO_WARN} No hay papas disponibles en el carro para regalar.</div>', unsafe_allow_html=True)
        else:
            sabor_reg = st.selectbox("Sabor", sabores_disp_r, key="sabor_reg")
            disp_reg = int(stock_carro_r.get(sabor_reg, 0))
            cant_reg = st.number_input("Cantidad", min_value=1, max_value=disp_reg, value=1, step=1, key="cant_reg")
            motivo_reg = st.text_input("Motivo (opcional)", placeholder="Ej: Cliente especial, muestra", key="motivo_reg")
            st.markdown(f'<div class="info-box">{ICO_GIFT} Regalando <b>{cant_reg}</b> bolsas de <b>{sabor_reg}</b> · Quedan: <b>{disp_reg - cant_reg}</b></div>', unsafe_allow_html=True)

            if st.button("🎁 Registrar regalo", key="btn_reg"):
                sb_post("ventas", {
                    "fecha": fecha_hoy(), "hora": ahora(), "canal": "Regalo",
                    "vendedor": "Javier & Edison", "sabor": sabor_reg,
                    "cantidad": cant_reg, "total": 0,
                    "cliente": motivo_reg.strip() if motivo_reg.strip() else "Regalo",
                    "factura_id": str(uuid.uuid4())[:8].upper(),
                    "abono": 0, "saldo": 0
                })
                st.session_state.ok_reg = True
                time.sleep(0.3)
                st.rerun()

        if st.session_state.get("ok_reg"):
            st.markdown(f'<div class="success-toast">{ICO_CHECK} Regalo registrado. Descontado del carro.</div>', unsafe_allow_html=True)
            st.session_state.ok_reg = False

        # Historial de regalos del día
        raw_reg = sb_get("ventas", f"select=hora,sabor,cantidad,cliente&fecha=eq.{fecha_hoy()}&canal=eq.Regalo&order=hora.desc")
        if raw_reg:
            st.markdown('<div class="section-label">Regalos de hoy</div>', unsafe_allow_html=True)
            filas_reg = "".join(
                f'<div class="factura-row"><span>{r["hora"]} · {r["sabor"]} × {r["cantidad"]}</span><span>{r["cliente"]}</span></div>'
                for r in raw_reg
            )
            total_regalado = sum(r["cantidad"] for r in raw_reg)
            st.markdown(
                f'<div class="factura-box">{filas_reg}'
                f'<div class="factura-total"><span>Total regalado hoy</span><span>{total_regalado} bolsas</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

    with sub5:
        mostrar_creditos_pendientes("Carro")

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: FÁBRICA
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "fabrica":

    render_venta_canal(CONFIG_FABRICA)

    # Solo admin ve resumen y historial
    if st.session_state.es_admin:
        raw_vf = sb_get("ventas", f"select=total,cantidad,vendedor&fecha=eq.{fecha_hoy()}&canal=in.(Fábrica,Cambio)")
        if raw_vf:
            total_fab_dia  = sum(r["total"]    for r in raw_vf if r["total"] > 0)
            bolsas_fab_dia = sum(r["cantidad"] for r in raw_vf if r["cantidad"] > 0)
            por_vendedor = {}
            for r in raw_vf:
                if r["total"] > 0:
                    v = r["vendedor"]
                    por_vendedor[v] = por_vendedor.get(v, 0) + r["total"]
            st.markdown('<div class="section-label">Resumen del día — Fábrica</div>', unsafe_allow_html=True)
            filas_v = "".join(
                f'<div class="factura-row"><span>{ICO_USER} {v}</span><span><b>{fmt(t)}</b></span></div>'
                for v, t in por_vendedor.items()
            )
            st.markdown(
                f'<div class="factura-box">{filas_v}'
                f'<div class="factura-row"><span>{ICO_CART} Bolsas vendidas hoy</span><span><b>{bolsas_fab_dia}</b></span></div>'
                f'<div class="factura-total"><span>{ICO_DOLLAR} Total a entregar</span><span>{fmt(total_fab_dia)}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: RESUMEN (solo admin)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "recibo":
    registros_recibo = st.session_state.get("recibo_canal_df", [])
    if registros_recibo:
        st.markdown(render_recibo(registros_recibo), unsafe_allow_html=True)

        # Botón imprimir
        _html_btn_imprimir = """
        <div style="text-align:center;margin-top:12px;">
            <button onclick="window.print()" style="
                background:#1565C0;color:white;border:none;
                border-radius:12px;padding:14px 32px;
                font-size:1rem;font-weight:700;cursor:pointer;
                box-shadow:0 4px 12px rgba(21,101,192,0.3);
            ">ICONO_PRINTER Imprimir recibo</button>
        </div>
        <style>
        @media print {
            body > * { display: none !important; }
            .recibo-wrap { display: flex !important; }
            .recibo-ticket {
                width: 58mm !important;
                margin: 0 auto !important;
                box-shadow: none !important;
                font-size: 11px !important;
            }
            .stButton, .stApp header, footer, [data-testid="stToolbar"] {
                display: none !important;
            }
        }
        </style>
        """.replace("ICONO_PRINTER", ICO_PRINTER)
        components.html(_html_btn_imprimir, height=80)

        # Eliminar factura — visible para todos
        if True:
            fid_recibo = registros_recibo[0].get("factura_id", "") if registros_recibo else ""
            canal_recibo = registros_recibo[0].get("canal", "") if registros_recibo else ""

            st.markdown("---")
            st.markdown(f'<div class="section-label">{ICO_WARN} Zona de administrador</div>', unsafe_allow_html=True)

            if st.session_state.get("confirmar_eliminar_fac") == fid_recibo:
                st.markdown('<div class="alert-low">¿Seguro que quieres eliminar esta factura? Esta acción devolverá las bolsas al inventario.</div>', unsafe_allow_html=True)
                col_si, col_no = st.columns(2)
                if col_si.button("✅ Sí, eliminar", key="btn_confirmar_elim"):
                    # Obtener todos los registros de la factura
                    regs = sb_get("ventas", f"select=sabor,cantidad,canal&factura_id=eq.{fid_recibo}")
                    if regs:
                        for r in regs:
                            cant = int(r.get("cantidad", 0))
                            sabor = r.get("sabor", "")
                            canal_r = r.get("canal", "")
                            if cant > 0 and sabor:
                                # Fábrica: devolver al inventario general
                                # Carro: NO tocar inventario general (el stock ya estaba descontado en el cargue)
                                if canal_r in ("Fábrica",):
                                    agregar_stock(sabor, cant)
                        # Eliminar todos los registros de la factura
                        sb_delete("ventas", f"factura_id=eq.{fid_recibo}")
                    st.session_state.confirmar_eliminar_fac = None
                    st.session_state.recibo_canal_df = []
                    st.session_state.vista = st.session_state.get("vista_anterior", "resumen")
                    time.sleep(0.3)
                    st.rerun()
                if col_no.button("✗ Cancelar", key="btn_cancelar_elim"):
                    st.session_state.confirmar_eliminar_fac = None
                    st.rerun()
            else:
                if st.button("🗑️ Eliminar esta factura", key="btn_eliminar_fac"):
                    st.session_state.confirmar_eliminar_fac = fid_recibo
                    st.rerun()
    else:
        st.info("No se encontró la factura seleccionada.")


elif st.session_state.vista == "materia_prima":

    INSUMOS_INFO = [
        ("Papa (bulto)",           "🥔", "bulto",   "mp"),
        ("Aceite (caneca)",        "🛢️", "caneca", "mp"),
        ("ACPM (caneca)",          "⛽", "caneca",  "mp"),
        ("Plátano (bolsa/caja)",   "🍌", "caja",    "mp"),
        ("Salsa de tomate (caja)", "🍅", "caja",    "mp"),
        ("Chicharrón (bulto)",     "🥩", "bulto",   "mp"),
        ("Tocineta (bulto)",       "🥓", "bulto",   "mp"),
    ]
    SABORIZANTES_INFO = [
        ("BBQ",           "🧂", "bolsa", "sab"),
        ("Limón",         "🧂", "bolsa", "sab"),
        ("Sal",           "🧂", "bolsa", "sab"),
        ("Pollo",         "🧂", "bolsa", "sab"),
        ("Parrillada",    "🧂", "bolsa", "sab"),
        ("Chorizo Limón", "🧂", "bolsa", "sab"),
        ("Mayonesa",      "🧂", "bolsa", "sab"),
        ("Queso",         "🧂", "bolsa", "sab"),
        ("Picante",       "🧂", "bolsa", "sab"),
    ]
    EMPAQUES_INFO = [
        ("BBQ emp",            "📦", "kg", "emp"),
        ("Limón emp",          "📦", "kg", "emp"),
        ("Natural",            "📦", "kg", "emp"),
        ("Pollo emp",          "📦", "kg", "emp"),
        ("Chorizo Limón emp",  "📦", "kg", "emp"),
        ("Mayoneza emp",       "📦", "kg", "emp"),
        ("Parrillada emp",     "📦", "kg", "emp"),
        ("Queso emp",          "📦", "kg", "emp"),
        ("Almuerzo Limón emp", "📦", "kg", "emp"),
        ("Almuerzo Pollo emp", "📦", "kg", "emp"),
        ("Almuerzo Picante emp","📦", "kg", "emp"),
        ("Picante emp",        "📦", "kg", "emp"),
        ("Mega emp",           "📦", "kg", "emp"),
        ("Mega Familiar",      "📦", "kg", "emp"),
        ("Fósforo 70g emp",    "📦", "kg", "emp"),
        ("Fósforo 140g emp",   "📦", "kg", "emp"),
        ("Funda Endocenar",    "📦", "kg", "emp"),
    ]
    SABORIZANTES_NAMES = {n for n,_,_,_ in SABORIZANTES_INFO}
    EMPAQUES_NAMES     = {n for n,_,_,_ in EMPAQUES_INFO}

    st.markdown(f'<div class="section-label">Materia Prima e Insumos {ICO_LAYERS}</div>', unsafe_allow_html=True)
    tab_mp1, tab_mp2, tab_mp3, tab_mp4 = st.tabs(["➕ Entrada", "📤 Salida", "💳 Créditos", "📋 Historial"])

    def registrar_entrada_mp(nombre_sel, unidad_sel, cant_mp, prov_mp, precio_mp, abono_mp, saldo_mp, precio_unit_mp=0, fecha_mp=None, es_stock_existente=False):
        if not es_stock_existente:
            if not prov_mp.strip():
                st.markdown(f'<div class="alert-low">{ICO_WARN} Escribe el nombre del proveedor.</div>', unsafe_allow_html=True)
                return False
            if precio_mp == 0:
                st.markdown(f'<div class="alert-low">{ICO_WARN} Ingresa el precio total.</div>', unsafe_allow_html=True)
                return False
        data_mp = {
            "fecha": str(fecha_mp) if fecha_mp else fecha_hoy(), "hora": ahora(),
            "insumo": nombre_sel, "cantidad": float(cant_mp),
            "unidad": unidad_sel, "proveedor": prov_mp.strip() or "Stock existente",
            "precio_total": float(precio_mp), "abono": float(abono_mp),
            "saldo": float(saldo_mp), "estado": "pagado" if saldo_mp == 0 else "pendiente",
            "precio_unitario": float(precio_unit_mp)
        }
        h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
             "Content-Type": "application/json", "Prefer": "return=minimal"}
        try:
            r = requests.post(f"{SUPABASE_URL}/rest/v1/materia_prima", headers=h, json=data_mp, timeout=10)
            if r.ok: return True
            else: st.error(f"Error: {r.status_code} — {r.text}"); return False
        except Exception as e:
            st.error(f"Error: {e}"); return False

    with tab_mp1:
        if not st.session_state.categoria_mp:
            st.markdown('<div class="section-label">¿Qué categoría ingresó?</div>', unsafe_allow_html=True)
            if st.button("🌽  Materia Prima\nPapa, aceite, ACPM, plátano...", key="btn_cat_mp", use_container_width=True):
                st.session_state.categoria_mp = "mp"; st.rerun()
            if st.button("🧪  Saborizantes\nSabores de las papas", key="btn_cat_sab", use_container_width=True):
                st.session_state.categoria_mp = "sab"; st.rerun()
            if st.button("📦  Empaque\nBolsas y fundas en kg", key="btn_cat_emp", use_container_width=True):
                st.session_state.categoria_mp = "emp"; st.rerun()

        elif not st.session_state.insumo_sel:
            cats = {"mp": INSUMOS_INFO, "sab": SABORIZANTES_INFO, "emp": EMPAQUES_INFO}
            labels = {"mp": "Materia Prima", "sab": "Saborizantes", "emp": "Empaque"}
            st.markdown(f'<div class="section-label">¿Qué {labels[st.session_state.categoria_mp]} ingresó?</div>', unsafe_allow_html=True)
            for nombre, icono, unidad, cat in cats[st.session_state.categoria_mp]:
                if st.button(f"{icono}  {nombre}", key=f"btn_ins_{nombre}", use_container_width=True):
                    st.session_state.insumo_sel = (nombre, unidad, cat); st.rerun()
            if st.button("← Volver", key="btn_volver_cat"):
                st.session_state.categoria_mp = None; st.rerun()

        else:
            nombre_sel, unidad_sel, cat_sel = st.session_state.insumo_sel
            con_credito = cat_sel != "emp"
            st.markdown(f'<div class="section-label">Entrada — {nombre_sel}</div>', unsafe_allow_html=True)
            fecha_mp = st.date_input("Fecha de la entrada", value=datetime.now(COL_TZ).date(), max_value=datetime.now(COL_TZ).date(), key="fecha_mp")
            if fecha_mp != datetime.now(COL_TZ).date():
                st.markdown(f'<div class="warn-box">{ICO_CALENDAR} Se registrará con fecha {fecha_mp}, no con la de hoy.</div>', unsafe_allow_html=True)
            cant_mp        = st.number_input(f"Cantidad ({unidad_sel})", min_value=0.1, max_value=9999.0, value=1.0, step=0.5, key="cant_mp")

            ya_tengo_mp = st.checkbox(
                "📦 Ya tengo este insumo (no es una compra nueva)",
                key="ya_tengo_mp",
                help="Úsalo para sumar al stock materia prima que ya tenías. No se descuenta de caja ni queda como deuda con el proveedor."
            )

            prov_mp = st.text_input(
                "Proveedor (opcional)" if ya_tengo_mp else "Proveedor",
                placeholder="Ej: Stock existente" if ya_tengo_mp else "Ej: Distribuidora La 14",
                key="prov_mp"
            )
            precio_unit_mp = st.number_input(
                f"Precio unitario ($ por {unidad_sel})" + (" — opcional" if ya_tengo_mp else ""),
                min_value=0, value=0, step=1000, key="precio_unit_mp"
            )
            precio_mp = round(precio_unit_mp * cant_mp)
            if precio_mp > 0:
                nota_caja = " (solo de referencia, no se cobra en caja)" if ya_tengo_mp else ""
                st.markdown(f'<div class="info-box">{ICO_DOLLAR} {cant_mp} × {fmt(precio_unit_mp)} = <b>{fmt(precio_mp)}</b> total{nota_caja}</div>', unsafe_allow_html=True)

            if ya_tengo_mp:
                abono_mp = 0
                saldo_mp = 0
                st.markdown(f'<div class="info-box">{ICO_CHECK} Se sumará al stock. No se descuenta de caja ni queda como deuda con proveedor.</div>', unsafe_allow_html=True)
            elif con_credito:
                abono_mp = st.number_input("Abono inicial ($)", min_value=0, max_value=max(0, precio_mp), value=0, step=1000, key="abono_mp")
                saldo_mp = max(0, precio_mp - abono_mp)
                if precio_mp > 0:
                    if abono_mp >= precio_mp:
                        st.markdown(f'<div class="info-box">{ICO_CHECK} Pago completo</div>', unsafe_allow_html=True)
                    elif abono_mp > 0:
                        st.markdown(f'<div class="warn-box">{ICO_CLIPBOARD} Debe: <b>{fmt(saldo_mp)}</b></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="warn-box">{ICO_CLIPBOARD} Fiado: <b>{fmt(precio_mp)}</b></div>', unsafe_allow_html=True)
            else:
                abono_mp = precio_mp; saldo_mp = 0
            col1, col2 = st.columns(2)
            if col1.button("✅ Registrar", key="btn_mp"):
                if registrar_entrada_mp(nombre_sel, unidad_sel, cant_mp, prov_mp, precio_mp, abono_mp, saldo_mp, precio_unit_mp, fecha_mp, es_stock_existente=ya_tengo_mp):
                    st.session_state.ok_mp = True
                    st.session_state.insumo_sel = None
                    st.session_state.categoria_mp = None
                    time.sleep(0.3); st.rerun()
            if col2.button("← Cambiar", key="btn_cambiar_ins"):
                st.session_state.insumo_sel = None; st.rerun()

            st.markdown(f'<div class="section-label">Entradas de {nombre_sel} este mes</div>', unsafe_allow_html=True)
            primer_dia = datetime.now(COL_TZ).date().replace(day=1)
            hoy_ins = datetime.now(COL_TZ).date()
            raw_ins_mes = sb_get("materia_prima",
                f"select=fecha,hora,cantidad,precio_unitario,proveedor&insumo=eq.{requests.utils.quote(nombre_sel)}&fecha=gte.{primer_dia}&fecha=lte.{hoy_ins}&order=fecha.desc,hora.desc") or []
            if raw_ins_mes:
                total_cant_mes = sum(float(r["cantidad"]) for r in raw_ins_mes)
                st.caption(f"Total ingresado este mes: {total_cant_mes:.1f} {unidad_sel}")
                df_ins_mes = pd.DataFrame(raw_ins_mes)
                df_ins_mes["precio_unitario"] = df_ins_mes["precio_unitario"].apply(lambda x: fmt(x) if x else "—")
                df_ins_mes.columns = ["Fecha", "Hora", f"Cantidad ({unidad_sel})", "Precio unitario", "Proveedor"]
                st.dataframe(df_ins_mes, use_container_width=True, hide_index=True)
            else:
                st.caption(f"Aún no hay entradas de {nombre_sel} este mes.")

        if st.session_state.get("ok_mp"):
            st.markdown(f'<div class="success-toast">{ICO_CHECK} Entrada registrada.</div>', unsafe_allow_html=True)
            st.session_state.ok_mp = False

    with tab_mp2:
        st.markdown('<div class="section-label">Registrar salida (uso en producción)</div>', unsafe_allow_html=True)
        cat_sal = st.selectbox("Categoría", ["🌽 Materia Prima", "🧪 Saborizantes", "📦 Empaque"], key="cat_sal")
        if "Materia Prima" in cat_sal:
            opciones_sal = [n for n,_,_,_ in INSUMOS_INFO]
            unidades_sal = {n: u for n,_,u,_ in INSUMOS_INFO}
            cat_key = "mp"
        elif "Saborizantes" in cat_sal:
            opciones_sal = [n for n,_,_,_ in SABORIZANTES_INFO]
            unidades_sal = {n: u for n,_,u,_ in SABORIZANTES_INFO}
            cat_key = "sab"
        else:
            opciones_sal = [n for n,_,_,_ in EMPAQUES_INFO]
            unidades_sal = {n: u for n,_,u,_ in EMPAQUES_INFO}
            cat_key = "emp"
        insumo_sal = st.selectbox("Insumo", opciones_sal, key="insumo_sal")
        unidad_sal = unidades_sal[insumo_sal]

        # Calcular stock disponible de ese insumo
        raw_ent_sal = sb_get("materia_prima", f"select=cantidad&insumo=eq.{requests.utils.quote(insumo_sal)}") or []
        raw_sal_sal = sb_get("salidas_mp",    f"select=cantidad&insumo=eq.{requests.utils.quote(insumo_sal)}") or []
        total_ent_sal = sum(float(r["cantidad"]) for r in raw_ent_sal)
        total_sal_sal = sum(float(r["cantidad"]) for r in raw_sal_sal)
        stock_disp_sal = max(0, total_ent_sal - total_sal_sal)

        if stock_disp_sal == 0:
            st.markdown(f'<div class="alert-low">{ICO_DOT_RED} No hay stock disponible de <b>{insumo_sal}</b>. Registra una entrada primero.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box">{ICO_PACKAGE} Stock disponible de <b>{insumo_sal}</b>: <b>{stock_disp_sal:.1f} {unidad_sal}</b></div>', unsafe_allow_html=True)

        cant_sal = st.number_input(f"Cantidad ({unidad_sal})", min_value=0.1,
                                    max_value=max(0.1, stock_disp_sal),
                                    value=min(1.0, max(0.1, stock_disp_sal)),
                                    step=0.5, key="cant_sal")
        motivo_sal = st.text_input("Motivo", value="Producción", key="motivo_sal")

        if st.button("📤 Registrar salida", key="btn_sal", disabled=(stock_disp_sal == 0)):
            h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                 "Content-Type": "application/json", "Prefer": "return=minimal"}
            data_sal = {"fecha": fecha_hoy(), "hora": ahora(), "insumo": insumo_sal,
                        "categoria": cat_key, "cantidad": float(cant_sal),
                        "unidad": unidad_sal, "motivo": motivo_sal.strip() or "Producción"}
            try:
                r = requests.post(f"{SUPABASE_URL}/rest/v1/salidas_mp", headers=h, json=data_sal, timeout=10)
                if r.ok:
                    st.markdown(f'<div class="success-toast">{ICO_CHECK} Salida registrada.</div>', unsafe_allow_html=True)
                    time.sleep(0.3); st.rerun()
                else:
                    st.error(f"Error: {r.status_code} — {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab_mp3:
        raw_pend = sb_get("materia_prima", "select=*&estado=eq.pendiente&order=fecha.desc") or []
        pend_mp  = [r for r in raw_pend if r["insumo"] not in SABORIZANTES_NAMES and r["insumo"] not in EMPAQUES_NAMES]
        pend_sab = [r for r in raw_pend if r["insumo"] in SABORIZANTES_NAMES]

        def mostrar_creditos_mp(lista, icono):
            if not lista:
                st.info("No hay créditos pendientes."); return
            total = sum(float(r["saldo"]) for r in lista)
            st.markdown(f'<div class="warn-box">{ICO_CARD} Total pendiente: <b>{fmt(total)}</b></div>', unsafe_allow_html=True)
            for r in lista:
                saldo_r = float(r["saldo"])
                st.markdown(
                    f'<div class="factura-box"><div class="factura-header">{icono} {r["insumo"]} · {r["proveedor"]}</div>'
                    f'<div class="factura-row"><span>Fecha</span><span>{r["fecha"]}</span></div>'
                    f'<div class="factura-row"><span>Cantidad</span><span>{r["cantidad"]} {r["unidad"]}</span></div>'
                    f'<div class="factura-row"><span>Total</span><span>{fmt(r["precio_total"])}</span></div>'
                    f'<div class="factura-row"><span>Abonado</span><span>{fmt(r["abono"])}</span></div>'
                    f'<div class="factura-total"><span>Saldo</span><span>{fmt(saldo_r)}</span></div></div>',
                    unsafe_allow_html=True
                )
                col_a, col_b = st.columns([3, 1])
                nv = col_a.number_input("Abono ($)", min_value=0, max_value=int(saldo_r), value=int(saldo_r), step=1000, key=f"abono_pend_mp_{r['id']}")
                if col_b.button("✅ Pagar", key=f"btn_pagar_mp_{r['id']}"):
                    ns = max(0, saldo_r - nv)
                    sb_patch("materia_prima", f"id=eq.{r['id']}", {"abono": float(r["abono"])+nv, "saldo": ns, "estado": "pagado" if ns==0 else "pendiente"})
                    time.sleep(0.3); st.rerun()

        sc1, sc2 = st.tabs(["🌽 Materia Prima", "🧪 Saborizantes"])
        with sc1:
            st.markdown('<div class="section-label">Créditos — Materia Prima</div>', unsafe_allow_html=True)
            mostrar_creditos_mp(pend_mp, ICO_LAYERS)
        with sc2:
            st.markdown('<div class="section-label">Créditos — Saborizantes</div>', unsafe_allow_html=True)
            mostrar_creditos_mp(pend_sab, ICO_FLASK)

    with tab_mp4:
        st.markdown('<div class="section-label">Resumen del período</div>', unsafe_allow_html=True)
        col_f1, col_f2 = st.columns(2)
        f_ini_mp = col_f1.date_input("Desde", value=datetime.now(COL_TZ).date().replace(day=1), key="f_ini_mp")
        f_fin_mp = col_f2.date_input("Hasta", value=datetime.now(COL_TZ).date(), key="f_fin_mp")

        raw_ent = sb_get("materia_prima", f"select=*&fecha=gte.{f_ini_mp}&fecha=lte.{f_fin_mp}&order=fecha.desc") or []
        raw_sal = sb_get("salidas_mp",    f"select=*&fecha=gte.{f_ini_mp}&fecha=lte.{f_fin_mp}&order=fecha.desc") or []

        resumen = {}
        for r in raw_ent:
            k = r["insumo"]
            pu = float(r.get("precio_unitario", 0))
            cant = float(r["cantidad"])
            gasto_calc = pu * cant if pu > 0 else float(r.get("precio_total", 0))
            if k not in resumen:
                resumen[k] = {"entradas": 0, "salidas": 0, "unidad": r["unidad"], "gasto": 0}
            resumen[k]["entradas"] += cant
            resumen[k]["gasto"]    += gasto_calc
        for r in raw_sal:
            k = r["insumo"]
            if k not in resumen:
                resumen[k] = {"entradas": 0, "salidas": 0, "unidad": r["unidad"], "gasto": 0}
            resumen[k]["salidas"] += float(r["cantidad"])

        def tabla_resumen(data, titulo, icono, raw_ent_cat, raw_sal_cat):
            if not data and not raw_ent_cat and not raw_sal_cat: return
            st.markdown(f'<div class="section-label">{icono} {titulo}</div>', unsafe_allow_html=True)
            if data:
                # Promedio ponderado por insumo: suma(cant*precio_unit) / suma(cant)
                prom_pond = {}
                for r in raw_ent_cat:
                    k = r["insumo"]
                    pu = float(r.get("precio_unitario", 0))
                    cant = float(r.get("cantidad", 0))
                    if pu > 0 and cant > 0:
                        if k not in prom_pond:
                            prom_pond[k] = {"total_costo": 0, "total_cant": 0}
                        prom_pond[k]["total_costo"] += pu * cant
                        prom_pond[k]["total_cant"]  += cant

                filas_res = []
                for k, v in data.items():
                    d = prom_pond.get(k, {"total_costo": 0, "total_cant": 0})
                    pu_prom = round(d["total_costo"] / d["total_cant"]) if d["total_cant"] > 0 else 0
                    costo_consumido = round(v["salidas"] * pu_prom) if pu_prom > 0 else 0
                    stock_val = round((v["entradas"] - v["salidas"]) * pu_prom) if pu_prom > 0 else 0
                    filas_res.append({
                        "Insumo": k,
                        "Entradas": v["entradas"],
                        "Salidas": v["salidas"],
                        "Stock": round(v["entradas"]-v["salidas"], 1),
                        "Precio prom. pond.": fmt(pu_prom) if pu_prom > 0 else "—",
                        "Costo consumido": fmt(costo_consumido) if costo_consumido > 0 else "—",
                        "Inventario total": fmt(stock_val) if stock_val > 0 else "—",
                    })
                st.dataframe(pd.DataFrame(filas_res), use_container_width=True, hide_index=True)
                # Nota explicativa
                st.caption("💡 Precio promedio ponderado: promedio de todos los lotes del período, ponderado por cantidad ingresada.")
            else:
                st.info("No hay registros en este período.")

        if resumen or raw_ent or raw_sal:
            res_mp  = {k: v for k, v in resumen.items() if k not in SABORIZANTES_NAMES and k not in EMPAQUES_NAMES}
            res_sab = {k: v for k, v in resumen.items() if k in SABORIZANTES_NAMES}
            res_emp = {k: v for k, v in resumen.items() if k in EMPAQUES_NAMES}
            ent_mp  = [r for r in raw_ent if r["insumo"] not in SABORIZANTES_NAMES and r["insumo"] not in EMPAQUES_NAMES]
            ent_sab = [r for r in raw_ent if r["insumo"] in SABORIZANTES_NAMES]
            ent_emp = [r for r in raw_ent if r["insumo"] in EMPAQUES_NAMES]
            sal_mp  = [r for r in raw_sal if r["categoria"] == "mp"]
            sal_sab = [r for r in raw_sal if r["categoria"] == "sab"]
            sal_emp = [r for r in raw_sal if r["categoria"] == "emp"]

            sh1, sh2, sh3 = st.tabs(["🌽 Materia Prima", "🧪 Saborizantes", "📦 Empaque"])
            with sh1:
                tabla_resumen(res_mp,  "Materia Prima", ICO_LAYERS, ent_mp,  sal_mp)
            with sh2:
                tabla_resumen(res_sab, "Saborizantes",  ICO_FLASK, ent_sab, sal_sab)
            with sh3:
                tabla_resumen(res_emp, "Empaque",       ICO_PACKAGE, ent_emp, sal_emp)
        else:
            st.info("No hay registros en ese período.")

elif st.session_state.vista == "caja":
    st.markdown(f'<div class="section-label">{ICO_DOLLAR} Caja</div>', unsafe_allow_html=True)
    tab_caja1, tab_caja2, tab_caja3 = st.tabs(["📊 Resumen", "➕ Registrar egreso", "📋 Historial"])

    # Fechas del período
    hoy_caja = datetime.now(COL_TZ).date()
    primer_dia_caja = hoy_caja.replace(day=1)

    with tab_caja1:
        st.markdown('<div class="section-label">Resumen de caja</div>', unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        f_ini_caja = col_c1.date_input("Desde", value=primer_dia_caja, key="f_ini_caja")
        f_fin_caja = col_c2.date_input("Hasta", value=hoy_caja, key="f_fin_caja")

        # INGRESOS — ventas pagadas (total - saldo = abonado)
        with ThreadPoolExecutor(max_workers=5) as ex:
            f_vf = ex.submit(sb_get, "ventas", f"select=fecha,total,abono,saldo,canal,cliente,factura_id&fecha=gte.{f_ini_caja}&fecha=lte.{f_fin_caja}&canal=in.(Fábrica,Carro)&order=fecha.desc")
            f_ab = ex.submit(sb_get, "creditos", f"select=fecha,cliente,canal,total,pagado&fecha=gte.{f_ini_caja}&fecha=lte.{f_fin_caja}&estado=eq.pagado&order=fecha.desc")
            f_mp = ex.submit(sb_get, "materia_prima", f"select=fecha,insumo,proveedor,precio_total,abono&fecha=gte.{f_ini_caja}&fecha=lte.{f_fin_caja}&order=fecha.desc")
            f_cxc = ex.submit(sb_get, "ventas", "select=factura_id,cliente,canal,total,abono,saldo&saldo=gt.0&order=fecha.desc")
            f_cxp = ex.submit(sb_get, "materia_prima", "select=id,insumo,proveedor,precio_total,abono,saldo&estado=eq.pendiente&order=fecha.desc")
            f_cxc_m = ex.submit(sb_get, "creditos", "select=id,cliente,canal,total,pagado&estado=eq.pendiente")
        raw_ventas_caja = f_vf.result() or []
        raw_creditos_cobrados = f_ab.result() or []
        raw_mp_pagos = f_mp.result() or []
        raw_egresos = sb_get("caja_egresos", f"select=*&fecha=gte.{f_ini_caja}&fecha=lte.{f_fin_caja}&order=fecha.desc") or []
        raw_cxc = f_cxc.result() or []
        raw_cxp = f_cxp.result() or []
        raw_cxc_m = f_cxc_m.result() or []

        # Calcular ingresos — una sola entrada por factura (la primera fila de cada una)
        facturas_vistas = {}
        for r in raw_ventas_caja:
            fid = r.get("factura_id", "")
            if fid and fid not in facturas_vistas:
                facturas_vistas[fid] = float(r.get("abono", 0))
        ingresos_ventas = sum(facturas_vistas.values())

        # Egresos: pagos de materia prima + gastos varios
        egresos_mp = sum(float(r["abono"]) for r in raw_mp_pagos)
        egresos_gastos = sum(float(r["valor"]) for r in raw_egresos)
        total_egresos = egresos_mp + egresos_gastos

        saldo_caja = ingresos_ventas - total_egresos

        # Cuentas por cobrar a clientes (créditos de ventas, saldo pendiente) — una sola vez por factura
        facturas_cxc = {}
        for r in raw_cxc:
            fid = r.get("factura_id", "")
            if fid and fid not in facturas_cxc:
                facturas_cxc[fid] = float(r.get("saldo", 0))
        cuentas_por_cobrar_manual = sum(max(0.0, float(r["total"]) - float(r.get("pagado", 0) or 0)) for r in raw_cxc_m)
        cuentas_por_cobrar = sum(facturas_cxc.values()) + cuentas_por_cobrar_manual

        # Cuentas por pagar a proveedores (materia prima/insumos pendientes de pago)
        cuentas_por_pagar = sum(float(r.get("saldo", 0)) for r in raw_cxp)

        # Tarjetas resumen
        color_saldo = "metric-green" if saldo_caja >= 0 else "metric-red"
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-box metric-blue"><div class="val">{fmt(ingresos_ventas)}</div><div class="lbl">Ingresos</div></div>
            <div class="metric-box metric-yellow"><div class="val">{fmt(total_egresos)}</div><div class="lbl">Egresos</div></div>
            <div class="metric-box {color_saldo}"><div class="val">{fmt(saldo_caja)}</div><div class="lbl">Saldo caja</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="section-label">{ICO_RECEIPT} Para contabilidad — créditos vigentes</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-box metric-blue"><div class="val">{fmt(cuentas_por_cobrar)}</div><div class="lbl">Cuentas por cobrar (clientes)</div></div>
            <div class="metric-box metric-red"><div class="val">{fmt(cuentas_por_pagar)}</div><div class="lbl">Cuentas por pagar (proveedores)</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Detalle egresos
        if egresos_mp > 0 or egresos_gastos > 0:
            st.markdown('<div class="section-label">Detalle egresos</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="factura-box">'
                f'<div class="factura-row"><span>{ICO_LAYERS} Pagos materia prima</span><span><b>{fmt(egresos_mp)}</b></span></div>'
                f'<div class="factura-row"><span>{ICO_NOTE} Gastos varios</span><span><b>{fmt(egresos_gastos)}</b></span></div>'
                f'<div class="factura-total"><span>Total egresos</span><span>{fmt(total_egresos)}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

    with tab_caja2:
        st.markdown('<div class="section-label">Registrar egreso / gasto</div>', unsafe_allow_html=True)
        concepto_eg = st.text_input("Concepto", placeholder="Ej: Pago arriendo, gas, luz...", key="concepto_eg")
        cat_eg = st.selectbox("Categoría", ["Servicios", "Arriendo", "Transporte", "Mantenimiento", "Salario", "Otro"], key="cat_eg")
        valor_eg = st.number_input("Valor ($)", min_value=0, value=0, step=1000, key="valor_eg")

        if st.button("✅ Registrar egreso", key="btn_eg"):
            if not concepto_eg.strip():
                st.markdown(f'<div class="alert-low">{ICO_WARN} Escribe el concepto del egreso.</div>', unsafe_allow_html=True)
            elif valor_eg == 0:
                st.markdown(f'<div class="alert-low">{ICO_WARN} Ingresa el valor.</div>', unsafe_allow_html=True)
            else:
                h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"}
                data_eg = {"fecha": fecha_hoy(), "hora": ahora(),
                           "concepto": concepto_eg.strip(), "valor": float(valor_eg), "categoria": cat_eg}
                try:
                    r_eg = requests.post(f"{SUPABASE_URL}/rest/v1/caja_egresos", headers=h, json=data_eg, timeout=10)
                    if r_eg.ok:
                        st.markdown(f'<div class="success-toast">{ICO_CHECK} Egreso registrado.</div>', unsafe_allow_html=True)
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.error(f"Error: {r_eg.status_code} — {r_eg.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab_caja3:
        st.markdown('<div class="section-label">Historial de movimientos</div>', unsafe_allow_html=True)
        col_h1, col_h2 = st.columns(2)
        f_ini_h = col_h1.date_input("Desde", value=primer_dia_caja, key="f_ini_h")
        f_fin_h = col_h2.date_input("Hasta", value=hoy_caja, key="f_fin_h")

        movimientos = []

        # Ingresos por ventas
        raw_v_h = sb_get("ventas", f"select=fecha,hora,canal,cliente,factura_id,abono,saldo&fecha=gte.{f_ini_h}&fecha=lte.{f_fin_h}&canal=in.(Fábrica,Carro)&order=fecha.desc,hora.desc") or []
        facturas_h = set()
        for r in raw_v_h:
            fid = r.get("factura_id", "")
            if fid and fid not in facturas_h and float(r.get("abono", 0)) > 0:
                facturas_h.add(fid)
                movimientos.append({
                    "Fecha": r["fecha"], "Hora": r["hora"],
                    "Concepto": f'Venta {r["canal"]} — {r["cliente"]}',
                    "Categoría": "Ingreso ventas",
                    "Ingreso": fmt(r["abono"]), "Egreso": "—"
                })

        # Egresos materia prima
        raw_mp_h = sb_get("materia_prima", f"select=fecha,hora,insumo,proveedor,abono&fecha=gte.{f_ini_h}&fecha=lte.{f_fin_h}&abono=gt.0&order=fecha.desc") or []
        for r in raw_mp_h:
            movimientos.append({
                "Fecha": r["fecha"], "Hora": r.get("hora",""),
                "Concepto": f'{r["insumo"]} — {r["proveedor"]}',
                "Categoría": "Pago MP",
                "Ingreso": "—", "Egreso": fmt(r["abono"])
            })

        # Egresos gastos varios
        raw_eg_h = sb_get("caja_egresos", f"select=*&fecha=gte.{f_ini_h}&fecha=lte.{f_fin_h}&order=fecha.desc") or []
        for r in raw_eg_h:
            movimientos.append({
                "Fecha": r["fecha"], "Hora": r["hora"],
                "Concepto": r["concepto"],
                "Categoría": r["categoria"],
                "Ingreso": "—", "Egreso": fmt(r["valor"])
            })

        if movimientos:
            movimientos.sort(key=lambda x: (x["Fecha"], x["Hora"]), reverse=True)
            st.dataframe(pd.DataFrame(movimientos), use_container_width=True, hide_index=True)
        else:
            st.info("No hay movimientos en ese período.")

elif st.session_state.vista == "resumen" and st.session_state.es_admin:
    sub_r1, sub_r2, sub_r3, sub_r4 = st.tabs(["Hoy", "Por fechas", "📅 Mes", "💾 Exportar"])

    with sub_r1:
        st.markdown('<div class="section-label">Resumen del día</div>', unsafe_allow_html=True)
        raw_vt = sb_get("ventas", f"select=*&fecha=eq.{fecha_hoy()}&order=hora.asc")
        if not raw_vt:
            st.info("Aún no hay ventas hoy.")
        else:
            df_vt = pd.DataFrame(raw_vt)

            # Dinero realmente cobrado y pendiente en créditos — una sola vez por
            # factura (abono/saldo quedan repetidos en cada línea de una misma factura).
            facturas_hoy = {}
            for r in raw_vt:
                fid = r.get("factura_id", "")
                if fid and fid not in facturas_hoy:
                    facturas_hoy[fid] = {
                        "canal": r.get("canal", ""),
                        "abono": float(r.get("abono", 0)),
                        "saldo": float(r.get("saldo", 0)),
                    }
            cobrado_fab   = sum(f["abono"] for f in facturas_hoy.values() if f["canal"] == "Fábrica")
            cobrado_carro = sum(f["abono"] for f in facturas_hoy.values() if f["canal"] == "Carro")
            pendiente_hoy = sum(f["saldo"] for f in facturas_hoy.values())

            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-blue"><div class="val">{fmt(cobrado_fab)}</div><div class="lbl">Fábrica</div></div>
                <div class="metric-box metric-yellow"><div class="val">{fmt(cobrado_carro)}</div><div class="lbl">Carro</div></div>
                <div class="metric-box metric-green"><div class="val">{fmt(cobrado_fab+cobrado_carro)}</div><div class="lbl">Total cobrado</div></div>
                <div class="metric-box metric-red"><div class="val">{fmt(pendiente_hoy)}</div><div class="lbl">Pendiente en créditos</div></div>
            </div>""", unsafe_allow_html=True)
            st.caption("💰 Estas tarjetas muestran solo el dinero cobrado. Los créditos sin pagar aparecen aparte, en \"Pendiente en créditos\".")

            st.markdown('<div class="section-label">Por sabor</div>', unsafe_allow_html=True)
            por_sabor = df_vt.groupby("sabor").agg(bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
            por_sabor = por_sabor.sort_values("total", ascending=False)

            chart_data = por_sabor.set_index("sabor")["bolsas"]
            grafica_barras_sabor(por_sabor["sabor"].tolist(), por_sabor["bolsas"].tolist(), "bolsas vendidas")

            por_sabor["total"] = por_sabor["total"].apply(fmt)
            por_sabor.columns = ["Sabor","Bolsas","Total $"]
            st.dataframe(por_sabor, use_container_width=True, hide_index=True)

            st.markdown('<div class="section-label">Facturas fábrica</div>', unsafe_allow_html=True)
            st.caption("Toca una fila para ver el recibo completo.")
            df_fab = df_vt[df_vt["canal"]=="Fábrica"]
            if not df_fab.empty:
                mostrar_facturas_seleccionables(df_fab, "hoy")

            st.markdown('<div class="section-label">Facturas carro</div>', unsafe_allow_html=True)
            st.caption("Toca una fila para ver el recibo completo.")
            df_carro_resumen = df_vt[df_vt["canal"]=="Carro"]
            if not df_carro_resumen.empty:
                mostrar_facturas_seleccionables(df_carro_resumen, "hoy_carro")

    with sub_r2:
        st.markdown('<div class="section-label">Consultar por fechas</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        f_ini = col_a.date_input("Desde", value=date(datetime.now(COL_TZ).year, datetime.now(COL_TZ).month, 1), key="f_ini")
        f_fin = col_b.date_input("Hasta", value=datetime.now(COL_TZ).date(), key="f_fin")
        raw_rango = sb_get("ventas", f"select=*&fecha=gte.{f_ini}&fecha=lte.{f_fin}&order=fecha.asc")

        if not raw_rango:
            st.info("No hay ventas en ese rango.")
        else:
            df_r = pd.DataFrame(raw_rango)
            bolsas_r = int(df_r["cantidad"].sum())
            dias_r   = df_r["fecha"].nunique()

            # Dinero realmente cobrado y pendiente en créditos — una sola vez por
            # factura (abono/saldo quedan repetidos en cada línea de una misma factura).
            facturas_rango = {}
            for r in raw_rango:
                fid = r.get("factura_id", "")
                if fid and fid not in facturas_rango:
                    facturas_rango[fid] = {
                        "abono": float(r.get("abono", 0)),
                        "saldo": float(r.get("saldo", 0)),
                    }
            cobrado_r   = sum(f["abono"] for f in facturas_rango.values())
            pendiente_r = sum(f["saldo"] for f in facturas_rango.values())

            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-green"><div class="val">{fmt(cobrado_r)}</div><div class="lbl">Cobrado</div></div>
                <div class="metric-box metric-blue"><div class="val">{bolsas_r}</div><div class="lbl">Bolsas</div></div>
                <div class="metric-box metric-yellow"><div class="val">{dias_r}</div><div class="lbl">Días</div></div>
                <div class="metric-box metric-red"><div class="val">{fmt(pendiente_r)}</div><div class="lbl">Pendiente en créditos</div></div>
            </div>""", unsafe_allow_html=True)
            st.caption("💰 \"Cobrado\" es el dinero que efectivamente entró. Los créditos sin pagar se muestran aparte.")

            st.markdown('<div class="section-label">Por día</div>', unsafe_allow_html=True)
            por_dia = df_r.groupby("fecha").agg(bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
            por_dia["total"] = por_dia["total"].apply(fmt)
            por_dia.columns  = ["Fecha","Bolsas","Total $"]
            st.dataframe(por_dia, use_container_width=True, hide_index=True)

            st.markdown('<div class="section-label">Por canal</div>', unsafe_allow_html=True)
            por_canal = df_r.groupby("canal").agg(bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
            por_canal["total"] = por_canal["total"].apply(fmt)
            por_canal.columns  = ["Canal","Bolsas","Total $"]
            st.dataframe(por_canal, use_container_width=True, hide_index=True)

            # Facturas individuales del rango, en formato tabla
            df_fab_r = df_r[df_r["canal"]=="Fábrica"]
            if not df_fab_r.empty:
                st.markdown('<div class="section-label">Facturas fábrica del rango</div>', unsafe_allow_html=True)
                st.caption("Toca una fila para ver el recibo completo.")
                mostrar_facturas_seleccionables(df_fab_r, "rango")

            df_carro_r = df_r[df_r["canal"]=="Carro"]
            if not df_carro_r.empty:
                st.markdown('<div class="section-label">Facturas carro del rango</div>', unsafe_allow_html=True)
                st.caption("Toca una fila para ver el recibo completo.")
                mostrar_facturas_seleccionables(df_carro_r, "rango_carro")

    with sub_r3:
        st.markdown('<div class="section-label">Reporte del mes actual</div>', unsafe_allow_html=True)
        hoy_dt = datetime.now(COL_TZ)
        primer_dia = date(hoy_dt.year, hoy_dt.month, 1)
        ultimo_dia = hoy_dt.date()
        nombre_mes = hoy_dt.strftime("%B %Y").capitalize()
        st.caption(f"Resumen automático de {nombre_mes}")

        raw_mes = sb_get("ventas", f"select=*&fecha=gte.{primer_dia}&fecha=lte.{ultimo_dia}")
        raw_prod_mes = sb_get("produccion", f"select=cantidad&fecha=gte.{primer_dia}&fecha=lte.{ultimo_dia}")

        if not raw_mes:
            st.info("Aún no hay ventas este mes.")
        else:
            df_mes = pd.DataFrame(raw_mes)
            bolsas_mes  = int(df_mes["cantidad"].sum())
            dias_mes    = df_mes["fecha"].nunique()
            prod_mes    = sum(r["cantidad"] for r in raw_prod_mes) if raw_prod_mes else 0

            # Dinero realmente cobrado y pendiente en créditos — una sola vez por
            # factura (abono/saldo quedan repetidos en cada línea de una misma factura).
            facturas_mes = {}
            for r in raw_mes:
                fid = r.get("factura_id", "")
                if fid and fid not in facturas_mes:
                    facturas_mes[fid] = {
                        "abono": float(r.get("abono", 0)),
                        "saldo": float(r.get("saldo", 0)),
                    }
            cobrado_mes   = sum(f["abono"] for f in facturas_mes.values())
            pendiente_mes = sum(f["saldo"] for f in facturas_mes.values())
            promedio_dia  = cobrado_mes / dias_mes if dias_mes > 0 else 0

            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-green"><div class="val">{fmt(cobrado_mes)}</div><div class="lbl">Cobrado del mes</div></div>
                <div class="metric-box metric-blue"><div class="val">{bolsas_mes}</div><div class="lbl">Bolsas vendidas</div></div>
                <div class="metric-box metric-yellow"><div class="val">{fmt(promedio_dia)}</div><div class="lbl">Promedio diario</div></div>
                <div class="metric-box metric-red"><div class="val">{fmt(pendiente_mes)}</div><div class="lbl">Pendiente en créditos</div></div>
            </div>""", unsafe_allow_html=True)
            st.caption("💰 \"Cobrado\" es el dinero que efectivamente entró. Los créditos sin pagar se muestran aparte.")

            st.markdown(f'<div class="info-box">{ICO_PACKAGE} Producción total del mes: <b>{prod_mes} bolsas</b></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-label">Sabor más vendido</div>', unsafe_allow_html=True)
            top_sabores = df_mes.groupby("sabor")["cantidad"].sum().reset_index().sort_values("cantidad", ascending=False)
            if not top_sabores.empty:
                top1 = top_sabores.iloc[0]
                st.markdown(f'<div class="info-box">{ICO_TROPHY} <b>{top1["sabor"]}</b> con {int(top1["cantidad"])} bolsas vendidas</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-label">Evolución de ventas en el mes</div>', unsafe_allow_html=True)
            por_dia_mes = df_mes.groupby("fecha")["total"].sum().reset_index()
            grafica_linea_ventas(por_dia_mes["fecha"].tolist(), por_dia_mes["total"].tolist())

            st.markdown('<div class="section-label">Tendencia por sabor</div>', unsafe_allow_html=True)
            top_sabores.columns = ["Sabor","Bolsas"]
            st.dataframe(top_sabores, use_container_width=True, hide_index=True)

    with sub_r4:
        st.markdown('<div class="section-label">Exportar datos</div>', unsafe_allow_html=True)
        col_e1, col_e2 = st.columns(2)
        f_exp_ini = col_e1.date_input("Desde", value=date(datetime.now(COL_TZ).year, datetime.now(COL_TZ).month, 1), key="f_exp_ini")
        f_exp_fin = col_e2.date_input("Hasta", value=datetime.now(COL_TZ).date(), key="f_exp_fin")

        def generar_pdf(titulo, df, nombre_archivo):
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            import io

            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                                    leftMargin=1*cm, rightMargin=1*cm,
                                    topMargin=1.5*cm, bottomMargin=1*cm)
            styles = getSampleStyleSheet()
            elements = []

            # Título
            elements.append(Paragraph(f"Productos La Delicia — {titulo}", styles["Title"]))
            elements.append(Paragraph(f"Período: {f_exp_ini} al {f_exp_fin}  |  Generado: {fecha_hoy()}", styles["Normal"]))
            elements.append(Spacer(1, 0.4*cm))

            # Tabla
            cols = list(df.columns)
            data = [cols] + df.astype(str).values.tolist()

            col_width = (landscape(A4)[0] - 2*cm) / len(cols)
            tabla = Table(data, colWidths=[col_width]*len(cols), repeatRows=1)
            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1565C0")),
                ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
                ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",   (0,0), (-1,-1), 7),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#EEF4FF")]),
                ("GRID",       (0,0), (-1,-1), 0.3, colors.HexColor("#BBDEFB")),
                ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
                ("PADDING",    (0,0), (-1,-1), 4),
            ]))
            elements.append(tabla)
            doc.build(elements)
            buf.seek(0)
            return buf.read()

        # Ventas
        st.markdown('<div class="section-label">Ventas</div>', unsafe_allow_html=True)
        col_v1, col_v2 = st.columns(2)
        if col_v1.button("📥 CSV", key="btn_exp_v"):
            raw_e = sb_get("ventas", f"select=*&fecha=gte.{f_exp_ini}&fecha=lte.{f_exp_fin}&order=fecha.asc")
            if raw_e:
                csv = pd.DataFrame(raw_e).to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Descargar ventas CSV", csv, f"ventas_{f_exp_ini}_{f_exp_fin}.csv", "text/csv", key="dl_v")
        if col_v2.button("📄 PDF", key="btn_pdf_v"):
            raw_e = sb_get("ventas", f"select=fecha,hora,canal,vendedor,cliente,factura_id,total&fecha=gte.{f_exp_ini}&fecha=lte.{f_exp_fin}&order=fecha.asc")
            if raw_e:
                df_v = pd.DataFrame(raw_e)
                df_v = (df_v.groupby("factura_id", as_index=False)
                        .agg(fecha=("fecha", "first"), hora=("hora", "first"),
                             canal=("canal", "first"), vendedor=("vendedor", "first"),
                             cliente=("cliente", "first"), total=("total", "sum"))
                        .sort_values(["fecha", "hora"]))
                df_v["total"] = df_v["total"].apply(lambda x: f"${int(x):,.0f}".replace(",","."))
                df_v = df_v[["fecha", "hora", "canal", "vendedor", "cliente", "total"]]
                pdf_bytes = generar_pdf("Reporte de Ventas", df_v, f"ventas_{f_exp_ini}_{f_exp_fin}")
                st.download_button("⬇️ Descargar ventas PDF", pdf_bytes, f"ventas_{f_exp_ini}_{f_exp_fin}.pdf", "application/pdf", key="dl_pdf_v")

        # Producción
        st.markdown('<div class="section-label">Producción</div>', unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        if col_p1.button("📥 CSV", key="btn_exp_p"):
            raw_e2 = sb_get("produccion", f"select=*&fecha=gte.{f_exp_ini}&fecha=lte.{f_exp_fin}&order=fecha.asc")
            if raw_e2:
                csv2 = pd.DataFrame(raw_e2).to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Descargar producción CSV", csv2, f"produccion_{f_exp_ini}_{f_exp_fin}.csv", "text/csv", key="dl_p")
        if col_p2.button("📄 PDF", key="btn_pdf_p"):
            raw_e2 = sb_get("produccion", f"select=fecha,hora,empleado,sabor,cantidad&fecha=gte.{f_exp_ini}&fecha=lte.{f_exp_fin}&order=fecha.asc")
            if raw_e2:
                df_p = pd.DataFrame(raw_e2)
                pdf_bytes = generar_pdf("Reporte de Producción", df_p, f"produccion_{f_exp_ini}_{f_exp_fin}")
                st.download_button("⬇️ Descargar producción PDF", pdf_bytes, f"produccion_{f_exp_ini}_{f_exp_fin}.pdf", "application/pdf", key="dl_pdf_p")

        # Inventario
        st.markdown('<div class="section-label">Inventario</div>', unsafe_allow_html=True)
        col_i1, col_i2 = st.columns(2)
        if col_i1.button("📥 CSV", key="btn_exp_i"):
            raw_e3 = sb_get("inventario", "select=*&order=sabor.asc")
            if raw_e3:
                csv3 = pd.DataFrame(raw_e3).to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Descargar inventario CSV", csv3, f"inventario_{fecha_hoy()}.csv", "text/csv", key="dl_i")
        if col_i2.button("📄 PDF", key="btn_pdf_i"):
            raw_e3 = sb_get("inventario", "select=sabor,stock,precio&order=sabor.asc")
            if raw_e3:
                df_i = pd.DataFrame(raw_e3)
                df_i["precio"] = df_i["precio"].apply(lambda x: f"${int(x):,.0f}".replace(",","."))
                pdf_bytes = generar_pdf("Inventario Actual", df_i, f"inventario_{fecha_hoy()}")
                st.download_button("⬇️ Descargar inventario PDF", pdf_bytes, f"inventario_{fecha_hoy()}.pdf", "application/pdf", key="dl_pdf_i")

        st.markdown(f'<div class="warn-box">{ICO_BULB} Guarda estos archivos semanalmente como respaldo.</div>', unsafe_allow_html=True)
