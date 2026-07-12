# -*- coding: utf-8 -*-
"""
prepare.py — 一键完成"抽取 + 确定性检查"，产出 artifacts 与 det_*.json 证据。

语义检查(由 Claude 按 SKILL.md 并行 subagent 完成)与最终合成(assemble_report.py)不在本脚本内。

用法：
  python prepare.py <docx或doc路径> [run_dir]
"""

from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_docx        # noqa: E402
import deterministic_checks  # noqa: E402


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python prepare.py <docx或doc路径> [run_dir]")
        sys.exit(1)
    docx_path = args[0]
    here = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.normpath(os.path.join(here, ".."))
    default_run = os.path.join(skill_root, "_run",
                               os.path.splitext(os.path.basename(docx_path))[0])
    run_dir = args[1] if len(args) > 1 else default_run

    # 0) 确保索引/要求存在
    idx = os.path.join(here, "references_index.json")
    req = os.path.join(here, "requirements.json")
    if not os.path.exists(idx) or not os.path.exists(req):
        print("[prepare] 缺少索引/要求，先调用 build_reference_index.py 与 parse_requirements.py")
        sys.exit(1)

    # 1) 抽取
    meta = extract_docx.extract(docx_path, run_dir)
    print(f"[prepare] 抽取完成：段落 {meta['paragraphs']}，表格 {meta['tables']}，标题 {len(meta['headings'])}")

    # 2) 确定性检查
    #    复用 deterministic_checks 的函数，避免再次 subprocess
    sys.argv = ["deterministic_checks.py", run_dir]
    deterministic_checks.main()


if __name__ == "__main__":
    main()
