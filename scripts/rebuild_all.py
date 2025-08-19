# -*- coding: utf-8 -*-
"""
Reconstrói os *_ALL.csv a partir de qualquer batch em results/jooken/batches/**.
Aceita variações de nomes: execucoes.csv ou execucoes_jooken.csv; resumo.csv ou resumo_jooken.csv.
Gera:
 - results/jooken/execucoes_jooken_ALL.csv
 - results/jooken/resumo_jooken_ALL.csv
"""

import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH_DIR = ROOT / "results" / "jooken" / "batches"
OUT_EXEC_ALL = ROOT / "results" / "jooken" / "execucoes_jooken_ALL.csv"
OUT_RESM_ALL = ROOT / "results" / "jooken" / "resumo_jooken_ALL.csv"

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
    to_rename = {k:v for k,v in RENAME.items() if k in df.columns}
    if to_rename:
        df.rename(columns=to_rename, inplace=True)
    # normaliza chaves
    for k in ["instance","variant"]:
        if k in df.columns:
            df[k] = df[k].astype(str).str.strip()
    # itens sempre texto
    if "items" in df.columns:
        df["items"] = df["items"].astype(str)
    return df

def read_csv_flex(p: pathlib.Path) -> pd.DataFrame:
    try:
        return pd.read_csv(p, encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(p, engine="python")

def add_context_columns(df: pd.DataFrame, path: pathlib.Path) -> pd.DataFrame:
    # tenta extrair seed e timestamp usando a estrutura .../batches/seedNNNNN/AAAAmmdd_HHMMSS/arquivo.csv
    seed = ""
    stamp = ""
    parts = [x.name for x in path.parents]
    # parents[0] = pasta do arquivo, parents[1] = timestamp, parents[2] = seed12345 (em geral)
    if len(parts) >= 3:
        stamp = parts[1]
        seed_part = parts[2]
        if seed_part.lower().startswith("seed"):
            seed = ''.join([c for c in seed_part if c.isdigit()])
    if "seed" not in df.columns:
        df["seed"] = seed
    if "batch" not in df.columns:
        df["batch"] = stamp
    return df

def concat_kind(patterns):
    files = []
    for pat in patterns:
        files += list(BATCH_DIR.rglob(pat))
    dfs = []
    for f in files:
        try:
            df = read_csv_flex(f)
            df = norm_cols(df)
            df = add_context_columns(df, f)
            dfs.append(df)
        except Exception as e:
            print(f"[WARN] Falha lendo {f}: {e}")
    if not dfs:
        return pd.DataFrame(), files
    out = pd.concat(dfs, ignore_index=True, sort=False)
    return out, files

def main():
    if not BATCH_DIR.exists():
        print(f"[WARN] Pasta não existe: {BATCH_DIR}")
        return

    exec_df, exec_files = concat_kind(["execucoes.csv", "execucoes_jooken.csv"])
    resm_df, resm_files = concat_kind(["resumo.csv", "resumo_jooken.csv"])

    if len(exec_files) == 0:
        print("[WARN] Nenhum CSV de execuções encontrado.")
    if len(resm_files) == 0:
        print("[WARN] Nenhum CSV de resumo encontrado.")

    if len(exec_files) == 0 and len(resm_files) == 0:
        return

    OUT_EXEC_ALL.parent.mkdir(parents=True, exist_ok=True)

    if not exec_df.empty:
        exec_df.to_csv(OUT_EXEC_ALL, index=False)
        print(f"[OK] execucoes ALL -> {OUT_EXEC_ALL}  (linhas: {len(exec_df)})")

    if not resm_df.empty:
        resm_df.to_csv(OUT_RESM_ALL, index=False)
        print(f"[OK] resumo ALL    -> {OUT_RESM_ALL}  (linhas: {len(resm_df)})")

    # feedback útil
    if exec_files:
        print("Arquivos de execuções considerados:")
        for p in exec_files:
            print(" -", p)
    if resm_files:
        print("Arquivos de resumo considerados:")
        for p in resm_files:
            print(" -", p)

if __name__ == "__main__":
    main()
