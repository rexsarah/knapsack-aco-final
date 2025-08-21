# scripts/quick_check_merged.py
import os, pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "results")
MERGED = os.path.join(BASE, "execucoes_merged.csv")

print("==> Lendo", MERGED)
df = pd.read_csv(MERGED, low_memory=False)
for col in ["instance","variant","run","seed","seconds","value"]:
    if col not in df.columns:
        raise SystemExit(f"[ERRO] Coluna ausente: {col}")

# Normaliza nomes básicos
df["group"] = df["instance"].astype(str).apply(lambda s: "classic" if "\\data\\p0" in s.replace("/", "\\").lower() else "difficult")
df["variant"] = df["variant"].astype(str).str.strip()

print("\nTamanho:", len(df))
print("Grupos:", df["group"].value_counts().to_dict())
print("Variantes:", df["variant"].value_counts().to_dict())

# (instance, variant) pares únicos
pairs = df[["instance","variant"]].drop_duplicates()
print("\nPares únicos (instance,variant):", len(pairs))

# Cobertura por variante em cada grupo
cov = df.groupby(["group","variant"])["instance"].nunique().reset_index(name="unique_instances")
print("\nCobertura por grupo/variante (instâncias únicas):")
print(cov.sort_values(["group","variant"]).to_string(index=False))

# Duplicatas (mesma instância, variante, run, seed)
dups = df.duplicated(subset=["instance","variant","run","seed"]).sum()
print("\nDuplicatas (instance,variant,run,seed):", dups)

# Resumo por grupo
agg = df.groupby(["group","variant"]).agg(
    runs=("instance","size"),
    instancias=("instance","nunique"),
    media_seg=("seconds","mean"),
    desvio_seg=("seconds","std"),
    media_val=("value","mean"),
    desvio_val=("value","std"),
).reset_index()
out = os.path.join(BASE, "analysis", "merged_quick_summary.csv")
os.makedirs(os.path.dirname(out), exist_ok=True)
agg.to_csv(out, index=False)
print("\nResumo salvo em:", out)

# Checagem das 8 clássicas
classics = [f"p0{i}.txt" for i in range(1,9)]
present = [c for c in classics if any(df["instance"].astype(str).str.endswith(c))]
missing = [c for c in classics if c not in present]
print("\nClássicas presentes:", present)
print("Clássicas faltando:", missing or "nenhuma")
