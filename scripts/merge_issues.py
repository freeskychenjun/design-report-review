# -*- coding: utf-8 -*-
"""
merge_issues.py — 把若干"逐条 issues"结果(按 id)合并回 findings.json，并按 requirements 顺序重排。

用法：python merge_issues.py <run_dir> <extra1.json> [<extra2.json> ...]
每个 extra 文件为 {"results":[{"id","name","verdict","conclusion","issues":[...]}, ...]}
（grammar 已含 issues 的无需再传；本脚本按 id 覆盖对应条目）
"""

from __future__ import annotations
import json
import os
import sys
from collections import OrderedDict


def main():
    args = sys.argv[1:]
    run_dir = args[0]
    extra_files = args[1:]
    here = os.path.dirname(os.path.abspath(__file__))
    reqs = json.load(open(os.path.join(here, "requirements.json"), encoding="utf-8"))
    id2cat = {r["id"]: r["category"] for r in reqs}
    cat_order = list(OrderedDict.fromkeys(r["category"] for r in reqs))
    ids_by_cat = {}
    for r in reqs:
        ids_by_cat.setdefault(r["category"], []).append(r["id"])

    fpath = os.path.join(run_dir, "findings.json")
    findings = json.load(open(fpath, encoding="utf-8"))
    by_cat = {}
    for grp in findings:
        by_cat[grp["category"]] = {r["id"]: r for r in grp["results"]}

    n_replaced = 0
    for ef in extra_files:
        data = json.load(open(ef, encoding="utf-8"))
        results = data["results"] if isinstance(data, dict) else data
        for r in results:
            rid = r.get("id")
            cat = id2cat.get(rid)
            if not cat or cat not in by_cat:
                print(f"  跳过未知 id: {rid}")
                continue
            # 保留/合并：若新结果缺 issues 而旧的有，保留旧的 issues
            old = by_cat[cat].get(rid, {})
            if not r.get("issues") and old.get("issues"):
                r["issues"] = old["issues"]
            by_cat[cat][rid] = r
            n_replaced += 1

    out = []
    for cat in cat_order:
        if cat not in by_cat:
            continue
        res = [by_cat[cat][i] for i in ids_by_cat.get(cat, []) if i in by_cat[cat]]
        out.append({"category": cat, "results": res})
    json.dump(out, open(fpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total = sum(len(g["results"]) for g in out)
    n_issues = sum(len(r.get("issues", [])) for g in out for r in g["results"])
    print(f"[merge_issues] 覆盖 {n_replaced} 条；findings 共 {total} 条，issues 共 {n_issues} 处")


if __name__ == "__main__":
    main()
