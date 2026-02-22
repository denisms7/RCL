import streamlit as st
import plotly.express as px
from data.rcl.data import load_data_rcl


# -------------------------------------------------
# Configuração da página
# -------------------------------------------------
st.set_page_config(
    page_title="Receita Corrente Geral",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Receita Corrente Geral")


# ==================================================
# Carregamento de Dados
# ==================================================
with st.spinner("Carregando dados..."):
    df = load_data_rcl()


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

        # Calcula o total
        df_neg_total = df_neg["VALOR"].sum() * -1
        df_neg_min = df_neg["VALOR"].min() * -1
        df_neg_max = df_neg["VALOR"].max() * -1

        # Formata VALOR em reais (somente para exibição)
        df_neg["VALOR"] = df_neg["VALOR"].apply(lambda x: f"R$ {x:,.2f}")

        cola, colb, colc = st.columns(3)

        # Mostra metricas formatado
        with cola:
            st.metric(
                label="Total de Valores Negativos",
                value=f"R$ {df_neg_total:,.2f}"
            )

        with colb:
            st.metric(
                label="Maior Negativo",
                value=f"R$ {df_neg_min:,.2f}"
            )

        with colc:
            st.metric(
                label="Menor Negativo",
                value=f"R$ {df_neg_max:,.2f}"
            )

        # Mostra tabela
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

if anexo_rcl is None:
    st.warning("Selecione um tipo de receita válido.")
    st.stop()


# Dicionário de cores
cores_plotly = {
    "RECEITA CORRENTE LÍQUIDA (III) = (I - II)": "seagreen",
    "RECEITAS CORRENTES (I)": "navy",
    "DEDUÇÕES (II)": "red"
}


anexo_rcl_tipo = st.segmented_control(
    "Tipo de Visualização",
    options=[
        "Grafico Mensal",
        "Grafico Anual",
        "Tabela de Dados",
    ],
    default="Grafico Mensal",
)

rcl_geral = df[df['ESPECIFICACAO'] == anexo_rcl]

if anexo_rcl_tipo == "Grafico Mensal":
    anexo_rcl_tipo_coluna = "MES_ANO"
    rcl_geral = rcl_geral.sort_values(by="MES_ANO")

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

elif anexo_rcl_tipo == "Grafico Anual":
    anexo_rcl_tipo_coluna = "ANO"
    rcl_geral = rcl_geral.groupby("ANO", as_index=False).agg({"VALOR": "sum"})
    rcl_geral = rcl_geral.sort_values(by="ANO")

    fig_rcl = px.bar(
        rcl_geral,
        x=anexo_rcl_tipo_coluna,
        y="VALOR",
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

elif anexo_rcl_tipo == "Tabela de Dados":

    st.dataframe(rcl_geral[['ESPECIFICACAO', "ANO", "MES_ANO", "VALOR"]])

else:
    st.warning("Selecione um tipo de visualização válido.")


# -------------------------------------------------
# ACUMULADO
# -------------------------------------------------
rcl_acumulado = (
    df.loc[df['ESPECIFICACAO'] == anexo_rcl, 'VALOR'].sum()
)

st.metric(
    label=f"Acumulado de {ano_min} a {ano_max}",
    value=f"R$ {rcl_acumulado:,.2f}",
    help=f"{anexo_rcl}"
)


# -------------------------------------------------
# INFORMACAO
# -------------------------------------------------
if anexo_rcl == "RECEITA CORRENTE LÍQUIDA (III) = (I - II)":
    st.markdown(
        "A **Receita Corrente Líquida (RCL)** é um indicador fundamental para a gestão financeira dos municípios, pois representa a receita disponível após as deduções legais. Ela é calculada subtraindo as deduções (II) das receitas correntes (I). A RCL é utilizada para determinar os limites de gastos públicos, como o percentual destinado à educação e saúde, e para avaliar a capacidade financeira do município. Manter uma RCL saudável é crucial para garantir a sustentabilidade fiscal e a capacidade de investimento em serviços públicos essenciais."
    )
elif anexo_rcl == "RECEITAS CORRENTES (I)":
    st.markdown(
        "As **Receitas Correntes (I)** englobam todas as receitas que o município arrecada regularmente, como impostos, taxas, contribuições e transferências correntes. Essas receitas são essenciais para financiar as despesas públicas e manter os serviços oferecidos à população. As receitas correntes são a base para o cálculo da Receita Corrente Líquida (RCL) e são um indicador importante da capacidade de arrecadação do município."
    )
elif anexo_rcl == "DEDUÇÕES (II)":
    st.markdown(
        "As **Deduções (II)** referem-se às despesas obrigatórias que devem ser subtraídas das receitas correntes para calcular a Receita Corrente Líquida (RCL). Essas deduções incluem transferências constitucionais, como o Fundo de Participação dos Municípios (FPM), e outras despesas legais que reduzem a receita disponível para o município. As deduções são um componente crucial para entender a real capacidade financeira do município e para garantir que os limites de gastos públicos sejam respeitados."
    )
