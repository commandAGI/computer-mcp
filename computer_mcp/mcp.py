"""MCP server adapter - supports stdio and HTTP/SSE transport modes."""

import asyncio
import json
from typing import Any, Union

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import ImageContent, TextContent, Tool
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController

from computer_mcp.actions import (
    keyboard as keyboard_actions,
    mouse as mouse_actions,
    screenshot as screenshot_actions,
    window as window_actions,
    config as config_actions,
)
from computer_mcp.core.response import format_response
from computer_mcp.core.state import ComputerState


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
    """Handle tool calls by routing to action functions."""
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
        
        # Route to appropriate action function
        result: dict[str, Any] | None = None
        screenshot_data: dict[str, Any] | None = None
        
        # Mouse actions
        if name == "click":
            result = mouse_actions.click(
                button=arguments.get("button", "left"),
                controller=mouse_controller
            )
        elif name == "double_click":
            result = mouse_actions.double_click(
                button=arguments.get("button", "left"),
                controller=mouse_controller
            )
        elif name == "triple_click":
            result = mouse_actions.triple_click(
                button=arguments.get("button", "left"),
                controller=mouse_controller
            )
        elif name == "button_down":
            result = mouse_actions.button_down(
                button=arguments.get("button", "left"),
                controller=mouse_controller
            )
        elif name == "button_up":
            result = mouse_actions.button_up(
                button=arguments.get("button", "left"),
                controller=mouse_controller
            )
        elif name == "drag":
            result = mouse_actions.drag(
                start=arguments["start"],
                end=arguments["end"],
                button=arguments.get("button", "left"),
                controller=mouse_controller
            )
        elif name == "mouse_move":
            result = mouse_actions.move_mouse(
                x=arguments["x"],
                y=arguments["y"],
                controller=mouse_controller
            )
        
        # Keyboard actions
        elif name == "type":
            result = keyboard_actions.type_text(
                text=arguments["text"],
                controller=keyboard_controller
            )
        elif name == "key_down":
            result = keyboard_actions.key_down(
                key=arguments["key"],
                controller=keyboard_controller
            )
        elif name == "key_up":
            result = keyboard_actions.key_up(
                key=arguments["key"],
                controller=keyboard_controller
            )
        elif name == "key_press":
            result = keyboard_actions.key_press(
                key=arguments["key"],
                controller=keyboard_controller
            )
        
        # Screenshot actions
        elif name == "screenshot":
            screenshot_result = screenshot_actions.get_screenshot()
            if "error" not in screenshot_result:
                screenshot_data = screenshot_result
                result = {"success": True, "action": "screenshot"}
            else:
                result = screenshot_result
        
        # Config actions
        elif name == "set_config":
            # Update state config first
            for key in ["observe_screen", "observe_mouse_position", "observe_mouse_button_states", 
                       "observe_keyboard_key_states", "observe_focused_app", "observe_accessibility_tree"]:
                if key in arguments:
                    computer_state.config[key] = arguments[key]
            result = {"success": True, "action": "set_config", "config": computer_state.config.copy()}
        
        # Window actions
        elif name == "list_windows":
            result = window_actions.list_windows()
        elif name == "switch_to_window":
            result = window_actions.switch_to_window(
                hwnd=arguments.get("hwnd"),
                title=arguments.get("title")
            )
        elif name == "move_window":
            result = window_actions.move_window(
                hwnd=arguments["hwnd"],
                x=arguments["x"],
                y=arguments["y"],
                width=arguments.get("width"),
                height=arguments.get("height")
            )
        elif name == "resize_window":
            result = window_actions.resize_window(
                hwnd=arguments["hwnd"],
                width=arguments["width"],
                height=arguments["height"]
            )
        elif name == "minimize_window":
            result = window_actions.minimize_window(hwnd=arguments["hwnd"])
        elif name == "maximize_window":
            result = window_actions.maximize_window(hwnd=arguments["hwnd"])
        elif name == "restore_window":
            result = window_actions.restore_window(hwnd=arguments["hwnd"])
        elif name == "set_window_topmost":
            result = window_actions.set_window_topmost(
                hwnd=arguments["hwnd"],
                topmost=arguments.get("topmost", True)
            )
        elif name == "get_window_info":
            result = window_actions.get_window_info(hwnd=arguments["hwnd"])
        elif name == "close_window":
            result = window_actions.close_window(hwnd=arguments["hwnd"])
        elif name == "snap_window_left":
            result = window_actions.snap_window_left(hwnd=arguments["hwnd"])
        elif name == "snap_window_right":
            result = window_actions.snap_window_right(hwnd=arguments["hwnd"])
        elif name == "snap_window_top":
            result = window_actions.snap_window_top(hwnd=arguments["hwnd"])
        elif name == "snap_window_bottom":
            result = window_actions.snap_window_bottom(hwnd=arguments["hwnd"])
        elif name == "screenshot_window":
            screenshot_result = window_actions.screenshot_window(hwnd=arguments["hwnd"])
            if "error" not in screenshot_result:
                screenshot_data = {
                    "format": screenshot_result.get("format", "base64_png"),
                    "data": screenshot_result.get("data"),
                    "width": screenshot_result.get("width"),
                    "height": screenshot_result.get("height")
                }
                result = {"success": screenshot_result.get("success"), "action": "screenshot_window", "hwnd": arguments["hwnd"]}
            else:
                result = screenshot_result
        
        # Virtual desktop actions
        elif name == "list_virtual_desktops":
            result = window_actions.list_virtual_desktops()
        elif name == "switch_virtual_desktop":
            result = window_actions.switch_virtual_desktop(
                desktop_id=arguments.get("desktop_id"),
                name=arguments.get("name")
            )
        elif name == "move_window_to_virtual_desktop":
            result = window_actions.move_window_to_virtual_desktop(
                hwnd=arguments["hwnd"],
                desktop_id=arguments["desktop_id"]
            )
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        # Format response using MCP format_response helper
        if result is None:
            result = {"error": "Action returned None"}
        
        return format_response(result, computer_state, screenshot_data=screenshot_data)
    
    except Exception as e:
        error_msg = {"error": str(e), "tool": name, "arguments": arguments}
        return [TextContent(type="text", text=json.dumps(error_msg))]


