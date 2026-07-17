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
from datetime import date, datetime, timezone, timedelta, time as dtime
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
    "Almuerzo Limón": 9000, "Almuerzo Picante": 9000, "Surtidas": 9000,
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
    "Surtidas":         [("Mayorista", 8500), ("Frecuente", 9000), ("Ocasional", 9500), ("Pequeño", 10000)],
    "Fósforo 70g (x10)": [("Mayorista", 14500), ("Minorista", 15000)],
    "Fósforo 140g":      [("Mayorista", 3500),  ("Minorista", 4000)],
    "Fósforo 500g":      [("Mayorista", 14500), ("Minorista", 15000)],
    "Mega":    [("$1.600", 1600), ("$1.700", 1700), ("$1.800", 1800)],
    "Megaton": [("$5.000", 5000), ("$5.500", 5500)],
}
SABORES_LISTA = list(PRODUCTOS.keys())

# Cuántas bolsas individuales representa "1" registrado en Producción/Ventas para
# cada sabor — la mayoría se vende y se registra por docena, pero unos pocos son
# por unidad o por decena. Sin esto, sumar "cantidad" tal cual mezcla conteos que
# no son comparables (1 docena de BBQ != 1 unidad de Mega).
UNIDADES_POR_BOLSA = {
    "Mega": 1, "Megaton": 1, "Fósforo 140g": 1, "Fósforo 500g": 1,
    "Fósforo 70g (x10)": 10,
}
UNIDADES_POR_BOLSA_DEFAULT = 12  # docena — el resto de los sabores

# Peso en kg de papa FRITA por bolsa individual — para calcular el costo de papa
# por rendimiento (crudo → frito) en vez de repartirlo a ciegas entre bolsas.
# Fósforo queda afuera hasta tener su dato de rendimiento.
PESO_KG_BOLSA = {"Mega": 0.070, "Megaton": 0.180}
PESO_KG_BOLSA_DOCENA = 0.035  # cada bolsita individual de los sabores por docena
FOSFORO_SABORES = {"Fósforo 70g (x10)", "Fósforo 140g", "Fósforo 250g", "Fósforo 500g"}

EMPLEADOS = ["Andrea", "Sofía", "Javier", "Edison", "Otro"]
RESERVA_META = {"Papa": 50_000_000, "Empaque": 50_000_000}
VENDEDORES_FABRICA = ["Sofía", "Andrea"]
STOCK_MINIMO = 10  # alerta cuando un sabor tenga menos de esta cantidad

def fmt(n):
    return f"${int(n):,.0f}".replace(",", ".")

def _fmt_celda(v):
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return f"{v:.3f}".rstrip("0").rstrip(".")
    return v

def tabla_view(df):
    """Tabla de solo consulta, estática (sin ordenar/arrastrar columnas al tocar en tablet)."""
    st.table(df.style.hide(axis="index").format(_fmt_celda))

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

def _parse_hora(hora_str):
    """Convierte '2:35 PM' a un time comparable; si no se puede leer, va al final."""
    try:
        return datetime.strptime(hora_str, "%I:%M %p").time()
    except (ValueError, TypeError):
        return dtime.min

def mostrar_facturas_seleccionables(df_canal, key_prefix):
    """Tabla con facturas; al seleccionar una fila se abre el recibo en una vista nueva."""
    filas = []
    for fid in df_canal["factura_id"].unique():
        if not fid:
            continue
        grupo = df_canal[df_canal["factura_id"]==fid]
        saldo_fac = float(grupo["saldo"].max()) if "saldo" in grupo.columns and not grupo.empty else 0
        estado = "📋 Crédito" if saldo_fac > 0 else "✓ Aprobado"
        filas.append({
            "Fecha": grupo["fecha"].iloc[0],
            "N° Comprobante": f"FV-{fid}",
            "Vendedor": grupo["vendedor"].iloc[0],
            "Cliente": grupo["cliente"].iloc[0],
            "Total": fmt(grupo[grupo["total"] > 0]["total"].sum()),
            "Estado": estado,
            "_fid": fid,
            "_hora": grupo["hora"].iloc[0] if "hora" in grupo.columns else "",
        })
    if not filas:
        return
    filas.sort(key=lambda r: (r["Fecha"], _parse_hora(r["_hora"])), reverse=True)
    df_tabla = pd.DataFrame(filas)

    evento = st.dataframe(
        df_tabla.drop(columns=["_fid", "_hora"]),
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

def _pendiente_creditos_antiguos(f_ini, f_fin, canal=None):
    """Saldo pendiente de créditos antiguos manuales (tabla 'creditos') originados
    entre f_ini y f_fin, opcionalmente filtrado por canal."""
    filtro = f"select=total,pagado&fecha=gte.{f_ini}&fecha=lte.{f_fin}&estado=eq.pendiente"
    if canal:
        filtro += f"&canal=eq.{requests.utils.quote(canal)}"
    raw = sb_get("creditos", filtro) or []
    return sum(max(0.0, float(r["total"]) - float(r.get("pagado", 0) or 0)) for r in raw)

def calcular_cobros_periodo(f_ini, f_fin):
    """Dinero realmente cobrado entre f_ini y f_fin — ventas nuevas del período
    MÁS créditos viejos (de cualquier fecha) que se cobraron dentro del período.
    Fetea todos los canales; cada llamador filtra/suma por canal si lo necesita.

    Antes este cálculo (con el ajuste de "no contar dos veces lo cobrado después
    de la venta") estaba copiado y pegado en ~8 lugares distintos — Caja→Resumen,
    Caja→Arqueo, Resumen→Hoy/Por fechas/Mes, y los "Resumen del día" de Carro y
    Fábrica. Al agregar el cobro de créditos viejos se corrigió solo una copia
    primero, y las demás quedaron desactualizadas hasta que se reportó el bug —
    por eso ahora viven en un solo lugar.

    Devuelve:
      raw_ventas: filas crudas de 'ventas' en el rango (una por producto vendido)
      facturas: {factura_id: {"canal", "abono" (ya sin lo cobrado después), "saldo"}},
                 una entrada por factura, no por línea de producto
      cobro_creditos_por_canal: {canal: $ cobrado en créditos viejos dentro del rango}
      cobro_creditos_total: suma de lo anterior
    """
    f_ini_d = f_ini if isinstance(f_ini, date) else date.fromisoformat(str(f_ini))
    f_fin_d = f_fin if isinstance(f_fin, date) else date.fromisoformat(str(f_fin))

    raw_ventas = sb_get("ventas", f"select=*&fecha=gte.{f_ini}&fecha=lte.{f_fin}") or []
    raw_pg = sb_get("pagos_credito", "select=fecha,monto,tipo,factura_id,canal") or []

    # Cuánto de cada factura se cobró DESPUÉS de la venta (vía "Cobrar" en créditos
    # pendientes) — se resta del abono actual para no contar ese dinero dos veces:
    # una en la fecha de la venta y otra en la fecha real del cobro. Se necesita el
    # histórico completo de pagos_credito (sin filtrar por fecha) porque el pago
    # pudo haber ocurrido antes o después del rango que se está consultando.
    cobrado_despues = {}
    for r in raw_pg:
        if r.get("tipo") == "venta" and r.get("factura_id"):
            fid = r["factura_id"]
            cobrado_despues[fid] = cobrado_despues.get(fid, 0) + float(r["monto"])

    facturas = {}
    for r in raw_ventas:
        fid = r.get("factura_id", "")
        if fid and fid not in facturas:
            abono_inicial = max(0.0, float(r.get("abono", 0) or 0) - cobrado_despues.get(fid, 0))
            facturas[fid] = {
                "canal": r.get("canal", ""),
                "abono": abono_inicial,
                "saldo": float(r.get("saldo", 0) or 0),
            }

    cobro_creditos_por_canal = {}
    for r in raw_pg:
        if f_ini_d <= date.fromisoformat(r["fecha"]) <= f_fin_d:
            c = r.get("canal", "")
            cobro_creditos_por_canal[c] = cobro_creditos_por_canal.get(c, 0.0) + float(r["monto"])

    return {
        "raw_ventas": raw_ventas,
        "facturas": facturas,
        "cobro_creditos_por_canal": cobro_creditos_por_canal,
        "cobro_creditos_total": sum(cobro_creditos_por_canal.values()),
    }

def mostrar_creditos_pendientes(canal):
    """Muestra facturas con saldo pendiente y permite registrar abonos."""
    with st.expander("➕ Cargar crédito antiguo"):
        st.caption("Para deudas que ya existían antes de usar la app. Solo el monto — no afecta el inventario.")
        col_f1, col_f2 = st.columns(2)
        fecha_cred = col_f1.date_input("Fecha de la venta", value=datetime.now(COL_TZ).date(), key=f"cred_fecha_{canal}")
        vendedor_cred = col_f2.radio("Vendedor", EMPLEADOS, horizontal=True, key=f"cred_vendedor_{canal}")
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
    contenedor_creditos = st.container(height=820) if len(facturas) > 5 else st.container()
    for key, datos in facturas.items():
        saldo = datos["saldo"]
        contenedor_creditos.markdown(
            f'<div class="warn-box">'
            f'<b>{datos["cliente"]}</b> · {datos["etiqueta"]}<br>'
            f'Total: {fmt(datos["total"])} · Abonado: {fmt(datos["abono"])} · '
            f'<b>Debe: {fmt(saldo)}</b>'
            f'</div>',
            unsafe_allow_html=True
        )
        if datos["tipo"] == "venta":
            col_v, col_m, col_b = contenedor_creditos.columns([1, 2, 1])
            if col_v.button("🧾", key=f"ver_fact_{key}", help="Ver factura completa"):
                todos_fact = sb_get("ventas", f"select=*&factura_id=eq.{requests.utils.quote(datos['ref'])}")
                st.session_state.recibo_a_mostrar = datos["ref"]
                st.session_state.recibo_canal_df = todos_fact if todos_fact else []
                st.session_state.vista_anterior = st.session_state.vista
                st.session_state.vista = "recibo"
                st.rerun()
        else:
            col_m, col_b = contenedor_creditos.columns([3, 1])
        nuevo_abono = col_m.number_input(
            "Abono ($)", min_value=0, max_value=int(saldo),
            value=int(saldo), step=1000, key=f"abono_pend_{key}"
        )
        if col_b.button("✅ Cobrar", key=f"btn_cobrar_{key}") and nuevo_abono > 0:
            if datos["tipo"] == "venta":
                filtro_cobro = f"factura_id=eq.{datos['ref']}&canal=eq.{requests.utils.quote(canal)}"
                ok_cobro = _ajustar_saldo_ventas_cas(filtro_cobro, delta_saldo=-nuevo_abono, delta_abono=nuevo_abono)
                id_factura, id_credito = datos["ref"], None
            else:
                ok_cobro = _registrar_pago_credito_cas(datos["ref"], nuevo_abono)
                id_factura, id_credito = None, datos["ref"]
            if ok_cobro:
                sb_post("pagos_credito", {
                    "fecha": fecha_hoy(), "hora": ahora(), "tipo": datos["tipo"],
                    "factura_id": id_factura, "credito_id": id_credito,
                    "cliente": datos["cliente"], "canal": canal, "vendedor": datos["vendedor"],
                    "monto": float(nuevo_abono),
                })
            time.sleep(0.3)
            st.rerun()

def mostrar_historial_pagos_credito(canal):
    """Historial de créditos ya cobrados en este canal, con la fecha real del pago
    (no la fecha de la venta original) — visible para Fábrica y Carro, no solo admin."""
    st.markdown('<div class="section-label">🕒 Historial de créditos pagados</div>', unsafe_allow_html=True)
    col_hp1, col_hp2 = st.columns(2)
    f_ini_hp = col_hp1.date_input("Desde", value=datetime.now(COL_TZ).date().replace(day=1), key=f"hp_ini_{canal}")
    f_fin_hp = col_hp2.date_input("Hasta", value=datetime.now(COL_TZ).date(), key=f"hp_fin_{canal}")

    raw_hp = sb_get("pagos_credito", f"select=*&canal=eq.{requests.utils.quote(canal)}&fecha=gte.{f_ini_hp}&fecha=lte.{f_fin_hp}&order=fecha.desc,hora.desc")
    if not raw_hp:
        st.caption("No hay créditos pagados en ese rango.")
        return

    df_hp = pd.DataFrame(raw_hp)
    total_hp = df_hp["monto"].sum()
    st.markdown(f'<div class="info-box">{ICO_DOLLAR} Total cobrado en el rango: <b>{fmt(total_hp)}</b></div>', unsafe_allow_html=True)

    busqueda_hp = st.text_input("🔍 Buscar por cliente", key=f"buscar_hp_{canal}", placeholder="Ej: Don Carlos")
    if busqueda_hp.strip():
        df_hp = df_hp[df_hp["cliente"].apply(lambda c: _coincide_nombre(busqueda_hp, c or ""))]

    if df_hp.empty:
        st.caption("No hay créditos pagados para ese cliente en ese rango.")
    else:
        tabla_hp = df_hp.copy()
        tabla_hp["Referencia"] = tabla_hp.apply(
            lambda r: f"FV-{r['factura_id']}" if r["tipo"]=="venta" else "Crédito antiguo", axis=1
        )
        tabla_hp["monto"] = tabla_hp["monto"].apply(fmt)
        tabla_hp = tabla_hp[["fecha","hora","cliente","vendedor","Referencia","monto"]]
        tabla_hp.columns = ["Fecha","Hora","Cliente","Vendedor","Factura","Monto cobrado"]
        tabla_view(tabla_hp)

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
        vendedor = st.radio("Vendedor", cfg["vendedores"], horizontal=True, key="venta_vendedor")
    else:
        vendedor = cfg["vendedor_fijo"]
    cliente = st.text_input("Nombre del cliente", placeholder="Ej: Tienda Don Carlos", key="venta_cliente")

    st.markdown('<div class="section-label">Agregar al carrito</div>', unsafe_allow_html=True)
    sabor = st.radio("Sabor", cfg["sabores_venta_fn"](), key="venta_sabor")

    disp_map = cfg["disponible_map_fn"]()
    en_carrito = st.session_state[key_carrito].get(sabor, 0)
    disponible = max(0, disp_map.get(sabor, 0) - en_carrito)

    cant = st.number_input("Bolsas", min_value=1, max_value=max(1, disponible), value=1, step=1, key="venta_cant")

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
                    _ajustar_saldo_ventas_cas(f"factura_id=eq.{fac['id']}&canal=eq.{canal}", delta_saldo=diferencia)
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
                    _ajustar_saldo_ventas_cas(f"factura_id=eq.{fac['id']}&canal=eq.{canal}", delta_saldo=precio_add)
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
        f"select=fecha,hora,cliente,vendedor,sabor,cantidad,total,factura_id,saldo&fecha=eq.{fecha_hoy()}&canal=eq.{canal}&order=hora.desc")
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

def _consolidar_items_recibo(registros):
    """Cantidad y total netos por sabor, sumando venta original + cambios (canal='Cambio')."""
    items_cons = {}
    totales_cons = {}
    for r in registros:
        s = r["sabor"]
        items_cons[s]  = items_cons.get(s, 0) + r["cantidad"]
        totales_cons[s] = totales_cons.get(s, 0) + r["total"]
    # Filtrar items con cantidad > 0 (los que quedaron después de cambios)
    items_finales = {s: c for s, c in items_cons.items() if c > 0}
    return items_finales, totales_cons

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

    items_finales, totales_cons = _consolidar_items_recibo(registros)
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
        f'<div class="recibo-logo">{logo_recibo_html}</div>',
        '<div class="recibo-titulo">Productos La Delicia</div>',
        '<div class="recibo-sub">Factura de venta</div>',
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

def _ajustar_saldo_ventas_cas(filtro, delta_saldo, delta_abono=0, intentos=5):
    """Ajusta saldo/abono de las filas de 'ventas' que cumplan filtro (normalmente
    factura_id + canal), con concurrencia optimista: el PATCH solo aplica si nadie
    más cambió el saldo entre la lectura y la escritura (mismo patrón que
    _ajustar_stock_cas — evita perder un cobro o una edición de factura si dos
    personas tocan la misma factura casi al mismo tiempo)."""
    if delta_saldo == 0 and delta_abono == 0:
        return True
    for _ in range(intentos):
        r = sb_get("ventas", f"select=saldo,abono&{filtro}&limit=1")
        saldo_actual = float(r[0]["saldo"]) if r else 0
        abono_actual = float(r[0]["abono"]) if r else 0
        saldo_nuevo = max(0, saldo_actual + delta_saldo)
        abono_nuevo = abono_actual + delta_abono
        try:
            resp = requests.patch(
                f"{SUPABASE_URL}/rest/v1/ventas?{filtro}&saldo=eq.{saldo_actual}",
                headers=HEADERS, json={"saldo": saldo_nuevo, "abono": abono_nuevo}, timeout=10
            )
            if resp.ok and resp.json():
                return True
        except Exception:
            pass
    st.error("⚠️ No se pudo actualizar el saldo (otro cambio ocurrió al mismo tiempo). Vuelve a intentarlo.")
    return False

def _registrar_pago_credito_cas(id_credito, monto_abono, intentos=5):
    """Registra un abono sobre un crédito manual antiguo (tabla 'creditos'), con la
    misma concurrencia optimista que _ajustar_saldo_ventas_cas pero comparando sobre
    el campo 'pagado' (esta tabla no tiene columna 'saldo')."""
    for _ in range(intentos):
        r = sb_get("creditos", f"select=total,pagado&id=eq.{id_credito}&limit=1")
        if not r:
            return False
        total_actual = float(r[0]["total"])
        pagado_actual = float(r[0].get("pagado", 0) or 0)
        pagado_nuevo = pagado_actual + monto_abono
        estado_nuevo = "pagado" if pagado_nuevo >= total_actual else "pendiente"
        try:
            resp = requests.patch(
                f"{SUPABASE_URL}/rest/v1/creditos?id=eq.{id_credito}&pagado=eq.{pagado_actual}",
                headers=HEADERS, json={"pagado": pagado_nuevo, "estado": estado_nuevo}, timeout=10
            )
            if resp.ok and resp.json():
                return True
        except Exception:
            pass
    st.error("⚠️ No se pudo registrar el abono (otro cambio ocurrió al mismo tiempo). Vuelve a intentarlo.")
    return False

