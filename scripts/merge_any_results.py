# scripts/merge_any_results.py
# Consolida quaisquer CSVs de execuções em results/ e gera results/execucoes_robust.csv.
# - Varre recursivamente results/ atrás de CSVs com colunas esperadas
# - Concatena tudo, remove duplicatas por (instance, variant, run, seed)
# - Rotula grupo: classic (p01..p08), difficult (Jooken difíceis) ou other
# - Salva o consolidado e imprime cobertura por grupo/variante e clássicas faltantes

from __future__ import annotations
import os, re, sys
import pandas as pd
from typing import List, Tuple

REQUIRED = {"instance", "variant", "run", "seed"}   # "value" e "seconds" podem existir ou não
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
OUT_CSV     = os.path.join(RESULTS_DIR, "execucoes_robust.csv")
AN_DIR      = os.path.join(RESULTS_DIR, "analysis")
os.makedirs(AN_DIR, exist_ok=True)

# ==========================
# 1) DETECÇÃO DE GRUPO
# ==========================
def tag_group_from_path(path_or_instance: str) -> str:
    """
    classic  : p01..p08 (aceita 'p1'..'p8', com/sem .txt, em qualquer ponto do caminho)
    difficult: instâncias Jooken difíceis (caminhos contendo 'jooken' e 'dificil'/'dif')
    other    : demais
    """
    if not isinstance(path_or_instance, str):
        return "other"

    s = path_or_instance.replace("/", os.sep).lower()

    # 1) tenta pelo basename sem extensão
    name = os.path.basename(s)
    root, _ext = os.path.splitext(name)          # ex: ("p01", ".txt")
    if re.fullmatch(r"p0?[1-8]", root):
        return "classic"

    # 2) fallback: escaneia o caminho inteiro (fim de pasta/arquivo)
    if re.search(r"(?:^|[/\\])p0?[1-8](?:\.txt)?$", s):
        return "classic"

    # difíceis (Jooken)
    if "jooken" in s and ("dificil" in s or "dif" in s):
        return "difficult"

    return "other"

# ==========================
# 2) BUSCA E LEITURA
# ==========================
def looks_like_execution_csv(path: str) -> bool:
    """Heurística simples pelo nome do arquivo."""
    base = os.path.basename(path).lower()
    if not base.endswith(".csv"):
        return False
    # preferir arquivos de execuções; evita os "summary", "wins", "validation" etc
    if base.startswith(("execucoes_",)):
        return True
    # ainda assim aceitar "merged" / "fixed" previamente gerados
    if "execucoes" in base and any(t in base for t in ("merged", "fixed", "p01_p08", "jooken")):
        return True
    return False

def has_required_columns(path: str) -> Tuple[bool, List[str]]:
    try:
        hdr = pd.read_csv(path, nrows=0, low_memory=False)
    except Exception:
        return False, []
    cols = [c.strip() for c in hdr.columns]
    ok = REQUIRED.issubset(set(map(str.lower, cols)))
    return ok, cols

def read_exec_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    # normaliza nomes (sem alterar case original no arquivo)
    df.columns = [c.strip() for c in df.columns]
    # garante que as essenciais existam
    missing = REQUIRED - set(map(str.lower, df.columns))
    if missing:
        raise ValueError(f"Arquivo {path} não contém colunas obrigatórias: {missing}")
    # coerce tipos
    for c in ("run", "seed"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ("value", "seconds"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

# ==========================
# 3) PIPELINE
# ==========================
def find_candidate_csvs(root: str) -> List[str]:
    cand = []
    for dp, _dn, files in os.walk(root):
        for f in files:
            p = os.path.join(dp, f)
            if looks_like_execution_csv(p):
                ok, _ = has_required_columns(p)
                if ok:
                    cand.append(os.path.abspath(p))
    return sorted(set(cand))

def merge_and_dedupe(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True, sort=False)
    before = len(df)
    # drop linhas sem chaves essenciais
    df = df.dropna(subset=["instance", "variant", "run", "seed"])
    # rotula grupo
    df["group"] = df["instance"].astype(str).map(tag_group_from_path)
    # dedup por chave
    df = df.drop_duplicates(subset=["instance", "variant", "run", "seed"], keep="first").reset_index(drop=True)
    after = len(df)
    print(f"Linhas antes: {before} | depois (sem duplicatas): {after}")
    return df

def classic_missing_report(df: pd.DataFrame) -> List[str]:
    # quais 'p01..p08' (ou p1..p8) aparecem?
    if df.empty:
        return [f"p0{i}.txt" for i in range(1, 9)]
    inst = df.loc[df["group"]=="classic", "instance"].astype(str).tolist()
    present = set()
    for s in inst:
        name = os.path.basename(s).lower()
        root, _ = os.path.splitext(name)
        # aceita "p01".."p08" ou "p1".."p8"
        m = re.fullmatch(r"p0?([1-8])", root)
        if m:
            present.add(f"p0{int(m.group(1))}.txt")
    expected = [f"p0{i}.txt" for i in range(1, 9)]
    missing = [x for x in expected if x not in present]
    return missing

def coverage_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["group","variant","unique_instances"])
    # quantidade de instâncias únicas por (group, variant)
    out = (
        df.assign(instance=df["instance"].astype(str))
          .groupby(["group","variant"])["instance"]
          .nunique()
          .reset_index(name="unique_instances")
          .sort_values(["group","variant"])
    )
    return out

# ==========================
# 4) MAIN
# ==========================
def main():
    print(f"==> Varredura por CSVs válidos em {RESULTS_DIR} ...")
    cands = find_candidate_csvs(RESULTS_DIR)
    if not cands:
        print("[ERRO] Nenhum CSV de execuções válido encontrado em results/.")
        sys.exit(1)

    print("Candidatos aceitos:")
    for p in cands:
        print(" -", p)

    # carrega todos
    dfs = []
    for p in cands:
        try:
            dfs.append(read_exec_csv(p))
        except Exception as e:
            print(f"[IGNORADO] {p} -> {e}")

    if not dfs:
        print("[ERRO] Não foi possível ler nenhum CSV.")
        sys.exit(2)

    df = merge_and_dedupe(dfs)

    # salva consolidado
    os.makedirs(RESULTS_DIR, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\n[OK] Consolidado salvo em {OUT_CSV}")

    # Cobertura por grupo/variante
    cov = coverage_table(df)
    if not cov.empty:
        print("\nCobertura por grupo/variante (instâncias únicas):")
        print(cov.to_string(index=False))
        cov_path = os.path.join(AN_DIR, "coverage_from_robust.csv")
        cov.to_csv(cov_path, index=False)
        print("Cobertura salva em:", cov_path)

    # Clássicas faltantes (p01..p08)
    missing = classic_missing_report(df)
    if missing:
        print("\nClássicas presentes: nenhuma" if len(missing)==8 else "\nClássicas presentes: parciais")
        print("Clássicas faltando :", missing)
    else:
        print("\nClássicas (p01..p08) presentes.")

if __name__ == "__main__":
    main()
