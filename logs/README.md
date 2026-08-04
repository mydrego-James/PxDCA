# LogicMCP Server logs

This directory is owned exclusively by the MCP service. It contains server
startup/shutdown records, MCP/API activity, validation evidence, and MCP Tool
execution records. Factory, CLI, LLM, and APP logs must not be written here.

`logs/fastmcp/` contains both the LogicMCP service log and HTTP access/response
status log produced by the FastMCP/Uvicorn transport.
