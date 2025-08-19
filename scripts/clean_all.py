import os, csv

def clean(in_path):
    if not os.path.exists(in_path):
        print(f"nao encontrado: {in_path}")
        return
    # detecta delimitador no cabecalho
    with open(in_path, 'r', encoding='utf-8', errors='ignore') as f:
        head = f.readline()
    delim = ';' if head.count(';') > head.count(',') else ','

    tmp_path = in_path + ".tmp"

    with open(in_path, 'r', encoding='utf-8', errors='ignore', newline='') as fin, \
         open(tmp_path, 'w', encoding='utf-8', newline='') as fout:
        r = csv.reader(fin, delimiter=delim)
        w = csv.writer(fout, delimiter=delim)
        header = next(r)
        w.writerow(header)

        # localiza a coluna 'instance' (case-insensitive)
        lower = [h.strip().lower() for h in header]
        inst_idx = lower.index('instance') if 'instance' in lower else None
        if inst_idx is None:
            print(f"[AVISO] coluna 'instance' nao encontrada em {in_path}. header={header}")
            kept = 0; removed = 0
            for row in r:
                w.writerow(row); kept += 1
        else:
            kept = 0; removed = 0
            for row in r:
                if not row or inst_idx >= len(row):
                    w.writerow(row); kept += 1; continue
                inst = (row[inst_idx] or '').strip().lower()
                # remove as linhas antigas (outp) e exige caminho/nome plausivel terminando com .txt
                if inst == 'outp' or (not inst.endswith('.txt')):
                    removed += 1
                    continue
                w.writerow(row); kept += 1

        print(f"{os.path.basename(in_path)} -> mantidas={kept}, removidas={removed}")

    # substitui o original pelo limpo
    os.replace(tmp_path, in_path)

def main():
    clean("results/jooken/execucoes_jooken_ALL.csv")
    clean("results/jooken/resumo_jooken_ALL.csv")

if __name__ == "__main__":
    main()
