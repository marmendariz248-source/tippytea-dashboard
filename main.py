import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="TIPPYTEA | Inventory BI", page_icon="🍃", layout="wide")

# Estilo UX mejorado
st.markdown("""
    <style>
    .main { background-color: #f1f3f1; }
    .stMetric { 
        background-color: #ffffff; border-radius: 15px; 
        padding: 20px; box-shadow: 0 4px 12px rgba(27, 94, 32, 0.08);
        border: 1px solid #e1e8e1;
    }
    h1, h2, h3 { color: #1b5e20 !important; font-family: 'Helvetica Neue', sans-serif; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { color: #2e7d32 !important; border-bottom: 3px solid #2e7d32 !important; }
    </style>
    """, unsafe_allow_html=True)


# --- 2. SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🍃</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Acceso Ejecutivo Tippytea</h2>", unsafe_allow_html=True)
        pwd = st.text_input("Ingrese la clave:", type="password")
        if st.button("Ingresar"):
            if pwd == "Tippytea2025":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Credencial incorrecta")
    return False


if not check_password(): st.stop()


# --- 3. CARGA DE DATOS ---
@st.cache_data
def load_data():
    files = [
        {"Mes": "Octubre", "Sede": "Paseo", "Path": "TOMA DE INVENTARIO OCTUBRE PASEO.csv"},
        {"Mes": "Octubre", "Sede": "Jardin", "Path": "TOMA INVENTARIO OCTUBRE JARDIN.csv"},
        {"Mes": "Octubre", "Sede": "Planta", "Path": "TOMA DE INVENTARIO OCTUBRE PLANTA.csv"},
        {"Mes": "Noviembre", "Sede": "Paseo",
         "Path": "Copia de Toma de Inventarios Tippytea Original Noviembre Paseo.csv"},
        {"Mes": "Noviembre", "Sede": "Jardin",
         "Path": "Copia de Toma de Inventarios Tippytea Original Noviembre Jardin (1).csv"},
        {"Mes": "Noviembre", "Sede": "Planta",
         "Path": "Copia de Toma de Inventarios Tippytea Original Planta Noviembre 2025 (1).csv"}
    ]
    all_data = []
    for f in files:
        try:
            df = pd.read_csv(f['Path'], sep=';')
            df.columns = df.columns.str.strip()
            col_costo = next((c for c in df.columns if 'Costo' in c), 'Costo')
            for c in ['Saldo', col_costo]:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.').str.strip(), errors='coerce').fillna(0)
            df['Mes'], df['Sede'] = f['Mes'], f['Sede']
            df['Valor_Total'] = df['Saldo'] * df[col_costo]
            all_data.append(df[['Codigo', 'nombre', 'Saldo', col_costo, 'Valor_Total', 'Mes', 'Sede']])
        except:
            continue
    return pd.concat(all_data, ignore_index=True) if all_data else None


full_df = load_data()

# --- 4. INTERFAZ ---
if full_df is not None:
    # Encabezado con Hoja
    st.markdown("<h1 style='text-align: center;'>🍃 INVENTARIOS TIPPYTEA 🍃</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>Sistema de Auditoría y Control de Activos</p>",
                unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown("### 🔍 Buscador Global")
    search = st.sidebar.text_input("Nombre o Código:", placeholder="Ej: Matcha...")
    mes_sel = st.sidebar.multiselect("Periodos:", full_df['Mes'].unique(), default=["Noviembre"])
    sede_sel = st.sidebar.multiselect("Sedes:", full_df['Sede'].unique(), default=full_df['Sede'].unique())

    # Filtros
    df_f = full_df[(full_df['Mes'].isin(mes_sel)) & (full_df['Sede'].isin(sede_sel))]
    if search:
        df_f = df_f[df_f['nombre'].str.contains(search, case=False) | df_f['Codigo'].str.contains(search)]

    # Tabs de Análisis
    tab1, tab2, tab3 = st.tabs(["📋 Resumen Ejecutivo", "📈 Existencias", "🕵️ Auditoría de Inventario"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        v_total = df_f['Valor_Total'].sum()
        c1.metric("Inversión Total", f"${v_total:,.2f}")
        c2.metric("Items en Stock", f"{len(df_f[df_f['Saldo'] > 0])}")
        c3.metric("Sede Líder", df_f.groupby('Sede')['Valor_Total'].sum().idxmax())

        st.divider()
        st.subheader("Distribución Patrimonial por Sede")
        fig_pie = px.pie(df_f, values='Valor_Total', names='Sede', hole=0.4,
                         color_discrete_sequence=px.colors.sequential.Greens_r)
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.subheader("Análisis de Stock Crítico vs Mayoritario")
        ver = st.radio("Mostrar Top 15:", ["Mayor Stock", "Stock Crítico", "Agotados"], horizontal=True)

        df_rank = df_f.copy()
        if ver == "Mayor Stock":
            df_rank = df_rank.sort_values('Saldo', ascending=False).head(15)
        elif ver == "Stock Crítico":
            df_rank = df_rank[df_rank['Saldo'] > 0].sort_values('Saldo', ascending=True).head(15)
        else:
            df_rank = df_rank[df_rank['Saldo'] == 0]

        fig_bar = px.bar(df_rank, x='Saldo', y='nombre', color='Sede', orientation='h', text_auto='.2s',
                         color_discrete_map={"Paseo": "#81c784", "Jardin": "#4caf50", "Planta": "#1b5e20"})
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.subheader("🕵️ Auditoría de Movimientos (Octubre vs Noviembre)")
        st.markdown("Identificación automática de **Dinero Dormido** y productos de **Alta Rotación**.")

        comp = full_df[full_df['Sede'].isin(sede_sel)].pivot_table(index=['Sede', 'nombre'], columns='Mes',
                                                                   values='Saldo').fillna(0).reset_index()

        if 'Octubre' in comp.columns and 'Noviembre' in comp.columns:
            comp['Diferencia'] = comp['Noviembre'] - comp['Octubre']
            cola, colb = st.columns(2)

            with cola:
                st.error("🧊 Dinero Dormido")
                st.caption("Sin movimiento en 30 días. Evaluar evacuación.")
                parados = comp[(comp['Octubre'] == comp['Noviembre']) & (comp['Noviembre'] > 0)]
                st.dataframe(parados[['Sede', 'nombre', 'Noviembre']].rename(columns={'Noviembre': 'Saldo'}).head(20),
                             use_container_width=True, hide_index=True)

            with colb:
                st.success("🚀 Alta Rotación")
                st.caption("Items con mayor velocidad de salida.")
                salida = comp[comp['Diferencia'] < 0].copy()
                salida['Uso'] = salida['Diferencia'].abs()
                st.dataframe(salida[['Sede', 'nombre', 'Uso']].sort_values('Uso', ascending=False).head(20),
                             use_container_width=True, hide_index=True)
        else:
            st.warning("Selecciona Octubre y Noviembre para ver la Auditoría.")

    with st.expander("📄 Ver Tabla de Datos Maestra"):
        st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("❌ Los archivos CSV no han sido detectados en la carpeta del proyecto.")