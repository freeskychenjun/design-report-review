---
name: design-report-review
description: 对水利工程设计报告（Word .docx/.doc）进行智能校审。按"检查要求.md"中强制性条文、常见设计问题、一致性、语法表述、文字规范性、设计标准、法律法规、表格逻辑关系共8大类42条逐项检查，输出与要求一一对应、引用完整要求原文的校审报告。默认输出仪表板式 HTML（顶部横幅+左侧目录+KPI统计卡+问题筛选+按类别表格化结论、行级配色），用户指定时输出 Markdown；两种格式均正确渲染上标/下标（如 m³/s、10⁸、km²、H₂O）。触发词：校审/审查/检查 报告、报告智能校审、docx校审、设计报告检查、校审报告。
---

# 报告智能校审 · 技能说明

本技能对一份水利工程设计报告（项目建议书/可研/初设等，Word 文档）执行**逐条、可追溯**的智能校审，覆盖 `references/检查要求.md` 的 **8 大类 42 条**检查要求，并按其"检查结果输出要求"产出校审报告：**默认输出 HTML**（用户明确要求 Markdown 时输出 Markdown）。每条要求都一一对应、不遗漏（即使全部符合也输出主要分析结论），并引用完整的各检查项要求原文。两种格式均**正确渲染上标/下标**（m3/s→m³/s、10的8次方→10⁸、km²、H2O→H₂O 等）。HTML 版为**仪表板式**：顶部横幅 + 左侧目录（滚动高亮）+ KPI 统计卡 + 问题筛选（全部/仅存在问题/仅不符合）+ 按类别表格化结论（每条一行、行级配色），便于速览与归档。

> 设计要点：**确定性脚本**负责抽取与机器可验证的硬证据（数值、引用对照、表格核算、编号顺序），**并行 subagent** 负责语义判断（条文落实、一致性、语法、合理性）。二者结合保证严谨与高效。

---

## 0. 运行环境与路径

- 技能根目录（下称 `$SKILL`）= 本 SKILL.md 所在目录。
- 依赖：Python 3 + `python-docx`、`lxml`（已随环境安装）。Windows 下 `.doc` 转换可选依赖 LibreOffice 或 pywin32。
- 关键脚本：`$SKILL/scripts/` 下的 `build_reference_index.py`、`extract_docx.py`、`deterministic_checks.py`、`parse_requirements.py`。
- 参考/索引（首次运行自动生成）：`$SKILL/scripts/references_index.json`、`$SKILL/scripts/requirements.json`。
- 运行产物目录：`$SKILL/_run/<文档名去后缀>/`。

如索引/要求文件缺失，先运行：
```bash
cd "$SKILL" && python scripts/maintain.py --force   # 一键（等价于分别跑 build_reference_index.py + parse_requirements.py）
```

---

## 1. 流程总览（5 步）

```
[输入 docx]
   │  ① 抽取  extract_docx.py
   ▼
artifacts: fulltext.md / tables.json / captions.json / citations.json / numbers.json / meta.json
   │  ② 确定性检查  deterministic_checks.py
   ▼
证据: det_table.json / det_citations.json / det_numbers.json / det_numbering.json
   │  ③ 并行语义检查（按8大类 fan-out subagent，每类1个；轻量类可合并）
   ▼
各条结构化结论 (id → 结论/依据/定位)
   │  ④ 合成报告（逐条对应 + 引用原文 + 即使符合也写结论；默认 .html，用户指定时 .md）
   ▼
[输出 <文档名>_校审报告.html（默认）/ <文档名>_校审报告.md（用户指定时）]
```

### ① 抽取
```bash
python "$SKILL/scripts/extract_docx.py" "<docx或doc路径>" ["<输出目录>"]
```
默认输出到 `$SKILL/_run/<文档名>/`。`.doc` 会自动尝试转换；转换失败则提示用户另存为 `.docx`。
抽取同时生成 `locators.json`：每段最近**章节标题**、每表**题录号(表X.X.X)** 映射。

### ①b 页码定位（可选，需 Windows + Word）
```bash
python "$SKILL/scripts/page_map.py" "$SKILL/_run/<文档名>"
```
用 Word COM 计算每个顶层段落对应的 **Word 页码**，回填 `locators.json` 的 `page_by_para`（无 Word 时跳过，定位自动回退为章节标题§）。合成时 `P0154`→`第16页`、`T039`→`表3.7.2.2`。

### ② 确定性检查
```bash
python "$SKILL/scripts/deterministic_checks.py" "$SKILL/_run/<文档名>"
```
产出四份 `det_*.json` 证据并打印摘要。**这些证据是数值类、对照类检查的权威依据，subagent 必须优先引用。**

### ③ 并行语义检查（效率核心）
将 42 条要求按**类别**分为若干组，**同一条消息内并发启动多个 subagent**（Agent 工具一次发多个调用；或使用 Workflow 工具）。每个 subagent 只读取本类所需 artifacts/证据，互不阻塞。建议分组（轻量类 `ds_*`、`lr_*` 可合并为一组）：

