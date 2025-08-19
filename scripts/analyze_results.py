# -*- coding: utf-8 -*-
"""
Consolidacao/analise robusta sobre *_ALL.csv com normalizacao de cabecalhos.
Gera: results/validation/summary.csv e results/excel/validacao.xlsx
"""

import pathlib, csv, re
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXEC_ALL = ROOT / "results" / "jooken" / "execucoes_jooken_ALL.csv"
RESM_ALL = ROOT / "results" / "jooken" / "resumo_jooken_ALL.csv"
OUT_SUM = ROOT / "results" / "validation" / "summary.csv"
OUT_XLS = ROOT / "results" / "excel" / "validacao.xlsx"

# mapeamento de nomes "baguncados" -> padrao
rename_map = {
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

# colunas que devem ser numericas (se existirem)
NUM_COLS = [
    "run","seed",
    "value","weight","seconds",
    "best_value","best_weight","best_seconds",
    "mean_seconds","std_seconds",
    "hit_optimal","target","feasible"
]

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    cols_norm = (df.columns.astype(str)
                 .str.replace('\ufeff','',regex=False)
                 .str.strip().str.lower())
    df.columns = cols_norm
    # renomeia o que reconhecer
    to_rename = {k: v for k, v in rename_map.items() if k in df.columns}
    if to_rename:
        df.rename(columns=to_rename, inplace=True)
    return df

def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Forca colunas esperadas como numericas.
    - remove espacos
    - troca virgula decimal por ponto quando necessario
    - converte com errors='coerce'
    """
    for c in NUM_COLS:
        if c in df.columns:
            # se a coluna veio como objeto, tenta normalizar texto/virgula
            if df[c].dtype == object:
                s = df[c].astype(str).str.strip()
                # remove espacos "soltos" dentro de numeros (ex: "1 234" -> "1234")
                s = s.str.replace(r"\s+", "", regex=True)
                # troca virgula decimal por ponto, mas mantem hifens de negativos
                s = s.str.replace(",", ".", regex=False)
                df[c] = pd.to_numeric(s, errors="coerce")
            else:
                df[c] = pd.to_numeric(df[c], errors="coerce")
    # padroniza colunas booleanas/inteiras se existirem
    for c in ["feasible", "hit_optimal"]:
        if c in df.columns:
            df[c] = df[c].fillna(0).round().astype(int)
    return df

def read_clean(p: pathlib.Path) -> pd.DataFrame:
    # tenta utf-8 com BOM, cai para engine python se precisar
    try:
        df = pd.read_csv(p, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(p, engine="python")
    df = norm_cols(df)
    df = coerce_numeric(df)
    # items deve ser sempre string (evita medias indevidas)
    if "items" in df.columns:
        df["items"] = df["items"].astype(str)
    return df

def main():
    if not EXEC_ALL.exists() or not RESM_ALL.exists():
        raise SystemExit("Faltam *_ALL.csv. Rode antes: python scripts/rebuild_all.py")

    exec_all = read_clean(EXEC_ALL)
    resm_all = read_clean(RESM_ALL)

    # checagens minimas
    for name, df, req in [
        ("execucoes", exec_all, ["instance","variant","run","value","seconds"]),
        ("resumo"   , resm_all, ["instance","variant","best_value","best_seconds"]),
    ]:
        miss = [c for c in req if c not in df.columns]
        if miss:
            raise SystemExit(f"CSV {name} sem colunas: {miss}")

    # agrupa execucoes por (instancia, variante)
    g = exec_all.groupby(["instance","variant"], dropna=False)

    per_pair = g.agg(
        runs=("run","count"),
        mean_value=("value","mean"),
        best_value=("value","max"),
        mean_seconds=("seconds","mean"),
        std_seconds=("seconds","std")
    ).reset_index()

    # garante numerico pos-agg
    per_pair = coerce_numeric(per_pair)

    # se houver target no resumo, traz por instancia
    if "target" in resm_all.columns:
        targets = (resm_all[["instance","target"]]
                   .dropna(subset=["instance"])
                   .drop_duplicates("instance"))
        per_pair = per_pair.merge(targets, on="instance", how="left")
        # hit_optimal: best_value >= target (quando target existir)
        per_pair["hit_optimal"] = (
            (per_pair["best_value"] >= per_pair["target"])
            & per_pair["target"].notna()
        ).astype(int)
    else:
        per_pair["hit_optimal"] = 0

    # agregacao por variante
    by_variant = per_pair.groupby("variant", dropna=False).agg(
        pairs=("variant","count"),
        runs_total=("runs","sum"),
        mean_best_value=("best_value","mean"),
        mean_seconds=("mean_seconds","mean"),
        std_seconds=("std_seconds","mean"),
        hit_optimal_pct=("hit_optimal","mean"),
    ).reset_index()

    # ajustes finais
    by_variant["hit_optimal_pct"] = (by_variant["hit_optimal_pct"] * 100).round(2)

    OUT_SUM.parent.mkdir(parents=True, exist_ok=True)
    by_variant.to_csv(OUT_SUM, index=False, quoting=csv.QUOTE_MINIMAL)

    OUT_XLS.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUT_XLS, engine="xlsxwriter") as xw:
        per_pair.to_excel(xw, sheet_name="por_par", index=False)
        by_variant.to_excel(xw, sheet_name="por_variante", index=False)

    print("Resumo salvo em:")
    print(" -", OUT_SUM)
    print("Excel salvo em:")
    print(" -", OUT_XLS)

if __name__ == "__main__":
    main()
