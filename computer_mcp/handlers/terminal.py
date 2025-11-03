"""Terminal action handlers."""

from typing import Any, Union

from mcp.types import ImageContent, TextContent

from computer_mcp.actions import terminal as terminal_actions
from computer_mcp.core.response import format_response
from computer_mcp.core.state import ComputerState


async def handle_spawn_terminal(
    arguments: dict[str, Any],
    state: ComputerState,  # noqa: ARG001
    controller  # noqa: ARG001
) -> list[Union[TextContent, ImageContent]]:
    """Handle spawn_terminal action."""
    command = arguments.get("command")  # Optional list of strings
    shell = arguments.get("shell", False)
    
    result = await terminal_actions.spawn_terminal(command=command, shell=shell)
    return format_response(result, state)


def handle_list_terminals(
    arguments: dict[str, Any],  # noqa: ARG001
    state: ComputerState,
    controller  # noqa: ARG001
) -> list[Union[TextContent, ImageContent]]:
    """Handle list_terminals action."""
    result = terminal_actions.list_terminals()
    return format_response(result, state)


async def handle_send_terminal_text(
    arguments: dict[str, Any],
    state: ComputerState,
    controller  # noqa: ARG001
) -> list[Union[TextContent, ImageContent]]:
    """Handle send_terminal_text action."""
    pid = arguments.get("pid")
    text = arguments.get("text")
    
    if pid is None:
        result = {"error": "pid is required"}
        return format_response(result, state)
    
    if text is None:
        result = {"error": "text is required"}
        return format_response(result, state)
    
    terminal = terminal_actions.get_terminal(pid)
    if terminal is None:
        result = {"error": f"Terminal with PID {pid} not found"}
        return format_response(result, state)
    
    result = await terminal.send_text(text)
    return format_response(result, state)


async def handle_read_terminal_output(
    arguments: dict[str, Any],
    state: ComputerState,
    controller  # noqa: ARG001
) -> list[Union[TextContent, ImageContent]]:
    """Handle read_terminal_output action."""
    pid = arguments.get("pid")
    
    if pid is None:
        result = {"error": "pid is required"}
        return format_response(result, state)
    
    terminal = terminal_actions.get_terminal(pid)
    if terminal is None:
        result = {"error": f"Terminal with PID {pid} not found"}
        return format_response(result, state)
    
    # Get output mode from config (default: "chars")
    output_mode = state.config.get("terminal_output_mode", "chars")
    as_chars = output_mode == "chars"
    
    count = arguments.get("count")  # Optional max count
    
    result = await terminal.read_output(as_chars=as_chars, count=count)
    return format_response(result, state)


async def handle_send_terminal_key(
    arguments: dict[str, Any],
    state: ComputerState,
    controller  # noqa: ARG001
) -> list[Union[TextContent, ImageContent]]:
    """Handle send_terminal_key action."""
    pid = arguments.get("pid")
    key = arguments.get("key")
    event = arguments.get("event", "down")  # Default to "down"
    
    if pid is None:
        result = {"error": "pid is required"}
        return format_response(result, state)
    
    if key is None:
        result = {"error": "key is required"}
        return format_response(result, state)
    
    if event not in ("down", "up"):
        result = {"error": "event must be 'down' or 'up'"}
        return format_response(result, state)
    
    terminal = terminal_actions.get_terminal(pid)
    if terminal is None:
        result = {"error": f"Terminal with PID {pid} not found"}
        return format_response(result, state)
    
    result = await terminal.send_key(key, event)
    return format_response(result, state)


def handle_close_terminal(
    arguments: dict[str, Any],
    state: ComputerState,
    controller  # noqa: ARG001
) -> list[Union[TextContent, ImageContent]]:
    """Handle close_terminal action."""
    pid = arguments.get("pid")
    
    if pid is None:
        result = {"error": "pid is required"}
        return format_response(result, state)
    
    result = terminal_actions.close_terminal(pid)
    return format_response(result, state)

