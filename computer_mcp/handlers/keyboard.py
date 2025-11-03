"""Keyboard action handlers."""

from typing import Any, Union

from mcp.types import ImageContent, TextContent
from pynput.keyboard import Key

from computer_mcp.core.response import format_response
from computer_mcp.core.state import ComputerState
from computer_mcp.core.utils import is_hotkey_disallowed, key_from_string


def _is_modifier_key(key) -> bool:
    """Check if a key is a modifier key."""
    if isinstance(key, Key):
        return key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r,
                       Key.alt, Key.alt_l, Key.alt_r,
                       Key.shift, Key.shift_l, Key.shift_r,
                       Key.cmd, Key.cmd_l, Key.cmd_r)
    return False


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
    
    # Check if this hotkey is disallowed
    disallowed_hotkeys = state.config.get("disallowed_hotkeys", [])
    if disallowed_hotkeys:
        if is_hotkey_disallowed(key_str, state._held_keys_for_hotkeys, disallowed_hotkeys):
            result = {
                "success": False,
                "action": "key_down",
                "key": key_str,
                "error": f"Hotkey is disallowed: {key_str}"
            }
            return format_response(result, state)
    
    keyboard_controller.press(key)
    
    # Track held keys for hotkey checking
    if _is_modifier_key(key) or key_str.lower() in ("ctrl", "alt", "shift", "cmd", "control", "win", "windows", "meta"):
        state._held_keys_for_hotkeys.add(key)
    
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
    
    # Remove from held keys tracking
    state._held_keys_for_hotkeys.discard(key)
    # Also remove any variant of the same modifier key (e.g., Key.ctrl_l vs Key.ctrl)
    if _is_modifier_key(key):
        from pynput.keyboard import Key as PynputKey
        modifier_groups = [
            {PynputKey.ctrl, PynputKey.ctrl_l, PynputKey.ctrl_r},
            {PynputKey.alt, PynputKey.alt_l, PynputKey.alt_r},
            {PynputKey.shift, PynputKey.shift_l, PynputKey.shift_r},
            {PynputKey.cmd, PynputKey.cmd_l, PynputKey.cmd_r},
        ]
        for group in modifier_groups:
            if key in group:
                state._held_keys_for_hotkeys = {k for k in state._held_keys_for_hotkeys if k not in group}
                break
    
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
    
    # Check if this hotkey is disallowed
    disallowed_hotkeys = state.config.get("disallowed_hotkeys", [])
    if disallowed_hotkeys:
        if is_hotkey_disallowed(key_str, state._held_keys_for_hotkeys, disallowed_hotkeys):
            result = {
                "success": False,
                "action": "key_press",
                "key": key_str,
                "error": f"Hotkey is disallowed: {key_str}"
            }
            return format_response(result, state)
    
    keyboard_controller.press(key)
    keyboard_controller.release(key)
    result = {"success": True, "action": "key_press", "key": key_str}
    return format_response(result, state)

