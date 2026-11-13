verify 对照 fixtures/expected/scd2.json，比较每个 product_id 的行数、sku 序列、valid_from/valid_to、is_current，以及删除与新增。行顺序无关，同一产品的版本按 valid_from 排序后比较。
