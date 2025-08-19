# -*- coding: utf-8 -*-
"""
Validacao forte dos *_ALL.csv.
Compara o melhor resultado obtido nas execucoes com o 'resumo' e verifica
contagens por (instance, variant). Gera:
 - results/validation/anomalies.csv
 - results/validation/summary.csv   (visao geral)
 - results/excel/validacao.xlsx     (abas: validacao, anomalies, summary_valid)
"""

import pathlib, csv
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]

EXEC_ALL = ROOT / "results" / "jooken" / "execucoes_jooken_ALL.csv"
RESM_ALL = ROOT / "results" / "jooken" / "resumo_jooken_ALL.csv"

OUT_DIR  = ROOT / "results" / "validation"
OUT_ANOM = OUT_DIR / "anomalies.csv"
OUT_SUMM = OUT_DIR / "summary.csv"
OUT_XLS  = ROOT / "results" / "excel" / "validacao.xlsx"

# nomes baguncados -> padrao
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

NUM_COLS = [
    "run","seed",
    "value","weight","seconds",
    "best_value","best_weight","best_seconds",
    "mean_seconds","std_seconds",
    "hit_optimal","target","feasible"
]

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (df.columns.astype(str)
                  .str.replace('\ufeff','',regex=False)
                  .str.strip().str.lower())
    to_rename = {k:v for k,v in RENAME.items() if k in df.columns}
    if to_rename:
        df.rename(columns=to_rename, inplace=True)
    return df

def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in NUM_COLS:
        if c in df.columns:
            if df[c].dtype == object:
                s = (df[c].astype(str)
                           .str.strip()
                           .str.replace(r"\s+","", regex=True)
                           .str.replace(",", ".", regex=False))
                df[c] = pd.to_numeric(s, errors="coerce")
            else:
                df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["feasible","hit_optimal"]:
        if c in df.columns:
            df[c] = df[c].fillna(0).round().astype(int)
    return df

def read_clean(path: pathlib.Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(path, engine="python")
    df = norm_cols(df)
    df = coerce_numeric(df)
    if "items" in df.columns:
        df["items"] = df["items"].astype(str)
    for k in ["instance","variant"]:
        if k in df.columns:
            df[k] = df[k].astype(str).str.strip()
    return df

def main():
    if not EXEC_ALL.exists() or not RESM_ALL.exists():
        raise SystemExit("Faltam *_ALL.csv. Rode antes: python scripts/rebuild_all.py")

    exec_df = read_clean(EXEC_ALL)
    resm_df = read_clean(RESM_ALL)

    # checagens minimas
    need_exec = ["instance","variant","run","value","seconds"]
    miss = [c for c in need_exec if c not in exec_df.columns]
    if miss:
        raise SystemExit(f"execucoes_jooken_ALL.csv sem colunas: {miss}")

    need_resm = ["instance","variant","best_value"]
    miss = [c for c in need_resm if c not in resm_df.columns]
    if miss:
        raise SystemExit(f"resumo_jooken_ALL.csv sem colunas: {miss}")

    # contagem por (instancia, variante)
    counts = (exec_df.groupby(["instance","variant"], dropna=False)
                     .agg(runs=("run","count"))
                     .reset_index())

    # melhor valor encontrado nas execucoes
    best_exec = (exec_df.sort_values(["instance","variant","value","seconds"],
                                     ascending=[True, True, False, True])
                        .groupby(["instance","variant"], dropna=False)
                        .agg(best_value_exec=("value","max"),
                             best_seconds_exec=("seconds","min"))
                        .reset_index())

    # junta com resumo
    resm2 = resm_df.merge(best_exec, on=["instance","variant"], how="left") \
                   .merge(counts,   on=["instance","variant"], how="left")

    # flags de anomalias
    anomalies = []

    # 1) faltou par no exec_df
    missing_pairs = resm2[resm2["best_value_exec"].isna()]
    for _, r in missing_pairs.iterrows():
        anomalies.append({
            "type":"exec_missing_pair",
            "instance": r["instance"],
            "variant":  r["variant"],
            "run":      "",
            "seed":     "",
            "msg":      "par (instance,variant) nao encontrado nas execucoes",
            "expected": "registro em execucoes",
            "got":      ""
        })

    # 2) diferenca de melhor valor
    comp = resm2.dropna(subset=["best_value","best_value_exec"]).copy()
    comp["same_best"] = (comp["best_value"] == comp["best_value_exec"])
    diff_best = comp[~comp["same_best"]]
    for _, r in diff_best.iterrows():
        anomalies.append({
            "type":"best_value_mismatch",
            "instance": r["instance"],
            "variant":  r["variant"],
            "run":      "",
            "seed":     "",
            "msg":      "best_value do resumo difere do melhor encontrado nas execucoes",
            "expected": r["best_value_exec"],
            "got":      r["best_value"],
        })

    # 3) contagem de runs != 20
    for _, r in counts.iterrows():
        if r["runs"] != 20:
            anomalies.append({
                "type":"runs_count",
                "instance": r["instance"],
                "variant":  r["variant"],
                "run":      "",
                "seed":     "",
                "msg":      "contagem de runs != 20",
                "expected": 20,
                "got":      int(r["runs"]),
            })

    # escreve anomalies
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    an_df = pd.DataFrame(anomalies,
                         columns=["type","instance","variant","run","seed","msg","expected","got"])
    an_df.to_csv(OUT_ANOM, index=False, quoting=csv.QUOTE_MINIMAL)

    # resumo geral
    summary = pd.DataFrame({
        "pares_total": [len(resm_df.drop_duplicates(subset=["instance","variant"]))],
        "pares_ok":    [int((comp["same_best"]).sum())],
        "pares_best_diff": [int((~comp["same_best"]).sum())],
        "pares_sem_exec":  [int(len(missing_pairs))],
        "anomalies":       [len(anomalies)]
    })
    summary.to_csv(OUT_SUMM, index=False, quoting=csv.QUOTE_MINIMAL)

    # Excel: usar openpyxl para permitir append com replace de abas
    try:
        import openpyxl  # noqa: F401
    except Exception:
        raise SystemExit("Precisa do pacote openpyxl para escrever em modo append no Excel. "
                         "Instale com: pip install openpyxl")

    mode = "a" if OUT_XLS.exists() else "w"
    with pd.ExcelWriter(OUT_XLS, engine="openpyxl", mode=mode, if_sheet_exists="replace") as xw:
        resm2.to_excel(xw, sheet_name="validacao", index=False)
        an_df.to_excel(xw, sheet_name="anomalies", index=False)
        summary.to_excel(xw, sheet_name="summary_valid", index=False)

    print("Validacao concluida.")
    print("Anomalias:", OUT_ANOM)
    print("Resumo  :", OUT_SUMM)
    print("Excel   :", OUT_XLS)

if __name__ == "__main__":
    main()
