from pathlib import Path
from datetime import datetime

def modification_date(caminho_pasta):
    pasta = Path(caminho_pasta)
    
    arquivos = [f for f in pasta.iterdir() if f.is_file()]
    
    if not arquivos:
        return None
    
    mais_recente = max(arquivos, key=lambda f: f.stat().st_mtime)
    
    data_modificacao = datetime.fromtimestamp(mais_recente.stat().st_mtime)
    
    return mais_recente.name, data_modificacao
