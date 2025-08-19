# -*- coding: utf-8 -*-
"""
Comparacao das variantes nas instancias Jooken.
Entrada:
  - results/jooken/execucoes_jooken_ALL.csv
  - results/jooken/resumo_jooken_ALL.csv
Saida:
  - results/analysis/por_instancia.csv
  - results/analysis/por_variante.csv
  - results/analysis/wins.csv
  - results/excel/comparacao.xlsx (abas: por_instancia, por_variante, wins)
"""

import pathlib, pandas as pd, numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXEC_ALL = ROOT / "results" / "jooken" / "execucoes_jooken_ALL.csv"
RESM_ALL = ROOT / "results" / "jooken" / "resumo_jooken_ALL.csv"
OUT_DIR  = ROOT / "results" / "analysis"
OUT_PI   = OUT_DIR / "por_instancia.csv"
OUT_PV   = OUT_DIR / "por_variante.csv"
OUT_WINS = OUT_DIR / "wins.csv"
OUT_XLS  = ROOT / "results" / "excel" / "comparacao.xlsx"

RENAME = {
    '\ufeffinstance':'instance','instancia':'instance','instance ':'instance',
    'algoritmo':'variant','variante':'variant','alg':'variant',
    'runid':'run','execucao':'run',
    'valor':'value','best value':'best_value','bestvalue':'best_value',
    'peso':'weight','best weight':'best_weight','bestweight':'best_weight',
    'segundos':'seconds','tempo':'seconds',
    'best-seconds':'best_seconds','bestseconds':'best_seconds',
    'media_segundos':'mean_seconds','mean-seconds':'mean_seconds',
    'desvio_segundos':'std_seconds','std-seconds':'std_seconds',
    'hitoptimal':'hit_optimal','hit-optimal':'hit_optimal',
    'alvo':'target','targetvalue':'target',
    'melhor_seed':'best_seed','bestseed':'best_seed',
    'factivel':'feasible','itens':'items'
}

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (df.columns.astype(str)
                  .str.replace('\ufeff','',regex=False)
                  .str.strip().str.lower())
    df.rename(columns={k:v for k,v in RENAME.items() if k in df.columns}, inplace=True)
    for k in ["instance","variant"]:
        if k in df.columns:
            df[k] = df[k].astype(str).str.strip()
    if "items" in df.columns:
        df["items"] = df["items"].astype(str)
    return df

def read_clean(p: pathlib.Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(p, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(p, engine="python")
    return norm_cols(df)

def main():
    if not EXEC_ALL.exists():
        raise SystemExit("Faltou execucoes_jooken_ALL.csv (rode rebuild_all.py).")

    exec_all = read_clean(EXEC_ALL)

    # resumo pode não ter 'target'; lidamos com ou sem
    resm_all = read_clean(RESM_ALL) if RESM_ALL.exists() else pd.DataFrame()

    # Agrega por (instancia, variante)
    pair = (exec_all.groupby(["instance","variant"], dropna=False)
                    .agg(runs=("run","count"),
                         mean_value=("value","mean"),
                         best_value=("value","max"),
                         mean_seconds=("seconds","mean"),
                         std_seconds=("seconds","std"))
                    .reset_index())

    # Melhor valor por instancia (entre variantes)
    best_by_inst = pair.groupby("instance", as_index=False).agg(best_overall=("best_value","max"))
    pair = pair.merge(best_by_inst, on="instance", how="left")
    pair["gap_to_best_pct"] = 100 * (pair["best_overall"] - pair["best_value"]) / pair["best_overall"]
    pair["gap_to_best_pct"] = pair["gap_to_best_pct"].fillna(0)

    # Vencedor(es) por instancia (pode haver empate)
    pair["is_winner"] = (pair["best_value"] == pair["best_overall"]).astype(int)
    wins = (pair[pair["is_winner"]==1]
            .groupby("variant", as_index=False)
            .agg(wins=("instance","count")))

    # Se existir 'target' em resumo, calcula hit_optimal por par e por variante
    if not resm_all.empty and "target" in resm_all.columns:
        targets = resm_all[["instance","target"]].drop_duplicates()
        pair = pair.merge(targets, on="instance", how="left")
        pair["hit_optimal"] = ((pair["best_value"] >= pair["target"]).astype(int)
                               if pair["target"].notna().any() else 0)
    else:
        pair["hit_optimal"] = 0

    # Resumo por variante (média dos pares)
    by_var = (pair.groupby("variant", as_index=False)
                   .agg(instancias=("instance","nunique"),
                        wins=("is_winner","sum"),
                        mean_gap_pct=("gap_to_best_pct","mean"),
                        mean_best_value=("best_value","mean"),
                        mean_seconds=("mean_seconds","mean"),
                        std_seconds=("std_seconds","mean"),
                        hit_optimal_pct=("hit_optimal","mean")))
    by_var["hit_optimal_pct"] = (by_var["hit_optimal_pct"]*100).round(2)
    by_var["mean_gap_pct"] = by_var["mean_gap_pct"].round(4)

    # Ordena: mais vitórias, menor gap, menor tempo
    by_var = by_var.sort_values(
        by=["wins","mean_gap_pct","mean_seconds"],
        ascending=[False, True, True]
    ).reset_index(drop=True)

    # Salva CSVs e Excel
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pair.to_csv(OUT_PI, index=False)
    by_var.to_csv(OUT_PV, index=False)
    wins.to_csv(OUT_WINS, index=False)

    OUT_XLS.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUT_XLS, engine="xlsxwriter") as xw:
        pair.to_excel(xw, sheet_name="por_instancia", index=False)
        by_var.to_excel(xw, sheet_name="por_variante", index=False)
        wins.to_excel(xw, sheet_name="wins", index=False)

    print("OK. Arquivos gerados:")
    print(" -", OUT_PI)
    print(" -", OUT_PV)
    print(" -", OUT_WINS)
    print(" -", OUT_XLS)

if __name__ == "__main__":
    main()
