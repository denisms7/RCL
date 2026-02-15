"""
Sistema de Previsão de Receitas Públicas usando Machine Learning
Modelo: Prophet (Meta/Facebook)
Versão: 2.0 - Corrigida
Autor: Sistema de Análise Financeira
Data: Fevereiro 2026
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

from data.data import carregar_rcl


# ==================================================
# CONFIGURAÇÃO DA PÁGINA
# ==================================================
st.set_page_config(
    page_title="Previsão de Receitas Públicas",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Previsão de Receitas Públicas - Machine Learning")
st.markdown(
    "Sistema de previsão utilizando **Prophet (Meta/Facebook)** "
    "com validação estatística e análise de performance"
)
st.markdown("---")


# ==================================================
# CARREGAMENTO E CACHE DE DADOS
# ==================================================
@st.cache_data
def carregar_dados() -> pd.DataFrame:
    """
    Carrega dados de receitas do arquivo.
    
    Returns:
        DataFrame com colunas: MES_ANO, ESPECIFICACAO, VALOR
    """
    df_local = carregar_rcl("RCL/RCL-DATA")
    df_local["MES_ANO"] = pd.to_datetime(df_local["MES_ANO"])
    df_local = df_local.sort_values("MES_ANO")
    return df_local


# Carrega dados
df = carregar_dados()

if df.empty:
    st.error("❌ Erro ao carregar dados. Verifique o arquivo de dados.")
    st.stop()


# ==================================================
# DEFINIÇÃO DOS TIPOS DE RECEITAS PERMITIDOS
# ==================================================

# Receitas tributárias próprias
TIPOS_TRIBUTARIOS = [
    "IPTU",
    "ISS",
    "ITBI",
    "IRRF",
    "Outros Impostos, Taxas e Contribuições de Melhoria",
]

# Transferências constitucionais e legais
TIPOS_TRANSFERENCIAS = [
    "Cota parte do FPM",
    "Cota parte do ICMS",
    "Cota parte do IPVA",
    "Cota parte do ITR",
    "Transferências da LC 87/1996",
    "Transferências da LC 61/1989",
    "Transferências do FUNDEB",
    "Outras transferências correntes",
]

# Receita corrente líquida total
RCL_LABEL = "RECEITAS CORRENTES (I)"

# Combina todos os tipos permitidos
TIPOS_PERMITIDOS = TIPOS_TRIBUTARIOS + [RCL_LABEL] + TIPOS_TRANSFERENCIAS


# ==================================================
# INTERFACE: FILTROS E PARÂMETROS DO USUÁRIO
# ==================================================
st.subheader("⚙️ Configurações")

col1, col2 = st.columns(2)

with col1:
    # Filtra apenas opções válidas para o selectbox
    # NÃO modifica o dataframe original - apenas as opções exibidas
    opcoes_disponiveis = sorted([
        spec for spec in df["ESPECIFICACAO"].unique() 
        if spec in TIPOS_PERMITIDOS
    ])
    
    if not opcoes_disponiveis:
        st.error(
            "❌ **Nenhuma receita válida encontrada nos dados.**\n\n"
            "Verifique se o arquivo contém as especificações corretas."
        )
        st.stop()
    
    especificacao = st.selectbox(
        "📊 Tipo de Receita",
        opcoes_disponiveis,
        help="Selecione o tipo de receita para análise e previsão"
    )

with col2:
    anos_previsao = st.slider(
        "🔮 Horizonte de Previsão (anos)",
        min_value=1,
        max_value=5,
        value=3,
        help="Defina quantos anos à frente deseja prever"
    )

st.markdown("---")


# ==================================================
# PREPARAÇÃO E LIMPEZA DOS DADOS
# ==================================================

# Filtra apenas a receita selecionada
df_filtrado = df[df["ESPECIFICACAO"] == especificacao].copy()

if df_filtrado.empty:
    st.error(f"❌ Nenhum dado encontrado para: **{especificacao}**")
    st.stop()

# Renomeia para formato esperado pelo Prophet (ds = date, y = value)
df_modelo = df_filtrado.rename(
    columns={"MES_ANO": "ds", "VALOR": "y"}
)[["ds", "y"]].copy()

# Garante ordenação cronológica
df_modelo = df_modelo.sort_values("ds").reset_index(drop=True)

# Remove valores não positivos (Prophet requer y > 0)
valores_invalidos = len(df_modelo[df_modelo["y"] <= 0])
if valores_invalidos > 0:
    st.warning(
        f"⚠️ Removidos {valores_invalidos} registro(s) com valores não positivos."
    )
    df_modelo = df_modelo[df_modelo["y"] > 0].reset_index(drop=True)

# Validação final: verifica quantidade mínima de dados
total_registros = len(df_modelo)

if total_registros < 24:
    st.error(
        f"⚠️ **Dados insuficientes para previsão confiável!**\n\n"
        f"📊 Dados disponíveis: **{total_registros} meses**\n"
        f"📊 Mínimo necessário: **24 meses** (para divisão 50/50)\n\n"
        f"**Motivo:** Com menos de 24 meses, não é possível dividir os dados "
        f"adequadamente entre treino (50%) e teste (50%) para validar o modelo.\n\n"
        f"**Solução:** Selecione outra receita com histórico mais longo."
    )
    st.stop()


# ==================================================
# DIVISÃO DOS DADOS: TREINO E TESTE (50% / 50%)
# ==================================================

total_meses = len(df_modelo)
meses_teste = total_meses // 2          # Metade para teste
meses_treino = total_meses - meses_teste # Outra metade para treino

# Calcula data de corte
data_corte = df_modelo["ds"].max() - pd.DateOffset(months=meses_teste)

# Separa conjuntos
df_treino = df_modelo[df_modelo["ds"] <= data_corte].copy()
df_teste = df_modelo[df_modelo["ds"] > data_corte].copy()

# Exibe informações da divisão
st.info(
    f"📊 **Divisão dos Dados:** "
    f"{meses_treino} meses para treino • "
    f"{meses_teste} meses para validação • "
    f"Proporção: 50% / 50%"
)

# Validação adicional
if len(df_treino) < 12:
    st.warning(
        f"⚠️ **Atenção:** Apenas {len(df_treino)} meses de treino. "
        f"Resultados podem ser menos confiáveis."
    )


# ==================================================
# TREINAMENTO DO MODELO PROPHET
# ==================================================
st.subheader("🤖 Treinamento do Modelo")

with st.spinner("⏳ Treinando modelo de Machine Learning..."):
    
    # Configuração do modelo Prophet
    modelo = Prophet(
        growth='linear',                    # Crescimento linear (adequado para receitas)
        yearly_seasonality=True,            # Captura padrões anuais
        weekly_seasonality=False,           # Desabilitado (dados mensais)
        daily_seasonality=False,            # Desabilitado (dados mensais)
        seasonality_mode='multiplicative',  # Sazonalidade proporcional ao nível
        interval_width=0.95,                # Intervalo de confiança de 95%
        changepoint_prior_scale=0.1,        # Flexibilidade para mudanças de tendência
    )
    
    # Adiciona sazonalidade mensal customizada
    modelo.add_seasonality(
        name='monthly',
        period=30.5,        # Ciclo mensal
        fourier_order=5     # Complexidade da sazonalidade
    )
    
    # Treina o modelo com dados ORIGINAIS (sem transformação)
    modelo.fit(df_treino[["ds", "y"]])
    
    # Cria dataframe de datas futuras
    periodos_futuros = anos_previsao * 12  # Converte anos em meses
    df_futuro = modelo.make_future_dataframe(
        periods=periodos_futuros,
        freq='MS'  # Month Start
    )
    
    # Realiza previsões
    previsoes = modelo.predict(df_futuro)
    
    # Garante valores não negativos
    previsoes["yhat"] = previsoes["yhat"].clip(lower=0)
    previsoes["yhat_lower"] = previsoes["yhat_lower"].clip(lower=0)
    previsoes["yhat_upper"] = previsoes["yhat_upper"].clip(lower=0)

st.success("✅ Modelo treinado com sucesso!")


# ==================================================
# CÁLCULO DAS MÉTRICAS DE VALIDAÇÃO
# ==================================================

if not df_teste.empty:
    
    st.subheader(f"📊 Métricas de Validação ({meses_teste} meses)")
    
    # Merge das previsões com dados reais do conjunto de teste
    previsoes_teste = previsoes.merge(
        df_teste[["ds", "y"]],
        on="ds",
        how="inner"
    )
    
    if not previsoes_teste.empty:
        
        valores_reais = previsoes_teste["y"]
        valores_previstos = previsoes_teste["yhat"]
        
        # === CÁLCULO DAS MÉTRICAS ===
        
        # MAE - Mean Absolute Error
        mae = mean_absolute_error(valores_reais, valores_previstos)
        
        # RMSE - Root Mean Squared Error
        rmse = np.sqrt(mean_squared_error(valores_reais, valores_previstos))
        
        # MAPE - Mean Absolute Percentage Error (com proteção contra divisão por zero)
        mascara_nao_zero = valores_reais != 0
        if mascara_nao_zero.sum() > 0:
            mape = np.mean(
                np.abs((valores_reais[mascara_nao_zero] - valores_previstos[mascara_nao_zero]) 
                       / valores_reais[mascara_nao_zero])
            ) * 100
        else:
            mape = np.nan
        
        # Calcula percentuais em relação à média dos valores
        media_valores = valores_reais.mean()
        percentual_mae = (mae / media_valores * 100) if media_valores > 0 else np.nan
        percentual_rmse = (rmse / media_valores * 100) if media_valores > 0 else np.nan
        
        
        # === FUNÇÃO AUXILIAR PARA FORMATAÇÃO ===
        def formatar_delta_metrica(percentual, limite_bom=20):
            """
            Formata delta para métricas de erro (quanto menor, melhor).
            
            Args:
                percentual: Valor percentual da métrica
                limite_bom: Limite considerado bom (padrão: 20%)
            
            Returns:
                String formatada para delta ou None se inválido
            """
            if np.isnan(percentual):
                return None
            
            # Para métricas de erro, valores menores são melhores
            # Usamos negativo para aparecer verde, positivo para vermelho
            if percentual <= limite_bom:
                return f"-{percentual:.2f}%"  # Verde (bom)
            else:
                return f"{percentual:.2f}%"   # Vermelho (ruim)
        
        
        # Formata deltas
        delta_mae = formatar_delta_metrica(percentual_mae, limite_bom=20)
        delta_rmse = formatar_delta_metrica(percentual_rmse, limite_bom=25)
        delta_mape = formatar_delta_metrica(mape, limite_bom=15) if not np.isnan(mape) else None
        
        
        # === EXIBIÇÃO DAS MÉTRICAS ===
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="MAE - Erro Médio Absoluto",
                value=f"R$ {mae:,.2f}",
                delta=delta_mae,
                delta_color="inverse",
                help=(
                    "**Mean Absolute Error**\n\n"
                    "Indica o erro médio em valor absoluto (R$).\n"
                    "Quanto menor, melhor a precisão do modelo.\n\n"
                    "• Até 10%: Excelente\n"
                    "• 10-20%: Bom\n"
                    "• 20-30%: Aceitável\n"
                    "• >30%: Necessita ajuste"
                )
            )
        
        with col2:
            st.metric(
                label="RMSE - Erro Quadrático Médio",
                value=f"R$ {rmse:,.2f}",
                delta=delta_rmse,
                delta_color="inverse",
                help=(
                    "**Root Mean Squared Error**\n\n"
                    "Penaliza mais os erros grandes.\n"
                    "Se RMSE >> MAE, há picos de erro.\n\n"
                    "• Até 15%: Muito bom\n"
                    "• 15-30%: Utilizável\n"
                    "• >30%: Alta volatilidade"
                )
            )
        
        with col3:
            st.metric(
                label="MAPE - Erro Percentual Médio",
                value=f"{mape:.2f}%" if not np.isnan(mape) else "N/A",
                delta=delta_mape,
                delta_color="inverse",
                help=(
                    "**Mean Absolute Percentage Error**\n\n"
                    "Erro percentual médio.\n"
                    "Mais intuitivo para interpretação.\n\n"
                    "• Até 10%: Alta confiabilidade\n"
                    "• 10-20%: Confiável\n"
                    "• 20-30%: Moderado\n"
                    "• 30-40%: Baixa precisão\n"
                    "• >40%: Não recomendado"
                )
            )
        
        st.markdown("---")
    
    else:
        st.warning("⚠️ Não foi possível calcular métricas de validação.")

else:
    st.info("ℹ️ Sem dados de teste disponíveis. Exibindo apenas previsões.")


# ==================================================
# GRÁFICO INTERATIVO: SÉRIE TEMPORAL E PREVISÃO
# ==================================================
st.subheader("📈 Visualização: Histórico e Previsão")

fig = go.Figure()

# Trace 1: Dados históricos (linha azul sólida)
fig.add_trace(
    go.Scatter(
        x=df_modelo["ds"],
        y=df_modelo["y"],
        name="📊 Histórico",
        mode="lines",
        line=dict(color="#1f77b4", width=2.5),
        hovertemplate=(
            "<b>Dados Históricos</b><br>"
            "Data: %{x|%m/%Y}<br>"
            "Valor: R$ %{y:,.2f}<br>"
            "<extra></extra>"
        )
    )
)

# Trace 2: Linha de previsão (linha vermelha tracejada)
fig.add_trace(
    go.Scatter(
        x=previsoes["ds"],
        y=previsoes["yhat"],
        name="🔮 Previsão",
        mode="lines",
        line=dict(color="#d62728", width=2.5, dash="dash"),
        customdata=np.column_stack((
            previsoes["yhat_lower"], 
            previsoes["yhat_upper"]
        )),
        hovertemplate=(
            "<b>Previsão</b><br>"
            "Data: %{x|%m/%Y}<br>"
            "Previsto: R$ %{y:,.2f}<br>"
            "Mínimo (95%): R$ %{customdata[0]:,.2f}<br>"
            "Máximo (95%): R$ %{customdata[1]:,.2f}<br>"
            "<extra></extra>"
        )
    )
)

# Trace 3: Limite superior do intervalo (linha pontilhada)
fig.add_trace(
    go.Scatter(
        x=previsoes["ds"],
        y=previsoes["yhat_upper"],
        name="📈 Limite Superior (95%)",
        mode="lines",
        line=dict(color="rgba(214, 39, 40, 0.3)", width=1, dash="dot"),
        hovertemplate=(
            "<b>Limite Superior</b><br>"
            "Data: %{x|%m/%Y}<br>"
            "Máximo: R$ %{y:,.2f}<br>"
            "<extra></extra>"
        )
    )
)

# Trace 4: Limite inferior do intervalo (linha pontilhada)
fig.add_trace(
    go.Scatter(
        x=previsoes["ds"],
        y=previsoes["yhat_lower"],
        name="📉 Limite Inferior (95%)",
        mode="lines",
        line=dict(color="rgba(214, 39, 40, 0.3)", width=1, dash="dot"),
        hovertemplate=(
            "<b>Limite Inferior</b><br>"
            "Data: %{x|%m/%Y}<br>"
            "Mínimo: R$ %{y:,.2f}<br>"
            "<extra></extra>"
        )
    )
)

# Trace 5 e 6: Área preenchida (intervalo de confiança)
fig.add_trace(
    go.Scatter(
        x=previsoes["ds"],
        y=previsoes["yhat_upper"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    )
)

fig.add_trace(
    go.Scatter(
        x=previsoes["ds"],
        y=previsoes["yhat_lower"],
        fill="tonexty",
        mode="lines",
        line=dict(width=0),
        fillcolor="rgba(214, 39, 40, 0.15)",
        name="🎯 Intervalo de Confiança",
        hoverinfo="skip"
    )
)

# Configurações do layout do gráfico
fig.update_layout(
    height=600,
    template="plotly_white",
    xaxis=dict(
        title="Data",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)"
    ),
    yaxis=dict(
        title="Valor (R$)",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)"
    ),
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(255,255,255,0.8)"
    ),
    margin=dict(l=60, r=40, t=40, b=60)
)

st.plotly_chart(fig, use_container_width=True)


# ==================================================
# TABELA DE VALORES PROJETADOS
# ==================================================
st.subheader("📋 Tabela de Valores Projetados")

# Filtra apenas datas futuras (após última data histórica)
ultima_data_historica = df_modelo["ds"].max()
df_projecoes = previsoes[
    previsoes["ds"] > ultima_data_historica
][["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

if df_projecoes.empty:
    st.warning("⚠️ Não há projeções futuras disponíveis.")
else:
    
    # Adiciona coluna de especificação
    df_projecoes["ESPECIFICAÇÃO"] = especificacao
    
    # Formata data
    df_projecoes["MÊS/ANO"] = pd.to_datetime(
        df_projecoes["ds"]
    ).dt.strftime("%m/%Y")
    
    # Renomeia colunas
    df_projecoes = df_projecoes.rename(columns={
        "yhat": "PREVISTO",
        "yhat_lower": "LIMITE_INFERIOR",
        "yhat_upper": "LIMITE_SUPERIOR"
    })
    
    # Cria versão para exibição com formatação monetária
    df_display = df_projecoes.copy()
    for col in ["PREVISTO", "LIMITE_INFERIOR", "LIMITE_SUPERIOR"]:
        df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}")
    
    # Seleciona e reordena colunas
    colunas_finais = [
        "ESPECIFICAÇÃO",
        "MÊS/ANO",
        "PREVISTO",
        "LIMITE_INFERIOR",
        "LIMITE_SUPERIOR"
    ]
    df_display = df_display[colunas_finais]
    
    # Exibe tabela
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Estatísticas resumidas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "💰 Média Projetada",
            f"R$ {df_projecoes['PREVISTO'].mean():,.2f}"
        )
    
    with col2:
        st.metric(
            "📈 Crescimento Esperado",
            f"{((df_projecoes['PREVISTO'].iloc[-1] / df_projecoes['PREVISTO'].iloc[0] - 1) * 100):.1f}%"
        )
    
    with col3:
        st.metric(
            "📊 Total Projetado",
            f"R$ {df_projecoes['PREVISTO'].sum():,.2f}"
        )
    
    # Botão de download
    csv_data = df_projecoes[colunas_finais].to_csv(index=False).encode('utf-8')
    nome_arquivo = f"previsao_{especificacao.replace(' ', '_')}_{anos_previsao}anos.csv"
    
    st.download_button(
        label="📥 Baixar Projeções (CSV)",
        data=csv_data,
        file_name=nome_arquivo,
        mime="text/csv",
        help="Baixa as projeções em formato CSV para análise externa"
    )


# ==================================================
# DOCUMENTAÇÃO E GUIAS
# ==================================================
st.markdown("---")

# Guia de interpretação das métricas
with st.expander("📚 Como Interpretar as Métricas de Validação"):
    st.markdown("""
    ### 📊 Guia Completo de Interpretação
    
    #### **MAE - Erro Médio Absoluto (Mean Absolute Error)**
    
    Representa a média das diferenças absolutas entre valores previstos e reais.
    
    | Percentual | Classificação | Interpretação |
    |------------|---------------|---------------|
    | ≤ 10% | ✅ Excelente | Modelo muito preciso |
    | 10% - 20% | 🟢 Bom | Precisão adequada para planejamento |
    | 20% - 30% | 🟡 Aceitável | Use com cautela |
    | > 30% | 🔴 Ruim | Modelo precisa de ajuste |
    
    ---
    
    #### **RMSE - Raiz do Erro Quadrático Médio (Root Mean Squared Error)**
    
    Similar ao MAE, mas penaliza erros grandes de forma mais intensa.
    
    | Percentual | Classificação | Interpretação |
    |------------|---------------|---------------|
    | ≤ 15% | ✅ Muito Bom | Erros consistentemente baixos |
    | 15% - 30% | 🟢 Utilizável | Alguns picos de erro podem ocorrer |
    | > 30% | 🔴 Problemático | Alta volatilidade ou baixa precisão |
    
    **Dica:** Se RMSE é muito maior que MAE, indica presença de outliers ou erros pontuais grandes.
    
    ---
    
    #### **MAPE - Erro Percentual Médio Absoluto (Mean Absolute Percentage Error)**
    
    Métrica mais intuitiva: mostra o erro médio em termos percentuais.
    
    | Percentual | Classificação | Uso Recomendado |
    |------------|---------------|-----------------|
    | ≤ 10% | ✅ Alta Confiabilidade | Decisões estratégicas |
    | 10% - 20% | 🟢 Confiável | Planejamento orçamentário |
    | 20% - 30% | 🟡 Moderado | Estimativas preliminares |
    | 30% - 40% | 🟠 Baixa Precisão | Use com reservas |
    | > 40% | 🔴 Não Confiável | Não recomendado |
    
    ---
    
    #### ⚠️ **Considerações Importantes**
    
    - **Sazonalidade:** Receitas com forte variação sazonal podem ter erros maiores
    - **Volatilidade:** Receitas muito voláteis são naturalmente mais difíceis de prever
    - **Outliers:** Eventos extraordinários podem afetar temporariamente a precisão
    - **Intervalo de Confiança:** O intervalo de 95% indica que há 95% de probabilidade 
      do valor real estar dentro da faixa projetada
    
    ---
    
    #### 💡 **Exemplo Prático**
    
    Se o MAE é R$ 100.000 e a média mensal é R$ 1.000.000:
    - Erro percentual = 10%
    - Interpretação: Em média, o modelo erra R$ 100.000 para mais ou para menos
    - Classificação: ✅ Excelente precisão
    """)

# Informações sobre o modelo
with st.expander("ℹ️ Sobre o Modelo de Previsão"):
    st.markdown(f"""
    ### 🤖 Prophet: Previsão de Séries Temporais
    
    O **Prophet** é um modelo de previsão desenvolvido pela equipe de Data Science do 
    Facebook/Meta, projetado especificamente para séries temporais de negócios com 
    forte sazonalidade e feriados.
    
    ---
    
    #### 🎯 **Por que Prophet?**
    
    - **Robusto a dados faltantes:** Lida bem com gaps nos dados
    - **Detecção automática:** Identifica tendências e sazonalidades automaticamente
    - **Interpretável:** Decompõe a previsão em componentes compreensíveis
    - **Flexível:** Permite ajustes finos e sazonalidades customizadas
    - **Battle-tested:** Usado em produção por empresas como Facebook, Uber, Airbnb
    
    ---
    
    #### ⚙️ **Configurações do Modelo Atual**
    
    | Parâmetro | Valor | Descrição |
    |-----------|-------|-----------|
    | **Tipo de Crescimento** | Linear | Adequado para receitas com tendência linear/estável |
    | **Sazonalidade** | Multiplicativa | A sazonalidade cresce proporcionalmente ao nível |
    | **Sazonalidade Anual** | ✅ Habilitada | Captura padrões que se repetem a cada ano |
    | **Sazonalidade Mensal** | ✅ Customizada | Fourier order 5 para padrões mensais |
    | **Intervalo de Confiança** | 95% | Faixa com 95% de probabilidade de conter o valor real |
    | **Changepoint Prior** | 0.1 | Flexibilidade moderada para mudanças de tendência |
    | **Divisão Treino/Teste** | 50% / 50% | {meses_treino} meses treino + {meses_teste} meses teste |
    
    ---
    
    #### 📊 **Componentes da Previsão**
    
    A previsão final é composta por:
    
    1. **Tendência (Trend):** Comportamento geral de longo prazo
    2. **Sazonalidade Anual:** Padrões que se repetem todo ano
    3. **Sazonalidade Mensal:** Variações dentro do mês
    4. **Ruído:** Variações aleatórias não explicadas
    
    ```
    y(t) = Tendência(t) + Sazonalidade_Anual(t) + Sazonalidade_Mensal(t) + Ruído(t)
    ```
    
    ---
    
    #### 🔬 **Validação do Modelo**
    
    O modelo é validado usando a técnica de **holdout validation**:
    
    1. **Treino:** Primeiros 50% dos dados ({meses_treino} meses)
    2. **Teste:** Últimos 50% dos dados ({meses_teste} meses)
    3. **Métricas:** MAE, RMSE e MAPE calculados no conjunto de teste
    4. **Previsão Final:** Modelo retreinado com 100% dos dados para previsões futuras
    
    ---
    
    #### 📖 **Referências e Documentação**
    
    - [Prophet - Documentação Oficial](https://facebook.github.io/prophet/)
    - [Paper: Forecasting at Scale](https://peerj.com/preprints/3190/)
    - [GitHub Repository](https://github.com/facebook/prophet)
    - [Prophet em Python](https://facebook.github.io/prophet/docs/quick_start.html)
    
    ---
    
    #### ⚡ **Nota sobre Transformações**
    
    Este modelo **NÃO utiliza transformação logarítmica**. 
    
    Para receitas públicas, que geralmente apresentam crescimento linear estável, 
    a transformação log é desnecessária e pode até distorcer as previsões. O Prophet 
    é suficientemente robusto para trabalhar diretamente com os valores originais.
    """)

# Informações técnicas adicionais
with st.expander("🔧 Informações Técnicas Adicionais"):
    st.markdown(f"""
    ### 📋 Detalhes da Execução
    
    #### **Dados Processados**
    - Receita selecionada: **{especificacao}**
    - Total de registros: **{total_meses} meses**
    - Período histórico: **{df_modelo['ds'].min().strftime('%m/%Y')}** até **{df_modelo['ds'].max().strftime('%m/%Y')}**
    - Registros de treino: **{meses_treino} meses**
    - Registros de teste: **{meses_teste} meses**
    - Períodos projetados: **{anos_previsao} anos** ({anos_previsao * 12} meses)
    
    ---
    
    #### **Qualidade dos Dados**
    - Valores removidos (≤0): **{valores_invalidos}**
    - Dados faltantes: **{df_modelo['y'].isna().sum()}**
    - Valor médio histórico: **R$ {df_modelo['y'].mean():,.2f}**
    - Desvio padrão: **R$ {df_modelo['y'].std():,.2f}**
    - Coeficiente de variação: **{(df_modelo['y'].std() / df_modelo['y'].mean() * 100):.1f}%**
    
    ---
    
    #### **Bibliotecas e Versões**
    - Prophet (fbprophet)
    - Pandas
    - NumPy
    - Plotly
    - Scikit-learn
    - Streamlit
    
    ---
    
    #### **Suporte e Feedback**
    
    Para reportar problemas, sugerir melhorias ou fazer perguntas:
    - Use o botão de feedback no canto da página
    - Entre em contato com a equipe técnica
    - Consulte a documentação interna do sistema
    """)


# ==================================================
# RODAPÉ
# ==================================================
st.markdown("---")
st.caption(
    "🤖 **Sistema de Previsão de Receitas Públicas** | "
    "Powered by Prophet (Meta/Facebook) | "
    f"Última atualização: {pd.Timestamp.now().strftime('%d/%m/%Y às %H:%M')}"
)