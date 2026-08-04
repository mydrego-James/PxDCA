import hashlib
import json
from pathlib import Path
from string import Template
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CATEGORY_LABELS = {
    "business": "業務需求",
    "functional": "功能需求",
    "data": "資料需求",
    "integration": "整合需求",
    "security": "安全需求",
    "non_functional": "非功能需求",
    "deployment": "部署需求",
}
COVERAGE_LABELS = {
    "covered": "已覆蓋",
    "partial": "部分覆蓋",
    "unresolved": "待解決",
}
CONFIDENCE_LABELS = {"low": "低", "medium": "中", "high": "高"}


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _bullets(values) -> str:
    filtered = [value for value in values if _has_content(value)]
    return "\n".join(f"- {value}" for value in filtered) if filtered else "- 無"


def render_requirement_spec(payload: dict[str, Any], output_path: str | Path) -> dict[str, str]:
    template = Template((ROOT / "resources" / "templates" / "delivery" / "requirement-spec.md").read_text(encoding="utf-8"))
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    project = payload.get("project", {}) if isinstance(payload.get("project"), dict) else {}
    project_name = payload.get("project_name") or project.get("name") or "需求規格專案"
    project_topic = project.get("topic") or project_name
    project_summary = project.get("summary") or project.get("purpose") or f"本專案主題為「{project_topic}」。"
    project_objective = project.get("objective") or project.get("purpose") or "依已確認需求建立可實作、可驗收的系統基準。"
    target_users = project.get("target_users", [])
    if isinstance(target_users, str):
        target_users = [target_users]

    identity_items = [
        f"需求會話追蹤 ID：{payload.get('source_requirement_session_id', 'N/A')}",
        f"文件階段：{payload.get('stage', 'batch_audit_draft')} (版本 {payload.get('schema_version', '1.0')})",
        f"狀態：{payload.get('status', 'draft')}",
    ]

    parties_items = [
        "甲方 (需求提出方)：業務與使用者代表",
        "乙方 (技術交付方)：LogicMCP 自動化架構師團隊",
    ]

    overview_lines = [
        f"**專案主題：** {project_topic}",
        f"**專案摘要：** {project_summary}",
        f"**建置目標：** {project_objective}",
    ]
    if target_users:
        overview_lines.append("**目標使用者：** " + "、".join(str(item) for item in target_users if _has_content(item)))

    core_reqs = payload.get("core_requirements", [])
    requirement_blocks: list[str] = []
    if core_reqs:
        for req in core_reqs:
            if not isinstance(req, dict) or not _has_content(req.get("description")):
                continue
            req_id = str(req.get("id") or "REQ")
            title = str(req.get("title") or f"{req_id} 已確認需求").strip()
            category_code = str(req.get("category") or "functional").strip()
            category = f"{CATEGORY_LABELS.get(category_code, category_code)} ({category_code})"
            rationale = str(req.get("rationale") or "本項為訪談中已確認且影響專案範圍的需求。").strip()
            source = str(req.get("source_boundary") or "未提供").strip()
            requirement_blocks.append(
                f"### {req_id}｜{title}\n\n"
                f"- **需求類別：** {category}\n"
                f"- **需求描述：** {str(req['description']).strip()}\n"
                f"- **需求目的：** {rationale}\n"
                f"- **追溯來源：** {source}"
            )
    else:
        facts = payload.get("facts", {})
        if facts:
            for k, v in facts.items():
                if not _has_content(v):
                    continue
                if isinstance(v, dict) and "value" in v:
                    value = v.get("value")
                    if not _has_content(value):
                        continue
                    source = v.get("source")
                    source_text = str(source) if _has_content(source) else "未提供"
                    requirement_blocks.append(
                        f"### {k}\n\n- **需求描述：** {value}\n- **追溯來源：** {source_text}"
                    )
                else:
                    requirement_blocks.append(f"### {k}\n\n- **需求描述：** {v}")

    scope = payload.get("scope", {}) if isinstance(payload.get("scope"), dict) else {}
    in_scope = scope.get("in_scope", [])
    out_of_scope = scope.get("out_of_scope", [])
    if not in_scope:
        in_scope = [req.get("title") or req.get("description") for req in core_reqs if isinstance(req, dict)]
    if not out_of_scope:
        out_of_scope = [item.get("title") or item.get("description") for item in payload.get("add_on_services", []) if isinstance(item, dict)]
    scope_overview = "### 納入本階段\n\n" + _bullets(in_scope)
    scope_overview += "\n\n### 不納入本階段\n\n" + _bullets(out_of_scope)

    addon_blocks: list[str] = []
    addons = payload.get("add_on_services", [])
    if addons:
        for add in addons:
            if not isinstance(add, dict) or not _has_content(add.get("description")):
                continue
            add_id = str(add.get("id") or "EXT")
            title = str(add.get("title") or "後續擴充項目")
            reason = str(add.get("reason") or "本項目尚未納入當前交付基準。")
            addon_blocks.append(
                f"### {add_id}｜{title}\n\n"
                f"- **項目說明：** {str(add['description']).strip()}\n"
                f"- **延後原因：** {reason}"
            )

    dep_items = [item for item in payload.get("unresolved_items", []) if _has_content(item)]

    change_items = [
        "所有範疇變更須經由雙方代表簽署 CR (Change Request) 變更單"
    ]

    approval_items = ["需求負責人：待簽核"]

    context = {
        "project_name": project_name,
        "document_identity": _bullets(identity_items),
        "project_overview": "\n\n".join(overview_lines),
        "scope_overview": scope_overview,
        "requirements": "\n\n".join(requirement_blocks) if requirement_blocks else "- 無已確認需求",
        "parties_and_roles": _bullets(parties_items),
        "add_on_services": "\n\n".join(addon_blocks) if addon_blocks else "- 無",
        "customer_dependencies": _bullets(dep_items),
        "change_control": _bullets(change_items),
        "baseline_and_approval": _bullets([f"SHA-256：{digest}", *approval_items]),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template.safe_substitute(context), encoding="utf-8", newline="")
    return {"path": str(output), "sha256": digest}


