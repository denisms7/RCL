from pathlib import Path
from typing import List
import pandas as pd


def carregar_rcl(diretorio: str) -> pd.DataFrame:
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

        df_long["MES_ANO"] = pd.to_datetime(
            df_long["MES_ANO"],
            format="%m/%Y"
        )

        lista_dfs.append(df_long)


    df_final = pd.concat(lista_dfs, ignore_index=True)

    renomeando_colunas = {
            "RECEITA CORRENTE LÍQUIDA (I-II)": "RECEITA CORRENTE LÍQUIDA (III) = (I - II)",
            "Outras receitas tributárias": "Outros Impostos, Taxas e Contribuições de Melhoria",
            "Receita tributária": "Impostos, Taxas e Contribuições de Melhoria",
        }

    df_final["ESPECIFICACAO"] = df_final["ESPECIFICACAO"].replace(renomeando_colunas)

    return df_final
