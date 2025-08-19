import os
import re

RAW_DIR = "data/jooken/raw"
OUT_DIR = "data/jooken/prepared"
SET_FILE = "config/sets/jooken_all.txt"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SET_FILE), exist_ok=True)

def convert_file(in_path, out_path):
    with open(in_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]
    
    # Caso já esteja no formato certo, apenas salva em OUT_DIR
    try:
        cap = int(lines[0])
        n = int(lines[1])
        # Testa se a terceira linha é "valor peso"
        test_val, test_wt = map(int, lines[2].split())
        is_ok = True
    except:
        is_ok = False
    
    if not is_ok:
        # Se não estiver no formato, tenta extrair dos padrões do Jooken
        # Exemplo comum: profits: ... weights: ...
        profits, weights = [], []
        for line in lines:
            nums = re.findall(r"\d+", line)
            if not nums:
                continue
            if len(nums) == 1:
                continue
            # Primeira lista: valores, segunda: pesos
            if not profits:
                profits = list(map(int, nums))
            elif not weights:
                weights = list(map(int, nums))
        
        if len(profits) != len(weights):
            raise ValueError(f"Erro no formato: {in_path}")
        
        n = len(profits)
        cap = max(weights) * 2  # chute, ajustar se souber valor real
        lines = [str(cap), str(n)] + [f"{profits[i]} {weights[i]}" for i in range(n)]
    
    # Salva arquivo convertido
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# Lista para o arquivo de sets
converted_paths = []

for root, _, files in os.walk(RAW_DIR):
    for file in files:
        if file.startswith("."):
            continue
        in_path = os.path.join(root, file)
        rel_path = os.path.relpath(in_path, RAW_DIR)
        out_path = os.path.join(OUT_DIR, os.path.splitext(rel_path)[0] + ".txt")
        try:
            convert_file(in_path, out_path)
            converted_paths.append(out_path.replace("\\", "/"))
            print(f"[OK] {rel_path} -> {out_path}")
        except Exception as e:
            print(f"[ERRO] {rel_path}: {e}")

# Salva lista no config/sets
with open(SET_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(converted_paths)))

print(f"\nConversão concluída! {len(converted_paths)} arquivos salvos em {OUT_DIR}")
print(f"Lista de arquivos salva em {SET_FILE}")
