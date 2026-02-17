# app.py
import streamlit as st
from data.folha.data import load_data_folha


# ==================================================
# Configuração da página
# ==================================================
st.set_page_config(
    page_title="Fontes de Dados - Folha",
    page_icon="🗂️",
    layout="wide"
)

st.title("🗂️ Fontes de Dados - Folha")

with st.spinner("Carregando dados..."):
    df = load_data_folha()

# -------------------------------------------------
# Fonte
# -------------------------------------------------
st.link_button(
    "🔗 Portal da Transparência",
    "https://centenariodosulpr.equiplano.com.br:7508/transparencia/srhRelacaoDeServidoresSalariosDetalhado/listEntidades"
)


# ==================================================
# Botão para exportar DataFrame
# ==================================================


st.subheader("💾 Exportar DataFrame rcl")
csv_bytes = df.to_csv(index=False, sep=";").encode("utf-8")
st.download_button(
    label="📥 Baixar (CSV)",
    data=csv_bytes,
    file_name="Folha_Pagamento.csv",
    mime="text/csv"
)
