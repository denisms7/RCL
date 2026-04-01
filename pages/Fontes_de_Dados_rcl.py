# app.py
import streamlit as st
from pathlib import Path
from data.rcl.data import load_data_rcl, RENOMEANDO_COLUNAS


# ==================================================
# Configuração da página
# ==================================================
st.set_page_config(
    page_title="Fontes de Dados RCL",
    page_icon="🗂️",
    layout="wide"
)

st.title("🗂️ Fontes de Dados RCL")

# ==================================================
# Carregamento de Dados
# ==================================================
with st.spinner("Carregando dados..."):
    df = load_data_rcl()

# -------------------------------------------------
# Fonte
# -------------------------------------------------
st.link_button(
    "🔗 Portal da Transparência",
    "https://centenariodosulpr.equiplano.com.br:7508/transparencia/receitaCorrenteLiquida"
)


# ==================================================
# Lista de PDFs e criação dos botões em linha
# ==================================================
pdf_dir = Path("data/rcl/rcl-pdf")  # caminho da pasta com os PDFs
pdf_files = sorted(pdf_dir.glob("*.pdf"))  # pega todos os PDFs


# Função para exibir o PDF no modal
@st.dialog("Visualizar PDF", width="large")
def mostrar_pdf(pdf_path, nome):
    st.subheader(f"📄 {nome}")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Exibir o PDF
    st.pdf(pdf_bytes, height=600)

    # Botão de download dentro do modal
    st.download_button(
        label=f"📥 Baixar {nome}",
        data=pdf_bytes,
        file_name=nome,
        mime="application/pdf",
        width='stretch'
    )


if pdf_files:
    st.subheader("📄 PDFs de Receita Corrente Líquida")

    # Criar colunas dinamicamente
    num_colunas = 5  # quantos botões por linha
    colunas = st.columns(num_colunas)

    for i, pdf in enumerate(pdf_files):
        col = colunas[i % num_colunas]  # seleciona a coluna correta
        nome_arquivo = pdf.stem  # ex: 2013

        # Botão para abrir o modal
        if col.button(f"📄 {nome_arquivo}", key=f"btn_{i}", width='stretch'):
            mostrar_pdf(pdf, f"{nome_arquivo}.pdf")

else:
    st.info("Nenhum PDF encontrado na pasta rcl-pdf.")

st.subheader("ℹ️ Observações sobre dados renomeados")

st.markdown(
    "Algumas colunas foram **renomeadas** para consolidar ou juntar dados semelhantes, conforme abaixo:"
)
for original, novo in RENOMEANDO_COLUNAS.items():
    st.markdown(f"- **{original}** → **{novo}**")


# ==================================================
# Botão para exportar DataFrame
# ==================================================

st.subheader("💾 Exportar DataFrame RCL")
csv_bytes = df.to_csv(index=False, sep=";").encode("utf-8")
st.download_button(
    label="📥 Baixar (CSV)",
    data=csv_bytes,
    file_name="RCL_Dados.csv",
    mime="text/csv"
)
