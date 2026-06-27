import streamlit as st
import pandas as pd
import base64
import hashlib
import requests
import json
import time
from pathlib import Path
from datetime import date, datetime, timezone, timedelta

# Zona horaria Colombia (UTC-5)
COL_TZ = timezone(timedelta(hours=-5))
def fecha_hoy():
    return datetime.now(COL_TZ).strftime("%Y-%m-%d")
def ahora():
    return datetime.now(COL_TZ).strftime("%H:%M")

st.set_page_config(
    page_title="Productos La Delicia",
    page_icon="Logo.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# SUPABASE CONFIG
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
        if r.ok:
            return r.json()
        return []
    except:
        return []

def sb_post(tabla, data):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{tabla}", headers=HEADERS, json=data)
    return r.ok

def sb_patch(tabla, filtro, data):
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}", headers=HEADERS, json=data)
    return r.ok

def sb_delete(tabla, filtro):
    r = requests.delete(f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}", headers=HEADERS)
    return r.ok

# ══════════════════════════════════════════════════════════════════════════════
# DATOS MAESTROS
# ══════════════════════════════════════════════════════════════════════════════

PRODUCTOS = {
    "BBQ":                  9_000,
    "Limón":                9_000,
    "Carita Feliz":         9_000,
    "Pollo":                9_000,
    "Parrillada":           9_000,
    "Chorizo Limón":        9_000,
    "Mayonesa":             9_000,
    "Queso":                9_000,
    "Picante":              9_000,
    "Almuerzo Pollo":       9_000,
    "Almuerzo Limón":       9_000,
    "Almuerzo Picante":     9_000,
    "Mega":                 1_700,
    "Megaton":              5_000,
    "Fósforo 70g (x10)":   14_500,
    "Fósforo 140g":         3_500,
    "Fósforo 250g":         7_000,
    "Fósforo 500g":        14_000,
}

EMPLEADOS_PRODUCCION = ["Andrea", "Sofía", "Javier", "Edison", "Otro"]
VENDEDORES_FABRICA   = ["Sofía", "Andrea"]
VENDEDORES_CARRO     = "Javier & Edison"

def fmt(n):
    return f"${int(n):,.0f}".replace(",", ".")

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

def init_inventario():
    """Inserta productos si el inventario está vacío."""
    data = sb_get("inventario", "select=sabor")
    if not data:
        for sabor, precio in PRODUCTOS.items():
            sb_post("inventario", {"sabor": sabor, "stock": 0, "precio": precio})

def leer_inventario():
    data = sb_get("inventario", "select=*&order=sabor.asc")
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["sabor","stock","precio"])

def leer_produccion_hoy():
    hoy = fecha_hoy()
    data = sb_get("produccion", f"select=id,hora,empleado,sabor,cantidad&fecha=eq.{hoy}&order=hora.desc")
    return pd.DataFrame(data) if data else pd.DataFrame()

def leer_ventas_hoy():
    hoy = fecha_hoy()
    data = sb_get("ventas", f"select=*&fecha=eq.{hoy}&order=hora.desc")
    return pd.DataFrame(data) if data else pd.DataFrame()

def leer_cargue_activo():
    hoy = fecha_hoy()
    cargues = sb_get("cargues", f"select=sabor,cantidad&fecha=eq.{hoy}")
    ventas  = sb_get("ventas",  f"select=sabor,cantidad&fecha=eq.{hoy}&canal=eq.Carro")
    if not cargues:
        return pd.DataFrame(columns=["sabor","pendiente"])
    df_c = pd.DataFrame(cargues).groupby("sabor")["cantidad"].sum().reset_index()
    df_c.columns = ["sabor","cargado"]
    if ventas:
        df_v = pd.DataFrame(ventas).groupby("sabor")["cantidad"].sum().reset_index()
        df_v.columns = ["sabor","vendido"]
        df = df_c.merge(df_v, on="sabor", how="left").fillna(0)
    else:
        df = df_c.copy()
        df["vendido"] = 0
    df["pendiente"] = df["cargado"] - df["vendido"]
    return df[df["pendiente"] > 0][["sabor","pendiente"]]

def leer_ventas_rango(f_ini, f_fin):
    data = sb_get("ventas", f"select=*&fecha=gte.{f_ini}&fecha=lte.{f_fin}")
    return pd.DataFrame(data) if data else pd.DataFrame()

