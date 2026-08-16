# 滴滴行程地图生成器

把滴滴导出的行程单 PDF（以及可选的截图 OCR）转换成结构化 CSV，再调用高德地图 API 生成一个可交互的行程地图 HTML。

## 功能

- 解析 `滴滴出行行程报销单*.pdf` 和 `滴滴顺风车行程单.pdf`
- 可选使用 macOS Vision OCR 识别行程截图
- 使用高德 POI 搜索和地理编码批量定位起终点
- 支持人工坐标纠错，修复高德误匹配
- 输出可直接分析的 `trips.csv` / `trips.xlsx`
- 输出独立 HTML 地图，支持城市、年份、来源筛选
- 点击起点/终点标记只显示相关行程线，并自动缩放

## 在线体验

不需要 API Key 的 Leaflet 静态示例页已经放在 GitHub Pages：

https://garyleejava.github.io/didi-trip-map/

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
