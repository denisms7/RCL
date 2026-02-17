import streamlit as st
import plotly.express as px
from data.folha.data import load_data_folha


# -------------------------------------------------
# Configuração da página
# -------------------------------------------------
st.set_page_config(
    page_title="Folha de Pagamento",
    page_icon="👤",
    layout="wide"
)

st.title("👤 Folha de Pagamento")

with st.spinner("Carregando dados..."):
    df = load_data_folha()

# -------------------------------------------------
# Filtrar período 👤
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


anos = len(df["ANO"].unique())
meses = len(df["MES_ANO"].unique())
zeros = len(df[df["TOTAL_VANTAGENS"].isna()])

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Anos",
        value=anos,
        help=f"Quantidade de anos registrados: {ano_inicio} a {ano_fim}"
    )

with col2:
    st.metric(
        label="Mêses",
        value=meses,
        help=f"Quantidade de meses registrados: {ano_inicio} a {ano_fim}"
    )

with col3:
    st.metric(
        label="Mêses Ausentes",
        value=zeros,
        help=f"Quantidade de meses com total vantagens zero: {ano_inicio} a {ano_fim} (Ausentes no Portal da Transparência)"
    )

tipo_dado = st.segmented_control(
    "Tipo de Visualização",
    options=[
        "Grafico Mensal",
        "Grafico Anual",
        "Tabela de Dados",
    ],
    default="Grafico Mensal",
)

if tipo_dado == None:
    st.warning("Selecione um tipo de visualização.")
    st.stop()

if tipo_dado == "Grafico Mensal":
    df_mensal = df.groupby("MES_ANO")["TOTAL_VANTAGENS"].sum().reset_index()
    fig_mensal = px.line(
        df_mensal,
        x="MES_ANO",
        y="TOTAL_VANTAGENS",
        markers=True,
    )

    fig_mensal.update_layout(
        title="Total de Vantagens por Mês",
        xaxis_title="Mês",
        yaxis_title="Valor (R$)",
        yaxis=dict(
            tickformat=",.2f",
            tickprefix="R$ ",
            separatethousands=True
        )
    )

    fig_mensal.update_traces(
        hovertemplate=(
            f"Total de Vantagens: %{{x}}<br>"
            "Valor: R$ %{y:,.2f}"
            "<extra></extra>"
        )
    )

    st.plotly_chart(fig_mensal, width='stretch')

elif tipo_dado == "Grafico Anual":
    df_anual = df.groupby("ANO")["TOTAL_VANTAGENS"].sum().reset_index()
    fig_anual = px.bar(
        df_anual,
        x="ANO",
        y="TOTAL_VANTAGENS",
    )

    fig_anual.update_layout(
        title="Total de Vantagens por Ano",
        xaxis_title="Ano",
        yaxis_title="Valor (R$)",
        yaxis=dict(
            tickformat=",.2f",
            tickprefix="R$ ",
            separatethousands=True
        )
    )

    fig_anual.update_traces(
        hovertemplate=(
            f"Total de Vantagens ano: %{{x}}<br>"
            "Valor: R$ %{y:,.2f}"
            "<extra></extra>"
        )
    )

    st.plotly_chart(fig_anual, width='stretch')

elif tipo_dado == "Tabela de Dados":
    st.dataframe(df[["ANO", "MES_ANO", "TOTAL_VANTAGENS"]].sort_values(by=["ANO", "MES_ANO"], ascending=[True, True]).reset_index(drop=True))



st.subheader("Comparativo Mensal", divider=True)

MESES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

col1, col2 = st.columns(2)

with col1:
    mes_selecionado = st.selectbox(
        "Selecione o mês",
        options=list(MESES.keys()),
        format_func=lambda x: MESES[x],
    )

df_comparativo = df[df["MES"] == mes_selecionado]

df_comparativo = df_comparativo.sort_values(by=["ANO"], ascending=True).reset_index(drop=True)

comparativo = px.bar(
    df_comparativo,
    x="ANO",
    y="TOTAL_VANTAGENS",
)

comparativo.update_layout(
    title="Total de Vantagens por Ano",
    xaxis_title="Ano",
    yaxis_title="Valor (R$)",
    yaxis=dict(
        tickformat=",.2f",
        tickprefix="R$ ",
        separatethousands=True
    )
)

comparativo.update_traces(
    hovertemplate=(
        f"Total de Vantagens ano: %{{x}}<br>"
        "Valor: R$ %{y:,.2f}"
        "<extra></extra>"
    )
)

st.plotly_chart(comparativo, width='stretch')
