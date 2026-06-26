import streamlit as st
import pandas as pd
import sqlite3
import base64
import hashlib
from pathlib import Path
from datetime import date, datetime

st.set_page_config(
    page_title="Productos La Delicia",
    page_icon="Logo.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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
    return f"${n:,.0f}".replace(",", ".")

# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

DB = "delicia.db"

def conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    c = conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS inventario (
            sabor  TEXT PRIMARY KEY,
            stock  INTEGER NOT NULL DEFAULT 0,
            precio INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS produccion (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha    TEXT NOT NULL,
            hora     TEXT NOT NULL,
            empleado TEXT NOT NULL,
            sabor    TEXT NOT NULL,
            cantidad INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cargues (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha    TEXT NOT NULL,
            hora     TEXT NOT NULL,
            sabor    TEXT NOT NULL,
            cantidad INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ventas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha     TEXT NOT NULL,
            hora      TEXT NOT NULL,
            canal     TEXT NOT NULL,
            vendedor  TEXT NOT NULL,
            sabor     TEXT NOT NULL,
            cantidad  INTEGER NOT NULL,
            total     INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS devoluciones (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha    TEXT NOT NULL,
            sabor    TEXT NOT NULL,
            cantidad INTEGER NOT NULL
        );
    """)
    # Insertar productos si inventario está vacío
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM inventario")
    if cur.fetchone()[0] == 0:
        for sabor, precio in PRODUCTOS.items():
            cur.execute("INSERT INTO inventario VALUES (?,?,?)", (sabor, 0, precio))
    c.commit()
    c.close()

init_db()

# ── Helpers DB ───────────────────────────────────────────────────────────────

def leer_inventario():
    c = conn()
    df = pd.read_sql("SELECT * FROM inventario ORDER BY sabor", c)
    c.close()
    return df

def leer_produccion_hoy():
    c = conn()
    df = pd.read_sql(
        "SELECT * FROM produccion WHERE fecha=? ORDER BY hora DESC",
        c, params=(str(date.today()),))
    c.close()
    return df

def leer_ventas_hoy():
    c = conn()
    df = pd.read_sql(
        "SELECT * FROM ventas WHERE fecha=? ORDER BY hora DESC",
        c, params=(str(date.today()),))
    c.close()
    return df

def leer_cargue_activo():
    """Suma de cargues del día menos devoluciones de hoy — lo que lleva el carro ahora."""
    c = conn()
    df_c = pd.read_sql(
        "SELECT sabor, SUM(cantidad) as cargado FROM cargues WHERE fecha=? GROUP BY sabor",
        c, params=(str(date.today()),))
    df_v = pd.read_sql(
        "SELECT sabor, SUM(cantidad) as vendido FROM ventas WHERE fecha=? AND canal='Carro' GROUP BY sabor",
        c, params=(str(date.today()),))
    c.close()
    if df_c.empty:
        return pd.DataFrame(columns=["sabor","pendiente"])
    df = df_c.merge(df_v, on="sabor", how="left").fillna(0)
    df["pendiente"] = df["cargado"] - df["vendido"]
    return df[df["pendiente"] > 0][["sabor","pendiente"]]

def leer_ventas_rango(f_ini, f_fin):
    c = conn()
    df = pd.read_sql(
        "SELECT * FROM ventas WHERE fecha BETWEEN ? AND ?",
        c, params=(str(f_ini), str(f_fin)))
    c.close()
    return df

def agregar_stock(sabor, cantidad):
    c = conn()
    c.execute("UPDATE inventario SET stock=stock+? WHERE sabor=?", (cantidad, sabor))
    c.commit(); c.close()

def restar_stock(sabor, cantidad):
    c = conn()
    c.execute("UPDATE inventario SET stock=MAX(0,stock-?) WHERE sabor=?", (cantidad, sabor))
    c.commit(); c.close()

def set_stock(sabor, cantidad):
    c = conn()
    c.execute("UPDATE inventario SET stock=? WHERE sabor=?", (cantidad, sabor))
    c.commit(); c.close()

def guardar_produccion(empleado, sabor, cantidad):
    c = conn()
    c.execute("INSERT INTO produccion (fecha,hora,empleado,sabor,cantidad) VALUES (?,?,?,?,?)",
              (str(date.today()), datetime.now().strftime("%H:%M"), empleado, sabor, cantidad))
    c.commit(); c.close()
    agregar_stock(sabor, cantidad)

def guardar_cargue(sabor, cantidad):
    c = conn()
    c.execute("INSERT INTO cargues (fecha,hora,sabor,cantidad) VALUES (?,?,?,?)",
              (str(date.today()), datetime.now().strftime("%H:%M"), sabor, cantidad))
    c.commit(); c.close()
    restar_stock(sabor, cantidad)

def guardar_venta(canal, vendedor, sabor, cantidad):
    precio = PRODUCTOS[sabor]
    total  = precio * cantidad
    c = conn()
    c.execute("INSERT INTO ventas (fecha,hora,canal,vendedor,sabor,cantidad,total) VALUES (?,?,?,?,?,?,?)",
              (str(date.today()), datetime.now().strftime("%H:%M"), canal, vendedor, sabor, cantidad, total))
    c.commit(); c.close()
    if canal == "Fábrica":
        restar_stock(sabor, cantidad)

def guardar_devolucion(sabor, cantidad):
    c = conn()
    c.execute("INSERT INTO devoluciones (fecha,sabor,cantidad) VALUES (?,?,?)",
              (str(date.today()), sabor, cantidad))
    c.commit(); c.close()
    agregar_stock(sabor, cantidad)

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
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

for k in ["ok_prod","ok_cargue","ok_venta_fab","ok_venta_carro","ok_dev","ok_stock"]:
    if k not in st.session_state:
        st.session_state[k] = False

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
# MÉTRICAS RÁPIDAS
# ══════════════════════════════════════════════════════════════════════════════

df_inv      = leer_inventario()
df_ventas   = leer_ventas_hoy()
df_prod_hoy = leer_produccion_hoy()

total_bolsas_inv  = int(df_inv["stock"].sum())
total_prod_hoy    = int(df_prod_hoy["cantidad"].sum()) if not df_prod_hoy.empty else 0
total_ventas_hoy  = int(df_ventas["total"].sum())      if not df_ventas.empty  else 0
bolsas_vendidas   = int(df_ventas["cantidad"].sum())   if not df_ventas.empty  else 0

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
# TABS
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN ADMINISTRADOR
# ══════════════════════════════════════════════════════════════════════════════

ADMIN_USER = "jorge"
ADMIN_HASH = "096f6432e029084963ccb57b61a5b46dd3188f9d4fe73333d7be8289ffeb7057"  # ladelicia

def check_password(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_HASH

if "es_admin" not in st.session_state:
    st.session_state.es_admin = False

# Panel de login — solo visible si no ha iniciado sesión
if not st.session_state.es_admin:
    with st.expander("🔐 Acceso administrador", expanded=False):
        st.markdown('<div class="section-label">Solo para Jorge</div>', unsafe_allow_html=True)
        col_u, col_p = st.columns(2)
        usuario_input  = col_u.text_input("Usuario", placeholder="jorge", key="login_user", label_visibility="collapsed")
        password_input = col_p.text_input("Contraseña", type="password", placeholder="••••••••", key="login_pass", label_visibility="collapsed")
        if st.button("Entrar", key="btn_login"):
            if usuario_input.lower() == ADMIN_USER and check_password(password_input):
                st.session_state.es_admin = True
                st.rerun()
            else:
                st.markdown('<div class="alert-low">⚠️ Usuario o contraseña incorrectos.</div>', unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="info-box">✅ Sesión activa — <b>Jorge (Administrador)</b></div>',
        unsafe_allow_html=True)
    if st.button("🔒 Cerrar sesión", key="btn_logout"):
        st.session_state.es_admin = False
        st.rerun()

# Tabs según rol
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

    empleado  = st.selectbox("¿Quién registra?", EMPLEADOS_PRODUCCION, key="emp")
    sabor_p   = st.selectbox("Sabor producido", list(PRODUCTOS.keys()), key="sabor_p")
    cantidad_p = st.number_input("Bolsas producidas", min_value=1, max_value=5000, value=50, step=10, key="cant_p")

    stock_actual = int(df_inv[df_inv["sabor"]==sabor_p]["stock"].values[0])
    st.markdown(
        f'<div class="info-box">📦 Stock actual de <b>{sabor_p}</b>: {stock_actual} bolsas → '
        f'quedará en <b>{stock_actual + cantidad_p}</b> bolsas</div>',
        unsafe_allow_html=True)

    if st.button("✅ Registrar producción", key="btn_prod"):
        guardar_produccion(empleado, sabor_p, cantidad_p)
        st.session_state.ok_prod = True
        st.rerun()

    if st.session_state.ok_prod:
        st.markdown('<div class="success-toast">✅ ¡Producción registrada!</div>', unsafe_allow_html=True)
        st.session_state.ok_prod = False

    # Historial del día
    df_ph = leer_produccion_hoy()
    if not df_ph.empty:
        st.markdown('<div class="section-label">Producción de hoy</div>', unsafe_allow_html=True)
        vista = df_ph[["hora","empleado","sabor","cantidad"]].copy()
        vista.columns = ["Hora","Empleado","Sabor","Bolsas"]
        st.dataframe(vista, use_container_width=True, hide_index=True)
        st.markdown(f'<div class="info-box">Total producido hoy: <b>{int(df_ph["cantidad"].sum())} bolsas</b></div>',
                    unsafe_allow_html=True)

    # Inventario completo
    st.markdown('<div class="section-label">Inventario actual</div>', unsafe_allow_html=True)
    df_inv2 = leer_inventario()
    df_inv2["Precio"] = df_inv2["precio"].apply(fmt)
    df_inv2["Estado"] = df_inv2["stock"].apply(lambda x: "🔴 Agotado" if x == 0 else ("🟡 Poco" if x < 10 else "🟢 OK"))
    st.dataframe(
        df_inv2[["sabor","stock","Precio","Estado"]].rename(columns={"sabor":"Sabor","stock":"Bolsas"}),
        use_container_width=True, hide_index=True)

    # Ajuste manual de stock
    st.markdown('<div class="section-label">Ajustar stock manualmente</div>', unsafe_allow_html=True)
    st.caption("Úsalo si necesitas corregir algún conteo.")
    sabor_adj = st.selectbox("Sabor a ajustar", list(PRODUCTOS.keys()), key="sabor_adj")
    stock_adj_actual = int(df_inv2[df_inv2["sabor"]==sabor_adj]["stock"].values[0])
    nuevo_stock = st.number_input("Stock real (bolsas)", min_value=0, value=stock_adj_actual, step=1, key="nuevo_s")
    if st.button("💾 Guardar ajuste", key="btn_adj"):
        set_stock(sabor_adj, nuevo_stock)
        st.session_state.ok_stock = True
        st.rerun()
    if st.session_state.ok_stock:
        st.markdown('<div class="success-toast">✅ Stock ajustado.</div>', unsafe_allow_html=True)
        st.session_state.ok_stock = False

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 · CARRO (Javier & Edison)
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    sub_c1, sub_c2, sub_c3 = st.tabs(["Nuevo cargue", "Registrar venta", "Devolución semanal"])

    # ── CARGUE ───────────────────────────────────────────────────────────────
    with sub_c1:
        st.markdown('<div class="section-label">Cargue del carro 🚗</div>', unsafe_allow_html=True)
        st.caption("Registra lo que llevan Javier y Edison en este viaje.")

        sabor_cg  = st.selectbox("Sabor", list(PRODUCTOS.keys()), key="sabor_cg")
        cant_cg   = st.number_input("Bolsas a cargar", min_value=1, max_value=500, value=10, step=5, key="cant_cg")

        stock_disp = int(leer_inventario()[leer_inventario()["sabor"]==sabor_cg]["stock"].values[0])

        if stock_disp < cant_cg:
            st.markdown(f'<div class="alert-low">⚠️ Solo hay {stock_disp} bolsas de {sabor_cg} en inventario.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="info-box">📦 Disponible: <b>{stock_disp}</b> bolsas · '
                        f'Quedarán: <b>{stock_disp - cant_cg}</b></div>', unsafe_allow_html=True)

        if st.button("🚗 Registrar cargue", key="btn_cg", disabled=(stock_disp < cant_cg)):
            guardar_cargue(sabor_cg, cant_cg)
            st.session_state.ok_cargue = True
            st.rerun()

        if st.session_state.ok_cargue:
            st.markdown('<div class="success-toast">✅ Cargue registrado. ¡Buen viaje!</div>', unsafe_allow_html=True)
            st.session_state.ok_cargue = False

        # Cargue activo
        df_ca = leer_cargue_activo()
        if not df_ca.empty:
            st.markdown('<div class="section-label">Lo que lleva el carro ahora</div>', unsafe_allow_html=True)
            df_ca.columns = ["Sabor","Bolsas pendientes"]
            st.dataframe(df_ca, use_container_width=True, hide_index=True)

    # ── VENTA CARRO ───────────────────────────────────────────────────────────
    with sub_c2:
        st.markdown('<div class="section-label">Venta del carro 💵</div>', unsafe_allow_html=True)
        st.caption("Registra lo que vendieron Javier y Edison al regresar.")

        sabor_vc  = st.selectbox("Sabor vendido", list(PRODUCTOS.keys()), key="sabor_vc")
        cant_vc   = st.number_input("Bolsas vendidas", min_value=1, max_value=500, value=10, step=1, key="cant_vc")
        precio_vc = PRODUCTOS[sabor_vc]

        st.markdown(f'<div class="info-box">💰 Total: <b>{fmt(precio_vc * cant_vc)}</b> '
                    f'({cant_vc} × {fmt(precio_vc)})</div>', unsafe_allow_html=True)

        if st.button("💵 Registrar venta", key="btn_vc"):
            guardar_venta("Carro", VENDEDORES_CARRO, sabor_vc, cant_vc)
            st.session_state.ok_venta_carro = True
            st.rerun()

        if st.session_state.ok_venta_carro:
            st.markdown('<div class="success-toast">✅ Venta del carro registrada.</div>', unsafe_allow_html=True)
            st.session_state.ok_venta_carro = False

        # Ventas del carro hoy
        df_vh = leer_ventas_hoy()
        df_vc = df_vh[df_vh["canal"]=="Carro"] if not df_vh.empty else pd.DataFrame()
        if not df_vc.empty:
            st.markdown('<div class="section-label">Ventas del carro hoy</div>', unsafe_allow_html=True)
            vista_vc = df_vc[["hora","sabor","cantidad","total"]].copy()
            vista_vc["total"] = vista_vc["total"].apply(fmt)
            vista_vc.columns = ["Hora","Sabor","Bolsas","Total $"]
            st.dataframe(vista_vc, use_container_width=True, hide_index=True)
            st.markdown(f'<div class="info-box">Total ventas carro hoy: <b>{fmt(df_vc["total"].sum())}</b></div>',
                        unsafe_allow_html=True)

    # ── DEVOLUCIÓN SEMANAL ────────────────────────────────────────────────────
    with sub_c3:
        st.markdown('<div class="section-label">Devolución semanal 🔄</div>', unsafe_allow_html=True)
        st.caption("Registra las bolsas que devuelven Javier y Edison al inventario.")

        st.markdown('<div class="warn-box">⚠️ Solo usar al final de la semana (viernes o sábado).</div>',
                    unsafe_allow_html=True)

        sabor_dev = st.selectbox("Sabor a devolver", list(PRODUCTOS.keys()), key="sabor_dev")
        cant_dev  = st.number_input("Bolsas devueltas", min_value=1, max_value=500, value=1, step=1, key="cant_dev")

        if st.button("🔄 Registrar devolución", key="btn_dev"):
            guardar_devolucion(sabor_dev, cant_dev)
            st.session_state.ok_dev = True
            st.rerun()

        if st.session_state.ok_dev:
            st.markdown('<div class="success-toast">✅ Devolución registrada. Stock actualizado.</div>',
                        unsafe_allow_html=True)
            st.session_state.ok_dev = False

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 · FÁBRICA (Sofía & Andrea)
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-label">Venta en fábrica 🏭</div>', unsafe_allow_html=True)

    vendedor_f = st.selectbox("Vendedor", VENDEDORES_FABRICA, key="vend_f")
    sabor_vf   = st.selectbox("Sabor vendido", list(PRODUCTOS.keys()), key="sabor_vf")
    cant_vf    = st.number_input("Bolsas vendidas", min_value=1, max_value=500, value=1, step=1, key="cant_vf")
    precio_vf  = PRODUCTOS[sabor_vf]
    stock_vf   = int(leer_inventario()[leer_inventario()["sabor"]==sabor_vf]["stock"].values[0])

    if stock_vf < cant_vf:
        st.markdown(f'<div class="alert-low">⚠️ Solo hay {stock_vf} bolsas de {sabor_vf}.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="info-box">💰 Total: <b>{fmt(precio_vf * cant_vf)}</b> · '
                    f'Stock restante: <b>{stock_vf - cant_vf}</b> bolsas</div>', unsafe_allow_html=True)

    if st.button("💵 Registrar venta fábrica", key="btn_vf", disabled=(stock_vf < cant_vf)):
        guardar_venta("Fábrica", vendedor_f, sabor_vf, cant_vf)
        st.session_state.ok_venta_fab = True
        st.rerun()

    if st.session_state.ok_venta_fab:
        st.markdown('<div class="success-toast">✅ Venta registrada.</div>', unsafe_allow_html=True)
        st.session_state.ok_venta_fab = False

    # Ventas fábrica hoy
    df_vh2 = leer_ventas_hoy()
    df_vf  = df_vh2[df_vh2["canal"]=="Fábrica"] if not df_vh2.empty else pd.DataFrame()
    if not df_vf.empty:
        st.markdown('<div class="section-label">Ventas fábrica hoy</div>', unsafe_allow_html=True)
        vista_vf = df_vf[["hora","vendedor","sabor","cantidad","total"]].copy()
        vista_vf["total"] = vista_vf["total"].apply(fmt)
        vista_vf.columns = ["Hora","Vendedor","Sabor","Bolsas","Total $"]
        st.dataframe(vista_vf, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        col1.metric("Total fábrica hoy", fmt(df_vf["total"].sum()))
        col2.metric("Bolsas vendidas",   int(df_vf["cantidad"].sum()))

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 · RESUMEN (solo administrador)
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
                total_fab   = int(df_vt[df_vt["canal"]=="Fábrica"]["total"].sum()) if not df_vt[df_vt["canal"]=="Fábrica"].empty else 0
                total_carro = int(df_vt[df_vt["canal"]=="Carro"]["total"].sum())   if not df_vt[df_vt["canal"]=="Carro"].empty  else 0
                gran_total  = total_fab + total_carro

                st.markdown(f"""
                <div class="metric-row">
                    <div class="metric-box metric-pink">
                        <div class="val">{fmt(total_fab)}</div>
                        <div class="lbl">Fábrica</div>
                    </div>
                    <div class="metric-box metric-yellow">
                        <div class="val">{fmt(total_carro)}</div>
                        <div class="lbl">Carro</div>
                    </div>
                    <div class="metric-box metric-green">
                        <div class="val">{fmt(gran_total)}</div>
                        <div class="lbl">Total día</div>
                    </div>
                </div>""", unsafe_allow_html=True)

                st.markdown('<div class="section-label">Ventas por sabor hoy</div>', unsafe_allow_html=True)
                por_sabor = df_vt.groupby("sabor").agg(
                    bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
                por_sabor = por_sabor.sort_values("total", ascending=False)
                por_sabor["total"] = por_sabor["total"].apply(fmt)
                por_sabor.columns = ["Sabor","Bolsas","Total $"]
                st.dataframe(por_sabor, use_container_width=True, hide_index=True)

        with sub_r2:
            st.markdown('<div class="section-label">Consultar por fechas</div>', unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            f_ini = col_a.date_input("Desde", value=date.today().replace(day=1), key="f_ini")
            f_fin = col_b.date_input("Hasta", value=date.today(), key="f_fin")

            df_rango = leer_ventas_rango(f_ini, f_fin)

            if df_rango.empty:
                st.info("No hay ventas en ese rango.")
            else:
                total_r     = int(df_rango["total"].sum())
                bolsas_r    = int(df_rango["cantidad"].sum())
                dias_r      = df_rango["fecha"].nunique()

                st.markdown(f"""
                <div class="metric-row">
                    <div class="metric-box metric-green">
                        <div class="val">{fmt(total_r)}</div>
                        <div class="lbl">Ingresos</div>
                    </div>
                    <div class="metric-box metric-pink">
                        <div class="val">{bolsas_r}</div>
                        <div class="lbl">Bolsas vendidas</div>
                    </div>
                    <div class="metric-box metric-yellow">
                        <div class="val">{dias_r}</div>
                        <div class="lbl">Días</div>
                    </div>
                </div>""", unsafe_allow_html=True)

                st.markdown('<div class="section-label">Por día</div>', unsafe_allow_html=True)
                por_dia = df_rango.groupby("fecha").agg(
                    bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
                por_dia["total"] = por_dia["total"].apply(fmt)
                por_dia.columns  = ["Fecha","Bolsas","Total $"]
                st.dataframe(por_dia, use_container_width=True, hide_index=True)

                st.markdown('<div class="section-label">Por canal</div>', unsafe_allow_html=True)
                por_canal = df_rango.groupby("canal").agg(
                    bolsas=("cantidad","sum"), total=("total","sum")).reset_index()
                por_canal["total"] = por_canal["total"].apply(fmt)
                por_canal.columns  = ["Canal","Bolsas","Total $"]
                st.dataframe(por_canal, use_container_width=True, hide_index=True)