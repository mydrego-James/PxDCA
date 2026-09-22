from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ..settings import PROJECT_ROOT, load_settings


class SettingsTests(unittest.TestCase):
    def test_toml_loads_and_environment_has_priority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pxdca-config-") as directory:
            config = Path(directory) / "pxdca.toml"
            config.write_text(
                """[server]
host = "127.0.0.1"
port = 7000
path = "/configured"
transport = "http"
[state]
root = "configured/state"
[artifacts]
enabled = false
root = "configured/artifacts"
allow_tool_override = false
[logging]
root = "configured/logs"
level = "WARNING"
""",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "PXDCA_CONFIG": str(config),
                    "PXDCA_PORT": "8123",
                    "PXDCA_ARTIFACTS_ENABLED": "true",
                },
                clear=True,
            ):
                result = load_settings()
            self.assertEqual(result.server.port, 8123)
            self.assertEqual(result.server.path, "/configured")
            self.assertTrue(result.artifacts.enabled)
            self.assertEqual(result.state.root, (PROJECT_ROOT / "configured/state").resolve())

    def test_legacy_environment_is_reported(self) -> None:
        with patch.dict(os.environ, {"MCP_PORT": "8124"}, clear=True):
            result = load_settings()
        self.assertEqual(result.server.port, 8124)
        self.assertIn("MCP_PORT", result.legacy_environment)
