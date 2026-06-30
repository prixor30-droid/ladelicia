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

def fmt(n):
    return f"${int(n):,.0f}".replace(",", ".")

# ══════════════════════════════════════════════════════════════════════════════
# DB HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def init_inventario():
    data = sb_get("inventario", "select=sabor")
    if not data:
        for sabor, precio in PRODUCTOS.items():
            sb_post("inventario", {"sabor": sabor, "stock": 0, "precio": precio})

def get_stock(sabor):
    q = requests.utils.quote(sabor)
    r = sb_get("inventario", f"select=stock&sabor=eq.{q}")
    return int(r[0]["stock"]) if r else 0

def agregar_stock(sabor, cantidad):
    q = requests.utils.quote(sabor)
    stock = get_stock(sabor)
    sb_patch("inventario", f"sabor=eq.{q}", {"stock": stock + cantidad})

def restar_stock(sabor, cantidad):
    q = requests.utils.quote(sabor)
    stock = get_stock(sabor)
    sb_patch("inventario", f"sabor=eq.{q}", {"stock": max(0, stock - cantidad)})

def set_stock(sabor, cantidad):
    q = requests.utils.quote(sabor)
    sb_patch("inventario", f"sabor=eq.{q}", {"stock": cantidad})

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
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif !important;background-color:#FFFFFF !important;color:#1A0A12 !important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem;padding-bottom:3rem;max-width:500px;margin:0 auto;}
@media (min-width: 768px){
  .block-container{max-width:680px;}
}
@media (min-width: 1100px){
  .block-container{max-width:760px;}
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
.stTabs [data-baseweb="tab-list"]{background:#FAF0F5;border-radius:12px;padding:4px;gap:2px;border:1px solid #E5C5D5;margin-bottom:16px;}
.stTabs [data-baseweb="tab"]{border-radius:10px;font-size:0.78rem;font-weight:600;padding:8px 4px;color:#7A2050 !important;flex:1;justify-content:center;background:transparent !important;}
.stTabs [aria-selected="true"]{background-color:#D81B7A !important;color:white !important;}
.brand-header{background:#FFFFFF;border:1.5px solid #E5C5D5;border-radius:20px;padding:22px 20px 16px;margin-bottom:16px;text-align:center;box-shadow:0 2px 12px rgba(216,27,122,0.08);}
.brand-header p{color:#9C4270;font-size:0.78rem;margin:0;}
.metric-row{display:flex;gap:9px;margin-bottom:16px;}
.metric-box{flex:1;background:#FAF0F5;border-radius:14px;padding:14px 8px;text-align:center;border:1px solid #E5C5D5;}
.metric-box .val{font-size:1.2rem;font-weight:700;line-height:1.1;}
.metric-box .lbl{font-size:0.65rem;color:#9C4270;margin-top:3px;}
.metric-pink .val{color:#D81B7A;}.metric-green .val{color:#1B9E5A;}.metric-red .val{color:#D32F2F;}.metric-yellow .val{color:#E68900;}
.alert-low{background:#FFEBEE;border-left:3px solid #D32F2F;border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:9px;font-size:0.83rem;color:#B71C1C;}
.info-box{background:#E8F5E9;border:1px solid #A5D6A7;border-radius:12px;padding:12px 14px;margin:8px 0 14px;font-size:0.82rem;color:#1B5E20;}
.warn-box{background:#FFF8E1;border:1px solid #FFD54F;border-radius:12px;padding:12px 14px;margin:8px 0 14px;font-size:0.82rem;color:#8D6E00;}
.success-toast{background:#E8F5E9;border:1px solid #A5D6A7;border-radius:12px;padding:14px 16px;text-align:center;font-weight:600;color:#1B5E20;font-size:0.95rem;margin-top:10px;}
.section-label{font-size:0.69rem;font-weight:700;text-transform:uppercase;letter-spacing:0.7px;color:#B0185F;margin:16px 0 6px;}
.stButton>button{width:100%;background:#D81B7A !important;color:white !important;-webkit-text-fill-color:white !important;border:none !important;border-radius:12px !important;padding:14px !important;font-size:1rem !important;font-weight:700 !important;cursor:pointer;margin-top:4px;box-shadow:0 4px 16px rgba(216,27,122,0.25);white-space:pre-line !important;line-height:1.4 !important;}
.stButton>button:hover{opacity:0.88;}
.menu-btn-wrap .stButton>button{min-height:84px !important;display:flex !important;flex-direction:column !important;justify-content:center !important;align-items:center !important;text-align:center !important;}
[data-testid="stMetricLabel"] p{color:#9C4270 !important;}
[data-testid="stMetricValue"]{color:#1A0A12 !important;}
.stDataFrame{border-radius:12px;overflow:hidden;font-size:0.83rem;border:1px solid #E5C5D5;}
.stCaption,small{color:#9C4270 !important;}
.stAlert{background:#FAF0F5 !important;color:#1A0A12 !important;border-color:#E5C5D5 !important;}
.factura-box{background:#FAF0F5;border:1px solid #E5C5D5;border-radius:14px;padding:16px;margin-bottom:14px;}
.factura-header{font-size:0.9rem;font-weight:700;color:#D81B7A;margin-bottom:8px;}
.factura-row{display:flex;justify-content:space-between;font-size:0.85rem;padding:4px 0;border-bottom:1px solid #E5C5D5;color:#1A0A12;}
.factura-total{display:flex;justify-content:space-between;font-size:1rem;font-weight:700;color:#1B9E5A;margin-top:8px;}
.factura-cambio{font-size:0.9rem;color:#E68900;margin-top:6px;text-align:center;}
.calc-box{background:#FAF0F5;border:1px solid #E5C5D5;border-radius:14px;padding:14px;margin-bottom:14px;}
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
bloquearTecladoSelects();
setInterval(bloquearTecladoSelects, 500);
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
ADMIN_USER = "jorge"
ADMIN_HASH = "096f6432e029084963ccb57b61a5b46dd3188f9d4fe73333d7be8289ffeb7057"

def check_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest() == ADMIN_HASH

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
_inv   = sb_get("inventario", "select=stock")
_prod  = sb_get("produccion", f"select=cantidad&fecha=eq.{fecha_hoy()}")
_venta = sb_get("ventas",     f"select=total&fecha=eq.{fecha_hoy()}")
total_inv  = sum(r["stock"]    for r in _inv)   if _inv   else 0
total_prod = sum(r["cantidad"] for r in _prod)  if _prod  else 0
total_vta  = sum(r["total"]    for r in _venta) if _venta else 0

st.markdown(f"""
<div class="metric-row">
    <div class="metric-box metric-pink"><div class="val">{total_inv}</div><div class="lbl">En inventario</div></div>
    <div class="metric-box metric-yellow"><div class="val">{total_prod}</div><div class="lbl">Producidas hoy</div></div>
    <div class="metric-box metric-green"><div class="val">{fmt(total_vta)}</div><div class="lbl">Ventas hoy</div></div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.es_admin:
    with st.expander("🔐 Acceso administrador", expanded=False):
        cu, cp = st.columns(2)
        u = cu.text_input("Usuario", placeholder="jorge", key="lu", label_visibility="collapsed")
        p = cp.text_input("Contraseña", type="password", placeholder="••••••••", key="lp", label_visibility="collapsed")
        if st.button("Entrar", key="btn_login"):
            if u.lower() == ADMIN_USER and check_pw(p):
                st.session_state.es_admin = True
                st.rerun()
            else:
                st.markdown('<div class="alert-low">⚠️ Usuario o contraseña incorrectos.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="info-box">✅ Sesión activa — <b>Jorge (Administrador)</b></div>', unsafe_allow_html=True)
    if st.button("🔒 Cerrar sesión", key="btn_logout"):
        st.session_state.es_admin = False
        st.session_state.vista = "menu"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# NAVEGACIÓN — botón atrás
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista != "menu":
    if st.button("← Volver al menú", key="btn_back"):
        st.session_state.vista = "menu"
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

    for vista, icon, titulo, sub in opciones:
        st.markdown('<div class="menu-btn-wrap">', unsafe_allow_html=True)
        if st.button(f"{icon}  {titulo}\n{sub}", key=f"btn_{vista}"):
            st.session_state.vista = vista
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: PRODUCCIÓN
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "produccion":
    st.markdown('<div class="section-label">Registrar producción</div>', unsafe_allow_html=True)

    empleado   = st.selectbox("¿Quién registra?", EMPLEADOS, key="emp")
    sabor_p    = st.selectbox("Sabor producido", SABORES_LISTA, key="sabor_p")
    cantidad_p = st.number_input("Bolsas producidas", min_value=1, max_value=5000, value=50, step=10, key="cant_p")

    stock_act = get_stock(sabor_p)
    st.markdown(f'<div class="info-box">📦 Stock actual de <b>{sabor_p}</b>: {stock_act} → quedará en <b>{stock_act + cantidad_p}</b></div>', unsafe_allow_html=True)

    if st.button("✅ Registrar producción", key="btn_prod"):
        sb_post("produccion", {
            "fecha": fecha_hoy(), "hora": ahora(),
            "empleado": empleado, "sabor": sabor_p, "cantidad": cantidad_p
        })
        agregar_stock(sabor_p, cantidad_p)
        st.session_state.ok_prod = True
        time.sleep(1)
        st.rerun()

    if st.session_state.ok_prod:
        st.markdown('<div class="success-toast">✅ ¡Producción registrada!</div>', unsafe_allow_html=True)
        st.session_state.ok_prod = False

    # Producción de hoy — tabla totalmente editable
    raw_prod = sb_get("produccion", f"select=id,fecha,hora,empleado,sabor,cantidad&fecha=eq.{fecha_hoy()}&order=hora.desc")
    if raw_prod:
        st.markdown('<div class="section-label">Producción de hoy</div>', unsafe_allow_html=True)
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
            time.sleep(1)
            st.rerun()

        # Eliminar fila seleccionada
        ids_prod = {f"{r['fecha']} {r['hora']} — {r['sabor']} ({r['cantidad']} bolsas)": r for r in raw_prod}
        sel_del = st.selectbox("Eliminar registro", ["— Selecciona —"] + list(ids_prod.keys()), key="sel_del_prod")
        if sel_del != "— Selecciona —" and col_e.button("🗑️ Eliminar", key="btn_del_prod"):
            reg_del = ids_prod[sel_del]
            sb_delete("produccion", f"id=eq.{reg_del['id']}")
            restar_stock(reg_del["sabor"], reg_del["cantidad"])
            time.sleep(1)
            st.rerun()

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
        time.sleep(1)
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
        sabor_cg = st.selectbox("Sabor", SABORES_LISTA, key="sabor_cg")
        cant_cg  = st.number_input("Bolsas a cargar", min_value=1, max_value=500, value=10, step=5, key="cant_cg")
        stock_cg = get_stock(sabor_cg)

        if stock_cg < cant_cg:
            st.markdown(f'<div class="alert-low">⚠️ Solo hay {stock_cg} bolsas de {sabor_cg}.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box">📦 Disponible: <b>{stock_cg}</b> · Quedarán: <b>{stock_cg - cant_cg}</b></div>', unsafe_allow_html=True)

        if st.button("🚗 Registrar cargue", key="btn_cg", disabled=(stock_cg < cant_cg)):
            sb_post("cargues", {"fecha": fecha_hoy(), "hora": ahora(), "sabor": sabor_cg, "cantidad": cant_cg})
            restar_stock(sabor_cg, cant_cg)
            st.session_state.ok_cargue = True
            time.sleep(1)
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

    with sub2:
        st.markdown('<div class="section-label">Venta del carro</div>', unsafe_allow_html=True)

        col_s, col_c = st.columns([2, 1])
        sabor_vc = col_s.selectbox("Sabor", SABORES_LISTA, key="sabor_vc")
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
                time.sleep(1)
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
            st.session_state.ok_dev = True
            time.sleep(1)
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
    sabor_vf = col_s.selectbox("Sabor", SABORES_LISTA, key="sabor_vf")
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
                time.sleep(1)
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
            time.sleep(1)
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
elif st.session_state.vista == "resumen" and st.session_state.es_admin:
    sub_r1, sub_r2, sub_r3 = st.tabs(["Hoy", "Por fechas", "💾 Exportar"])

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
            por_sabor["total"] = por_sabor["total"].apply(fmt)
            por_sabor.columns = ["Sabor","Bolsas","Total $"]
            st.dataframe(por_sabor, use_container_width=True, hide_index=True)

            st.markdown('<div class="section-label">Facturas fábrica</div>', unsafe_allow_html=True)
            df_fab = df_vt[df_vt["canal"]=="Fábrica"]
            if not df_fab.empty:
                for fid in df_fab["factura_id"].unique():
                    if not fid:
                        continue
                    grupo = df_fab[df_fab["factura_id"]==fid]
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

    with sub_r3:
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
