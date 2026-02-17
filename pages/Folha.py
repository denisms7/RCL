import streamlit as st
import plotly.express as px
from FOLHA.data import carregar_folha


df = carregar_folha('FOLHA/FOLHA-DATA/Folha_Geral.xls')


# -------------------------------------------------
# Configuração da página
# -------------------------------------------------
st.set_page_config(
    page_title="Folha de Pagamento",
    page_icon="👤",
    layout="wide"
)

st.title("👤 Folha de Pagamento")


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
        help=f"Quantidade de anos registrados: {ano_min} a {ano_max}"
    )

with col2:
    st.metric(
        label="Mêses",
        value=meses,
        help=f"Quantidade de meses registrados: {ano_min} a {ano_max}"
    )

with col3:
    st.metric(
        label="Mêses Ausentes",
        value=zeros, 
        help=f"Quantidade de meses com total vantagens zero: {ano_min} a {ano_max} (Ausentes no Portal da Transparência)"
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

if tipo_dado == "Grafico Mensal":
    df_mensal = df.groupby("MES_ANO")["TOTAL_VANTAGENS"].sum().reset_index()
    fig_mensal = px.line(
        df_mensal,
        x="MES_ANO",
        y="TOTAL_VANTAGENS",
        title="Total de Vantagens por Mês")
    
    fig_mensal.update_layout(
        title=f"Total de Vantagens por Mês",
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

    st.plotly_chart(fig_mensal, use_container_width=True)

elif tipo_dado == "Grafico Anual":
    df_anual = df.groupby("ANO")["TOTAL_VANTAGENS"].sum().reset_index()
    fig_anual = px.bar(
        df_anual, x="ANO",
        y="TOTAL_VANTAGENS",
        title="Total de Vantagens por Ano")
    
    fig_anual.update_layout(
        title=f"Total de Vantagens por Ano",
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

    st.plotly_chart(fig_anual, use_container_width=True)

elif tipo_dado == "Tabela de Dados":
    st.dataframe(df[["ANO", "MES_ANO", "TOTAL_VANTAGENS"]].sort_values(by=["ANO", "MES_ANO"], ascending=[True, True]).reset_index(drop=True))
