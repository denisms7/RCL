import streamlit as st
import pandas as pd
import plotly.express as px

from data.data import carregar_rcl


# ==================================================
# Configuração da Página
# ==================================================
st.set_page_config(
    page_title="Receitas Tributárias",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Receitas Tributárias")


# ==================================================
# Carregamento de Dados
# ==================================================
@st.cache_data
def load_data() -> pd.DataFrame:
    return carregar_rcl("RCL/RCL-DATA")


df = load_data()


# ==================================================
# Constantes
# ==================================================
TIPOS_TRIBUTARIOS = [
    "IPTU",
    "ISS",
    "ITBI",
    "IRRF",
    "Outros Impostos, Taxas e Contribuições de Melhoria",
]

RCL_LABEL = "RECEITAS CORRENTES (I)"
TIPOS_COMPOSICAO = TIPOS_TRIBUTARIOS + [RCL_LABEL]


# ==================================================
# Funções Auxiliares
# ==================================================
def filtrar_especificacao(
    dataframe: pd.DataFrame,
    especificacoes: list[str],
) -> pd.DataFrame:
    return dataframe[
        dataframe["ESPECIFICACAO"].isin(especificacoes)
    ].copy()


def agrupar_valor(
    dataframe: pd.DataFrame,
    colunas: list[str],
) -> pd.DataFrame:
    return (
        dataframe
        .groupby(colunas, as_index=False)["VALOR"]
        .sum()
    )


def formatar_layout_monetario(fig, titulo: str):
    fig.update_layout(
        title=titulo,
        title_x=0.5,
        yaxis=dict(
            tickformat=",.2f",
            tickprefix="R$ ",
            separatethousands=True,
        ),
    )
    return fig


def calcular_composicao_liquida(
    dataframe: pd.DataFrame,
    ano: int,
) -> pd.DataFrame:
    df_ano = (
        dataframe[dataframe["ANO"] == ano]
        .groupby("ESPECIFICACAO", as_index=False)["VALOR"]
        .sum()
    )

    valor_rcl = df_ano.loc[
        df_ano["ESPECIFICACAO"] == RCL_LABEL,
        "VALOR",
    ].sum()

    valor_tributos = df_ano.loc[
        df_ano["ESPECIFICACAO"].isin(TIPOS_TRIBUTARIOS),
        "VALOR",
    ].sum()

    df_ano.loc[
        df_ano["ESPECIFICACAO"] == RCL_LABEL,
        "VALOR",
    ] = valor_rcl - valor_tributos

    df_ano["ESPECIFICACAO"] = df_ano["ESPECIFICACAO"].replace(
        {RCL_LABEL: "OUTRAS RECEITAS CORRENTES"}
    )

    return df_ano


# ==================================================
# DataFrames Base
# ==================================================
df_tributos = filtrar_especificacao(df, TIPOS_TRIBUTARIOS)
df_rcl = df[df["ESPECIFICACAO"] == RCL_LABEL].copy()
df_composicao_base = filtrar_especificacao(df, TIPOS_COMPOSICAO)


# ==================================================
# Tributação Geral
# ==================================================
st.subheader("📊 Tributação Geral")

tipo_visualizacao_geral = st.segmented_control(
    "Tipo de Visualização",
    options=["Mensal", "Anual"],
    default="Mensal",
    key="vis_geral",
)

coluna_periodo_geral = (
    "MES_ANO"
    if tipo_visualizacao_geral == "Mensal"
    else "ANO"
)

if tipo_visualizacao_geral == "Mensal":
    df_geral = agrupar_valor(
        df_tributos,
        ["MES_ANO", "ESPECIFICACAO"],
    )
else:
    df_geral = (
        agrupar_valor(
            df_tributos,
            ["ANO", "ESPECIFICACAO"],
        )
        .sort_values("ANO")
    )


fig_geral = px.bar(
    df_geral,
    x=coluna_periodo_geral,
    y="VALOR",
    color="ESPECIFICACAO",
    labels={
        coluna_periodo_geral: tipo_visualizacao_geral,
        "VALOR": "Valor (R$)",
        "ESPECIFICACAO": "Tributo",
    },
)

fig_geral.update_layout(barmode="stack")
fig_geral = formatar_layout_monetario(
    fig_geral,
    "Receita Tributária Geral",
)


df_total = (
    df_geral
    .groupby(coluna_periodo_geral, as_index=False)["VALOR"]
    .sum()
)

fig_total = px.line(
    df_total,
    x=coluna_periodo_geral,
    y="VALOR",
    markers=True,
)

fig_total = formatar_layout_monetario(
    fig_total,
    "Total de Receita Tributária",
)


col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig_geral, use_container_width=True)

