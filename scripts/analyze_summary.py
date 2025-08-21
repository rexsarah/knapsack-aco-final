# -*- coding: utf-8 -*-
"""
Gera sumários e gráficos das execuções (clássicas + difíceis).

Entrada preferencial:
  results/jooken/execucoes_jooken_ALL.csv
Fallback:
  results/jooken/execucoes_jooken.csv

Saídas:
  - results/analysis/variant_summary.csv
  - results/analysis/instance_winners.csv
  - results/analysis/per_instance_best.csv
  - results/analysis/*.png (gráficos)
  - results/excel/analysis.xlsx (opcional, se openpyxl disponível)
"""

import pathlib
import math
import pandas as pd
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
IN_ALL = ROOT / "results" / "jooken" / "execucoes_jooken_ALL.csv"
IN_FALL = ROOT / "results" / "jooken" / "execucoes_jooken.csv"

OUT_DIR = ROOT / "results" / "analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_VARIANT = OUT_DIR / "variant_summary.csv"
OUT_WINNERS = OUT_DIR / "instance_winners.csv"
OUT_PERBEST = OUT_DIR / "per_instance_best.csv"

EXCEL_OUT  = ROOT / "results" / "excel" / "analysis.xlsx"

def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (df.columns.astype(str)
                    .str.replace('\ufeff','',regex=False)
                    .str.strip().str.lower())
    return df

