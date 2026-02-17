from pathlib import Path
import pandas as pd


def carregar_folha(diretorio: str) -> pd.DataFrame:
    caminho = Path(diretorio)

    df = pd.read_excel(
        caminho,
        engine="xlrd",
        decimal=",",
        thousands="."
    )

    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").astype("Int64")
    df["Mês"] = pd.to_numeric(df["Mês"], errors="coerce").astype("Int64")

    df["MES_ANO"] = (
        df["Mês"].astype(str).str.zfill(2) + "/" + df["Ano"].astype(str)
    )

    # ==================================================
    # Conversão Numérica
    # ==================================================
    colunas_float = [
        "Vencimento Básico",
        "Outras Vantagens",
        "Férias",
        "Décimo Terceiro",
        "Desconto Previdência",
        "Desconto IR",
        "Outros Descontos",
        "Total Líquido",
    ]

    for coluna in colunas_float:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df["total vantagens"] = pd.to_numeric(
        df["total vantagens"],
        errors="coerce",
    ).astype("float64")

    # ==================================================
    # Renomeação
    # ==================================================
    df = df.rename(
        columns={
            "Ano": "ANO",
            "Mês": "MES",
            "Vencimento Básico": "VENCIMENTO_BASICO",
            "Outras Vantagens": "OUTRAS_VANTAGENS",
            "Férias": "FERIAS",
            "Décimo Terceiro": "DECIMO_TERCEIRO",
            "total vantagens": "TOTAL_VANTAGENS",
            "Desconto Previdência": "DESCONTO_PREVIDENCIA",
            "Desconto IR": "DESCONTO_IR",
            "Outros Descontos": "OUTROS_DESCONTOS",
            "Total Líquido": "TOTAL_LIQUIDO",
        }
    )

    df["MES_ANO"] = pd.to_datetime(
        df["MES_ANO"],
        format="%m/%Y"
    )

    return df
