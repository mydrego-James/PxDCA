from pathlib import Path
from string import Template
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _bullets(values) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- 無"


def render_audit(payload: dict[str, Any], output_path: str | Path) -> str:
    template = Template((ROOT / "resources" / "templates" / "audit" / "iso-aligned-audit.md").read_text(encoding="utf-8"))
    context = {
        "project_name": payload["project_name"],
        "audit_basis": _bullets(payload.get("audit_basis", [])),
        "blockers": _bullets(payload.get("blockers", [])),
        "major_findings": _bullets(payload.get("major_findings", [])),
        "other_findings": _bullets(payload.get("other_findings", [])),
        "coverage": _bullets(payload.get("coverage", [])),
        "audit_conclusion": payload.get("audit_conclusion", "尚未判定"),
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template.safe_substitute(context), encoding="utf-8", newline="")
    return str(output)
