#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import argparse
import sys
import os
from typing import Any

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render interactive HTML dashboard.")
    parser.add_argument("--in-json", required=True, help="Path to input computed JSON data")
    parser.add_argument("--analysis-json", required=True, help="Path to AI analysis JSON data")
    parser.add_argument("--template", required=True, help="Path to HTML template file")
    parser.add_argument("--out-html", required=True, help="Path to save output HTML dashboard")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    
    # Load raw computed report data
    with open(args.in_json, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
        
    # Load AI text analysis with robust fallbacks
    analysis_data: dict[str, Any] = {
        "diagnostic_card": {
            "core_定性": "未检测到针对本期视频的 AI 核心定性诊断卡。",
            "physical_actions": ["未检测到优化动作建议。"],
            "next_topic_recommendation": "未检测到选题上演进方向建议。"
        },
        "creation_perspective": [],
        "ops_perspective": []
    }
    
    if os.path.exists(args.analysis_json):
        try:
            with open(args.analysis_json, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                # Overwrite defaults where present
                if "diagnostic_card" in loaded_data:
                    analysis_data["diagnostic_card"] = loaded_data["diagnostic_card"]
                if "creation_perspective" in loaded_data:
                    analysis_data["creation_perspective"] = loaded_data["creation_perspective"]
                if "ops_perspective" in loaded_data:
                    analysis_data["ops_perspective"] = loaded_data["ops_perspective"]
        except json.JSONDecodeError as e:
            # Do NOT silently fall back — surface the root cause clearly.
            # Root cause: AI wrote analysis.json as raw JSON text, and natural-language
            # content (e.g. 「"引用词"」) contains unescaped ASCII double-quote characters.
            # Fix: run `scripts/sanitize_analysis.py` before this script, or ensure
            # analysis.json is serialized via Python's json.dumps() rather than written
            # as hand-crafted JSON text.
            print(
                f"FATAL: analysis.json contains invalid JSON and cannot be loaded.\n"
                f"  Error   : {e}\n"
                f"  Position: line {e.lineno}, col {e.colno} (char {e.pos})\n"
                f"  Likely cause: unescaped ASCII double-quote characters inside string values.\n"
                f"  Fix: run  python3 scripts/sanitize_analysis.py --analysis-json \"{args.analysis_json}\"  first.",
                file=sys.stderr
            )
            sys.exit(2)
        except Exception as e:
            print(f"FATAL: Unexpected error loading analysis JSON: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        print(f"Warning: Analysis file '{args.analysis_json}' not found. Rendering dashboard with default placeholder content.", file=sys.stderr)
        
    # Merge analysis into report data
    report_data["ai_analysis"] = analysis_data
    
    # Read HTML Template
    with open(args.template, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    # Inject serialized JSON data
    serialized_data = json.dumps(report_data, ensure_ascii=False, indent=2)
    # Prevent XSS injection by escaping </script> tags in the JSON
    serialized_data = serialized_data.replace("</script>", r"<\/script>")
    rendered_content = html_content.replace("{{DATA_PLACEHOLDER}}", serialized_data)
    
    # Create output directory if it does not exist
    out_dir = os.path.dirname(args.out_html)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        
    # Write to target HTML file
    with open(args.out_html, 'w', encoding='utf-8') as f:
        f.write(rendered_content)
        
    print(f"HTML Dashboard successfully generated at: {args.out_html}")

if __name__ == "__main__":
    main()
