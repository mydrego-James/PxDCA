"""Load PxDCA runtime settings from TOML with environment overrides."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "pxdca.toml"


@dataclass(frozen=True)
class ServerSettings:
    host: str
    port: int
    path: str
    transport: str


@dataclass(frozen=True)
class StateSettings:
    root: Path


@dataclass(frozen=True)
class ArtifactSettings:
    enabled: bool
    root: Path
    allow_tool_override: bool


@dataclass(frozen=True)
class LoggingSettings:
    root: Path
    level: str


@dataclass(frozen=True)
class Settings:
    config_path: Path
    server: ServerSettings
    state: StateSettings
    artifacts: ArtifactSettings
    logging: LoggingSettings
    legacy_environment: tuple[str, ...]


def _table(document: dict[str, Any], name: str) -> dict[str, Any]:
    value = document.get(name, {})
    return value if isinstance(value, dict) else {}


def _environment(
    canonical: str,
    legacy: str | None,
    fallback: Any,
    legacy_used: list[str],
) -> Any:
    value = os.environ.get(canonical)
    if value is not None:
        return value
    if legacy:
        value = os.environ.get(legacy)
        if value is not None:
            legacy_used.append(legacy)
            return value
    return fallback


def _boolean(value: Any, *, name: str) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def _path(value: Any) -> Path:
    candidate = Path(str(value)).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def load_settings() -> Settings:
    config_value = os.environ.get("PXDCA_CONFIG")
    config_path = _path(config_value) if config_value else DEFAULT_CONFIG_PATH.resolve()
    if config_value and not config_path.is_file():
        raise FileNotFoundError(f"PXDCA_CONFIG does not exist: {config_path}")
    if config_path.exists():
        with config_path.open("rb") as stream:
            document = tomllib.load(stream)
    else:
        document = {}

    server = _table(document, "server")
    state = _table(document, "state")
    artifacts = _table(document, "artifacts")
    logging = _table(document, "logging")
    legacy_used: list[str] = []

    host = str(_environment("PXDCA_HOST", "MCP_HOST", server.get("host", "127.0.0.1"), legacy_used))
    port = int(_environment("PXDCA_PORT", "MCP_PORT", server.get("port", 8000), legacy_used))
    path = str(_environment("PXDCA_PATH", "MCP_PATH", server.get("path", "/mcp"), legacy_used))
    transport = str(
        _environment(
            "PXDCA_TRANSPORT",
            "MCP_TRANSPORT",
            server.get("transport", "http"),
            legacy_used,
        )
    ).lower()
    if transport == "streamable-http":
        transport = "http"
    if transport not in {"http", "stdio", "sse"}:
        raise ValueError("server.transport must be http, stdio, or sse")
    if not 1 <= port <= 65535:
        raise ValueError("server.port must be between 1 and 65535")
    if not path.startswith("/"):
        raise ValueError("server.path must start with '/'")

    state_root = _path(
        _environment(
            "PXDCA_STATE_ROOT",
            "MCP_STATE_ROOT",
            state.get("root", "data/state"),
            legacy_used,
        )
    )
    artifact_root = _path(
        _environment(
            "PXDCA_ARTIFACT_ROOT",
            "MCP_OUTPUT_ROOT",
            artifacts.get("root", "data/artifacts"),
            legacy_used,
        )
    )
    artifact_enabled = _boolean(
        _environment(
            "PXDCA_ARTIFACTS_ENABLED",
            None,
            artifacts.get("enabled", True),
            legacy_used,
        ),
        name="PXDCA_ARTIFACTS_ENABLED",
    )
    allow_override = _boolean(
        _environment(
            "PXDCA_ALLOW_TOOL_OUTPUT_OVERRIDE",
            None,
            artifacts.get("allow_tool_override", False),
            legacy_used,
        ),
        name="PXDCA_ALLOW_TOOL_OUTPUT_OVERRIDE",
    )
    log_root = _path(
        _environment(
            "PXDCA_LOG_ROOT",
            None,
            logging.get("root", "data/logs"),
            legacy_used,
        )
    )
    log_level = str(
        _environment("PXDCA_LOG_LEVEL", None, logging.get("level", "INFO"), legacy_used)
    ).upper()

    return Settings(
        config_path=config_path,
        server=ServerSettings(host=host, port=port, path=path, transport=transport),
        state=StateSettings(root=state_root),
        artifacts=ArtifactSettings(
            enabled=artifact_enabled,
            root=artifact_root,
            allow_tool_override=allow_override,
        ),
        logging=LoggingSettings(root=log_root, level=log_level),
        legacy_environment=tuple(dict.fromkeys(legacy_used)),
    )


settings = load_settings()
