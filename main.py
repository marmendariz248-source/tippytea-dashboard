import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURACIÓN DE PÁGINA (Debe ser lo primero) ---
st.set_page_config(
    page_title="TIPPYTEA | Gestión de Inventario",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 2. SISTEMA DE SEGURIDAD (Contraseña) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.markdown("""
        <style>
        .stApp { background-color: #fcfdfc; }
        h1 { color: #1b5e20; font-family: sans-serif; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🔒 Acceso Restringido - TIPPYTEA")
    password = st.text_input("Ingresa la clave de acceso:", type="password")

    if st.button("Entrar"):
        if password == "Tippytea2025":  # <--- PUEDES CAMBIAR TU CLAVE AQUÍ
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Clave incorrecta")
    return False


if not check_password():
    st.stop()

# --- 3. ESTILOS REFORZADOS (Para PC y Celular) ---
st.markdown("""
    <style>
    /* Forzar colores claros y visibilidad */
    .stApp {
        background-color: #fcfdfc !important;
    }
    /* Forzar color de texto para evitar que el modo oscuro del celular lo oculte */
    h1, h2, h3, p, span, label, .stMetric div {
        color: #1b5e20 !important;
    }
    /* Tarjetas de métricas profesionales */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.1);
        border-left: 5px solid #2e7d32;
    }
    /* Sidebar personalizado */
    section[data-testid="stSidebar"] {
        background-color: #e8f5e9;
    }
    </style>
    """, unsafe_allow_html=True)


# --- 4. CARGA DE DATOS ---
@st.cache_data
def load_data():
    files = {
        "Paseo": "Copia de Toma de Inventarios Tippytea Original Noviembre Paseo.csv",
        "Jardin": "Copia de Toma de Inventarios Tippytea Original Noviembre Jardin (1).csv",
        "Planta": "Copia de Toma de Inventarios Tippytea Original Planta Noviembre 2025 (1).csv"
    }

    all_data = []
    for sede, path in files.items():
        try:
            # Leer con punto y coma (delimitador de tus archivos)
            df = pd.read_csv(path, sep=';')
            df.columns = df.columns.str.strip()  # Limpiar espacios en nombres de columnas

            # Limpieza de números (Cambiar comas por puntos en Costo y Saldo)
            for col in ['Costo', 'Saldo']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            df['Sede'] = sede
            df['Valor_Total'] = df['Saldo'] * df['Costo']
            all_data.append(df)
        except Exception as e:
            st.error(f"Error cargando la sede {sede}: {e}")

    return pd.concat(all_data, ignore_index=True) if all_data else None


# --- 5. EJECUCIÓN DEL DASHBOARD ---
df = load_data()

if df is not None:
    st.title("🍃 TIPPYTEA - Panel Multisede")
    st.markdown("Consolidado de inventarios actualizado")
    st.divider()

    # --- FILTROS SIDEBAR ---
    st.sidebar.header("📍 Control de Sedes")
    sedes_sel = st.sidebar.multiselect("Ver Sedes:", ["Paseo", "Jardin", "Planta"],
                                       default=["Paseo", "Jardin", "Planta"])
    buscar = st.sidebar.text_input("🔍 Buscar Insumo:")

    # Filtrado
    df_filtrado = df[df['Sede'].isin(sedes_sel)]
    if buscar:
        df_filtrado = df_filtrado[df_filtrado['nombre'].str.contains(buscar, case=False, na=False)]

    # --- MÉTRICAS (KPIs) ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Inversión Total", f"${df_filtrado['Valor_Total'].sum():,.2f}")
    c2.metric("Unidades Totales", f"{df_filtrado['Saldo'].sum():,.0f}")
    c3.metric("Items Agotados", len(df_filtrado[df_filtrado['Saldo'] == 0]))

    st.divider()

    # --- GRÁFICOS ---
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("💰 Inversión por Sede")
        resumen_sede = df_filtrado.groupby('Sede')['Valor_Total'].sum().reset_index()
        fig_sede = px.bar(resumen_sede, x='Sede', y='Valor_Total', color='Sede',
                          color_discrete_map={"Paseo": "#81c784", "Jardin": "#4caf50", "Planta": "#1b5e20"})
        st.plotly_chart(fig_sede, use_container_width=True)

    with col_graf2:
        st.subheader("⚠️ Stock Bajo (1-10 unidades)")
        bajo_stock = df_filtrado[(df_filtrado['Saldo'] > 0) & (df_filtrado['Saldo'] <= 10)]
        if not bajo_stock.empty:
            fig_bajo = px.bar(bajo_stock.head(15), x='Saldo', y='nombre', color='Sede', orientation='h')
            st.plotly_chart(fig_bajo, use_container_width=True)
        else:
            st.write("No hay stock crítico.")

    # --- TABLA DETALLADA ---
    st.subheader("📋 Lista de Existencias")
    st.dataframe(
        df_filtrado[['Sede', 'Codigo', 'nombre', 'Saldo', 'Costo', 'Valor_Total']].sort_values('Valor_Total',
                                                                                               ascending=False),
        use_container_width=True,
        hide_index=True
    )