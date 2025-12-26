import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="TIPPYTEA | Dashboard Multisede", page_icon="🍃", layout="wide")

# Estilo TIPPYTEA Profesional
st.markdown("""
    <style>
    .stApp { background-color: #fcfdfc; }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.1);
        border-left: 5px solid #2e7d32;
    }
    h1 { color: #1b5e20; font-family: 'Helvetica Neue', sans-serif; }
    </style>
    """, unsafe_allow_html=True)


# --- 2. CARGA Y LIMPIEZA DE DATOS ---
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
            # Leer con punto y coma
            df = pd.read_csv(path, sep=';')

            # Limpiar nombres de columnas (quitar espacios al final como 'Costo ')
            df.columns = df.columns.str.strip()

            # Convertir Saldo y Costo a números (manejar comas decimales)
            for col in ['Saldo', 'Costo']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            df['Sede'] = sede
            df['Valor_Total'] = df['Saldo'] * df['Costo']
            all_data.append(df)
        except Exception as e:
            st.error(f"Error cargando {sede}: {e}")

    return pd.concat(all_data, ignore_index=True) if all_data else None


# --- 3. LÓGICA DEL DASHBOARD ---
df = load_data()

if df is not None:
    st.title("🍃 TIPPYTEA - Gestión de Inventario Multisede")
    st.markdown(f"Consolidado de inventarios actualizado a Noviembre 2025")

    # --- SIDEBAR ---
    st.sidebar.header("📍 Filtros de Red")
    sedes_sel = st.sidebar.multiselect("Seleccionar Sedes:", ["Paseo", "Jardin", "Planta"],
                                       default=["Paseo", "Jardin", "Planta"])
    busqueda = st.sidebar.text_input("🔍 Buscar insumo (ej: Matcha):")

    # Filtrado
    df_filtered = df[df['Sede'].isin(sedes_sel)]
    if busqueda:
        df_filtered = df_filtered[df_filtered['nombre'].str.contains(busqueda, case=False, na=False)]

    # --- MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    inv_total = df_filtered['Valor_Total'].sum()
    stock_total = df_filtered['Saldo'].sum()
    sin_stock = len(df_filtered[df_filtered['Saldo'] == 0])

    m1.metric("Inversión Total", f"${inv_total:,.2f}")
    m2.metric("Items Totales", len(df_filtered))
    m3.metric("Existencias (Unid/Gramos)", f"{stock_total:,.0f}")
    m4.metric("Productos en Cero", sin_stock, delta=f"{sin_stock}", delta_color="inverse")

    st.divider()

    # --- GRÁFICOS ---
    c1, c2 = st.columns([1, 1])

    with c1:
        st.subheader("💰 Inversión por Sede")
        fig_sede = px.bar(df_filtered.groupby('Sede')['Valor_Total'].sum().reset_index(),
                          x='Sede', y='Valor_Total', color='Sede',
                          color_discrete_map={"Paseo": "#81c784", "Jardin": "#4caf50", "Planta": "#1b5e20"})
        st.plotly_chart(fig_sede, use_container_width=True)

    with c2:
        st.subheader("⚠️ Alerta de Stock Bajo (Menos de 10)")
        stock_bajo = df_filtered[(df_filtered['Saldo'] > 0) & (df_filtered['Saldo'] < 10)].sort_values('Saldo')
        if not stock_bajo.empty:
            fig_bajo = px.bar(stock_bajo.head(10), x='Saldo', y='nombre', color='Sede', orientation='h',
                              title="Top 10 productos por agotarse")
            st.plotly_chart(fig_bajo, use_container_width=True)
        else:
            st.write("No hay productos con stock crítico (1-10 unidades).")

    # --- TABLA MAESTRA ---
    st.subheader("📋 Detalle General de Existencias")
    st.dataframe(
        df_filtered[['Sede', 'Codigo', 'nombre', 'unidad', 'Saldo', 'Costo', 'Valor_Total']],
        use_container_width=True,
        hide_index=True
    )