with col2:
    st.plotly_chart(fig_total, use_container_width=True)


# ==================================================
# Evolução Individual (CORRIGIDO)
# ==================================================
st.subheader("📈 Evolução Individual")

col_a, col_b = st.columns(2)

with col_a:
    tipo_visualizacao_ind = st.segmented_control(
        "Tipo de Visualização",
        options=["Mensal", "Anual"],
        default="Mensal",
        key="vis_individual",
    )

with col_b:
    tributo_selecionado = st.selectbox(
        "Selecione o tributo",
        options=TIPOS_TRIBUTARIOS,
        key="tributo_individual",
    )


df_individual = df_tributos[
    df_tributos["ESPECIFICACAO"] == tributo_selecionado
].copy()


if tipo_visualizacao_ind == "Anual":

    df_individual = (
        agrupar_valor(df_individual, ["ANO"])
        .sort_values("ANO")
    )

    coluna_periodo_ind = "ANO"

else:
    ano_min = int(df_individual["ANO"].min())
    ano_max = int(df_individual["ANO"].max())

    ano_individual = st.slider(
        "Selecione o intervalo de anos",
        min_value=ano_min,
        max_value=ano_max,
        value=(ano_min, ano_max),
        step=1,
    )

    df_individual = (
        df_individual[
            (df_individual["ANO"] >= ano_individual[0]) &
            (df_individual["ANO"] <= ano_individual[1])
        ]
        .sort_values("MES_ANO")
    )

    coluna_periodo_ind = "MES_ANO"


fig_individual = px.line(
    df_individual,
    x=coluna_periodo_ind,
    y="VALOR",
    markers=True,
)

fig_individual = formatar_layout_monetario(
    fig_individual,
    tributo_selecionado,
)

st.plotly_chart(fig_individual, use_container_width=True)


# ==================================================
# Representações Percentuais
# ==================================================
st.subheader("🥧 Representação na Receita")

ano_min = int(df["ANO"].min())
ano_max = int(df["ANO"].max())

ano_selecionado = st.slider(
    "Selecione o ano",
    min_value=ano_min,
    max_value=ano_max,
    value=ano_max,
)


df_pizza_tributos = (
    df_tributos[df_tributos["ANO"] == ano_selecionado]
    .groupby("ESPECIFICACAO", as_index=False)["VALOR"]
    .sum()
)

fig_pizza_tributos = px.pie(
    df_pizza_tributos,
    names="ESPECIFICACAO",
    values="VALOR",
)


total_rcl = df_rcl[df_rcl["ANO"] == ano_selecionado]["VALOR"].sum()
total_tributos = df_pizza_tributos["VALOR"].sum()

df_proporcao = pd.DataFrame(
    {
        "Categoria": [
            "TRIBUTOS",
            "OUTRAS RECEITAS CORRENTES",
        ],
        "Valor": [
            total_tributos,
            total_rcl - total_tributos,
        ],
    }
)

fig_rcl_vs_tributos = px.pie(
    df_proporcao,
    names="Categoria",
    values="Valor",
)


df_composicao = calcular_composicao_liquida(
    df_composicao_base,
    ano_selecionado,
)

fig_composicao = px.pie(
    df_composicao,
    names="ESPECIFICACAO",
    values="VALOR",
)


col3, col4 = st.columns(2)

with col3:
    st.plotly_chart(fig_rcl_vs_tributos, use_container_width=True)

with col4:
    st.plotly_chart(fig_composicao, use_container_width=True)

st.plotly_chart(fig_pizza_tributos, use_container_width=True)
