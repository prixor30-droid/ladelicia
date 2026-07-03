import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import hashlib
import requests
import time
import uuid
from pathlib import Path
from datetime import date, datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor

COL_TZ = timezone(timedelta(hours=-5))
def fecha_hoy():
    return datetime.now(COL_TZ).strftime("%Y-%m-%d")
def ahora():
    return datetime.now(COL_TZ).strftime("%I:%M %p").lstrip("0")

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
SUPABASE_URL = "https://duhsskisgksyozjdrusl.supabase.co"
SUPABASE_KEY = "sb_publishable_ChRLE6JchVDz1lW6ExRCDA_ibizrTGU"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def sb_get(tabla, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{tabla}"
    if params:
        url += f"?{params}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        return r.json() if r.ok else []
    except:
        return []

def sb_post(tabla, data):
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{tabla}", headers=HEADERS, json=data)
        return r.ok
    except:
        return False

def sb_patch(tabla, filtro, data):
    try:
        r = requests.patch(f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}", headers=HEADERS, json=data)
        return r.ok
    except:
        return False

def sb_delete(tabla, filtro):
    try:
        r = requests.delete(f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}", headers=HEADERS)
        return r.ok
    except:
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
            <td class="estado-ok">✓ Aprobado</td>
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

def mostrar_creditos_pendientes(canal):
    """Muestra facturas con saldo pendiente y permite registrar abonos."""
    raw = sb_get("ventas", f"select=factura_id,cliente,vendedor,total,abono,saldo&fecha=gte.2024-01-01&canal=eq.{requests.utils.quote(canal)}&saldo=gt.0")
    if not raw:
        return
    # Agrupar por factura para no repetir
    facturas = {}
    for r in raw:
        fid = r["factura_id"]
        if fid and fid not in facturas:
            facturas[fid] = {
                "cliente": r["cliente"],
                "vendedor": r["vendedor"],
                "saldo": float(r["saldo"]),
                "total": float(r["total"]),
                "abono": float(r["abono"]),
            }
    if not facturas:
        return
    st.markdown('<div class="section-label">💳 Créditos pendientes de cobro</div>', unsafe_allow_html=True)
    for fid, datos in facturas.items():
        saldo = datos["saldo"]
        st.markdown(
            f'<div class="warn-box">'
            f'<b>{datos["cliente"]}</b> · FV-{fid}<br>'
            f'Total: {fmt(datos["total"])} · Abonado: {fmt(datos["abono"])} · '
            f'<b>Debe: {fmt(saldo)}</b>'
            f'</div>',
            unsafe_allow_html=True
        )
        col_m, col_b = st.columns([3, 1])
        nuevo_abono = col_m.number_input(
            "Abono ($)", min_value=0, max_value=int(saldo),
            value=int(saldo), step=1000, key=f"abono_pend_{fid}"
        )
        if col_b.button("✅ Cobrar", key=f"btn_cobrar_{fid}"):
            nuevo_saldo = max(0, saldo - nuevo_abono)
            nuevo_total_abono = datos["abono"] + nuevo_abono
            sb_patch("ventas", f"factura_id=eq.{fid}", {
                "abono": nuevo_total_abono,
                "saldo": nuevo_saldo
            })
            time.sleep(0.3)
            st.rerun()

def _recargar_factura_vc(fac_vc):
    """Recarga la factura del carro desde Supabase y actualiza session_state."""
    registros_act = sb_get("ventas", f"select=sabor,cantidad,total&factura_id=eq.{fac_vc['id']}")
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
    st.session_state.factura_carro_guardada = {**fac_vc, "items": items_act, "precios": precios_act, "total": total_act}

def _recargar_factura_f(fac):
    """Recarga la factura de fábrica desde Supabase y actualiza session_state."""
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
    st.session_state.factura_guardada = {**fac, "items": items_act, "precios": precios_act, "total": total_act}

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

def get_inventario_completo():
    """Trae todo el inventario de una sola vez."""
    data = sb_get("inventario", "select=sabor,stock,precio")
    return {r["sabor"]: r["stock"] for r in data} if data else {}

def get_stock(sabor):
    inv = get_inventario_completo()
    if sabor in inv:
        return inv[sabor]
    q = requests.utils.quote(sabor)
    r = sb_get("inventario", f"select=stock&sabor=eq.{q}")
    return int(r[0]["stock"]) if r else 0

def agregar_stock(sabor, cantidad):
    q = requests.utils.quote(sabor)
    r = sb_get("inventario", f"select=stock&sabor=eq.{q}")
    stock = int(r[0]["stock"]) if r else 0
    sb_patch("inventario", f"sabor=eq.{q}", {"stock": stock + cantidad})

def restar_stock(sabor, cantidad):
    q = requests.utils.quote(sabor)
    r = sb_get("inventario", f"select=stock&sabor=eq.{q}")
    stock = int(r[0]["stock"]) if r else 0
    sb_patch("inventario", f"sabor=eq.{q}", {"stock": max(0, stock - cantidad)})

def set_stock(sabor, cantidad):
    q = requests.utils.quote(sabor)
    sb_patch("inventario", f"sabor=eq.{q}", {"stock": cantidad})

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
.brand-header{background:linear-gradient(135deg,#1565C0,#1E88E5);border-radius:0 0 22px 22px;padding:22px 20px 18px;margin:-1rem -1rem 16px -1rem;text-align:center;}
.brand-header p{color:rgba(255,255,255,0.85);font-size:0.78rem;margin:0;}
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
[data-testid="stButton-btn_produccion"] button,
[data-testid="stButton-btn_carro"] button,
[data-testid="stButton-btn_fabrica"] button,
[data-testid="stButton-btn_resumen"] button{
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
[data-testid="stButton-btn_produccion"] button:hover,
[data-testid="stButton-btn_carro"] button:hover,
[data-testid="stButton-btn_fabrica"] button:hover,
[data-testid="stButton-btn_resumen"] button:hover{
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
.calc-box{background:#FFFFFF;border-radius:14px;padding:14px;margin-bottom:14px;box-shadow:0 2px 10px rgba(21,101,192,0.10);}
.main-btn{background:#F0F7FF;border:1px solid #BBDEFB;border-radius:14px;padding:20px 16px;margin-bottom:10px;cursor:pointer;display:flex;align-items:center;gap:14px;}
.main-btn-icon{font-size:2rem;}
.main-btn-text{font-size:1.1rem;font-weight:700;color:#0D1B2A;}
.main-btn-sub{font-size:0.78rem;color:#1565C0;}
</style>
""", unsafe_allow_html=True)

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
bloquearTecladoSelects();
bloquearTecladoFechas();
setInterval(bloquearTecladoSelects, 500);
setInterval(bloquearTecladoFechas, 500);
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
ADMINS = {
    "1": "49bd2aab5ca8c640d9461d138268eaba3a12831bd634ce9e65c013425460de1b",
}
NOMBRES_ADMIN = {"1": "Admin"}

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
    {logo_html}
    <p>Control de producción y ventas</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MÉTRICAS
# ══════════════════════════════════════════════════════════════════════════════
def get_metricas_globales(fecha):
    def q_inv():   return sb_get("inventario", "select=sabor,stock")
    def q_prod():  return sb_get("produccion", f"select=cantidad&fecha=eq.{fecha}")
    def q_venta(): return sb_get("ventas",     f"select=total&fecha=eq.{fecha}")
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_inv   = ex.submit(q_inv)
        f_prod  = ex.submit(q_prod)
        f_venta = ex.submit(q_venta)
    return f_inv.result(), f_prod.result(), f_venta.result()

_inv, _prod, _venta = get_metricas_globales(fecha_hoy())
total_inv  = sum(r["stock"]    for r in _inv)   if _inv   else 0
total_prod = sum(r["cantidad"] for r in _prod)  if _prod  else 0
total_vta  = sum(r["total"]    for r in _venta) if _venta else 0

if st.session_state.es_admin:
    tarjeta_ventas = f'<div class="metric-box metric-green"><div class="val">{fmt(total_vta)}</div><div class="lbl">Ventas hoy</div></div>'
else:
    tarjeta_ventas = '<div class="metric-box metric-green"><div class="val">🔒</div><div class="lbl">Solo admin</div></div>'

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
            f'<div class="alert-low">🔴 <b>Agotado:</b> {nombres_ag}{extra_ag}</div>',
            unsafe_allow_html=True
        )

    if bajos_global:
        nombres_bj = ", ".join(f"{r['sabor']} ({r['stock']})" for r in bajos_global[:6])
        extra_bj = f" y {len(bajos_global)-6} más" if len(bajos_global) > 6 else ""
        st.markdown(
            f'<div class="warn-box">⚠️ <b>Stock bajo:</b> {nombres_bj}{extra_bj}</div>',
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
                st.markdown('<div class="alert-low">⚠️ Usuario o contraseña incorrectos.</div>', unsafe_allow_html=True)
else:
    nombre_admin = NOMBRES_ADMIN.get(st.session_state.admin_actual, "Administrador")
    st.markdown(f'<div class="info-box">✅ Sesión activa — <b>{nombre_admin} (Administrador)</b></div>', unsafe_allow_html=True)
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
def mostrar_calculadora():
    with st.expander("🧮 Calculadora", expanded=False):
        st.markdown('<div class="calc-box">', unsafe_allow_html=True)
        billete = st.number_input("Billete del cliente ($)", min_value=0, value=0, step=1000,
                                  key="calc_billete")
        cobrar  = st.number_input("Total a cobrar ($)", min_value=0, value=0, step=100,
                                  key="calc_cobrar")
        if billete > 0 and cobrar > 0:
            if billete >= cobrar:
                st.markdown(f'<div class="info-box">💵 Devolver: <b>{fmt(billete - cobrar)}</b></div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-low">⚠️ El billete no alcanza — faltan {fmt(cobrar - billete)}</div>',
                            unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista == "menu":
    opciones = [
        ("produccion",    "📦", "Producción",      "Registrar bolsas fabricadas"),
        ("carro",         "🚗", "Edison & Javier", "Cargues y ventas del carro"),
        ("fabrica",       "🏭", "Fábrica",          "Ventas de Sofía y Andrea"),
        ("materia_prima", "🌽", "Materia Prima",    "Insumos y proveedores"),
    ]
    if st.session_state.es_admin:
        opciones.append(("resumen", "📊", "Resumen", "Ventas, facturas y exportar"))

    for vista, icon, titulo, sub in opciones:
        with st.container():
            if st.button(f"{icon}  {titulo}\n{sub}", key=f"btn_{vista}", use_container_width=True):
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
    st.markdown(f'<div class="info-box">📦 Stock actual de <b>{sabor_p}</b>: {stock_act} → quedará en <b>{stock_act + cantidad_p}</b></div>', unsafe_allow_html=True)

    if st.button("✅ Registrar producción", key="btn_prod"):
        sb_post("produccion", {
            "fecha": fecha_hoy(), "hora": ahora(),
            "empleado": empleado, "sabor": sabor_p, "cantidad": cantidad_p
        })
        agregar_stock(sabor_p, cantidad_p)
        st.session_state.ok_prod = True
        time.sleep(0.3)
        st.rerun()

    if st.session_state.ok_prod:
        st.markdown('<div class="success-toast">✅ ¡Producción registrada!</div>', unsafe_allow_html=True)
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
    nuevo_stock = st.number_input("Stock real", min_value=0, value=stock_adj, step=1, key="nuevo_s")
    if st.button("💾 Guardar ajuste", key="btn_adj"):
        set_stock(sabor_adj, nuevo_stock)
        st.session_state.ok_stock = True
        time.sleep(0.3)
        st.rerun()
    if st.session_state.ok_stock:
        st.markdown('<div class="success-toast">✅ Stock ajustado.</div>', unsafe_allow_html=True)
        st.session_state.ok_stock = False

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: CARRO (Edison & Javier)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "carro":
    mostrar_calculadora()

    sub1, sub2, sub3, sub4 = st.tabs(["🚗 Nuevo cargue", "💵 Registrar venta", "🔄 Devolución", "🎁 Regalar"])

    with sub1:
        st.markdown('<div class="section-label">Cargue del carro</div>', unsafe_allow_html=True)
        sabor_cg = st.selectbox("Sabor", sabores_por_frecuencia("Carro"), key="sabor_cg")
        stock_cg = get_stock(sabor_cg)
        cant_cg  = st.number_input("Bolsas a cargar", min_value=1, max_value=max(1, stock_cg), value=min(10, max(1, stock_cg)), step=5, key="cant_cg")

        if stock_cg < cant_cg:
            st.markdown(f'<div class="alert-low">⚠️ Solo hay {stock_cg} bolsas de {sabor_cg}.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box">📦 Disponible: <b>{stock_cg}</b> · Quedarán: <b>{stock_cg - cant_cg}</b></div>', unsafe_allow_html=True)

        if st.button("🚗 Registrar cargue", key="btn_cg", disabled=(stock_cg < cant_cg)):
            sb_post("cargues", {"fecha": fecha_hoy(), "hora": ahora(), "sabor": sabor_cg, "cantidad": cant_cg})
            restar_stock(sabor_cg, cant_cg)
            st.session_state.ok_cargue = True
            time.sleep(0.3)
            st.rerun()

        if st.session_state.ok_cargue:
            st.markdown('<div class="success-toast">✅ Cargue registrado.</div>', unsafe_allow_html=True)
            st.session_state.ok_cargue = False

        # Cargue activo hoy
        with ThreadPoolExecutor(max_workers=3) as ex:
            f_cg  = ex.submit(sb_get, "cargues",      f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}")
            f_vc  = ex.submit(sb_get, "ventas",        f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}&canal=in.(Carro,Cambio,Regalo)")
            f_dev = ex.submit(sb_get, "devoluciones",  f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}")
        raw_cg = f_cg.result()
        raw_vc = f_vc.result()
        raw_dev = f_dev.result()
        if raw_cg:
            df_cg = pd.DataFrame(raw_cg).groupby("sabor")["cantidad"].sum().reset_index()
            df_cg.columns = ["sabor","cargado"]
            if raw_vc:
                df_vc2 = pd.DataFrame(raw_vc).groupby("sabor")["cantidad"].sum().reset_index()
                df_vc2.columns = ["sabor","vendido"]
                df_cg = df_cg.merge(df_vc2, on="sabor", how="left").fillna(0)
            else:
                df_cg["vendido"] = 0
            if raw_dev:
                df_dev2 = pd.DataFrame(raw_dev).groupby("sabor")["cantidad"].sum().reset_index()
                df_dev2.columns = ["sabor","devuelto"]
                df_cg = df_cg.merge(df_dev2, on="sabor", how="left").fillna(0)
            else:
                df_cg["devuelto"] = 0
            df_cg["pendiente"] = df_cg["cargado"] - df_cg["vendido"] - df_cg["devuelto"]
            df_pend = df_cg[df_cg["pendiente"] > 0][["sabor","pendiente"]]
            if not df_pend.empty:
                st.markdown('<div class="section-label">Lo que lleva el carro ahora</div>', unsafe_allow_html=True)
                df_pend.columns = ["Sabor","Bolsas pendientes"]
                st.dataframe(df_pend, use_container_width=True, hide_index=True)

        # Tabla editable de cargues del día — para corregir errores
        raw_cg_full = sb_get("cargues", f"select=id,fecha,hora,sabor,cantidad&fecha=eq.{fecha_hoy()}&order=hora.desc")
        if raw_cg_full:
            st.markdown('<div class="section-label">Cargues registrados hoy</div>', unsafe_allow_html=True)
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

    with sub2:
        st.markdown('<div class="section-label">Nueva venta 🚗</div>', unsafe_allow_html=True)

        cliente_vc = st.text_input("Nombre del cliente", placeholder="Ej: Tienda Don Carlos", key="cliente_vc")

        st.markdown('<div class="section-label">Agregar al carrito</div>', unsafe_allow_html=True)

        col_s, col_c = st.columns([2, 1])
        sabor_vc = col_s.selectbox("Sabor", sabores_por_frecuencia("Carro"), key="sabor_vc")
        cant_vc  = col_c.number_input("Bolsas", min_value=1, max_value=500, value=1, step=1, key="cant_vc")

        # Calcular disponible del carro por sabor (cargado - vendido - devuelto)
        with ThreadPoolExecutor(max_workers=3) as ex:
            f_cg2  = ex.submit(sb_get, "cargues",     f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}")
            f_vc2  = ex.submit(sb_get, "ventas",       f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}&canal=in.(Carro,Cambio,Regalo)")
            f_dev2 = ex.submit(sb_get, "devoluciones", f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}")
        raw_cg_check  = f_cg2.result()
        raw_vc_check  = f_vc2.result()
        raw_dev_check = f_dev2.result()

        stock_carro = {}  # disponible por sabor en el carro
        if raw_cg_check:
            for r in raw_cg_check:
                stock_carro[r["sabor"]] = stock_carro.get(r["sabor"], 0) + r["cantidad"]
        if raw_vc_check:
            for r in raw_vc_check:
                if r.get("cantidad", 0) > 0:
                    stock_carro[r["sabor"]] = stock_carro.get(r["sabor"], 0) - r["cantidad"]
        if raw_dev_check:
            for r in raw_dev_check:
                stock_carro[r["sabor"]] = stock_carro.get(r["sabor"], 0) - r.get("cantidad", 0)

        hay_cargue = sum(max(0, v) for v in stock_carro.values()) > 0
        disp_sabor = max(0, stock_carro.get(sabor_vc, 0))

        if not hay_cargue:
            st.markdown('<div class="warn-box">⚠️ No hay papas cargadas disponibles. Registra un cargue primero.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box">📦 Disponible en el carro de <b>{sabor_vc}</b>: <b>{disp_sabor}</b> bolsas</div>', unsafe_allow_html=True)

        if st.button("➕ Agregar al carrito", key="btn_add_carro", disabled=(not hay_cargue or disp_sabor < cant_vc)):
            actual = st.session_state.carrito_carro.get(sabor_vc, 0)
            st.session_state.carrito_carro[sabor_vc] = actual + cant_vc
            if sabor_vc not in st.session_state.precios_carro:
                st.session_state.precios_carro[sabor_vc] = PRODUCTOS[sabor_vc]
            st.rerun()
            actual = st.session_state.carrito_carro.get(sabor_vc, 0)
            st.session_state.carrito_carro[sabor_vc] = actual + cant_vc
            if sabor_vc not in st.session_state.precios_carro:
                st.session_state.precios_carro[sabor_vc] = PRODUCTOS[sabor_vc]
            st.rerun()

        if st.session_state.carrito_carro:
            st.markdown('<div class="section-label">Carrito de venta</div>', unsafe_allow_html=True)
            st.caption("Toca cualquier celda para cambiar cantidad o precio.")

            sabores_cc = list(st.session_state.carrito_carro.keys())
            df_cc = pd.DataFrame({
                "Sabor":    sabores_cc,
                "Cantidad": [st.session_state.carrito_carro[s] for s in sabores_cc],
                "Precio":   [st.session_state.precios_carro.get(s, PRODUCTOS[s]) for s in sabores_cc],
            })
            df_cc["Subtotal"] = df_cc["Cantidad"] * df_cc["Precio"]

            edited_cc = st.data_editor(
                df_cc,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                column_config={
                    "Sabor":    st.column_config.TextColumn("Sabor", disabled=True),
                    "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1),
                    "Precio":   st.column_config.NumberColumn("Precio", min_value=100, step=100),
                    "Subtotal": st.column_config.NumberColumn("Subtotal", disabled=True),
                },
                key="carro_cart_editor"
            )

            if st.button("💾 Aplicar cambios", key="btn_save_cc"):
                nuevo_cc = {}
                nuevos_p_cc = {}
                for _, row in edited_cc.iterrows():
                    if pd.notna(row["Sabor"]) and row["Cantidad"] > 0:
                        nuevo_cc[row["Sabor"]] = nuevo_cc.get(row["Sabor"], 0) + int(row["Cantidad"])
                        nuevos_p_cc[row["Sabor"]] = int(row["Precio"])
                st.session_state.carrito_carro = nuevo_cc
                st.session_state.precios_carro = nuevos_p_cc
                st.rerun()

            sabor_quitar_cc = st.selectbox("Quitar un sabor", ["— Selecciona —"] + sabores_cc, key="sel_quitar_cc")
            if sabor_quitar_cc != "— Selecciona —" and st.button("✕ Quitar", key="btn_quitar_cc"):
                del st.session_state.carrito_carro[sabor_quitar_cc]
                if sabor_quitar_cc in st.session_state.precios_carro:
                    del st.session_state.precios_carro[sabor_quitar_cc]
                st.rerun()

            total_cc = float((edited_cc["Cantidad"] * edited_cc["Precio"]).sum())

            # Billete y vuelto
            st.markdown('<div class="section-label">Pago del cliente</div>', unsafe_allow_html=True)
            abono_vc = st.number_input("Abono del cliente ($)", min_value=0, value=0, step=1000, key="abono_vc")
            if abono_vc > 0:
                if abono_vc >= total_cc:
                    st.markdown(f'<div class="info-box">💰 Total: <b>{fmt(total_cc)}</b> · Devolver: <b>{fmt(abono_vc - total_cc)}</b></div>', unsafe_allow_html=True)
                else:
                    saldo_mostrar = total_cc - abono_vc
                    st.markdown(f'<div class="warn-box">📋 Abono: <b>{fmt(abono_vc)}</b> · Queda debiendo: <b>{fmt(saldo_mostrar)}</b></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="warn-box">📋 Sin abono — queda debiendo: <b>{fmt(total_cc)}</b></div>', unsafe_allow_html=True)

            col_clr2, col_conf = st.columns(2)
            if col_clr2.button("🗑️ Vaciar carrito", key="btn_clr_cc"):
                st.session_state.carrito_carro = {}
                st.session_state.precios_carro = {}
                st.rerun()

            if col_conf.button("✅ Confirmar venta", key="btn_vc"):
                if not cliente_vc.strip():
                    st.markdown('<div class="alert-low">⚠️ Escribe el nombre del cliente.</div>', unsafe_allow_html=True)
                else:
                    sin_stock = [s for s, c in st.session_state.carrito_carro.items() if stock_carro.get(s, 0) < c]
                    if sin_stock:
                        st.markdown(f'<div class="alert-low">⚠️ Stock insuficiente: <b>{", ".join(sin_stock)}</b>. Ajusta el carrito.</div>', unsafe_allow_html=True)
                    else:
                        fid_vc = str(uuid.uuid4())[:8].upper()
                        total_venta_vc = 0
                        abono_val = int(st.session_state.get("abono_vc", 0))
                        for s, c in st.session_state.carrito_carro.items():
                            precio_final = st.session_state.precios_carro.get(s, PRODUCTOS[s])
                            subtotal = precio_final * c
                            total_venta_vc += subtotal
                            sb_post("ventas", {
                                "fecha": fecha_hoy(), "hora": ahora(), "canal": "Carro",
                                "vendedor": "Javier & Edison", "sabor": s,
                                "cantidad": c, "total": subtotal,
                                "cliente": cliente_vc.strip(), "factura_id": fid_vc,
                                "abono": abono_val, "saldo": max(0, total_venta_vc - abono_val)
                            })
                        # Actualizar saldo en todos los registros de la factura
                        saldo_final = max(0, total_venta_vc - abono_val)
                        sb_patch("ventas", f"factura_id=eq.{fid_vc}", {"abono": abono_val, "saldo": saldo_final})
                        st.session_state.factura_carro_guardada = {
                            "id": fid_vc, "cliente": cliente_vc.strip(),
                            "vendedor": "Javier & Edison",
                            "items": dict(st.session_state.carrito_carro),
                            "precios": dict(st.session_state.precios_carro),
                            "total": total_venta_vc,
                            "billete": abono_val,
                            "saldo": saldo_final,
                        }
                        st.session_state.carrito_carro = {}
                        st.session_state.precios_carro = {}
                        time.sleep(0.3)
                        st.rerun()

        # Opciones post-venta — solo si hay una factura activa en esta sesión
        if st.session_state.factura_carro_guardada:
            fac_vc = st.session_state.factura_carro_guardada
            vuelto_vc = fac_vc["billete"] - fac_vc["total"] if fac_vc["billete"] >= fac_vc["total"] and fac_vc["billete"] > 0 else 0
            saldo_vc = fac_vc.get("saldo", 0)
            msg = f'✅ Venta registrada — <b>#{fac_vc["id"]}</b> · {fac_vc["cliente"]} · {fmt(fac_vc["total"])}'
            if vuelto_vc > 0:
                msg += f'<br>💵 Devolver: <b>{fmt(vuelto_vc)}</b>'
            if saldo_vc > 0:
                msg += f'<br>📋 Queda debiendo: <b>{fmt(saldo_vc)}</b>'
            st.markdown(f'<div class="success-toast">{msg}</div>', unsafe_allow_html=True)

            # Modificar factura post-venta
            st.markdown('<div class="section-label">¿El cliente quiere algo más?</div>', unsafe_allow_html=True)
            tab_cambio_vc, tab_agregar_vc = st.tabs(["🔁 Cambiar producto", "➕ Agregar producto"])

            with tab_cambio_vc:
                col_a, col_b = st.columns(2)

                # Devuelve: solo sabores que están en la factura actual
                sabores_en_factura = list(fac_vc["items"].keys())
                sabor_out_vc = col_a.selectbox("Devuelve", sabores_en_factura, key="cambio_out_vc")
                max_out = fac_vc["items"].get(sabor_out_vc, 1)
                cant_out_vc = col_a.number_input("Cantidad que devuelve", min_value=1, max_value=max_out, value=1, step=1, key="cant_out_vc")

                # Lleva en cambio: solo sabores disponibles en el carro
                # Al devolver, ese sabor vuelve al carro — sumarlo temporalmente
                stock_carro_cambio = dict(stock_carro)
                stock_carro_cambio[sabor_out_vc] = stock_carro_cambio.get(sabor_out_vc, 0) + cant_out_vc
                sabores_disp_cambio = [s for s, v in stock_carro_cambio.items() if v > 0]
                sabor_in_vc = col_b.selectbox("Lleva en cambio", sabores_disp_cambio, key="cambio_in_vc")
                max_in = int(stock_carro_cambio.get(sabor_in_vc, 1))
                cant_in_vc = col_b.number_input("Cantidad que lleva", min_value=1, max_value=max_in, value=1, step=1, key="cant_in_vc")

                valor_out_vc = fac_vc["precios"].get(sabor_out_vc, PRODUCTOS[sabor_out_vc]) * cant_out_vc
                valor_in_vc  = fac_vc["precios"].get(sabor_in_vc,  PRODUCTOS[sabor_in_vc])  * cant_in_vc
                dif_vc = valor_in_vc - valor_out_vc
                if dif_vc > 0:
                    st.markdown(f'<div class="warn-box">💰 El cliente debe pagar <b>{fmt(dif_vc)}</b> adicionales</div>', unsafe_allow_html=True)
                elif dif_vc < 0:
                    st.markdown(f'<div class="info-box">💵 Hay que devolver <b>{fmt(abs(dif_vc))}</b> al cliente</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="info-box">✅ Cambio sin diferencia de valor</div>', unsafe_allow_html=True)

                if st.button("🔁 Registrar cambio", key="btn_cambio_vc"):
                    sb_post("ventas", {
                        "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                        "vendedor": fac_vc["vendedor"], "sabor": sabor_out_vc,
                        "cantidad": -cant_out_vc, "total": -valor_out_vc,
                        "cliente": fac_vc["cliente"], "factura_id": fac_vc["id"],
                        "abono": 0, "saldo": 0
                    })
                    sb_post("ventas", {
                        "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                        "vendedor": fac_vc["vendedor"], "sabor": sabor_in_vc,
                        "cantidad": cant_in_vc, "total": valor_in_vc,
                        "cliente": fac_vc["cliente"], "factura_id": fac_vc["id"],
                        "abono": 0, "saldo": 0
                    })
                    # Actualizar saldo de la factura si hay diferencia
                    if dif_vc > 0:
                        raw_saldo = sb_get("ventas", f"select=saldo&factura_id=eq.{fac_vc['id']}&canal=eq.Carro&limit=1")
                        saldo_actual = float(raw_saldo[0]["saldo"]) if raw_saldo else 0
                        nuevo_saldo = saldo_actual + dif_vc
                        sb_patch("ventas", f"factura_id=eq.{fac_vc['id']}&canal=eq.Carro", {"saldo": nuevo_saldo})
                    elif dif_vc < 0:
                        raw_saldo = sb_get("ventas", f"select=saldo&factura_id=eq.{fac_vc['id']}&canal=eq.Carro&limit=1")
                        saldo_actual = float(raw_saldo[0]["saldo"]) if raw_saldo else 0
                        nuevo_saldo = max(0, saldo_actual + dif_vc)
                        sb_patch("ventas", f"factura_id=eq.{fac_vc['id']}&canal=eq.Carro", {"saldo": nuevo_saldo})
                    time.sleep(0.3)
                    todos_vc = sb_get("ventas", f"select=*&factura_id=eq.{fac_vc['id']}")
                    st.session_state.recibo_canal_df = todos_vc or []
                    _recargar_factura_vc(fac_vc)
                    st.rerun()

            with tab_agregar_vc:
                # Solo mostrar sabores disponibles en el carro
                sabores_disponibles_vc = [s for s, v in stock_carro.items() if v > 0]
                if not sabores_disponibles_vc:
                    st.markdown('<div class="warn-box">⚠️ No hay papas disponibles en el carro para agregar.</div>', unsafe_allow_html=True)
                else:
                    sabor_add_vc = st.selectbox("Sabor a agregar", sabores_disponibles_vc, key="add_sabor_vc")
                    disp_add_vc = int(stock_carro.get(sabor_add_vc, 0))
                    cant_add_vc = st.number_input("Cantidad", min_value=1, max_value=disp_add_vc, value=1, step=1, key="add_cant_vc")
                    precio_add_vc = fac_vc["precios"].get(sabor_add_vc, PRODUCTOS[sabor_add_vc]) * cant_add_vc
                    st.markdown(f'<div class="info-box">📦 Disponible: <b>{disp_add_vc}</b> · 💰 A cobrar: <b>{fmt(precio_add_vc)}</b></div>', unsafe_allow_html=True)

                    if st.button("➕ Agregar a la factura", key="btn_add_vc"):
                        sb_post("ventas", {
                            "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                            "vendedor": fac_vc["vendedor"], "sabor": sabor_add_vc,
                            "cantidad": cant_add_vc, "total": precio_add_vc,
                            "cliente": fac_vc["cliente"], "factura_id": fac_vc["id"],
                            "abono": 0, "saldo": 0
                        })
                        # Actualizar saldo — el cliente debe más
                        raw_saldo = sb_get("ventas", f"select=saldo&factura_id=eq.{fac_vc['id']}&canal=eq.Carro&limit=1")
                        saldo_actual = float(raw_saldo[0]["saldo"]) if raw_saldo else 0
                        nuevo_saldo = saldo_actual + precio_add_vc
                        sb_patch("ventas", f"factura_id=eq.{fac_vc['id']}&canal=eq.Carro", {"saldo": nuevo_saldo})
                        time.sleep(0.3)
                        _recargar_factura_vc(fac_vc)
                        st.rerun()

            if st.button("🧾 Nueva venta", key="btn_nueva_vc"):
                st.session_state.factura_carro_guardada = None
                st.rerun()

        # Facturas del día — visible para todos desde cualquier dispositivo
        st.markdown('<div class="section-label">Ventas de hoy</div>', unsafe_allow_html=True)
        st.caption("Toca una fila para ver el recibo completo.")
        raw_fact_vc = sb_get("ventas",
            f"select=fecha,hora,cliente,vendedor,sabor,cantidad,total,factura_id,es_credito&fecha=eq.{fecha_hoy()}&canal=eq.Carro&order=hora.desc")
        if raw_fact_vc:
            df_fact_vc = pd.DataFrame(raw_fact_vc)
            mostrar_facturas_seleccionables(df_fact_vc, "carro_todos")
        else:
            st.caption("Aún no hay ventas registradas hoy.")

        mostrar_creditos_pendientes("Carro")


        # Papas disponibles del cargue — lo que lleva el carro pendiente de vender
        st.markdown('<div class="section-label">Papas disponibles del cargue</div>', unsafe_allow_html=True)
        with ThreadPoolExecutor(max_workers=3) as ex:
            f_cg3  = ex.submit(sb_get, "cargues",     f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}")
            f_vc3  = ex.submit(sb_get, "ventas",       f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}&canal=in.(Carro,Cambio,Regalo)")
            f_dev3 = ex.submit(sb_get, "devoluciones", f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}")
        raw_cg2  = f_cg3.result()
        raw_vc2  = f_vc3.result()
        raw_dev2 = f_dev3.result()
        if raw_cg2:
            df_cg2 = pd.DataFrame(raw_cg2).groupby("sabor")["cantidad"].sum().reset_index()
            df_cg2.columns = ["sabor","cargado"]
            if raw_vc2:
                df_vc3 = pd.DataFrame(raw_vc2).groupby("sabor")["cantidad"].sum().reset_index()
                df_vc3.columns = ["sabor","vendido"]
                df_cg2 = df_cg2.merge(df_vc3, on="sabor", how="left").fillna(0)
            else:
                df_cg2["vendido"] = 0
            if raw_dev2:
                df_dev3 = pd.DataFrame(raw_dev2).groupby("sabor")["cantidad"].sum().reset_index()
                df_dev3.columns = ["sabor","devuelto"]
                df_cg2 = df_cg2.merge(df_dev3, on="sabor", how="left").fillna(0)
            else:
                df_cg2["devuelto"] = 0
            df_cg2["pendiente"] = df_cg2["cargado"] - df_cg2["vendido"] - df_cg2["devuelto"]
            disponibles = df_cg2[df_cg2["pendiente"] > 0]
            if not disponibles.empty:
                filas_cg = "".join(
                    f'<div class="factura-row"><span>{row["sabor"]}</span><span><b>{int(row["pendiente"])} bolsas</b></span></div>'
                    for _, row in disponibles.iterrows()
                )
                st.markdown(f'<div class="factura-box">{filas_cg}</div>', unsafe_allow_html=True)
            else:
                st.caption("No hay cargue activo hoy.")
        else:
            st.caption("No hay cargue registrado hoy.")

        # Solo admin ve resumen del carro
        if st.session_state.es_admin:
            raw_resumen_carro = sb_get("ventas", f"select=total,cantidad&fecha=eq.{fecha_hoy()}&canal=eq.Carro")
            if raw_resumen_carro:
                total_carro_dia  = sum(r["total"]    for r in raw_resumen_carro if r["total"] > 0)
                bolsas_carro_dia = sum(r["cantidad"] for r in raw_resumen_carro if r["cantidad"] > 0)
                st.markdown('<div class="section-label">Resumen del día — Javier & Edison</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="factura-box">'
                    f'<div class="factura-row"><span>🛒 Bolsas vendidas hoy</span><span><b>{bolsas_carro_dia}</b></span></div>'
                    f'<div class="factura-total"><span>💰 Total a entregar</span><span>{fmt(total_carro_dia)}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    with sub3:
        st.markdown('<div class="section-label">Devolución al inventario 🔄</div>', unsafe_allow_html=True)
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
        st.markdown(f'<div class="info-box">📦 Máximo a devolver de <b>{sabor_dev}</b> hoy: <b>{max_dev}</b> bolsas</div>', unsafe_allow_html=True)

        if st.button("🔄 Registrar devolución", key="btn_dev"):
            sb_post("devoluciones", {"fecha": str(fecha_dev), "sabor": sabor_dev, "cantidad": cant_dev})
            agregar_stock(sabor_dev, cant_dev)
            st.session_state.ok_dev = True
            time.sleep(0.3)
            st.rerun()

        if st.session_state.ok_dev:
            st.markdown('<div class="success-toast">✅ Devolución registrada. Stock actualizado.</div>', unsafe_allow_html=True)
            st.session_state.ok_dev = False

    with sub4:
        st.markdown('<div class="section-label">Regalar bolsa 🎁</div>', unsafe_allow_html=True)
        st.caption("Registra las bolsas que se regalan — se descuentan del carro pero no cuentan como venta.")

        # Solo sabores disponibles en el carro
        with ThreadPoolExecutor(max_workers=3) as ex:
            f_cg_r  = ex.submit(sb_get, "cargues",     f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}")
            f_vc_r  = ex.submit(sb_get, "ventas",       f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}&canal=in.(Carro,Cambio,Regalo)")
            f_dev_r = ex.submit(sb_get, "devoluciones", f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}")
        raw_cg_r  = f_cg_r.result()
        raw_vc_r  = f_vc_r.result()
        raw_dev_r = f_dev_r.result()

        stock_carro_r = {}
        if raw_cg_r:
            for r in raw_cg_r:
                stock_carro_r[r["sabor"]] = stock_carro_r.get(r["sabor"], 0) + r["cantidad"]
        if raw_vc_r:
            for r in raw_vc_r:
                if r.get("cantidad", 0) > 0:
                    stock_carro_r[r["sabor"]] = stock_carro_r.get(r["sabor"], 0) - r["cantidad"]
        if raw_dev_r:
            for r in raw_dev_r:
                stock_carro_r[r["sabor"]] = stock_carro_r.get(r["sabor"], 0) - r.get("cantidad", 0)

        sabores_disp_r = [s for s, v in stock_carro_r.items() if v > 0]

        if not sabores_disp_r:
            st.markdown('<div class="warn-box">⚠️ No hay papas disponibles en el carro para regalar.</div>', unsafe_allow_html=True)
        else:
            sabor_reg = st.selectbox("Sabor", sabores_disp_r, key="sabor_reg")
            disp_reg = int(stock_carro_r.get(sabor_reg, 0))
            cant_reg = st.number_input("Cantidad", min_value=1, max_value=disp_reg, value=1, step=1, key="cant_reg")
            motivo_reg = st.text_input("Motivo (opcional)", placeholder="Ej: Cliente especial, muestra", key="motivo_reg")
            st.markdown(f'<div class="info-box">🎁 Regalando <b>{cant_reg}</b> bolsas de <b>{sabor_reg}</b> · Quedan: <b>{disp_reg - cant_reg}</b></div>', unsafe_allow_html=True)

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
            st.markdown('<div class="success-toast">✅ Regalo registrado. Descontado del carro.</div>', unsafe_allow_html=True)
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

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: FÁBRICA
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "fabrica":
    mostrar_calculadora()

    st.markdown('<div class="section-label">Nueva venta 🏭</div>', unsafe_allow_html=True)

    vendedor_f = st.selectbox("Vendedor", VENDEDORES_FABRICA, key="vend_f")
    cliente_f  = st.text_input("Nombre del cliente", placeholder="Ej: Tienda Don Carlos", key="cliente_f")

    st.markdown('<div class="section-label">Agregar al carrito</div>', unsafe_allow_html=True)

    col_s, col_c = st.columns([2, 1])
    sabor_vf = col_s.selectbox("Sabor", sabores_por_frecuencia("Fábrica"), key="sabor_vf")
    cant_vf  = col_c.number_input("Bolsas", min_value=1, max_value=500, value=1, step=1, key="cant_vf")

    stock_vf   = get_stock(sabor_vf)
    en_carrito = st.session_state.carrito.get(sabor_vf, 0)
    disponible = stock_vf - en_carrito

    if disponible < cant_vf:
        st.markdown(f'<div class="alert-low">⚠️ Solo hay {disponible} bolsas disponibles de {sabor_vf}.</div>', unsafe_allow_html=True)

    col_add, col_clr = st.columns(2)
    if col_add.button("➕ Agregar", key="btn_add", disabled=(disponible < cant_vf)):
        st.session_state.carrito[sabor_vf] = en_carrito + cant_vf
        if sabor_vf not in st.session_state.precios_carrito:
            st.session_state.precios_carrito[sabor_vf] = PRODUCTOS[sabor_vf]
        st.rerun()

    if col_clr.button("🗑️ Vaciar", key="btn_clr"):
        st.session_state.carrito = {}
        st.session_state.precios_carrito = {}
        st.rerun()

    # Carrito como tabla editable
    if st.session_state.carrito:
        st.markdown('<div class="section-label">Carrito actual</div>', unsafe_allow_html=True)
        st.caption("Toca cualquier celda para cambiar cantidad o precio.")

        sabores_carrito = list(st.session_state.carrito.keys())
        df_carrito = pd.DataFrame({
            "Sabor":    sabores_carrito,
            "Cantidad": [st.session_state.carrito[s] for s in sabores_carrito],
            "Precio":   [st.session_state.precios_carrito.get(s, PRODUCTOS[s]) for s in sabores_carrito],
        })
        df_carrito["Subtotal"] = df_carrito["Cantidad"] * df_carrito["Precio"]

        edited_cart = st.data_editor(
            df_carrito,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Sabor":    st.column_config.TextColumn("Sabor", disabled=True),
                "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1),
                "Precio":   st.column_config.NumberColumn("Precio", min_value=100, step=100),
                "Subtotal": st.column_config.NumberColumn("Subtotal", disabled=True),
            },
            key="carrito_editor"
        )

        if st.button("💾 Aplicar cambios al carrito", key="btn_save_cart"):
            nuevo_carrito = {}
            nuevos_precios = {}
            for _, row in edited_cart.iterrows():
                if pd.notna(row["Sabor"]) and row["Cantidad"] > 0:
                    nuevo_carrito[row["Sabor"]] = nuevo_carrito.get(row["Sabor"], 0) + int(row["Cantidad"])
                    nuevos_precios[row["Sabor"]] = int(row["Precio"])
            st.session_state.carrito = nuevo_carrito
            st.session_state.precios_carrito = nuevos_precios
            st.rerun()

        # Quitar un sabor completo del carrito
        sabor_quitar = st.selectbox("Quitar un sabor del carrito", ["— Selecciona —"] + sabores_carrito, key="sel_quitar")
        if sabor_quitar != "— Selecciona —" and st.button("✕ Quitar del carrito", key="btn_quitar"):
            del st.session_state.carrito[sabor_quitar]
            if sabor_quitar in st.session_state.precios_carrito:
                del st.session_state.precios_carrito[sabor_quitar]
            st.rerun()

        total_fac = float((edited_cart["Cantidad"] * edited_cart["Precio"]).sum())

        # Billete y vuelto
        st.markdown('<div class="section-label">Pago del cliente</div>', unsafe_allow_html=True)
        abono_f = st.number_input("Abono del cliente ($)", min_value=0, value=0, step=1000, key="abono_f")
        if abono_f > 0:
            if abono_f >= total_fac:
                st.markdown(f'<div class="info-box">💰 Total: <b>{fmt(total_fac)}</b> · Devolver: <b>{fmt(abono_f - total_fac)}</b></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="warn-box">📋 Abono: <b>{fmt(abono_f)}</b> · Queda debiendo: <b>{fmt(total_fac - abono_f)}</b></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warn-box">📋 Sin abono — queda debiendo: <b>{fmt(total_fac)}</b></div>', unsafe_allow_html=True)

        if st.button("✅ Confirmar venta", key="btn_vf"):
            if not cliente_f.strip():
                st.markdown('<div class="alert-low">⚠️ Escribe el nombre del cliente.</div>', unsafe_allow_html=True)
            else:
                sin_stock_f = [s for s, c in st.session_state.carrito.items() if get_stock(s) < c]
                if sin_stock_f:
                    st.markdown(f'<div class="alert-low">⚠️ Stock insuficiente: <b>{", ".join(sin_stock_f)}</b>. Ajusta el carrito.</div>', unsafe_allow_html=True)
                else:
                    fid = str(uuid.uuid4())[:8].upper()
                    total_venta_f = 0
                    abono_val_f = int(st.session_state.get("abono_f", 0))
                    for s, c in st.session_state.carrito.items():
                        precio_final = st.session_state.precios_carrito.get(s, PRODUCTOS[s])
                        subtotal = precio_final * c
                        total_venta_f += subtotal
                        sb_post("ventas", {
                            "fecha": fecha_hoy(), "hora": ahora(), "canal": "Fábrica",
                            "vendedor": vendedor_f, "sabor": s, "cantidad": c,
                            "total": subtotal, "cliente": cliente_f.strip(),
                            "factura_id": fid, "abono": abono_val_f, "saldo": 0
                        })
                        restar_stock(s, c)
                    saldo_final_f = max(0, total_venta_f - abono_val_f)
                    sb_patch("ventas", f"factura_id=eq.{fid}", {"abono": abono_val_f, "saldo": saldo_final_f})
                    st.session_state.factura_guardada = {
                        "id": fid, "cliente": cliente_f.strip(),
                        "vendedor": vendedor_f,
                        "items": dict(st.session_state.carrito),
                        "precios": dict(st.session_state.precios_carrito),
                        "total": total_venta_f,
                        "billete": abono_val_f,
                        "saldo": saldo_final_f,
                    }
                    st.session_state.carrito = {}
                    st.session_state.precios_carrito = {}
                    time.sleep(0.3)
                    st.rerun()

    # Opciones post-venta — solo si hay una factura activa en esta sesión
    if st.session_state.factura_guardada:
        fac = st.session_state.factura_guardada
        vuelto = fac["billete"] - fac["total"] if fac["billete"] >= fac["total"] and fac["billete"] > 0 else 0
        saldo_fac = fac.get("saldo", 0)
        msg_f = f'✅ Venta registrada — <b>#{fac["id"]}</b> · {fac["cliente"]} · {fmt(fac["total"])}'
        if vuelto > 0:
            msg_f += f'<br>💵 Devolver: <b>{fmt(vuelto)}</b>'
        if saldo_fac > 0:
            msg_f += f'<br>📋 Queda debiendo: <b>{fmt(saldo_fac)}</b>'
        st.markdown(f'<div class="success-toast">{msg_f}</div>', unsafe_allow_html=True)

        # Modificar factura post-venta
        st.markdown('<div class="section-label">¿El cliente quiere algo más?</div>', unsafe_allow_html=True)
        tab_cambio_f, tab_agregar_f = st.tabs(["🔁 Cambiar producto", "➕ Agregar producto"])

        with tab_cambio_f:
            col_a, col_b = st.columns(2)
            sabores_en_fac = list(fac["items"].keys())
            sabor_out = col_a.selectbox("Devuelve", sabores_en_fac, key="cambio_out")
            max_out_f = fac["items"].get(sabor_out, 1)
            cant_out  = col_a.number_input("Cantidad que devuelve", min_value=1, max_value=max_out_f, value=1, step=1, key="cant_out")
            sabor_in  = col_b.selectbox("Lleva en cambio", SABORES_LISTA, key="cambio_in")
            max_in_f  = max(1, get_stock(sabor_in))
            cant_in   = col_b.number_input("Cantidad que lleva", min_value=1, max_value=max_in_f, value=1, step=1, key="cant_in")

            valor_out = fac["precios"].get(sabor_out, PRODUCTOS[sabor_out]) * cant_out
            valor_in  = fac["precios"].get(sabor_in,  PRODUCTOS[sabor_in])  * cant_in
            diferencia = valor_in - valor_out
            if diferencia > 0:
                st.markdown(f'<div class="warn-box">💰 El cliente debe pagar <b>{fmt(diferencia)}</b> adicionales</div>', unsafe_allow_html=True)
            elif diferencia < 0:
                st.markdown(f'<div class="info-box">💵 Hay que devolver <b>{fmt(abs(diferencia))}</b> al cliente</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="info-box">✅ Cambio sin diferencia de valor</div>', unsafe_allow_html=True)

            if st.button("🔁 Registrar cambio", key="btn_cambio"):
                sb_post("ventas", {"fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                    "vendedor": fac["vendedor"], "sabor": sabor_out,
                    "cantidad": -cant_out, "total": -valor_out,
                    "cliente": fac["cliente"], "factura_id": fac["id"],
                    "abono": 0, "saldo": 0})
                agregar_stock(sabor_out, cant_out)
                sb_post("ventas", {"fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                    "vendedor": fac["vendedor"], "sabor": sabor_in,
                    "cantidad": cant_in, "total": valor_in,
                    "cliente": fac["cliente"], "factura_id": fac["id"],
                    "abono": 0, "saldo": 0})
                restar_stock(sabor_in, cant_in)
                if diferencia != 0:
                    raw_saldo_f = sb_get("ventas", f"select=saldo&factura_id=eq.{fac['id']}&canal=eq.Fábrica&limit=1")
                    saldo_act_f = float(raw_saldo_f[0]["saldo"]) if raw_saldo_f else 0
                    nuevo_saldo_f = max(0, saldo_act_f + diferencia)
                    sb_patch("ventas", f"factura_id=eq.{fac['id']}&canal=eq.Fábrica", {"saldo": nuevo_saldo_f})
                time.sleep(0.3)
                _recargar_factura_f(fac)
                st.rerun()
                restar_stock(sabor_in, cant_in)
                time.sleep(0.3)
                _recargar_factura_f(fac)
                st.rerun()

        with tab_agregar_f:
            sabor_add_f = st.selectbox("Sabor a agregar", SABORES_LISTA, key="add_sabor_f")
            cant_add_f  = st.number_input("Cantidad", min_value=1, max_value=50, value=1, step=1, key="add_cant_f")
            precio_add_f = fac["precios"].get(sabor_add_f, PRODUCTOS[sabor_add_f]) * cant_add_f
            st.markdown(f'<div class="info-box">💰 A cobrar adicionalmente: <b>{fmt(precio_add_f)}</b></div>', unsafe_allow_html=True)

            if st.button("➕ Agregar a la factura", key="btn_add_f"):
                sb_post("ventas", {"fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                    "vendedor": fac["vendedor"], "sabor": sabor_add_f,
                    "cantidad": cant_add_f, "total": precio_add_f,
                    "cliente": fac["cliente"], "factura_id": fac["id"],
                    "abono": 0, "saldo": 0})
                restar_stock(sabor_add_f, cant_add_f)
                # Actualizar saldo — el cliente debe más
                raw_saldo_f2 = sb_get("ventas", f"select=saldo&factura_id=eq.{fac['id']}&canal=eq.Fábrica&limit=1")
                saldo_act_f2 = float(raw_saldo_f2[0]["saldo"]) if raw_saldo_f2 else 0
                nuevo_saldo_f2 = saldo_act_f2 + precio_add_f
                sb_patch("ventas", f"factura_id=eq.{fac['id']}&canal=eq.Fábrica", {"saldo": nuevo_saldo_f2})
                time.sleep(0.3)
                _recargar_factura_f(fac)
                st.rerun()
                st.rerun()

        if st.button("🧾 Nueva venta", key="btn_nueva"):
            st.session_state.factura_guardada = None
            st.rerun()

    # Ventas de hoy — visible para todos, igual que en el resumen del admin
    st.markdown('<div class="section-label">Ventas de hoy</div>', unsafe_allow_html=True)
    st.caption("Toca una fila para ver el recibo completo.")
    raw_fact_f = sb_get("ventas",
        f"select=fecha,hora,cliente,vendedor,sabor,cantidad,total,factura_id,es_credito&fecha=eq.{fecha_hoy()}&canal=eq.Fábrica&order=hora.desc")
    if raw_fact_f:
        df_fact_f = pd.DataFrame(raw_fact_f)
        mostrar_facturas_seleccionables(df_fact_f, "fabrica_todos")
    else:
        st.caption("Aún no hay ventas registradas hoy.")

    mostrar_creditos_pendientes("Fábrica")


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
                f'<div class="factura-row"><span>👤 {v}</span><span><b>{fmt(t)}</b></span></div>'
                for v, t in por_vendedor.items()
            )
            st.markdown(
                f'<div class="factura-box">{filas_v}'
                f'<div class="factura-row"><span>🛒 Bolsas vendidas hoy</span><span><b>{bolsas_fab_dia}</b></span></div>'
                f'<div class="factura-total"><span>💰 Total a entregar</span><span>{fmt(total_fab_dia)}</span></div>'
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
        components.html("""
        <div style="text-align:center;margin-top:12px;">
            <button onclick="window.print()" style="
                background:#1565C0;color:white;border:none;
                border-radius:12px;padding:14px 32px;
                font-size:1rem;font-weight:700;cursor:pointer;
                box-shadow:0 4px 12px rgba(21,101,192,0.3);
            ">🖨️ Imprimir recibo</button>
        </div>
        <style>
        @media print {
            /* Ocultar todo excepto el recibo */
            body > * { display: none !important; }
            .recibo-wrap { display: flex !important; }
            .recibo-ticket {
                width: 58mm !important;
                margin: 0 auto !important;
                box-shadow: none !important;
                font-size: 11px !important;
            }
            /* Ocultar botones de Streamlit */
            .stButton, .stApp header, footer, [data-testid="stToolbar"] {
                display: none !important;
            }
        }
        </style>
        """, height=80)
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

    st.markdown('<div class="section-label">Materia Prima e Insumos 🌽</div>', unsafe_allow_html=True)
    tab_mp1, tab_mp2, tab_mp3, tab_mp4 = st.tabs(["➕ Entrada", "📤 Salida", "💳 Créditos", "📋 Historial"])

    def registrar_entrada_mp(nombre_sel, unidad_sel, cant_mp, prov_mp, precio_mp, abono_mp, saldo_mp, precio_unit_mp=0):
        if not prov_mp.strip():
            st.markdown('<div class="alert-low">⚠️ Escribe el nombre del proveedor.</div>', unsafe_allow_html=True)
            return False
        if precio_mp == 0:
            st.markdown('<div class="alert-low">⚠️ Ingresa el precio total.</div>', unsafe_allow_html=True)
            return False
        data_mp = {
            "fecha": fecha_hoy(), "hora": ahora(),
            "insumo": nombre_sel, "cantidad": float(cant_mp),
            "unidad": unidad_sel, "proveedor": prov_mp.strip(),
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
            cant_mp   = st.number_input(f"Cantidad ({unidad_sel})", min_value=0.1, max_value=9999.0, value=1.0, step=0.5, key="cant_mp")
            prov_mp   = st.text_input("Proveedor", placeholder="Ej: Distribuidora La 14", key="prov_mp")
            precio_mp = st.number_input("Precio total ($)", min_value=0, value=0, step=1000, key="precio_mp")
            precio_unit_mp = round(precio_mp / cant_mp, 2) if cant_mp > 0 and precio_mp > 0 else 0
            if precio_unit_mp > 0:
                st.markdown(f'<div class="info-box">💰 Precio unitario: <b>{fmt(precio_unit_mp)}</b> por {unidad_sel}</div>', unsafe_allow_html=True)
            if con_credito:
                abono_mp = st.number_input("Abono inicial ($)", min_value=0, max_value=max(0, precio_mp), value=0, step=1000, key="abono_mp")
                saldo_mp = max(0, precio_mp - abono_mp)
                if precio_mp > 0:
                    if abono_mp >= precio_mp:
                        st.markdown(f'<div class="info-box">✅ Pago completo</div>', unsafe_allow_html=True)
                    elif abono_mp > 0:
                        st.markdown(f'<div class="warn-box">📋 Debe: <b>{fmt(saldo_mp)}</b></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="warn-box">📋 Fiado: <b>{fmt(precio_mp)}</b></div>', unsafe_allow_html=True)
            else:
                abono_mp = precio_mp; saldo_mp = 0
            col1, col2 = st.columns(2)
            if col1.button("✅ Registrar", key="btn_mp"):
                if registrar_entrada_mp(nombre_sel, unidad_sel, cant_mp, prov_mp, precio_mp, abono_mp, saldo_mp, precio_unit_mp):
                    st.session_state.ok_mp = True
                    st.session_state.insumo_sel = None
                    st.session_state.categoria_mp = None
                    time.sleep(0.3); st.rerun()
            if col2.button("← Cambiar", key="btn_cambiar_ins"):
                st.session_state.insumo_sel = None; st.rerun()

        if st.session_state.get("ok_mp"):
            st.markdown('<div class="success-toast">✅ Entrada registrada.</div>', unsafe_allow_html=True)
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
            st.markdown(f'<div class="alert-low">🔴 No hay stock disponible de <b>{insumo_sal}</b>. Registra una entrada primero.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box">📦 Stock disponible de <b>{insumo_sal}</b>: <b>{stock_disp_sal:.1f} {unidad_sal}</b></div>', unsafe_allow_html=True)

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
                    st.markdown('<div class="success-toast">✅ Salida registrada.</div>', unsafe_allow_html=True)
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
            st.markdown(f'<div class="warn-box">💳 Total pendiente: <b>{fmt(total)}</b></div>', unsafe_allow_html=True)
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
            mostrar_creditos_mp(pend_mp, "🌽")
        with sc2:
            st.markdown('<div class="section-label">Créditos — Saborizantes</div>', unsafe_allow_html=True)
            mostrar_creditos_mp(pend_sab, "🧂")

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
            if k not in resumen:
                resumen[k] = {"entradas": 0, "salidas": 0, "unidad": r["unidad"], "gasto": 0}
            resumen[k]["entradas"] += float(r["cantidad"])
            resumen[k]["gasto"]    += float(r["precio_total"])
        for r in raw_sal:
            k = r["insumo"]
            if k not in resumen:
                resumen[k] = {"entradas": 0, "salidas": 0, "unidad": r["unidad"], "gasto": 0}
            resumen[k]["salidas"] += float(r["cantidad"])

        def tabla_resumen(data, titulo, icono, raw_ent_cat, raw_sal_cat):
            if not data and not raw_ent_cat and not raw_sal_cat: return
            st.markdown(f'<div class="section-label">{icono} {titulo}</div>', unsafe_allow_html=True)
            if data:
                # Calcular precio unitario promedio ponderado por insumo
                precio_unit_por_insumo = {}
                for r in raw_ent_cat:
                    k = r["insumo"]
                    pu = float(r.get("precio_unitario", 0))
                    if pu > 0:
                        precio_unit_por_insumo[k] = pu

                filas_res = []
                for k, v in data.items():
                    pu = precio_unit_por_insumo.get(k, 0)
                    costo_consumido = v["salidas"] * pu if pu > 0 else 0
                    filas_res.append({
                        "Insumo": k,
                        "Entradas": f'{v["entradas"]} {v["unidad"]}',
                        "Salidas": f'{v["salidas"]} {v["unidad"]}',
                        "Stock": f'{v["entradas"]-v["salidas"]:.1f} {v["unidad"]}',
                        "Precio unitario": fmt(pu) if pu > 0 else "—",
                        "Costo consumido": fmt(costo_consumido) if costo_consumido > 0 else "—",
                        "Gasto total entrada": fmt(v["gasto"])
                    })
                st.dataframe(pd.DataFrame(filas_res), use_container_width=True, hide_index=True)
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
                tabla_resumen(res_mp,  "Materia Prima", "🌽", ent_mp,  sal_mp)
            with sh2:
                tabla_resumen(res_sab, "Saborizantes",  "🧂", ent_sab, sal_sab)
            with sh3:
                tabla_resumen(res_emp, "Empaque",       "📦", ent_emp, sal_emp)
        else:
            st.info("No hay registros en ese período.")

elif st.session_state.vista == "resumen" and st.session_state.es_admin:
    sub_r1, sub_r2, sub_r3, sub_r4 = st.tabs(["Hoy", "Por fechas", "📅 Mes", "💾 Exportar"])

    with sub_r1:
        st.markdown('<div class="section-label">Resumen del día</div>', unsafe_allow_html=True)
        raw_vt = sb_get("ventas", f"select=*&fecha=eq.{fecha_hoy()}&order=hora.asc")
        if not raw_vt:
            st.info("Aún no hay ventas hoy.")
        else:
            df_vt = pd.DataFrame(raw_vt)
            total_fab   = int(df_vt[df_vt["canal"]=="Fábrica"]["total"].sum()) if "canal" in df_vt.columns else 0
            total_carro = int(df_vt[df_vt["canal"]=="Carro"]["total"].sum())   if "canal" in df_vt.columns else 0
            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-blue"><div class="val">{fmt(total_fab)}</div><div class="lbl">Fábrica</div></div>
                <div class="metric-box metric-yellow"><div class="val">{fmt(total_carro)}</div><div class="lbl">Carro</div></div>
                <div class="metric-box metric-green"><div class="val">{fmt(total_fab+total_carro)}</div><div class="lbl">Total</div></div>
            </div>""", unsafe_allow_html=True)

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
            total_r  = int(df_r["total"].sum())
            bolsas_r = int(df_r["cantidad"].sum())
            dias_r   = df_r["fecha"].nunique()
            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-green"><div class="val">{fmt(total_r)}</div><div class="lbl">Ingresos</div></div>
                <div class="metric-box metric-blue"><div class="val">{bolsas_r}</div><div class="lbl">Bolsas</div></div>
                <div class="metric-box metric-yellow"><div class="val">{dias_r}</div><div class="lbl">Días</div></div>
            </div>""", unsafe_allow_html=True)

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
            total_mes   = int(df_mes["total"].sum())
            bolsas_mes  = int(df_mes["cantidad"].sum())
            dias_mes    = df_mes["fecha"].nunique()
            prod_mes    = sum(r["cantidad"] for r in raw_prod_mes) if raw_prod_mes else 0
            promedio_dia = total_mes / dias_mes if dias_mes > 0 else 0

            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box metric-green"><div class="val">{fmt(total_mes)}</div><div class="lbl">Ingresos del mes</div></div>
                <div class="metric-box metric-blue"><div class="val">{bolsas_mes}</div><div class="lbl">Bolsas vendidas</div></div>
                <div class="metric-box metric-yellow"><div class="val">{fmt(promedio_dia)}</div><div class="lbl">Promedio diario</div></div>
            </div>""", unsafe_allow_html=True)

            st.markdown(f'<div class="info-box">📦 Producción total del mes: <b>{prod_mes} bolsas</b></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-label">Sabor más vendido</div>', unsafe_allow_html=True)
            top_sabores = df_mes.groupby("sabor")["cantidad"].sum().reset_index().sort_values("cantidad", ascending=False)
            if not top_sabores.empty:
                top1 = top_sabores.iloc[0]
                st.markdown(f'<div class="info-box">🏆 <b>{top1["sabor"]}</b> con {int(top1["cantidad"])} bolsas vendidas</div>', unsafe_allow_html=True)

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

        if st.button("📥 Ventas (CSV)", key="btn_exp_v"):
            raw_e = sb_get("ventas", f"select=*&fecha=gte.{f_exp_ini}&fecha=lte.{f_exp_fin}&order=fecha.asc")
            if raw_e:
                csv = pd.DataFrame(raw_e).to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Descargar ventas", csv, f"ventas_{f_exp_ini}_{f_exp_fin}.csv", "text/csv", key="dl_v")

        if st.button("📥 Producción (CSV)", key="btn_exp_p"):
            raw_e2 = sb_get("produccion", f"select=*&fecha=gte.{f_exp_ini}&fecha=lte.{f_exp_fin}&order=fecha.asc")
            if raw_e2:
                csv2 = pd.DataFrame(raw_e2).to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Descargar producción", csv2, f"produccion_{f_exp_ini}_{f_exp_fin}.csv", "text/csv", key="dl_p")

        if st.button("📥 Inventario actual (CSV)", key="btn_exp_i"):
            raw_e3 = sb_get("inventario", "select=*&order=sabor.asc")
            if raw_e3:
                csv3 = pd.DataFrame(raw_e3).to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Descargar inventario", csv3, f"inventario_{fecha_hoy()}.csv", "text/csv", key="dl_i")

        st.markdown('<div class="warn-box">💡 Guarda estos archivos semanalmente como respaldo.</div>', unsafe_allow_html=True)
