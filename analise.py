# -*- coding: utf-8 -*-

from pathlib import Path
from typing import List
import plotly.express as px
import pandas as pd
import plotly.io as pio

pio.renderers.default = "browser"


## fonte https://centenariodosulpr.equiplano.com.br:7508/transparencia/receitaCorrenteLiquida


def carregar_arquivos(diretorio: str) -> pd.DataFrame:
    caminho = Path(diretorio)

    if not caminho.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {diretorio}")

    arquivos: List[Path] = sorted(caminho.glob("RCL-*.xls"))

    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo RCL-*.xls encontrado.")

    lista_dfs: List[pd.DataFrame] = []

    for arquivo in arquivos:
        ano = int(arquivo.stem.split("-")[1])

        df = pd.read_excel(
            arquivo,
            engine="xlrd",
            decimal=",",
            thousands="."
        )

        # Limpa nomes das colunas
        df.columns = df.columns.str.strip()

        # Remove colunas desnecessárias
        df = df.drop(columns=["TOTAL", "Previsão"], errors="ignore")

        # Remove linhas totalmente vazias
        df = df.dropna(how="all")

        # Limpa coluna ESPECIFICAÇÃO
        df["ESPECIFICAÇÃO"] = (
            df["ESPECIFICAÇÃO"]
            .astype(str)
            .str.strip()
        )

        # Seleciona apenas colunas de mês
        colunas_meses = [
            col for col in df.columns
            if "/" in col
        ]

        # Transforma para formato longo
        df_long = df.melt(
            id_vars=["ESPECIFICAÇÃO"],
            value_vars=colunas_meses,
            var_name="MES_ANO",
            value_name="VALOR"
        )
        
        df_long["ANO"] = ano
        
        df_long["ANO"] = df_long["ANO"].astype(int)
        df_long["VALOR"] = df_long["VALOR"].astype(float)
        df_long["ESPECIFICAÇÃO"] = df_long["ESPECIFICAÇÃO"].str.strip()
        
        df_long = df_long.rename(
            columns={"ESPECIFICAÇÃO": "ESPECIFICACAO"}
        )

        
        

        lista_dfs.append(df_long)

    df_final = pd.concat(lista_dfs, ignore_index=True)

    return df_final



df_rcl = carregar_arquivos("RCL-DATA")

variaveis = df_rcl["ESPECIFICACAO"].unique().tolist()


uteis_anexos = [
    "RECEITAS CORRENTES (I)",
    "DEDUÇÕES (II)",
    "RECEITA CORRENTE LÍQUIDA (I-II)",
    "RECEITA CORRENTE LÍQUIDA (III) = (I - II)",
    "RECEITA CORRENTE LÍQUIDA AJUSTADA PARA CÁLCULO DOS LIMITES DE ENDIVIDAMENTO (V) = (III - IV)",
    "RECEITA CORRENTE LÍQUIDA AJUSTADA PARA CÁLCULO DOS LIMITES DA DESPESA COM PESSOAL (VIII) = (V - VI - VII)",
    ]


df_rcl["ESPECIFICACAO"] = df_rcl["ESPECIFICACAO"].replace(
    {
        "RECEITA CORRENTE LÍQUIDA (I-II)": "RECEITA CORRENTE LÍQUIDA (III) = (I - II)",
    }
)



uteis = [
    #  Impostos, Taxas e Contribuições de Melhoria
    "IPTU",
    "ISS",
    "ITBI",
    "IRRF",
    "Outros Impostos, Taxas e Contribuições de Melhoria",
    
    
    "Contribuições",
    
    "Receita de contribuições", # 2015
    
    # Receita patrimonial
    "Rendimentos de Aplicação Financeira",
    "Outras Receitas Patrimoniais",
    
    
    "Receita agropecuária",
    "Receita industrial",
    "Receita de serviços",
    
    # Transferências correntes
    "Cota parte do FPM",
    "Cota parte do ICMS",
    "Cota parte do IPVA",
    "Cota parte do ITR",
    "Transferências da LC 87/1996",
    "Transferências da LC 61/1989",
    "Transferências do FUNDEB",
    "Outras transferências correntes",

    "Outras receitas correntes",
    ]




filtro = uteis_anexos[4]

df_iptu = df_rcl[
    df_rcl["ESPECIFICACAO"].str.upper() == filtro.upper()
]


df_iptu = df_rcl[
    df_rcl["ESPECIFICACAO"].str.upper() == filtro.upper()
]


df_iptu = df_iptu.groupby(["ESPECIFICACAO", "ANO"], as_index=False)["VALOR"].sum()


fig_iptu = px.line(
    df_iptu,
    x="ANO",
    y="VALOR",
    title=f"Evolução Mensal do {filtro}",
    markers=True
)

fig_iptu.update_layout(
    xaxis_title="Data",
    yaxis_title="Valor (R$)",
    template="plotly_white"
)

fig_iptu.show()


df_receitas_1 = df_rcl[
    df_rcl["ESPECIFICACAO"].isin(uteis_anexos)
]


grupo = df_receitas_1.groupby(
    ["MES_ANO", "ANO"],
    as_index=False,
)["VALOR"].sum()