def agregar_stock(sabor, cantidad):
    inv = sb_get("inventario", f"select=stock&sabor=eq.{requests.utils.quote(sabor)}")
    if inv:
        nuevo = inv[0]["stock"] + cantidad
        sb_patch("inventario", f"sabor=eq.{requests.utils.quote(sabor)}", {"stock": nuevo})

def restar_stock(sabor, cantidad):
    inv = sb_get("inventario", f"select=stock&sabor=eq.{requests.utils.quote(sabor)}")
    if inv:
        nuevo = max(0, inv[0]["stock"] - cantidad)
        sb_patch("inventario", f"sabor=eq.{requests.utils.quote(sabor)}", {"stock": nuevo})

def set_stock(sabor, cantidad):
    sb_patch("inventario", f"sabor=eq.{requests.utils.quote(sabor)}", {"stock": cantidad})

def guardar_produccion(empleado, sabor, cantidad):
    sb_post("produccion", {
        "fecha": fecha_hoy(),
        "hora": ahora(),
        "empleado": empleado,
        "sabor": sabor,
        "cantidad": cantidad
    })
    agregar_stock(sabor, cantidad)

def guardar_cargue(sabor, cantidad):
    sb_post("cargues", {
        "fecha": fecha_hoy(),
        "hora": ahora(),
        "sabor": sabor,
        "cantidad": cantidad
    })
    restar_stock(sabor, cantidad)

def guardar_venta(canal, vendedor, sabor, cantidad):
    precio = PRODUCTOS[sabor]
    total  = precio * cantidad
    sb_post("ventas", {
        "fecha": fecha_hoy(),
        "hora": ahora(),
        "canal": canal,
        "vendedor": vendedor,
        "sabor": sabor,
        "cantidad": cantidad,
        "total": total
    })
    if canal == "Fábrica":
        restar_stock(sabor, cantidad)

def guardar_devolucion(sabor, cantidad):
    sb_post("devoluciones", {
        "fecha": fecha_hoy(),
        "sabor": sabor,
        "cantidad": cantidad
    })
    agregar_stock(sabor, cantidad)

def limpiar_datos_viejos():
    from datetime import timedelta
    limite = (datetime.now(COL_TZ) - timedelta(days=180)).strftime("%Y-%m-%d")
    sb_delete("produccion",   f"fecha=lt.{limite}")
    sb_delete("ventas",       f"fecha=lt.{limite}")
    sb_delete("cargues",      f"fecha=lt.{limite}")
    sb_delete("devoluciones", f"fecha=lt.{limite}")

# ══════════════════════════════════════════════════════════════════════════════
# LOGO
# ══════════════════════════════════════════════════════════════════════════════

def get_logo_b64():
    p = Path("Logo.png")
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else None

