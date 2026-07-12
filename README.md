# 报告智能校审 技能（skill 标识：`design-report-review`）

对水利工程设计报告（Word `.docx`/`.doc`）进行**逐条、可追溯**的智能校审，覆盖 8 大类 42 条检查要求，输出与要求一一对应、引用完整要求原文的校审报告。**默认输出仪表板式 HTML**（顶部横幅 + 左侧目录 + KPI 统计卡 + 问题筛选 + 按类别表格化结论、行级配色），用户指定时输出 Markdown；两种格式均正确渲染上标/下标（如 m³/s、10⁸、km²、H₂O）。

## 目录结构

```
design-report-review/
├── SKILL.md                      技能定义与编排流程（核心）
├── README.md                     本文件
├── 使用说明.html                 用户使用说明（HTML，浏览器打开）
├── references/                   参考/规则（可更新）
│   ├── 检查要求.md               8 大类 42 条检查项与输出要求（权威）
│   ├── 水利标准.md               水利标准现行有效清单
│   └── 法律法规.md               法律法规现行有效清单
├── scripts/
│   ├── lib_docx.py               docx 解析基础库（顺序遍历/合并单元格重建/正则）
│   ├── build_reference_index.py  解析两份清单 → references_index.json
│   ├── extract_docx.py           docx → 结构化 artifacts
│   ├── deterministic_checks.py   机器可验证证据（表格核算/引用对照/有效数字/编号）
│   ├── parse_requirements.py     解析检查要求.md → requirements.json
│   ├── assemble_report.py        由结构化结论 + requirements 合成 Markdown + HTML 报告
│   ├── merge_issues.py           把各组"逐条 issues"按 id 合并回 findings.json
│   ├── page_map.py               用 Word COM 计算每段 Word 页码 → locators.json（可选）
│   ├── prepare.py                一键"抽取+确定性检查"
│   ├── maintain.py               清单维护：一键重建索引/要求（智能/强制/检查/备份）
│   ├── references_index.json     (生成) 标准/法规检索索引
│   └── requirements.json         (生成) 42 条结构化要求
└── _run/<文档名>/                 (生成) 每次运行的 artifacts 与证据
    ├── fulltext.md tables.json captions.json citations.json numbers.json meta.json
    ├── det_table.json det_citations.json det_numbers.json det_numbering.json
    ├── evidence_summary.json     (生成) 喂给语义 subagent 的锚定证据
    └── findings.json             (生成) 各组 subagent 结论
```

## 8 大类 42 条检查项

| 大类 | 编号 | 条数 | 主要数据来源 |
|------|------|------|--------------|
| 强制性条文检查 | mp_001–011 | 11 | 全文(语义) |
| 常见设计问题检查 | ci_* | 9 | 全文 + 排涝模数数值 |
| 一致性检查 | cons_001–003 | 3 | 全文 + 表格 + 数值 |
| 语法表述检查 | gram_001–008 | 8 | 全文 + 题录 |
| 文字规范性检查 | std_001–004 | 4 | 机器证据 det_numbers |
| 设计标准检查 | ds_001–002 | 2 | 机器证据 det_citations + 索引 |
| 法律法规检查 | lr_001–002 | 2 | 机器证据 det_citations + 索引 |
| 表格逻辑关系专项检查 | tbl_001–003 | 3 | 表格网格 + det_table |

## 工作原理（确定性 + 语义 的混合）

1. **抽取**（`extract_docx.py`，确定性）：保留文档顺序，重建合并单元格，产出全文/表格/题录/引用/数值五类结构化 artifacts。
2. **确定性证据**（`deterministic_checks.py`）：高精度产出机器可验证结论——表格统计值核算、标准/法规编号有效性对照清单、流量有效数字、工程等别/级别罗马-阿拉伯、图表编号顺序与格式。**宁可漏报(留给语义)也不误报**。
3. **并行语义检查**（Claude 按 SKILL.md fan-out subagent）：8 类分 7 组并行，逐条判断条文落实、一致性、语法、合理性等需要理解的内容，**优先引用机器证据与原文定位**。
4. **合成**（`assemble_report.py`，确定性）：以 `requirements.json` 为序遍历全部 42 条，确保一一对应、引用完整要求原文；结构与引文来自脚本，结论与依据来自语义。

## 使用方式

### 作为 Claude Code 技能（推荐）
将本目录置于 `.claude/skills/design-report-review/`，随后在对话中：
> 用报告智能校审技能检查 `安徽两湖涝区项建第2、3、5章.docx`

Claude 会读取 `SKILL.md` 并自动执行上述流程，**默认**在同目录生成 `<文档名>_校审报告.html`；若用户要求 Markdown，则生成 `<文档名>_校审报告.md`。

完整的用户使用说明（检查范围 / 输出报告样例 / 清单动态维护）见 [`使用说明.html`](使用说明.html)，浏览器直接打开。

### 手动分步（便于调试/复现）
```bash
cd .claude/skills/design-report-review
# 0) 建索引与要求（仅首次或清单更新后）
python scripts/build_reference_index.py
python scripts/parse_requirements.py
#   一键等价：python scripts/maintain.py --force  （清单更新后日常维护也用 maintain.py，默认只重建改过的）
# 1+2) 抽取 + 确定性检查（生成 fulltext/tables/.../locators.json 等）
python scripts/prepare.py "<docx路径>"
# 1b) 可选：Word 页码定位（Windows+Word；把 P段落号 映射为 Word 页码）
python scripts/page_map.py "_run/<文档名>"
# 3) 语义检查：由 Claude 并行 subagent 完成（产出含 issues 逐条问题+建议），结果写入 _run/<文档名>/findings.json
# 4) 合成报告（默认 html；--format md 出 Markdown；--format both 两者都出）
python scripts/assemble_report.py "_run/<文档名>"            # 默认 HTML
python scripts/assemble_report.py "_run/<文档名>" --format=md  # 只要 Markdown
```

## 设计取舍

- **效率**：抽取与确定性检查为单进程秒级；语义检查按类别并行，墙钟≈最慢一组。
- **严谨**：数值/对照/编号类交由确定性脚本（零臆测），语义类强制引用原文定位与机器证据。
- **可信度**：确定性脚本对易误报场景（kW/台双单位、经验频率列、序号列、多合计行、区间值）仅给 `info`，是否成问题由语义结合网格判定。
- **可移植**：`references/` 可替换为其他行业/版本的清单，索引自动重建。

## 依赖
Python 3 + `python-docx`、`lxml`。`.doc` 转换可选 LibreOffice 或 pywin32。
