from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

# fields: sku, title, color, capacity_ml, image, price_cents
WAVE1 = [
    {"sku":"SKU-MUG-A","title":"Blue Mug","color":"blue","capacity_ml":300,"image":"/img/mug-blue.png","price_cents":1290},
    {"sku":"SKU-LAMP-1","title":"Desk Lamp","color":"black","capacity_ml":0,"image":"/img/lamp.png","price_cents":5900},
    {"sku":"NW-1","title":"Night Light","color":"white","capacity_ml":0,"image":"/img/night-a.png","price_cents":800},
    {"sku":"NW-2","title":"Night Light","color":"white","capacity_ml":0,"image":"/img/night-b.png","price_cents":820},
    {"sku":"SKU-CUP-3","title":"Travel Cup","color":"silver","capacity_ml":450,"image":"/img/cup.png","price_cents":2100},
]
WAVE2 = [
    {"sku":"SKU-MUG-A2","title":"Blue Mug","color":"blue","capacity_ml":300,"image":"/img/mug-blue.png","price_cents":1490},  # same product, new sku+price
    # LAMP gone
    {"sku":"NW-1B","title":"Night Light","color":"white","capacity_ml":0,"image":"/img/night-a.png","price_cents":800},
    {"sku":"NW-2B","title":"Night Light","color":"white","capacity_ml":0,"image":"/img/night-b.png","price_cents":820},
    {"sku":"SKU-CUP-3","title":"Travel Cup","color":"silver","capacity_ml":450,"image":"/img/cup.png","price_cents":2100},  # unchanged sku
    {"sku":"SKU-BOWL-9","title":"Soup Bowl","color":"green","capacity_ml":600,"image":"/img/bowl.png","price_cents":1600},
]
STATE={"wave":1}

def items():
    return WAVE2 if STATE["wave"]==2 else WAVE1

def list_html():
    cards=[]
    for it in items():
        cards.append(
            f'<div class="card" data-sku="{it["sku"]}" data-title="{it["title"]}" data-color="{it["color"]}">'
            f'<a href="/item/{it["sku"]}?utm_source=list">{it["title"]}</a>'
            f'<img src="{it["image"]}" alt="">'
            f"</div>"
        )
    return "<!doctype html><html><body>" + "".join(cards) + "</body></html>"

def detail_html(it):
    return (
        f'<!doctype html><html><body><article class="product" data-sku="{it["sku"]}" data-capacity-ml="{it["capacity_ml"]}">'
        f'<h1>{it["title"]}</h1><p data-color="{it["color"]}">{it["color"]}</p>'
        f'<p data-price-cents="{it["price_cents"]}">{it["price_cents"]}</p>'
        f'<img src="{it["image"]}?utm_source=detail">'
        f"</article></body></html>"
    )

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):
        return
    def _send(self, st, body, ctype="text/html; charset=utf-8"):
        if isinstance(body,str):
            body=body.encode()
        self.send_response(st)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        path=unquote(urlparse(self.path).path)
        if path=="/_ctl/wave":
            n=int(self.headers.get("Content-Length") or 0)
            body=json.loads(self.rfile.read(n) or b"{}")
            STATE["wave"]=int(body.get("wave",1))
            return self._send(200, json.dumps({"wave":STATE["wave"]}), "application/json")
        return self._send(404,"no")
    def do_GET(self):
        path=unquote(urlparse(self.path).path)
        if path=="/":
            return self._send(200, list_html())
        if path.startswith("/item/"):
            sku=path.split("/")[-1]
            it=next((x for x in items() if x["sku"]==sku), None)
            if not it:
                return self._send(404,"missing")
            return self._send(200, detail_html(it))
        if path.startswith("/img/"):
            return self._send(200, b"fake-image", "image/png")
        return self._send(404,"no")

def serve(host="127.0.0.1", port=8765, wave=1):
    STATE["wave"]=wave
    httpd=ThreadingHTTPServer((host,port), Handler)
    print(f"idshift fixture site on http://{host}:{port} wave={wave}")
    httpd.serve_forever()
