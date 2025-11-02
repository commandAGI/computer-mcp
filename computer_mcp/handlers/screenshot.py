"""Screenshot handler."""

from typing import Any, Union

from mcp.types import ImageContent, TextContent

from computer_mcp.core.response import format_response
from computer_mcp.core.screenshot import capture_screenshot
from computer_mcp.core.state import ComputerState


def handle_screenshot(
    arguments: dict[str, Any],  # noqa: ARG001
    state: ComputerState,
    mouse_controller  # noqa: ARG001
) -> list[Union[TextContent, ImageContent]]:
    """Handle screenshot action."""
    screenshot_data = capture_screenshot()
    result_state = state.get_state(include_screenshot=False)  # Don't double-capture
    result = {"success": True, "action": "screenshot"}
    result.update(result_state)
    # Pass the pre-captured screenshot to avoid double capture
    return format_response(result, state, screenshot_data=screenshot_data)

