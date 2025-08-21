# -*- coding: utf-8 -*-
"""
Comparação entre instâncias clássicas (p01–p08) e difíceis (NMGE Jooken),
com checagens verbosas e estatísticas por grupo e variante.
"""

import sys
import pathlib
import pandas as pd
import os

ROOT = pathlib.Path(__file__).resolve().parents[1]
CANDIDATE_PATHS = [
    ROOT / "results" / "jooken" / "execucoes_jooken_ALL.csv",
    ROOT / "results" / "jooken" / "execucoes_jooken.csv",   # fallback
]

OUT_DIR = ROOT / "results" / "analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def find_csv():
    print("==> Procurando arquivo de execuções…")
    for p in CANDIDATE_PATHS:
        print(f"   - checando {p}")
        if p.exists():
            print(f"   ✔ encontrado: {p}")
            return p
    print("   ✖ Nenhum CSV de execuções encontrado nos caminhos conhecidos.")
    print("     Dica: rode 'python scripts/rebuild_all.py' para gerar *_ALL.csv")
    sys.exit(1)

def detect_columns(df: pd.DataFrame):
    cols = {c.lower(): c for c in df.columns}
    col_instance = cols.get("instance")
    col_variant  = cols.get("variant")
    col_run      = cols.get("run", None)
    col_seed     = cols.get("seed", None)
    col_value    = cols.get("best_value") or cols.get("value") or None
    col_seconds  = cols.get("seconds") or cols.get("mean_seconds") or None
    col_target   = cols.get("target") or None

    needed = [("instance", col_instance), ("variant", col_variant)]
    missing = [n for n,c in needed if c is None]
    if missing:
        print("✖ Colunas obrigatórias ausentes:", ", ".join(missing))
        sys.exit(1)

    print("==> Colunas detectadas:")
    print("   instance :", col_instance)
    print("   variant  :", col_variant)
    print("   run      :", col_run)
    print("   seed     :", col_seed)
    print("   value    :", col_value)
    print("   seconds  :", col_seconds)
    print("   target   :", col_target)

    return dict(
        instance=col_instance, variant=col_variant, run=col_run, seed=col_seed,
        value=col_value, seconds=col_seconds, target=col_target
    )

def basename_no_ext(path_str: str) -> str:
    """
    Extrai somente o nome do arquivo sem extensão, mesmo vindo caminho completo.
    Ex.: 'C:\\...\\data\\p01.txt' -> 'p01'
    Ex.: '/.../jooken/dificil/.../test.in' -> 'test'
    """
    try:
        base = os.path.basename(str(path_str))
        name, _ext = os.path.splitext(base)
        return name
    except Exception:
        return str(path_str)

def classify_group(row, col_instance):
    """
    Usa o caminho completo para detectar 'difficult' (pasta jooken/dificil)
    e o basename para detectar 'classic' (p01..p08).
    """
    inst_full = str(row[col_instance])
    inst_base = basename_no_ext(inst_full).lower()

    # clássicas
    classic_names = {f"p0{i}" for i in range(1,9)}
    if inst_base in classic_names:
        return "classic"

    # difíceis (pela pasta/segmento do caminho)
    full_lower = inst_full.replace("\\", "/").lower()
    if "/jooken/dificil/" in full_lower:
        return "difficult"

    # fallback
    return "other"

def main():
    print("==> Iniciando análise clássicas vs difíceis")
    csv_path = find_csv()

    print("==> Carregando CSV… (low_memory=False)")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"   linhas: {len(df):,}  |  colunas: {len(df.columns)}")

    df.columns = [c.strip() for c in df.columns]
    cols_map = detect_columns(df)

    # cria coluna group usando caminho + basename
    df["group"] = df.apply(lambda r: classify_group(r, cols_map["instance"]), axis=1)

    # checa clássicas obrigatórias
    classic_expected = {f"p0{i}" for i in range(1,9)}
    # extrai basenames das clássicas detectadas
    classic_found = {
        basename_no_ext(x).lower()
        for x in df.loc[df["group"]=="classic", cols_map["instance"]].unique()
    }
    missing_classics = sorted(list(classic_expected - classic_found))
    if missing_classics:
        print("⚠️  Instâncias clássicas faltando:", missing_classics)
        (OUT_DIR / "missing_classics.txt").write_text("\n".join(missing_classics), encoding="utf-8")
    else:
        print("✅ Todas as instâncias clássicas (p01–p08) foram encontradas.")

    have_value   = cols_map["value"]   is not None and cols_map["value"]   in df.columns
    have_seconds = cols_map["seconds"] is not None and cols_map["seconds"] in df.columns
    have_target  = cols_map["target"]  is not None and cols_map["target"]  in df.columns

    if have_value:
        df[cols_map["value"]] = pd.to_numeric(df[cols_map["value"]], errors="coerce")
    if have_seconds:
        df[cols_map["seconds"]] = pd.to_numeric(df[cols_map["seconds"]], errors="coerce")
    if have_target:
        df[cols_map["target"]] = pd.to_numeric(df[cols_map["target"]], errors="coerce")

    agg_dict = {"runs": (cols_map["variant"], "count")}
    if have_value:
        agg_dict.update({
            "mean_value": (cols_map["value"], "mean"),
            "std_value":  (cols_map["value"], "std"),
            "best_value": (cols_map["value"], "max"),
        })
    if have_seconds:
        agg_dict.update({
            "mean_seconds": (cols_map["seconds"], "mean"),
            "std_seconds":  (cols_map["seconds"], "std"),
        })

    stats = (df
             .groupby(["group", cols_map["variant"]], dropna=False)
             .agg(**agg_dict)
             .reset_index()
             .rename(columns={cols_map["variant"]: "variant"}))

    if have_target and have_value:
        df["_hit"] = (df[cols_map["value"]] >= df[cols_map["target"]]).astype("float")
        hit = (df.groupby(["group", cols_map["variant"]])["_hit"].mean()
                 .reset_index()
                 .rename(columns={cols_map["variant"]: "variant", "_hit": "hit_optimal_pct"}))
        hit["hit_optimal_pct"] = (hit["hit_optimal_pct"]*100).round(2)
        stats = stats.merge(hit, on=["group","variant"], how="left")
    else:
        stats["hit_optimal_pct"] = None

    stats = stats.sort_values(["group","variant"]).reset_index(drop=True)

    out_csv = OUT_DIR / "classic_vs_difficult.csv"
    stats.to_csv(out_csv, index=False, encoding="utf-8")
    print("\n==> Estatísticas por grupo/variante salvas em:")
    print(f"   {out_csv}")

    # contagem por grupo para conferência
    counts = df["group"].value_counts(dropna=False)
    (OUT_DIR / "group_counts.txt").write_text(counts.to_string(), encoding="utf-8")
    print("\n==> Contagem por grupo (salvo em group_counts.txt):")
    print(counts.to_string())

    print("\n--- Preview (top 12):")
    print(stats.head(12).to_string(index=False))

    (OUT_DIR / "sample_head.csv").write_text(
        df.head(20).to_csv(index=False), encoding="utf-8"
    )
    print(f"\n(amostra do CSV original salva em {OUT_DIR/'sample_head.csv'})")

if __name__ == "__main__":
    main()
