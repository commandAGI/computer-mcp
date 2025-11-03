"""MCP server setup and tool definitions."""

from typing import Any, Union

from mcp.server import Server
from mcp.types import ImageContent, Tool, TextContent
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController

from computer_mcp.core.state import ComputerState
from computer_mcp.handlers import config, keyboard, mouse, screenshot, window


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
        Tool(
            name="list_windows",
            description="List all visible windows with their handles, titles, processes, and bounds",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="switch_to_window",
            description="Switch focus to a window by handle or title pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle (from list_windows)"
                    },
                    "title": {
                        "type": "string",
                        "description": "Window title pattern to search for (alternative to hwnd)"
                    }
                },
                "oneOf": [
                    {"required": ["hwnd"]},
                    {"required": ["title"]}
                ]
            }
        ),
        Tool(
            name="move_window",
            description="Move and/or resize a window to specified position and size",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    },
                    "x": {
                        "type": "integer",
                        "description": "X coordinate for window position"
                    },
                    "y": {
                        "type": "integer",
                        "description": "Y coordinate for window position"
                    },
                    "width": {
                        "type": "integer",
                        "description": "Window width (optional, preserves current if not specified)"
                    },
                    "height": {
                        "type": "integer",
                        "description": "Window height (optional, preserves current if not specified)"
                    }
                },
                "required": ["hwnd", "x", "y"]
            }
        ),
        Tool(
            name="resize_window",
            description="Resize a window to specified dimensions",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    },
                    "width": {
                        "type": "integer",
                        "description": "Window width"
                    },
                    "height": {
                        "type": "integer",
                        "description": "Window height"
                    }
                },
                "required": ["hwnd", "width", "height"]
            }
        ),
        Tool(
            name="minimize_window",
            description="Minimize a window",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="maximize_window",
            description="Maximize a window",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="restore_window",
            description="Restore a minimized or maximized window to normal state",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="set_window_topmost",
            description="Set or remove a window's always-on-top property",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    },
                    "topmost": {
                        "type": "boolean",
                        "description": "Whether window should be always on top",
                        "default": True
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="get_window_info",
            description="Get detailed information about a window",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="close_window",
            description="Close a window",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="snap_window_left",
            description="Snap window to fill left half of screen",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="snap_window_right",
            description="Snap window to fill right half of screen",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="snap_window_top",
            description="Snap window to fill top half of screen",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="snap_window_bottom",
            description="Snap window to fill bottom half of screen",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="screenshot_window",
            description="Capture screenshot of a specific window",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    }
                },
                "required": ["hwnd"]
            }
        ),
        Tool(
            name="list_virtual_desktops",
            description="List all virtual desktops with their IDs and names",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="switch_virtual_desktop",
            description="Switch to a virtual desktop by ID or name",
            inputSchema={
                "type": "object",
                "properties": {
                    "desktop_id": {
                        "type": "integer",
                        "description": "Virtual desktop ID (0-indexed)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Virtual desktop name (alternative to desktop_id)"
                    }
                },
                "oneOf": [
                    {"required": ["desktop_id"]},
                    {"required": ["name"]}
                ]
            }
        ),
        Tool(
            name="move_window_to_virtual_desktop",
            description="Move a window to a different virtual desktop",
            inputSchema={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "Window handle"
                    },
                    "desktop_id": {
                        "type": "integer",
                        "description": "Target virtual desktop ID"
                    }
                },
                "required": ["hwnd", "desktop_id"]
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
            "list_windows": window.handle_list_windows,
            "switch_to_window": window.handle_switch_to_window,
            "move_window": window.handle_move_window,
            "resize_window": window.handle_resize_window,
            "minimize_window": window.handle_minimize_window,
            "maximize_window": window.handle_maximize_window,
            "restore_window": window.handle_restore_window,
            "set_window_topmost": window.handle_set_window_topmost,
            "get_window_info": window.handle_get_window_info,
            "close_window": window.handle_close_window,
            "snap_window_left": window.handle_snap_window_left,
            "snap_window_right": window.handle_snap_window_right,
            "snap_window_top": window.handle_snap_window_top,
            "snap_window_bottom": window.handle_snap_window_bottom,
            "screenshot_window": window.handle_screenshot_window,
            "list_virtual_desktops": window.handle_list_virtual_desktops,
            "switch_virtual_desktop": window.handle_switch_virtual_desktop,
            "move_window_to_virtual_desktop": window.handle_move_window_to_virtual_desktop,
        }
        
        if name in handlers:
            controller = None
            if "mouse" in name or name == "drag":
                controller = mouse_controller
            elif "key" in name or name == "type":
                controller = keyboard_controller
            return handlers[name](arguments, computer_state, controller)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    
    except Exception as e:
        error_msg = {"error": str(e), "tool": name, "arguments": arguments}
        return [TextContent(type="text", text=json.dumps(error_msg))]

