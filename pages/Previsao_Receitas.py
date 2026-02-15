"""
Sistema de Previsão de Receitas Públicas
Modelo: Prophet (Facebook/Meta)
Baseado no código original com melhorias visuais
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

from data.data import carregar_rcl


# ==================================================
# CONFIGURAÇÃO
# ==================================================
st.set_page_config(
    page_title="Previsão de Receitas",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Previsão de Receitas - Machine Learning")
st.markdown("---")


# ==================================================
# CARREGAMENTO DE DADOS
# ==================================================
@st.cache_data
def carregar_dados() -> pd.DataFrame:
    df_local = carregar_rcl("RCL/RCL-DATA")
    df_local["MES_ANO"] = pd.to_datetime(df_local["MES_ANO"])
    df_local = df_local.sort_values("MES_ANO")
    return df_local


df = carregar_dados()


# ==================================================
# TIPOS DE RECEITAS PERMITIDOS
# ==================================================
TIPOS_TRIBUTARIOS = [
    "IPTU",
    "ISS",
    "ITBI",
    "IRRF",
    "Outros Impostos, Taxas e Contribuições de Melhoria",
]

TIPOS_COTA = [
    "Cota parte do FPM",
    "Cota parte do ICMS",
    "Cota parte do IPVA",
    "Cota parte do ITR",
    "Transferências da LC 87/1996",
    "Transferências da LC 61/1989",
    "Transferências do FUNDEB",
    "Outras transferências correntes",
]

RCL_LABEL = "RECEITAS CORRENTES (I)"
TIPOS_COMPOSICAO = TIPOS_TRIBUTARIOS + [RCL_LABEL] + TIPOS_COTA

df = df[df["ESPECIFICACAO"].isin(TIPOS_COMPOSICAO)]


# ==================================================
# FILTROS
# ==================================================
col1, col2 = st.columns(2)

with col1:
    especificacao = st.selectbox(
        "Selecione a Receita",
        sorted(df["ESPECIFICACAO"].unique())
    )

with col2:
    anos_previsao = st.slider(
        "Horizonte de previsão (anos)",
        min_value=1,
        max_value=5,
        value=3
    )


# ==================================================
# PREPARAÇÃO DOS DADOS
# ==================================================
df_modelo = df[df["ESPECIFICACAO"] == especificacao].copy()

df_modelo = df_modelo.rename(
    columns={"MES_ANO": "ds", "VALOR": "y"}
)[["ds", "y"]]

df_modelo = df_modelo.sort_values("ds").reset_index(drop=True)

# Remove valores <= 0
df_modelo = df_modelo[df_modelo["y"] > 0].reset_index(drop=True)

# Validação: mínimo de 24 meses
if len(df_modelo) < 24:
    st.error("⚠️ Série insuficiente para previsão confiável. Mínimo: 24 meses.")
    st.stop()

# Transformação logarítmica (ESSENCIAL para receitas com crescimento exponencial)
df_modelo["y_log"] = np.log1p(df_modelo["y"])


# ==================================================
# DIVISÃO TREINO/TESTE (últimos 12 meses para teste)
# ==================================================
corte_validacao = df_modelo["ds"].max() - pd.DateOffset(months=12)

train = df_modelo[df_modelo["ds"] <= corte_validacao].copy()
test = df_modelo[df_modelo["ds"] > corte_validacao].copy()

# Info sobre divisão
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Meses", len(df_modelo))
with col2:
    st.metric("Treino", len(train))
with col3:
    st.metric("Teste (Validação)", len(test))

st.markdown("---")


# ==================================================
# TREINAMENTO DO MODELO
# ==================================================
with st.spinner("🤖 Treinando modelo Prophet..."):
    
    modelo = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        interval_width=0.95
    )
    
    # Treina com dados transformados (log)
    modelo.fit(train[["ds", "y_log"]].rename(columns={"y_log": "y"}))
    
    # Cria dataframe futuro
    future = modelo.make_future_dataframe(
        periods=anos_previsao * 12,
        freq="MS"
    )
    
    # Faz previsão
    forecast = modelo.predict(future)
    
    # Reverte transformação logarítmica
    forecast["yhat"] = np.expm1(forecast["yhat"]).clip(lower=0)
    forecast["yhat_lower"] = np.expm1(forecast["yhat_lower"]).clip(lower=0)
    forecast["yhat_upper"] = np.expm1(forecast["yhat_upper"]).clip(lower=0)



# ==================================================
# MÉTRICAS DE VALIDAÇÃO (últimos 12 meses)
# ==================================================
if not test.empty:
    
    st.subheader("📊 Métricas de Validação (últimos 12 meses)")
    
    forecast_test = forecast.merge(
        test[["ds", "y"]],
        on="ds",
        how="inner"
    )
    
    if not forecast_test.empty:
        
        y_true = forecast_test["y"]
        y_pred = forecast_test["yhat"]
        
        # Calcula métricas
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        
        # MAPE seguro (evita divisão por zero)
        mask = y_true != 0
        if mask.sum() > 0:
            mape = np.mean(
                np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])
            ) * 100
        else:
            mape = np.nan
        
        # Percentuais em relação à média
        media_valor = y_true.mean()
        percentual_mae = (mae / media_valor) * 100 if media_valor > 0 else np.nan
        percentual_rmse = (rmse / media_valor) * 100 if media_valor > 0 else np.nan
        
        # Viés (tendência de super/subestimar)
        vies = np.mean(y_pred - y_true)
        vies_perc = (vies / media_valor) * 100 if media_valor > 0 else np.nan
        
        # Exibe métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "MAE",
                f"R$ {mae:,.2f}",
                delta=f"{percentual_mae:.1f}%",
                delta_color="inverse",
                help="Erro médio absoluto"
            )
        
        with col2:
            st.metric(
                "RMSE",
                f"R$ {rmse:,.2f}",
                delta=f"{percentual_rmse:.1f}%",
                delta_color="inverse",
                help="Raiz do erro quadrático médio"
            )
        
        with col3:
            st.metric(
                "MAPE",
                f"{mape:.1f}%" if not np.isnan(mape) else "N/A",
                help="Erro percentual médio absoluto"
            )
        
        with col4:
            vies_label = "Superestima" if vies > 0 else "Subestima"
            st.metric(
                "Viés",
                f"{abs(vies_perc):.1f}%",
                delta=vies_label,
                delta_color="off",
                help="Tendência sistemática do modelo"
            )
        
        # Avaliação da qualidade
        if mape < 10:
            st.success("✅ Excelente precisão no último ano!")
        elif mape < 20:
            st.info("ℹ️ Boa precisão no último ano.")
        elif mape < 30:
            st.warning("⚠️ Precisão moderada.")
        else:
            st.error("❌ Baixa precisão. Recomenda-se revisão.")
        
        st.markdown("---")


# ==================================================
# GRÁFICO PRINCIPAL
# ==================================================
st.subheader("📈 Série Temporal e Previsão")

fig = go.Figure()

# Dados reais (azul - toda a série histórica)
fig.add_trace(
    go.Scatter(
        x=df_modelo["ds"],
        y=df_modelo["y"],
        name="Dados Reais",
        mode="lines",
        line=dict(color="blue", width=2.5),
        hovertemplate="<b>Real</b><br>Data: %{x}<br>Valor: R$ %{y:,.2f}<extra></extra>"
    )
)

# Previsão (vermelha tracejada)
fig.add_trace(
    go.Scatter(
        x=forecast["ds"],
        y=forecast["yhat"],
        name="Previsão",
        mode="lines",
        line=dict(color="red", width=2.5, dash="dash"),
        hovertemplate="<b>Previsão</b><br>Data: %{x}<br>Valor: R$ %{y:,.2f}<extra></extra>"
    )
)

# Intervalo de confiança superior (linha pontilhada)
fig.add_trace(
    go.Scatter(
        x=forecast["ds"],
        y=forecast["yhat_upper"],
        mode="lines",
        line=dict(color="rgba(255, 0, 0, 0.3)", width=1, dash="dot"),
        name="Limite Superior (95%)",
        hovertemplate="<b>Limite Superior</b><br>Data: %{x}<br>Máximo: R$ %{y:,.2f}<extra></extra>"
    )
)

# Intervalo de confiança inferior (linha pontilhada)
fig.add_trace(
    go.Scatter(
        x=forecast["ds"],
        y=forecast["yhat_lower"],
        mode="lines",
        line=dict(color="rgba(255, 0, 0, 0.3)", width=1, dash="dot"),
        name="Limite Inferior (95%)",
        hovertemplate="<b>Limite Inferior</b><br>Data: %{x}<br>Mínimo: R$ %{y:,.2f}<extra></extra>"
    )
)

# Área preenchida entre os limites (área sombreada)
fig.add_trace(
    go.Scatter(
        x=forecast["ds"],
        y=forecast["yhat_upper"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    )
)

fig.add_trace(
    go.Scatter(
        x=forecast["ds"],
        y=forecast["yhat_lower"],
        fill="tonexty",
        mode="lines",
        line=dict(width=0),
        fillcolor="rgba(255, 0, 0, 0.1)",
        showlegend=False,
        hoverinfo="skip"
    )
)

fig.update_layout(
    height=600,
    template="plotly_white",
    xaxis_title="Data",
    yaxis_title="Valor (R$)",
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig, use_container_width=True)


# ==================================================
# ANÁLISE DETALHADA DE ERROS (opcional)
# ==================================================
if not test.empty and not forecast_test.empty:
    
    with st.expander("📉 Ver Análise Detalhada de Erros no Período de Teste"):
        
        # Calcula erros
        df_erros = forecast_test.copy()
        df_erros["erro"] = df_erros["yhat"] - df_erros["y"]
        df_erros["erro_perc"] = (df_erros["erro"] / df_erros["y"]) * 100
        
        # Gráfico de barras dos erros
        fig_erro = go.Figure()
        
        fig_erro.add_trace(
            go.Bar(
                x=df_erros["ds"],
                y=df_erros["erro"],
                name="Erro (R$)",
                marker_color=["red" if e < 0 else "green" for e in df_erros["erro"]]
            )
        )
        
        fig_erro.update_layout(
            title="Erro por Mês (Positivo = Superestimou | Negativo = Subestimou)",
            xaxis_title="Mês",
            yaxis_title="Erro (R$)",
            height=350,
            template="plotly_white",
            showlegend=False
        )
        
        st.plotly_chart(fig_erro, use_container_width=True)
        
        # Tabela detalhada
        st.subheader("Detalhamento Mês a Mês")
        
        df_tabela_erros = df_erros[["ds", "y", "yhat", "erro", "erro_perc"]].copy()
        df_tabela_erros.columns = ["Data", "Real", "Previsto", "Erro (R$)", "Erro (%)"]
        df_tabela_erros["Data"] = df_tabela_erros["Data"].dt.strftime("%m/%Y")
        df_tabela_erros["Real"] = df_tabela_erros["Real"].apply(lambda x: f"R$ {x:,.2f}")
        df_tabela_erros["Previsto"] = df_tabela_erros["Previsto"].apply(lambda x: f"R$ {x:,.2f}")
        df_tabela_erros["Erro (R$)"] = df_tabela_erros["Erro (R$)"].apply(lambda x: f"R$ {x:,.2f}")
        df_tabela_erros["Erro (%)"] = df_tabela_erros["Erro (%)"].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(df_tabela_erros, use_container_width=True, hide_index=True)


# ==================================================
# TABELA DE PREVISÕES FUTURAS
# ==================================================
st.subheader("📋 Valores Projetados")

ultima_data = df_modelo["ds"].max()

df_futuro = forecast.loc[
    forecast["ds"] > ultima_data,
    ["ds", "yhat", "yhat_lower", "yhat_upper"],
].copy()

if df_futuro.empty:
    st.warning("⚠️ Não há previsões futuras disponíveis.")
else:
    
    # Prepara tabela formatada
    df_tabela = pd.DataFrame({
        "Mês/Ano": df_futuro["ds"].dt.strftime("%m/%Y"),
        "Previsão": df_futuro["yhat"].apply(lambda x: f"R$ {x:,.2f}"),
        "Mínimo (95%)": df_futuro["yhat_lower"].apply(lambda x: f"R$ {x:,.2f}"),
        "Máximo (95%)": df_futuro["yhat_upper"].apply(lambda x: f"R$ {x:,.2f}")
    })
    
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)
    
    # Estatísticas resumidas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Média Mensal Projetada",
            f"R$ {df_futuro['yhat'].mean():,.2f}"
        )
    
    with col2:
        crescimento = ((df_futuro["yhat"].iloc[-1] / df_futuro["yhat"].iloc[0]) - 1) * 100
        st.metric(
            "Crescimento Total",
            f"{crescimento:.1f}%"
        )
    
    with col3:
        st.metric(
            "Total Acumulado",
            f"R$ {df_futuro['yhat'].sum():,.2f}"
        )
    
    # Botão de download
    csv = df_futuro[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_csv(index=False)
    st.download_button(
        label="📥 Baixar Previsões (CSV)",
        data=csv,
        file_name=f"previsao_{especificacao.replace(' ', '_')}_{anos_previsao}anos.csv",
        mime="text/csv"
    )


# ==================================================
# DOCUMENTAÇÃO E GUIAS
# ==================================================
st.markdown("---")

with st.expander("📚 Como Interpretar os Indicadores de Erro"):
    st.markdown("""
    ### 📊 Guia de Interpretação das Métricas
    
    #### **MAE (Erro Médio Absoluto)**
    Indica, em média, quanto a previsão errou em valor absoluto (R$).  
    O percentual representa o erro em relação à média da receita no período.
    
    - ✅ Até 10% → Excelente  
    - 🟢 10% a 20% → Bom  
    - 🟡 20% a 30% → Aceitável  
    - 🔴 Acima de 30% → Modelo precisa de ajuste  
    
    ---
    
    #### **RMSE (Raiz do Erro Quadrático Médio)**
    Similar ao MAE, porém penaliza mais os erros grandes.  
    Quando o RMSE é muito maior que o MAE, indica picos de erro em alguns meses.
    
    - ✅ Até 15% → Muito bom  
    - 🟢 15% a 30% → Utilizável  
    - 🔴 Acima de 30% → Alta volatilidade ou baixa precisão  
    
    ---
    
    #### **MAPE (Erro Percentual Médio Absoluto)**
    Mostra o erro percentual médio. É o mais intuitivo para planejamento orçamentário.
    
    - ✅ Até 10% → Alta confiabilidade  
    - 🟢 10% a 20% → Confiável  
    - 🟡 20% a 30% → Moderado  
    - 🟠 30% a 40% → Baixa precisão  
    - 🔴 Acima de 40% → Não recomendado para decisões estratégicas  
    
    ---
    
    #### **Viés**
    Indica se o modelo tem tendência sistemática de superestimar ou subestimar.
    
    - **Superestima:** Previsões consistentemente maiores que valores reais
    - **Subestima:** Previsões consistentemente menores que valores reais
    - **Ideal:** Viés próximo de zero (erros equilibrados)
    
    ---
    
    #### ⚠️ **Observações Importantes**
    - Valores elevados podem ocorrer em receitas muito voláteis
    - Sazonalidade forte pode aumentar os erros
    - Meses com valores próximos de zero afetam o MAPE
    - O intervalo de confiança de 95% indica que há 95% de probabilidade 
      do valor real estar dentro da faixa projetada
    """)

with st.expander("ℹ️ Sobre o Modelo de Previsão"):
    st.markdown("""
    ### 🤖 Metodologia
    
    Este sistema utiliza o **Prophet**, desenvolvido pelo Facebook/Meta, 
    um modelo de previsão de séries temporais que:
    
    - 📈 Detecta automaticamente tendências e sazonalidades
    - 📊 Lida bem com dados faltantes e outliers
    - 🔄 Considera sazonalidade anual
    - 📉 **Usa transformação logarítmica** para estabilizar variância e capturar 
      crescimento exponencial (essencial para receitas públicas)
    - ✅ Valida o modelo com os últimos 12 meses de dados históricos
    
    ---
    
    ### ⚙️ Configurações Aplicadas
    
    - **Sazonalidade:** Multiplicativa (ideal para dados que crescem proporcionalmente)
    - **Intervalo de Confiança:** 95%
    - **Validação:** Últimos 12 meses separados para teste
    - **Transformação:** Logarítmica (log1p/expm1) para estabilizar série
    
    ---
    
    ### 🔬 Por Que Transformação Log?
    
    Receitas públicas geralmente crescem de forma **percentual** (ex: 10% ao ano), 
    não em valores absolutos.
    
    **Sem transformação log:**
    - Modelo aprende: +R$ 100.000 por ano (linear)
    - Erro cresce com o tempo
    
    **Com transformação log:**
    - Modelo aprende: +10% por ano (exponencial)
    - Captura o padrão real de crescimento
    - Erros proporcionais ao nível
    
    **Resultado:** Previsões muito mais precisas! ✅
    """)

