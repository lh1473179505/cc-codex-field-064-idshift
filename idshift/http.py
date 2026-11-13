from __future__ import annotations
import urllib.request, urllib.error, json
from dataclasses import dataclass

@dataclass
class Response:
    status: int
    body: bytes
    url: str

class Client:
    def get(self, url):
        req=urllib.request.Request(url, headers={"User-Agent":"idshift/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return Response(r.getcode(), r.read(), r.geturl())
        except urllib.error.HTTPError as e:
            return Response(e.code, e.read() if e.fp else b"", url)
    def post_json(self, url, payload):
        req=urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            return Response(r.getcode(), r.read(), r.geturl())
