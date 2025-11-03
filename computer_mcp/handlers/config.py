"""Configuration handler."""

from typing import Any, Union

from mcp.types import ImageContent, TextContent

from computer_mcp.core.response import format_response
from computer_mcp.core.state import ComputerState


def handle_set_config(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller  # noqa: ARG001
) -> list[Union[TextContent, ImageContent]]:
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
    
    if "disallowed_hotkeys" in arguments:
        state.config["disallowed_hotkeys"] = arguments["disallowed_hotkeys"]
    
    if "constrain_mouse_to_window" in arguments:
        state.config["constrain_mouse_to_window"] = arguments["constrain_mouse_to_window"]
    
    if "observe_system_metrics" in arguments:
        state.config["observe_system_metrics"] = arguments["observe_system_metrics"]
    
    if "terminal_output_mode" in arguments:
        terminal_output_mode = arguments["terminal_output_mode"]
        if terminal_output_mode not in ("chars", "text"):
            result = {
                "error": "terminal_output_mode must be 'chars' or 'text'",
                "action": "set_config"
            }
            return format_response(result, state)
        state.config["terminal_output_mode"] = terminal_output_mode
    
    result = {
        "success": True,
        "action": "set_config",
        "config": state.config.copy()
    }
    return format_response(result, state)

