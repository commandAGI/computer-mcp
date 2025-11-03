#!/usr/bin/env python3
"""
Computer MCP Server
Main entry point for the MCP server (stdio mode, default).
For CLI and HTTP/SSE modes, use: python -m computer_mcp
"""

import asyncio

from computer_mcp.mcp import run_stdio


async def main():
    """Main entry point for stdio MCP server."""
    await run_stdio()


def entry_point():
    """Synchronous entry point for setuptools console script."""
    asyncio.run(main())


if __name__ == "__main__":
    entry_point()
