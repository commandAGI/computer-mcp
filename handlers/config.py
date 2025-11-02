"""Configuration handler."""

import json
from typing import Any

from mcp.types import TextContent

from ..core.state import ComputerState


def handle_set_config(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller  # noqa: ARG001
) -> list[TextContent]:
    """Handle set_config action."""
    # Update configuration
    if "observe_screen" in arguments:
        state.config["observe_screen"] = arguments["observe_screen"]
    
    if "observe_mouse_position" in arguments:
        state.config["observe_mouse_position"] = arguments["observe_mouse_position"]
    
    if "observe_mouse_button_states" in arguments:
        state.config["observe_mouse_button_states"] = arguments["observe_mouse_button_states"]
    
    if "observe_keyboard_key_states" in arguments:
        state.config["observe_keyboard_key_states"] = arguments["observe_keyboard_key_states"]
    
    if "observe_focused_app" in arguments:
        state.config["observe_focused_app"] = arguments["observe_focused_app"]
    
    if "observe_accessibility_tree" in arguments:
        state.config["observe_accessibility_tree"] = arguments["observe_accessibility_tree"]
    
    result = {
        "success": True,
        "action": "set_config",
        "config": state.config.copy()
    }
    return [TextContent(type="text", text=json.dumps(result))]