def render_planning_spec(payload: dict[str, Any], output_path: str | Path) -> dict[str, str]:
    template = Template((ROOT / "resources" / "templates" / "delivery" / "planning-spec.md").read_text(encoding="utf-8"))
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    project = payload.get("project", {}) if isinstance(payload.get("project"), dict) else {}
    project_name = payload.get("project_name") or project.get("name") or "技術規劃專案"
    project_purpose = project.get("purpose") or "依已確認需求建立技術對應與實作方向。"

    identity_items = [
        f"文件階段：technical_alignment_draft (版本 {payload.get('schema_version', '1.0')})",
        f"狀態：{payload.get('status', 'draft')}"
    ]

    arch = payload.get("architecture_outline", [])
    architecture_text = _bullets(arch)

    alignment_blocks: list[str] = []
    req_align = payload.get("requirement_alignment", [])
    for item in req_align:
        if not isinstance(item, dict):
            continue
        rid = item.get("requirement_id", "")
        cov_status = item.get("coverage_status", "covered")
        coverage_label = f"{COVERAGE_LABELS.get(cov_status, cov_status)} ({cov_status})"
        notes = item.get("notes", "")
        implications = item.get("technical_implications", [])
        architecture_acceptance = item.get("architecture_acceptance_criteria", [])
        acceptance_text = _bullets(architecture_acceptance).replace("\n", "\n  ")
        alignment_blocks.append(
            f"### {rid}｜{item.get('summary') or '需求技術對應'}\n\n"
            f"- **覆蓋狀態：** {coverage_label}\n"
            f"- **技術實作要點：**\n  {_bullets(implications).replace(chr(10), chr(10) + '  ')}\n"
            f"- **架構驗收條件：**\n  {acceptance_text}\n"
            f"- **說明與限制：** {notes or '無額外說明'}"
        )

    decision_blocks: list[str] = []
    for tc in payload.get("technical_choices", []):
        if not isinstance(tc, dict) or not _has_content(tc.get("proposal")):
            continue
        req_ids = tc.get("requirement_ids", [])
        decision_blocks.append(
            f"### {tc.get('area') or '技術決策'}\n\n"
            f"- **建議方案：** {tc.get('proposal')}\n"
            f"- **選擇理由：** {tc.get('rationale') or '未提供'}\n"
            f"- **信心等級：** {CONFIDENCE_LABELS.get(tc.get('confidence'), tc.get('confidence') or '未評估')}\n"
            f"- **對應需求：** {'、'.join(str(item) for item in req_ids) if req_ids else '未指定'}"
        )

    unresolved_blocks: list[str] = []
    for item in payload.get("unresolved_decisions", []):
        if isinstance(item, dict):
            unresolved_blocks.append(
                f"### {item.get('id') or 'TBD'}\n\n"
                f"- **待決內容：** {item.get('description') or '未提供'}\n"
                f"- **是否阻斷後續：** {'是' if item.get('blocking') else '否'}"
            )
        elif _has_content(item):
            unresolved_blocks.append(f"- {item}")

    maint_items = []
    limitations = payload.get("limitations", [])
    for lim in limitations:
        maint_items.append(f"維護/限制聲明：{lim}")
    if not maint_items:
        maint_items = ["交付後提供標準 30 天維運平穩期移交支援"]

    legal_items = payload.get("legal_review_items", [])
    if not legal_items:
        legal_items = [
            "本草案由演算法自動繪製生成，未經法務簽核前不具備最終法律約束力",
            "智財權歸屬與商業授權需依最終合約約定條款為準"
        ]

    approval_items = ["技術負責人：待簽核"]

    context = {
        "project_name": project_name,
        "document_identity": _bullets(identity_items),
        "project_overview": f"**專案名稱：** {project_name}\n\n**技術目標：** {project_purpose}",
        "architecture": architecture_text,
        "requirement_alignment": "\n\n".join(alignment_blocks) if alignment_blocks else "- 無需求對應資料",
        "technical_decisions": "\n\n".join(decision_blocks) if decision_blocks else "- 無已確認技術決策",
        "assumptions": _bullets(payload.get("assumptions", [])),
        "unresolved_decisions": "\n\n".join(unresolved_blocks) if unresolved_blocks else "- 無",
        "maintenance_handover_termination": _bullets(maint_items),
        "legal_review_items": _bullets(legal_items),
        "baseline_and_approval": _bullets([f"SHA-256：{digest}", *approval_items]),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template.safe_substitute(context), encoding="utf-8", newline="")
    return {"path": str(output), "sha256": digest}


