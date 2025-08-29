#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Converte instâncias no formato Jooken/Pisinger para o formato clássico usado no seu projeto e,
opcionalmente, valida arquivos de solução emparelhados.

Entrada (Jooken):
    n
    idx profit weight
    ...
    capacity

Saída (Clássico):
    n capacity
    profit weight
    ...
Solução (formatos aceitos – detecção por linha):
    Linha 1: valor_total_declarado
    Linha 2: k (número de linhas de itens)
    Linhas 3..k+2: qualquer um dos três:
        (a) "index"
        (b) "index multiplicity"
        (c) "profit weight"

Uso (conversão simples):
    python convert_jooken_to_classic.py -i <pasta_entrada> -o <pasta_saida> --ext .in .txt

Uso (com validação de soluções):
    python convert_jooken_to_classic.py -i <pasta_entrada> -o <pasta_saida> \
        --validate --sol-ext .txt --solutions-dir <pasta_solucoes>

Regras para emparelhamento de solução:
    - Por padrão, o script procura um arquivo de solução que tenha o MESMO "stem" do arquivo de instância.
      Ex.: "foo.in" -> "foo.txt" (na mesma pasta da instância, ou em --solutions-dir).
    - Você pode apontar --solutions-dir; se não passar, busca ao lado da instância.

Dicas:
    - Usa varredura recursiva (subpastas).
    - Gera arquivos com o mesmo nome + sufixo (por padrão '_clean') na pasta de saída,
      preservando a estrutura de subpastas.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# -------------------------
# Utilidades básicas
# -------------------------

def to_int(x: str) -> int:
    x = x.strip()
    if any(c in x for c in "eE."):
        try:
            return int(float(x))
        except Exception:
            pass
    return int(x)

def split_ints(line: str) -> List[int]:
    return [to_int(t) for t in line.strip().split() if t.strip()]

# -------------------------
# Leitura Jooken e escrita Clássico
# -------------------------

def read_jooken_instance(path: Path):
    lines = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.strip()
            if s:
                lines.append(s)

    if len(lines) < 2:
        raise ValueError(f"Arquivo muito curto: {path}")

    n = to_int(lines[0])
    if len(lines) < n + 2:
        raise ValueError(f"Contagem inconsistente em {path}: n={n}, linhas={len(lines)}")

    rows = []
    for i in range(1, 1 + n):
        parts = split_ints(lines[i])
        if len(parts) < 3:
            raise ValueError(f"Linha {i+1} inválida em {path}: '{lines[i]}'")
        idx, profit, weight = parts[0], parts[1], parts[2]
        rows.append((idx, profit, weight))

    capacity = to_int(lines[1 + n])
    return n, capacity, rows  # rows: List[(idx, profit, weight)]

def write_classic_instance(path_out: Path, n: int, capacity: int, rows_sorted: List[Tuple[int,int,int]]):
    path_out.parent.mkdir(parents=True, exist_ok=True)
    with path_out.open("w", encoding="utf-8") as f:
        f.write(f"{n} {capacity}\n")
        for _, p, w in rows_sorted:
            f.write(f"{p} {w}\n")

# -------------------------
# Leitura do formato Clássico (para validação)
# -------------------------

def read_classic_instance(path: Path):
    """
    Lê:
        n capacity
        p w  (n linhas)
    Retorna:
        n, capacity, items: List[(profit, weight)]
    """
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        header = split_ints(f.readline())
        if len(header) < 2:
            raise ValueError(f"Cabeçalho inválido em {path}")
        n, capacity = header[0], header[1]
        items = []
        for i in range(n):
            parts = split_ints(f.readline())
            if len(parts) < 2:
                raise ValueError(f"Linha de item inválida (#{i+1}) em {path}")
            items.append((parts[0], parts[1]))
    return n, capacity, items

# -------------------------
# Validador de soluções
# -------------------------

