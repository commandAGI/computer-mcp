"""Platform-specific implementations."""

import platform
from typing import Any


def get_focused_app() -> dict[str, Any]:
    """Get current focused application (platform-agnostic wrapper)."""
    system = platform.system()
    try:
        if system == "Windows":
            from computer_mcp.platforms import windows
            return windows.get_focused_app()
        elif system == "Darwin":
            from computer_mcp.platforms import macos
            return macos.get_focused_app()
        elif system == "Linux":
            from computer_mcp.platforms import linux
            return linux.get_focused_app()
        else:
            return {"error": f"Unsupported platform: {system}"}
    except Exception as e:
        return {"error": f"Error retrieving focused app: {str(e)}"}


def get_accessibility_tree() -> dict[str, Any]:
    """Get accessibility tree (platform-agnostic wrapper)."""
    system = platform.system()
    try:
        if system == "Windows":
            from computer_mcp.platforms import windows
            return windows.get_accessibility_tree()
        elif system == "Darwin":
            from computer_mcp.platforms import macos
            return macos.get_accessibility_tree()
        elif system == "Linux":
            from computer_mcp.platforms import linux
            return linux.get_accessibility_tree()
        else:
            return {"error": f"Unsupported platform: {system}"}
    except Exception as e:
        return {"error": f"Error getting accessibility tree: {str(e)}"}
