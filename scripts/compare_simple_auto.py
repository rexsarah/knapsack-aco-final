#!/usr/bin/env python3
"""
compare_simple_auto.py
----------------------
Gera um gráfico comparativo simples a partir de um CSV,
com **detecção automática de delimitador** e nomes de colunas robustos (BOM/espacos).

Exemplos:
  python compare_simple_auto.py --input results/validation/summary.csv \
    --output figs/comparativo_summary_bestvalue.png \
    --group-col variant --metric-col mean_best_value

  # Se quiser forçar delimitador:
  python compare_simple_auto.py --input ... --output ... \
    --group-col variant --metric-col mean_seconds --delimiter ";"

Parâmetros:
  --input            Caminho do CSV
  --output           Caminho do PNG a salvar
  --group-col        Nome da coluna de agrupamento (ex.: variant, algorithm)
  --metric-col       Nome da coluna métrica (ex.: mean_best_value, mean_seconds, hit_optimal_pct)
  --instance-col     (opcional) Nome da coluna de instância
  --no-filter-instance  (flag) Não filtrar pra primeira instância
  --delimiter        (opcional) Força delimitador ("," ou ";")
"""

import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt

def sanitize_columns(df):
    clean = []
    for c in df.columns:
        s = str(c).replace("\ufeff", "").strip()
        clean.append(s)
    df.columns = clean
    return df

def resolve_col_name(df, user_name):
    if user_name is None:
        return None
    target = str(user_name).strip().lower()
    for c in df.columns:
        if c.lower() == target:
            return c
    # tentativa relaxada: remover espaços e sublinhados
    t2 = target.replace(" ", "").replace("_", "")
    for c in df.columns:
        c2 = c.lower().replace(" ", "").replace("_", "")
        if c2 == t2:
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

def load_df(path, delimiter=None):
    # Tenta detectar automaticamente o delimitador quando não for informado.
    if delimiter:
        try:
            df = pd.read_csv(path, sep=delimiter, encoding="utf-8-sig")
            return df, delimiter
        except Exception:
            pass

    # Tentativa 1: auto-infer (sep=None) com engine=python
    try:
        df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
        return df, "auto"
    except Exception:
        pass

    # Tentativa 2: vírgula
    try:
        df = pd.read_csv(path, sep=",", encoding="utf-8-sig")
        return df, ","
    except Exception:
        pass

    # Tentativa 3: ponto-e-vírgula
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    return df, ";"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--group-col", default=None)
    ap.add_argument("--metric-col", default=None)
    ap.add_argument("--instance-col", default=None)
    ap.add_argument("--no-filter-instance", action="store_true")
    ap.add_argument("--delimiter", default=None)
    args = ap.parse_args()

    df, used_sep = load_df(args.input, args.delimiter)
    df = sanitize_columns(df)

    auto_group, auto_inst, auto_metric = autodetect_columns(df)
    group_col  = resolve_col_name(df, args.group_col)  or auto_group
    inst_col   = resolve_col_name(df, args.instance_col) or auto_inst
    metric_col = resolve_col_name(df, args.metric_col) or auto_metric

    print(f"[info] delimiter usado: {used_sep}")
    print("[cols]", list(df.columns))
    print(f"[map] group_col={group_col}  metric_col={metric_col}  instance_col={inst_col}")

    if group_col is None or metric_col is None:
        numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        print("❌ Não foi possível detectar colunas de agrupamento e/ou métrica.")
        print("Colunas numéricas candidatas a --metric-col:", numeric)
        raise SystemExit("➡️  Informe --group-col e --metric-col (veja [cols] acima).")

    # Coagir métrica para numérico (caso venha como string)
    df[metric_col] = pd.to_numeric(df[metric_col], errors="coerce")

    plot_df = df.copy()
    title_suffix = ""
    if (not args.no_filter_instance) and inst_col and inst_col in plot_df.columns:
        first_inst = str(plot_df[inst_col].iloc[0])
        plot_df = plot_df[plot_df[inst_col] == first_inst]
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
    print(f"✅ Gráfico salvo em: {args.output}")

if __name__ == "__main__":
    main()
