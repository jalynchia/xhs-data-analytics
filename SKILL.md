---
name: xhs-data-analytics
description: "小红书视频数据多维深度分析与复盘工具。当用户提出要对小红书内容数据进行数据整理、数据分析时，必须触发此 Skill。本 Skill 将通过多模态数据提取、指标自动计算、导出无样式 Excel 数据以及生成交互式 HTML Dashboard 完成闭环分析，甚至在用户只说「帮我整理下数据」或「看看这个视频表现」时，也应当优先使用本 Skill 进行分析服务。"
---

# xhs-data-analytics

本 Skill 用于对小红书平台的视频数据进行一键式数据清洗、汇总，并生成支持高度交互、带动态图表及 AI 深度文字复盘的 HTML Dashboard。

## 1. 核心流程与执行步骤

收到用户提供的文件后，请复制并严格执行以下 Step list：

- **Step 1: 输入完整性检查与多模态识别**
  - 检查 3 个核心文件是否齐备：
    - `[标题]-播放数据明细表.xlsx`
    - `[标题]-互动数据明细表.xlsx`
    - `[标题]-观看趋势.json`
  - 视觉识别 2 张截图（如有缺项，应主动询问用户补全，若用户无法提供，降级为用 0 填充）：
    1. **「观看来源」截图**：提取每个来源（首页推荐、视频推荐、搜索、个人主页、其他）的占比数据。
    2. **「观众画像」截图**：提取性别分布（女/男）、年龄区间占比、城市分布 Top 5 占比。
  - 将所有提取到的多模态数据，保存为临时文件 `visual_data.json`（见 `references/data-schema.md` 获取结构）。

- **Step 2: 运行数据提取与指标计算脚本**
  - 使用 Python 运行 `scripts/extract_data.py`。该脚本会自动勘误粉丝指标、计算派生指标（互动率、均播占比、涨粉率等）并合并时序。
  - 运行命令示例：
    ```bash
    python scripts/extract_data.py \
      --play-file "path/to/播放数据明细表.xlsx" \
      --interact-file "path/to/互动数据明细表.xlsx" \
      --trend-file "path/to/观看趋势.json" \
      --visual-json "visual_data.json" \
      --out-json "report_data.json"
    ```

- **Step 3: 撰写深度文字复盘报告**
  - 读取刚才生成的 `report_data.json` 中的数据，并查阅 [references/analysis-framework.md](file:///references/analysis-framework.md) 规定的分析维度。
  - 撰写包含“内容创作视角”与“渠道运营视角”共 9 个诊断点的复盘，确保结论完全由数据推导，行动建议具体到“下一期视频做什么”。
  - 将分析报告以 JSON 结构保存至 `analysis.json`，结构如下（**必须包含全部三个顶级字段，缺少任一字段将导致仪表盘对应区块显示占位文本**）：
    ```json
    {
      "diagnostic_card": {
        "core_定性": "一句话漏斗定性，必须包含具体数字，例如：获客层断点：CTR 5.9% 处于良好区间，但 2秒退出率 40.1% 超过危险线，前 5 秒拖沓导致约 157,300 名陌生用户流失。",
        "physical_actions": [
          "物理动作 1：具体到剪辑/字幕/时间戳的可执行动作",
          "物理动作 2：同上",
          "物理动作 3：同上"
        ],
        "next_topic_recommendation": "下期具体选题标题建议，例如：《我让免费 Claude 整理了我 3 年的照片，结果有点上头》"
      },
      "creation_perspective": [
        {
          "point_name": "分析点名称",
          "data_performance": "引用的具体数字与计算公式",
          "diagnosis_insight": "深度诊断解读结论",
          "action_suggestions": ["行动建议 1", "行动建议 2"]
        }
      ],
      "ops_perspective": [ ... ]
    }
    ```

- **Step 3.5: 校验 analysis.json 的 JSON 合法性（必须执行，不可跳过）**
  - **根因说明**：Step 3 中 AI 直接将自然语言分析文字写成 JSON 文本。自然语言中天然出现的 ASCII 双引号（如「"前言税"」「"引用词"」）在 JSON 字符串值内部若未转义，会导致后续 `json.load()` 抛出 `JSONDecodeError`。
  - **执行命令**：
    ```bash
    python3 scripts/sanitize_analysis.py --analysis-json "analysis.json"
    ```
  - 若脚本输出 `OK`，继续执行 Step 4。
  - 若脚本输出 `ERROR` 并以非零状态码退出，说明 `analysis.json` 中存在非法 JSON。须重新检查并修正 Step 3 生成的内容，确保字符串值内部的双引号已转义（`\"`）后再重试。

- **Step 4: 导出纯数据汇总 Excel 文件**
  - 使用 Python 运行 `scripts/build_excel.py`，静默导出汇总的 xlsx 表格（不带复杂样式，纯用于数据归档）。
  - 运行命令示例：
    ```bash
    python scripts/build_excel.py \
      --in-json "report_data.json" \
      --out-xlsx "path/to/输出_数据汇总表.xlsx"
    ```

- **Step 5: 生成炫酷的交互式 HTML Dashboard**
  - 使用 Python 运行 `scripts/build_dashboard.py`，将提取的数据与 AI 文字复盘自动注入到 HTML 模板中，生成一站式可视化网页报告。
  - 运行命令示例：
    ```bash
    python scripts/build_dashboard.py \
      --in-json "report_data.json" \
      --analysis-json "analysis.json" \
      --template "templates/dashboard_template.html" \
      --out-html "path/to/输出_数据复盘仪表盘.html"
    ```

- **Step 6: 交付与引导**
  - 告知用户文件已生成，附上生成的 Excel 文件和 HTML Dashboard 的绝对路径链接。
  - 提示用户可在浏览器中直接双击打开 HTML 仪表盘，体验包含留存曲线拖拽缩放、粉丝对比及侧边栏 AI 诊断的动态交互效果。

## 2. 指针与规范索引

在处理时，必须查阅并遵守以下资源：
- **数据勘误与文件结构** ➔ [references/data-schema.md](file:///references/data-schema.md)
- **文字分析报告深度与格式** ➔ [references/analysis-framework.md](file:///references/analysis-framework.md)
