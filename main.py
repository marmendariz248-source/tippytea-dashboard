import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="TIPPYTEA | Inteligencia de Inventario", page_icon="🍃", layout="wide")

# Estilos para visibilidad total en PC y Móvil
st.markdown("""
    <style>
    .stApp { background-color: #fcfdfc !important; }
    h1, h2, h3, p, span, label, .stMetric div { color: #1b5e20 !important; }
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 15px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-left: 5px solid #2e7d32;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #e8f5e9; border-radius: 4px 4px 0 0; padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)


# --- 2. SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True

    st.title("🔒 Acceso Reservado - TIPPYTEA")
    password = st.text_input("Clave de acceso:", type="password")
    if st.button("Entrar"):
        if password == "Tippytea2025":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Clave incorrecta")
    return False


if not check_password(): st.stop()


# --- 3. CARGA Y PROCESAMIENTO ---
@st.cache_data
def load_all_data():
    # Definición de archivos
    files = [
        {"mes": "Octubre", "sede": "Paseo", "path": "TOMA DE INVENTARIO OCTUBRE PASEO.csv"},
        {"mes": "Octubre", "sede": "Jardin", "path": "TOMA INVENTARIO OCTUBRE JARDIN.csv"},
        {"mes": "Octubre", "sede": "Planta", "path": "TOMA DE INVENTARIO OCTUBRE PLANTA.csv"},
        {"mes": "Noviembre", "sede": "Paseo",
         "path": "Copia de Toma de Inventarios Tippytea Original Noviembre Paseo.csv"},
        {"mes": "Noviembre", "sede": "Jardin",
         "path": "Copia de Toma de Inventarios Tippytea Original Noviembre Jardin (1).csv"},
        {"mes": "Noviembre", "sede": "Planta",
         "path": "Copia de Toma de Inventarios Tippytea Original Planta Noviembre 2025 (1).csv"}
    ]

    data_frames = []
    for f in files:
        try:
            temp_df = pd.read_csv(f['path'], sep=';')
            temp_df.columns = temp_df.columns.str.strip()
            # Limpieza numérica
            for col in ['Saldo', 'Costo']:
                if col in temp_df.columns:
                    temp_df[col] = temp_df[col].astype(str).str.replace(',', '.').str.strip()
                    temp_df[col] = pd.to_numeric(temp_df[col], errors='coerce').fillna(0)

            temp_df['Mes'] = f['mes']
            temp_df['Sede'] = f['sede']
            temp_df['Valor_Total'] = temp_df['Saldo'] * temp_df['Costo']
            data_frames.append(temp_df[['Codigo', 'nombre', 'Saldo', 'Costo', 'Valor_Total', 'Mes', 'Sede']])
        except:
            continue

    return pd.concat(data_frames, ignore_index=True) if data_frames else None


df = load_all_data()

# --- 4. INTERFAZ ---
if df is not None:
    st.title("🍃 TIPPYTEA - Análisis Evolutivo")

    # Filtros Globales
    st.sidebar.header("⚙️ Configuración")
    sedes_sel = st.sidebar.multiselect("Sedes:", df['Sede'].unique(), default=df['Sede'].unique())
    df_f = df[df['Sede'].isin(sedes_sel)]

    tab1, tab2, tab3 = st.tabs(["📊 Vista Actual", "📈 Evolución", "⚠️ Rotación y Alertas"])

    # TAB 1: VISTA ACTUAL (NOVIEMBRE)
    with tab1:
        df_nov = df_f[df_f['Mes'] == 'Noviembre']
        c1, c2, c3 = st.columns(3)
        c1.metric("Inversión Noviembre", f"${df_nov['Valor_Total'].sum():,.2f}")
        c2.metric("Items en Inventario", len(df_nov))
        c3.metric("Stock Crítico (<5)", len(df_nov[(df_nov['Saldo'] > 0) & (df_nov['Saldo'] < 5)]))

        st.subheader("Inventario por Sede (Noviembre)")
        fig_nov = px.bar(df_nov.groupby('Sede')['Valor_Total'].sum().reset_index(),
                         x='Sede', y='Valor_Total', color='Sede', text_auto='.2s')
        st.plotly_chart(fig_nov, use_container_width=True)

    # TAB 2: EVOLUCIÓN (OCT VS NOV)
    with tab2:
        st.subheader("Comparativa de Inversión Mensual")
        evol_sede = df_f.groupby(['Mes', 'Sede'])['Valor_Total'].sum().reset_index()
        # Ordenar meses para que Octubre salga antes que Noviembre
        evol_sede['Mes'] = pd.Categorical(evol_sede['Mes'], categories=['Octubre', 'Noviembre'], ordered=True)
        fig_evol = px.bar(evol_sede.sort_values('Mes'), x='Mes', y='Valor_Total', color='Sede', barmode='group')
        st.plotly_chart(fig_evol, use_container_width=True)

    # TAB 3: ANÁLISIS DE ROTACIÓN (LO QUE PIDIÓ GERENCIA)
    with tab3:
        st.subheader("🔍 Diagnóstico de Movimiento")

        # Preparar comparación
        pivoted = df_f.pivot_table(index=['Sede', 'nombre'], columns='Mes', values='Saldo').fillna(0).reset_index()

        if 'Octubre' in pivoted.columns and 'Noviembre' in pivoted.columns:
            pivoted['Diferencia'] = pivoted['Noviembre'] - pivoted['Octubre']

            col_a, col_b = st.columns(2)

            with col_a:
                st.error("🚫 Items Sin Movimiento (Parados)")
                st.caption("Items que tienen el mismo saldo en Octubre y Noviembre (y > 0)")
                parados = pivoted[(pivoted['Octubre'] == pivoted['Noviembre']) & (pivoted['Noviembre'] > 0)]
                st.dataframe(parados[['Sede', 'nombre', 'Noviembre']].rename(columns={'Noviembre': 'Saldo Actual'}),
                             hide_index=True)

            with col_b:
                st.success("🚀 Mayor Rotación (Consumo)")
                st.caption("Items que más disminuyeron su saldo este mes")
                rotacion = pivoted[pivoted['Diferencia'] < 0].copy()
                rotacion['Consumo'] = rotacion['Diferencia'].abs()
                st.dataframe(rotacion[['Sede', 'nombre', 'Consumo']].sort_values('Consumo', ascending=False).head(15),
                             hide_index=True)
        else:
            st.warning("Se necesitan datos de Octubre y Noviembre para este análisis.")

else:
    st.error("No se pudieron cargar los archivos. Verifica los nombres en GitHub.")