async def run_stdio():
    """Run MCP server in stdio mode."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


async def run_http(host: str = "127.0.0.1", port: int = 8000):
    """Run MCP server in HTTP/SSE mode.
    
    Implements HTTP/SSE transport for MCP server using aiohttp or similar.
    Note: The MCP Python SDK doesn't natively support HTTP/SSE transport,
    so we implement a custom HTTP server that handles MCP protocol over SSE.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    try:
        from aiohttp import web, web_response
        import json as json_lib
    except ImportError:
        raise ImportError(
            "aiohttp is required for HTTP/SSE mode. Install with: pip install aiohttp"
        )
    
    async def handle_sse(request):
        """Handle Server-Sent Events connection."""
        response = web_response.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        await response.prepare(request)
        
        # Read from request and write to response
        # This is a simplified implementation - full MCP over SSE would need
        # proper message framing according to MCP spec
        try:
            async for line in request.content:
                # Process MCP messages (simplified - actual implementation would parse JSON-RPC)
                await response.write(f"data: {line.decode()}\n\n".encode())
        except Exception as e:
            await response.write(f"event: error\ndata: {json_lib.dumps({'error': str(e)})}\n\n".encode())
        finally:
            await response.write_eof()
        
        return response
    
    async def handle_mcp_message(request):
        """Handle MCP tool call via HTTP POST."""
        try:
            data = await request.json()
            tool_name = data.get("name")
            arguments = data.get("arguments", {})
            
            # Call the tool handler
            result = await call_tool(tool_name, arguments)
            
            # Convert MCP response format to JSON
            response_data = []
            for content in result:
                if hasattr(content, 'text'):
                    response_data.append({"type": "text", "text": content.text})
                elif hasattr(content, 'data'):
                    response_data.append({
                        "type": "image",
                        "data": content.data,
                        "mimeType": getattr(content, 'mimeType', 'image/png')
                    })
            
            return web.json_response({"content": response_data})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    app = web.Application()
    app.router.add_get('/sse', handle_sse)
    app.router.add_post('/mcp', handle_mcp_message)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    print(f"MCP server running in HTTP/SSE mode on http://{host}:{port}")
    print(f"SSE endpoint: http://{host}:{port}/sse")
    print(f"MCP endpoint: http://{host}:{port}/mcp")
    
    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()

