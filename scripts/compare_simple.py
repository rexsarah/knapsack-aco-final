#!/usr/bin/env python3
"""
Gera um gráfico comparativo simples a partir de um CSV.

- Detecta automaticamente colunas de grupo (algorithm/variant) e de instância, e uma coluna métrica numérica.
- Por padrão, se houver "instance", filtra para a primeira instância encontrada (pode desativar via flag).
- Uso básico:
    python compare_simple.py --input /caminho/para.csv --output figs/comparativo.png
Parâmetros (opcionais):
    --group-col NOME_COLUNA      # força a coluna de agrupamento
    --metric-col NOME_COLUNA     # força a coluna de métrica
    --instance-col NOME_COLUNA   # força a coluna de instância
    --no-filter-instance         # não filtra para a primeira instância (agrega todas)
    --sep ";"                    # separador do CSV (padrão auto)
"""
import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt

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

    try:
        df = pd.read_csv(args.input) if not args.sep else pd.read_csv(args.input, sep=args.sep)
    except Exception:
        df = pd.read_csv(args.input, sep=";")

    auto_group, auto_inst, auto_metric = autodetect_columns(df)
    group_col = args.group_col or auto_group
    inst_col  = args.instance_col or auto_inst
    metric_col= args.metric_col or auto_metric

    if group_col is None or metric_col is None:
        raise SystemExit("Não foi possível detectar colunas de agrupamento e/ou métrica. Use --group-col e --metric-col.")

    plot_df = df.copy()
    title_suffix = ""
    if (not args.no_filter_instance) and inst_col and inst_col in plot_df.columns:
        first_inst = str(plot_df[inst_col].iloc[0])
        plot_df = plot_df[plot_df[inst_col]==first_inst]
        title_suffix = f" — instância {first_inst}"

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
    print(f"Salvo em: {args.output}")

if __name__ == "__main__":
    main()