def read_solution_flexible(path: Path) -> Tuple[int, List[Tuple[str, Tuple[int,int]]]]:
    """
    Lê um arquivo de solução em formato flexível.
    Retorna:
        valor_total_declarado,
        linhas_itens: lista de tuplas (tipo, payload)
            tipo ∈ {"index", "index_mult", "profit_weight"}
            payload:
                - "index": (idx, 1)
                - "index_mult": (idx, multiplicity)
                - "profit_weight": (profit, weight)
    """
    lines = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.strip()
            if s:
                lines.append(s)

    if len(lines) < 2:
        raise ValueError(f"Solução muito curta: {path}")

    declared_value = to_int(lines[0])
    k = to_int(lines[1])

    if len(lines) < 2 + k:
        raise ValueError(f"Solução inconsistente (k={k}, linhas={len(lines)}) em {path}")

    parsed = []
    for i in range(2, 2 + k):
        parts = split_ints(lines[i])
        if len(parts) == 1:
            parsed.append(("index", (parts[0], 1)))
        elif len(parts) >= 2:
            a, b = parts[0], parts[1]
            # Heurística: se 'a' é pequeno (índice provável) e 'b' é pequeno (multiplicidade),
            # ou se explicitamente quer tratar como index/mult:
            if a >= 0 and b >= 0 and (a < 10**7 and b < 10**3):
                # preferimos tratar como index/mult quando 'a' parece índice
                parsed.append(("index_mult", (a, b)))
            else:
                # caso contrário, tratamos como (profit, weight)
                parsed.append(("profit_weight", (a, b)))
        else:
            raise ValueError(f"Linha de item inválida em {path}: '{lines[i]}'")

    return declared_value, parsed

def validate_solution_for_instance(instance_classic_path: Path, sol_path: Path) -> Dict[str, int]:
    """
    Valida solução contra a instância clássica.
    Retorna um dicionário com métricas e flags.
    """
    n, capacity, items = read_classic_instance(instance_classic_path)
    # Índice → (profit, weight)
    idx_to_item = {i: items[i] for i in range(n)}
    # Para busca por (profit, weight), montamos um multimap value->indices disponíveis:
    from collections import defaultdict, deque
    pw_to_indices = defaultdict(list)
    for i, (p, w) in enumerate(items):
        pw_to_indices[(p, w)].append(i)
    # usaremos filas para marcar consumo de duplicatas
    for k in list(pw_to_indices.keys()):
        pw_to_indices[k] = deque(pw_to_indices[k])

    declared_value, entries = read_solution_flexible(sol_path)

    chosen_indices = []  # expandido com multiplicidade
    # Interpreta linha a linha (pode misturar formatos)
    for t, payload in entries:
        if t == "index":
            idx, mult = payload[0], 1
            if idx < 0 or idx >= n:
                raise ValueError(f"Índice fora do intervalo na solução {sol_path}: {idx}")
            chosen_indices.extend([idx] * mult)
        elif t == "index_mult":
            idx, mult = payload
            if idx < 0 or idx >= n:
                raise ValueError(f"Índice fora do intervalo na solução {sol_path}: {idx}")
            if mult < 0:
                raise ValueError(f"Multiplicidade negativa para índice {idx} em {sol_path}")
            chosen_indices.extend([idx] * mult)
        elif t == "profit_weight":
            p, w = payload
            q = pw_to_indices.get((p, w))
            if not q or len(q) == 0:
                raise ValueError(f"Item (p={p}, w={w}) não encontrado/indisponível em {instance_classic_path}")
            idx = q.popleft()  # consome 1 unidade desse par (resolve duplicatas)
            chosen_indices.append(idx)
        else:
            raise ValueError(f"Tipo de linha desconhecido na solução {sol_path}: {t}")

    # Acumula valor e peso
    total_value = 0
    total_weight = 0
    for idx in chosen_indices:
        p, w = idx_to_item[idx]
        total_value += p
        total_weight += w

    return {
        "declared_value": declared_value,
        "recomputed_value": total_value,
        "total_weight": total_weight,
        "capacity": capacity,
        "feasible": 1 if total_weight <= capacity else 0,
        "value_match": 1 if total_value == declared_value else 0,
        "num_items_selected": len(chosen_indices),
    }

# -------------------------
# CLI / fluxo principal
# -------------------------

