import datetime
import logging
import os

from fastmcp import FastMCP

from .settings import PROJECT_ROOT, settings


ROOT = PROJECT_ROOT
OUTPUT_ROOT = settings.artifacts.root
if settings.artifacts.enabled:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
STATE_ROOT = settings.state.root
STATE_ROOT.mkdir(parents=True, exist_ok=True)
MCPS_LOG_DIR = settings.logging.root
MCPS_LOG_DIR.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("PxDCA Server", version="3.1.0")

def setup_logger() -> logging.Logger:
    """Create the service logger without depending on optional root tooling."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = MCPS_LOG_DIR / f"mcps-{timestamp}.log"

    service_logger = logging.getLogger("pxdca.fastmcp")
    service_logger.setLevel(settings.logging.level)
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
logger.info("PxDCA configuration loaded from %s", settings.config_path)
if settings.legacy_environment:
    logger.warning(
        "Deprecated LogicMCP environment names detected: %s; use PXDCA_* settings instead.",
        ", ".join(settings.legacy_environment),
    )
legacy_state_root = ROOT / "output" / ".logicmcp" / "sessions"
if (
    "PXDCA_STATE_ROOT" not in os.environ
    and legacy_state_root.is_dir()
    and not any(STATE_ROOT.glob("*.json"))
):
    logger.warning(
        "Legacy LogicMCP sessions found at %s. Set PXDCA_STATE_ROOT to that path "
        "for temporary access, or migrate them to %s.",
        legacy_state_root,
        STATE_ROOT,
    )

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
