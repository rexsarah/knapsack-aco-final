# -*- coding: utf-8 -*-
"""
Valida uma lista de caminhos (um por linha) e gera:
 - config/sets/jooken_dificil_valid.txt (apenas os OK)
 - results/validation/invalid_instances.csv (motivo do erro)
Uso:
  python scripts/validate_instance_files.py config/sets/jooken_dificil_all.txt
"""

import sys, re, pathlib, csv

def is_valid_instance(path: pathlib.Path) -> str|None:
    if not path.exists():
        return "nao_existe"
    if path.suffix.lower() not in {".kp", ".dat"}:
        return "ext_invalida"
    txt = path.read_text(errors="ignore")
    nums = list(map(int, re.findall(r"-?\d+", txt)))
    if len(nums) < 10:
        return "poucos_numeros"  # heurística.
    return None

def main():
    if len(sys.argv) != 2:
        print("Uso: python scripts/validate_instance_files.py <lista.txt>")
        sys.exit(2)

    in_list = pathlib.Path(sys.argv[1]).resolve()
    if not in_list.exists():
        print(f"Lista não encontrada: {in_list}")
        sys.exit(2)

    root = in_list.parent.parent  # .../config/sets/ -> repo raiz
    out_ok  = root / "config" / "sets" / "jooken_dificil_valid.txt"
    out_bad = root / "results" / "validation" / "invalid_instances.csv"
    out_bad.parent.mkdir(parents=True, exist_ok=True)

    ok_paths, bad_rows = [], []
    for line in in_list.read_text().splitlines():
        p = pathlib.Path(line.strip().strip('"'))
        if not p:
            continue
        reason = is_valid_instance(p)
        if reason is None:
            ok_paths.append(str(p))
        else:
            bad_rows.append({"path": str(p), "reason": reason})

    pathlib.Path(out_ok).write_text("\n".join(ok_paths), encoding="utf-8")
    with open(out_bad, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path","reason"])
        w.writeheader()
        w.writerows(bad_rows)

    print(f"OK: {len(ok_paths)} | inválidos: {len(bad_rows)}")
    print(f"Lista válida: {out_ok}")
    print(f"Relatório inválidos: {out_bad}")

if __name__ == "__main__":
    main()
