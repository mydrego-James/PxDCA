from .mcp_instance import UVICORN_LOG_CONFIG, mcp, logger
from .settings import settings
from . import public_tools  # noqa: F401

logger.info(
    "PxDCA public Tools registered: requirements, architecture, audit, skill generation."
)

def main():
    transport = settings.server.transport

    logger.info(f"Starting server with transport: {transport}")
    try:
        if transport == "stdio":
            mcp.run(transport="stdio")
            return

        mcp.run(
            transport=transport,
            host=settings.server.host,
            port=settings.server.port,
            path=settings.server.path,
            uvicorn_config={"log_config": UVICORN_LOG_CONFIG},
        )
    except KeyboardInterrupt:
        logger.info("FastMCP server stopped by user.")

if __name__ == "__main__":
    main()
