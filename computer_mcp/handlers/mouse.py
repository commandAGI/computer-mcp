"""Mouse action handlers."""

import time
from typing import Any, Union

from mcp.types import ImageContent, TextContent

from computer_mcp.core.response import format_response
from computer_mcp.core.state import ComputerState
from computer_mcp.core.utils import button_from_string, constrain_mouse_coordinates


def handle_click(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle click action."""
    # Get current mouse position and constrain it if needed
    current_pos = mouse_controller.position
    constrain_window = state.config.get("constrain_mouse_to_window")
    if constrain_window:
        constrained_x, constrained_y = constrain_mouse_coordinates(
            int(current_pos[0]), int(current_pos[1]), constrain_window
        )
        if (constrained_x, constrained_y) != (int(current_pos[0]), int(current_pos[1])):
            # Position was constrained, move to constrained position first
            mouse_controller.position = (constrained_x, constrained_y)
    
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.click(button)
    result = {"success": True, "action": "click", "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_double_click(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle double_click action."""
    # Get current mouse position and constrain it if needed
    current_pos = mouse_controller.position
    constrain_window = state.config.get("constrain_mouse_to_window")
    if constrain_window:
        constrained_x, constrained_y = constrain_mouse_coordinates(
            int(current_pos[0]), int(current_pos[1]), constrain_window
        )
        if (constrained_x, constrained_y) != (int(current_pos[0]), int(current_pos[1])):
            # Position was constrained, move to constrained position first
            mouse_controller.position = (constrained_x, constrained_y)
    
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.click(button, 2)
    result = {"success": True, "action": "double_click", "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_triple_click(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle triple_click action."""
    # Get current mouse position and constrain it if needed
    current_pos = mouse_controller.position
    constrain_window = state.config.get("constrain_mouse_to_window")
    if constrain_window:
        constrained_x, constrained_y = constrain_mouse_coordinates(
            int(current_pos[0]), int(current_pos[1]), constrain_window
        )
        if (constrained_x, constrained_y) != (int(current_pos[0]), int(current_pos[1])):
            # Position was constrained, move to constrained position first
            mouse_controller.position = (constrained_x, constrained_y)
    
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.click(button, 3)
    result = {"success": True, "action": "triple_click", "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_button_down(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle button_down action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.press(button)
    result = {"success": True, "action": "button_down", "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_button_up(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle button_up action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.release(button)
    result = {"success": True, "action": "button_up", "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_drag(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle drag action."""
    start = arguments["start"]
    end = arguments["end"]
    button = button_from_string(arguments.get("button", "left"))
    
    # Constrain start and end positions to window bounds if configured
    constrain_window = state.config.get("constrain_mouse_to_window")
    if constrain_window:
        start_x, start_y = constrain_mouse_coordinates(
            start["x"], start["y"], constrain_window
        )
        end_x, end_y = constrain_mouse_coordinates(
            end["x"], end["y"], constrain_window
        )
    else:
        start_x, start_y = start["x"], start["y"]
        end_x, end_y = end["x"], end["y"]
    
    # Move to start, press button, move to end, release button
    mouse_controller.position = (start_x, start_y)
    mouse_controller.press(button)
    time.sleep(0.01)  # Small delay
    mouse_controller.position = (end_x, end_y)
    time.sleep(0.01)
    mouse_controller.release(button)
    
    result = {"success": True, "action": "drag", "start": {"x": start_x, "y": start_y}, "end": {"x": end_x, "y": end_y}, "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_mouse_move(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle mouse_move action."""
    x = arguments["x"]
    y = arguments["y"]
    
    # Constrain coordinates to window bounds if configured
    constrain_window = state.config.get("constrain_mouse_to_window")
    if constrain_window:
        x, y = constrain_mouse_coordinates(x, y, constrain_window)
    
    mouse_controller.position = (x, y)
    result = {"success": True, "action": "mouse_move", "x": x, "y": y}
    return format_response(result, state)

