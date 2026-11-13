# idshift

目录站的商品主键隔夜会变。把两波抓取对成稳定身份，并按 SCD2 写出历史。

```
python -m idshift site --port 8765 --wave 1
python -m idshift harvest --base http://127.0.0.1:8765 --wave-name 2026-03-01 --out <out> --checkpoint <ckpt>
# 切换 wave 2：POST /_ctl/wave  {"wave":2}
python -m idshift harvest --base http://127.0.0.1:8765 --wave-name 2026-03-02 --out <out> --checkpoint <ckpt>
python -m idshift verify --out <out> --expect fixtures/expected/scd2.json
```
