import streamlit as st
import pandas as pd
import plotly.express as px

from data.data import carregar_rcl


# ==================================================
# Configuração da Página
# ==================================================
st.set_page_config(
    page_title="Transferências correntes",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Transferências correntes")


# ==================================================
# Carregamento de Dados
# ==================================================
@st.cache_data
def load_data() -> pd.DataFrame:
    return carregar_rcl("RCL/RCL-DATA")


df = load_data()

TIPOS_TRIBUTARIOS = [
    "Cota parte do FPM",
    "Cota parte do ICMS",
    "Cota parte do IPVA",
    "Cota parte do ITR",
    "Transferências da LC 87/1996",
    "Transferências da LC 61/1989",
    "Transferências do FUNDEB",
    "Outras transferências correntes",
]

RCL_LABEL = "RECEITAS CORRENTES (I)"

ano_min = int(df["ANO"].min())
ano_max = int(df["ANO"].max())

df_transferencias = df[df["ESPECIFICACAO"].isin(TIPOS_TRIBUTARIOS)].copy()


# ==================================================
# Controle de Visualização
# ==================================================
tipo_visualizacao_geral = st.segmented_control(
    "Tipo de Visualização",
    options=["Mensal", "Anual"],
    default="Mensal",
    key="vis_geral",
)


# ==================================================
# Agrupamento Dinâmico
# ==================================================
if tipo_visualizacao_geral == "Mensal":
    eixo_x = "MES_ANO"
    x_title = "Mês/Ano"

    df_linha = (
        df_transferencias
        .groupby(["MES_ANO", "ESPECIFICACAO"], as_index=False)["VALOR"]
        .sum()
    )

    df_total = (
        df_transferencias
        .groupby("MES_ANO", as_index=False)["VALOR"]
        .sum()
    )

else:
    eixo_x = "ANO"
    x_title = "Ano"

    df_linha = (
        df_transferencias
        .groupby(["ANO", "ESPECIFICACAO"], as_index=False)["VALOR"]
        .sum()
    )

    df_total = (
        df_transferencias
        .groupby("ANO", as_index=False)["VALOR"]
        .sum()
    )


# ==================================================
# Gráfico Total Geral
# ==================================================
fig_total = px.line(
    df_total,
    x=eixo_x,
    y="VALOR",
    markers=True,
)

fig_total.update_layout(
    title="Transferências correntes - Total",
    xaxis_title=x_title,
    yaxis_title="Valor (R$)",
    yaxis=dict(
        tickformat=",.2f",
        tickprefix="R$ ",
        separatethousands=True,
    ),
)

fig_total.update_traces(
    hovertemplate=(
        f"{x_title}: %{{x}}<br>"
        "Valor: R$ %{y:,.2f}"
        "<extra></extra>"
    )
)


# ==================================================
# Gráfico por Especificação
# ==================================================
fig_total_linha = px.line(
    df_linha,
    x=eixo_x,
    y="VALOR",
    color="ESPECIFICACAO",
    markers=True,
)

fig_total_linha.update_layout(
    title="Transferências correntes por tipo",
    xaxis_title=x_title,
    yaxis_title="Valor (R$)",
    yaxis=dict(
        tickformat=",.2f",
        tickprefix="R$ ",
        separatethousands=True,
    ),
)

fig_total_linha.update_traces(
    hovertemplate=(
        f"{x_title}: %{{x}}<br>"
        "Especificação: %{fullData.name}<br>"
        "Valor: R$ %{y:,.2f}"
        "<extra></extra>"
    )
)


# ==================================================
# Layout
# ==================================================
col_a, col_b = st.columns(2)

with col_a:
    st.plotly_chart(fig_total, width='stretch')

with col_b:
    st.plotly_chart(fig_total_linha, width='stretch')



ano_individual = st.slider(
    "Selecione o ano",
    min_value=ano_min,
    max_value=ano_max,
    value=ano_max,
    step=1,
)

df_filtrado = df_transferencias[
    df_transferencias["ANO"] == ano_individual
]

df_individual = (
    df_filtrado
    .groupby("ESPECIFICACAO", as_index=False)["VALOR"]
    .sum()
    .sort_values("VALOR", ascending=False)
)




# ==================================================
# Gráfico Pizza
# ==================================================
fig_pizza = px.pie(
    df_individual,
    names="ESPECIFICACAO",
    values="VALOR",
    hole=0.4,
)

fig_pizza.update_layout(
    title=f"Distribuição - {ano_individual}"
)

fig_pizza.update_traces(
    texttemplate="%{percent}",
    hovertemplate=(
        "Ano: " + str(ano_individual) + "<br>"
        "Especificação: %{label}<br>"
        "Valor: R$ %{value:,.2f}<br>"
        "Percentual: %{percent}"
        "<extra></extra>"
    )
)

# ==================================================
# Gráfico Barras
# ==================================================
fig_barra = px.bar(
    df_individual,
    x="VALOR",
    y="ESPECIFICACAO",
    orientation="h",
    text="VALOR",
)

fig_barra.update_layout(
    title=f"Ranking das Transferências - {ano_individual}",
    xaxis_title="Valor (R$)",
    yaxis_title="",
    yaxis=dict(autorange="reversed"),
)

fig_barra.update_traces(
    texttemplate="R$ %{x:,.2f}",
    hovertemplate=(
        "Ano: " + str(ano_individual) + "<br>"
        "Especificação: %{y}<br>"
        "Valor: R$ %{x:,.2f}"
        "<extra></extra>"
    )
)

# ==================================================
# Layout lado a lado
# ==================================================
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig_pizza, width='stretch')

with col2:
    st.plotly_chart(fig_barra, width='stretch')




# 🔹 Total RCL no ano
total_rcl = (
    df[df["ANO"] == ano_individual]
    .loc[df["ESPECIFICACAO"] == RCL_LABEL, "VALOR"]
    .sum()
)

# 🔹 Total Transferências no ano
total_transferencias = (
    df[
        (df["ANO"] == ano_individual) &
        (df["ESPECIFICACAO"].isin(TIPOS_TRIBUTARIOS))
    ]["VALOR"]
    .sum()
)

df_proporcao_transferencias = pd.DataFrame(
    {
        "Categoria": [
            "TRANSFERÊNCIAS",
            "OUTRAS RECEITAS CORRENTES",
        ],
        "Valor": [
            total_transferencias,
            total_rcl - total_transferencias,
        ],
    }
)

fig_transferencias_vs_outras = px.pie(
    df_proporcao_transferencias,
    names="Categoria",
    values="Valor",
    hole=0.4,
)

fig_transferencias_vs_outras.update_layout(
    title=f"Transferências x Outras Receitas - {ano_individual}"
)

fig_transferencias_vs_outras.update_traces(
    texttemplate="%{percent}",
    hovertemplate=(
        "Ano: " + str(ano_individual) + "<br>"
        "Categoria: %{label}<br>"
        "Valor: R$ %{value:,.2f}<br>"
        "Percentual: %{percent}"
        "<extra></extra>"
    )
)

st.plotly_chart(fig_transferencias_vs_outras, width='stretch')