from pathlib import Path
from typing import List
import pandas as pd



def carregar_folha(diretorio: str) -> pd.DataFrame:
    caminho = Path(diretorio)

    df = pd.read_excel(
        caminho,
        engine="xlrd",
        decimal=",",
        thousands="."
    )

    df["Ano"] = df["Ano"].astype(int)
    df["Mês"] = df["Mês"].astype(int)

    df["MES_ANO"] = df["MES_ANO"].astype(str) + "-" + df["Ano"].astype(str)

    df["Vencimento Básico"] = df["Vencimento Básico"].astype(float)
    df["Outras Vantagens"] = df["Outras Vantagens"].astype(float)
    df["Férias"] = df["Férias"].astype(float)
    df["Décimo Terceiro"] = df["Décimo Terceiro"].astype(float)
    df["total vantagens"] = df["total vantagens"].astype(int)
    df["Desconto Previdência"] = df["Desconto Previdência"].astype(float)
    df["Desconto IR"] = df["Desconto IR"].astype(float)
    df["Outros Descontos"] = df["Outros Descontos"].astype(float)
    df["Total Líquido"] = df["Total Líquido"].astype(float)

    return df
