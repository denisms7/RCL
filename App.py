import streamlit as st


pages = {
    "Receitas": [
        st.Page("pages/rcl.py", title="Receita Corrente Geral"),
        st.Page("pages/Transferencias.py", title="Transferências Correntes"),
        st.Page("pages/Tributario.py", title="Tributação"),
        st.Page("pages/Previsao_Receitas.py", title="Previsão de Receitas"),
        st.Page("pages/Fontes_de_Dados_rcl.py", title="Fontes de Dados"),
    ],
    "Outros": [
        st.Page("pages/Folha.py", title="Folha de Pagamento"),
        st.Page("pages/Fontes_de_Dados_Folha.py", title="Fontes de Dados"),
    ],
}

pg = st.navigation(pages)
pg.run()