def _registrar_auditoria_factura(factura_id, accion, detalle, usuario):
    """Deja constancia de quién editó o eliminó una factura ya existente."""
    sb_post("factura_auditoria", {
        "fecha": fecha_hoy(), "hora": ahora(),
        "factura_id": factura_id, "accion": accion,
        "detalle": detalle, "usuario": usuario or "Sin especificar"
    })

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

def get_logo_recibo_b64():
    p = Path("Ladelicia_recibo.png")
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else None

logo_recibo_b64 = get_logo_recibo_b64()
logo_recibo_html = (
    f'<img src="data:image/png;base64,{logo_recibo_b64}" style="height:70px;object-fit:contain;margin-bottom:6px;">'
    if logo_recibo_b64 else logo_html
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
.brand-logo img{height:620px !important;margin-bottom:0 !important;animation:logoBounce 2.2s ease-in-out infinite;transform-origin:bottom center;}
.metric-row{display:flex;gap:9px;margin-bottom:16px;}
.metric-box{flex:1;background:#FFFFFF;border-radius:14px;padding:14px 8px;text-align:center;box-shadow:0 2px 8px rgba(21,101,192,0.12);}
.metric-box .val{font-size:1.2rem;font-weight:700;line-height:1.1;}
.metric-box .lbl{font-size:0.65rem;color:#1565C0;margin-top:3px;}
.metric-blue .val{color:#1565C0;}.metric-green .val{color:#1B9E5A;}.metric-red .val{color:#D32F2F;}.metric-yellow .val{color:#E68900;}
@keyframes fadeInUp{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
@keyframes btnPress{0%{transform:scale(1);}40%{transform:scale(0.93);}100%{transform:scale(0.97);}}
@keyframes cardPress{0%{transform:scale(1) translateY(0);}30%{transform:scale(0.93) translateY(2px);}65%{transform:scale(1.01) translateY(-1px);}100%{transform:scale(0.98) translateY(0);}}
@keyframes logoBounce{0%,100%{transform:translateY(0) scale(1,1);}10%{transform:translateY(0) scale(1.08,0.92);}35%{transform:translateY(-36px) scale(0.96,1.06);}55%{transform:translateY(0) scale(1.1,0.9);}65%{transform:translateY(-12px) scale(1,1);}80%{transform:translateY(0) scale(1.04,0.96);}90%{transform:translateY(0) scale(1,1);}}
@keyframes ctaPulse{0%,100%{box-shadow:0 4px 16px rgba(21,101,192,0.3);transform:scale(1);}50%{box-shadow:0 4px 26px rgba(21,101,192,0.65);transform:scale(1.02);}}
.st-key-venta_btn_confirmar button:not(:disabled),
.st-key-btn_prod button:not(:disabled),
.st-key-btn_adj button:not(:disabled),
.st-key-btn_dev button:not(:disabled),
.st-key-btn_reg button:not(:disabled),
.st-key-btn_reg_fab button:not(:disabled),
.st-key-btn_rollo_registrar button:not(:disabled),
.st-key-btn_sal button:not(:disabled),
.st-key-btn_eg button:not(:disabled),
.st-key-btn_in button:not(:disabled),
.st-key-btn_guardar_arqueo button:not(:disabled),
.st-key-btn_guardar_reserva button:not(:disabled),
[class*="st-key-btn_cred_guardar_"] button:not(:disabled){
  animation:ctaPulse 1.6s ease-in-out infinite !important;
}
.st-key-venta_btn_confirmar button:hover,.st-key-venta_btn_confirmar button:active,
.st-key-btn_prod button:hover,.st-key-btn_prod button:active,
.st-key-btn_adj button:hover,.st-key-btn_adj button:active,
.st-key-btn_dev button:hover,.st-key-btn_dev button:active,
.st-key-btn_reg button:hover,.st-key-btn_reg button:active,
.st-key-btn_reg_fab button:hover,.st-key-btn_reg_fab button:active,
.st-key-btn_rollo_registrar button:hover,.st-key-btn_rollo_registrar button:active,
.st-key-btn_sal button:hover,.st-key-btn_sal button:active,
.st-key-btn_eg button:hover,.st-key-btn_eg button:active,
.st-key-btn_in button:hover,.st-key-btn_in button:active,
.st-key-btn_guardar_arqueo button:hover,.st-key-btn_guardar_arqueo button:active,
.st-key-btn_guardar_reserva button:hover,.st-key-btn_guardar_reserva button:active,
[class*="st-key-btn_cred_guardar_"] button:hover,[class*="st-key-btn_cred_guardar_"] button:active{
  animation:none !important;
}
.alert-low,.info-box,.warn-box,.success-toast,.factura-box,.recibo-ticket,.metric-box{animation:fadeInUp 0.25s ease both;}
.alert-low{background:#FFEBEE;border-left:3px solid #D32F2F;border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:9px;font-size:0.83rem;color:#B71C1C;}
.info-box{background:#FFFFFF;border-left:3px solid #1B9E5A;border-radius:10px;padding:12px 14px;margin:8px 0 14px;font-size:0.82rem;color:#1B5E20;box-shadow:0 1px 6px rgba(0,0,0,0.05);}
.warn-box{background:#FFFFFF;border-left:3px solid #E68900;border-radius:10px;padding:12px 14px;margin:8px 0 14px;font-size:0.82rem;color:#8D6E00;box-shadow:0 1px 6px rgba(0,0,0,0.05);}
.success-toast{background:#E8F5E9;border:1px solid #A5D6A7;border-radius:12px;padding:14px 16px;text-align:center;font-weight:600;color:#1B5E20;font-size:0.95rem;margin-top:10px;}
.section-label{font-size:0.69rem;font-weight:700;text-transform:uppercase;letter-spacing:0.7px;color:#B0185F;margin:16px 0 6px;}
.stButton>button{width:100%;background:#1565C0 !important;color:white !important;-webkit-text-fill-color:white !important;border:none !important;border-radius:12px !important;padding:14px !important;font-size:1rem !important;font-weight:700 !important;cursor:pointer;margin-top:4px;box-shadow:0 4px 16px rgba(21,101,192,0.25);white-space:pre-line !important;line-height:1.4 !important;transition:transform 0.3s ease,box-shadow 0.3s ease,opacity 0.3s ease !important;-webkit-tap-highlight-color:transparent;touch-action:manipulation;}
.stButton>button:hover{opacity:0.88;box-shadow:0 6px 20px rgba(21,101,192,0.35);transform:translateY(-1px);}
.stButton>button:active{transform:scale(0.97) translateY(0);box-shadow:0 2px 8px rgba(21,101,192,0.25);opacity:1;animation:btnPress 0.45s ease-out;}
.st-key-btn_resumen button,.st-key-btn_contador button{
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
  transition:transform 0.3s ease,box-shadow 0.3s ease !important;
  -webkit-tap-highlight-color:transparent;
  touch-action:manipulation;
}
.st-key-btn_resumen button:hover,.st-key-btn_contador button:hover{
  box-shadow:0 5px 16px rgba(21,101,192,0.25) !important;
  opacity:1 !important;
  transform:translateY(-2px) !important;
}
.st-key-btn_resumen button:active,.st-key-btn_contador button:active{
  transform:scale(0.98) !important;
  box-shadow:0 2px 8px rgba(21,101,192,0.15) !important;
  animation:cardPress 0.45s ease-out !important;
}

[data-testid="stMetricLabel"] p{color:#1565C0 !important;}
[data-testid="stMetricValue"]{color:#0D1B2A !important;}
.stDataFrame{border-radius:12px;overflow:hidden;font-size:0.83rem;border:1px solid #BBDEFB;}
[data-testid="stTable"]{overflow-x:auto !important;-webkit-overflow-scrolling:touch;}
[data-testid="stTable"] table{width:auto !important;min-width:100%;}
[data-testid="stTable"] th,[data-testid="stTable"] td{white-space:nowrap;}
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
.recibo-logo img{height:auto !important;max-height:70px !important;max-width:100% !important;}
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
div[data-testid="stRadio"] label[data-baseweb="radio"]{background:#1565C0 !important;border:2px solid #1565C0 !important;border-radius:8px !important;padding:8px 16px !important;cursor:pointer;}
div[data-testid="stRadio"] label[data-baseweb="radio"] p, div[data-testid="stRadio"] label[data-baseweb="radio"] span{color:white !important;font-weight:600 !important;}
div[data-testid="stRadio"] input[type="radio"]{accent-color:#1565C0;}
.st-key-venta_sabor div[data-testid="stRadio"] > div{flex-direction:column;flex-wrap:nowrap;max-height:280px;overflow-y:auto;gap:8px;border:1px solid #BBDEFB;border-radius:14px;padding:10px;background:#F8FBFF;box-shadow:inset 0 1px 4px rgba(21,101,192,0.08);}
.st-key-venta_sabor div[data-testid="stRadio"] label[data-baseweb="radio"]{width:100%;box-sizing:border-box;background:#FFFFFF !important;border:1.5px solid #BBDEFB !important;border-radius:10px !important;padding:12px 16px !important;transition:background .15s ease,border-color .15s ease;}
.st-key-venta_sabor div[data-testid="stRadio"] label[data-baseweb="radio"] p,
.st-key-venta_sabor div[data-testid="stRadio"] label[data-baseweb="radio"] span{color:#0D1B2A !important;font-weight:600 !important;}
.st-key-venta_sabor div[data-testid="stRadio"] label[data-baseweb="radio"]:active{background:#E3F0FF !important;}
.st-key-venta_sabor div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){background:#1565C0 !important;border-color:#1565C0 !important;box-shadow:0 2px 8px rgba(21,101,192,0.35);}
.st-key-venta_sabor div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p,
.st-key-venta_sabor div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) span{color:#FFFFFF !important;}
.st-key-cat_sal div[data-testid="stRadio"] > div,
.st-key-rollo_insumo div[data-testid="stRadio"] > div,
.st-key-radio_insumo_mp div[data-testid="stRadio"] > div,
.st-key-insumo_sal div[data-testid="stRadio"] > div,
.st-key-sabor_p div[data-testid="stRadio"] > div{flex-direction:column;flex-wrap:nowrap;max-height:280px;overflow-y:auto;gap:8px;border:1px solid #BBDEFB;border-radius:14px;padding:10px;background:#F8FBFF;box-shadow:inset 0 1px 4px rgba(21,101,192,0.08);}
.st-key-cat_sal div[data-testid="stRadio"] label[data-baseweb="radio"],
.st-key-rollo_insumo div[data-testid="stRadio"] label[data-baseweb="radio"],
.st-key-radio_insumo_mp div[data-testid="stRadio"] label[data-baseweb="radio"],
.st-key-insumo_sal div[data-testid="stRadio"] label[data-baseweb="radio"],
.st-key-sabor_p div[data-testid="stRadio"] label[data-baseweb="radio"]{width:100%;box-sizing:border-box;background:#FFFFFF !important;border:1.5px solid #BBDEFB !important;border-radius:10px !important;padding:12px 16px !important;transition:background .15s ease,border-color .15s ease;}
.st-key-cat_sal div[data-testid="stRadio"] label[data-baseweb="radio"] p,
.st-key-cat_sal div[data-testid="stRadio"] label[data-baseweb="radio"] span,
.st-key-rollo_insumo div[data-testid="stRadio"] label[data-baseweb="radio"] p,
.st-key-rollo_insumo div[data-testid="stRadio"] label[data-baseweb="radio"] span,
.st-key-radio_insumo_mp div[data-testid="stRadio"] label[data-baseweb="radio"] p,
.st-key-radio_insumo_mp div[data-testid="stRadio"] label[data-baseweb="radio"] span,
.st-key-insumo_sal div[data-testid="stRadio"] label[data-baseweb="radio"] p,
.st-key-insumo_sal div[data-testid="stRadio"] label[data-baseweb="radio"] span,
.st-key-sabor_p div[data-testid="stRadio"] label[data-baseweb="radio"] p,
.st-key-sabor_p div[data-testid="stRadio"] label[data-baseweb="radio"] span{color:#0D1B2A !important;font-weight:600 !important;}
.st-key-cat_sal div[data-testid="stRadio"] label[data-baseweb="radio"]:active,
.st-key-rollo_insumo div[data-testid="stRadio"] label[data-baseweb="radio"]:active,
.st-key-radio_insumo_mp div[data-testid="stRadio"] label[data-baseweb="radio"]:active,
.st-key-insumo_sal div[data-testid="stRadio"] label[data-baseweb="radio"]:active,
.st-key-sabor_p div[data-testid="stRadio"] label[data-baseweb="radio"]:active{background:#E3F0FF !important;}
.st-key-cat_sal div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
.st-key-rollo_insumo div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
.st-key-radio_insumo_mp div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
.st-key-insumo_sal div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
.st-key-sabor_p div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){background:#1565C0 !important;border-color:#1565C0 !important;box-shadow:0 2px 8px rgba(21,101,192,0.35);}
.st-key-cat_sal div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p,
.st-key-cat_sal div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) span,
.st-key-rollo_insumo div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p,
.st-key-rollo_insumo div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) span,
.st-key-radio_insumo_mp div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p,
.st-key-radio_insumo_mp div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) span,
.st-key-insumo_sal div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p,
.st-key-insumo_sal div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) span,
.st-key-sabor_p div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p,
.st-key-sabor_p div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) span{color:#FFFFFF !important;}
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
    "resumen":       "Resumen.jpg",
    "contador":      "Contador.jpg",
}

# Iconos vectoriales (reemplazan los emojis, que no siempre se ven igual en todos los dispositivos)
_iconos_svg = {
    "produccion":    '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
    "carro":         '<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
    "fabrica":       '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
    "materia_prima": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "caja":          '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "resumen":       '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "contador":      '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
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

if not get_img_b64(_imagenes_menu["resumen"]):
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

if not get_img_b64(_imagenes_menu["contador"]):
    _contador_icon_b64 = get_svg_b64(_iconos_svg["contador"], "#0D1B2A")
    _css_botones_menu += f"""
.st-key-btn_contador button{{
  padding-left:60px !important;
  position:relative !important;
}}
.st-key-btn_contador button::before{{
  content:'';
  position:absolute;
  left:18px;
  top:50%;
  transform:translateY(-50%);
  width:28px;
  height:28px;
  background:url("data:image/svg+xml;base64,{_contador_icon_b64}") no-repeat center/contain;
}}
"""

_fondo_b64 = get_img_b64("fondo.jpg")
if _fondo_b64:
    _css_botones_menu += f"""
.stApp{{
  background:linear-gradient(rgba(240,244,255,0.8),rgba(240,244,255,0.8)),url("data:image/jpeg;base64,{_fondo_b64}") center/cover no-repeat !important;
}}
"""

_fondo_logo_b64 = get_img_b64("Fondo_del_logo.jpg")
if _fondo_logo_b64:
    _css_botones_menu += f"""
.brand-header{{
  background:linear-gradient(135deg,rgba(21,101,192,0.55),rgba(30,136,229,0.55)),url("data:image/jpeg;base64,{_fondo_logo_b64}") center/cover no-repeat !important;
}}
"""

_imagenes_cat_mp = {
    "btn_cat_mp":  "MateriaprimaInsumos.jpg",
    "btn_cat_sab": "saborizantes.jpg",
    "btn_cat_emp": "rollos_empaque.jpg",
}
for _key_cat, _archivo_cat in _imagenes_cat_mp.items():
    _b64_cat = get_img_b64(_archivo_cat)
    if _b64_cat:
        _css_botones_menu += f"""
.st-key-{_key_cat} button{{
  background:linear-gradient(90deg,rgba(0,0,0,0.68) 0%,rgba(0,0,0,0.5) 55%,rgba(0,0,0,0.35) 100%),url("data:image/jpeg;base64,{_b64_cat}") center/cover no-repeat !important;
  color:#FFFFFF !important;
  -webkit-text-fill-color:#FFFFFF !important;
  border:none !important;
  border-radius:18px !important;
  box-shadow:0 3px 12px rgba(21,101,192,0.25) !important;
  min-height:110px !important;
  padding:18px 20px !important;
  font-size:1rem !important;
  font-weight:700 !important;
  white-space:pre-line !important;
  line-height:1.5 !important;
  text-align:left !important;
  text-shadow:0 1px 3px rgba(0,0,0,0.9),0 2px 8px rgba(0,0,0,0.6) !important;
}}
.st-key-{_key_cat} button:hover{{
  background:linear-gradient(90deg,rgba(0,0,0,0.58) 0%,rgba(0,0,0,0.4) 55%,rgba(0,0,0,0.25) 100%),url("data:image/jpeg;base64,{_b64_cat}") center/cover no-repeat !important;
  box-shadow:0 5px 16px rgba(21,101,192,0.32) !important;
  opacity:1 !important;
}}
"""

_b64_volver = get_img_b64("Volver.jpg")
if _b64_volver:
    _css_botones_menu += f"""
.st-key-btn_back button{{
  background:linear-gradient(90deg,rgba(0,0,0,0.6) 0%,rgba(0,0,0,0.6) 100%),url("data:image/jpeg;base64,{_b64_volver}") center/cover no-repeat !important;
  color:#FFFFFF !important;
  -webkit-text-fill-color:#FFFFFF !important;
  border:none !important;
  text-shadow:0 1px 3px rgba(0,0,0,0.9),0 2px 8px rgba(0,0,0,0.6) !important;
}}
.st-key-btn_back button:hover{{
  background:linear-gradient(90deg,rgba(0,0,0,0.48) 0%,rgba(0,0,0,0.48) 100%),url("data:image/jpeg;base64,{_b64_volver}") center/cover no-repeat !important;
  opacity:1 !important;
}}
"""

if _css_botones_menu:
    st.markdown(f"<style>{_css_botones_menu}</style>", unsafe_allow_html=True)

# Bloquear teclado virtual en los selectbox y fechas (solo permite tocar y elegir)
components.html("""
<script>
(function () {
    const SEL_SELECTS = '[data-baseweb="select"] input';
    const SEL_FECHAS   = '[data-testid="stDateInputField"], [data-baseweb="datepicker"] input';
    const SEL_NUMEROS  = '[data-testid="stNumberInputField"]';

    function marcar(inp, modo) {
        // Evita llamar setAttribute si ya está puesto, para no generar
        // mutaciones de DOM innecesarias (eso causaba un bucle con el observer).
        if (inp.getAttribute('inputmode') !== modo) inp.setAttribute('inputmode', modo);
        if (modo !== 'numeric' && inp.getAttribute('readonly') !== 'true') inp.setAttribute('readonly', 'true');
    }

    function bloquear(doc) {
        try {
            doc.querySelectorAll(SEL_SELECTS).forEach(function (inp) { marcar(inp, 'none'); });
            doc.querySelectorAll(SEL_FECHAS).forEach(function (inp) { marcar(inp, 'none'); });
            doc.querySelectorAll(SEL_NUMEROS).forEach(function (inp) { marcar(inp, 'numeric'); });
        } catch (e) {}
    }

    try {
        const doc = window.parent.document;
        bloquear(doc);

        // Streamlit re-ejecuta este componente en cada rerun de la app; sin
        // esta bandera, cada rerun agregaría listeners y un observer nuevos
        // (duplicados, nunca se quitan los anteriores), acumulando cientos
        // con el uso y congelando la app. Con la bandera, todo lo de abajo
        // se registra una sola vez por sesión de navegador.
        if (doc.defaultView.__fabricaTecladoInit) return;
        doc.defaultView.__fabricaTecladoInit = true;

        // Reacciona cuando Streamlit crea nodos nuevos, y también cuando React
        // le quita el atributo readonly/inputmode a un input ya existente (pasa
        // en algunos selects al reabrir la lista). marcar() ya evita setAttribute
        // si el valor no cambió, así que observar atributos no genera bucle: solo
        // reacciona cuando el valor real cambia (por ejemplo, cuando React lo borra).
        const observer = new MutationObserver(function () { bloquear(doc); });
        observer.observe(doc.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['readonly', 'inputmode']
        });

        // Refuerzo justo antes del toque: el dedo cae sobre el div contenedor,
        // no sobre el input, así que hay que buscar hacia arriba con closest().
        function reforzarDesdeEvento(e) {
            const t = e.target;
            if (!t || !t.closest) return;
            const cont = t.closest('[data-baseweb="select"], [data-baseweb="datepicker"], [data-testid="stDateInputField"]');
            if (!cont) return;
            const inp = cont.tagName === 'INPUT' ? cont : cont.querySelector('input');
            if (inp) marcar(inp, 'none');
        }
        doc.addEventListener('touchstart', reforzarDesdeEvento, true);
        doc.addEventListener('touchend', reforzarDesdeEvento, true);
        doc.addEventListener('pointerdown', reforzarDesdeEvento, true);
        doc.addEventListener('mousedown', reforzarDesdeEvento, true);

        // Último respaldo: React recrea el <input> justo al abrir la lista,
        // así que puede recibir foco sin el atributo puesto todavía. Si eso
        // pasa, se quita el foco y se repone al instante ya con el bloqueo
        // (mismo tick), antes de que el teclado alcance a mostrarse.
        doc.addEventListener('focus', function (e) {
            const t = e.target;
            if (!t || !t.matches) return;
            if (!t.matches(SEL_SELECTS)) return;
            if (t.getAttribute('readonly') === 'true') return;
            t.setAttribute('inputmode', 'none');
            t.setAttribute('readonly', 'true');
            t.blur();
            t.focus();
        }, true);

        // Respaldo por si el observer se pierde algún cambio. 100ms en vez de 300ms
        // para achicar la ventana en la que un input puede quedar sin bloquear.
        setInterval(function () { bloquear(doc); }, 100);
    } catch (e) {}
})();
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
    ]
    if st.session_state.es_admin:
        opciones.append(("caja", "Caja", "Ingresos y egresos"))
        opciones.append(("resumen", "Resumen", "Ventas, facturas y exportar"))
        opciones.append(("contador", "Contador", "Costos, inventario y utilidad"))

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
    sabor_p    = st.radio("Sabor producido", sabores_produccion_frecuente(), key="sabor_p")
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
        tabla_view(df_inv)

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

    sub1, sub2, sub3, sub4, sub5, sub6 = st.tabs(["🚗 Nuevo cargue", "💵 Registrar venta", "🔄 Devolución", "🎁 Regalar", "📋 Resumen del día", "💳 Créditos"])

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
            tabla_view(df_pend)

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
            valor_regalado = sum(r["cantidad"] * PRODUCTOS.get(r["sabor"], 0) for r in raw_reg)
            st.markdown(
                f'<div class="factura-box">{filas_reg}'
                f'<div class="factura-row"><span>Total regalado hoy</span><span>{total_regalado} bolsas</span></div>'
                f'<div class="factura-total"><span>Valor que se dejó de cobrar</span><span>{fmt(valor_regalado)}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

    with sub5:
        # Visible para todos (no solo admin) — Javier y Edison lo necesitan para
        # saber cuánto entregar al final del día.
        cobros_carro_dia = calcular_cobros_periodo(fecha_hoy(), fecha_hoy())
        raw_resumen_carro = [r for r in cobros_carro_dia["raw_ventas"] if r.get("canal") == "Carro"]
        cobro_creditos_carro_hoy = cobros_carro_dia["cobro_creditos_por_canal"].get("Carro", 0.0)
        if not raw_resumen_carro and not cobro_creditos_carro_hoy:
            st.info("Aún no hay ventas hoy.")
        else:
            bolsas_carro_dia = sum(r["cantidad"] for r in raw_resumen_carro if r["cantidad"] > 0)
            facturas_carro_dia = {fid: f for fid, f in cobros_carro_dia["facturas"].items() if f["canal"] == "Carro"}
            cobrado_ventas_carro_dia = sum(f["abono"] for f in facturas_carro_dia.values())
            cobrado_carro_dia = cobrado_ventas_carro_dia + cobro_creditos_carro_hoy
            credito_carro_dia = sum(f["saldo"] for f in facturas_carro_dia.values())
            fila_credito_viejo_carro = (
                f'<div class="factura-row"><span>{ICO_CARD} Cobrado en créditos viejos</span><span><b>{fmt(cobro_creditos_carro_hoy)}</b></span></div>'
                if cobro_creditos_carro_hoy > 0 else ""
            )
            st.markdown('<div class="section-label">Resumen del día — Javier & Edison</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="factura-box">'
                f'<div class="factura-row"><span>{ICO_CART} Bolsas vendidas hoy</span><span><b>{bolsas_carro_dia}</b></span></div>'
                f'<div class="factura-row"><span>{ICO_DOLLAR} Cobrado (ventas de hoy)</span><span><b>{fmt(cobrado_ventas_carro_dia)}</b></span></div>'
                f'{fila_credito_viejo_carro}'
                f'<div class="factura-row"><span>{ICO_CLIPBOARD} Dejado en crédito</span><span><b>{fmt(credito_carro_dia)}</b></span></div>'
                f'<div class="factura-total"><span>{ICO_DOLLAR} Total a entregar</span><span>{fmt(cobrado_carro_dia)}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            if cobro_creditos_carro_hoy > 0:
                st.markdown(f'<div class="warn-box">{ICO_CARD} Ojo: de los {fmt(cobrado_carro_dia)} a entregar, <b>{fmt(cobro_creditos_carro_hoy)}</b> son de créditos viejos que cobraron hoy, no de ventas nuevas — no lo olviden.</div>', unsafe_allow_html=True)

    with sub6:
        mostrar_creditos_pendientes("Carro")
        mostrar_historial_pagos_credito("Carro")

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: FÁBRICA
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "fabrica":

    sub_f1, sub_f2, sub_f3, sub_f4 = st.tabs(["💵 Registrar venta", "💳 Créditos", "🎁 Regalar", "📋 Resumen del día"])

    with sub_f1:
        render_venta_canal(CONFIG_FABRICA, mostrar_creditos=False)

    with sub_f2:
        mostrar_creditos_pendientes("Fábrica")
        mostrar_historial_pagos_credito("Fábrica")

    with sub_f3:
        st.markdown(f'<div class="section-label">Regalar bolsa {ICO_GIFT}</div>', unsafe_allow_html=True)
        st.caption("Registra las bolsas que se regalan — se descuentan del inventario pero no cuentan como venta.")

        stock_fab_r = get_inventario_completo()
        sabores_disp_fab_r = [s for s, v in stock_fab_r.items() if v > 0]

        if not sabores_disp_fab_r:
            st.markdown(f'<div class="warn-box">{ICO_WARN} No hay papas disponibles para regalar.</div>', unsafe_allow_html=True)
        else:
            sabor_reg_f = st.selectbox("Sabor", sabores_disp_fab_r, key="sabor_reg_fab")
            disp_reg_f = int(stock_fab_r.get(sabor_reg_f, 0))
            cant_reg_f = st.number_input("Cantidad", min_value=1, max_value=disp_reg_f, value=1, step=1, key="cant_reg_fab")
            vendedor_reg_f = st.radio("Vendedor", VENDEDORES_FABRICA, horizontal=True, key="vendedor_reg_fab")
            motivo_reg_f = st.text_input("Motivo (opcional)", placeholder="Ej: Cliente especial, muestra", key="motivo_reg_fab")
            st.markdown(f'<div class="info-box">{ICO_GIFT} Regalando <b>{cant_reg_f}</b> bolsas de <b>{sabor_reg_f}</b> · Quedan: <b>{disp_reg_f - cant_reg_f}</b></div>', unsafe_allow_html=True)

            if st.button("🎁 Registrar regalo", key="btn_reg_fab"):
                sb_post("ventas", {
                    "fecha": fecha_hoy(), "hora": ahora(), "canal": "Regalo Fábrica",
                    "vendedor": vendedor_reg_f, "sabor": sabor_reg_f,
                    "cantidad": cant_reg_f, "total": 0,
                    "cliente": motivo_reg_f.strip() if motivo_reg_f.strip() else "Regalo",
                    "factura_id": str(uuid.uuid4())[:8].upper(),
                    "abono": 0, "saldo": 0
                })
                restar_stock(sabor_reg_f, cant_reg_f)
                st.session_state.ok_reg_fab = True
                time.sleep(0.3)
                st.rerun()

        if st.session_state.get("ok_reg_fab"):
            st.markdown(f'<div class="success-toast">{ICO_CHECK} Regalo registrado. Descontado del inventario.</div>', unsafe_allow_html=True)
            st.session_state.ok_reg_fab = False

        # Historial de regalos del día
        raw_reg_f = sb_get("ventas", f"select=hora,sabor,cantidad,cliente,vendedor&fecha=eq.{fecha_hoy()}&canal=eq.{requests.utils.quote('Regalo Fábrica')}&order=hora.desc")
        if raw_reg_f:
            st.markdown('<div class="section-label">Regalos de hoy</div>', unsafe_allow_html=True)
            filas_reg_f = "".join(
                f'<div class="factura-row"><span>{r["hora"]} · {r["sabor"]} × {r["cantidad"]}</span><span>{r["cliente"]}</span></div>'
                for r in raw_reg_f
            )
            total_regalado_f = sum(r["cantidad"] for r in raw_reg_f)
            valor_regalado_f = sum(r["cantidad"] * PRODUCTOS.get(r["sabor"], 0) for r in raw_reg_f)
            st.markdown(
                f'<div class="factura-box">{filas_reg_f}'
                f'<div class="factura-row"><span>Total regalado hoy</span><span>{total_regalado_f} bolsas</span></div>'
                f'<div class="factura-total"><span>Valor que se dejó de cobrar</span><span>{fmt(valor_regalado_f)}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

    with sub_f4:
        # Visible para todos (no solo admin) — Sofía y Andrea lo necesitan para
        # saber cuánto entregar al final del día.
        cobros_fab_dia = calcular_cobros_periodo(fecha_hoy(), fecha_hoy())
        raw_vf = [r for r in cobros_fab_dia["raw_ventas"] if r.get("canal") in ("Fábrica", "Cambio")]
        cobro_creditos_fab_hoy = cobros_fab_dia["cobro_creditos_por_canal"].get("Fábrica", 0.0)
        if not raw_vf and not cobro_creditos_fab_hoy:
            st.info("Aún no hay ventas hoy.")
        else:
            bolsas_fab_dia = sum(r["cantidad"] for r in raw_vf if r["cantidad"] > 0)
            por_vendedor = {}
            for r in raw_vf:
                if r["total"] > 0:
                    v = r["vendedor"]
                    por_vendedor[v] = por_vendedor.get(v, 0) + r["total"]
            facturas_fab_dia = {fid: f for fid, f in cobros_fab_dia["facturas"].items() if f["canal"] in ("Fábrica", "Cambio")}
            cobrado_ventas_fab_dia = sum(f["abono"] for f in facturas_fab_dia.values())
            cobrado_fab_dia = cobrado_ventas_fab_dia + cobro_creditos_fab_hoy
            credito_fab_dia = sum(f["saldo"] for f in facturas_fab_dia.values())
            fila_credito_viejo_fab = (
                f'<div class="factura-row"><span>{ICO_CARD} Cobrado en créditos viejos</span><span><b>{fmt(cobro_creditos_fab_hoy)}</b></span></div>'
                if cobro_creditos_fab_hoy > 0 else ""
            )
            filas_v = "".join(
                f'<div class="factura-row"><span>{ICO_USER} {v}</span><span><b>{fmt(t)}</b></span></div>'
                for v, t in por_vendedor.items()
            )
            st.markdown('<div class="section-label">Resumen del día — Fábrica</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="factura-box">{filas_v}'
                f'<div class="factura-row"><span>{ICO_CART} Bolsas vendidas hoy</span><span><b>{bolsas_fab_dia}</b></span></div>'
                f'<div class="factura-row"><span>{ICO_DOLLAR} Cobrado (ventas de hoy)</span><span><b>{fmt(cobrado_ventas_fab_dia)}</b></span></div>'
                f'{fila_credito_viejo_fab}'
                f'<div class="factura-row"><span>{ICO_CLIPBOARD} Dejado en crédito</span><span><b>{fmt(credito_fab_dia)}</b></span></div>'
                f'<div class="factura-total"><span>{ICO_DOLLAR} Total a entregar</span><span>{fmt(cobrado_fab_dia)}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            if cobro_creditos_fab_hoy > 0:
                st.markdown(f'<div class="warn-box">{ICO_CARD} Ojo: de los {fmt(cobrado_fab_dia)} a entregar, <b>{fmt(cobro_creditos_fab_hoy)}</b> son de créditos viejos que cobraron hoy, no de ventas nuevas — no lo olviden.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: RESUMEN (solo admin)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "recibo":
    registros_recibo = st.session_state.get("recibo_canal_df", [])
    if registros_recibo:
        st.markdown(render_recibo(registros_recibo), unsafe_allow_html=True)

        # Botón imprimir
        # window.print() debe llamarse sobre la ventana padre: components.html()
        # renderiza este botón dentro de un iframe aislado, así que imprimir "aquí"
        # imprime el iframe vacío (solo el botón) en vez de la página con el recibo.
        # Por el mismo motivo, el <style> @media print se inyecta en el <head> del
        # documento padre, no en el del iframe.
        _html_btn_imprimir = """
        <div style="text-align:center;margin-top:12px;">
            <button onclick="window.parent.print()" style="
                background:#1565C0;color:white;border:none;
                border-radius:12px;padding:14px 32px;
                font-size:1rem;font-weight:700;cursor:pointer;
                box-shadow:0 4px 12px rgba(21,101,192,0.3);
            ">ICONO_PRINTER Imprimir recibo</button>
        </div>
        <script>
        (function() {
            var doc = window.parent.document;
            if (doc.getElementById("fabrica-print-style")) return;
            var style = doc.createElement("style");
            style.id = "fabrica-print-style";
            style.innerHTML = `
                @media print {
                    body * { visibility: hidden !important; }
                    .recibo-wrap, .recibo-wrap * { visibility: visible !important; }
                    .recibo-wrap {
                        position: absolute !important;
                        left: 0 !important; top: 0 !important;
                        width: 100% !important;
                        padding: 0 !important;
                    }
                    .recibo-ticket {
                        width: 58mm !important;
                        margin: 0 auto !important;
                        box-shadow: none !important;
                        font-size: 11px !important;
                    }
                }
            `;
            doc.head.appendChild(style);
        })();
        </script>
        """.replace("ICONO_PRINTER", ICO_PRINTER)
        components.html(_html_btn_imprimir, height=80)

        fid_recibo = registros_recibo[0].get("factura_id", "") if registros_recibo else ""
        canal_recibo = registros_recibo[0].get("canal", "") if registros_recibo else ""

        st.markdown("---")
        st.markdown(f'<div class="section-label">{ICO_WARN} Zona de administrador</div>', unsafe_allow_html=True)

        usuario_edicion = st.selectbox("¿Quién hace este cambio?", EMPLEADOS, key="usuario_edicion_fac")

        # Historial de cambios/eliminaciones sobre esta factura
        raw_auditoria = sb_get("factura_auditoria", f"select=hora,accion,detalle,usuario&factura_id=eq.{fid_recibo}&order=id.desc")
        if raw_auditoria:
            with st.expander(f"🕒 Historial de esta factura ({len(raw_auditoria)})"):
                for a in raw_auditoria:
                    st.markdown(
                        f'<div class="factura-row"><span>{a["hora"]} · <b>{a["accion"]}</b> — {a.get("detalle","")}</span>'
                        f'<span>{a.get("usuario","")}</span></div>',
                        unsafe_allow_html=True
                    )

        # Editar factura — funciona con facturas de cualquier fecha (no depende de
        # la sesión activa como el cambio/agregar del flujo de venta en vivo).
        cfg_edit = CONFIG_FABRICA if canal_recibo == "Fábrica" else CONFIG_CARRO
        vendedor_recibo = registros_recibo[0].get("vendedor", "") if registros_recibo else ""
        cliente_recibo = (registros_recibo[0].get("cliente", "") if registros_recibo else "") or "Consumidor Final"
        items_recibo, totales_recibo = _consolidar_items_recibo(registros_recibo)
        precios_recibo = {s: (totales_recibo[s] / c if c else 0) for s, c in items_recibo.items()}

        def _recargar_recibo():
            st.session_state.recibo_canal_df = sb_get("ventas", f"select=*&factura_id=eq.{fid_recibo}") or []

        def _ajustar_saldo(delta):
            _ajustar_saldo_ventas_cas(f"factura_id=eq.{fid_recibo}&canal=eq.{canal_recibo}", delta_saldo=delta)

        with st.expander("✏️ Editar factura"):
            if not items_recibo:
                st.caption("Esta factura no tiene productos activos para editar.")
            else:
                tab_ed_cambio, tab_ed_agregar, tab_ed_quitar = st.tabs(
                    ["🔁 Cambiar producto", "➕ Agregar producto", "➖ Quitar producto"])

                with tab_ed_cambio:
                    col_a, col_b = st.columns(2)
                    sabor_out = col_a.selectbox("Devuelve", list(items_recibo.keys()), key="edit_cambio_out")
                    max_out = items_recibo.get(sabor_out, 1)
                    cant_out = col_a.number_input("Cantidad que devuelve", min_value=1, max_value=max_out, value=1, step=1, key="edit_cant_out")

                    disp_cambio = cfg_edit["disponible_map_fn"]()
                    disp_cambio[sabor_out] = disp_cambio.get(sabor_out, 0) + cant_out
                    opciones_in = cfg_edit["sabores_post_venta_fn"](disp_cambio)
                    sabor_in = col_b.selectbox("Lleva en cambio", opciones_in, key="edit_cambio_in")
                    max_in = max(1, int(disp_cambio.get(sabor_in, 0)))
                    cant_in = col_b.number_input("Cantidad que lleva", min_value=1, max_value=max_in, value=1, step=1, key="edit_cant_in")

                    valor_out = precios_recibo.get(sabor_out, PRODUCTOS[sabor_out]) * cant_out
                    valor_in  = precios_recibo.get(sabor_in,  PRODUCTOS[sabor_in])  * cant_in
                    diferencia = valor_in - valor_out
                    if diferencia > 0:
                        st.markdown(f'<div class="warn-box">{ICO_DOLLAR} El cliente debe pagar <b>{fmt(diferencia)}</b> adicionales</div>', unsafe_allow_html=True)
                    elif diferencia < 0:
                        st.markdown(f'<div class="info-box">{ICO_DOLLAR} Hay que devolver <b>{fmt(abs(diferencia))}</b> al cliente</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="info-box">{ICO_CHECK} Cambio sin diferencia de valor</div>', unsafe_allow_html=True)

                    if st.button("🔁 Registrar cambio", key="edit_btn_cambio"):
                        sb_post("ventas", {
                            "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                            "vendedor": vendedor_recibo, "sabor": sabor_out,
                            "cantidad": -cant_out, "total": -valor_out,
                            "cliente": cliente_recibo, "factura_id": fid_recibo,
                            "abono": 0, "saldo": 0
                        })
                        if cfg_edit["mutar_stock"]:
                            agregar_stock(sabor_out, cant_out)
                        sb_post("ventas", {
                            "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                            "vendedor": vendedor_recibo, "sabor": sabor_in,
                            "cantidad": cant_in, "total": valor_in,
                            "cliente": cliente_recibo, "factura_id": fid_recibo,
                            "abono": 0, "saldo": 0
                        })
                        if cfg_edit["mutar_stock"]:
                            restar_stock(sabor_in, cant_in)
                        _ajustar_saldo(diferencia)
                        _registrar_auditoria_factura(
                            fid_recibo, "Cambio de producto",
                            f"Devuelve {cant_out} {sabor_out} · Lleva {cant_in} {sabor_in}",
                            usuario_edicion
                        )
                        _recargar_recibo()
                        time.sleep(0.3)
                        st.rerun()

                with tab_ed_agregar:
                    disp_add = cfg_edit["disponible_map_fn"]()
                    opciones_add = cfg_edit["sabores_post_venta_fn"](disp_add)
                    if not opciones_add:
                        st.markdown(f'<div class="warn-box">{ICO_WARN} No hay disponible para agregar.</div>', unsafe_allow_html=True)
                    else:
                        sabor_add = st.selectbox("Sabor a agregar", opciones_add, key="edit_add_sabor")
                        max_add = max(1, int(disp_add.get(sabor_add, 0)))
                        cant_add = st.number_input("Cantidad", min_value=1, max_value=max_add, value=1, step=1, key="edit_add_cant")
                        precio_add = precios_recibo.get(sabor_add, PRODUCTOS[sabor_add]) * cant_add
                        st.markdown(f'<div class="info-box">{ICO_PACKAGE} Disponible: <b>{max_add}</b> · {ICO_DOLLAR} A cobrar: <b>{fmt(precio_add)}</b></div>', unsafe_allow_html=True)

                        if st.button("➕ Agregar a la factura", key="edit_btn_add"):
                            sb_post("ventas", {
                                "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                                "vendedor": vendedor_recibo, "sabor": sabor_add,
                                "cantidad": cant_add, "total": precio_add,
                                "cliente": cliente_recibo, "factura_id": fid_recibo,
                                "abono": 0, "saldo": 0
                            })
                            if cfg_edit["mutar_stock"]:
                                restar_stock(sabor_add, cant_add)
                            _ajustar_saldo(precio_add)
                            _registrar_auditoria_factura(
                                fid_recibo, "Agregar producto",
                                f"+{cant_add} {sabor_add} ({fmt(precio_add)})",
                                usuario_edicion
                            )
                            _recargar_recibo()
                            time.sleep(0.3)
                            st.rerun()

                with tab_ed_quitar:
                    sabor_quitar = st.selectbox("Producto a quitar", list(items_recibo.keys()), key="edit_quitar_sabor")
                    max_quitar = items_recibo.get(sabor_quitar, 1)
                    cant_quitar = st.number_input("Cantidad a quitar", min_value=1, max_value=max_quitar, value=1, step=1, key="edit_quitar_cant")
                    valor_quitar = precios_recibo.get(sabor_quitar, PRODUCTOS[sabor_quitar]) * cant_quitar
                    st.markdown(f'<div class="info-box">{ICO_DOLLAR} Se descuenta <b>{fmt(valor_quitar)}</b> de la factura</div>', unsafe_allow_html=True)

                    if st.button("➖ Quitar de la factura", key="edit_btn_quitar"):
                        sb_post("ventas", {
                            "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                            "vendedor": vendedor_recibo, "sabor": sabor_quitar,
                            "cantidad": -cant_quitar, "total": -valor_quitar,
                            "cliente": cliente_recibo, "factura_id": fid_recibo,
                            "abono": 0, "saldo": 0
                        })
                        if cfg_edit["mutar_stock"]:
                            agregar_stock(sabor_quitar, cant_quitar)
                        _ajustar_saldo(-valor_quitar)
                        _registrar_auditoria_factura(
                            fid_recibo, "Quitar producto",
                            f"-{cant_quitar} {sabor_quitar} ({fmt(valor_quitar)})",
                            usuario_edicion
                        )
                        _recargar_recibo()
                        time.sleep(0.3)
                        st.rerun()

        # Eliminar factura — visible para todos
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
                _registrar_auditoria_factura(
                    fid_recibo, "Eliminar factura",
                    f"{cliente_recibo} · {fmt(sum(totales_recibo.values()))}",
                    usuario_edicion
                )
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
        ("Salsa de tomate (unidad)", "🍅", "unidad", "mp"),
        ("Chicharrón (bulto)",     "🥩", "bulto",   "mp"),
        ("Tocineta (bulto)",       "🥓", "bulto",   "mp"),
    ]
    SABORIZANTES_INFO = [
        ("BBQ Normal",    "🧂", "kg", "sab"),
        ("BBQ Dulce",     "🧂", "kg", "sab"),
        ("Limón",         "🧂", "kg", "sab"),
        ("Sal",           "🧂", "kg", "sab"),
        ("Pollo",         "🧂", "kg", "sab"),
        ("Parrillada",    "🧂", "kg", "sab"),
        ("Chorizo Limón", "🧂", "kg", "sab"),
        ("Mayonesa",      "🧂", "kg", "sab"),
        ("Queso Cheddar",   "🧂", "kg", "sab"),
        ("Queso Agridulce", "🧂", "kg", "sab"),
        ("Queso Picante",   "🧂", "kg", "sab"),
        ("Picante",       "🧂", "kg", "sab"),
        ("Pimienta",      "🧂", "kg", "sab"),
    ]
    EMPAQUES_INFO = [
        ("Transparente",       "📦", "kg", "emp"),
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

    UMBRAL_ROLLO_AGOTADO = 1.0  # kg — por debajo de esto se considera que el rollo se acabó

    def registrar_entrada_mp(nombre_sel, unidad_sel, cant_mp, prov_mp, precio_mp, abono_mp, saldo_mp, precio_unit_mp=0, fecha_mp=None, es_stock_existente=False, numero_factura_mp=""):
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
            "precio_unitario": float(precio_unit_mp),
            "numero_factura": numero_factura_mp.strip() or None
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
            opciones_ins = cats[st.session_state.categoria_mp]
            datos_por_etiqueta = {f"{icono}  {nombre}": (nombre, unidad, cat) for nombre, icono, unidad, cat in opciones_ins}
            etiqueta_ins_sel = st.radio(
                "Insumo", list(datos_por_etiqueta.keys()),
                key="radio_insumo_mp", label_visibility="collapsed"
            )
            if st.button("Continuar →", key="btn_confirmar_ins", use_container_width=True):
                st.session_state.insumo_sel = datos_por_etiqueta[etiqueta_ins_sel]
                st.session_state.pop("radio_insumo_mp", None)
                st.rerun()
            if st.button("← Volver", key="btn_volver_cat"):
                st.session_state.categoria_mp = None
                st.session_state.pop("radio_insumo_mp", None)
                st.rerun()

        else:
            nombre_sel, unidad_sel, cat_sel = st.session_state.insumo_sel
            con_credito = cat_sel != "emp"
            st.markdown(f'<div class="section-label">Entrada — {nombre_sel}</div>', unsafe_allow_html=True)

            raw_ent_actual = sb_get("materia_prima", f"select=cantidad&insumo=eq.{requests.utils.quote(nombre_sel)}") or []
            raw_sal_actual = sb_get("salidas_mp",    f"select=cantidad&insumo=eq.{requests.utils.quote(nombre_sel)}") or []
            stock_actual_ins = max(0, sum(float(r["cantidad"]) for r in raw_ent_actual) - sum(float(r["cantidad"]) for r in raw_sal_actual))
            st.markdown(f'<div class="info-box">{ICO_PACKAGE} Stock disponible de <b>{nombre_sel}</b>: <b>{stock_actual_ins:.3f} {unidad_sel}</b></div>', unsafe_allow_html=True)

            fecha_mp = st.date_input("Fecha de la entrada", value=datetime.now(COL_TZ).date(), max_value=datetime.now(COL_TZ).date(), key="fecha_mp")
            if fecha_mp != datetime.now(COL_TZ).date():
                st.markdown(f'<div class="warn-box">{ICO_CALENDAR} Se registrará con fecha {fecha_mp}, no con la de hoy.</div>', unsafe_allow_html=True)
            cant_mp        = st.number_input(f"Cantidad ({unidad_sel})", min_value=0.001, max_value=999999.0, value=1.0, step=0.001, format="%.3f", key="cant_mp")

            tipo_entrada_mp = st.radio(
                "Tipo de entrada",
                ["🆕 Compra nueva", "📦 Ya tengo este insumo"],
                horizontal=True,
                key="tipo_entrada_mp",
                help="\"Ya tengo este insumo\" suma al stock que ya tenías. No se descuenta de caja ni queda como deuda con el proveedor."
            )
            ya_tengo_mp = tipo_entrada_mp == "📦 Ya tengo este insumo"

            prov_mp = st.text_input(
                "Proveedor (opcional)" if ya_tengo_mp else "Proveedor",
                placeholder="Ej: Stock existente" if ya_tengo_mp else "Ej: Distribuidora La 14",
                key="prov_mp"
            )
            numero_factura_mp = ""
            if not ya_tengo_mp:
                numero_factura_mp = st.text_input(
                    "N° de factura (opcional)",
                    placeholder="Ej: 4521",
                    help="Si dos entregas del mismo proveedor caen el mismo día, este número las separa en Créditos.",
                    key="numero_factura_mp"
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
                if registrar_entrada_mp(nombre_sel, unidad_sel, cant_mp, prov_mp, precio_mp, abono_mp, saldo_mp, precio_unit_mp, fecha_mp, es_stock_existente=ya_tengo_mp, numero_factura_mp=numero_factura_mp):
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
                f"select=id,fecha,hora,cantidad,precio_unitario,precio_total,abono,saldo,estado,proveedor&insumo=eq.{requests.utils.quote(nombre_sel)}&fecha=gte.{primer_dia}&fecha=lte.{hoy_ins}&order=fecha.desc,hora.desc") or []
            if raw_ins_mes:
                total_cant_mes = sum(float(r["cantidad"]) for r in raw_ins_mes)
                st.caption(f"Total ingresado este mes: {total_cant_mes:.3f} {unidad_sel} — toca cualquier celda para editar, luego Guardar cambios.")
                df_ins_mes = pd.DataFrame(raw_ins_mes)
                df_edit_mp = df_ins_mes[["fecha", "hora", "cantidad", "precio_unitario", "proveedor"]].copy()
                df_edit_mp.columns = ["Fecha", "Hora", f"Cantidad ({unidad_sel})", "Precio unitario", "Proveedor"]

                edited_mp = st.data_editor(
                    df_edit_mp,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Fecha":                      st.column_config.TextColumn("Fecha"),
                        "Hora":                       st.column_config.TextColumn("Hora"),
                        f"Cantidad ({unidad_sel})":   st.column_config.NumberColumn(f"Cantidad ({unidad_sel})", min_value=0.001, step=0.001, format="%.3f"),
                        "Precio unitario":            st.column_config.NumberColumn("Precio unitario", min_value=0, step=1000),
                        "Proveedor":                  st.column_config.TextColumn("Proveedor"),
                    },
                    key=f"mp_editor_{nombre_sel}"
                )

                col_gmp, col_dmp = st.columns(2)
                if col_gmp.button("💾 Guardar cambios", key="btn_save_mp"):
                    for i, row in edited_mp.iterrows():
                        orig = df_ins_mes.iloc[i]
                        cambios = {}

                        fecha_new = str(row["Fecha"])
                        hora_new  = str(row["Hora"])
                        cant_new  = float(row[f"Cantidad ({unidad_sel})"])
                        pu_new    = float(row["Precio unitario"])
                        prov_new  = str(row["Proveedor"])

                        if fecha_new != str(orig["fecha"]):
                            cambios["fecha"] = fecha_new
                        if hora_new != str(orig["hora"]):
                            cambios["hora"] = hora_new
                        if prov_new != str(orig["proveedor"]):
                            cambios["proveedor"] = prov_new

                        cant_orig = float(orig["cantidad"])
                        pu_orig = float(orig["precio_unitario"] or 0)
                        if cant_new != cant_orig or pu_new != pu_orig:
                            precio_total_new = round(pu_new * cant_new)
                            precio_total_orig = float(orig["precio_total"] or 0)
                            saldo_new = max(0.0, float(orig["saldo"] or 0) + (precio_total_new - precio_total_orig))
                            cambios["cantidad"] = cant_new
                            cambios["precio_unitario"] = pu_new
                            cambios["precio_total"] = precio_total_new
                            cambios["saldo"] = saldo_new
                            cambios["estado"] = "pagado" if saldo_new == 0 else "pendiente"

                        if cambios:
                            sb_patch("materia_prima", f"id=eq.{orig['id']}", cambios)
                    time.sleep(1)
                    st.rerun()

                def _fmt_cant_mp(c):
                    return f"{float(c):.3f}" if unidad_sel == "kg" else c
                ids_mp = {f"{r['fecha']} {r['hora']} — {_fmt_cant_mp(r['cantidad'])} {unidad_sel} — {r['proveedor']}": r for r in raw_ins_mes}
                sel_del_mp = st.selectbox("Eliminar registro", ["— Selecciona —"] + list(ids_mp.keys()), key="sel_del_mp")
                if sel_del_mp != "— Selecciona —" and col_dmp.button("🗑️ Eliminar", key="btn_del_mp"):
                    reg_del_mp = ids_mp[sel_del_mp]
                    sb_delete("materia_prima", f"id=eq.{reg_del_mp['id']}")
                    time.sleep(0.3)
                    st.rerun()
            else:
                st.caption(f"Aún no hay entradas de {nombre_sel} este mes.")

        if st.session_state.get("ok_mp"):
            st.markdown(f'<div class="success-toast">{ICO_CHECK} Entrada registrada.</div>', unsafe_allow_html=True)
            st.session_state.ok_mp = False

    with tab_mp2:
        st.markdown('<div class="section-label">Registrar salida (uso en producción)</div>', unsafe_allow_html=True)
        cat_sal = st.radio("Categoría", ["🌽 Materia Prima", "🧪 Saborizantes", "📦 Empaque"], key="cat_sal")
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

        if cat_key == "emp":
            st.caption("Pesa el rollo antes y después de producir. La próxima vez que uses ese mismo rollo, el peso inicial ya viene precargado con el último peso registrado — no hace falta pesarlo de nuevo hasta que se acabe.")

            insumo_rollo = st.radio("Empaque", opciones_sal, key="rollo_insumo")

            raw_rollo = sb_get("rollos_empaque", f"select=*&insumo=eq.{requests.utils.quote(insumo_rollo)}&limit=1") or []
            rollo_previo = raw_rollo[0] if raw_rollo else None
            hay_rollo_activo = rollo_previo is not None and float(rollo_previo["peso_actual"]) >= UMBRAL_ROLLO_AGOTADO

            key_peso_inicial = f"rollo_peso_inicial_nuevo_{insumo_rollo}"
            key_peso_cono     = f"rollo_peso_cono_{insumo_rollo}"
            key_peso_final    = f"rollo_peso_final_{insumo_rollo}"

            # Stock disponible en bodega (total comprado - total consumido), igual que en
            # Materia Prima/Saborizantes — evita pesar un rollo "nuevo" que no está
            # respaldado por ninguna Entrada registrada.
            raw_ent_emp = sb_get("materia_prima", f"select=cantidad&insumo=eq.{requests.utils.quote(insumo_rollo)}") or []
            raw_sal_emp = sb_get("salidas_mp",    f"select=cantidad&insumo=eq.{requests.utils.quote(insumo_rollo)}") or []
            stock_disp_emp = max(0.0, sum(float(r["cantidad"]) for r in raw_ent_emp) - sum(float(r["cantidad"]) for r in raw_sal_emp))

            if stock_disp_emp == 0:
                st.markdown(f'<div class="alert-low">{ICO_DOT_RED} No hay stock disponible de <b>{insumo_rollo}</b> en bodega. Registra una entrada primero.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="info-box">{ICO_PACKAGE} Stock disponible de <b>{insumo_rollo}</b> en bodega: <b>{stock_disp_emp:.3f} kg</b></div>', unsafe_allow_html=True)

            fecha_sal_rollo = st.date_input("Fecha de la salida", value=datetime.now(COL_TZ).date(), max_value=datetime.now(COL_TZ).date(), key=f"fecha_sal_rollo_{insumo_rollo}")
            if str(fecha_sal_rollo) != fecha_hoy():
                st.markdown(f'<div class="warn-box">{ICO_CALENDAR} Se registrará con fecha {fecha_sal_rollo}, no con la de hoy.</div>', unsafe_allow_html=True)

            if hay_rollo_activo:
                peso_inicial_rollo = float(rollo_previo["peso_actual"])
                st.markdown(f'<div class="info-box">{ICO_PACKAGE} Rollo activo de <b>{insumo_rollo}</b> — peso inicial (último registrado): <b>{peso_inicial_rollo:.3f} kg</b></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="warn-box">{ICO_WARN} No hay rollo activo de <b>{insumo_rollo}</b>. Pesa el rollo nuevo que sacaste de bodega y anota su peso inicial.</div>', unsafe_allow_html=True)
                # Sin max_value ligado al stock: el peso en báscula es bruto (incluye el cono),
                # así que casi siempre supera el stock neto registrado — un tope ahí recortaba el
                # valor tecleado sin avisar (ej. escribir 30 con stock=25 lo dejaba en 25 sin que
                # se notara). El tope contra el stock se valida después, sobre el peso ya neto.
                peso_bruto_rollo = st.number_input(
                    "Peso en báscula del rollo nuevo (incluye cono de cartón, kg)",
                    min_value=0.001, value=1.0,
                    step=0.001, format="%.3f", key=key_peso_inicial
                )
                peso_cono_rollo = st.number_input(
                    "Peso del cono de cartón (dato de la etiqueta, kg)",
                    min_value=0.0, max_value=peso_bruto_rollo,
                    value=0.0, step=0.001, format="%.3f", key=key_peso_cono
                )
                peso_inicial_rollo = max(0.0, peso_bruto_rollo - peso_cono_rollo)
                tope_stock_emp = max(0.001, stock_disp_emp)
                if peso_inicial_rollo > tope_stock_emp:
                    st.markdown(f'<div class="alert-low">{ICO_WARN} El peso real ({peso_inicial_rollo:.3f}kg) supera el stock disponible en bodega ({stock_disp_emp:.3f}kg) — revisa el peso o registra una entrada. Por ahora se limita a {tope_stock_emp:.3f}kg.</div>', unsafe_allow_html=True)
                    peso_inicial_rollo = tope_stock_emp
                st.markdown(f'<div class="calc-box">⚖️ Peso real del empaque (sin cono): <b>{peso_inicial_rollo:.3f} kg</b></div>', unsafe_allow_html=True)

            peso_final_rollo = st.number_input(
                "Peso final (después de producir, kg)",
                min_value=0.0, max_value=peso_inicial_rollo, value=peso_inicial_rollo,
                step=0.001, format="%.3f", key=key_peso_final
            )
            consumo_rollo = max(0.0, peso_inicial_rollo - peso_final_rollo)
            st.markdown(f'<div class="calc-box">⚖️ Consumo de esta producción: <b>{consumo_rollo:.3f} kg</b></div>', unsafe_allow_html=True)

            if peso_final_rollo < UMBRAL_ROLLO_AGOTADO:
                st.markdown(f'<div class="warn-box">{ICO_WARN} Con este peso final, el rollo queda por debajo de {UMBRAL_ROLLO_AGOTADO:.0f}kg — la próxima vez la app va a pedir pesar un rollo nuevo.</div>', unsafe_allow_html=True)

            sin_stock_para_rollo_nuevo = not hay_rollo_activo and stock_disp_emp <= 0
            if st.button("📤 Registrar salida", key="btn_rollo_registrar", disabled=(consumo_rollo <= 0 or sin_stock_para_rollo_nuevo)):
                ok_salida = sb_post("salidas_mp", {
                    "fecha": str(fecha_sal_rollo), "hora": ahora(), "insumo": insumo_rollo,
                    "categoria": "emp", "cantidad": consumo_rollo, "unidad": "kg",
                    "motivo": "Producción (control de rollo)",
                    "peso_antes": peso_inicial_rollo, "peso_despues": peso_final_rollo
                })
                if ok_salida:
                    # Si la fecha elegida es más vieja que el último estado registrado del rollo
                    # (backdateando un papel atrasado después de ya haber pesado en tiempo real),
                    # no tocamos peso_actual/fecha — el registro histórico ya quedó en salidas_mp,
                    # pero el "estado actual" del rollo (lo que se precarga la próxima vez) no
                    # debe retroceder.
                    es_backdate_viejo = rollo_previo is not None and str(fecha_sal_rollo) < rollo_previo["fecha"]
                    if es_backdate_viejo:
                        ok_rollo = True
                    elif rollo_previo:
                        ok_rollo = sb_patch("rollos_empaque", f"id=eq.{rollo_previo['id']}", {"peso_actual": peso_final_rollo, "fecha": str(fecha_sal_rollo), "hora": ahora()})
                    else:
                        ok_rollo = sb_post("rollos_empaque", {"insumo": insumo_rollo, "peso_actual": peso_final_rollo, "fecha": str(fecha_sal_rollo), "hora": ahora()})
                    if ok_rollo:
                        # Sin esto, Streamlit reusa el último valor tecleado en estas keys la
                        # próxima vez (aunque cambie el "value=" por defecto) — por eso al
                        # agotarse un rollo, el campo de peso inicial nuevo mostraba el peso
                        # del rollo anterior en vez de pedir uno limpio.
                        for k in (key_peso_inicial, key_peso_cono, key_peso_final):
                            st.session_state.pop(k, None)
                        st.markdown(f'<div class="success-toast">{ICO_CHECK} Pesaje registrado — {consumo_rollo:.3f}kg de {insumo_rollo} descontados del stock de empaque.</div>', unsafe_allow_html=True)
                        if es_backdate_viejo:
                            st.markdown(f'<div class="warn-box">{ICO_CALENDAR} Como esta fecha es anterior al último pesaje registrado ({rollo_previo["fecha"]}), no se modificó el estado actual del rollo — solo quedó guardado el registro histórico.</div>', unsafe_allow_html=True)
                        time.sleep(0.3); st.rerun()

            raw_hist_rollo = sb_get(
                "salidas_mp",
                f"select=id,fecha,hora,peso_antes,peso_despues,cantidad&insumo=eq.{requests.utils.quote(insumo_rollo)}"
                "&peso_antes=not.is.null&order=fecha.desc,hora.desc&limit=5"
            ) or []
            if raw_hist_rollo:
                st.markdown('<div class="section-label">Últimos pesajes</div>', unsafe_allow_html=True)
                df_hist_rollo = pd.DataFrame([{
                    "Fecha": r["fecha"], "Hora": r["hora"],
                    "Peso antes": f'{float(r["peso_antes"]):.3f}',
                    "Peso después": f'{float(r["peso_despues"]):.3f}',
                    "Consumo": f'{float(r["cantidad"]):.3f}',
                } for r in raw_hist_rollo])
                tabla_view(df_hist_rollo)

                ids_hist_rollo = {f"{r['fecha']} {r['hora']} — {float(r['peso_antes']):.3f}→{float(r['peso_despues']):.3f}kg": r for r in raw_hist_rollo}
                sel_del_hist_rollo = st.selectbox("Eliminar registro", ["— Selecciona —"] + list(ids_hist_rollo.keys()), key="sel_del_hist_rollo")
                if sel_del_hist_rollo != "— Selecciona —" and st.button("🗑️ Eliminar", key="btn_del_hist_rollo"):
                    reg_del_hist_rollo = ids_hist_rollo[sel_del_hist_rollo]
                    # Si el registro borrado era el que definía el peso_actual del rollo activo
                    # (mismo fecha/hora/peso_despues guardados en rollos_empaque), hay que
                    # retroceder al pesaje anterior — si no, la app se queda mostrando un
                    # "rollo activo" con un peso que ya no está respaldado por ningún registro.
                    era_el_estado_actual = (
                        rollo_previo is not None
                        and rollo_previo["fecha"] == reg_del_hist_rollo["fecha"]
                        and rollo_previo["hora"] == reg_del_hist_rollo["hora"]
                        and float(rollo_previo["peso_actual"]) == float(reg_del_hist_rollo["peso_despues"])
                    )
                    sb_delete("salidas_mp", f"id=eq.{reg_del_hist_rollo['id']}")
                    if era_el_estado_actual:
                        raw_anterior_rollo = sb_get(
                            "salidas_mp",
                            f"select=fecha,hora,peso_despues&insumo=eq.{requests.utils.quote(insumo_rollo)}"
                            "&peso_antes=not.is.null&order=fecha.desc,hora.desc&limit=1"
                        ) or []
                        if raw_anterior_rollo:
                            ant = raw_anterior_rollo[0]
                            sb_patch("rollos_empaque", f"id=eq.{rollo_previo['id']}", {"peso_actual": float(ant["peso_despues"]), "fecha": ant["fecha"], "hora": ant["hora"]})
                        else:
                            sb_delete("rollos_empaque", f"id=eq.{rollo_previo['id']}")
                    time.sleep(0.3)
                    st.rerun()

        else:
            insumo_sal = st.radio("Insumo", opciones_sal, key="insumo_sal")
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
                st.markdown(f'<div class="info-box">{ICO_PACKAGE} Stock disponible de <b>{insumo_sal}</b>: <b>{stock_disp_sal:.3f} {unidad_sal}</b></div>', unsafe_allow_html=True)

            fecha_sal = st.date_input("Fecha de la salida", value=datetime.now(COL_TZ).date(), max_value=datetime.now(COL_TZ).date(), key="fecha_sal")
            if str(fecha_sal) != fecha_hoy():
                st.markdown(f'<div class="warn-box">{ICO_CALENDAR} Se registrará con fecha {fecha_sal}, no con la de hoy.</div>', unsafe_allow_html=True)
            cant_sal = st.number_input(f"Cantidad ({unidad_sal})", min_value=0.001,
                                        max_value=max(0.001, stock_disp_sal),
                                        value=min(1.0, max(0.001, stock_disp_sal)),
                                        step=0.001, format="%.3f", key="cant_sal")
            motivo_sal = st.text_input("Motivo", value="Producción", key="motivo_sal")

            if st.button("📤 Registrar salida", key="btn_sal", disabled=(stock_disp_sal == 0)):
                h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"}
                data_sal = {"fecha": str(fecha_sal), "hora": ahora(), "insumo": insumo_sal,
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

        def _icono_cred(insumo):
            if insumo in SABORIZANTES_NAMES:
                return ICO_FLASK
            if insumo in EMPAQUES_NAMES:
                return ICO_PACKAGE
            return ICO_LAYERS

        def mostrar_creditos_mp(lista, state_key):
            if not lista:
                st.info("No hay créditos pendientes."); return

            prov_sel_cred = st.session_state.get(state_key)

            if not prov_sel_cred:
                por_proveedor = {}
                for r in lista:
                    k = r["proveedor"]
                    if k not in por_proveedor:
                        por_proveedor[k] = {"saldo": 0.0, "n": 0}
                    por_proveedor[k]["saldo"] += float(r["saldo"])
                    por_proveedor[k]["n"] += 1
                total = sum(float(r["saldo"]) for r in lista)
                st.markdown(f'<div class="warn-box">{ICO_CARD} Total pendiente: <b>{fmt(total)}</b></div>', unsafe_allow_html=True)
                for k in sorted(por_proveedor.keys()):
                    v = por_proveedor[k]
                    if st.button(f"👤 {k} — {fmt(v['saldo'])} ({v['n']})", key=f"btn_cred_prov_{state_key}_{k}", use_container_width=True):
                        st.session_state[state_key] = k; st.rerun()
                return

            if st.button("← Volver", key=f"btn_cred_volver_{state_key}"):
                st.session_state[state_key] = None; st.rerun()

            lista_prov = [r for r in lista if r["proveedor"] == prov_sel_cred]
            total_prov = sum(float(r["saldo"]) for r in lista_prov)
            st.markdown(f'<div class="warn-box">{ICO_CARD} Total pendiente a {prov_sel_cred}: <b>{fmt(total_prov)}</b></div>', unsafe_allow_html=True)

            # Agrupa por número de factura cuando se anotó uno; si no, cae de vuelta a
            # agrupar por fecha (comportamiento anterior, para registros viejos sin número).
            # Así dos entregas del mismo proveedor el mismo día no se mezclan si tienen
            # número de factura distinto.
            facturas_prov = {}
            for r in lista_prov:
                num_f = (r.get("numero_factura") or "").strip()
                clave = f"N-{num_f}" if num_f else f"F-{r['fecha']}"
                facturas_prov.setdefault(clave, []).append(r)

            def _orden_factura(clave):
                lineas = facturas_prov[clave]
                return max(r["fecha"] for r in lineas)

            for clave in sorted(facturas_prov.keys(), key=_orden_factura, reverse=True):
                lineas = facturas_prov[clave]
                total_f = sum(float(r["precio_total"]) for r in lineas)
                abono_f = sum(float(r["abono"]) for r in lineas)
                saldo_f = sum(float(r["saldo"]) for r in lineas)
                num_f = (lineas[0].get("numero_factura") or "").strip()
                fecha_f = lineas[0]["fecha"] if len(set(r["fecha"] for r in lineas)) == 1 else f'{min(r["fecha"] for r in lineas)} a {max(r["fecha"] for r in lineas)}'
                titulo_f = f"Factura N° {num_f} · {fecha_f}" if num_f else f"Factura {fecha_f}"

                filas_html = ""
                for r in lineas:
                    cant_disp_r = f'{float(r["cantidad"]):.3f}' if r["unidad"] == "kg" else r["cantidad"]
                    filas_html += (
                        f'<div class="factura-row"><span>{_icono_cred(r["insumo"])} {r["insumo"]}'
                        f' ({cant_disp_r} {r["unidad"]})</span><span>{fmt(r["precio_total"])}</span></div>'
                    )

                st.markdown(
                    f'<div class="factura-box"><div class="factura-header">🧾 {titulo_f} · {prov_sel_cred}</div>'
                    f'{filas_html}'
                    f'<div class="factura-row"><span>Total</span><span>{fmt(total_f)}</span></div>'
                    f'<div class="factura-row"><span>Abonado</span><span>{fmt(abono_f)}</span></div>'
                    f'<div class="factura-total"><span>Saldo</span><span>{fmt(saldo_f)}</span></div></div>',
                    unsafe_allow_html=True
                )
                col_a, col_b = st.columns([3, 1])
                nv = col_a.number_input("Abono ($)", min_value=0, max_value=int(saldo_f), value=int(saldo_f), step=1000, key=f"abono_pend_mp_{state_key}_{prov_sel_cred}_{clave}")
                if col_b.button("✅ Pagar", key=f"btn_pagar_mp_{state_key}_{prov_sel_cred}_{clave}"):
                    restante = nv
                    for r in lineas:
                        if restante <= 0:
                            break
                        saldo_r = float(r["saldo"])
                        if saldo_r <= 0:
                            continue
                        pago_r = min(restante, saldo_r)
                        nuevo_saldo = saldo_r - pago_r
                        sb_patch("materia_prima", f"id=eq.{r['id']}", {"abono": float(r["abono"]) + pago_r, "saldo": nuevo_saldo, "estado": "pagado" if nuevo_saldo == 0 else "pendiente"})
                        restante -= pago_r
                    time.sleep(0.3); st.rerun()

        st.markdown('<div class="section-label">Créditos — Todos los proveedores</div>', unsafe_allow_html=True)
        mostrar_creditos_mp(raw_pend, "credito_sel_mp")

        st.markdown('<div class="section-label">🕒 Historial de créditos pagados</div>', unsafe_allow_html=True)
        col_hcp1, col_hcp2 = st.columns(2)
        f_ini_hcp = col_hcp1.date_input("Desde", value=datetime.now(COL_TZ).date().replace(day=1), key="f_ini_hist_cred_mp")
        f_fin_hcp = col_hcp2.date_input("Hasta", value=datetime.now(COL_TZ).date(), key="f_fin_hist_cred_mp")

        raw_pagados_mp = sb_get("materia_prima", f"select=*&estado=eq.pagado&abono=gt.0&fecha=gte.{f_ini_hcp}&fecha=lte.{f_fin_hcp}&order=fecha.desc") or []
        if not raw_pagados_mp:
            st.caption("No hay créditos pagados en ese rango.")
        else:
            total_pagado_hcp = sum(float(r["precio_total"]) for r in raw_pagados_mp)
            st.markdown(f'<div class="info-box">{ICO_DOLLAR} Total pagado en el rango: <b>{fmt(total_pagado_hcp)}</b></div>', unsafe_allow_html=True)

            busqueda_hcp = st.text_input("🔍 Buscar por proveedor", key="buscar_hist_cred_mp", placeholder="Ej: Don Carlos")
            filas_hcp = raw_pagados_mp
            if busqueda_hcp.strip():
                filas_hcp = [r for r in filas_hcp if _coincide_nombre(busqueda_hcp, r.get("proveedor") or "")]

            if not filas_hcp:
                st.caption("No hay créditos pagados para ese proveedor en ese rango.")
            else:
                df_hist_cred_mp = pd.DataFrame([{
                    "Fecha": r["fecha"],
                    "Proveedor": r["proveedor"],
                    "N° Factura": (r.get("numero_factura") or "—"),
                    "Insumo": r["insumo"],
                    "Cantidad": f'{float(r["cantidad"]):.3f}' if r["unidad"] == "kg" else r["cantidad"],
                    "Total": fmt(r["precio_total"]),
                } for r in filas_hcp])
                with st.container(height=420):
                    tabla_view(df_hist_cred_mp)

    with tab_mp4:
        st.markdown('<div class="section-label">Resumen del período</div>', unsafe_allow_html=True)
        col_f1, col_f2 = st.columns(2)
        f_ini_mp = col_f1.date_input("Desde", value=datetime.now(COL_TZ).date().replace(day=1), key="f_ini_mp")
        f_fin_mp = col_f2.date_input("Hasta", value=datetime.now(COL_TZ).date(), key="f_fin_mp")

        raw_ent = sb_get("materia_prima", f"select=*&fecha=gte.{f_ini_mp}&fecha=lte.{f_fin_mp}&order=fecha.desc") or []
        raw_sal = sb_get("salidas_mp",    f"select=*&fecha=gte.{f_ini_mp}&fecha=lte.{f_fin_mp}&order=fecha.desc") or []

        # Stock actual real y precio promedio (acumulado de siempre, no solo del período
        # filtrado arriba) — así el valor del inventario no cambia según qué rango se elija.
        raw_ent_todo = sb_get("materia_prima", "select=insumo,cantidad,precio_unitario,precio_total") or []
        raw_sal_todo = sb_get("salidas_mp", "select=insumo,cantidad") or []
        stock_actual_todo = {}
        for r in raw_ent_todo:
            stock_actual_todo[r["insumo"]] = stock_actual_todo.get(r["insumo"], 0) + float(r["cantidad"])
        for r in raw_sal_todo:
            stock_actual_todo[r["insumo"]] = stock_actual_todo.get(r["insumo"], 0) - float(r["cantidad"])

        # Promedio ponderado por insumo sobre TODO el histórico de compras (no el período
        # filtrado): total_costo/total_cant por insumo, usado tanto en la tabla por categoría
        # como en el total general de abajo.
        prom_pond_todo = {}
        for r in raw_ent_todo:
            k = r["insumo"]
            pu = float(r.get("precio_unitario", 0))
            cant = float(r.get("cantidad", 0))
            if pu > 0 and cant > 0:
                if k not in prom_pond_todo:
                    prom_pond_todo[k] = {"total_costo": 0, "total_cant": 0}
                prom_pond_todo[k]["total_costo"] += pu * cant
                prom_pond_todo[k]["total_cant"]  += cant

        # El total de $ invertido en inventario se ve en Contador (solo admin) — aquí solo
        # se mantiene el detalle operativo por insumo/categoría.
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
                filas_res = []
                for k, v in data.items():
                    d = prom_pond_todo.get(k, {"total_costo": 0, "total_cant": 0})
                    pu_prom = round(d["total_costo"] / d["total_cant"]) if d["total_cant"] > 0 else 0
                    costo_consumido = round(v["salidas"] * pu_prom) if pu_prom > 0 else 0
                    es_kg = v["unidad"] == "kg"
                    stock_actual = round(max(0.0, stock_actual_todo.get(k, 0)), 3 if es_kg else 1)
                    stock_val = round(stock_actual * pu_prom) if pu_prom > 0 else 0
                    nombre_disp = k[:-4] if titulo == "Empaque" and k.endswith(" emp") else k
                    filas_res.append({
                        "Insumo": nombre_disp,
                        "Entradas": f'{v["entradas"]:.3f}' if es_kg else v["entradas"],
                        "Salidas": f'{v["salidas"]:.3f}' if es_kg else v["salidas"],
                        "Stock": f'{stock_actual:.3f}' if es_kg else stock_actual,
                        "Precio prom. pond.": fmt(pu_prom) if pu_prom > 0 else "—",
                        "Costo consumido": fmt(costo_consumido) if costo_consumido > 0 else "—",
                        "Inventario total": fmt(stock_val) if stock_val > 0 else "—",
                    })
                tabla_view(pd.DataFrame(filas_res))
                # Nota explicativa
                st.caption("💡 Precio promedio ponderado: promedio de todo el histórico de compras (no solo el período filtrado arriba), ponderado por cantidad ingresada.")
            else:
                st.info("No hay registros en este período.")

        if resumen or raw_ent or raw_sal:
            res_mp  = {k: v for k, v in resumen.items() if k not in SABORIZANTES_NAMES and k not in EMPAQUES_NAMES}
            res_sab = {n: resumen.get(n, {"entradas": 0, "salidas": 0, "unidad": u, "gasto": 0}) for n, _, u, _ in SABORIZANTES_INFO}
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

elif st.session_state.vista == "caja" and st.session_state.es_admin:
    st.markdown(f'<div class="section-label">{ICO_DOLLAR} Caja</div>', unsafe_allow_html=True)
    tab_caja1, tab_caja2, tab_caja3, tab_caja4, tab_caja5 = st.tabs(["📊 Resumen", "➕ Ingreso / Egreso", "📋 Historial", "🧮 Arqueo de caja", "🎯 Reservas"])

    # Fechas del período
    hoy_caja = datetime.now(COL_TZ).date()
    primer_dia_caja = hoy_caja.replace(day=1)

    with tab_caja1:
        st.markdown('<div class="section-label">Resumen de caja</div>', unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        f_ini_caja = col_c1.date_input("Desde", value=primer_dia_caja, key="f_ini_caja")
        f_fin_caja = col_c2.date_input("Hasta", value=hoy_caja, key="f_fin_caja")

        # INGRESOS — ventas pagadas (total - saldo = abonado) y cobros de créditos
        with ThreadPoolExecutor(max_workers=3) as ex:
            f_cobros = ex.submit(calcular_cobros_periodo, f_ini_caja, f_fin_caja)
            f_mp = ex.submit(sb_get, "materia_prima", f"select=fecha,insumo,proveedor,precio_total,abono&fecha=gte.{f_ini_caja}&fecha=lte.{f_fin_caja}&order=fecha.desc")
            f_ing = ex.submit(sb_get, "caja_ingresos", f"select=*&fecha=gte.{f_ini_caja}&fecha=lte.{f_fin_caja}&order=fecha.desc")
        cobros_caja = f_cobros.result()
        raw_mp_pagos = f_mp.result() or []
        raw_egresos = sb_get("caja_egresos", f"select=*&fecha=gte.{f_ini_caja}&fecha=lte.{f_fin_caja}&order=fecha.desc") or []
        raw_ingresos_manuales = f_ing.result() or []

        # Solo Fábrica y Carro cuentan como caja real (Regalo/Cambio no mueven plata).
        ingresos_ventas = sum(f["abono"] for f in cobros_caja["facturas"].values() if f["canal"] in ("Fábrica", "Carro"))
        ingresos_cobro_creditos = (
            cobros_caja["cobro_creditos_por_canal"].get("Fábrica", 0.0)
            + cobros_caja["cobro_creditos_por_canal"].get("Carro", 0.0)
        )

        ingresos_manuales = sum(float(r["valor"]) for r in raw_ingresos_manuales)
        total_ingresos = ingresos_ventas + ingresos_cobro_creditos + ingresos_manuales

        # Egresos: pagos de materia prima + gastos varios
        egresos_mp = sum(float(r["abono"]) for r in raw_mp_pagos)
        egresos_gastos = sum(float(r["valor"]) for r in raw_egresos)
        total_egresos = egresos_mp + egresos_gastos

        saldo_caja = total_ingresos - total_egresos

        # Plata ya apartada en las reservas (Papa/Empaque) — no cuenta como libre
        # para proveedores/nómina aunque siga físicamente en la caja mayor.
        raw_reservas_resumen = sb_get("reservas_caja", "select=movimiento,monto") or []
        acumulado_reservas = sum(
            float(r["monto"]) if r["movimiento"] == "aporte" else -float(r["monto"])
            for r in raw_reservas_resumen
        )
        disponible_libre = saldo_caja - acumulado_reservas

        # Tarjetas resumen
        color_saldo = "metric-green" if saldo_caja >= 0 else "metric-red"
        color_disp = "metric-green" if disponible_libre >= 0 else "metric-red"
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-box metric-blue"><div class="val">{fmt(total_ingresos)}</div><div class="lbl">Ingresos</div></div>
            <div class="metric-box metric-yellow"><div class="val">{fmt(total_egresos)}</div><div class="lbl">Egresos</div></div>
            <div class="metric-box {color_saldo}"><div class="val">{fmt(saldo_caja)}</div><div class="lbl">Saldo caja</div></div>
            <div class="metric-box {color_disp}"><div class="val">{fmt(disponible_libre)}</div><div class="lbl">Libre para proveedores/nómina</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"💡 De los {fmt(saldo_caja)} en caja, {fmt(acumulado_reservas)} ya están apartados en reservas (ver pestaña 🎯 Reservas) — el resto es lo que realmente puedes usar libremente.")

        # Cuentas por cobrar/pagar y costo de producción se ven en Contador (solo admin).

        # Detalle ingresos
        if ingresos_ventas > 0 or ingresos_cobro_creditos > 0 or ingresos_manuales > 0:
            st.markdown('<div class="section-label">Detalle ingresos</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="factura-box">'
                f'<div class="factura-row"><span>{ICO_DOLLAR} Ventas</span><span><b>{fmt(ingresos_ventas)}</b></span></div>'
                f'<div class="factura-row"><span>{ICO_CARD} Cobro de créditos</span><span><b>{fmt(ingresos_cobro_creditos)}</b></span></div>'
                f'<div class="factura-row"><span>{ICO_NOTE} Dinero existente / aportes</span><span><b>{fmt(ingresos_manuales)}</b></span></div>'
                f'<div class="factura-total"><span>Total ingresos</span><span>{fmt(total_ingresos)}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

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
        tipo_mov = st.radio("Tipo de movimiento", ["📤 Egreso (gasto)", "📥 Ingreso (dinero existente)"], key="tipo_mov_caja")

        if tipo_mov == "📤 Egreso (gasto)":
            st.markdown('<div class="section-label">Registrar egreso / gasto</div>', unsafe_allow_html=True)
            concepto_eg = st.text_input("Concepto", placeholder="Ej: Pago arriendo, gas, luz...", key="concepto_eg")
            cat_eg = st.selectbox("Categoría", ["Servicios", "Arriendo", "Transporte", "Mantenimiento", "Salario", "Otro"], key="cat_eg")
            tipo_eg_label = st.radio(
                "¿Este gasto es de producción o administrativo/ventas?",
                ["🏭 Costo de producción (planta)", "🏢 Gasto operativo (admin/ventas)"],
                key="tipo_eg",
                help="Para el costo de producción (mano de obra de planta, servicios/mantenimiento de la fábrica) vs. gastos que no entran al costo del producto (arriendo de oficina, transporte de venta, etc.)."
            )
            tipo_eg = "costo" if "producción" in tipo_eg_label else "gasto"
            empleado_eg = ""
            if cat_eg == "Salario":
                empleado_eg = st.text_input("Nombre del empleado", placeholder="Ej: Juan Pérez", key="empleado_eg")
            valor_eg = st.number_input("Valor ($)", min_value=0, value=0, step=1000, key="valor_eg")

            if st.button("✅ Registrar egreso", key="btn_eg"):
                if not concepto_eg.strip():
                    st.markdown(f'<div class="alert-low">{ICO_WARN} Escribe el concepto del egreso.</div>', unsafe_allow_html=True)
                elif valor_eg == 0:
                    st.markdown(f'<div class="alert-low">{ICO_WARN} Ingresa el valor.</div>', unsafe_allow_html=True)
                elif cat_eg == "Salario" and not empleado_eg.strip():
                    st.markdown(f'<div class="alert-low">{ICO_WARN} Escribe el nombre del empleado.</div>', unsafe_allow_html=True)
                else:
                    h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json", "Prefer": "return=minimal"}
                    data_eg = {"fecha": fecha_hoy(), "hora": ahora(),
                               "concepto": concepto_eg.strip(), "valor": float(valor_eg), "categoria": cat_eg,
                               "tipo": tipo_eg, "empleado": empleado_eg.strip() or None}
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
        else:
            st.markdown('<div class="section-label">Registrar ingreso (dinero existente)</div>', unsafe_allow_html=True)
            st.caption("Úsalo para sumar a caja dinero que ya tenías (efectivo inicial, aportes, etc.) sin que cuente como una venta.")
            concepto_in = st.text_input("Concepto", placeholder="Ej: Efectivo en caja al iniciar", key="concepto_in")
            cat_in = st.selectbox("Categoría", ["Dinero existente en caja", "Aporte / capital", "Otro ingreso"], key="cat_in")
            valor_in = st.number_input("Valor ($)", min_value=0, value=0, step=1000, key="valor_in")

            if st.button("✅ Registrar ingreso", key="btn_in"):
                if not concepto_in.strip():
                    st.markdown(f'<div class="alert-low">{ICO_WARN} Escribe el concepto del ingreso.</div>', unsafe_allow_html=True)
                elif valor_in == 0:
                    st.markdown(f'<div class="alert-low">{ICO_WARN} Ingresa el valor.</div>', unsafe_allow_html=True)
                else:
                    h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json", "Prefer": "return=minimal"}
                    data_in = {"fecha": fecha_hoy(), "hora": ahora(),
                               "concepto": concepto_in.strip(), "valor": float(valor_in), "categoria": cat_in}
                    try:
                        r_in = requests.post(f"{SUPABASE_URL}/rest/v1/caja_ingresos", headers=h, json=data_in, timeout=10)
                        if r_in.ok:
                            st.markdown(f'<div class="success-toast">{ICO_CHECK} Ingreso registrado.</div>', unsafe_allow_html=True)
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(f"Error: {r_in.status_code} — {r_in.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab_caja3:
        st.markdown('<div class="section-label">Historial de movimientos</div>', unsafe_allow_html=True)
        col_h1, col_h2 = st.columns(2)
        f_ini_h = col_h1.date_input("Desde", value=primer_dia_caja, key="f_ini_h")
        f_fin_h = col_h2.date_input("Hasta", value=hoy_caja, key="f_fin_h")

        movimientos = []

        # Pagos de crédito de todo el histórico — se necesita completo (no solo el rango
        # filtrado) para poder restar de cada factura lo que se cobró después de la venta.
        raw_pg_h = sb_get("pagos_credito", "select=*") or []
        cobrado_despues_h = {}
        for r in raw_pg_h:
            if r.get("tipo") == "venta" and r.get("factura_id"):
                fid = r["factura_id"]
                cobrado_despues_h[fid] = cobrado_despues_h.get(fid, 0) + float(r["monto"])

        # Ingresos por ventas — solo el abono que existía al momento de la venta (lo
        # cobrado después vía créditos se cuenta aparte, más abajo, en su fecha real).
        raw_v_h = sb_get("ventas", f"select=fecha,hora,canal,cliente,factura_id,abono,saldo&fecha=gte.{f_ini_h}&fecha=lte.{f_fin_h}&canal=in.(Fábrica,Carro)&order=fecha.desc,hora.desc") or []
        facturas_h = set()
        for r in raw_v_h:
            fid = r.get("factura_id", "")
            if fid and fid not in facturas_h:
                abono_inicial = max(0.0, float(r.get("abono", 0)) - cobrado_despues_h.get(fid, 0))
                facturas_h.add(fid)
                if abono_inicial > 0:
                    movimientos.append({
                        "Fecha": r["fecha"], "Hora": r["hora"],
                        "Concepto": f'Venta {r["canal"]} — {r["cliente"]}',
                        "Categoría": "Ingreso ventas",
                        "Ingreso": fmt(abono_inicial), "Egreso": "—"
                    })

        # Ingresos por cobro de créditos (ventas y créditos antiguos), en la fecha real
        # del cobro.
        for r in raw_pg_h:
            fecha_pg = date.fromisoformat(r["fecha"])
            if f_ini_h <= fecha_pg <= f_fin_h:
                ref = f'FV-{r["factura_id"]}' if r.get("tipo") == "venta" else "Crédito antiguo"
                movimientos.append({
                    "Fecha": r["fecha"], "Hora": r.get("hora", ""),
                    "Concepto": f'Cobro crédito — {r.get("cliente","")} ({ref})',
                    "Categoría": "Cobro créditos",
                    "Ingreso": fmt(r["monto"]), "Egreso": "—"
                })

        # Ingresos manuales (dinero existente / aportes)
        raw_ing_h = sb_get("caja_ingresos", f"select=*&fecha=gte.{f_ini_h}&fecha=lte.{f_fin_h}&order=fecha.desc") or []
        for r in raw_ing_h:
            movimientos.append({
                "Fecha": r["fecha"], "Hora": r["hora"],
                "Concepto": r["concepto"],
                "Categoría": r["categoria"],
                "Ingreso": fmt(r["valor"]), "Egreso": "—"
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
            with st.container(height=420):
                tabla_view(pd.DataFrame(movimientos))
        else:
            st.info("No hay movimientos en ese período.")

    with tab_caja4:
        st.markdown('<div class="section-label">Arqueo de caja</div>', unsafe_allow_html=True)
        st.caption("Compara el efectivo que el sistema esperaba tener contra lo que contaste físicamente, para detectar si falta o sobra plata.")

        fecha_arq = st.date_input("Fecha del arqueo", value=hoy_caja, max_value=hoy_caja, key="fecha_arqueo")
        fecha_arq_str = str(fecha_arq)

        with ThreadPoolExecutor(max_workers=3) as ex:
            f_cobros_a = ex.submit(calcular_cobros_periodo, fecha_arq_str, fecha_arq_str)
            f_mp_a = ex.submit(sb_get, "materia_prima", f"select=abono&fecha=eq.{fecha_arq_str}")
            f_ing_a = ex.submit(sb_get, "caja_ingresos", f"select=valor&fecha=eq.{fecha_arq_str}")
        cobros_a = f_cobros_a.result()
        raw_mp_a = f_mp_a.result() or []
        raw_ing_a = f_ing_a.result() or []
        raw_eg_a = sb_get("caja_egresos", f"select=valor&fecha=eq.{fecha_arq_str}") or []

        ingresos_ventas_a = sum(f["abono"] for f in cobros_a["facturas"].values() if f["canal"] in ("Fábrica", "Carro"))
        ingresos_cobro_creditos_a = (
            cobros_a["cobro_creditos_por_canal"].get("Fábrica", 0.0)
            + cobros_a["cobro_creditos_por_canal"].get("Carro", 0.0)
        )
        ingresos_manuales_a = sum(float(r["valor"]) for r in raw_ing_a)
        total_ingresos_a = ingresos_ventas_a + ingresos_cobro_creditos_a + ingresos_manuales_a

        egresos_mp_a = sum(float(r["abono"]) for r in raw_mp_a)
        egresos_gastos_a = sum(float(r["valor"]) for r in raw_eg_a)
        total_egresos_a = egresos_mp_a + egresos_gastos_a

        # El efectivo con el que se abrió caja ese día se sugiere con lo contado en
        # el último arqueo anterior — así no hay que acordarse del número a mano.
        raw_arq_prev = sb_get("arqueos_caja", f"select=fecha,efectivo_contado&fecha=lt.{fecha_arq_str}&order=fecha.desc&limit=1") or []
        efectivo_inicial_sugerido = float(raw_arq_prev[0]["efectivo_contado"]) if raw_arq_prev else 0.0

        efectivo_inicial_a = st.number_input(
            "Efectivo con el que abriste caja ese día ($)",
            min_value=0, value=int(efectivo_inicial_sugerido), step=1000, key="efectivo_inicial_arqueo",
            help="Se sugiere con lo contado en el último arqueo anterior. Ajústalo si es distinto."
        )

        efectivo_esperado_a = efectivo_inicial_a + total_ingresos_a - total_egresos_a
        st.markdown(
            f'<div class="factura-box">'
            f'<div class="factura-row"><span>Efectivo inicial</span><span>{fmt(efectivo_inicial_a)}</span></div>'
            f'<div class="factura-row"><span>{ICO_DOLLAR} Ingresos del día</span><span>{fmt(total_ingresos_a)}</span></div>'
            f'<div class="factura-row"><span>{ICO_NOTE} Egresos del día</span><span>{fmt(total_egresos_a)}</span></div>'
            f'<div class="factura-total"><span>Efectivo esperado</span><span>{fmt(efectivo_esperado_a)}</span></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        efectivo_contado_a = st.number_input(
            "Efectivo contado físicamente ($)",
            min_value=0, value=max(0, int(efectivo_esperado_a)), step=1000, key="efectivo_contado_arqueo"
        )
        diferencia_a = efectivo_contado_a - efectivo_esperado_a

        if diferencia_a == 0:
            st.markdown(f'<div class="info-box">{ICO_CHECK} Cuadra exacto. Diferencia: <b>$0</b></div>', unsafe_allow_html=True)
        elif diferencia_a < 0:
            st.markdown(f'<div class="alert-low">{ICO_WARN} Falta <b>{fmt(abs(diferencia_a))}</b></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warn-box">{ICO_WARN} Sobra <b>{fmt(diferencia_a)}</b></div>', unsafe_allow_html=True)

        empleado_arq = st.selectbox("¿Quién hace este arqueo?", EMPLEADOS, key="empleado_arqueo")

        if st.button("💾 Guardar arqueo", key="btn_guardar_arqueo"):
            ok_arq = sb_post("arqueos_caja", {
                "fecha": fecha_arq_str, "hora": ahora(), "empleado": empleado_arq,
                "efectivo_inicial": float(efectivo_inicial_a), "ingresos_dia": float(total_ingresos_a),
                "egresos_dia": float(total_egresos_a), "efectivo_esperado": float(efectivo_esperado_a),
                "efectivo_contado": float(efectivo_contado_a), "diferencia": float(diferencia_a)
            })
            if ok_arq:
                st.markdown(f'<div class="success-toast">{ICO_CHECK} Arqueo guardado.</div>', unsafe_allow_html=True)
                time.sleep(0.3); st.rerun()

        st.markdown('<div class="section-label">Últimos arqueos</div>', unsafe_allow_html=True)
        raw_hist_arq = sb_get("arqueos_caja", "select=fecha,empleado,efectivo_esperado,efectivo_contado,diferencia&order=fecha.desc&limit=30") or []
        if raw_hist_arq:
            df_hist_arq = pd.DataFrame([{
                "Fecha": r["fecha"], "Quién": r.get("empleado") or "—",
                "Esperado": fmt(r["efectivo_esperado"]), "Contado": fmt(r["efectivo_contado"]),
                "Diferencia": fmt(r["diferencia"]),
            } for r in raw_hist_arq])
            tabla_view(df_hist_arq)
        else:
            st.caption("Aún no hay arqueos guardados.")

    with tab_caja5:
        st.markdown('<div class="section-label">Reservas dentro de caja mayor</div>', unsafe_allow_html=True)
        st.caption("Papa y Empaque son compras grandes y poco frecuentes — aparta la plata acá antes de gastar la caja mayor en otra cosa, para no quedarte corto cuando toque comprar.")

        raw_reservas = sb_get("reservas_caja", "select=*&order=fecha.desc,hora.desc") or []
        acumulado_por_tipo = {"Papa": 0.0, "Empaque": 0.0}
        for r in raw_reservas:
            signo = 1 if r["movimiento"] == "aporte" else -1
            acumulado_por_tipo[r["tipo"]] = acumulado_por_tipo.get(r["tipo"], 0.0) + signo * float(r["monto"])

        for tipo_res in ["Papa", "Empaque"]:
            meta_res = RESERVA_META[tipo_res]
            acumulado_res = max(0.0, acumulado_por_tipo.get(tipo_res, 0.0))
            avance = min(1.0, acumulado_res / meta_res) if meta_res > 0 else 0.0
            st.markdown(f'**{tipo_res}** — {fmt(acumulado_res)} de {fmt(meta_res)}')
            st.progress(avance)

        st.markdown('<div class="section-label">Registrar movimiento</div>', unsafe_allow_html=True)
        tipo_mov_res = st.radio("Reserva", ["Papa", "Empaque"], horizontal=True, key="tipo_res_sel")
        mov_res = st.radio(
            "Movimiento", ["➕ Aporte (apartar plata)", "➖ Uso (se compró)"],
            horizontal=True, key="mov_res_sel"
        )
        monto_res = st.number_input("Monto ($)", min_value=0, value=0, step=1000, key="monto_res")
        nota_res = st.text_input("Nota (opcional)", key="nota_res", placeholder="Ej: Abono semanal reserva Papa")

        if st.button("💾 Guardar movimiento", key="btn_guardar_reserva"):
            if monto_res == 0:
                st.markdown(f'<div class="alert-low">{ICO_WARN} Ingresa el monto.</div>', unsafe_allow_html=True)
            else:
                ok_res = sb_post("reservas_caja", {
                    "fecha": fecha_hoy(), "hora": ahora(), "tipo": tipo_mov_res,
                    "movimiento": "aporte" if "Aporte" in mov_res else "uso",
                    "monto": float(monto_res), "nota": nota_res.strip() or None
                })
                if ok_res:
                    st.markdown(f'<div class="success-toast">{ICO_CHECK} Movimiento guardado.</div>', unsafe_allow_html=True)
                    time.sleep(0.3); st.rerun()

        st.markdown('<div class="section-label">Historial de reservas</div>', unsafe_allow_html=True)
        if raw_reservas:
            df_res = pd.DataFrame([{
                "Fecha": r["fecha"], "Reserva": r["tipo"],
                "Movimiento": "Aporte" if r["movimiento"] == "aporte" else "Uso",
                "Monto": fmt(r["monto"]), "Nota": r.get("nota") or "—",
            } for r in raw_reservas])
            tabla_view(df_res)
        else:
            st.caption("Aún no hay movimientos de reserva.")

elif st.session_state.vista == "resumen" and st.session_state.es_admin:
    sub_r1, sub_r2, sub_r3, sub_r5, sub_r4 = st.tabs(["Hoy", "Por fechas", "📅 Mes", "💳 Créditos pagados", "💾 Exportar"])

    with sub_r1:
        st.markdown('<div class="section-label">Resumen del día</div>', unsafe_allow_html=True)
        cobros_hoy = calcular_cobros_periodo(fecha_hoy(), fecha_hoy())
        raw_vt = cobros_hoy["raw_ventas"]
        cobro_creditos_hoy_por_canal = cobros_hoy["cobro_creditos_por_canal"]

        if not raw_vt and not cobro_creditos_hoy_por_canal:
            st.info("Aún no hay ventas hoy.")
        else:
            facturas_hoy = cobros_hoy["facturas"]
            cobrado_fab   = sum(f["abono"] for f in facturas_hoy.values() if f["canal"] == "Fábrica") + cobro_creditos_hoy_por_canal.get("Fábrica", 0.0)
            cobrado_carro = sum(f["abono"] for f in facturas_hoy.values() if f["canal"] == "Carro")   + cobro_creditos_hoy_por_canal.get("Carro", 0.0)
            pendiente_hoy = sum(f["saldo"] for f in facturas_hoy.values()) + _pendiente_creditos_antiguos(fecha_hoy(), fecha_hoy())

            # Bolsas regaladas hoy, valoradas al precio normal — no mueven caja (total=0
            # en la venta), así que sin esto el costo de lo regalado no se veía en ninguna parte.
            reg_hoy = [r for r in (raw_vt or []) if r.get("canal") in ("Regalo", "Regalo Fábrica")]
            bolsas_reg_hoy = sum(r["cantidad"] for r in reg_hoy)
            valor_reg_hoy = sum(r["cantidad"] * PRODUCTOS.get(r["sabor"], 0) for r in reg_hoy)

            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-blue"><div class="val">{fmt(cobrado_fab)}</div><div class="lbl">Fábrica</div></div>
                <div class="metric-box metric-yellow"><div class="val">{fmt(cobrado_carro)}</div><div class="lbl">Carro</div></div>
                <div class="metric-box metric-green"><div class="val">{fmt(cobrado_fab+cobrado_carro)}</div><div class="lbl">Total cobrado</div></div>
                <div class="metric-box metric-red"><div class="val">{fmt(pendiente_hoy)}</div><div class="lbl">Pendiente en créditos</div></div>
            </div>""", unsafe_allow_html=True)
            st.caption("💰 \"Total cobrado\" incluye ventas de hoy y créditos viejos cobrados hoy. Los créditos sin pagar aparecen aparte, en \"Pendiente en créditos\".")

            if bolsas_reg_hoy > 0:
                st.markdown(
                    f'<div class="warn-box">{ICO_GIFT} Regalado hoy: <b>{bolsas_reg_hoy} bolsas</b> · '
                    f'valor que se dejó de cobrar: <b>{fmt(valor_reg_hoy)}</b></div>',
                    unsafe_allow_html=True
                )

        if raw_vt:
            df_vt = pd.DataFrame(raw_vt)
            st.markdown('<div class="section-label">Por sabor</div>', unsafe_allow_html=True)
            por_sabor = df_vt.groupby("sabor").agg(bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
            por_sabor = por_sabor.sort_values("total", ascending=False)

            chart_data = por_sabor.set_index("sabor")["bolsas"]
            grafica_barras_sabor(por_sabor["sabor"].tolist(), por_sabor["bolsas"].tolist(), "bolsas vendidas")

            por_sabor["total"] = por_sabor["total"].apply(fmt)
            por_sabor.columns = ["Sabor","Bolsas","Total $"]
            tabla_view(por_sabor)

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
        cobros_rango = calcular_cobros_periodo(f_ini, f_fin)
        raw_rango = cobros_rango["raw_ventas"]
        cobro_creditos_rango_por_canal = cobros_rango["cobro_creditos_por_canal"]

        if not raw_rango and not cobro_creditos_rango_por_canal:
            st.info("No hay ventas en ese rango.")
        else:
            df_r = pd.DataFrame(raw_rango) if raw_rango else pd.DataFrame()
            bolsas_r = int(df_r["cantidad"].sum()) if not df_r.empty else 0
            dias_r   = df_r["fecha"].nunique() if not df_r.empty else 0

            facturas_rango = cobros_rango["facturas"]
            cobrado_fab_r = sum(f["abono"] for f in facturas_rango.values() if f["canal"] == "Fábrica") + cobro_creditos_rango_por_canal.get("Fábrica", 0.0)
            cobrado_carro_r = sum(f["abono"] for f in facturas_rango.values() if f["canal"] == "Carro") + cobro_creditos_rango_por_canal.get("Carro", 0.0)
            pendiente_fab_r = sum(f["saldo"] for f in facturas_rango.values() if f["canal"] == "Fábrica") + _pendiente_creditos_antiguos(f_ini, f_fin, "Fábrica")
            pendiente_carro_r = sum(f["saldo"] for f in facturas_rango.values() if f["canal"] == "Carro") + _pendiente_creditos_antiguos(f_ini, f_fin, "Carro")
            pendiente_r = pendiente_fab_r + pendiente_carro_r

            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-blue"><div class="val">{fmt(cobrado_fab_r)}</div><div class="lbl">Fábrica</div></div>
                <div class="metric-box metric-yellow"><div class="val">{fmt(cobrado_carro_r)}</div><div class="lbl">Carro</div></div>
                <div class="metric-box metric-green"><div class="val">{fmt(cobrado_fab_r+cobrado_carro_r)}</div><div class="lbl">Total cobrado</div></div>
                <div class="metric-box metric-red"><div class="val">{fmt(pendiente_r)}</div><div class="lbl">Pendiente en créditos</div></div>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-blue"><div class="val">{bolsas_r}</div><div class="lbl">Bolsas</div></div>
                <div class="metric-box metric-yellow"><div class="val">{dias_r}</div><div class="lbl">Días</div></div>
            </div>""", unsafe_allow_html=True)
            st.caption("💰 \"Cobrado\" es el dinero que efectivamente entró. Los créditos sin pagar se muestran aparte.")

            # Bolsas regaladas en el rango, valoradas al precio normal — no mueven caja.
            reg_r = [r for r in raw_rango if r.get("canal") in ("Regalo", "Regalo Fábrica")]
            bolsas_reg_r = sum(r["cantidad"] for r in reg_r)
            valor_reg_r = sum(r["cantidad"] * PRODUCTOS.get(r["sabor"], 0) for r in reg_r)
            if bolsas_reg_r > 0:
                st.markdown(
                    f'<div class="warn-box">{ICO_GIFT} Regalado en el rango: <b>{bolsas_reg_r} bolsas</b> · '
                    f'valor que se dejó de cobrar: <b>{fmt(valor_reg_r)}</b></div>',
                    unsafe_allow_html=True
                )

            if not df_r.empty:
                st.markdown('<div class="section-label">Por día</div>', unsafe_allow_html=True)
                por_dia = df_r.groupby("fecha").agg(bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
                por_dia["total"] = por_dia["total"].apply(fmt)
                por_dia.columns  = ["Fecha","Bolsas","Total $"]
                tabla_view(por_dia)

                st.markdown('<div class="section-label">Por canal</div>', unsafe_allow_html=True)
                por_canal_base = df_r.groupby("canal").agg(bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
                cobrado_por_canal = {"Fábrica": cobrado_fab_r, "Carro": cobrado_carro_r}
                pendiente_por_canal = {"Fábrica": pendiente_fab_r, "Carro": pendiente_carro_r}
                por_canal_base["Cobrado (dinero real)"] = por_canal_base["canal"].map(cobrado_por_canal).fillna(0).apply(fmt)
                por_canal_base["Pendiente (crédito)"]   = por_canal_base["canal"].map(pendiente_por_canal).fillna(0).apply(fmt)
                por_canal_base["total"] = por_canal_base["total"].apply(fmt)
                por_canal_base.columns  = ["Canal","Bolsas","Total $","Cobrado (dinero real)","Pendiente (crédito)"]
                tabla_view(por_canal_base)

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

        raw_prod_mes = sb_get("produccion", f"select=cantidad&fecha=gte.{primer_dia}&fecha=lte.{ultimo_dia}")

        cobros_mes = calcular_cobros_periodo(primer_dia, ultimo_dia)
        raw_mes = cobros_mes["raw_ventas"]
        cobro_creditos_mes = cobros_mes["cobro_creditos_total"]

        if not raw_mes and cobro_creditos_mes == 0:
            st.info("Aún no hay ventas este mes.")
        else:
            df_mes = pd.DataFrame(raw_mes) if raw_mes else pd.DataFrame()
            bolsas_mes  = int(df_mes["cantidad"].sum()) if not df_mes.empty else 0
            dias_mes    = df_mes["fecha"].nunique() if not df_mes.empty else 0
            prod_mes    = sum(r["cantidad"] for r in raw_prod_mes) if raw_prod_mes else 0

            facturas_mes = cobros_mes["facturas"]
            cobrado_mes   = sum(f["abono"] for f in facturas_mes.values()) + cobro_creditos_mes
            pendiente_mes = sum(f["saldo"] for f in facturas_mes.values()) + _pendiente_creditos_antiguos(primer_dia, ultimo_dia)
            promedio_dia  = cobrado_mes / dias_mes if dias_mes > 0 else 0

            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-green"><div class="val">{fmt(cobrado_mes)}</div><div class="lbl">Cobrado del mes</div></div>
                <div class="metric-box metric-blue"><div class="val">{bolsas_mes}</div><div class="lbl">Bolsas vendidas</div></div>
                <div class="metric-box metric-yellow"><div class="val">{fmt(promedio_dia)}</div><div class="lbl">Promedio diario</div></div>
                <div class="metric-box metric-red"><div class="val">{fmt(pendiente_mes)}</div><div class="lbl">Pendiente en créditos</div></div>
            </div>""", unsafe_allow_html=True)
            st.caption("💰 \"Cobrado\" incluye ventas del mes y créditos viejos cobrados este mes. Los créditos sin pagar se muestran aparte.")

            # Bolsas regaladas en el mes, valoradas al precio normal — no mueven caja.
            reg_mes = [r for r in raw_mes if r.get("canal") in ("Regalo", "Regalo Fábrica")]
            bolsas_reg_mes = sum(r["cantidad"] for r in reg_mes)
            valor_reg_mes = sum(r["cantidad"] * PRODUCTOS.get(r["sabor"], 0) for r in reg_mes)
            if bolsas_reg_mes > 0:
                st.markdown(
                    f'<div class="warn-box">{ICO_GIFT} Regalado este mes: <b>{bolsas_reg_mes} bolsas</b> · '
                    f'valor que se dejó de cobrar: <b>{fmt(valor_reg_mes)}</b></div>',
                    unsafe_allow_html=True
                )

            st.markdown(f'<div class="info-box">{ICO_PACKAGE} Producción total del mes: <b>{prod_mes} bolsas</b></div>', unsafe_allow_html=True)

            if not df_mes.empty:
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
                tabla_view(top_sabores)

    with sub_r5:
        st.markdown('<div class="section-label">Créditos pagados</div>', unsafe_allow_html=True)
        st.caption("Cobros de créditos, con la fecha real en que se pagaron (no la fecha de la venta original).")
        col_p1, col_p2 = st.columns(2)
        f_ini_pg = col_p1.date_input("Desde", value=date(datetime.now(COL_TZ).year, datetime.now(COL_TZ).month, 1), key="f_ini_pg")
        f_fin_pg = col_p2.date_input("Hasta", value=datetime.now(COL_TZ).date(), key="f_fin_pg")

        raw_pagos = sb_get("pagos_credito", f"select=*&fecha=gte.{f_ini_pg}&fecha=lte.{f_fin_pg}&order=fecha.desc,hora.desc")

        if not raw_pagos:
            st.info("No hay créditos pagados en ese rango. (Si acabas de habilitar esta función, revisa que la tabla 'pagos_credito' ya exista en Supabase.)")
        else:
            df_pg = pd.DataFrame(raw_pagos)
            total_pg = df_pg["monto"].sum()
            total_pg_fab = df_pg[df_pg["canal"]=="Fábrica"]["monto"].sum()
            total_pg_carro = df_pg[df_pg["canal"]=="Carro"]["monto"].sum()

            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-blue"><div class="val">{fmt(total_pg_fab)}</div><div class="lbl">Fábrica</div></div>
                <div class="metric-box metric-yellow"><div class="val">{fmt(total_pg_carro)}</div><div class="lbl">Carro</div></div>
                <div class="metric-box metric-green"><div class="val">{fmt(total_pg)}</div><div class="lbl">Total cobrado</div></div>
            </div>""", unsafe_allow_html=True)

            busqueda_pg = st.text_input("🔍 Buscar por cliente", key="buscar_pago_credito", placeholder="Ej: Don Carlos")
            if busqueda_pg.strip():
                df_pg = df_pg[df_pg["cliente"].apply(lambda c: _coincide_nombre(busqueda_pg, c or ""))]

            if df_pg.empty:
                st.caption("No hay créditos pagados para ese cliente en ese rango.")
            else:
                tabla_pg = df_pg.copy()
                tabla_pg["Referencia"] = tabla_pg.apply(
                    lambda r: f"FV-{r['factura_id']}" if r["tipo"]=="venta" else "Crédito antiguo", axis=1
                )
                tabla_pg["monto"] = tabla_pg["monto"].apply(fmt)
                tabla_pg = tabla_pg[["fecha","hora","cliente","canal","vendedor","Referencia","monto"]]
                tabla_pg.columns = ["Fecha","Hora","Cliente","Canal","Vendedor","Factura","Monto cobrado"]
                tabla_view(tabla_pg)

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

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: CONTADOR (solo admin) — inventario invertido, costo de producción,
# cuentas por cobrar/pagar. Antes vivían en Materia Prima→Historial y Caja→Resumen,
# visibles para cualquiera; se consolidaron aquí porque son datos financieros.
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "contador" and st.session_state.es_admin:
    st.markdown(f'<div class="section-label">{ICO_RECEIPT} Contador</div>', unsafe_allow_html=True)

    # --- Inventario total invertido (materia prima + saborizantes + empaque) ---
    raw_ent_todo_c = sb_get("materia_prima", "select=insumo,cantidad,precio_unitario,precio_total") or []
    raw_sal_todo_c = sb_get("salidas_mp", "select=insumo,cantidad") or []
    stock_actual_todo_c = {}
    for r in raw_ent_todo_c:
        stock_actual_todo_c[r["insumo"]] = stock_actual_todo_c.get(r["insumo"], 0) + float(r["cantidad"])
    for r in raw_sal_todo_c:
        stock_actual_todo_c[r["insumo"]] = stock_actual_todo_c.get(r["insumo"], 0) - float(r["cantidad"])

    prom_pond_todo_c = {}
    for r in raw_ent_todo_c:
        k = r["insumo"]
        pu = float(r.get("precio_unitario", 0))
        cant = float(r.get("cantidad", 0))
        if pu > 0 and cant > 0:
            if k not in prom_pond_todo_c:
                prom_pond_todo_c[k] = {"total_costo": 0, "total_cant": 0}
            prom_pond_todo_c[k]["total_costo"] += pu * cant
            prom_pond_todo_c[k]["total_cant"]  += cant

    total_invertido_c = 0
    for k, cant_stock in stock_actual_todo_c.items():
        d = prom_pond_todo_c.get(k)
        if d and d["total_cant"] > 0 and cant_stock > 0:
            total_invertido_c += cant_stock * (d["total_costo"] / d["total_cant"])

    st.markdown(
        f'<div class="calc-box">💰 Inventario total invertido ahora mismo '
        f'(materia prima + saborizantes + empaque): <b>{fmt(round(total_invertido_c))}</b></div>',
        unsafe_allow_html=True
    )

    # --- Cuentas por cobrar / pagar (vigentes, sin filtro de fecha) ---
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_cxc_c = ex.submit(sb_get, "ventas", "select=factura_id,saldo&saldo=gt.0&order=fecha.desc")
        f_cxp_c = ex.submit(sb_get, "materia_prima", "select=id,saldo&estado=eq.pendiente")
        f_cxc_m_c = ex.submit(sb_get, "creditos", "select=id,total,pagado&estado=eq.pendiente")
    raw_cxc_c = f_cxc_c.result() or []
    raw_cxp_c = f_cxp_c.result() or []
    raw_cxc_m_c = f_cxc_m_c.result() or []

    facturas_cxc_c = {}
    for r in raw_cxc_c:
        fid = r.get("factura_id", "")
        if fid and fid not in facturas_cxc_c:
            facturas_cxc_c[fid] = float(r.get("saldo", 0))
    cuentas_por_cobrar_c = sum(facturas_cxc_c.values()) + sum(max(0.0, float(r["total"]) - float(r.get("pagado", 0) or 0)) for r in raw_cxc_m_c)
    cuentas_por_pagar_c = sum(float(r.get("saldo", 0)) for r in raw_cxp_c)

    st.markdown(f'<div class="section-label">{ICO_RECEIPT} Cuentas vigentes</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box metric-blue"><div class="val">{fmt(cuentas_por_cobrar_c)}</div><div class="lbl">Cuentas por cobrar (clientes)</div></div>
        <div class="metric-box metric-red"><div class="val">{fmt(cuentas_por_pagar_c)}</div><div class="lbl">Cuentas por pagar (proveedores)</div></div>
    </div>
    """, unsafe_allow_html=True)

    # --- Costo de producción del período / costo unitario / producto terminado valorizado ---
    st.markdown(f'<div class="section-label">{ICO_RECEIPT} Costo de producción</div>', unsafe_allow_html=True)
    col_ct1, col_ct2 = st.columns(2)
    f_ini_cont = col_ct1.date_input("Desde", value=datetime.now(COL_TZ).date().replace(day=1), key="f_ini_cont")
    f_fin_cont = col_ct2.date_input("Hasta", value=datetime.now(COL_TZ).date(), key="f_fin_cont")
    rendimiento_bulto_kg_c = st.number_input(
        "Rendimiento del bulto de papa (kg fritos por bulto de 50kg crudo)",
        min_value=1.0, max_value=50.0, value=14.3, step=0.1, key="rendimiento_papa_kg",
        help="Varía según la calidad de la papa (aprox. 14 a 14.6 kg por bulto). Ajustalo si cambia."
    )

    with ThreadPoolExecutor(max_workers=4) as ex:
        f_ent_prom_c = ex.submit(sb_get, "materia_prima", "select=insumo,precio_unitario,cantidad")
        f_sal_periodo_c = ex.submit(sb_get, "salidas_mp", f"select=insumo,cantidad&fecha=gte.{f_ini_cont}&fecha=lte.{f_fin_cont}")
        f_prod_periodo_c = ex.submit(sb_get, "produccion", f"select=sabor,cantidad&fecha=gte.{f_ini_cont}&fecha=lte.{f_fin_cont}")
        f_stock_term_c = ex.submit(sb_get, "inventario", "select=stock")
        f_egresos_c = ex.submit(sb_get, "caja_egresos", f"select=valor,tipo&fecha=gte.{f_ini_cont}&fecha=lte.{f_fin_cont}")
    raw_ent_prom_c = f_ent_prom_c.result() or []
    raw_sal_periodo_c = f_sal_periodo_c.result() or []
    raw_prod_periodo_c = f_prod_periodo_c.result() or []
    raw_stock_term_c = f_stock_term_c.result() or []
    raw_egresos_cont = f_egresos_c.result() or []

    prom_pond_c = {}
    for r in raw_ent_prom_c:
        k = r["insumo"]
        pu = float(r.get("precio_unitario", 0))
        cant = float(r.get("cantidad", 0))
        if pu > 0 and cant > 0:
            if k not in prom_pond_c:
                prom_pond_c[k] = {"total_costo": 0, "total_cant": 0}
            prom_pond_c[k]["total_costo"] += pu * cant
            prom_pond_c[k]["total_cant"]  += cant

    # Saborizantes + empaque consumidos (excluye la papa, que se calcula abajo por
    # rendimiento crudo→frito en vez de repartirse a ciegas entre bolsas).
    costo_mp_periodo_c = 0
    for r in raw_sal_periodo_c:
        if r["insumo"] == "Papa (bulto)":
            continue
        d = prom_pond_c.get(r["insumo"])
        if d and d["total_cant"] > 0:
            costo_mp_periodo_c += float(r["cantidad"]) * (d["total_costo"] / d["total_cant"])

    # Costo de papa por rendimiento: precio promedio del bulto crudo ÷ kg fritos que
    # rinde, aplicado al peso real de cada sabor. Fósforo queda afuera hasta tener
    # su dato de rendimiento — su papa no se cuenta todavía (ver aviso abajo).
    d_papa_c = prom_pond_c.get("Papa (bulto)")
    precio_bulto_papa_c = (d_papa_c["total_costo"] / d_papa_c["total_cant"]) if d_papa_c and d_papa_c["total_cant"] > 0 else 0
    costo_por_kg_frito_c = (precio_bulto_papa_c / rendimiento_bulto_kg_c) if rendimiento_bulto_kg_c > 0 else 0

    costo_papa_periodo_c = 0
    bolsas_fosforo_sin_costo_c = 0
    for r in raw_prod_periodo_c:
        sabor_r = r.get("sabor")
        bolsas_r = float(r["cantidad"]) * UNIDADES_POR_BOLSA.get(sabor_r, UNIDADES_POR_BOLSA_DEFAULT)
        if sabor_r in FOSFORO_SABORES:
            bolsas_fosforo_sin_costo_c += bolsas_r
            continue
        peso_kg_r = PESO_KG_BOLSA.get(sabor_r, PESO_KG_BOLSA_DOCENA)
        costo_papa_periodo_c += bolsas_r * peso_kg_r * costo_por_kg_frito_c

    costo_planta_c = sum(float(r["valor"]) for r in raw_egresos_cont if r.get("tipo") == "costo")
    costo_produccion_periodo_c = costo_mp_periodo_c + costo_papa_periodo_c + costo_planta_c
    unidades_producidas_periodo_c = sum(
        float(r["cantidad"]) * UNIDADES_POR_BOLSA.get(r.get("sabor"), UNIDADES_POR_BOLSA_DEFAULT)
        for r in raw_prod_periodo_c
    )
    costo_unitario_prod_c = (costo_produccion_periodo_c / unidades_producidas_periodo_c) if unidades_producidas_periodo_c > 0 else 0
    stock_terminado_total_c = sum(float(r["stock"]) for r in raw_stock_term_c)
    valor_inventario_terminado_c = costo_unitario_prod_c * stock_terminado_total_c

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box metric-blue"><div class="val">{fmt(round(costo_produccion_periodo_c))}</div><div class="lbl">Costo de producción del período</div></div>
        <div class="metric-box metric-yellow"><div class="val">{fmt(round(costo_unitario_prod_c))}</div><div class="lbl">Costo unitario promedio</div></div>
        <div class="metric-box metric-green"><div class="val">{fmt(round(valor_inventario_terminado_c))}</div><div class="lbl">Producto terminado en bodega</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"💡 Costo de producción = papa (según rendimiento crudo→frito y peso real de cada sabor, {fmt(round(costo_papa_periodo_c))}) + saborizantes/empaque consumidos a precio promedio histórico ({fmt(round(costo_mp_periodo_c))}) + egresos marcados como \"costo de producción\" ({fmt(round(costo_planta_c))}). Costo unitario = ese total ÷ {unidades_producidas_periodo_c:.0f} bolsas individuales producidas en el período. Para comparar contra el precio de venta por docena, multiplica ×12 (o ×10 si es Fósforo 70g). Los egresos sin clasificar no cuentan aquí.")
    if bolsas_fosforo_sin_costo_c > 0:
        st.caption(f"⚠️ {bolsas_fosforo_sin_costo_c:.0f} bolsas de Fósforo producidas en el período no tienen costo de papa incluido todavía (falta el dato de rendimiento) — el costo unitario promedio queda un poco subestimado mientras tanto.")

    # --- Costo unitario por referencia (sabor) ---
    bolsas_por_sabor_c = {}
    for r in raw_prod_periodo_c:
        sabor_r = r.get("sabor")
        bolsas_r = float(r["cantidad"]) * UNIDADES_POR_BOLSA.get(sabor_r, UNIDADES_POR_BOLSA_DEFAULT)
        bolsas_por_sabor_c[sabor_r] = bolsas_por_sabor_c.get(sabor_r, 0) + bolsas_r

    if bolsas_por_sabor_c:
        st.markdown('<div class="section-label">Costo unitario por referencia</div>', unsafe_allow_html=True)
        # La papa se calcula por rendimiento (precisa por sabor); saborizante+empaque+planta
        # no se pueden separar de forma confiable por sabor, así que se reparten parejo
        # entre todas las bolsas del período — la diferencia entre sabores acá viene sobre
        # todo del peso de papa de cada uno.
        otros_costo_por_bolsa_c = (
            (costo_mp_periodo_c + costo_planta_c) / unidades_producidas_periodo_c
            if unidades_producidas_periodo_c > 0 else 0
        )
        filas_costo_sabor_c = []
        for sabor_r, bolsas_r in sorted(bolsas_por_sabor_c.items()):
            mult_r = UNIDADES_POR_BOLSA.get(sabor_r, UNIDADES_POR_BOLSA_DEFAULT)
            es_fosforo_r = sabor_r in FOSFORO_SABORES
            costo_papa_bolsa_r = 0 if es_fosforo_r else PESO_KG_BOLSA.get(sabor_r, PESO_KG_BOLSA_DOCENA) * costo_por_kg_frito_c
            costo_bolsa_r = costo_papa_bolsa_r + otros_costo_por_bolsa_c
            costo_unidad_venta_r = costo_bolsa_r * mult_r
            precio_venta_r = PRODUCTOS.get(sabor_r, 0)
            margen_r = precio_venta_r - costo_unidad_venta_r
            margen_pct_r = (margen_r / precio_venta_r * 100) if precio_venta_r > 0 else None
            etiqueta_r = "unidad" if mult_r == 1 else ("decena" if mult_r == 10 else "docena")
            filas_costo_sabor_c.append({
                "Sabor": sabor_r + (" ⚠️" if es_fosforo_r else ""),
                "Bolsas prod.": f"{bolsas_r:.0f}",
                "Se vende por": etiqueta_r,
                "Costo x unidad de venta": fmt(round(costo_unidad_venta_r)),
                "Precio venta": fmt(precio_venta_r) if precio_venta_r else "—",
                "Margen": fmt(round(margen_r)) if precio_venta_r else "—",
                "Margen %": f"{margen_pct_r:.0f}%" if margen_pct_r is not None else "—",
            })
        tabla_view(pd.DataFrame(filas_costo_sabor_c))
        st.caption("💡 El costo de papa por sabor es preciso (según su peso real); el resto (saborizante, empaque, planta) se reparte parejo entre todas las bolsas del período porque no se puede rastrear por sabor con los datos actuales. \"Precio venta\" es el precio base — puede variar según el tipo de cliente. ⚠️ = Fósforo, sin costo de papa todavía.")

    # --- Historial de pagos por empleado ---
    st.markdown(f'<div class="section-label">{ICO_RECEIPT} Historial por empleado</div>', unsafe_allow_html=True)
    raw_salarios = sb_get("caja_egresos", "select=fecha,hora,concepto,valor,empleado&categoria=eq.Salario&empleado=not.is.null&order=fecha.desc,hora.desc") or []
    nombres_empleados = sorted({r["empleado"] for r in raw_salarios if r.get("empleado")})
    if not nombres_empleados:
        st.info("Todavía no hay pagos de salario con nombre de empleado registrados.")
    else:
        emp_sel_cont = st.selectbox("Empleado", nombres_empleados, key="emp_sel_cont")
        pagos_emp = [r for r in raw_salarios if r["empleado"] == emp_sel_cont]
        total_pagado_emp = sum(float(r["valor"]) for r in pagos_emp)
        st.markdown(f'<div class="calc-box">💵 Total pagado a <b>{emp_sel_cont}</b>: <b>{fmt(total_pagado_emp)}</b> ({len(pagos_emp)} pagos)</div>', unsafe_allow_html=True)
        df_emp = pd.DataFrame([{
            "Fecha": r["fecha"], "Hora": r["hora"],
            "Concepto": r["concepto"], "Valor": fmt(r["valor"]),
        } for r in pagos_emp])
        tabla_view(df_emp)
