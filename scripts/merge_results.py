import os
import glob
import pandas as pd

REPO = os.path.dirname(os.path.dirname(__file__))
BASE = os.path.join(REPO, "results")   # agora busca em toda a pasta results

# procura todos CSVs que podem conter execuções
candidates = glob.glob(os.path.join(BASE, "**", "*.csv"), recursive=True)
candidates = [f for f in candidates if "execucoes" in os.path.basename(f).lower()]

print("==> Candidatos encontrados:")
for c in candidates:
    print(" -", c)

frames = []
for f in candidates:
    try:
        df = pd.read_csv(f)
        # só inclui se tiver colunas mínimas
        if "instance" in df.columns and "variant" in df.columns:
            frames.append(df)
            print(f"[OK] {f} ({len(df)} linhas)")
        else:
            print(f"[IGNORADO] {f} (colunas não compatíveis)")
    except Exception as e:
        print(f"[ERRO] {f}: {e}")

if frames:
    merged = pd.concat(frames, ignore_index=True)
    out = os.path.join(BASE, "execucoes_merged.csv")
    merged.to_csv(out, index=False)
    print(f"\n✅ Consolidado salvo em {out} com {len(merged)} linhas.")
    
    # checa se p01–p08 aparecem
    classics = [f"p0{i}" for i in range(1, 9)]
    found = merged["instance"].astype(str).str.contains("|".join(classics)).any()
    if found:
        print("\nClássicas detectadas no merged ✅")
    else:
        print("\n⚠️ Clássicas ainda não apareceram, revisar nomes de instancia.")
else:
    print("\n❌ Nenhum arquivo válido encontrado.")
