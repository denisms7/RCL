from pathlib import Path
import pandas as pd


def carregar_ipca() -> pd.DataFrame:
    """
    Lê e trata um arquivo XLSX contendo dados do IPCA.

    Tratamentos:
    - Remove linhas vazias
    - Remove espaços extras
    - Converte Ano para inteiro
    - Converte Valor percentual para float
    - Remove duplicados
    """

    caminho = Path("data/ipca/ipca.xlsx")

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado:"
        )

    # Lê o Excel
    df = pd.read_excel(
        caminho,
    )

    # Remove linhas totalmente vazias
    df = df.dropna(how="all")

    # Limpa nomes das colunas
    df.columns = df.columns.str.strip()

    # Remove espaços extras dos textos
    colunas_texto = ["Descricao", "Fonte"]

    for coluna in colunas_texto:
        if coluna in df.columns:
            df[coluna] = (
                df[coluna]
                .astype(str)
                .str.strip()
            )

    # Converte Ano
    df["Ano"] = (
        pd.to_numeric(
            df["Ano"],
            errors="coerce",
        )
        .astype("Int64")
    )

    df["Valor"] = (
        df["Valor"]
        .astype(str)
        .str.strip()
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
        .mul(100)  # 0.0426 -> 4.26
    )

    # Remove duplicados
    df = df.drop_duplicates()

    # Ordena por ano
    df = df.sort_values(
        by="Ano",
        ascending=False,
    ).reset_index(drop=True)

    return df
