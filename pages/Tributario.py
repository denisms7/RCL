import streamlit as st
import pandas as pd
import plotly.express as px

from data.rcl.data import load_data_rcl


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
with st.spinner("Carregando dados..."):
    df = load_data_rcl()


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
    options=["Gráfico Mensal", "Gráfico Anual"],
    default="Gráfico Mensal",
    key="vis_geral",
)

coluna_periodo_geral = (
    "MES_ANO"
    if tipo_visualizacao_geral == "Gráfico Mensal"
    else "ANO"
)

if tipo_visualizacao_geral == "Gráfico Mensal":
    df_geral = agrupar_valor(
        df_tributos,
        ["MES_ANO", "ESPECIFICACAO"],
    )

elif tipo_visualizacao_geral == "Gráfico Anual":
    df_geral = (
        agrupar_valor(
            df_tributos,
            ["ANO", "ESPECIFICACAO"],
        )
        .sort_values("ANO")
    )

else:
    st.warning("Selecione um tipo de visualização.")
    st.stop()


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

fig_geral.update_traces(
    hovertemplate=(
        f"Data: %{{x}}<br>"
        "Especificação: %{fullData.name}<br>"
        "Valor: R$ %{y:,.2f}"
        "<extra></extra>"
    )
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

fig_total.update_traces(
    hovertemplate=(
        f"Data: %{{x}}<br>"
        "Valor: R$ %{y:,.2f}"
        "<extra></extra>"
    )
)


col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig_geral, width='stretch')

with col2:
    st.plotly_chart(fig_total, width='stretch')










# ==================================================
# Evolução Individual
# ==================================================
st.subheader("📈 Evolução Individual")

col_a, col_b = st.columns(2)

with col_a:
    tipo_visualizacao_ind = st.segmented_control(
        "Tipo de Visualização",
        options=[
            "Gráfico Mensal",
            "Gráfico Anual",
            "Tabela de Dados",
        ],
        default="Gráfico Mensal",
        key="vis_individual",
    )

with col_b:
    tributo_selecionado = st.selectbox(
        "Selecione o tributo",
        options=TIPOS_TRIBUTARIOS,
        key="tributo_individual",
    )

# -------------------------------------------------
# Filtro base
# -------------------------------------------------
df_individual = df_tributos[
    df_tributos["ESPECIFICACAO"] == tributo_selecionado
].copy()


# ==================================================
# TABELA
# ==================================================
if tipo_visualizacao_ind == None:
    st.warning("Selecione um tipo de visualização válido.")
    st.stop()

if tipo_visualizacao_ind == "Tabela de Dados":

    df_individual = df_individual.sort_values(["ANO", "MES_ANO"])
    st.dataframe(df_individual)
    csv = df_individual.to_csv(
        sep=';',
        index=False,
        decimal=',',
        encoding='utf-8-sig'
    )

    st.download_button(
        label="📥 Baixar dados em CSV",
        data=csv,
        file_name=f"dados_{tributo_selecionado}.csv",
        mime="text/csv",
    )


# ==================================================
# GRÁFICOS
# ==================================================
else:

    # -------------------------
    # ANUAL
    # -------------------------
    if tipo_visualizacao_ind == "Gráfico Anual":

        df_individual = (
            agrupar_valor(df_individual, ["ANO"])
            .sort_values("ANO")
        )

        coluna_periodo_ind = "ANO"

    # -------------------------
    # MENSAL
    # -------------------------
    elif tipo_visualizacao_ind == "Gráfico Mensal":

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

    # -------------------------
    # Criação do gráfico
    # -------------------------
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

    fig_individual.update_traces(
        hovertemplate=(
            "Data: %{x}<br>"
            "Valor: R$ %{y:,.2f}"
            "<extra></extra>"
        )
    )

    st.plotly_chart(fig_individual, width="stretch")








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

# Calcula percentuais para os tributos
total_tributos = df_pizza_tributos["VALOR"].sum()
df_pizza_tributos["PERCENTUAL"] = (df_pizza_tributos["VALOR"] / total_tributos * 100)

# Ordena do maior para o menor para o gráfico de barras
df_barras = df_pizza_tributos.sort_values(by="VALOR", ascending=True)

