# scripts/check_quick.py
import pandas as pd
from pathlib import Path

E = Path("results/jooken/execucoes_jooken_ALL.csv")
R = Path("results/jooken/resumo_jooken_ALL.csv")

def must_exist(p: Path):
    if not p.exists():
        raise SystemExit(f"nao encontrado: {p}")

def main():
    must_exist(E); must_exist(R)
    e = pd.read_csv(E)
    r = pd.read_csv(R)

    print("Execucoes - instancias distintas:", e['instance'].nunique())
    print("Resumo    - instancias distintas:", r['instance'].nunique())
    print("Execucoes - variantes:", sorted(map(str, e['variant'].unique())))
    print("Resumo    - variantes:", sorted(map(str, r['variant'].unique())))

    # Se tem coluna 'seed', o ALL junta 2 seeds -> espera 40 exec por (instancia, variante)
    expected = 40 if 'seed' in [c.lower() for c in e.columns] else 20
    counts = e.groupby(['instance','variant'])['run'].count()
    bad = counts[counts != expected]
    if len(bad):
        print(f"\nATENCAO: pares (instancia, variante) com contagem != {expected}")
        print(bad.sort_values())
    else:
        print(f"\nOK: todas as (instancia, variante) tem {expected} execucoes.")

    viol = e[(e['feasible'] == 1) & (e['weight'] <= 0)]
    print("\nExecucoes marcadas como factiveis com weight<=0:", len(viol))

    s = r.groupby('variant')['hit_optimal'].mean()
    if len(s)==0:
        print("\nHit_optimal medio por variante: (vazio)")
    else:
        print("\nHit_optimal medio por variante (%):")
        print((s*100).round(2).astype(str) + "%")

if __name__ == "__main__":
    main()