def _to_num(s):
    if s.dtype == object:
        s = (s.astype(str).str.strip()
                     .str.replace(r"\s+","", regex=True)
                     .str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")

def load_data() -> pd.DataFrame:
    path = IN_ALL if IN_ALL.exists() else IN_FALL
    if not path.exists():
        raise SystemExit(f"Não encontrei CSV de entrada em {IN_ALL} nem {IN_FALL}.")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = _norm_cols(df)

    # coerção numérica de campos conhecidos
    for c in ["value","seconds","run","seed","hit_optimal","target"]:
        if c in df.columns:
            df[c] = _to_num(df[c])

    # chaves string
    for c in ["instance","variant"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    # saneamento de booleans
    if "hit_optimal" in df.columns:
        df["hit_optimal"] = df["hit_optimal"].fillna(0).round().astype(int)

    return df

def compute_summaries(df: pd.DataFrame):
    # métricas por (instance, variant)
    g = (df.groupby(["instance","variant"], dropna=False)
            .agg(
                runs=("run","count"),
                best_value=("value","max"),
                best_seconds=("seconds","min"),
                mean_seconds=("seconds","mean")
            )
            .reset_index())

    # quem vence por instância (maximização de value)
    per_inst = (g.groupby("instance", as_index=False)
                  .agg(max_value=("best_value","max")))

    winners = g.merge(per_inst, on="instance", how="left")
    winners["is_winner"] = (winners["best_value"] == winners["max_value"]).astype(int)

    # vitórias por variante (conta instâncias)
    wins = (winners[winners["is_winner"]==1]
              .groupby("variant").size()
              .rename("wins").reset_index())

    # instâncias cobertas por variante (quantas instâncias ela apareceu)
    inst_cover = (g.groupby("variant")["instance"]
                    .nunique()
                    .rename("instances")
                    .reset_index())

    # runs totais por variante
    runs_tot = (g.groupby("variant")["runs"].sum()
                  .rename("runs_total").reset_index())

    # média de best_value por variante (média no nível instância-variante)
    mean_best_val = (g.groupby("variant")["best_value"]
                       .mean().rename("mean_best_value").reset_index())

    # tempos: média por RUN (do df original) e média do melhor tempo (por (i,v))
    mean_seconds_run = (df.groupby("variant")["seconds"]
                          .mean().rename("mean_seconds_run").reset_index())
    mean_best_seconds = (g.groupby("variant")["best_seconds"]
                           .mean().rename("mean_best_seconds").reset_index())

    # hit_optimal %
    hit = None
    if "hit_optimal" in df.columns:
        hit = (df.groupby("variant")["hit_optimal"]
                 .mean().mul(100).rename("hit_optimal_pct").reset_index())
    elif "target" in df.columns:
        # considera hit se best_value >= target (nível (inst, var))
        tmp = g.copy()
        tmp = tmp.merge(df[["instance","target"]].dropna().drop_duplicates("instance"),
                        on="instance", how="left")
        tmp["hit_flag"] = (tmp["best_value"] >= tmp["target"]).astype(int)
        hit = (tmp.groupby("variant")["hit_flag"]
                 .mean().mul(100).rename("hit_optimal_pct").reset_index())

    # consolida
    variant_summary = (inst_cover
                       .merge(runs_tot, on="variant", how="left")
                       .merge(wins, on="variant", how="left")
                       .merge(mean_best_val, on="variant", how="left")
                       .merge(mean_seconds_run, on="variant", how="left")
                       .merge(mean_best_seconds, on="variant", how="left"))

    if hit is not None:
        variant_summary = variant_summary.merge(hit, on="variant", how="left")

    variant_summary["wins"] = variant_summary["wins"].fillna(0).astype(int)

    # vencedores por instância (se houver empates, lista variantes separadas por '|')
    inst_win_map = (winners[winners["is_winner"]==1]
                      .groupby("instance")["variant"]
                      .apply(lambda s: "|".join(sorted(map(str,set(s)))))
                      .rename("winner_variants")
                      .reset_index())

    return g, winners, variant_summary, inst_win_map

def save_tables(g, winners, variant_summary, inst_win_map):
    # por instância/variante (melhor valor/tempo)
    perbest = g.sort_values(["instance","variant"])
    perbest.to_csv(OUT_PERBEST, index=False, encoding="utf-8-sig")

    # por variante (sumário)
    vs = variant_summary.sort_values(["wins","mean_best_value"], ascending=[False,False])
    vs.to_csv(OUT_VARIANT, index=False, encoding="utf-8-sig")

    # vencedor por instância
    inst_win_map.to_csv(OUT_WINNERS, index=False, encoding="utf-8-sig")

def make_plots(df, g, variant_summary):
    # figure helper
    def savefig(path):
        plt.tight_layout()
        plt.savefig(path, dpi=160)
        plt.close()

    # 1) vitórias por variante
    ax = variant_summary.sort_values("wins", ascending=False).plot(
        x="variant", y="wins", kind="bar", legend=False)
    ax.set_title("Vitórias por variante (melhor valor por instância)")
    ax.set_xlabel("Variante")
    ax.set_ylabel("Vitórias (instâncias)")
    savefig(OUT_DIR / "wins_by_variant.png")

    # 2) média do melhor valor por variante
    ax = variant_summary.sort_values("mean_best_value", ascending=False).plot(
        x="variant", y="mean_best_value", kind="bar", legend=False)
    ax.set_title("Média do melhor valor por variante")
    ax.set_xlabel("Variante")
    ax.set_ylabel("Média do melhor valor (por instância)")
    savefig(OUT_DIR / "mean_best_value_by_variant.png")

    # 3) tempo médio por run (do CSV de execuções)
    ax = variant_summary.sort_values("mean_seconds_run").plot(
        x="variant", y="mean_seconds_run", kind="bar", legend=False, rot=0)
    ax.set_title("Tempo médio por run (segundos)")
    ax.set_xlabel("Variante")
    ax.set_ylabel("segundos (média por run)")
    savefig(OUT_DIR / "mean_seconds_run_by_variant.png")

    # 4) boxplot valores por variante (todas as execuções)
    # (se o conjunto for muito grande, pode levar alguns segundos)
    order = (df.groupby("variant")["value"].median()
               .sort_values(ascending=False).index.tolist())
    data = [df.loc[df["variant"]==v, "value"].dropna().values for v in order]
    plt.figure(figsize=(10,5))
    plt.boxplot(data, labels=order, showfliers=False)
    plt.title("Distribuição dos valores por variante (todas as execuções)")
    plt.xlabel("Variante")
    plt.ylabel("Valor")
    savefig(OUT_DIR / "value_boxplot_by_variant.png")

def maybe_write_excel(g, variant_summary, inst_win_map):
    try:
        import openpyxl  # noqa: F401
        EXCEL_OUT.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(EXCEL_OUT, engine="openpyxl", mode="w") as xw:
            variant_summary.to_excel(xw, sheet_name="variant_summary", index=False)
            g.to_excel(xw, sheet_name="per_instance_best", index=False)
            inst_win_map.to_excel(xw, sheet_name="instance_winners", index=False)
        print(f"[OK] Excel salvo em: {EXCEL_OUT}")
    except Exception as e:
        print(f"[INFO] Excel não gerado (openpyxl ausente ou outro motivo): {e}")

def main():
    print(">> Carregando dados...")
    df = load_data()

    print(">> Calculando sumários...")
    g, winners, variant_summary, inst_win_map = compute_summaries(df)

    print(">> Gravando tabelas...")
    save_tables(g, winners, variant_summary, inst_win_map)

    print(">> Gerando gráficos...")
    make_plots(df, g, variant_summary)

    print(">> (Opcional) Salvando Excel...")
    maybe_write_excel(g, variant_summary, inst_win_map)

    print("\nConcluído.")
    print(f"- Tabelas em: {OUT_DIR}")
    print(f"- Gráficos em: {OUT_DIR}")

if __name__ == "__main__":
    main()