| 组 | 检查项 | 主用 artifacts | 主用证据 |
|----|--------|----------------|----------|
| A 强制性条文 | mp_001–011 | fulltext.md | （语义判断） |
| B 常见设计问题 | ci_flood/runoff/stage/water/drainage | fulltext.md、numbers.json、tables.json | det_numbers(排涝模数) |
| C 一致性 | cons_001–003 | fulltext.md、tables.json、numbers.json | — |
| D 语法表述 | gram_001–008 | fulltext.md、captions.json | det_numbering.json |
| E 文字规范 | std_001–004 | det_numbers.json、fulltext.md | det_numbers.json |
| F 设计标准+法律法规 | ds_001–002、lr_001–002 | det_citations.json | det_citations.json + references_index.json |
| G 表格逻辑 | tbl_001–003 | tables.json | det_table.json |

> 每组 subagent 用 Read 工具按需读取上表文件（避免一次性加载全部大文件）。`fulltext.md` 用 Grep/分段 Read 定位关键词。

### ④ 合成报告
收集所有 subagent 的结构化结论，与 `requirements.json` 比对，**确保 42 条全覆盖**（缺失项补查），再运行 `assemble_report.py` 合成报告（默认 HTML；用户明确要求 Markdown 时加 `--format md`，见第 4 节格式）。

---

## 2. 产物与证据字段速查

- **fulltext.md**：全文，每段前缀 `P0123`（段落序号）/`[H3]`（标题层级）；表格以 `【表012】(r×c) 题录（详见 tables.json#12）` 标记。→ 用于语义判断与定位引用。
- **tables.json**：`[{id,pid,caption,nrows,ncols,header,grid,section}]`，`grid` 为二维文本（合并单元格已重建）。→ 表格检查直接读 grid。
- **captions.json**：`[{type:图|表,num,text,is_def,para_idx,section}]`。→ 题录/编号检查。
- **citations.json**：`[{kind,std|law|law_code|std_name_only,raw,norm_code,name,norm_name,para_idx,context}]`。→ 引用检查的原始数据。
- **numbers.json**：`[{key:flows|moduli|areas_km2|areas_mu|bigunits|pow10,value,raw,para_idx,context}]`。
- **det_table.json**：每表 `{id,caption,n_checks,n_fail,n_warn,checks:[{type,stated,computed,status,note}]}`。`status` 含 `pass/fail/warn/info`；`info`（行平均、极值、多合计行/列）为机器核算供语义复核，**不直接判错**。
- **det_citations.json**：`{citations:[{kind,raw,norm_code,name,validity,note,...}],consistency:[...],summary}`。`validity`：`valid/not_in_list/year_mismatch/valid_name`。
- **det_numbers.json**：`std003_flow`(流量有效数字违规)、`std001_bigunit`(大数单位形式)、`std004_grade`(等别/级别罗马-阿拉伯)。
- **det_numbering.json**：`{图/表:{count,formats,format_inconsistent,issues}}`。
- **references_index.json**：标准/法规按 `norm_code`、`norm_name`、`prefix_num` 检索。
- **requirements.json**：`[{category,subcategory,id,name,content}]`（42 条）。

---

## 3. Subagent 提示模板与输出 schema

给每个 subagent 的提示（按组填充 `<...>`）：

```
你是水利工程设计报告校审专家。请对以下检查要求【逐条】给出结论。
只使用我提供的 artifacts/证据 与文档原文，禁止臆测；每条结论必须给出文档中的定位(段落号 PXXXX / 表号 / 题录)与原文片段作为依据。

【本组检查要求】（必须全部覆盖，逐条响应）：
<粘贴 requirements.json 中本组各条 的 id/name/content 原文>

【可用数据】（按需用 Read/Grep 读取，路径相对运行目录）：
- 全文：$SKILL/_run/<文档名>/fulltext.md
- 表格：$SKILL/_run/<文档名>/tables.json
- …（按组列出上表中的 artifacts/证据文件）

【确定性证据摘要】（优先引用，避免与机器核算冲突）：
<粘贴对应 det_*.json 中与本组相关的条目/摘要>

【判定口径】
- 符合：报告完整满足该要求。
- 部分符合：基本满足但存在不足/疏漏。
- 不符合：存在明确问题或缺失。
- 不适用：该要求不适用于本文档（须说明原因）。
- 即便全部符合，也要写出主要分析结论与支撑定位。
- 涉及数值/标准/法规时，以 det_*.json 与 references_index.json 为准。

【具体问题清单——关键要求，避免空泛】
对"部分符合/不符合"的检查项，**必须**逐处列出具体问题（不要只写"需逐处订正"这类空话），每条给：
- loc：段落号 PXXXX（合成时会自动转成 Word 页码"第N页"）
- original：从原文**精确照抄**的问题片段（含错字/原样）
- type：问题类型（2-6字，如"叠字/错字/标点/量纲/前后矛盾/编号倒置"）
- suggestion：**逐字修改建议**——直接给出修改后的文字 + 简述改法（如 original="进行了了技术改造" suggestion="进行了技术改造（删去重复的'了'）"）
尽量穷尽明显问题（每项可多条，宁缺毋滥、不编造）。语法表述(gram_*)、文字规范(std_*)、表格(tbl_*)、一致性(cons_*)等尤其需要这种可操作清单。

【输出】严格输出 JSON（仅 JSON）：
{"category":"<组名>","results":[
  {"id":"<编号>","name":"<名称>","verdict":"符合|部分符合|不符合|不适用",
   "conclusion":"<结论，含主要分析>","evidence":[{"loc":"<定位>","quote":"<原文片段>"}],
   "issues":[{"loc":"P0238","original":"…","type":"叠字","suggestion":"…"}]}
]}
```


