import importlib.util
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).parent / "render_specification.py"
_spec = importlib.util.spec_from_file_location("logicmcp_spec_renderer", SCRIPT)
if _spec is None or _spec.loader is None:
    raise ImportError("Unable to load specification renderer")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)


def render_specification(payload: dict[str, Any], output_dir: str | Path) -> list[str]:
    return [str(path) for path in _module.render(payload, Path(output_dir))]
