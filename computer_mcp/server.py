"""MCP server setup and tool definitions."""

from typing import Any, Union

from mcp.server import Server
from mcp.types import ImageContent, Tool, TextContent
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController

from computer_mcp.core.state import ComputerState
from computer_mcp.handlers import config, keyboard, mouse, screenshot


# Global state instance
computer_state = ComputerState()
mouse_controller = MouseController()
keyboard_controller = KeyboardController()

# Initialize MCP server
server = Server("computer-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="click",
            description="Perform a mouse click at the current cursor position",
            inputSchema={
                "type": "object",
                "properties": {
                    "button": {
                        "type": "string",
                        "enum": ["left", "middle", "right"],
                        "description": "Mouse button to click",
                        "default": "left"
                    }
                }
            }
        ),
        Tool(
            name="double_click",
            description="Perform a double mouse click at the current cursor position",
            inputSchema={
                "type": "object",
                "properties": {
                    "button": {
                        "type": "string",
                        "enum": ["left", "middle", "right"],
                        "description": "Mouse button to click",
                        "default": "left"
                    }
                }
            }
        ),
        Tool(
            name="triple_click",
            description="Perform a triple mouse click at the current cursor position",
            inputSchema={
                "type": "object",
                "properties": {
                    "button": {
                        "type": "string",
                        "enum": ["left", "middle", "right"],
                        "description": "Mouse button to click",
                        "default": "left"
                    }
                }
            }
        ),
        Tool(
            name="button_down",
            description="Press and hold a mouse button",
            inputSchema={
                "type": "object",
                "properties": {
                    "button": {
                        "type": "string",
                        "enum": ["left", "middle", "right"],
                        "description": "Mouse button to press",
                        "default": "left"
                    }
                }
            }
        ),
        Tool(
            name="button_up",
            description="Release a mouse button",
            inputSchema={
                "type": "object",
                "properties": {
                    "button": {
                        "type": "string",
                        "enum": ["left", "middle", "right"],
                        "description": "Mouse button to release",
                        "default": "left"
                    }
                }
            }
        ),
        Tool(
            name="drag",
            description="Drag mouse from start to end position",
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"}
                        },
                        "required": ["x", "y"],
                        "description": "Start position"
                    },
                    "end": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"}
                        },
                        "required": ["x", "y"],
                        "description": "End position"
                    },
                    "button": {
                        "type": "string",
                        "enum": ["left", "middle", "right"],
                        "description": "Mouse button to use for drag",
                        "default": "left"
                    }
                },
                "required": ["start", "end"]
            }
        ),
        Tool(
            name="mouse_move",
            description="Move the mouse cursor to the specified coordinates",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"}
                },
                "required": ["x", "y"]
            }
        ),
        Tool(
            name="type",
            description="Type the specified text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"}
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="key_down",
            description="Press and hold a key",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key to press (e.g., 'ctrl', 'a', 'space')"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="key_up",
            description="Release a key",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key to release (e.g., 'ctrl', 'a', 'space')"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="key_press",
            description="Press and release a key (convenience method)",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key to press and release (e.g., 'ctrl', 'a', 'space')"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="screenshot",
            description="Capture a screenshot of the display and return it as base64-encoded PNG",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="set_config",
            description="Configure observation options",
            inputSchema={
                "type": "object",
                "properties": {
                    "observe_screen": {
                        "type": "boolean",
                        "description": "Include screenshots in responses (default: true)",
                        "default": True
                    },
                    "observe_mouse_position": {
                        "type": "boolean",
                        "description": "Track and include mouse position",
                        "default": False
                    },
                    "observe_mouse_button_states": {
                        "type": "boolean",
                        "description": "Track and include mouse button states",
                        "default": False
                    },
                    "observe_keyboard_key_states": {
                        "type": "boolean",
                        "description": "Track and include keyboard key states",
                        "default": False
                    },
                    "observe_focused_app": {
                        "type": "boolean",
                        "description": "Include focused application information",
                        "default": False
                    },
                    "observe_accessibility_tree": {
                        "type": "boolean",
                        "description": "Include accessibility tree",
                        "default": False
                    }
                }
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[Union[TextContent, ImageContent]]:
    """Handle tool calls."""
    import json
    
    try:
        # Update listeners based on config
        if computer_state.config["observe_mouse_position"] or computer_state.config["observe_mouse_button_states"]:
            computer_state.start_mouse_listener()
        else:
            computer_state.stop_mouse_listener()
        
        if computer_state.config["observe_keyboard_key_states"]:
            computer_state.start_keyboard_listener()
        else:
            computer_state.stop_keyboard_listener()
        
        # Route to appropriate handler
        handlers = {
            "click": mouse.handle_click,
            "double_click": mouse.handle_double_click,
            "triple_click": mouse.handle_triple_click,
            "button_down": mouse.handle_button_down,
            "button_up": mouse.handle_button_up,
            "drag": mouse.handle_drag,
            "mouse_move": mouse.handle_mouse_move,
            "type": keyboard.handle_type,
            "key_down": keyboard.handle_key_down,
            "key_up": keyboard.handle_key_up,
            "key_press": keyboard.handle_key_press,
            "screenshot": screenshot.handle_screenshot,
            "set_config": config.handle_set_config,
        }
        
        if name in handlers:
            return handlers[name](arguments, computer_state, mouse_controller if "mouse" in name or name == "drag" else keyboard_controller)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    
    except Exception as e:
        error_msg = {"error": str(e), "tool": name, "arguments": arguments}
        return [TextContent(type="text", text=json.dumps(error_msg))]

