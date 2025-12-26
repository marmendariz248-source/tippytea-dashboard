import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="TIPPYTEA | Executive Analytics", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { 
        background-color: #ffffff; border: 1px solid #e0e0e0; 
        padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    h1, h2, h3 { color: #1b5e20 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    div[data-testid="stExpander"] { border: none; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)


# --- 2. SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    st.title("🔒 TIPPYTEA - Business Intelligence")
    pwd = st.text_input("Credencial de Acceso:", type="password")
    if st.button("Acceder"):
        if pwd == "Tippytea2025":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Acceso denegado")
    return False


if not check_password(): st.stop()


# --- 3. PROCESAMIENTO DE DATOS ---
@st.cache_data
def get_data():
    files = [
        {"m": "Octubre", "s": "Paseo", "p": "TOMA DE INVENTARIO OCTUBRE PASEO.csv"},
        {"m": "Octubre", "s": "Jardin", "p": "TOMA INVENTARIO OCTUBRE JARDIN.csv"},
        {"m": "Octubre", "s": "Planta", "p": "TOMA DE INVENTARIO OCTUBRE PLANTA.csv"},
        {"m": "Noviembre", "s": "Paseo", "p": "Copia de Toma de Inventarios Tippytea Original Noviembre Paseo.csv"},
        {"m": "Noviembre", "s": "Jardin",
         "p": "Copia de Toma de Inventarios Tippytea Original Noviembre Jardin (1).csv"},
        {"m": "Noviembre", "s": "Planta",
         "p": "Copia de Toma de Inventarios Tippytea Original Planta Noviembre 2025 (1).csv"}
    ]
    all_dfs = []
    for f in files:
        try:
            df = pd.read_csv(f['p'], sep=';')
            df.columns = df.columns.str.strip()
            for col in ['Saldo', 'Costo']:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.').str.strip(), errors='coerce').fillna(
                    0)
            df['Mes'], df['Sede'] = f['m'], f['s']
            df['Valor_Total'] = df['Saldo'] * df['Costo']
            # Categorización simple por prefijo de código
            df['Cat'] = df['Codigo'].astype(str).str[:7]
            all_dfs.append(df[['Codigo', 'nombre', 'Saldo', 'Costo', 'Valor_Total', 'Mes', 'Sede', 'Cat']])
        except:
            continue
    return pd.concat(all_dfs)


df_all = get_data()

# --- 4. DASHBOARD UI ---
st.title("🍃 TIPPYTEA Executive Dashboard")
st.markdown("### Inteligencia de Inventario y Control de Activos")

# Sidebar - Filtros de Alto Nivel
st.sidebar.image("https://tippytea.com/wp-content/uploads/2021/05/logo-tippytea.png",
                 width=150)  # Cambia por tu logo real
st.sidebar.header("Filtros de Análisis")
sel_sede = st.sidebar.multiselect("Sedes Seleccionadas", df_all['Sede'].unique(), default=df_all['Sede'].unique())
df_f = df_all[df_all['Sede'].isin(sel_sede)]

tabs = st.tabs(["📌 Resumen Ejecutivo", "💰 Análisis de Valor", "📉 Tendencias", "🕵️ Auditoría de Rotación"])

# --- TAB 1: KPI MASTER ---
with tabs[0]:
    nov = df_f[df_f['Mes'] == 'Noviembre']
    octub = df_f[df_f['Mes'] == 'Octubre']

    val_nov = nov['Valor_Total'].sum()
    val_oct = octub['Valor_Total'].sum()
    delta_val = ((val_nov - val_oct) / val_oct * 100) if val_oct > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Valor Inventario", f"${val_nov:,.2f}", f"{delta_val:+.1f}% vs Oct")
    c2.metric("Items Activos", f"{len(nov[nov['Saldo'] > 0])}")
    c3.metric("Stock Agotado", f"{len(nov[nov['Saldo'] == 0])}", border=True)
    c4.metric("Inversión en Planta", f"${nov[nov['Sede'] == 'Planta']['Valor_Total'].sum():,.0f}")

    st.subheader("Distribución Patrimonial (Sede y Categoría)")
    fig_tree = px.treemap(nov[nov['Valor_Total'] > 0], path=['Sede', 'Cat'], values='Valor_Total',
                          color='Valor_Total', color_continuous_scale='Greens')
    st.plotly_chart(fig_tree, use_container_width=True)

# --- TAB 2: PARETO Y ABC ---
with tabs[1]:
    st.subheader("Concentración de Inversión (Top 15 Items)")
    top_items = nov.groupby('nombre')['Valor_Total'].sum().sort_values(ascending=False).head(15).reset_index()
    fig_top = px.bar(top_items, x='Valor_Total', y='nombre', orientation='h',
                     color='Valor_Total', color_continuous_scale='Greens', text_auto='.2s')
    fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)

    st.info("💡 El 20% de estos productos suelen representar el 80% del valor total de TIPPYTEA.")

# --- TAB 3: TENDENCIAS ---
with tabs[2]:
    st.subheader("Evolución de Costos por Sede")
    evol = df_f.groupby(['Mes', 'Sede'])['Valor_Total'].sum().reset_index()
    evol['Mes'] = pd.Categorical(evol['Mes'], categories=['Octubre', 'Noviembre'], ordered=True)
    fig_line = px.line(evol.sort_values('Mes'), x='Mes', y='Valor_Total', color='Sede', markers=True)
    st.plotly_chart(fig_line, use_container_width=True)

# --- TAB 4: ROTACIÓN (EL PROBLEMA DE GERENCIA) ---
with tabs[3]:
    st.subheader("⚠️ Informe de Stock Crítico y Parado")

    # Comparativa de saldos
    comp = df_f.pivot_table(index=['Sede', 'nombre'], columns='Mes', values='Saldo').fillna(0).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        st.error("📉 Items con Fuga de Stock (Uso Rápido)")
        comp['Gasto'] = comp['Octubre'] - comp['Noviembre']
        gasto = comp[comp['Gasto'] > 0].sort_values('Gasto', ascending=False).head(10)
        st.table(gasto[['Sede', 'nombre', 'Gasto']])

    with col2:
        st.warning("🧊 Items Sin Movimiento (Dinero Dormido)")
        parados = comp[(comp['Octubre'] == comp['Noviembre']) & (comp['Noviembre'] > 0)]
        st.table(parados[['Sede', 'nombre', 'Noviembre']].head(10).rename(columns={'Noviembre': 'Stock Estancado'}))

    st.subheader("Explorador de Inventario Completo")
    st.dataframe(
        nov[['Sede', 'Codigo', 'nombre', 'Saldo', 'Costo', 'Valor_Total']].sort_values('Valor_Total', ascending=False),
        use_container_width=True, hide_index=True)