# 人工坐标纠错

高德偶尔会把模糊地点匹配到错误的城市或门店。把
`overrides/user_overrides.example.py` 复制为 `overrides/user_overrides.py`，
然后按 `("城市", "角色", "地点名")` 作为 key 增加覆盖项即可。

`角色` 只能是 `起点` 或 `终点`。`03_apply_overrides.py` 会读取该文件，
并在 `locations.csv` 中把对应地点标记为 `source=manual`。
