#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sanitize_analysis.py — analysis.json 合法性保障脚本

第一性原理：AI 直接将包含自然语言文字的分析内容写成 JSON 文本时，
文字中天然存在的 ASCII 双引号（如 "前言税"、"引用词"）不会被自动转义，
导致 json.load() 抛出 JSONDecodeError。

本脚本的职责：
  读取 AI 生成的原始 analysis.json → 用 Python json 模块重新序列化 → 
  写回磁盘，确保输出文件是严格合法的 JSON。

若原始文件本身就是合法 JSON，则本脚本是幂等的（no-op）。
若原始文件是非法 JSON，则打印详细错误信息并以非零状态码退出，
阻止后续 build_dashboard.py 以静默 fallback 方式掩盖问题。

用法：
    python3 sanitize_analysis.py --analysis-json "path/to/analysis.json"
"""

import json
import argparse
import sys
import os

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and re-serialize analysis.json to guarantee JSON compliance."
    )
    parser.add_argument(
        "--analysis-json",
        required=True,
        help="Path to the analysis JSON file to sanitize (edited in-place)."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = args.analysis_json

    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    # Attempt 1: direct parse — if this succeeds, file is already valid
    try:
        data = json.loads(raw)
        # Re-serialize with json.dumps to normalize formatting
        clean = json.dumps(data, ensure_ascii=False, indent=2)
        with open(path, "w", encoding="utf-8") as f:
            f.write(clean)
        print(f"[sanitize_analysis] OK — {path} is valid JSON. Re-serialized in-place.")
        sys.exit(0)
    except json.JSONDecodeError as e:
        print(
            f"[sanitize_analysis] ERROR — Invalid JSON detected in {path}.\n"
            f"  Cause   : {e}\n"
            f"  Position: line {e.lineno}, col {e.colno} (char {e.pos})\n"
            f"  Context : {repr(raw[max(0, e.pos - 80):e.pos + 80])}\n",
            file=sys.stderr
        )
        print(
            "  Diagnosis: The AI likely wrote unescaped ASCII double-quote characters\n"
            "  inside JSON string values (e.g. 「\"引用词\"」 should be 「\\\"引用词\\\"」).\n"
            "  Fix: Ensure all text content in analysis.json is serialized via\n"
            "  Python's json.dumps(), not written as raw JSON text.",
            file=sys.stderr
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
