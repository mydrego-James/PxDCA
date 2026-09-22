#!/usr/bin/env python3
"""Deterministically render PxDCA software specification Markdown files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from string import Template
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
PROFILES = {"simple", "professional", "consultant"}
SCHEMA = json.loads((ROOT / "resources" / "schemas" / "specification-schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


def bullets(values: list[Any], empty: str = "- ??") -> str:
    return "\n".join(f"- {value}" for value in values) if values else empty


def table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "- ??"
    head = "| " + " | ".join(headers) + " |"
    rule = "|" + "|".join("---" for _ in headers) + "|"
    body = ["| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |" for row in rows]
    return "\n".join([head, rule, *body])


def render_requirements(items: list[dict[str, Any]], detailed: bool) -> str:
    blocks = []
    for item in items:
        lines = [
            f"### {item['id']} {item['title']}",
            f"- 說明：{item['description']}",
            f"- 優先級：{item['priority']}",
        ]
        if detailed:
            lines.extend([
                f"- 來源：{item.get('source', '未指定')}",
                "- 業務規則：\n" + bullets(item.get("business_rules", [])),
                "- 例外處理：\n" + bullets(item.get("exceptions", [])),
            ])
        lines.append("- 驗收條件：\n" + bullets(item.get("acceptance", [])))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_context(payload: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    profile = payload["profile"]
    project = payload["project"]
    scope = payload["scope"]
    technical = payload["technical"]
    requirements = payload["requirements"]
    implementation = technical["implementation_items"]
    requirement_ids = {item["id"] for item in requirements}
    covered = {rid for item in implementation for rid in item.get("requirement_ids", [])}
    uncovered = sorted(requirement_ids - covered)
    blocking = [item.get("id", "TBD") for item in payload.get("unresolved_decisions", []) if item.get("blocking")]
    readiness_status = "ready" if not uncovered and not blocking else "not_ready"

    choices = table(
        ["類別", "技術", "理由", "對應需求"],
        [[x.get("category", ""), x.get("technology", ""), x.get("reason", ""), ", ".join(x.get("requirement_ids", []))] for x in technical.get("choices", [])],
    )
    impl = []
    for item in implementation:
        impl.append("\n".join([
            f"### {item.get('id', 'DEV-TBD')} {item.get('title', '')}",
            f"- 實作內容：{item.get('description', '')}",
            f"- 對應需求：{', '.join(item.get('requirement_ids', [])) or '無'}",
            f"- 完成條件：{item.get('done_condition', '未定義')}",
        ]))
    trace = table(
        ["需求 ID", "開發 ID", "驗證方式", "覆蓋狀態"],
        [[rid, item.get("id", ""), item.get("verification", "未定義"), "已覆蓋"] for item in implementation for rid in item.get("requirement_ids", [])]
        + [[rid, "-", "-", "未覆蓋"] for rid in uncovered],
    )
    constraints = "\n".join([
        "### 假設\n" + bullets(payload.get("assumptions", [])),
        "### 範疇外\n" + bullets(scope.get("out", [])),
        "### 未決事項\n" + bullets([f"{x.get('id', 'TBD')}：{x.get('description', '')}" for x in payload.get("unresolved_decisions", [])]),
    ])
    consulting = payload.get("consulting", {})
    context = {
        "project_name": project["name"],
        "document_info": bullets([f"版本：{project['version']}", f"狀態：{project['status']}", f"日期：{project['date']}", f"Profile：{profile}"]),
        "purpose": project["purpose"],
        "stakeholders": bullets(project.get("stakeholders", [])),
        "success_metrics": bullets(project.get("success_metrics", [])),
        "scope": "### 範疇內\n" + bullets(scope["in"]) + "\n\n### 範疇外\n" + bullets(scope["out"]),
        "requirements": render_requirements(requirements, profile != "simple"),
        "nfrs": bullets([f"{x.get('id', 'NFR')} {x.get('description', '')}：{x.get('measure', '未定義')}" for x in payload.get("non_functional_requirements", [])]),
        "constraints": constraints,
        "technical_choices": choices,
        "architecture": technical["architecture"],
        "implementation_items": "\n\n".join(impl) or "- ??",
        "traceability": trace,
        "readiness": bullets([f"狀態：{readiness_status}", f"未覆蓋需求：{', '.join(uncovered) or '無'}", f"卡關未決事項：{', '.join(blocking) or '無'}"]),
        "interfaces": table(["名稱", "方向", "合約", "對應需求"], [[x.get("name", ""), x.get("direction", ""), x.get("contract", ""), ", ".join(x.get("requirement_ids", []))] for x in technical.get("interfaces", [])]),
        "data_dictionary": table(["資料表", "欄位", "型別", "可為空", "主鍵/約束", "對應需求"], [[x.get("table", ""), x.get("column", ""), x.get("type", ""), x.get("nullable", ""), x.get("constraint", ""), ", ".join(x.get("requirement_ids", []))] for x in technical.get("data_dictionary", [])]),
        "security": bullets(technical.get("security", [])),
        "deployment": bullets(technical.get("deployment", [])),
        "test_strategy": bullets(technical.get("test_strategy", [])),
        "alternatives": bullets(consulting.get("alternatives", [])),
        "architecture_decisions": bullets(consulting.get("architecture_decisions", [])),
        "cost_and_schedule": bullets(consulting.get("cost_and_schedule", [])),
        "risk_register": bullets(consulting.get("risk_register", [])),
        "governance": bullets(consulting.get("governance", [])),
        "migration": bullets(consulting.get("migration", [])),
        "rollback": bullets(consulting.get("rollback", [])),
        "review_decisions": bullets(consulting.get("review_decisions", [])),
    }
    readiness = {"profile": profile, "status": readiness_status, "uncovered_requirements": uncovered, "blocking_tbd": blocking}
    return context, readiness


def render(payload: dict[str, Any], output_dir: Path) -> list[Path]:
    errors = sorted(VALIDATOR.iter_errors(payload), key=lambda error: list(error.absolute_path))
    if errors:
        detail = "; ".join(f"{'/'.join(map(str, error.absolute_path)) or '$'}: {error.message}" for error in errors[:10])
        raise ValueError(f"Specification payload failed schema validation: {detail}")
    profile = payload.get("profile")
    if profile not in PROFILES:
        raise ValueError(f"Unsupported profile: {profile!r}")
    context, readiness = build_context(payload)
    template_dir = ROOT / "resources" / "templates" / "specification" / profile
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for kind in ("requirements", "technical"):
        source = Template((template_dir / f"{kind}.md").read_text(encoding="utf-8"))
        target = output_dir / f"{kind}_{profile}.md"
        target.write_text(source.safe_substitute(context), encoding="utf-8", newline="")
        outputs.append(target)
    readiness_path = output_dir / "readiness.json"
    readiness_path.write_text(json.dumps(readiness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")
    outputs.append(readiness_path)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
    for output in render(payload, args.output_dir):
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
