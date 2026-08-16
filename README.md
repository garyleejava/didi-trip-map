# 滴滴行程地图生成器

把滴滴导出的行程单 PDF（以及可选的截图 OCR）转换成结构化 CSV，再调用高德地图 API 生成一个可交互的行程地图 HTML。

## 功能

- 解析 `滴滴出行行程报销单*.pdf` 和 `滴滴顺风车行程单.pdf`
- 可选使用 macOS Vision OCR 识别行程截图
- 使用高德 POI 搜索和地理编码批量定位起终点
- 支持人工坐标纠错，修复高德误匹配
- 输出可直接分析的 `trips.csv` / `trips.xlsx`
- 输出独立 HTML 地图，支持城市、年份、月份、来源、日期范围和地点搜索
- 三标签分析面板：概览趋势、可排序行程表、地点明细
- 高德 MarkerCluster 地点聚合、热力图、聚合 OD 连线三种地图视图
- 选中单条行程按需调用高德参考路线，失败时保留示意连线并提示
- 月度趋势和城市分布图表，点击图表可直接下钻筛选
- 移动端地图全屏 + 可展开底部抽屉
- URL 保存当前视图状态，可复制链接；支持筛选结果 CSV 导出
- 默认构建不写入高德 Key，页面不会从 URL 读取 Key

## 在线体验

无需高德 Key、使用仓库示例数据的静态演示页已经放在 GitHub Pages：

https://garyleejava.github.io/didi-trip-map/

完整版包含高德地图、热力图和路线规划，需要在本地配置高德 Key 后生成页面体验。

## 快速开始

```bash
git clone https://github.com/garyleejava/didi-trip-map.git
cd didi-trip-map
python3 -m pip install -r requirements.txt
```

1. 把你的滴滴行程单 PDF 放进 `data/input/`。
2. 到[高德开放平台](https://lbs.amap.com/)申请一个“Web 服务 API” Key，并开通 Web 端 JS API。
3. 设置环境变量并运行：

```bash
export AMAP_KEY=你的高德Key
make run
```

也可以分步执行：

```bash
bash scripts/run_all.sh
```

直接用已有 CSV 构建（默认不嵌入 Key）：

```bash
python3 scripts/04_build_map.py \
  --trips outputs/trips.csv \
  --locations outputs/locations.csv \
  --output outputs/trip-map.html
```

本地预览时再注入 Key，最终分享使用空 Key 版本：

```bash
AMAP_KEY=你的高德Key python3 scripts/04_build_map.py \
  --trips outputs/trips.csv \
  --locations outputs/locations.csv \
  --output outputs/trip-map.html
```

如果高德账号配置了 `securityJsCode`，可同时传入：

```bash
AMAP_SECURITY_JS_CODE=你的安全密钥 python3 scripts/04_build_map.py \
  --trips outputs/trips.csv \
  --locations outputs/locations.csv \
  --output outputs/trip-map.html
```

生成结果：

- `outputs/trips.csv`：结构化行程明细
- `outputs/trips.xlsx`：Excel 版本
- `outputs/locations.csv`：起终点坐标
- `outputs/trip-map.html`：可交互行程地图，浏览器直接打开

## 截图行程（可选）

截图识别只在 macOS 上可用，使用系统自带 Vision OCR：

```bash
swiftc -O scripts/ocr.swift -o scripts/ocr
scripts/ocr data/screenshots/*.png > outputs/ocr.txt
```

然后再次运行 `make run`，`01_parse_pdfs.py` 会自动读取 `outputs/ocr.txt` 并合并截图行程。

## 手动修正坐标

复制示例文件：

```bash
cp overrides/user_overrides.example.py overrides/user_overrides.py
```

按 `城市、角色、地点名` 增加覆盖项，例如：

```python
OVERRIDES = {
    ("北京市", "起点", "示例地点|示例门店"): {
        "lng": 116.481488,
        "lat": 39.990474,
        "matched_name": "示例门店",
        "address": "示例地址",
        "note": "修正高德误匹配",
    },
}
```

## 快速体验示例数据

仓库附带一组不涉及真实个人行程的示例数据，可直接生成地图预览：

```bash
export AMAP_KEY=你的高德Key
make demo
```

打开 `outputs/trip-map.html` 即可体验。

也可以直接构建无 Key 的静态演示页：

```bash
make demo-page
```

生成结果在 `docs/index.html`，可部署到 GitHub Pages 或任意静态托管。

## 目录结构

```text
data/input/        放滴滴行程单 PDF
data/screenshots/  放行程截图（可选）
scripts/           解析、地理编码、纠错、构建脚本
template/          地图 HTML 模板
docs/              静态演示页与 GitHub Pages 源文件
overrides/         人工坐标纠错配置
sample/            示例数据
outputs/           生成结果（不提交到 Git）
```

## 隐私说明

本仓库不包含任何个人行程数据。`data/input/`、`data/screenshots/`、`outputs/` 和 `overrides/user_overrides.py` 都已被 Git 忽略，请勿把个人数据或含 Key 的 HTML 提交到 GitHub。

## License

MIT
