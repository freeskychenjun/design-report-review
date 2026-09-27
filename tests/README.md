# 回归测试集与门禁（design-report-review）

## 组成

```
tests/
  regression_check.py   门禁脚本（findings / artifacts 两种模式）
  golden/
    shanxu/   山许水库项目建议书（小文档代表，109 处问题，2026-09-27 冻结）
    anhui/    安徽两湖涝区项建第2、3、5章（超大文档，236 处问题，2026-09-27 冻结）
      artifacts/          抽取产物 + det_*.json + _slices/（冻结切片）
      findings_golden.json 金标准结论
      golden_meta.json     冻结记录（版本/来源/原因）
```

## 用法

```bash
# findings 门禁（改了提示词/分组/collect/polish 后必跑）
python tests/regression_check.py findings <run_dir> --golden tests/golden/anhui

# artifacts 比对（改了 extract/det/slice 后必跑；预期变更用 --allow 豁免）
python tests/regression_check.py artifacts <run_dir> --golden tests/golden/anhui --allow groupC
```

退出码 0=PASS，1=FAIL。**FAIL 即回滚或修复；不得为放行而放宽门槛。**

## 门禁五项检查（findings 模式）

1. 42 条全覆盖、未检出=0
2. verdict 翻转分类：放宽（部分符合/不符合 → 符合/不适用）= FAIL（漏报信号）；收紧/新覆盖 = WARN
3. issue 数量下限：金标准 ≥5 条的项须 ≥80%；<5 条的项容差 n-2
4. 反幻觉抽查（确定性采样 ≤40 条）：issue.original 的片段必须在 fulltext/tables/captions 中找到
   （空白不敏感、上下标归一、引文片段抽取、数据型对照验数字），loc 段落号必须存在
5. 机器黑话残留 = 0

## 校准记录（2026-09-27）

- 双金标准自测 PASS；artifacts 自一致 PASS。
- 负样本校准：以 7 月旧结论冒充新结果 → 正确 FAIL（3 条放宽翻转 + 21 项 issue 不足 + 总量 136<80%×236）。
- 门禁自身抓到的真问题：金标准 mp_002 的 P0446 段落号写岔（实为 P0445，subagent off-by-one，
  已修正冻结）；山许金标准 5 条机器黑话残留（polish 规则盲区，已补规则并重清洗）。

## 杠杆 3 实验记录（det 疑点候选攻 C 组，2026-09-27，结论：两案皆否）

1. **预扫替代通读**：召回实测仅 46/163=28%（语病/歧义/逻辑/常识类为 0，必须语义阅读）→ 否决。
2. **候选核实+通读并存**：C 组实测 1711s / 5.8M tokens（基线 893s / 1.3M），候选核实成为
   额外一遍工作；issues 226>163 且过门禁（质量面合格），但效率面回退 → **切片集成已回退**，
   det_suspects.json 生成器保留作诊断工具（叠字类召回 5/6 值得后续做 det 直出实验）。
3. 附带产出：v3 的 226 条 C 组问题过门禁后已用于升级安徽两湖交付报告（总 299 条问题）。

## 新增金标准流程

选一个有代表性的新报告 → 跑完整管线（含 subagent）→ 人工抽查 findings 质量 →
`cp -r <run_dir>/artifacts tests/golden/<名>/ && cp <run_dir>/findings.json tests/golden/<名>/findings_golden.json`
→ 写 golden_meta.json → 用门禁自测校准。
