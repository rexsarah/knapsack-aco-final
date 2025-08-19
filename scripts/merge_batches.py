# scripts/merge_batches.py
import os, csv, glob
from pathlib import Path

ROOT = Path("results/jooken/batches")
OUT_EXEC_ALL = Path("results/jooken/execucoes_jooken_ALL.csv")
OUT_RESM_ALL = Path("results/jooken/resumo_jooken_ALL.csv")

# nomes dos arquivos dentro de cada batch
EXEC_NAME = "execucoes_jooken.csv"
RESM_NAME = "resumo_jooken.csv"

def read_csv_rows(path):
    # retorna header, rows
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    return header, rows

def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"gravado: {path}")

def is_valid_instance(s: str) -> bool:
    if not s: 
        return False
    s = s.strip().lower()
    # mantem somente instancias reais .txt
    return s.endswith(".txt")

def collect(pattern, expected_header=None, add_seed=False):
    files = glob.glob(pattern, recursive=True)
    out_header = None
    out_rows = []
    for fp in files:
        try:
            header, rows = read_csv_rows(fp)
        except Exception:
            continue

        # normaliza header na primeira vez
        if out_header is None:
            out_header = header.copy()
            if add_seed and "seed" not in [h.strip().lower() for h in out_header]:
                out_header.append("seed")
        # checa compatibilidade basica
        if expected_header and [h.strip().lower() for h in header] != [h.strip().lower() for h in expected_header]:
            # ignora formatos divergentes
            continue

        # tenta extrair seed do caminho: .../batches/seed12345/......
        seed = None
        parts = Path(fp).parts
        for p in parts:
            if p.lower().startswith("seed") and p[4:].isdigit():
                seed = p[4:]
        # índice da coluna instance
        try:
            inst_idx = [h.strip().lower() for h in header].index("instance")
        except ValueError:
            inst_idx = None

        for row in rows:
            if inst_idx is not None and not is_valid_instance(row[inst_idx]):
                continue  # filtra outp/test/etc
            if add_seed:
                if "seed" not in [h.strip().lower() for h in out_header]:
                    out_header.append("seed")
                row = row + [seed or ""]
            out_rows.append(row)

    return out_header, out_rows

def main():
    if not ROOT.exists():
        raise SystemExit(f"nao encontrado: {ROOT}")

    # junta todas as execucoes
    h_exec, rows_exec = collect(str(ROOT / "seed*/**" / EXEC_NAME), add_seed=True)
    if not rows_exec:
        print("ATENCAO: nenhuma linha de execucoes encontrada.")
    else:
        write_csv(OUT_EXEC_ALL, h_exec, rows_exec)

    # junta todos os resumos
    h_resm, rows_resm = collect(str(ROOT / "seed*/**" / RESM_NAME), add_seed=True)
    if not rows_resm:
        print("ATENCAO: nenhuma linha de resumo encontrada.")
    else:
        write_csv(OUT_RESM_ALL, h_resm, rows_resm)

if __name__ == "__main__":
    main()
