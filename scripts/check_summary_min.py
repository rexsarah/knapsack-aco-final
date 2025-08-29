# scripts/check_summary_min.py
import os, sys, csv, glob, math
import pandas as pd

RESUMO = r"results\jooken\resumo_jooken.csv"

def sniff_sep(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        head = f.read(2048)
    return ";" if (";" in head and "," not in head) else ","

def pick(colmap, candidates):
    for k in candidates:
        if k in colmap: return colmap[k]
    return None

def main():
    if not os.path.exists(RESUMO):
        print(f"[ERRO] Não encontrei {RESUMO}")
        sys.exit(1)

    sep = sniff_sep(RESUMO)
    df = pd.read_csv(RESUMO, sep=sep)
    cols = {c.lower(): c for c in df.columns}

    c_inst = pick(cols, ["instance","inst","name","file","filename"])
    c_algo = pick(cols, ["algo","variant","alg","method"])
    c_prof = pick(cols, ["profile","perfil","prof"])
    c_opt  = pick(cols, ["hit_optimal","is_optimal","optimal","isoptimal"])
    c_val  = pick(cols, ["best_value","value","best","bestvalue","val","objective"])

    print(">> colunas:", list(df.columns))
    print(">> linhas:", len(df))
    if c_inst: print(">> instâncias únicas:", df[c_inst].nunique())
    if c_algo: print(">> variantes:", sorted(df[c_algo].dropna().unique().tolist()))
    if c_prof: print(">> perfis:", sorted(df[c_prof].dropna().unique().tolist()))

    if c_algo and c_prof:
        print("\n# linhas por (variante, perfil):")
        print(df.groupby([c_algo, c_prof]).size().reset_index(name="rows"))

    if c_opt and c_algo and c_prof:
        print("\n# ótimos por (variante, perfil):")
        print(df[df[c_opt]==1].groupby([c_algo, c_prof]).size().reset_index(name="hits"))

    # Wins por instância (quem teve maior valor); empates contam como win para todos empatados
    if c_val and c_inst and c_algo and c_prof:
        print("\n# wins por (variante, perfil):")
        wins = []
        for inst, g in df.groupby(c_inst):
            m = g[c_val].max()
            winners = g[g[c_val] == m][[c_algo, c_prof]]
            for _, row in winners.iterrows():
                wins.append((row[c_algo], row[c_prof]))
        if wins:
            wdf = pd.DataFrame(wins, columns=[c_algo, c_prof])
            print(wdf.groupby([c_algo, c_prof]).size().reset_index(name="wins"))
        else:
            print("sem dados para wins (coluna de valor ausente?)")
    else:
        print("\n[AVISO] faltam colunas para calcular wins (preciso de instance, algo, profile e valor).")

if __name__ == "__main__":
    main()
