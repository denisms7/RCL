import streamlit as st
import plotly.express as px
from RCL.data import carregar_rcl


df = carregar_rcl('RCL/RCL-DATA')


# -------------------------------------------------
# Configuração da página
# -------------------------------------------------
st.set_page_config(
    page_title="Receita Corrente Geral",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Receita Corrente Geral")


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
# Descritical de receitas e despesas 💰
# -------------------------------------------------

valores_validos = df[df["VALOR"] != 0]["VALOR"]
df_negativo = df[df["VALOR"] < 0]

# Calcula métricas
df_min = valores_validos.min()
df_max = valores_validos.max()
df_mean = valores_validos.mean()
df_median = valores_validos.median()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Receita Negativa",
        value=len(df_negativo),
        help=f"Quantidade de entradas com valor negativo: {ano_min} a {ano_max}"
    )
with col2:
    st.metric(
        label="Menor Entrada",
        value=f"R$ {df_min:,.2f}",
        help=f"Menor valor registrado, desconsiderando zeros: {ano_min} a {ano_max}"
    )
with col3:
    st.metric(
        label="Maior Entrada",
        value=f"R$ {df_max:,.2f}",
        help=f"Maior valor registrado, desconsiderando zeros: {ano_min} a {ano_max}"
    )
with col4:
    st.metric(
        label="Média",
        value=f"R$ {df_mean:,.2f}",
        help=f"Média dos valores, desconsiderando zeros: {ano_min} a {ano_max}"
    )
with col5:
    st.metric(
        label="Mediana",
        value=f"R$ {df_median:,.2f}",
        help=f"Mediana dos valores, desconsiderando zeros: {ano_min} a {ano_max}"
    )


if len(df_negativo) > 0:
    with st.expander("📉 Valores de entrada negativos"):
        df_neg = df[df["VALOR"] < 0].copy()
        # Seleciona apenas as colunas relevantes
        df_neg = df_neg[["ANO", "MES_ANO", "ESPECIFICACAO", "VALOR"]]
        # Formata VALOR em reais
        df_neg["VALOR"] = df_neg["VALOR"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_neg)


# -------------------------------------------------
# Anexo da LRF receita corrente liquida
# -------------------------------------------------
st.subheader("📊 Receita Corrente Geral")

anexo_rcl = st.pills(
    "Tipo de Receita (Anexo LRF)",
    options=[
        "RECEITA CORRENTE LÍQUIDA (III) = (I - II)",
        "RECEITAS CORRENTES (I)",
        "DEDUÇÕES (II)",
        ],
    default="RECEITA CORRENTE LÍQUIDA (III) = (I - II)",
)


# Dicionário de cores
cores_plotly = {
    "RECEITA CORRENTE LÍQUIDA (III) = (I - II)": "seagreen",
    "RECEITAS CORRENTES (I)": "navy",
    "DEDUÇÕES (II)": "red"
}


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
