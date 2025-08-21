# scripts/analyse_from_robust.py
# Analisa execucoes_robust.csv (clássicas + difíceis), higieniza e calcula estatísticas e "wins".

import sys
from pathlib import Path
import pandas as pd

def load_robust(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {csv_path}")

    # Carrega leve, deixando pandas decidir tipos; depois coercionamos o que precisa.
    df = pd.read_csv(csv_path)
    expected = {'instance','variant','run','seed','value','seconds','group'}
    missing = expected - set(map(str.lower, df.columns))
    if missing:
        # tenta normalizar nomes
        cols = {c.lower(): c for c in df.columns}
        if not missing.issubset(cols.keys()):
            raise ValueError(f"Colunas esperadas ausentes: {missing}. Colunas presentes: {df.columns.tolist()}")

        # renomeia para minúsculo
        df.columns = [c.lower() for c in df.columns]

    # Higienização: mantém apenas colunas-chave
    keep = ['instance','variant','run','seed','value','seconds','group']
    df = df[keep].copy()

    # Força numéricos (linhas inválidas viram NaN e serão descartadas)
    for col in ['value','seconds']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # run/seed: tenta coerção também (se não forem numéricos, tudo bem; só não usaremos conversão agressiva)
    for col in ['run','seed']:
        if col in df.columns:
            # não é essencial serem numéricos para o cálculo de "wins"
            pass

    # Remove linhas sem value ou seconds
    before = len(df)
    df = df.dropna(subset=['value','seconds'])
    after = len(df)
    print(f"→ removidas inválidas (sem value/seconds): {before - after} | linhas atuais: {after}")

    return df

def stats_by_group_variant(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(['group','variant'], as_index=False)
    out = g.agg(
        runs=('instance','count'),
        instances=('instance','nunique'),
        mean_value=('value','mean'),
        std_value=('value','std'),
        mean_seconds=('seconds','mean'),
        std_seconds=('seconds','std')
    )
    return out

def compute_wins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vencedor por (instance, seed, run) com tie‑break em seconds (menor).
    Depois conta vitórias por (group, variant).
    """
    idx = (
        df
        .groupby(['instance','seed','run'], dropna=False, as_index=False)
        .apply(lambda g: g.loc[
            # pega todas as linhas com value máximo
            g['value'].eq(g['value'].max())
        ].sort_values('seconds', ascending=True).index[0])
        .reset_index(drop=True)
    )

    winners = df.loc[idx, ['group','variant']]
    wins = winners.value_counts().rename('wins').reset_index()
    # value_counts em DataFrame com 2 colunas -> level_0->group, level_1->variant
    wins = wins.rename(columns={'index':'__drop__'})
    # Em versões mais novas, o reset_index acima já traz colunas corretas; garantindo:
    if '__drop__' in wins.columns:
        wins = wins.drop(columns='__drop__')
    if 'level_0' in wins.columns: wins = wins.rename(columns={'level_0':'group'})
    if 'level_1' in wins.columns: wins = wins.rename(columns={'level_1':'variant'})

    return wins

def main():
    # uso: python scripts/analyse_from_robust.py [caminho_csv]
    base = Path('results') / 'execucoes_robust.csv'
    if len(sys.argv) > 1:
        base = Path(sys.argv[1])

    print(f"==> Lendo {base.resolve()}")
    df = load_robust(base)

    # Cobertura por variante (instâncias únicas)
    cover = (
        df.groupby(['group','variant'])['instance']
          .nunique()
          .rename('unique_instances')
          .reset_index()
    )
    print("\n==> Cobertura por grupo/variante (instâncias únicas)")
    print(cover.to_string(index=False))

    # Estatísticas por grupo/variante
    stats = stats_by_group_variant(df)
    print("\n==> Estatísticas por grupo/variante")
    print(stats.to_string(index=False))

    # Wins
    print("\n==> Wins por variante (vencedor por instance/seed/run)")
    try:
        wins = compute_wins(df)
        print(wins.to_string(index=False))
    except Exception as e:
        print(f"[AVISO] Falhou ao computar wins: {e}")
        wins = None

    # Salva saídas
    outdir = Path('results') / 'analysis'
    outdir.mkdir(parents=True, exist_ok=True)
    stats.to_csv(outdir / 'classic_vs_difficult_summary.csv', index=False)
    cover.to_csv(outdir / 'coverage_summary.csv', index=False)
    if wins is not None:
        wins.to_csv(outdir / 'wins_by_variant.csv', index=False)

    print(f"\nArquivos salvos em: {outdir.resolve()}")

if __name__ == "__main__":
    main()
