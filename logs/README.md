# PxDCA Server logs

This directory is owned exclusively by the MCP service. It contains server
startup/shutdown records, MCP/API activity, validation evidence, and MCP Tool
execution records. Client and provider logs belong to their own projects.

The current default `data/logs/` contains both the PxDCA service log and HTTP access/response
status log produced by the FastMCP/Uvicorn transport.