logo_b64 = get_logo_b64()
logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" style="height:90px;object-fit:contain;margin-bottom:6px;">'
    if logo_b64 else "🍟"
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS MODO OSCURO
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif !important;background-color:#1A0A12 !important;color:#F5E6EE !important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem;padding-bottom:3rem;max-width:500px;margin:0 auto;}
[data-baseweb="base-input"],[data-baseweb="base-input"] *,[data-baseweb="select"],[data-baseweb="select"]>div,[data-baseweb="select"]>div>div{background-color:#2A1020 !important;color:#F5E6EE !important;border-color:#4A1535 !important;}
[data-baseweb="base-input"] input,[data-baseweb="base-input"] textarea,input[type="number"],input[type="text"],input[type="date"]{background-color:#2A1020 !important;color:#F5E6EE !important;-webkit-text-fill-color:#F5E6EE !important;}
[data-testid="stNumberInputStepDown"],[data-testid="stNumberInputStepUp"]{background-color:#3D1528 !important;color:#F06292 !important;border:none !important;border-radius:7px !important;}
[data-testid="stNumberInputStepDown"]:hover,[data-testid="stNumberInputStepUp"]:hover{background-color:#D81B7A !important;color:white !important;}
[data-baseweb="select"]>div,[data-baseweb="base-input"]{border-radius:10px !important;border:1px solid #4A1535 !important;}
[data-baseweb="select"]>div:focus-within,[data-baseweb="base-input"]:focus-within{border-color:#D81B7A !important;box-shadow:0 0 0 3px rgba(216,27,122,0.18) !important;}
[data-baseweb="popover"],[data-baseweb="popover"] *,[data-baseweb="menu"],[data-baseweb="menu"] *,ul[data-testid="stSelectboxVirtualDropdown"],ul[data-testid="stSelectboxVirtualDropdown"] *{background-color:#2A1020 !important;color:#F5E6EE !important;}
[data-baseweb="menu"] li:hover,[role="option"]:hover,[aria-selected="true"][role="option"]{background-color:#3D1528 !important;color:#F06292 !important;}
[data-baseweb="calendar"],[data-baseweb="calendar"] *,[data-baseweb="datepicker"],[data-baseweb="datepicker"] *{background-color:#2A1020 !important;color:#F5E6EE !important;}
[data-baseweb="calendar"] button{color:#F5E6EE !important;background-color:transparent !important;}
[data-baseweb="calendar"] button:hover{background-color:#3D1528 !important;color:#F06292 !important;}
[data-baseweb="calendar"] [aria-selected="true"]{background-color:#D81B7A !important;color:white !important;}
[data-baseweb="calendar"] tbody tr:last-child td{background-color:#2A1020 !important;}
label,.stSelectbox label,.stNumberInput label,.stDateInput label{color:#F48FB1 !important;font-weight:500 !important;font-size:0.85rem !important;}
.stTabs [data-baseweb="tab-list"]{background:#2A1020;border-radius:12px;padding:4px;gap:2px;border:1px solid #4A1535;margin-bottom:16px;}
.stTabs [data-baseweb="tab"]{border-radius:10px;font-size:0.78rem;font-weight:600;padding:8px 4px;color:rgba(255,255,255,0.4) !important;flex:1;justify-content:center;background:transparent !important;}
.stTabs [aria-selected="true"]{background-color:#D81B7A !important;color:white !important;}
.brand-header{background:#1A0A12;border:1px solid #4A1535;border-radius:20px;padding:22px 20px 16px;margin-bottom:16px;text-align:center;}
.brand-header p{color:rgba(255,255,255,0.45);font-size:0.78rem;margin:0;}
.metric-row{display:flex;gap:9px;margin-bottom:16px;}
.metric-box{flex:1;background:#2A1020;border-radius:14px;padding:14px 8px;text-align:center;border:1px solid #4A1535;}
.metric-box .val{font-size:1.2rem;font-weight:700;line-height:1.1;}
.metric-box .lbl{font-size:0.65rem;color:rgba(255,255,255,0.4);margin-top:3px;}
.metric-pink .val{color:#F06292;}.metric-green .val{color:#4CAF8F;}.metric-red .val{color:#EF5350;}.metric-yellow .val{color:#FFB74D;}
.alert-low{background:rgba(239,83,80,0.12);border-left:3px solid #EF5350;border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:9px;font-size:0.83rem;color:#EF9A9A;}
.info-box{background:rgba(76,175,143,0.10);border:1px solid rgba(76,175,143,0.25);border-radius:12px;padding:12px 14px;margin:8px 0 14px;font-size:0.82rem;color:#80CBC4;}
.warn-box{background:rgba(255,183,77,0.10);border:1px solid rgba(255,183,77,0.25);border-radius:12px;padding:12px 14px;margin:8px 0 14px;font-size:0.82rem;color:#FFB74D;}
.success-toast{background:rgba(76,175,143,0.12);border:1px solid rgba(76,175,143,0.30);border-radius:12px;padding:14px 16px;text-align:center;font-weight:600;color:#80CBC4;font-size:0.95rem;margin-top:10px;}
.section-label{font-size:0.69rem;font-weight:700;text-transform:uppercase;letter-spacing:0.7px;color:#F06292;margin:16px 0 6px;}
.stButton>button{width:100%;background:#D81B7A !important;color:white !important;-webkit-text-fill-color:white !important;border:none !important;border-radius:12px !important;padding:14px !important;font-size:1rem !important;font-weight:700 !important;cursor:pointer;margin-top:4px;box-shadow:0 4px 20px rgba(216,27,122,0.35);}
.stButton>button:hover{opacity:0.88;}
[data-testid="stMetricLabel"] p{color:rgba(255,255,255,0.45) !important;}
[data-testid="stMetricValue"]{color:#F5E6EE !important;}
.stDataFrame{border-radius:12px;overflow:hidden;font-size:0.83rem;border:1px solid #4A1535 !important;}
[data-testid="stDataFrame"] *{background-color:#2A1020 !important;color:#F5E6EE !important;border-color:#4A1535 !important;}
.stCaption,small{color:rgba(255,255,255,0.4) !important;}
.stAlert{background:#2A1020 !important;color:#F5E6EE !important;border-color:#4A1535 !important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INICIALIZAR
# ══════════════════════════════════════════════════════════════════════════════

if "iniciado" not in st.session_state:
    init_inventario()
    st.session_state.iniciado = True

if "limpieza" not in st.session_state:
    limpiar_datos_viejos()
    st.session_state.limpieza = True

for k in ["ok_prod","ok_cargue","ok_venta_fab","ok_venta_carro","ok_dev","ok_stock","es_admin"]:
    if k not in st.session_state:
        st.session_state[k] = False

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════

ADMIN_USER = "jorge"
ADMIN_HASH = "096f6432e029084963ccb57b61a5b46dd3188f9d4fe73333d7be8289ffeb7057"

def check_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest() == ADMIN_HASH

# ══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO
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

# Métricas — consultas rápidas
_inv_data   = sb_get("inventario", "select=stock")
_prod_data  = sb_get("produccion", f"select=cantidad&fecha=eq.{fecha_hoy()}")
_venta_data = sb_get("ventas",     f"select=total&fecha=eq.{fecha_hoy()}")

total_bolsas_inv = sum(r["stock"] for r in _inv_data)      if _inv_data  else 0
total_prod_hoy   = sum(r["cantidad"] for r in _prod_data)  if _prod_data else 0
total_ventas_hoy = sum(r["total"] for r in _venta_data)    if _venta_data else 0

st.markdown(f"""
<div class="metric-row">
    <div class="metric-box metric-pink">
        <div class="val">{total_bolsas_inv}</div>
        <div class="lbl">En inventario</div>
    </div>
    <div class="metric-box metric-yellow">
        <div class="val">{total_prod_hoy}</div>
        <div class="lbl">Producidas hoy</div>
    </div>
    <div class="metric-box metric-green">
        <div class="val">{fmt(total_ventas_hoy)}</div>
        <div class="lbl">Ventas hoy</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PANEL
# ══════════════════════════════════════════════════════════════════════════════

if not st.session_state.es_admin:
    with st.expander("🔐 Acceso administrador", expanded=False):
        st.markdown('<div class="section-label">Solo para Jorge</div>', unsafe_allow_html=True)
        col_u, col_p = st.columns(2)
        u = col_u.text_input("Usuario", placeholder="jorge", key="lu", label_visibility="collapsed")
        p = col_p.text_input("Contraseña", type="password", placeholder="••••••••", key="lp", label_visibility="collapsed")
        if st.button("Entrar", key="btn_login"):
            if u.lower() == ADMIN_USER and check_password(p):
                st.session_state.es_admin = True
                st.rerun()
            else:
                st.markdown('<div class="alert-low">⚠️ Usuario o contraseña incorrectos.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="info-box">✅ Sesión activa — <b>Jorge (Administrador)</b></div>', unsafe_allow_html=True)
    if st.button("🔒 Cerrar sesión", key="btn_logout"):
        st.session_state.es_admin = False
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.es_admin:
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Producción", "🚗 Carro", "🏭 Fábrica", "📊 Resumen"])
else:
    tab1, tab2, tab3 = st.tabs(["📦 Producción", "🚗 Carro", "🏭 Fábrica"])
    tab4 = None

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 · PRODUCCIÓN
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-label">Registrar producción</div>', unsafe_allow_html=True)

    empleado   = st.selectbox("¿Quién registra?", EMPLEADOS_PRODUCCION, key="emp")
    sabor_p    = st.selectbox("Sabor producido", list(PRODUCTOS.keys()), key="sabor_p")
    cantidad_p = st.number_input("Bolsas producidas", min_value=1, max_value=5000, value=50, step=10, key="cant_p")

    _st = sb_get("inventario", f"select=stock&sabor=eq.{requests.utils.quote(sabor_p)}")
    stock_act = int(_st[0]["stock"]) if _st else 0
    st.markdown(f'<div class="info-box">📦 Stock actual de <b>{sabor_p}</b>: {stock_act} bolsas → quedará en <b>{stock_act + cantidad_p}</b></div>', unsafe_allow_html=True)

    if st.button("✅ Registrar producción", key="btn_prod"):
        guardar_produccion(empleado, sabor_p, cantidad_p)
        st.session_state.ok_prod = True
        st.rerun()

    if st.session_state.ok_prod:
        st.markdown('<div class="success-toast">✅ ¡Producción registrada!</div>', unsafe_allow_html=True)
        st.session_state.ok_prod = False

    # Leer datos frescos directamente desde Supabase
    raw_prod = sb_get("produccion", f"select=hora,empleado,sabor,cantidad&fecha=eq.{fecha_hoy()}&order=hora.desc")
    st.markdown('<div class="section-label">Producción de hoy</div>', unsafe_allow_html=True)
    st.caption(f"DEBUG fecha: {fecha_hoy()} — registros: {len(raw_prod) if raw_prod else 0}")
    if raw_prod:
        st.dataframe(pd.DataFrame(raw_prod), use_container_width=True, hide_index=True)
    else:
        st.caption(f"Sin datos — respuesta: {raw_prod}")

    raw_inv = sb_get("inventario", "select=sabor,stock,precio&order=sabor.asc")
    st.markdown('<div class="section-label">Inventario actual</div>', unsafe_allow_html=True)
    st.caption(f"DEBUG: {len(raw_inv) if raw_inv else 0} registros recibidos")
    if raw_inv:
        df_show = pd.DataFrame(raw_inv)
        df_show["precio"] = df_show["precio"].apply(fmt)
        df_show["estado"] = df_show["stock"].apply(lambda x: "🔴 Agotado" if x==0 else ("🟡 Poco" if x<10 else "🟢 OK"))
        df_show.columns = ["Sabor","Bolsas","Precio","Estado"]
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        st.caption(f"Sin datos — respuesta: {raw_inv}")

    st.markdown('<div class="section-label">Ajustar stock manualmente</div>', unsafe_allow_html=True)
    st.caption("Úsalo si necesitas corregir algún conteo.")
    sabor_adj = st.selectbox("Sabor a ajustar", list(PRODUCTOS.keys()), key="sabor_adj")
    _st_adj = sb_get("inventario", f"select=stock&sabor=eq.{requests.utils.quote(sabor_adj)}")
    stock_adj = int(_st_adj[0]["stock"]) if _st_adj else 0
    nuevo_stock = st.number_input("Stock real (bolsas)", min_value=0, value=stock_adj, step=1, key="nuevo_s")
    if st.button("💾 Guardar ajuste", key="btn_adj"):
        set_stock(sabor_adj, nuevo_stock)
        st.session_state.ok_stock = True
        time.sleep(1)
        st.rerun()
    if st.session_state.ok_stock:
        st.markdown('<div class="success-toast">✅ Stock ajustado.</div>', unsafe_allow_html=True)
        st.session_state.ok_stock = False

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 · CARRO
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    sub_c1, sub_c2, sub_c3 = st.tabs(["Nuevo cargue", "Registrar venta", "Devolución semanal"])

    with sub_c1:
        st.markdown('<div class="section-label">Cargue del carro 🚗</div>', unsafe_allow_html=True)
        st.caption("Registra lo que llevan Javier y Edison en este viaje.")
        sabor_cg = st.selectbox("Sabor", list(PRODUCTOS.keys()), key="sabor_cg")
        cant_cg  = st.number_input("Bolsas a cargar", min_value=1, max_value=500, value=10, step=5, key="cant_cg")
        _st2 = sb_get("inventario", f"select=stock&sabor=eq.{requests.utils.quote(sabor_cg)}")
        stock_disp = int(_st2[0]["stock"]) if _st2 else 0

        if stock_disp < cant_cg:
            st.markdown(f'<div class="alert-low">⚠️ Solo hay {stock_disp} bolsas de {sabor_cg}.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box">📦 Disponible: <b>{stock_disp}</b> · Quedarán: <b>{stock_disp - cant_cg}</b></div>', unsafe_allow_html=True)

        if st.button("🚗 Registrar cargue", key="btn_cg", disabled=(stock_disp < cant_cg)):
            guardar_cargue(sabor_cg, cant_cg)
            st.session_state.ok_cargue = True
            time.sleep(1)
            st.rerun()

        if st.session_state.ok_cargue:
            st.markdown('<div class="success-toast">✅ Cargue registrado. ¡Buen viaje!</div>', unsafe_allow_html=True)
            st.session_state.ok_cargue = False

        df_ca = leer_cargue_activo()
        if not df_ca.empty:
            st.markdown('<div class="section-label">Lo que lleva el carro ahora</div>', unsafe_allow_html=True)
            df_ca.columns = ["Sabor","Bolsas pendientes"]
            st.dataframe(df_ca, use_container_width=True, hide_index=True)

    with sub_c2:
        st.markdown('<div class="section-label">Venta del carro 💵</div>', unsafe_allow_html=True)
        sabor_vc = st.selectbox("Sabor vendido", list(PRODUCTOS.keys()), key="sabor_vc")
        cant_vc  = st.number_input("Bolsas vendidas", min_value=1, max_value=500, value=10, step=1, key="cant_vc")
        st.markdown(f'<div class="info-box">💰 Total: <b>{fmt(PRODUCTOS[sabor_vc] * cant_vc)}</b></div>', unsafe_allow_html=True)

        if st.button("💵 Registrar venta", key="btn_vc"):
            guardar_venta("Carro", VENDEDORES_CARRO, sabor_vc, cant_vc)
            st.session_state.ok_venta_carro = True
            time.sleep(1)
            st.rerun()

        if st.session_state.ok_venta_carro:
            st.markdown('<div class="success-toast">✅ Venta del carro registrada.</div>', unsafe_allow_html=True)
            st.session_state.ok_venta_carro = False

        df_vh = leer_ventas_hoy()
        if not df_vh.empty:
            df_vc = df_vh[df_vh["canal"]=="Carro"]
            if not df_vc.empty:
                st.markdown('<div class="section-label">Ventas del carro hoy</div>', unsafe_allow_html=True)
                vista_vc = df_vc[["hora","sabor","cantidad","total"]].copy()
                vista_vc["total"] = vista_vc["total"].apply(fmt)
                vista_vc.columns = ["Hora","Sabor","Bolsas","Total $"]
                st.dataframe(vista_vc, use_container_width=True, hide_index=True)

    with sub_c3:
        st.markdown('<div class="section-label">Devolución semanal 🔄</div>', unsafe_allow_html=True)
        st.markdown('<div class="warn-box">⚠️ Solo usar al final de la semana (viernes o sábado).</div>', unsafe_allow_html=True)
        sabor_dev = st.selectbox("Sabor a devolver", list(PRODUCTOS.keys()), key="sabor_dev")
        cant_dev  = st.number_input("Bolsas devueltas", min_value=1, max_value=500, value=1, step=1, key="cant_dev")

        if st.button("🔄 Registrar devolución", key="btn_dev"):
            guardar_devolucion(sabor_dev, cant_dev)
            st.session_state.ok_dev = True
            time.sleep(1)
            st.rerun()

        if st.session_state.ok_dev:
            st.markdown('<div class="success-toast">✅ Devolución registrada.</div>', unsafe_allow_html=True)
            st.session_state.ok_dev = False

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 · FÁBRICA
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-label">Venta en fábrica 🏭</div>', unsafe_allow_html=True)
    vendedor_f = st.selectbox("Vendedor", VENDEDORES_FABRICA, key="vend_f")
    sabor_vf   = st.selectbox("Sabor vendido", list(PRODUCTOS.keys()), key="sabor_vf")
    cant_vf    = st.number_input("Bolsas vendidas", min_value=1, max_value=500, value=1, step=1, key="cant_vf")
    _st3 = sb_get("inventario", f"select=stock&sabor=eq.{requests.utils.quote(sabor_vf)}")
    stock_vf = int(_st3[0]["stock"]) if _st3 else 0

    if stock_vf < cant_vf:
        st.markdown(f'<div class="alert-low">⚠️ Solo hay {stock_vf} bolsas de {sabor_vf}.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="info-box">💰 Total: <b>{fmt(PRODUCTOS[sabor_vf] * cant_vf)}</b> · Stock restante: <b>{stock_vf - cant_vf}</b></div>', unsafe_allow_html=True)

    if st.button("💵 Registrar venta fábrica", key="btn_vf", disabled=(stock_vf < cant_vf)):
        guardar_venta("Fábrica", vendedor_f, sabor_vf, cant_vf)
        st.session_state.ok_venta_fab = True
        time.sleep(1)
        st.rerun()

    if st.session_state.ok_venta_fab:
        st.markdown('<div class="success-toast">✅ Venta registrada.</div>', unsafe_allow_html=True)
        st.session_state.ok_venta_fab = False

    df_vh2 = leer_ventas_hoy()
    if not df_vh2.empty:
        df_vf = df_vh2[df_vh2["canal"]=="Fábrica"]
        if not df_vf.empty:
            st.markdown('<div class="section-label">Ventas fábrica hoy</div>', unsafe_allow_html=True)
            vista_vf = df_vf[["hora","vendedor","sabor","cantidad","total"]].copy()
            vista_vf["total"] = vista_vf["total"].apply(fmt)
            vista_vf.columns = ["Hora","Vendedor","Sabor","Bolsas","Total $"]
            st.dataframe(vista_vf, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 · RESUMEN (solo admin)
# ─────────────────────────────────────────────────────────────────────────────
if tab4 is not None:
    with tab4:
        sub_r1, sub_r2 = st.tabs(["Hoy", "Por fechas"])

        with sub_r1:
            st.markdown('<div class="section-label">Resumen del día</div>', unsafe_allow_html=True)
            df_vt = leer_ventas_hoy()
            if df_vt.empty:
                st.info("Aún no hay ventas registradas hoy.")
            else:
                total_fab   = int(df_vt[df_vt["canal"]=="Fábrica"]["total"].sum()) if "canal" in df_vt.columns else 0
                total_carro = int(df_vt[df_vt["canal"]=="Carro"]["total"].sum())   if "canal" in df_vt.columns else 0
                gran_total  = total_fab + total_carro

                st.markdown(f"""
                <div class="metric-row">
                    <div class="metric-box metric-pink"><div class="val">{fmt(total_fab)}</div><div class="lbl">Fábrica</div></div>
                    <div class="metric-box metric-yellow"><div class="val">{fmt(total_carro)}</div><div class="lbl">Carro</div></div>
                    <div class="metric-box metric-green"><div class="val">{fmt(gran_total)}</div><div class="lbl">Total día</div></div>
                </div>""", unsafe_allow_html=True)

                st.markdown('<div class="section-label">Por sabor</div>', unsafe_allow_html=True)
                por_sabor = df_vt.groupby("sabor").agg(bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
                por_sabor = por_sabor.sort_values("total", ascending=False)
                por_sabor["total"] = por_sabor["total"].apply(fmt)
                por_sabor.columns = ["Sabor","Bolsas","Total $"]
                st.dataframe(por_sabor, use_container_width=True, hide_index=True)

        with sub_r2:
            st.markdown('<div class="section-label">Consultar por fechas</div>', unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            f_ini = col_a.date_input("Desde", value=date(datetime.now(COL_TZ).year, datetime.now(COL_TZ).month, 1), key="f_ini")
            f_fin = col_b.date_input("Hasta", value=datetime.now(COL_TZ).date(), key="f_fin")
            df_rango = leer_ventas_rango(f_ini, f_fin)

            if df_rango.empty:
                st.info("No hay ventas en ese rango.")
            else:
                total_r  = int(df_rango["total"].sum())
                bolsas_r = int(df_rango["cantidad"].sum())
                dias_r   = df_rango["fecha"].nunique()

                st.markdown(f"""
                <div class="metric-row">
                    <div class="metric-box metric-green"><div class="val">{fmt(total_r)}</div><div class="lbl">Ingresos</div></div>
                    <div class="metric-box metric-pink"><div class="val">{bolsas_r}</div><div class="lbl">Bolsas</div></div>
                    <div class="metric-box metric-yellow"><div class="val">{dias_r}</div><div class="lbl">Días</div></div>
                </div>""", unsafe_allow_html=True)

                st.markdown('<div class="section-label">Por día</div>', unsafe_allow_html=True)
                por_dia = df_rango.groupby("fecha").agg(bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
                por_dia["total"] = por_dia["total"].apply(fmt)
                por_dia.columns  = ["Fecha","Bolsas","Total $"]
                st.dataframe(por_dia, use_container_width=True, hide_index=True)

                st.markdown('<div class="section-label">Por canal</div>', unsafe_allow_html=True)
                por_canal = df_rango.groupby("canal").agg(bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
                por_canal["total"] = por_canal["total"].apply(fmt)
                por_canal.columns  = ["Canal","Bolsas","Total $"]
                st.dataframe(por_canal, use_container_width=True, hide_index=True)
