import streamlit as st

pages = {
    "Receitas": [
        st.Page("pages/rcl.py", title="Receita Corrente Geral"),
        st.Page("pages/Transferencias.py", title="Transferências Correntes"),
        st.Page("pages/Tributario.py", title="Tributação"),
    ],
    "Outros": [
        st.Page("pages/Previsao_Receitas.py", title="Previsão de Receitas"),
        st.Page("pages/Fontes_de_Dados.py", title="Fontes de Dados"),
    ],
}

pg = st.navigation(pages)
pg.run()