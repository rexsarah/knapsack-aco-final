import pandas as pd

exec_all = pd.read_csv("results/jooken/execucoes_jooken_ALL.csv")
resm_all = pd.read_csv("results/jooken/resumo_jooken_ALL.csv")

mask_exec = ~exec_all["instance"].astype(str).str.lower().isin(["outp","test",""])
mask_resm = ~resm_all["instance"].astype(str).str.lower().isin(["outp","test",""])

exec_all2 = exec_all[mask_exec].copy()
resm_all2 = resm_all[mask_resm].copy()

exec_all2.to_csv("results/jooken/execucoes_jooken_ALL.csv", index=False)
resm_all2.to_csv("results/jooken/resumo_jooken_ALL.csv", index=False)

print("Removidas (execucoes):", len(exec_all) - len(exec_all2))
print("Removidas (resumo)   :", len(resm_all) - len(resm_all2))
