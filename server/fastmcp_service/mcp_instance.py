import datetime
import logging
import os
from pathlib import Path

from fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = Path(os.environ.get("MCP_OUTPUT_ROOT", ROOT / "output")).resolve()
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
MCPS_LOG_DIR = ROOT / "logs" / "fastmcp"
MCPS_LOG_DIR.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("LogicMCP Federated Server")

def setup_logger() -> logging.Logger:
    """Create the service logger without depending on optional root tooling."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = MCPS_LOG_DIR / f"mcps-{timestamp}.log"

    service_logger = logging.getLogger("logicmcp.fastmcp")
    service_logger.setLevel(logging.INFO)
    service_logger.propagate = False
    service_logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    service_logger.addHandler(console_handler)
    service_logger.addHandler(file_handler)
    return service_logger

logger = setup_logger()

UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(client_addr)s - %(request_line)s %(status_code)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stderr",
        },
        "access_console": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": str(MCPS_LOG_DIR / f"http-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["access_console", "file"], "level": "INFO", "propagate": False},
    },
}
