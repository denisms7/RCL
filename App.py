import streamlit as st
import pandas as pd
import plotly.express as px
from data.data import carregar_rcl
from plotly.subplots import make_subplots
import plotly.graph_objects as go


df = carregar_rcl('RCL/RCL-DATA')


# -------------------------------------------------
# Configuração da página
# -------------------------------------------------
st.set_page_config(
    page_title="Receitas e Despesas",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Receitas e Despesas")


# -------------------------------------------------
# Filtrar período 💰
# -------------------------------------------------
st.sidebar.subheader("🎯 Filtros", divider=True)

ano_min = int(df["ANO"].min())
ano_max = int(df["ANO"].max())

ano_inicio, ano_fim = st.sidebar.slider(
    "Selecione o intervalo de anos",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    step=1,
)

df = df.loc[
    (df["ANO"] >= ano_inicio) & (df["ANO"] <= ano_fim)
].copy()  # Adicione .copy() aqui


# -------------------------------------------------
# Anexo da LRF receita corrente liquida
# -------------------------------------------------
st.subheader("📊 Receita Corrente Geral")

anexo_rcl = st.segmented_control(
    "Tipo de Receita (Anexo LRF)",
    options=[
        "RECEITA CORRENTE LÍQUIDA (III) = (I - II)",
        "RECEITAS CORRENTES (I)",
        "DEDUÇÕES (II)",
        ],
    default="RECEITA CORRENTE LÍQUIDA (III) = (I - II)",
)

anexo_rcl_tipo = st.segmented_control(
    "Tipo de Visualização",
    options=[
        "Mensal",
        "Anual",
        ],
    default="Mensal",
)

rcl_geral = df[df['ESPECIFICACAO'] == anexo_rcl]

if anexo_rcl_tipo == "Mensal":
    anexo_rcl_tipo_coluna = "MES_ANO"
    rcl_geral = rcl_geral.sort_values(by="MES_ANO")
elif anexo_rcl_tipo == "Anual":
    anexo_rcl_tipo_coluna = "ANO"
    rcl_geral = rcl_geral.groupby("ANO", as_index=False).agg({"VALOR": "sum"})
    rcl_geral = rcl_geral.sort_values(by="ANO")

fig_rcl = px.line(
    rcl_geral,
    x=anexo_rcl_tipo_coluna,
    y="VALOR",
    markers=True,
    labels={anexo_rcl_tipo_coluna: anexo_rcl_tipo, "VALOR": "Valor"}
)

fig_rcl.update_layout(
    title=f"{anexo_rcl}",
    xaxis_title=anexo_rcl_tipo,
    yaxis_title="Valor (R$)",
    yaxis=dict(
        tickformat=",.2f",
        tickprefix="R$ ",
        separatethousands=True
    )
)

fig_rcl.update_traces(
    hovertemplate=(
        f"{anexo_rcl_tipo}: %{{x}}<br>"
        "Valor: R$ %{y:,.2f}"
        "<extra></extra>"
    )
)

st.plotly_chart(fig_rcl, width='stretch')

