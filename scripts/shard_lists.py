import argparse, os

def read_list(p):
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        return [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]

def write_list(paths, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for x in paths:
            f.write(x + "\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True, help="lista de instancias")
    ap.add_argument("--size", type=int, default=120, help="instancias por shard")
    ap.add_argument("--outdir", required=True, help="pasta de saida dos shards")
    args = ap.parse_args()

    items = read_list(args.infile)
    if not items:
        print("lista vazia:", args.infile)
        return

    os.makedirs(args.outdir, exist_ok=True)
    total = len(items)
    k = 0
    shard = 1
    while k < total:
        chunk = items[k:k+args.size]
        outp = os.path.join(args.outdir, f"shard_{shard:02d}.txt")
        write_list(chunk, outp)
        print(f"gravado: {outp} ({len(chunk)} instancias)")
        k += args.size
        shard += 1

if __name__ == "__main__":
    main()
