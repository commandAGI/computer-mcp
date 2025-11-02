"""Keyboard action handlers."""

import json
from typing import Any

from mcp.types import TextContent

from core.state import ComputerState
from core.utils import key_from_string


def handle_type(
    arguments: dict[str, Any],
    state: ComputerState,
    keyboard_controller
) -> list[TextContent]:
    """Handle type action."""
    text = arguments["text"]
    keyboard_controller.type(text)
    result_state = state.get_state()
    result = {"success": True, "action": "type", "text": text}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]


def handle_key_down(
    arguments: dict[str, Any],
    state: ComputerState,
    keyboard_controller
) -> list[TextContent]:
    """Handle key_down action."""
    key_str = arguments["key"]
    key = key_from_string(key_str)
    keyboard_controller.press(key)
    result_state = state.get_state()
    result = {"success": True, "action": "key_down", "key": key_str}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]


def handle_key_up(
    arguments: dict[str, Any],
    state: ComputerState,
    keyboard_controller
) -> list[TextContent]:
    """Handle key_up action."""
    key_str = arguments["key"]
    key = key_from_string(key_str)
    keyboard_controller.release(key)
    result_state = state.get_state()
    result = {"success": True, "action": "key_up", "key": key_str}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]


def handle_key_press(
    arguments: dict[str, Any],
    state: ComputerState,
    keyboard_controller
) -> list[TextContent]:
    """Handle key_press action."""
    key_str = arguments["key"]
    key = key_from_string(key_str)
    keyboard_controller.press(key)
    keyboard_controller.release(key)
    result_state = state.get_state()
    result = {"success": True, "action": "key_press", "key": key_str}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]

