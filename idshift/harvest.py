from __future__ import annotations
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

from idshift.http import Client


def strip_utm(url):
    parts = urlparse(url)
    qs = [(k, v) for k, v in parse_qsl(parts.query) if not k.startswith("utm_")]
    return parts._replace(query=urlencode(qs)).geturl()


def norm_title(title):
    return re.sub(r"\s+", " ", title.strip().lower())


def fingerprint(title, color, capacity_ml, image):
    filename = image.rsplit("/", 1)[-1].lower()
    key = "|".join([norm_title(title), color.lower(), str(int(capacity_ml)), filename])
    return hashlib.sha256(key.encode()).hexdigest()[:16]


class _ListParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self._cur = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div" and "card" in (attrs.get("class") or "").split():
            self._cur = {"sku": attrs.get("data-sku"), "title": attrs.get("data-title"),
                         "color": attrs.get("data-color"), "href": None, "image": None}
        elif self._cur is not None and tag == "a" and self._cur["href"] is None:
            self._cur["href"] = attrs.get("href")
        elif self._cur is not None and tag == "img" and self._cur["image"] is None:
            self._cur["image"] = attrs.get("src")

    def handle_endtag(self, tag):
        if tag == "div" and self._cur is not None:
            self.cards.append(self._cur)
            self._cur = None


class _DetailParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = {"sku": None, "capacity_ml": None, "title": None,
                     "color": None, "price_cents": None, "image": None}
        self._in_h1 = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article":
            self.data["sku"] = attrs.get("data-sku")
            cap = attrs.get("data-capacity-ml")
            self.data["capacity_ml"] = int(cap) if cap is not None else None
        elif tag == "h1":
            self._in_h1 = True
        elif tag == "p":
            if "data-color" in attrs:
                self.data["color"] = attrs["data-color"]
            if "data-price-cents" in attrs:
                self.data["price_cents"] = int(attrs["data-price-cents"])
        elif tag == "img" and self.data["image"] is None:
            self.data["image"] = attrs.get("src")

    def handle_endtag(self, tag):
        if tag == "h1":
            self._in_h1 = False

    def handle_data(self, data):
        if self._in_h1:
            self.data["title"] = (self.data["title"] or "") + data


def scrape(client, base):
    base = base.rstrip("/")
    resp = client.get(base + "/")
    parser = _ListParser()
    parser.feed(resp.body.decode())
    items = []
    for card in parser.cards:
        href = strip_utm(card["href"])
        detail = client.get(base + href)
        dp = _DetailParser()
        dp.feed(detail.body.decode())
        items.append({
            "sku": dp.data["sku"] or card["sku"],
            "title": dp.data["title"].strip(),
            "color": dp.data["color"],
            "capacity_ml": dp.data["capacity_ml"],
            "image": strip_utm(dp.data["image"]),
            "price_cents": dp.data["price_cents"],
        })
    return items


def _same_version(row, item):
    return all(row[f] == item[f] for f in
               ("sku", "title", "color", "capacity_ml", "image", "price_cents"))


def run_harvest(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ckpt_path = Path(args.checkpoint)
    ckpt = json.loads(ckpt_path.read_text()) if ckpt_path.is_file() else {"waves": []}
    if args.wave_name in ckpt["waves"]:
        print(f"wave {args.wave_name} already harvested, skipping")
        return 0

    items = scrape(Client(), args.base)

    products_path = out / "products.jsonl"
    rows = []
    if products_path.is_file():
        rows = [json.loads(l) for l in products_path.read_text().splitlines() if l.strip()]
    prev_wave = ckpt["waves"][-1] if ckpt["waves"] else None

    matches = []
    seen = set()
    for item in items:
        pid = fingerprint(item["title"], item["color"], item["capacity_ml"], item["image"])
        seen.add(pid)
        current = next((r for r in rows if r["product_id"] == pid and r["is_current"]), None)
        if current is not None and _same_version(current, item):
            continue
        rec = dict(item)
        rec["product_id"] = pid
        rec["valid_from"] = args.wave_name
        rec["valid_to"] = None
        rec["is_current"] = True
        if current is None:
            rows.append(rec)
            matches.append({"wave_from": prev_wave, "sku_from": None,
                            "wave_to": args.wave_name, "sku_to": item["sku"],
                            "product_id": pid, "reason": "new"})
        else:
            current["valid_to"] = args.wave_name
            current["is_current"] = False
            rows.append(rec)
            matches.append({"wave_from": prev_wave, "sku_from": current["sku"],
                            "wave_to": args.wave_name, "sku_to": item["sku"],
                            "product_id": pid, "reason": "fingerprint"})

    for row in rows:
        if row["is_current"] and row["product_id"] not in seen:
            row["valid_to"] = args.wave_name
            row["is_current"] = False
            matches.append({"wave_from": prev_wave, "sku_from": row["sku"],
                            "wave_to": args.wave_name, "sku_to": None,
                            "product_id": row["product_id"], "reason": "deleted"})

    with products_path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (out / "matches.jsonl").open("a") as fh:
        for m in matches:
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")

    ckpt["waves"].append(args.wave_name)
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    ckpt_path.write_text(json.dumps(ckpt, ensure_ascii=False, indent=2))
    print(f"harvested wave {args.wave_name}: {len(items)} items, {len(rows)} versions")
    return 0
