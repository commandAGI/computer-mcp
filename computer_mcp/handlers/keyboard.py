"""Keyboard action handlers."""

from typing import Any, Union

from mcp.types import ImageContent, TextContent

from computer_mcp.core.response import format_response
from computer_mcp.core.state import ComputerState
from computer_mcp.core.utils import key_from_string


def handle_type(
    arguments: dict[str, Any],
    state: ComputerState,
    keyboard_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle type action."""
    text = arguments["text"]
    keyboard_controller.type(text)
    result = {"success": True, "action": "type", "text": text}
    return format_response(result, state)


def handle_key_down(
    arguments: dict[str, Any],
    state: ComputerState,
    keyboard_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle key_down action."""
    key_str = arguments["key"]
    key = key_from_string(key_str)
    keyboard_controller.press(key)
    result = {"success": True, "action": "key_down", "key": key_str}
    return format_response(result, state)


def handle_key_up(
    arguments: dict[str, Any],
    state: ComputerState,
    keyboard_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle key_up action."""
    key_str = arguments["key"]
    key = key_from_string(key_str)
    keyboard_controller.release(key)
    result = {"success": True, "action": "key_up", "key": key_str}
    return format_response(result, state)


def handle_key_press(
    arguments: dict[str, Any],
    state: ComputerState,
    keyboard_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle key_press action."""
    key_str = arguments["key"]
    key = key_from_string(key_str)
    keyboard_controller.press(key)
    keyboard_controller.release(key)
    result = {"success": True, "action": "key_press", "key": key_str}
    return format_response(result, state)

