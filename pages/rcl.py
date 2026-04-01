import streamlit as st
import plotly.express as px
from data.rcl.data import load_data_rcl


# Dicionário de meses
MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


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
# Filtrar período
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
].copy()


# -------------------------------------------------
# Descritivas de receitas e despesas
# -------------------------------------------------
valores_validos = df[df["VALOR"] != 0]["VALOR"]
df_negativo = df[df["VALOR"] < 0]

df_min = valores_validos.min()
df_max = valores_validos.max()
df_mean = valores_validos.mean()
df_median = valores_validos.median()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Receita Negativa",
        value=len(df_negativo),
        help=f"Quantidade de entradas com valor negativo: {ano_inicio} a {ano_fim}"
    )
with col2:
    st.metric(
        label="Menor Entrada",
        value=f"R$ {df_min:,.2f}",
        help=f"Menor valor registrado, desconsiderando zeros: {ano_inicio} a {ano_fim}"
    )
with col3:
    st.metric(
        label="Maior Entrada",
        value=f"R$ {df_max:,.2f}",
        help=f"Maior valor registrado, desconsiderando zeros: {ano_inicio} a {ano_fim}"
    )
with col4:
    st.metric(
        label="Média",
        value=f"R$ {df_mean:,.2f}",
        help=f"Média dos valores, desconsiderando zeros: {ano_inicio} a {ano_fim}"
    )
with col5:
    st.metric(
        label="Mediana",
        value=f"R$ {df_median:,.2f}",
        help=f"Mediana dos valores, desconsiderando zeros: {ano_inicio} a {ano_fim}"
    )


if len(df_negativo) > 0:
    with st.expander("📉 Valores de entrada negativos"):
        df_neg = df[df["VALOR"] < 0].copy()
        df_neg = df_neg[["ANO", "MES_ANO", "ESPECIFICACAO", "VALOR"]]

        df_neg_total = df_neg["VALOR"].sum() * -1
        df_neg_min = df_neg["VALOR"].min() * -1
        df_neg_max = df_neg["VALOR"].max() * -1

        # Formata VALOR em reais (somente para exibição)
        df_neg["VALOR"] = df_neg["VALOR"].apply(lambda x: f"R$ {x:,.2f}")

        cola, colb, colc = st.columns(3)

        with cola:
            st.metric(label="Total de Valores Negativos", value=f"R$ {df_neg_total:,.2f}")
        with colb:
            st.metric(label="Maior Negativo", value=f"R$ {df_neg_min:,.2f}")
        with colc:
            st.metric(label="Menor Negativo", value=f"R$ {df_neg_max:,.2f}")

        st.dataframe(df_neg)


# -------------------------------------------------
# Anexo da LRF receita corrente líquida
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

anexo_rcl_tipo = st.segmented_control(
    "Tipo de Visualização",
    options=[
        "Gráfico Mensal",
        "Gráfico Anual",
        "Tabela de Dados",
    ],
    default="Gráfico Mensal",
)

rcl_geral = df[df['ESPECIFICACAO'] == anexo_rcl].copy()  # FIX: .copy() para evitar SettingWithCopyWarning

if anexo_rcl_tipo == "Gráfico Mensal":
    rcl_geral = rcl_geral.sort_values(by="MES_ANO")

    fig_rcl = px.line(
        rcl_geral,
        x="MES_ANO",
        y="VALOR",
        markers=True,
        labels={"MES_ANO": "Mês/Ano", "VALOR": "Valor"}
    )
    fig_rcl.update_layout(
        title=f"{anexo_rcl}",
        xaxis_title="Mês/Ano",
        yaxis_title="Valor (R$)",
        yaxis=dict(tickformat=",.2f", tickprefix="R$ ", separatethousands=True)
    )
    fig_rcl.update_traces(
        hovertemplate="Mês/Ano: %{x}<br>Valor: R$ %{y:,.2f}<extra></extra>"
    )
    st.plotly_chart(fig_rcl, width='stretch')  # FIX: width='stretch' não é parâmetro válido

elif anexo_rcl_tipo == "Gráfico Anual":
    rcl_geral_anual = rcl_geral.groupby("ANO", as_index=False).agg({"VALOR": "sum"})
    rcl_geral_anual = rcl_geral_anual.sort_values(by="ANO")

    fig_rcl = px.bar(
        rcl_geral_anual,
        x="ANO",
        y="VALOR",
        labels={"ANO": "Ano", "VALOR": "Valor"}
    )
    fig_rcl.update_layout(
        title=f"{anexo_rcl}",
        xaxis_title="Ano",
        yaxis_title="Valor (R$)",
        yaxis=dict(tickformat=",.2f", tickprefix="R$ ", separatethousands=True)
    )
    fig_rcl.update_traces(
        hovertemplate="Ano: %{x}<br>Valor: R$ %{y:,.2f}<extra></extra>"
    )
    st.plotly_chart(fig_rcl, width='stretch')  # FIX: width='stretch' não é parâmetro válido

elif anexo_rcl_tipo == "Tabela de Dados":
    st.dataframe(rcl_geral[['ESPECIFICACAO', "ANO", "MES_ANO", "VALOR"]])

else:
    st.warning("Selecione um tipo de visualização válido.")


# -------------------------------------------------
# ACUMULADO
# -------------------------------------------------
rcl_acumulado = df.loc[df['ESPECIFICACAO'] == anexo_rcl, 'VALOR'].sum()

st.metric(
    label=f"Acumulado de {ano_inicio} a {ano_fim}",
    value=f"R$ {rcl_acumulado:,.2f}",
    help=f"{anexo_rcl}"
)


# -------------------------------------------------
# INFORMAÇÃO
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


# -------------------------------------------------
# COMPARATIVO MENSAL
# -------------------------------------------------
st.title("📅 Comparativo Mensal")

# FIX: Criar coluna MES a partir de rcl_geral (já filtrado por especificação)
rcl_geral["MES"] = rcl_geral["MES_ANO"].dt.month

mes_selecionado = st.selectbox(
    "Selecione o mês:",
    options=list(MESES.keys()),
    format_func=lambda x: MESES[x]
)

nome_mes = MESES[mes_selecionado]

# FIX: Comparativo mensal sempre usa ANO no eixo X (comparação entre anos para o mesmo mês)
df_mes = rcl_geral[rcl_geral["MES"] == mes_selecionado].sort_values(by="MES_ANO")

mes_min = df_mes["ANO"].min()
mes_max = df_mes["ANO"].max()

fig_mes = px.bar(
    df_mes,
    x="ANO",
    y="VALOR",
    labels={"ANO": f"{nome_mes} ao longo dos anos", "VALOR": "Valor"}
)

fig_mes.update_layout(
    title=f"{mes_min} a {mes_max} | {nome_mes.upper()} | {anexo_rcl}",
    xaxis_title="Ano",
    yaxis_title="Valor (R$)",
    yaxis=dict(tickformat=",.2f", tickprefix="R$ ", separatethousands=True)
)
fig_mes.update_traces(
    hovertemplate="Ano: %{x}<br>Valor: R$ %{y:,.2f}<extra></extra>"
)

st.plotly_chart(fig_mes, width='stretch')  # FIX: width='stretch' não é parâmetro válido