def parse_args():
    ap = argparse.ArgumentParser(description="Converter instâncias de Jooken/Pisinger para formato clássico, com validador opcional de soluções.")
    ap.add_argument("-i", "--input_dir", required=True, type=Path, help="Pasta raiz com as instâncias de entrada.")
    ap.add_argument("-o", "--output_dir", required=True, type=Path, help="Pasta raiz de saída para arquivos convertidos.")
    ap.add_argument("--ext", nargs="+", default=[".in"], help="Extensões de instâncias a considerar (ex.: .in .dat .txt).")
    ap.add_argument("--suffix", default="_clean", help="Sufixo no arquivo de saída antes da extensão (padrão: _clean).")
    ap.add_argument("--sort_by_index", action="store_true", help="Ordena os itens pelo índice lido (coluna 1).")
    ap.add_argument("--dry_run", action="store_true", help="Não grava arquivos; apenas valida e mostra o que faria.")

    # Validação de soluções
    ap.add_argument("--validate", action="store_true", help="Ativa validação de soluções emparelhadas.")
    ap.add_argument("--solutions-dir", type=Path, default=None, help="Pasta raiz onde estão as soluções (opcional).")
    ap.add_argument("--sol-ext", nargs="+", default=[".txt"], help="Extensões de arquivos de solução (ex.: .sol .txt).")

    return ap.parse_args()

def find_solution_for_instance(inst_path: Path, base_in: Path, solutions_dir: Path, sol_exts: List[str]) -> Path:
    """
    Procura solução por mesmo 'stem' do arquivo de instância.
    1) Se solutions_dir for dado, busca lá recursivamente pelo stem.
    2) Caso contrário, busca ao lado da instância.
    Retorna Path ou None.
    """
    stem = inst_path.stem
    # Prioridade: solutions_dir
    if solutions_dir and solutions_dir.exists():
        candidates = list(solutions_dir.rglob(f"{stem}*"))
        for c in candidates:
            if c.is_file() and c.suffix.lower() in sol_exts:
                return c

    # fallback: mesma pasta
    local_candidates = list(inst_path.parent.glob(f"{stem}*"))
    for c in local_candidates:
        if c.is_file() and c.suffix.lower() in sol_exts:
            return c

    return None

def main():
    args = parse_args()
    if not args.input_dir.exists():
        print(f"Erro: pasta de entrada não existe: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    exts = set(e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.ext)
    sol_exts = set(e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.sol_ext)

    files = [p for p in args.input_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts]
    if not files:
        print("Nenhum arquivo de instância encontrado com as extensões fornecidas.")
        sys.exit(2)

    for path_in in files:
        try:
            n, capacity, rows = read_jooken_instance(path_in)
            rows_sorted = sorted(rows, key=lambda t: t[0]) if args.sort_by_index else rows

            rel = path_in.relative_to(args.input_dir)
            out_rel = rel.with_name(f"{rel.stem}{args.suffix}{rel.suffix}")
            path_out = args.output_dir / out_rel

            if args.dry_run:
                print(f"[DRY] {path_in} -> {path_out} | n={n}, capacity={capacity}, items={len(rows_sorted)}")
            else:
                write_classic_instance(path_out, n, capacity, rows_sorted)
                print(f"[OK ] {path_in} -> {path_out} | n={n}, capacity={capacity}, items={len(rows_sorted)}")

            if args.validate:
                # Procurar solução correspondente
                sol_path = find_solution_for_instance(path_in, args.input_dir, args.solutions_dir, list(sol_exts))
                if sol_path and sol_path.exists():
                    try:
                        metrics = validate_solution_for_instance(path_out, sol_path)
                        feas = "OK" if metrics["feasible"] else "OVER"
                        vmatch = "OK" if metrics["value_match"] else "DIFF"
                        print(f"      [VAL] {sol_path.name} | value_decl={metrics['declared_value']} "
                              f"recomp={metrics['recomputed_value']} | weight={metrics['total_weight']}/{metrics['capacity']} "
                              f"| feas={feas} | value_match={vmatch} | items={metrics['num_items_selected']}")
                    except Exception as ve:
                        print(f"      [VAL-ERRO] {sol_path.name}: {ve}", file=sys.stderr)
                else:
                    print("      [VAL] Nenhum arquivo de solução correspondente encontrado.")

        except Exception as e:
            print(f"[ERRO] Falha ao processar {path_in}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
