"""Screenshot handler."""

import json
from typing import Any

from mcp.types import TextContent

from computer_mcp.core.screenshot import capture_screenshot
from computer_mcp.core.state import ComputerState


def handle_screenshot(
    arguments: dict[str, Any],  # noqa: ARG001
    state: ComputerState,
    mouse_controller  # noqa: ARG001
) -> list[TextContent]:
    """Handle screenshot action."""
    screenshot_data = capture_screenshot()
    result_state = state.get_state(include_screenshot=False)  # Don't double-capture
    result = {"success": True, "action": "screenshot"}
    result.update(screenshot_data)
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]