# Gráfico de Pizza - Tributos
fig_pizza_tributos = px.pie(
    df_pizza_tributos,
    names="ESPECIFICACAO",
    values="VALOR",
    title=f"Composição dos Tributos - {ano_selecionado}",
)
fig_pizza_tributos.update_traces(
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Valor: R$ %{value:,.2f}<br>"
        "Percentual: %{percent}<br>"
        "<extra></extra>"
    ),
    textposition='inside',
    textinfo='percent+label'
)
fig_pizza_tributos.update_layout(
    showlegend=True,
    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
)

# Gráfico de Barras Horizontal
fig_bar_tributos = px.bar(
    df_barras,
    x="VALOR",
    y="ESPECIFICACAO",
    orientation='h',
    text="VALOR",
    labels={"VALOR": "Valor (R$)", "ESPECIFICACAO": "Tipo de Tributo"},
    title=f"Tributos por Categoria - {ano_selecionado}",
)
fig_bar_tributos.update_traces(
    texttemplate='R$ %{text:,.2f}',
    textposition='outside',
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Valor: R$ %{x:,.2f}<br>"
        "Percentual: %{customdata[0]:.2f}%<br>"
        "<extra></extra>"
    ),
    customdata=df_barras[["PERCENTUAL"]].values
)
fig_bar_tributos.update_layout(
    yaxis={'categoryorder': 'total ascending'},
    uniformtext_minsize=8,
    xaxis_title="Valor (R$)",
    yaxis_title="",
    margin=dict(l=20, r=20, t=40, b=20)
)

# Proporção rcl vs Tributos
total_rcl = df_rcl[df_rcl["ANO"] == ano_selecionado]["VALOR"].sum()
total_tributos_sum = df_pizza_tributos["VALOR"].sum()

df_proporcao = pd.DataFrame(
    {
        "Categoria": [
            "TRIBUTOS",
            "OUTRAS RECEITAS CORRENTES",
        ],
        "Valor": [
            total_tributos_sum,
            total_rcl - total_tributos_sum,
        ],
    }
)

# Calcula percentuais
df_proporcao["PERCENTUAL"] = (df_proporcao["Valor"] / total_rcl * 100)

fig_rcl_vs_tributos = px.pie(
    df_proporcao,
    names="Categoria",
    values="Valor",
    title=f"rcl: Tributos vs Outras Receitas - {ano_selecionado}",
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_rcl_vs_tributos.update_traces(
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Valor: R$ %{value:,.2f}<br>"
        "Percentual: %{percent}<br>"
        "Total rcl: R$ " + f"{total_rcl:,.2f}<br>"
        "<extra></extra>"
    ),
    textposition='inside',
    textinfo='percent+label',
    pull=[0.05, 0]  # destaca a fatia de Tributos
)

# Composição da rcl
df_composicao = calcular_composicao_liquida(
    df_composicao_base,
    ano_selecionado,
)

# Calcula percentuais para composição
total_composicao = df_composicao["VALOR"].sum()
df_composicao["PERCENTUAL"] = (df_composicao["VALOR"] / total_composicao * 100)

fig_composicao = px.pie(
    df_composicao,
    names="ESPECIFICACAO",
    values="VALOR",
    title=f"Composição Líquida da rcl - {ano_selecionado}",
    color_discrete_sequence=px.colors.qualitative.Pastel
)
fig_composicao.update_traces(
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Valor: R$ %{value:,.2f}<br>"
        "Percentual: %{percent}<br>"
        "Total: R$ " + f"{total_composicao:,.2f}<br>"
        "<extra></extra>"
    ),
    textposition='inside',
    textinfo='percent+label'
)
fig_composicao.update_layout(
    showlegend=True,
    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
)

# Layout com colunas
col3, col4 = st.columns(2)

with col3:
    st.plotly_chart(fig_rcl_vs_tributos, width='stretch')

with col4:
    st.plotly_chart(fig_composicao, width='stretch')

# Nova linha: Pizza e Barra Horizontal lado a lado
col5, col6 = st.columns(2)

with col5:
    st.plotly_chart(fig_pizza_tributos, width='stretch')

with col6:
    st.plotly_chart(fig_bar_tributos, width='stretch')
