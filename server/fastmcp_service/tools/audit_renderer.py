from pathlib import Path
from string import Template
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _bullets(values) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- 無"


def _coverage_lines(values: list[Any]) -> list[str]:
    lines: list[str] = []
    for item in values:
        if not isinstance(item, dict):
            lines.append(str(item))
            continue
        evidence = "；".join(str(value) for value in item.get("evidence", [])) or "無"
        gap = str(item.get("gap") or "無")
        lines.append(
            f"{item.get('requirement_id', 'N/A')} | {item.get('status', 'unknown')} "
            f"| 證據：{evidence} | 缺口：{gap}"
        )
    return lines


def _finding_lines(values: list[Any]) -> list[str]:
    lines: list[str] = []
    for item in values:
        if not isinstance(item, dict):
            lines.append(str(item))
            continue
        requirement_ids = ", ".join(str(value) for value in item.get("requirement_ids", [])) or "N/A"
        lines.append(
            f"[{item.get('finding_id', 'AUD')}] ({item.get('severity', 'observation')}/"
            f"{item.get('type', 'other')}) {item.get('description', '')} "
            f"| 建議：{item.get('recommendation', '')} | 需求：{requirement_ids}"
        )
    return lines


def render_audit(payload: dict[str, Any], output_path: str | Path) -> str:
    template = Template((ROOT / "resources" / "templates" / "audit" / "iso-aligned-audit.md").read_text(encoding="utf-8"))
    findings = payload.get("findings", [])
    major_findings = [
        item for item in findings
        if isinstance(item, dict) and item.get("severity") in {"blocker", "major"}
    ]
    other_findings = [item for item in findings if item not in major_findings]
    context = {
        "project_name": payload["project_name"],
        "audit_basis": _bullets(payload.get("audit_basis", [])),
        "blockers": _bullets(payload.get("blockers", [])),
        "major_findings": _bullets(_finding_lines(major_findings)),
        "other_findings": _bullets(_finding_lines(other_findings)),
        "coverage": _bullets(_coverage_lines(payload.get("coverage", []))),
        "audit_conclusion": payload.get("conclusion", "draft_pending_review"),
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template.safe_substitute(context), encoding="utf-8", newline="")
    return str(output)