def render_enterprise_delivery(payload: dict[str, Any], output_path: str | Path) -> dict[str, str]:
    template = Template((ROOT / "resources" / "templates" / "delivery" / "enterprise-delivery-baseline.md").read_text(encoding="utf-8"))
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    project = payload.get("project", {}) if isinstance(payload.get("project"), dict) else {}
    project_name = payload.get("project_name") or project.get("name") or "需求規格專案"
    purpose = project.get("purpose") or ""

    # Document Identity
    identity_items = payload.get("document_identity", [])
    if not identity_items:
        session_id = payload.get("source_requirement_session_id", "N/A")
        stage = payload.get("stage", "draft")
        status = payload.get("status", "draft")
        version = payload.get("schema_version", "1.0")
        identity_items = [
            f"文件階段：{stage} (版本 {version})",
            f"狀態：{status}",
            f"需求會話追蹤 ID：{session_id}",
        ]

    # Parties and Roles
    parties_items = payload.get("parties_and_roles", [])
    if not parties_items:
        parties_items = [
            "甲方 (需求提出方)：業務與使用者代表",
            "乙方 (技術交付方)：LogicMCP 自動化架構師團隊",
        ]

    # Scope
    scope_items = payload.get("scope", [])
    if not scope_items:
        if purpose:
            scope_items.append(f"專案核心目標：{purpose}")
        req_align = payload.get("requirement_alignment", [])
        for item in req_align:
            rid = item.get("requirement_id", "")
            summary = item.get("summary", "")
            if summary:
                scope_items.append(f"[{rid}] {summary}")

    # Deliverables
    deliverable_items = payload.get("deliverables", [])
    if not deliverable_items:
        arch = payload.get("architecture_outline", [])
        for a in arch:
            deliverable_items.append(f"架構組件：{a}")
        t_choices = payload.get("technical_choices", [])
        for tc in t_choices:
            area = tc.get("area", "")
            proposal = tc.get("proposal", "")
            if proposal:
                deliverable_items.append(f"技術選型 [{area}]：{proposal}")

    # Acceptance
    acceptance_items = payload.get("acceptance", [])
    if not acceptance_items:
        req_align = payload.get("requirement_alignment", [])
        for item in req_align:
            rid = item.get("requirement_id", "")
            cov_status = item.get("coverage_status", "covered")
            notes = item.get("notes", "")
            tech_impl = ", ".join(item.get("technical_implications", []))
            acceptance_items.append(f"[{rid}] 驗收狀態: {cov_status} | 技術實現: {tech_impl}" + (f" (備註: {notes})" if notes else ""))

    # Customer Dependencies & Assumptions
    dep_items = payload.get("customer_dependencies", [])
    if not dep_items:
        assumptions = payload.get("assumptions", [])
        for ass in assumptions:
            dep_items.append(f"假設條件：{ass}")
        unresolved = payload.get("unresolved_decisions", [])
        for un in unresolved:
            desc = un.get("description") if isinstance(un, dict) else str(un)
            dep_items.append(f"待定決策：{desc}")

    # Change Control
    change_items = payload.get("change_control", [])
    if not change_items:
        change_items = [
            "所有範疇變更須經由雙方代表簽署 CR (Change Request) 變更單",
            "技術影響評估與時程調整需按 LogicMCP 狀態機追溯",
        ]

    # Maintenance Handover
    maint_items = payload.get("maintenance_handover_termination", [])
    if not maint_items:
        limitations = payload.get("limitations", [])
        for lim in limitations:
            maint_items.append(f"維護/限制聲明：{lim}")
        if not maint_items:
            maint_items = ["交付後提供標準 30 天維運平穩期移交支援"]

    # Legal Review Items
    legal_items = payload.get("legal_review_items", [])
    if not legal_items:
        legal_items = [
            "本草案由演算法自動繪製生成，未經法務簽核前不具備最終法律約束力",
            "智財權歸屬與商業授權需依最終合約約定條款為準",
        ]

    # Approvals
    approval_items = payload.get("approvals", [])
    if not approval_items:
        approval_items = ["技術負責人：待簽核", "需求負責人：待簽核"]

    context = {
        "project_name": project_name,
        "document_identity": _bullets(identity_items),
        "parties_and_roles": _bullets(parties_items),
        "scope": _bullets(scope_items),
        "deliverables": _bullets(deliverable_items),
        "acceptance": _bullets(acceptance_items),
        "customer_dependencies": _bullets(dep_items),
        "change_control": _bullets(change_items),
        "maintenance_handover_termination": _bullets(maint_items),
        "legal_review_items": _bullets(legal_items),
        "baseline_and_approval": _bullets([f"SHA-256：{digest}", *approval_items]),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template.safe_substitute(context), encoding="utf-8", newline="")
    return {"path": str(output), "sha256": digest}
