#!/usr/bin/env python3
"""
generate_summary_triplet.py
--------------------------------
Gera três gráficos comparativos de uma vez a partir de um CSV-Resumo:

1) mean_best_value  (valor final médio)
2) mean_seconds     (tempo médio em segundos)
3) hit_optimal_pct  (% de execuções que atingiram o ótimo)

Recursos:
- Detecção automática de delimitador ("," ou ";") e UTF-8 com/sem BOM.
- Normaliza nomes de colunas (remove BOM/ espaços) e faz match case-insensitive.
- Aceita parâmetros para forçar nomes de colunas e métricas.
- Salva também um CSV agregado com os valores usados para cada gráfico.

Uso (exemplo):
  python generate_summary_triplet.py ^
    --input .\results\validation\summary.csv ^
    --outdir .\figs ^
    --group-col variant

Parâmetros:
  --input            Caminho do CSV de entrada
  --outdir           Pasta de saída (será criada)
  --group-col        Coluna de agrupamento (ex.: variant, algorithm)
  --metrics          Lista separada por vírgula (default: mean_best_value,mean_seconds,hit_optimal_pct)
  --delimiter        Força delimitador ("," ou ";") [opcional]
"""

import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt

DEFAULT_METRICS = ["mean_best_value", "mean_seconds", "hit_optimal_pct"]

def sanitize_columns(df):
    clean = []
    for c in df.columns:
        s = str(c).replace("\ufeff", "").strip()
        clean.append(s)
    df.columns = clean
    return df

def resolve_col_name(df, user_name):
    """Resolve nome de coluna por match case-insensitive, tolerando espaços/sublinhados."""
    if user_name is None:
        return None
    target = str(user_name).strip().lower()
    for c in df.columns:
        if c.lower() == target:
            return c
    t2 = target.replace(" ", "").replace("_", "")
    for c in df.columns:
        c2 = c.lower().replace(" ", "").replace("_", "")
        if c2 == t2:
            return c
    return None

def load_df(path, delimiter=None):
    if delimiter:
        try:
            return pd.read_csv(path, sep=delimiter, encoding="utf-8-sig"), delimiter
        except Exception:
            pass
    # auto-infer
    try:
        return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig"), "auto"
    except Exception:
        pass
    # fallback ,
    try:
        return pd.read_csv(path, sep=",", encoding="utf-8-sig"), ","
    except Exception:
        pass
    # fallback ;
    return pd.read_csv(path, sep=";", encoding="utf-8-sig"), ";"

def ensure_numeric(df, col):
    df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def plot_bar(agg, group_col, metric_col, out_png, title):
    plt.figure()
    plt.bar(agg[group_col].astype(str), agg[metric_col].values)
    plt.title(title)
    plt.xlabel(group_col)
    plt.ylabel(metric_col)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    plt.savefig(out_png, dpi=150)
    plt.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--group-col", required=True)
    ap.add_argument("--metrics", default=",".join(DEFAULT_METRICS))
    ap.add_argument("--delimiter", default=None)
    args = ap.parse_args()

    df, used_sep = load_df(args.input, args.delimiter)
    df = sanitize_columns(df)

    group_col = resolve_col_name(df, args.group_col)
    if group_col is None:
        raise SystemExit(f"Coluna de agrupamento não encontrada: '{args.group_col}'. "
                         f"Disponíveis: {list(df.columns)}")

    metrics = [m.strip() for m in args.metrics.split(",") if m.strip()]
    found_any = False

    # Saída agregada em CSV (um por métrica)
    os.makedirs(args.outdir, exist_ok=True)

    print(f"[info] delimiter usado: {used_sep}")
    print("[cols]", list(df.columns))
    print(f"[map] group_col={group_col}")
    print(f"[run] metrics={metrics}")

    for m in metrics:
        metric_col = resolve_col_name(df, m)
        if metric_col is None:
            print(f"⚠️  Métrica '{m}' não encontrada — ignorando.")
            continue

        ensure_numeric(df, metric_col)
        agg = (df.groupby(group_col, as_index=False)[metric_col]
                 .mean()
                 .sort_values(metric_col, ascending=False))

        # salva CSV agregado da métrica
        out_csv = os.path.join(args.outdir, f"agg_{metric_col}.csv")
        agg.to_csv(out_csv, index=False)

        # plota
        title = f"Comparativo — {metric_col}"
        out_png = os.path.join(args.outdir, f"comparativo_{metric_col}.png")
        plot_bar(agg, group_col, metric_col, out_png, title)

        print(f"✅ OK: {metric_col}  ->  {out_png}")
        found_any = True

    if not found_any:
        raise SystemExit("❌ Nenhuma métrica válida encontrada. Revise os nomes em --metrics ou o cabeçalho do CSV.")

if __name__ == "__main__":
    main()
