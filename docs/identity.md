# 身份与历史

夹具站分两波目录。wave 1 与 wave 2 的列表/详情主键（`data-sku` 和 URL 里的 `/item/{sku}`）会对不上，但其中一部分其实是同一商品。

## 页面

- `/` 列表页，每个卡片有 `data-sku`、`data-title`、`data-color`、`img[src]`。
- `/item/{sku}` 详情：标题、颜色、容量、图片路径、价格（分）。wave 2 部分商品换了 sku，价格也可能变。
- 列表和详情都可能带 `?utm_source=`，写入记录前去掉 utm_*。

## 稳定身份

不要用 sku 当长期主键。稳定指纹按下面字段生成，顺序固定，用 `|` 拼接后再 sha256 取前 16 个十六进制字符，作为 `product_id`：

1. 规范化标题：小写，去掉首尾空白，连续空白压成一个空格
2. 颜色：原样小写
3. 容量：整数升（详情里 `data-capacity-ml`）
4. 图片文件名（不含路径，保留扩展名，小写）

夹具里有一个陷阱：`/item/NW-1` 和 `/item/NW-2`（wave 2 也会出现对应项）标题和颜色非常接近，但容量或图片不同，必须是两条产品，不能合并。

wave 1 的 `SKU-MUG-A` 在 wave 2 会改名为 `SKU-MUG-A2`，标题/颜色/容量/图片不变，价格从 1290 变成 1490，这是同一商品的一次变更。

wave 1 的 `SKU-LAMP-1` 在 wave 2 列表和详情里都消失，视为删除。

wave 2 新增 `SKU-BOWL-9`，没有 wave 1 对应项。

## SCD2

`--out/products.jsonl` 每个版本一行：

- `product_id`（稳定指纹）
- `sku`（该版本观察到的主键）
- `title`、`color`、`capacity_ml`、`image`、`price_cents`
- `valid_from`：首次看到该版本时的 `--wave-name`
- `valid_to`：被后一版本替代或删除时的那个 `--wave-name`；仍有效则为 null
- `is_current`：是否当前版本

同一 `product_id` 在任意时刻只能有一行 `is_current=true`。价格变化要新开一行，旧行的 `valid_to` 设为新 wave-name，`is_current` 改为 false。若指纹未变但 sku 变了（例如 MUG-A 变成 MUG-A2），即使价格以外的描述字段相同，也要新开一行记录新 sku。删除则把当前行 `valid_to` 设为该 wave-name，`is_current=false`，不要为删除再插一个空版本。字段全部不变（包括 sku 和价格）的商品在新 wave 里不要再插行，只保持原来的当前行。

`--out/matches.jsonl` 记录跨波对齐：`{"wave_from","sku_from","wave_to","sku_to","product_id","reason"}`，`reason` 为 `fingerprint` 或 `new` 或 `deleted`。

checkpoint 记下已经收获的 wave-name，避免同一波重复追加版本。
