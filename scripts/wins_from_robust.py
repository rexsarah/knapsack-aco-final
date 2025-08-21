# scripts/wins_from_robust.py
# Calcula "wins" por variante (e por grupo), escolhendo o MAIOR 'value'
# em cada chave (instance[, seed][, run]). Empate dividido proporcionalmente.
# Uso:
#   python scripts/wins_from_robust.py                # usa results/execucoes_robust.csv
#   python scripts/wins_from_robust.py results\X.csv  # ou informe um CSV qualquer compatível

from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

def main():
    # 1) Resolver caminho do CSV
    csv = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results") / "execucoes_robust.csv"

    # Fallbacks úteis se o robusto ainda não existir
    if not csv.exists():
        for alt in [
            Path("results") / "execucoes_robust.csv",
            Path("results") / "execucoes_merged.csv",
            Path("results") / "jooken" / "execucoes_jooken_ALL.csv",
            Path("results") / "jooken" / "execucoes_jooken.csv",
        ]:
            if alt.exists():
                csv = alt
                break

    if not csv.exists():
        raise FileNotFoundError(
            f"CSV não encontrado. Rode antes: python scripts\\merge_any_results.py\n"
            f"Procurado em: {csv}"
        )

    print(f"==> Lendo {csv}")
    df = pd.read_csv(csv, low_memory=False)

    # 2) Normalizações básicas
    # tenta garantir numéricos (ignora lixo sem quebrar)
    for col in ("value", "seconds"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Se houver alguma coluna "best_value"/"feasible", ignore; usamos 'value'.
    # Remove linhas inválidas (sem value/seconds)
    if "value" in df.columns:
        df = df.dropna(subset=["value"])
    if "seconds" in df.columns:
        df = df.dropna(subset=["seconds"])

    # 3) Descobrir chaves de grupo (instance / seed / run) disponíveis
    key_cols = [c for c in ["instance", "seed", "run"] if c in df.columns]
    if "instance" not in key_cols:
        # sem 'instance' não dá para computar wins
        raise ValueError("Coluna 'instance' ausente no CSV; não é possível calcular wins.")

    # 4) Selecionar vencedores por chave (maior 'value'), com desempate justo
    # max value por chave
    max_by_key = df.groupby(key_cols)["value"].transform("max")
    winners = df[df["value"] == max_by_key].copy()

    # fraciona o ponto quando há empate
    winners["share"] = 1.0 / winners.groupby(key_cols)["variant"].transform("count")

    # 5) Agregações por variante e por grupo (se existir)
    if "group" not in df.columns:
        # se não existir 'group', cria como 'other' para não quebrar
        winners["group"] = "other"

    wins_by_variant = (
        winners.groupby(["variant"], as_index=False)["share"]
        .sum()
        .rename(columns={"share": "wins"})
        .sort_values("wins", ascending=False)
    )

    wins_by_group_variant = (
        winners.groupby(["group", "variant"], as_index=False)["share"]
        .sum()
        .rename(columns={"share": "wins"})
        .sort_values(["group", "wins"], ascending=[True, False])
    )

    # 6) Salvar saídas
    out_dir = Path("results") / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    out1 = out_dir / "wins_por_variante.csv"
    out2 = out_dir / "wins_por_grupo_e_variante.csv"

    wins_by_variant.to_csv(out1, index=False)
    wins_by_group_variant.to_csv(out2, index=False)

    # 7) Resumo no console
    print("\n==> Wins por variante")
    print(wins_by_variant.to_string(index=False))

    print("\n==> Wins por grupo e variante")
    print(wins_by_group_variant.to_string(index=False))

    print(f"\nArquivos salvos em:\n - {out1}\n - {out2}")

if __name__ == "__main__":
    main()