> subagent 若发现某条要求需补充数据，可自行 Read 对应文件。收齐 8 组 JSON 后进入合成。

---

## 4. 报告输出格式（严格遵守"检查结果输出要求"）

- 与要求**一一对应、不遗漏**：按 `requirements.json` 顺序，42 条全部出现；与 subagent 结论比对，缺失立即补查。
- **引用完整要求原文**：每条在结论前以引用块给出该条要求全文（取自 requirements.json 的 content；强制性条文条目含规范条款原文）。
- 即便符合，也写"主要分析结论"。
- **默认输出 HTML**，保存到**输入文档同目录**：`<文档名>_校审报告.html`（**仪表板式**：顶部横幅 + 左侧目录(滚动高亮) + KPI 统计卡(总数/符合/存在问题/符合率) + 问题筛选(全部/仅存在问题/仅不符合) + 按类别表格化结论(列：检查项｜要求｜检查结果｜说明/建议，每条一行、行级配色 绿/橙/红/灰、有问题内容红色粗体)，说明/建议列只给结论与建议（不单列定位依据引用），浏览器直接打开/归档、支持打印）。
- **用户明确要求 Markdown 时**才输出 `<文档名>_校审报告.md`。
- 由 `assemble_report.py` 控制：默认 `--format html`；`--format md` 出 Markdown；`--format both` 两者都出。
- **两种格式均正确渲染上标/下标**：`m3/s`→m³/s、`10的8次方`→10⁸、`km2/km²`→km²、`H2O`→H₂O、`SO4`→SO₄ 等。HTML 用 `<sup>`/`<sub>` 标签，Markdown 用 GFM 内联 `<sup>`/`<sub>` 标签（在 GitHub/VSCode/Typora/Obsidian 等渲染器中正确显示）。

模板：

```markdown
# 《<文档名>》智能校审报告

- 文件：<文档名>　段落：<n>　表格：<n>　标题：<n>
- 校审依据：检查要求.md（8 大类 42 条）；标准清单：水利标准.md；法规清单：法律法规.md
- 生成方式：确定性脚本 + 并行语义检查

## 一、强制性条文检查
### mp_001 设计洪水计算过程检查
> **要求**：《水利水电工程设计洪水计算规范》1.0.9：……（完整原文）
**结论**：符合 / 部分符合 / 不符合
**依据**：P0123「……原文片段……」；……
（…… mp_002 … mp_011 ……）

## 二、常见设计问题检查
### ci_drainage_001 排涝模数合理性分析
> **要求**：对设计排涝流量要进行合理性分析：5年一遇农田涝区0.50～0.65m³/s·km²……
**结论**：部分符合
**依据**：numbers.json 记录排涝模数54处；其中 P0586「排涝模数0.33m³/s/km2，不足5年一遇」低于5年一遇农田下限0.50；P…「3.2、4.4」显著超城镇20年一遇上限1.40，需核实……

## 三、一致性检查 / 四、语法表述检查 / 五、文字规范性检查 / 六、设计标准检查 / 七、法律法规检查 / 八、表格逻辑关系专项检查
（同样格式，逐条展开）

---
## 校审结果汇总
| 类别 | 条数 | 符合 | 部分符合 | 不符合 | 不适用 |
| ... | ... | ... | ... | ... | ... |
```

---

## 5. 效率与降级

- **首选并行**：在**一条消息内**同时发起多组 subagent（Agent 工具并发，或 Workflow 工具）。8 组可同时跑，墙钟≈最慢一组。
- **大文件**：fulltext.md 较大时，subagent 用 Grep 定位关键词后再分段 Read，勿整文件灌入。
- **降级**：若无法并发，按 A→G 顺序逐组串行，结果不变。
- **证据优先**：凡 det_*.json 已给出的结论（如 std_003 流量有效数字、ds 标准有效性、gram_007 编号格式不一致），subagent 直接引用、不重复人工核算，避免误判。

---

## 6. 边界与注意

- `.doc`（旧二进制）：脚本自动尝试 LibreOffice/Word 转换；失败则要求用户另存 `.docx`。
- 表格合并单元格已重建为二维网格；`det_table` 对多合计行/列、kW/台双单位、区间值等只给 `info`，**是否成问题由 G 组 subagent 结合 grid 判定**。
- 引用清单为"现行有效版本"参考；`not_in_list` 可能是地方/行业外标准或内部技术文件，subagent 应区分"编号错误/已废止"与"非本清单范围但合理"。
- 强制性条文（mp_*）判"落实"须以正文是否对该环节做了分析/论证为准，并给出定位；不得仅因提及规范名即判符合。
