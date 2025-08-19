# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

MAP = {
    # Portugues -> padrao
    "instancia": "instance",
    "algoritmo": "variant",
    "variante": "variant",
    "algoritmo_variantes": "variant",
    "execucao": "run",
    "semente": "seed",
    "tempo": "time_s",
    "tempo_s": "time_s",
    "valor": "value",
    "peso": "weight",
    "factivel": "feasible",
    "factivel?": "feasible",
    "viavel": "feasible",
}

def load_fix(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in list(df.columns):
        if c.startswith("unnamed"):
            df = df.drop(columns=[c])
    df = df.rename(columns={k:v for k, v in MAP.items() if k in df.columns})
    return df

p_exec = Path("results/jooken/execucoes_jooken_ALL.csv")
p_resm = Path("results/jooken/resumo_jooken_ALL.csv")

for p in [p_exec, p_resm]:
    if not p.exists():
        raise SystemExit(f"Arquivo nao encontrado: {p}")

df_e = load_fix(p_exec)
df_r = load_fix(p_resm)

for name, df in [("execucoes", df_e), ("resumo", df_r)]:
    for col in ["instance", "variant"]:
        if col not in df.columns:
            raise SystemExit(f"{name}: coluna obrigatoria ausente: {col}. Colunas: {list(df.columns)}")

df_e.to_csv(p_exec, index=False)
df_r.to_csv(p_resm, index=False)
print("OK: cabecalhos normalizados e arquivos regravados.")
