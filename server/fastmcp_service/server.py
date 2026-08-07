import os

from .mcp_instance import UVICORN_LOG_CONFIG, mcp, logger
from . import public_tools  # noqa: F401

logger.info("LogicMCP public workflows registered: requirements, architecture, audit.")

def main():
    transport = os.environ.get("MCP_TRANSPORT", "http").lower()
    if transport == "streamable-http":
        transport = "http"

    logger.info(f"Starting server with transport: {transport}")
    try:
        if transport == "stdio":
            mcp.run(transport="stdio")
            return

        mcp.run(
            transport=transport,
            host=os.environ.get("MCP_HOST", "127.0.0.1"),
            port=int(os.environ.get("MCP_PORT", "8000")),
            path=os.environ.get("MCP_PATH", "/mcp"),
            uvicorn_config={"log_config": UVICORN_LOG_CONFIG},
        )
    except KeyboardInterrupt:
        logger.info("FastMCP server stopped by user.")

if __name__ == "__main__":
    main()
