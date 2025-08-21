# scripts/fix_merge.py
import os, pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "results")
MERGED = os.path.join(BASE, "execucoes_merged.csv")

# arquivos de origem
classic_file = os.path.join(BASE, "execucoes_p01_p08.csv")
difficult_file = os.path.join(BASE, "jo0ken", "execucoes_jo0ken.csv")

print("==> Lendo arquivos...")
df_classic = pd.read_csv(classic_file, low_memory=False) if os.path.exists(classic_file) else pd.DataFrame()
df_difficult = pd.read_csv(difficult_file, low_memory=False) if os.path.exists(difficult_file) else pd.DataFrame()

print("Clássicas:", len(df_classic))
print("Difíceis:", len(df_difficult))

# concatena
df = pd.concat([df_classic, df_difficult], ignore_index=True)

# remove duplicatas
before = len(df)
df = df.drop_duplicates(subset=["instance","variant","run","seed"])
after = len(df)

print(f"Linhas antes: {before}, depois de remover duplicatas: {after}")

# define grupos
df["group"] = df["instance"].astype(str).apply(
    lambda s: "classic" if "p0" in s.lower() else "difficult"
)

# salva corrigido
out = os.path.join(BASE, "execucoes_fixed.csv")
df.to_csv(out, index=False)
print("Arquivo corrigido salvo em:", out)

# verificação das clássicas
classics = [f"p0{i}.txt" for i in range(1,9)]
present = [c for c in classics if any(df["instance"].astype(str).str.endswith(c))]
missing = [c for c in classics if c not in present]
print("\nClássicas presentes:", present)
print("Clássicas faltando:", missing or "nenhuma")
