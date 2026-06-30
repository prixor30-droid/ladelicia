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
        filas.append({
            "Fecha": grupo["fecha"].iloc[0],
            "N° Comprobante": f"FV-{fid}",
            "Vendedor": grupo["vendedor"].iloc[0],
            "Cliente": grupo["cliente"].iloc[0],
            "Total": fmt(grupo["total"].sum()),
            "Estado": "✓ Aprobado",
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
        st.session_state.recibo_a_mostrar = fid_sel
        st.session_state.recibo_canal_df = df_canal[df_canal["factura_id"]==fid_sel].to_dict("records")
        st.session_state.vista = "recibo"
        st.rerun()

def render_recibo(registros):
    """Genera el HTML de un recibo tipo ticket de papel a partir de los registros de una factura."""
    if not registros:
        return ""
    r0 = registros[0]
    fid = r0["factura_id"]
    fecha_r = r0["fecha"]
    hora_r = r0["hora"]
    cliente_r = r0.get("cliente", "Consumidor Final") or "Consumidor Final"
    vendedor_r = r0["vendedor"]
    total_r = sum(r["total"] for r in registros)

    items_partes = []
    for r in registros:
        precio_unit = fmt(r['total']/r['cantidad']) if r['cantidad'] else fmt(0)
        items_partes.append(
            '<div class="recibo-item">'
            f'<div class="recibo-item-nombre">{r["sabor"]}</div>'
            '<div class="recibo-item-detalle">'
            f'<span>{r["cantidad"]} × {precio_unit}</span>'
            f'<span>{fmt(r["total"])}</span>'
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
    <div style="position:relative;width:100%;height:{altura}px;background:#FFFFFF;border-radius:14px;padding:12px;box-shadow:0 2px 10px rgba(216,27,122,0.10);">
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
                backgroundColor: '#D81B7A',
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
                x: {{ grid: {{ color: '#F0E0E8' }}, ticks: {{ color: '#9C4270', font: {{ size: 11 }} }} }},
                y: {{ grid: {{ display: false }}, ticks: {{ color: '#1A0A12', font: {{ size: 12, weight: '600' }} }} }}
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
    <div style="position:relative;width:100%;height:260px;background:#FFFFFF;border-radius:14px;padding:14px;box-shadow:0 2px 10px rgba(216,27,122,0.10);">
        <canvas id="chartLinea" role="img" aria-label="Gráfica de evolución de ventas en el mes"></canvas>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
    <script>
    const ctx = document.getElementById('chartLinea').getContext('2d');
    const gradiente = ctx.createLinearGradient(0,0,0,220);
    gradiente.addColorStop(0, 'rgba(216,27,122,0.25)');
    gradiente.addColorStop(1, 'rgba(216,27,122,0.02)');
    new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: {fechas_json},
            datasets: [{{
                label: 'Ventas',
                data: {valores_json},
                borderColor: '#D81B7A',
                backgroundColor: gradiente,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: '#D81B7A',
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
                x: {{ grid: {{ display: false }}, ticks: {{ color: '#9C4270', font: {{ size: 10 }}, maxRotation: 45 }} }},
                y: {{ grid: {{ color: '#F0E0E8' }}, ticks: {{ color: '#9C4270', font: {{ size: 11 }} }} }}
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

@st.cache_data(ttl=15)
def get_inventario_completo():
    """Trae todo el inventario de una sola vez, cacheado 15 segundos."""
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
    get_inventario_completo.clear()

def restar_stock(sabor, cantidad):
    q = requests.utils.quote(sabor)
    r = sb_get("inventario", f"select=stock&sabor=eq.{q}")
    stock = int(r[0]["stock"]) if r else 0
    sb_patch("inventario", f"sabor=eq.{q}", {"stock": max(0, stock - cantidad)})
    get_inventario_completo.clear()

def set_stock(sabor, cantidad):
    q = requests.utils.quote(sabor)
    sb_patch("inventario", f"sabor=eq.{q}", {"stock": cantidad})
    get_inventario_completo.clear()

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
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif !important;background-color:#FFF8FB !important;color:#1A0A12 !important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem;padding-bottom:3rem;max-width:500px;margin:0 auto;}
@media (min-width: 768px){
  .block-container{max-width:900px;}
  html,body{font-size:17px;}
  .brand-header p{font-size:0.95rem;}
  .metric-box .val{font-size:1.6rem;}
  .metric-box .lbl{font-size:0.8rem;}
  .section-label{font-size:0.85rem;}
  .stButton>button{font-size:1.15rem !important;padding:18px !important;}
  label,.stSelectbox label,.stNumberInput label,.stDateInput label,.stTextInput label{font-size:1rem !important;}
}
@media (min-width: 1200px){
  .block-container{max-width:1100px;}
  html,body{font-size:18px;}
  .metric-box .val{font-size:1.9rem;}
  .stButton>button{font-size:1.25rem !important;padding:20px !important;}
}
[data-baseweb="base-input"],[data-baseweb="base-input"] *,[data-baseweb="select"],[data-baseweb="select"]>div,[data-baseweb="select"]>div>div{background-color:#FFFFFF !important;color:#1A0A12 !important;border-color:#E5C5D5 !important;}
[data-baseweb="base-input"] input,[data-baseweb="base-input"] textarea,input[type="number"],input[type="text"],input[type="date"]{background-color:#FFFFFF !important;color:#1A0A12 !important;-webkit-text-fill-color:#1A0A12 !important;}
[data-testid="stNumberInputStepDown"],[data-testid="stNumberInputStepUp"]{background-color:#FCE4EC !important;color:#D81B7A !important;border:none !important;border-radius:7px !important;}
[data-testid="stNumberInputStepDown"]:hover,[data-testid="stNumberInputStepUp"]:hover{background-color:#D81B7A !important;color:white !important;}
[data-baseweb="select"]>div,[data-baseweb="base-input"]{border-radius:10px !important;border:1.5px solid #E5C5D5 !important;}
[data-baseweb="select"] input{caret-color:transparent !important;cursor:pointer !important;}
[data-baseweb="select"] input:focus{caret-color:transparent !important;}
[data-baseweb="select"]>div:focus-within,[data-baseweb="base-input"]:focus-within{border-color:#D81B7A !important;box-shadow:0 0 0 3px rgba(216,27,122,0.15) !important;}
[data-baseweb="popover"],[data-baseweb="popover"] *,[data-baseweb="menu"],[data-baseweb="menu"] *,ul[data-testid="stSelectboxVirtualDropdown"],ul[data-testid="stSelectboxVirtualDropdown"] *{background-color:#FFFFFF !important;color:#1A0A12 !important;}
[data-baseweb="menu"] li:hover,[role="option"]:hover,[aria-selected="true"][role="option"]{background-color:#FCE4EC !important;color:#D81B7A !important;}
[data-baseweb="calendar"],[data-baseweb="calendar"] *{background-color:#FFFFFF !important;color:#1A0A12 !important;}
[data-baseweb="calendar"] button{color:#1A0A12 !important;background-color:transparent !important;}
[data-baseweb="calendar"] button:hover{background-color:#FCE4EC !important;color:#D81B7A !important;}
[data-baseweb="calendar"] [aria-selected="true"]{background-color:#D81B7A !important;color:white !important;}
[data-baseweb="calendar"] tbody tr:last-child td{background-color:#FFFFFF !important;}
label,.stSelectbox label,.stNumberInput label,.stDateInput label,.stTextInput label{color:#D81B7A !important;font-weight:600 !important;font-size:0.85rem !important;}
.stTabs [data-baseweb="tab-list"]{background:#FFFFFF;border-radius:12px;padding:4px;gap:2px;box-shadow:0 1px 4px rgba(216,27,122,0.10);margin-bottom:16px;}
.stTabs [data-baseweb="tab"]{border-radius:10px;font-size:0.78rem;font-weight:600;padding:8px 4px;color:#7A2050 !important;flex:1;justify-content:center;background:transparent !important;}
.stTabs [aria-selected="true"]{background-color:#D81B7A !important;color:white !important;}
.brand-header{background:linear-gradient(135deg,#D81B7A,#F06292);border-radius:0 0 22px 22px;padding:22px 20px 18px;margin:-1rem -1rem 16px -1rem;text-align:center;}
.brand-header p{color:rgba(255,255,255,0.85);font-size:0.78rem;margin:0;}
.metric-row{display:flex;gap:9px;margin-bottom:16px;}
.metric-box{flex:1;background:#FFFFFF;border-radius:14px;padding:14px 8px;text-align:center;box-shadow:0 2px 8px rgba(216,27,122,0.12);}
.metric-box .val{font-size:1.2rem;font-weight:700;line-height:1.1;}
.metric-box .lbl{font-size:0.65rem;color:#9C4270;margin-top:3px;}
.metric-pink .val{color:#D81B7A;}.metric-green .val{color:#1B9E5A;}.metric-red .val{color:#D32F2F;}.metric-yellow .val{color:#E68900;}
.alert-low{background:#FFEBEE;border-left:3px solid #D32F2F;border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:9px;font-size:0.83rem;color:#B71C1C;}
.info-box{background:#FFFFFF;border-left:3px solid #1B9E5A;border-radius:10px;padding:12px 14px;margin:8px 0 14px;font-size:0.82rem;color:#1B5E20;box-shadow:0 1px 6px rgba(0,0,0,0.05);}
.warn-box{background:#FFFFFF;border-left:3px solid #E68900;border-radius:10px;padding:12px 14px;margin:8px 0 14px;font-size:0.82rem;color:#8D6E00;box-shadow:0 1px 6px rgba(0,0,0,0.05);}
.success-toast{background:#E8F5E9;border:1px solid #A5D6A7;border-radius:12px;padding:14px 16px;text-align:center;font-weight:600;color:#1B5E20;font-size:0.95rem;margin-top:10px;}
.section-label{font-size:0.69rem;font-weight:700;text-transform:uppercase;letter-spacing:0.7px;color:#B0185F;margin:16px 0 6px;}
.stButton>button{width:100%;background:#D81B7A !important;color:white !important;-webkit-text-fill-color:white !important;border:none !important;border-radius:12px !important;padding:14px !important;font-size:1rem !important;font-weight:700 !important;cursor:pointer;margin-top:4px;box-shadow:0 4px 16px rgba(216,27,122,0.25);white-space:pre-line !important;line-height:1.4 !important;}
.stButton>button:hover{opacity:0.88;}
[data-testid="stButton-btn_produccion"],[data-testid="stButton-btn_carro"],[data-testid="stButton-btn_fabrica"],[data-testid="stButton-btn_resumen"]{width:100% !important;max-width:100% !important;}
[data-testid="stButton-btn_produccion"] button,[data-testid="stButton-btn_carro"] button,[data-testid="stButton-btn_fabrica"] button,[data-testid="stButton-btn_resumen"] button{background:#FFFFFF !important;color:#1A0A12 !important;-webkit-text-fill-color:#1A0A12 !important;box-shadow:0 2px 10px rgba(216,27,122,0.15) !important;min-height:84px !important;border-radius:16px !important;width:100% !important;max-width:100% !important;}
[data-testid="stButton-btn_produccion"] button:hover,[data-testid="stButton-btn_carro"] button:hover,[data-testid="stButton-btn_fabrica"] button:hover,[data-testid="stButton-btn_resumen"] button:hover{box-shadow:0 4px 14px rgba(216,27,122,0.22) !important;opacity:1 !important;}
div[data-testid="stElementContainer"]:has([data-testid="stButton-btn_produccion"]),div[data-testid="stElementContainer"]:has([data-testid="stButton-btn_carro"]),div[data-testid="stElementContainer"]:has([data-testid="stButton-btn_fabrica"]),div[data-testid="stElementContainer"]:has([data-testid="stButton-btn_resumen"]){width:100% !important;min-width:100% !important;}

[data-testid="stMetricLabel"] p{color:#9C4270 !important;}
[data-testid="stMetricValue"]{color:#1A0A12 !important;}
.stDataFrame{border-radius:12px;overflow:hidden;font-size:0.83rem;border:1px solid #E5C5D5;}
.stCaption,small{color:#9C4270 !important;}
.stAlert{background:#FAF0F5 !important;color:#1A0A12 !important;border-color:#E5C5D5 !important;}
.factura-box{background:#FFFFFF;border-radius:16px;padding:16px;margin-bottom:14px;box-shadow:0 2px 10px rgba(216,27,122,0.10);}
.factura-header{font-size:0.9rem;font-weight:700;color:#D81B7A;margin-bottom:8px;}
.factura-row{display:flex;justify-content:space-between;font-size:0.85rem;padding:4px 0;border-bottom:1px solid #E5C5D5;color:#1A0A12;}
.factura-total{display:flex;justify-content:space-between;font-size:1rem;font-weight:700;color:#1B9E5A;margin-top:8px;}
.factura-cambio{font-size:0.9rem;color:#E68900;margin-top:6px;text-align:center;}
.tabla-fact-wrap{overflow-x:auto;border-radius:10px;box-shadow:0 2px 10px rgba(216,27,122,0.10);margin-bottom:14px;}
.tabla-fact{width:100%;border-collapse:collapse;font-size:0.78rem;background:#FFFFFF;}
.tabla-fact thead{background:#D81B7A;}
.tabla-fact thead th{color:white;font-weight:600;padding:10px 8px;text-align:left;white-space:nowrap;}
.tabla-fact tbody td{padding:9px 8px;border-bottom:1px solid #F0E0E8;color:#1A0A12;white-space:nowrap;}
.tabla-fact tbody tr:hover{background:#FAF0F5;}
.tabla-fact .num-comp{color:#D81B7A;font-weight:600;}
.tabla-fact .estado-ok{color:#1B9E5A;font-weight:600;}
.tabla-fact .total-col{text-align:right;font-weight:600;}
.recibo-wrap{display:flex;justify-content:center;padding:20px 0;}
.recibo-ticket{background:#FFFFFF;width:100%;max-width:380px;padding:24px 20px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.12);font-family:'Courier New',monospace;}
.recibo-logo{text-align:center;margin-bottom:6px;}
.recibo-logo img{height:60px !important;}
.recibo-titulo{text-align:center;font-weight:700;font-size:1rem;color:#1A0A12;}
.recibo-sub{text-align:center;font-size:0.78rem;color:#9C4270;}
.recibo-linea-punteada{border-top:1.5px dashed #D8B5C8;margin:12px 0;}
.recibo-dato{font-size:0.82rem;color:#1A0A12;margin-bottom:4px;}
.recibo-item{margin-bottom:8px;}
.recibo-item-nombre{font-size:0.85rem;font-weight:600;color:#1A0A12;}
.recibo-item-detalle{display:flex;justify-content:space-between;font-size:0.8rem;color:#9C4270;}
.recibo-total-row{display:flex;justify-content:space-between;font-size:1.05rem;font-weight:700;color:#1B9E5A;}
.recibo-footer{text-align:center;font-size:0.8rem;color:#9C4270;font-style:italic;}
.calc-box{background:#FFFFFF;border-radius:14px;padding:14px;margin-bottom:14px;box-shadow:0 2px 10px rgba(216,27,122,0.10);}
.main-btn{background:#FAF0F5;border:1px solid #E5C5D5;border-radius:14px;padding:20px 16px;margin-bottom:10px;cursor:pointer;display:flex;align-items:center;gap:14px;}
.main-btn-icon{font-size:2rem;}
.main-btn-text{font-size:1.1rem;font-weight:700;color:#1A0A12;}
.main-btn-sub{font-size:0.78rem;color:#9C4270;}
</style>
""", unsafe_allow_html=True)

# Bloquear teclado virtual en los selectbox (solo permite tocar y elegir)
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
function arreglarAnchoBotonesMenu() {
    try {
        const keys = ['btn_produccion', 'btn_carro', 'btn_fabrica', 'btn_resumen'];
        keys.forEach(function(k) {
            const btnWrap = window.parent.document.querySelector('[data-testid="stButton-' + k + '"]');
            if (btnWrap) {
                let el = btnWrap;
                for (let i = 0; i < 4; i++) {
                    if (el && el.parentElement) {
                        el = el.parentElement;
                        if (el.getAttribute('data-testid') === 'stElementContainer') {
                            el.style.width = '100%';
                            el.style.minWidth = '100%';
                            el.style.maxWidth = '100%';
                            break;
                        }
                    }
                }
            }
        });
    } catch (e) {}
}
bloquearTecladoSelects();
arreglarAnchoBotonesMenu();
setInterval(bloquearTecladoSelects, 500);
setInterval(arreglarAnchoBotonesMenu, 500);
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
    "carrito": {},
    "precios_carrito": {},  # precio modificado por item
    "carrito_carro": {},
    "precios_carro": {},
    "factura_guardada": None,
    "ok_prod": False,
    "ok_cargue": False,
    "ok_dev": False,
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
    "jorge":  "096f6432e029084963ccb57b61a5b46dd3188f9d4fe73333d7be8289ffeb7057",
    "andrea": "55739c3876b1b91c8ef3712eda72ec732cd187f1c31f59f14ab187fe3cd04b5f",
}
NOMBRES_ADMIN = {"jorge": "Jorge", "andrea": "Andrea"}

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
@st.cache_data(ttl=10)
def get_metricas_globales(fecha):
    _inv   = sb_get("inventario", "select=sabor,stock")
    _prod  = sb_get("produccion", f"select=cantidad&fecha=eq.{fecha}")
    _venta = sb_get("ventas",     f"select=total&fecha=eq.{fecha}")
    return _inv, _prod, _venta

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
    <div class="metric-box metric-pink"><div class="val">{total_inv}</div><div class="lbl">En inventario</div></div>
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
    texto_volver = "← Volver al resumen" if st.session_state.vista == "recibo" else "← Volver al menú"
    if st.button(texto_volver, key="btn_back"):
        st.session_state.vista = "resumen" if st.session_state.vista == "recibo" else "menu"
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
        ("produccion", "📦", "Producción", "Registrar bolsas fabricadas"),
        ("carro",      "🚗", "Edison & Javier", "Cargues y ventas del carro"),
        ("fabrica",    "🏭", "Fábrica", "Ventas de Sofía y Andrea"),
    ]
    if st.session_state.es_admin:
        opciones.append(("resumen", "📊", "Resumen", "Ventas, facturas y exportar"))

    st.markdown('<div class="menu-activo"></div>', unsafe_allow_html=True)
    for vista, icon, titulo, sub in opciones:
        if st.button(f"{icon}  {titulo}\n{sub}", key=f"btn_{vista}"):
            st.session_state.vista = vista
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: PRODUCCIÓN
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "produccion":
    st.markdown('<div class="section-label">Registrar producción</div>', unsafe_allow_html=True)

    empleado   = st.selectbox("¿Quién registra?", EMPLEADOS, key="emp")
    sabor_p    = st.selectbox("Sabor producido", sabores_produccion_frecuente(), key="sabor_p")
    cantidad_p = st.number_input("Bolsas producidas", min_value=1, max_value=5000, value=50, step=10, key="cant_p")

    stock_act = get_stock(sabor_p)
    st.markdown(f'<div class="info-box">📦 Stock actual de <b>{sabor_p}</b>: {stock_act} → quedará en <b>{stock_act + cantidad_p}</b></div>', unsafe_allow_html=True)

    if st.button("✅ Registrar producción", key="btn_prod"):
        sb_post("produccion", {
            "fecha": fecha_hoy(), "hora": ahora(),
            "empleado": empleado, "sabor": sabor_p, "cantidad": cantidad_p
        })
        agregar_stock(sabor_p, cantidad_p)
        get_metricas_globales.clear()
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
                diff_stock = 0
                sabor_para_stock = orig["sabor"]

                if row["Fecha"] != orig["fecha"]:
                    cambios["fecha"] = row["Fecha"]
                if row["Hora"] != orig["hora"]:
                    cambios["hora"] = row["Hora"]
                if row["Empleado"] != orig["empleado"]:
                    cambios["empleado"] = row["Empleado"]
                if row["Sabor"] != orig["sabor"]:
                    # Cambió el sabor: revertir stock del sabor viejo, aplicar al nuevo
                    restar_stock(orig["sabor"], orig["cantidad"])
                    agregar_stock(row["Sabor"], int(row["Bolsas"]))
                    cambios["sabor"] = row["Sabor"]
                    cambios["cantidad"] = int(row["Bolsas"])
                elif int(row["Bolsas"]) != orig["cantidad"]:
                    diff = int(row["Bolsas"]) - orig["cantidad"]
                    if diff > 0:
                        agregar_stock(orig["sabor"], diff)
                    elif diff < 0:
                        restar_stock(orig["sabor"], abs(diff))
                    cambios["cantidad"] = int(row["Bolsas"])

                if cambios:
                    sb_patch("produccion", f"id=eq.{orig['id']}", cambios)
            time.sleep(0.3)
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

    sub1, sub2, sub3 = st.tabs(["🚗 Nuevo cargue", "💵 Registrar venta", "🔄 Devolución"])

    with sub1:
        st.markdown('<div class="section-label">Cargue del carro</div>', unsafe_allow_html=True)
        sabor_cg = st.selectbox("Sabor", sabores_por_frecuencia("Carro"), key="sabor_cg")
        cant_cg  = st.number_input("Bolsas a cargar", min_value=1, max_value=500, value=10, step=5, key="cant_cg")
        stock_cg = get_stock(sabor_cg)

        if stock_cg < cant_cg:
            st.markdown(f'<div class="alert-low">⚠️ Solo hay {stock_cg} bolsas de {sabor_cg}.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box">📦 Disponible: <b>{stock_cg}</b> · Quedarán: <b>{stock_cg - cant_cg}</b></div>', unsafe_allow_html=True)

        if st.button("🚗 Registrar cargue", key="btn_cg", disabled=(stock_cg < cant_cg)):
            sb_post("cargues", {"fecha": fecha_hoy(), "hora": ahora(), "sabor": sabor_cg, "cantidad": cant_cg})
            restar_stock(sabor_cg, cant_cg)
            get_metricas_globales.clear()
            st.session_state.ok_cargue = True
            time.sleep(0.3)
            st.rerun()

        if st.session_state.ok_cargue:
            st.markdown('<div class="success-toast">✅ Cargue registrado.</div>', unsafe_allow_html=True)
            st.session_state.ok_cargue = False

        # Cargue activo hoy
        raw_cg = sb_get("cargues", f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}")
        raw_vc = sb_get("ventas",  f"select=sabor,cantidad&fecha=eq.{fecha_hoy()}&canal=eq.Carro")
        if raw_cg:
            df_cg = pd.DataFrame(raw_cg).groupby("sabor")["cantidad"].sum().reset_index()
            df_cg.columns = ["sabor","cargado"]
            if raw_vc:
                df_vc2 = pd.DataFrame(raw_vc).groupby("sabor")["cantidad"].sum().reset_index()
                df_vc2.columns = ["sabor","vendido"]
                df_cg = df_cg.merge(df_vc2, on="sabor", how="left").fillna(0)
            else:
                df_cg["vendido"] = 0
            df_cg["pendiente"] = df_cg["cargado"] - df_cg["vendido"]
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
                    if row["Fecha"] != orig["fecha"]:
                        cambios["fecha"] = row["Fecha"]
                    if row["Hora"] != orig["hora"]:
                        cambios["hora"] = row["Hora"]
                    if row["Sabor"] != orig["sabor"]:
                        # Cambió el sabor: revertir stock del sabor viejo (devolverlo) y restar del nuevo
                        agregar_stock(orig["sabor"], orig["cantidad"])
                        restar_stock(row["Sabor"], int(row["Bolsas"]))
                        cambios["sabor"] = row["Sabor"]
                        cambios["cantidad"] = int(row["Bolsas"])
                    elif int(row["Bolsas"]) != orig["cantidad"]:
                        diff = int(row["Bolsas"]) - orig["cantidad"]
                        if diff > 0:
                            restar_stock(orig["sabor"], diff)
                        elif diff < 0:
                            agregar_stock(orig["sabor"], abs(diff))
                        cambios["cantidad"] = int(row["Bolsas"])

                    if cambios:
                        sb_patch("cargues", f"id=eq.{orig['id']}", cambios)
                get_metricas_globales.clear()
                time.sleep(0.3)
                st.rerun()

            ids_cg = {f"{r['fecha']} {r['hora']} — {r['sabor']} ({r['cantidad']} bolsas)": r for r in raw_cg_full}
            sel_del_cg = st.selectbox("Eliminar registro", ["— Selecciona —"] + list(ids_cg.keys()), key="sel_del_cg")
            if sel_del_cg != "— Selecciona —" and col_ecg.button("🗑️ Eliminar", key="btn_del_cg"):
                reg_del_cg = ids_cg[sel_del_cg]
                sb_delete("cargues", f"id=eq.{reg_del_cg['id']}")
                agregar_stock(reg_del_cg["sabor"], reg_del_cg["cantidad"])
                get_metricas_globales.clear()
                time.sleep(0.3)
                st.rerun()

    with sub2:
        st.markdown('<div class="section-label">Venta del carro</div>', unsafe_allow_html=True)

        col_s, col_c = st.columns([2, 1])
        sabor_vc = col_s.selectbox("Sabor", sabores_por_frecuencia("Carro"), key="sabor_vc")
        cant_vc  = col_c.number_input("Bolsas", min_value=1, max_value=500, value=1, step=1, key="cant_vc")

        if st.button("➕ Agregar al carrito", key="btn_add_carro"):
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
                    "Precio":   st.column_config.NumberColumn("Precio", min_value=0, step=100),
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
            st.markdown(f'<div class="info-box">💰 Total: <b>{fmt(total_cc)}</b></div>', unsafe_allow_html=True)

            col_clr2, col_conf = st.columns(2)
            if col_clr2.button("🗑️ Vaciar carrito", key="btn_clr_cc"):
                st.session_state.carrito_carro = {}
                st.session_state.precios_carro = {}
                st.rerun()

            if col_conf.button("✅ Confirmar venta", key="btn_vc"):
                for s, c in st.session_state.carrito_carro.items():
                    precio_final = st.session_state.precios_carro.get(s, PRODUCTOS[s])
                    sb_post("ventas", {
                        "fecha": fecha_hoy(), "hora": ahora(), "canal": "Carro",
                        "vendedor": "Javier & Edison", "sabor": s,
                        "cantidad": c, "total": precio_final * c,
                        "cliente": "", "factura_id": ""
                    })
                st.session_state.carrito_carro = {}
                st.session_state.precios_carro = {}
                st.session_state.ok_cargue = True
                get_metricas_globales.clear()
                time.sleep(0.3)
                st.rerun()

        if st.session_state.ok_cargue:
            st.markdown('<div class="success-toast">✅ Venta del carro registrada.</div>', unsafe_allow_html=True)
            st.session_state.ok_cargue = False

        # Solo admin ve ventas del carro
        if st.session_state.es_admin:
            raw_vcv = sb_get("ventas", f"select=hora,sabor,cantidad,total&fecha=eq.{fecha_hoy()}&canal=eq.Carro&order=hora.desc")
            if raw_vcv:
                st.markdown('<div class="section-label">Ventas del carro hoy</div>', unsafe_allow_html=True)
                df_vcv = pd.DataFrame(raw_vcv)
                df_vcv["total"] = df_vcv["total"].apply(fmt)
                df_vcv.columns = ["Hora","Sabor","Bolsas","Total $"]
                st.dataframe(df_vcv, use_container_width=True, hide_index=True)

    with sub3:
        st.markdown('<div class="section-label">Devolución al inventario 🔄</div>', unsafe_allow_html=True)
        st.caption("Registra las bolsas que regresan al inventario.")
        sabor_dev = st.selectbox("Sabor a devolver", SABORES_LISTA, key="sabor_dev")
        cant_dev  = st.number_input("Bolsas devueltas", min_value=1, max_value=500, value=1, step=1, key="cant_dev")
        fecha_dev = st.date_input("Fecha de devolución", value=datetime.now(COL_TZ).date(), key="fecha_dev")

        if st.button("🔄 Registrar devolución", key="btn_dev"):
            sb_post("devoluciones", {"fecha": str(fecha_dev), "sabor": sabor_dev, "cantidad": cant_dev})
            agregar_stock(sabor_dev, cant_dev)
            get_metricas_globales.clear()
            st.session_state.ok_dev = True
            time.sleep(0.3)
            st.rerun()

        if st.session_state.ok_dev:
            st.markdown('<div class="success-toast">✅ Devolución registrada. Stock actualizado.</div>', unsafe_allow_html=True)
            st.session_state.ok_dev = False

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
        st.caption("Toca cualquier celda para cambiar sabor, cantidad o precio.")

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
                "Precio":   st.column_config.NumberColumn("Precio", min_value=0, step=100),
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
        billete_f = st.number_input("Billete del cliente ($)", min_value=0, value=0,
                                    step=1000, key="billete_fab")
        if billete_f > 0:
            if billete_f >= total_fac:
                st.markdown(f'<div class="info-box">💰 Total: <b>{fmt(total_fac)}</b> · Devolver: <b>{fmt(billete_f - total_fac)}</b></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-low">⚠️ Total: {fmt(total_fac)} · Falta: {fmt(total_fac - billete_f)}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box">💰 Total a cobrar: <b>{fmt(total_fac)}</b></div>', unsafe_allow_html=True)

        if st.button("✅ Confirmar venta", key="btn_vf"):
            if not cliente_f.strip():
                st.markdown('<div class="alert-low">⚠️ Escribe el nombre del cliente.</div>', unsafe_allow_html=True)
            else:
                fid = str(uuid.uuid4())[:8].upper()
                for s, c in st.session_state.carrito.items():
                    precio_final = st.session_state.precios_carrito.get(s, PRODUCTOS[s])
                    sb_post("ventas", {
                        "fecha": fecha_hoy(), "hora": ahora(), "canal": "Fábrica",
                        "vendedor": vendedor_f, "sabor": s, "cantidad": c,
                        "total": precio_final * c, "cliente": cliente_f.strip(),
                        "factura_id": fid
                    })
                    restar_stock(s, c)
                st.session_state.factura_guardada = {
                    "id": fid, "cliente": cliente_f.strip(),
                    "vendedor": vendedor_f,
                    "items": dict(st.session_state.carrito),
                    "precios": dict(st.session_state.precios_carrito),
                    "total": total_fac,
                    "billete": billete_f
                }
                st.session_state.carrito = {}
                st.session_state.precios_carrito = {}
                get_metricas_globales.clear()
                time.sleep(0.3)
                st.rerun()

    # Mostrar factura confirmada
    if st.session_state.factura_guardada:
        fac = st.session_state.factura_guardada
        st.markdown(f"""
        <div class="factura-box">
            <div class="factura-header">🧾 Factura #{fac['id']} — {fac['cliente']}</div>
            <div style="font-size:0.78rem;color:rgba(255,255,255,0.4);margin-bottom:8px;">Vendedor: {fac['vendedor']} · {fecha_hoy()}</div>
        """, unsafe_allow_html=True)
        for s, c in fac["items"].items():
            precio = fac["precios"].get(s, PRODUCTOS[s])
            st.markdown(f'<div class="factura-row"><span>{s} × {c}</span><span>{fmt(precio*c)}</span></div>', unsafe_allow_html=True)
        vuelto = fac["billete"] - fac["total"] if fac["billete"] > 0 else 0
        st.markdown(f'<div class="factura-total"><span>TOTAL</span><span>{fmt(fac["total"])}</span></div>', unsafe_allow_html=True)
        if vuelto > 0:
            st.markdown(f'<div class="factura-cambio">💵 Devolver al cliente: <b>{fmt(vuelto)}</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Cambio de producto post-factura
        st.markdown('<div class="section-label">¿El cliente quiere cambiar algo?</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        sabor_out = col_a.selectbox("Devuelve", SABORES_LISTA, key="cambio_out")
        sabor_in  = col_b.selectbox("Lleva en cambio", SABORES_LISTA, key="cambio_in")
        cant_cambio = st.number_input("Cantidad", min_value=1, max_value=50, value=1, step=1, key="cant_cambio")

        if st.button("🔁 Registrar cambio", key="btn_cambio"):
            # Revertir el producto devuelto
            sb_post("ventas", {
                "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                "vendedor": fac["vendedor"], "sabor": sabor_out,
                "cantidad": -cant_cambio,
                "total": -(PRODUCTOS[sabor_out] * cant_cambio),
                "cliente": fac["cliente"], "factura_id": fac["id"]
            })
            agregar_stock(sabor_out, cant_cambio)
            # Registrar el nuevo producto
            sb_post("ventas", {
                "fecha": fecha_hoy(), "hora": ahora(), "canal": "Cambio",
                "vendedor": fac["vendedor"], "sabor": sabor_in,
                "cantidad": cant_cambio,
                "total": PRODUCTOS[sabor_in] * cant_cambio,
                "cliente": fac["cliente"], "factura_id": fac["id"]
            })
            restar_stock(sabor_in, cant_cambio)
            st.markdown(f'<div class="success-toast">✅ Cambio registrado: {cant_cambio} {sabor_out} → {cant_cambio} {sabor_in}</div>', unsafe_allow_html=True)
            time.sleep(0.3)
            st.rerun()

        if st.button("🧾 Nueva venta", key="btn_nueva"):
            st.session_state.factura_guardada = None
            st.rerun()

    # Solo admin ve historial
    if st.session_state.es_admin:
        raw_vf = sb_get("ventas", f"select=hora,cliente,vendedor,sabor,cantidad,total,factura_id&fecha=eq.{fecha_hoy()}&canal=eq.Fábrica&order=factura_id.asc,hora.asc")
        if raw_vf:
            st.markdown('<div class="section-label">Facturas de hoy</div>', unsafe_allow_html=True)
            df_vf = pd.DataFrame(raw_vf)
            facturas_ids = df_vf["factura_id"].unique()
            for fid in facturas_ids:
                grupo = df_vf[df_vf["factura_id"]==fid]
                cliente_n = grupo["cliente"].iloc[0]
                vendedor_n = grupo["vendedor"].iloc[0]
                hora_n = grupo["hora"].iloc[0]
                total_n = grupo["total"].sum()
                st.markdown(f"""
                <div class="factura-box">
                    <div class="factura-header">🧾 #{fid} — {cliente_n}</div>
                    <div style="font-size:0.78rem;color:rgba(255,255,255,0.4);margin-bottom:8px;">{vendedor_n} · {hora_n}</div>
                """, unsafe_allow_html=True)
                for _, row in grupo.iterrows():
                    st.markdown(f'<div class="factura-row"><span>{row["sabor"]} × {row["cantidad"]}</span><span>{fmt(row["total"])}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="factura-total"><span>TOTAL</span><span>{fmt(total_n)}</span></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: RESUMEN (solo admin)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "recibo":
    registros_recibo = st.session_state.get("recibo_canal_df", [])
    if registros_recibo:
        st.markdown(render_recibo(registros_recibo), unsafe_allow_html=True)
    else:
        st.info("No se encontró la factura seleccionada.")

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
                <div class="metric-box metric-pink"><div class="val">{fmt(total_fab)}</div><div class="lbl">Fábrica</div></div>
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
                <div class="metric-box metric-pink"><div class="val">{bolsas_r}</div><div class="lbl">Bolsas</div></div>
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
                st.markdown('<div class="section-label">Facturas del rango</div>', unsafe_allow_html=True)
                st.caption("Toca una fila para ver el recibo completo.")
                mostrar_facturas_seleccionables(df_fab_r, "rango")

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
                <div class="metric-box metric-pink"><div class="val">{bolsas_mes}</div><div class="lbl">Bolsas vendidas</div></div>
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
