# scripts/analyse_from_merged.py
import os, pandas as pd, numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..", "results")
MERGED = os.path.join(BASE, "execucoes_merged.csv")

print("==> Lendo", MERGED)
df = pd.read_csv(MERGED, low_memory=False)

# define grupos
df["group"] = df["instance"].astype(str).apply(lambda s: "classic" if "\\data\\p0" in s.replace("/", "\\").lower() else "difficult")
df["variant"] = df["variant"].astype(str).str.strip()

# estatísticas por grupo/variante
stats = df.groupby(["group","variant"]).agg(
    runs=("instance","size"),
    instances=("instance","nunique"),
    mean_value=("value","mean"),
    std_value=("value","std"),
    mean_seconds=("seconds","mean"),
    std_seconds=("seconds","std"),
).reset_index()

# “wins” por instância: menor tempo (seconds) vence
def wins_per_instance(x: pd.DataFrame) -> pd.DataFrame:
    m = x.groupby("variant")["seconds"].mean()
    best = m.min()
    winners = m.index[m == best]
    return pd.DataFrame({"variant": winners, "wins": 1})

wins = (df.groupby(["group","instance"])
          .apply(wins_per_instance)
          .reset_index(level=[0,1], drop=False)
          .groupby(["group","variant"])["wins"]
          .sum()
          .reset_index())

summary = stats.merge(wins, how="left", on=["group","variant"])
summary["wins"] = summary["wins"].fillna(0).astype(int)

os.makedirs(os.path.join(BASE,"analysis"), exist_ok=True)
out = os.path.join(BASE,"analysis","classic_vs_difficult_summary.csv")
summary.sort_values(["group","variant"]).to_csv(out, index=False)
print("\nResumo salvo em:", out)
print(summary.sort_values(["group","variant"]).to_string(index=False))
