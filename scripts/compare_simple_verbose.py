#!/usr/bin/env python3
"""
Versão VERBOSE (robusta a BOM e espaços) do gráfico comparativo simples.

- Remove BOM/espacos dos nomes de colunas e faz match case-insensitive.
- Se não detectar colunas, lista as disponíveis e as numéricas.

Exemplo:
  python compare_simple_verbose.py \
    --input .\results\validation\summary.csv \
    --output .\figs\comparativo_summary_bestvalue.png \
    --group-col variant --metric-col mean_best_value --no-filter-instance --sep ";"
"""

import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt

def sanitize_columns(df):
    clean = []
    for c in df.columns:
        s = str(c).replace("\ufeff", "").strip()  # remove BOM + espaços
        clean.append(s)
    df.columns = clean
    return df

def resolve_col_name(df, user_name):
    """Resolve nome de coluna por match case-insensitive após sanitização."""
    if user_name is None:
        return None
    target = user_name.strip().lower()
    for c in df.columns:
        if c.lower() == target:
            return c
    return None

def autodetect_columns(df):
    lower = {c.lower(): c for c in df.columns}
    def pick(cands):
        for c in cands:
            if c in lower: return lower[c]
        return None

    group_col = pick(["algorithm","algoritmo","algo","variant","variante"])
    inst_col  = pick(["instance","instancia","instância"])
    metric_col = pick(["mean_best_value","mean","avg","valor","value","score","best_value","media","média"])

    if metric_col is None:
        numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        metric_col = numeric[0] if numeric else None
    return group_col, inst_col, metric_col

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--group-col", default=None)
    ap.add_argument("--metric-col", default=None)
    ap.add_argument("--instance-col", default=None)
    ap.add_argument("--no-filter-instance", action="store_true")
    ap.add_argument("--sep", default=None)
    args = ap.parse_args()

    # Load CSV (tentativa com sep indicado; fallback ; )
    try:
        df = pd.read_csv(args.input) if not args.sep else pd.read_csv(args.input, sep=args.sep)
    except Exception:
        df = pd.read_csv(args.input, sep=";")

    # Sanitize BOM/espacos dos nomes
    df = sanitize_columns(df)

    # Autodetect + resolver nomes informados pelo usuário (case-insensitive)
    auto_group, auto_inst, auto_metric = autodetect_columns(df)
    group_col  = resolve_col_name(df, args.group_col)  or auto_group
    inst_col   = resolve_col_name(df, args.instance_col) or auto_inst
    metric_col = resolve_col_name(df, args.metric_col) or auto_metric

    # Verbose: mostrar mapeamento
    print("[cols]", list(df.columns))
    print(f"[map] group_col={group_col}  metric_col={metric_col}  instance_col={inst_col}")

    if group_col is None or metric_col is None:
        print("❌ Não foi possível detectar colunas de agrupamento e/ou métrica.")
        numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        print("Colunas numéricas candidatas a --metric-col:", numeric)
        raise SystemExit("➡️  Informe --group-col e --metric-col (confira nomes acima).")

    plot_df = df.copy()
    title_suffix = ""
    if (not args.no_filter_instance) and inst_col and inst_col in plot_df.columns:
        first_inst = str(plot_df[inst_col].iloc[0])
        plot_df = plot_df[plot_df[inst_col] == first_inst]
        title_suffix = f" — instância {first_inst}"

    # Agrupar e plotar
    agg = (plot_df.groupby(group_col, as_index=False)[metric_col]
           .mean()
           .sort_values(metric_col, ascending=False))

    plt.figure()
    plt.bar(agg[group_col].astype(str), agg[metric_col].values)
    plt.title(f"Gráfico comparativo simples{title_suffix}")
    plt.xlabel(group_col)
    plt.ylabel(metric_col)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    plt.savefig(args.output, dpi=150)
    print(f"✅ Gráfico salvo em: {args.output}")

if __name__ == "__main__":
    main()
