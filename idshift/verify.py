from __future__ import annotations
import json
from pathlib import Path

def _rows(path: Path):
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

def run_verify(args) -> int:
    out = Path(args.out)
    expect = json.loads(Path(args.expect).read_text())
    got = _rows(out / "products.jsonl")
    errors = []
    got_by = {}
    for r in got:
        got_by.setdefault(r["product_id"], []).append(r)
    exp_ids = {p["product_id"] for p in expect["products"]}
    if set(got_by) != exp_ids:
        errors.append(f"product_id set extra={sorted(set(got_by)-exp_ids)} missing={sorted(exp_ids-set(got_by))}")
    def key(r):
        return (r.get("valid_from") or "", r.get("sku") or "")
    for p in expect["products"]:
        evs = sorted(p["versions"], key=key)
        gvs = sorted(got_by.get(p["product_id"], []), key=key)
        if len(evs) != len(gvs):
            errors.append(f"{p['product_id']} version count {len(gvs)} != {len(evs)}")
            continue
        fields = ("sku","title","color","capacity_ml","image","price_cents","valid_from","valid_to","is_current")
        for e,g in zip(evs, gvs):
            for f in fields:
                if g.get(f) != e.get(f):
                    errors.append(f"{p['product_id']} {e.get('sku')} {f} {g.get(f)!r} != {e.get(f)!r}")
    if errors:
        print("verify failed:")
        for e in errors:
            print(" -", e)
        return 1
    print("verify ok")
    return 0
