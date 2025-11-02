#!/usr/bin/env python3
"""
Computer MCP Server
A cross-platform MCP server for computer automation and control.
"""

import asyncio
import base64
import json
import platform
import subprocess
import time
from io import BytesIO
from typing import Any, Optional

import mss
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pynput import keyboard, mouse
from pynput.keyboard import Controller as KeyboardController, Key, KeyCode
from pynput.mouse import Button, Controller as MouseController
from PIL import Image
import psutil


def _capture_screenshot() -> dict[str, Any]:
    """Capture screenshot and return as base64-encoded PNG."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Index 0 is all monitors, 1+ are individual
        screenshot = sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        
        return {
            "format": "base64_png",
            "data": img_base64,
            "width": screenshot.width,
            "height": screenshot.height
        }


class AccessibilityTree:
    """Platform-specific accessibility tree implementations."""
    
    @staticmethod
    def get_tree() -> dict[str, Any]:
        """Get accessibility tree for current platform."""
        system = platform.system()
        
        try:
            if system == "Windows":
                return AccessibilityTree._get_windows_tree()
            elif system == "Darwin":  # macOS
                return AccessibilityTree._get_macos_tree()
            elif system == "Linux":
                return AccessibilityTree._get_linux_tree()
            else:
                return {"error": f"Unsupported platform: {system}"}
        except Exception as e:
            return {"error": f"Error getting accessibility tree: {str(e)}"}
    
    @staticmethod
    def _get_windows_tree() -> dict[str, Any]:
        """Get Windows accessibility tree using UI Automation API."""
        try:
            import win32gui
            import win32process
            
            # Get focused window info
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return {"error": "No focused window"}
            
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                window_title = win32gui.GetWindowText(hwnd)
                
                # Get window bounds
                rect = win32gui.GetWindowRect(hwnd)
                bounds = {
                    "x": rect[0],
                    "y": rect[1],
                    "width": rect[2] - rect[0],
                    "height": rect[3] - rect[1]
                }
                
                return {
                    "tree": {
                        "name": window_title or proc.name(),
                        "control_type": "Window",
                        "process": proc.name(),
                        "pid": pid,
                        "bounds": bounds,
                        "children": [{
                            "name": "Window content",
                            "note": "Full UI Automation tree requires win32com.client.Dispatch('UIAutomation.UIAutomation') - see documentation"
                        }]
                    },
                    "note": "Simplified tree - for full accessibility tree, use Windows UI Automation via comtypes or win32com"
                }
            except Exception as e:
                return {"error": f"Error getting window info: {str(e)}"}
            
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows accessibility tree support"}
        except Exception as e:
            return {"error": f"Windows accessibility error: {str(e)}"}
    
    @staticmethod
    def _get_macos_tree() -> dict[str, Any]:
        """Get macOS accessibility tree using AppleScript (pyobjc alternative)."""
        try:
            # Use AppleScript to get accessibility tree
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set appName to name of frontApp
                set appUIElements to UI elements of frontApp
                
                set resultText to appName & "|"
                
                repeat with i from 1 to (count of appUIElements)
                    if i > 20 then exit repeat  -- Limit depth
                    try
                        set elem to item i of appUIElements
                        set elemName to name of elem
                        set elemRole to role of elem
                        set resultText to resultText & elemName & ":" & elemRole & ";"
                    end try
                end repeat
                
                return resultText
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split("|")
                app_name = parts[0] if parts else "Unknown"
                elements = []
                if len(parts) > 1 and parts[1]:
                    for elem_str in parts[1].split(";"):
                        if ":" in elem_str:
                            name, role = elem_str.split(":", 1)
                            elements.append({"name": name, "role": role})
                
                return {
                    "tree": {
                        "name": app_name,
                        "elements": elements,
                        "note": "AppleScript-based tree - install pyobjc for full native accessibility tree"
                    }
                }
            return {"error": "Could not retrieve accessibility tree via AppleScript"}
        except subprocess.TimeoutExpired:
            return {"error": "Timeout retrieving accessibility tree"}
        except Exception as e:
            return {"error": f"macOS accessibility error: {str(e)}"}
    
    @staticmethod
    def _get_linux_tree() -> dict[str, Any]:
        """Get Linux accessibility tree using AT-SPI."""
        try:
            import gi
            gi.require_version('Atspi', '2.0')
            from gi.repository import Atspi
            
            # Initialize AT-SPI
            Atspi.init()
            
            desktop = Atspi.get_desktop(0)
            
            def _object_to_dict(obj) -> dict[str, Any]:
                """Convert AT-SPI object to dictionary."""
                try:
                    name = obj.get_name() if hasattr(obj, 'get_name') else ""
                    role = str(obj.get_role_name()) if hasattr(obj, 'get_role_name') else ""
                    
                    # Get bounds
                    bounds = None
                    try:
                        if hasattr(obj, 'get_extents'):
                            extents = obj.get_extents(Atspi.CoordType.SCREEN)
                            bounds = {
                                "x": extents.x,
                                "y": extents.y,
                                "width": extents.width,
                                "height": extents.height
                            }
                    except:
                        pass
                    
                    # Get children
                    children = []
                    try:
                        if hasattr(obj, 'get_child_count') and hasattr(obj, 'get_child_at_index'):
                            child_count = obj.get_child_count()
                            for i in range(child_count):
                                child = obj.get_child_at_index(i)
                                if child:
                                    children.append(_object_to_dict(child))
                    except:
                        pass
                    
                    return {
                        "name": name,
                        "role": role,
                        "bounds": bounds,
                        "children": children
                    }
                except Exception as e:
                    return {"error": f"Error processing object: {str(e)}"}
            
            tree = _object_to_dict(desktop)
            return {"tree": tree}
            
        except ImportError:
            # Fallback to xdotool for basic window info
            try:
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    return {
                        "tree": {
                            "name": result.stdout.strip(),
                            "note": "Simplified tree - install python3-gi and gir1.2-atspi-2.0 for full accessibility tree"
                        }
                    }
            except:
                pass
            return {"error": "python-gi/AT-SPI not installed", "note": "Install python3-gi and gir1.2-atspi-2.0 for Linux accessibility tree support"}
        except Exception as e:
            return {"error": f"Linux AT-SPI error: {str(e)}"}


class ComputerState:
    """Manages computer state tracking."""
    
    def __init__(self):
        self.config = {
            "observe_screen": True,  # Default true
            "observe_mouse_position": False,
            "observe_mouse_button_states": False,
            "observe_keyboard_key_states": False,
            "observe_focused_app": False,
            "observe_accessibility_tree": False,
        }
        self.mouse_position = (0, 0)
        self.mouse_buttons = set()
        self.keyboard_keys = set()
        self.mouse_listener: Optional[mouse.Listener] = None
        self.keyboard_listener: Optional[keyboard.Listener] = None
        
    def start_mouse_listener(self):
        """Start mouse state tracking."""
        if self.mouse_listener is None and (self.config["observe_mouse_position"] or self.config["observe_mouse_button_states"]):
            self.mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self.mouse_listener.start()
    
    def stop_mouse_listener(self):
        """Stop mouse state tracking."""
        if self.mouse_listener is not None:
            self.mouse_listener.stop()
            self.mouse_listener = None
    
    def start_keyboard_listener(self):
        """Start keyboard state tracking."""
        if self.keyboard_listener is None and self.config["observe_keyboard_key_states"]:
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.keyboard_listener.start()
    
    def stop_keyboard_listener(self):
        """Stop keyboard state tracking."""
        if self.keyboard_listener is not None:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
    def _on_mouse_move(self, x: int, y: int):
        if self.config["observe_mouse_position"]:
            self.mouse_position = (x, y)
    
    def _on_mouse_click(self, x: int, y: int, button: Button, pressed: bool):
        if self.config["observe_mouse_position"]:
            self.mouse_position = (x, y)
        if self.config["observe_mouse_button_states"]:
            if pressed:
                self.mouse_buttons.add(button)
            else:
                self.mouse_buttons.discard(button)
    
    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int):  # noqa: ARG002
        if self.config["observe_mouse_position"]:
            self.mouse_position = (x, y)
    
    def _on_key_press(self, key):
        self.keyboard_keys.add(key)
    
    def _on_key_release(self, key):
        self.keyboard_keys.discard(key)
    
    def get_state(self, include_screenshot: bool = True) -> dict[str, Any]:
        """Get current state based on configuration."""
        state = {}
        
        # Screenshot (default true)
        if include_screenshot and self.config["observe_screen"]:
            try:
                state["screenshot"] = _capture_screenshot()
            except Exception as e:
                state["screenshot"] = {"error": str(e)}
        
        # Mouse position
        if self.config["observe_mouse_position"]:
            current_pos = mouse_controller.position
            state["mouse_position"] = {"x": int(current_pos[0]), "y": int(current_pos[1])}
        
        # Mouse button states
        if self.config["observe_mouse_button_states"]:
            state["mouse_button_states"] = [str(btn) for btn in self.mouse_buttons]
        
        # Keyboard key states
        if self.config["observe_keyboard_key_states"]:
            state["keyboard_key_states"] = [self._format_key(key) for key in self.keyboard_keys]
        
        # Focused app
        if self.config["observe_focused_app"]:
            state["focused_app"] = self._get_focused_app()
        
        # Accessibility tree
        if self.config["observe_accessibility_tree"]:
            state["accessibility_tree"] = AccessibilityTree.get_tree()
        
        return state
    
    def _format_key(self, key) -> str:
        """Format key for display."""
        if isinstance(key, Key):
            return key.name if hasattr(key, 'name') else str(key)
        elif isinstance(key, KeyCode):
            return key.char if key.char else f"<{key.vk}>"
        return str(key)
    
    def _get_focused_app(self) -> dict[str, Any]:
        """Get current focused application (platform-specific)."""
        system = platform.system()
        
        try:
            if system == "Windows":
                try:
                    import win32gui
                    import win32process
                except ImportError:
                    return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows support"}
                
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        proc = psutil.Process(pid)
                        return {
                            "name": proc.name(),
                            "pid": pid,
                            "title": win32gui.GetWindowText(hwnd)
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return {"error": "Could not access process information"}
                return {"error": "No focused window"}
            
            elif system == "Darwin":  # macOS
                script = '''
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    set appTitle to name of front window of frontApp
                    return frontApp & "|" & appTitle
                end tell
                '''
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False
                )
                if result.returncode == 0:
                    parts = result.stdout.strip().split("|")
                    return {
                        "name": parts[0] if parts else "Unknown",
                        "title": parts[1] if len(parts) > 1 else ""
                    }
                return {"error": "Could not retrieve focused app"}
            
            elif system == "Linux":
                try:
                    result = subprocess.run(
                        ["xdotool", "getactivewindow", "getwindowname"],
                        capture_output=True,
                        text=True,
                        timeout=1,
                        check=False
                    )
                    if result.returncode == 0:
                        return {"title": result.stdout.strip()}
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                
                return {"error": "Window manager tools not available"}
            
            else:
                return {"error": f"Unsupported platform: {system}"}
        
        except Exception as e:
            return {"error": f"Error retrieving focused app: {str(e)}"}


# Global state instance
computer_state = ComputerState()
mouse_controller = MouseController()
keyboard_controller = KeyboardController()


def _key_from_string(key_str: str):
    """Convert string key name to pynput Key or KeyCode."""
    key_str = key_str.lower().strip()
    
    key_map = {
        "ctrl": Key.ctrl, "control": Key.ctrl,
        "alt": Key.alt,
        "shift": Key.shift,
        "cmd": Key.cmd, "command": Key.cmd, "win": Key.cmd, "windows": Key.cmd, "meta": Key.cmd,
        "space": Key.space,
        "enter": Key.enter, "return": Key.enter,
        "tab": Key.tab,
        "esc": Key.esc, "escape": Key.esc,
        "backspace": Key.backspace,
        "delete": Key.delete,
        "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
        "pageup": Key.page_up, "pagedown": Key.page_down,
        "home": Key.home, "end": Key.end, "insert": Key.insert,
        "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
        "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
        "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
    }
    
    if key_str in key_map:
        return key_map[key_str]
    
    if len(key_str) == 1:
        return KeyCode.from_char(key_str)
    
    return KeyCode.from_vk(int(key_str)) if key_str.isdigit() else key_str


def _button_from_string(button_str: str) -> Button:
    """Convert string button name to pynput Button."""
    button_str = button_str.lower().strip()
    if button_str in ["left", "1"]:
        return Button.left
    elif button_str in ["right", "2"]:
        return Button.right
    elif button_str in ["middle", "3"]:
        return Button.middle
    else:
        return Button.left


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
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    
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
        
        if name == "click":
            button = _button_from_string(arguments.get("button", "left"))
            mouse_controller.click(button)
            state = computer_state.get_state()
            result = {"success": True, "action": "click", "button": arguments.get("button", "left")}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "double_click":
            button = _button_from_string(arguments.get("button", "left"))
            mouse_controller.click(button, 2)
            state = computer_state.get_state()
            result = {"success": True, "action": "double_click", "button": arguments.get("button", "left")}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "triple_click":
            button = _button_from_string(arguments.get("button", "left"))
            mouse_controller.click(button, 3)
            state = computer_state.get_state()
            result = {"success": True, "action": "triple_click", "button": arguments.get("button", "left")}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "button_down":
            button = _button_from_string(arguments.get("button", "left"))
            mouse_controller.press(button)
            state = computer_state.get_state()
            result = {"success": True, "action": "button_down", "button": arguments.get("button", "left")}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "button_up":
            button = _button_from_string(arguments.get("button", "left"))
            mouse_controller.release(button)
            state = computer_state.get_state()
            result = {"success": True, "action": "button_up", "button": arguments.get("button", "left")}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "drag":
            start = arguments["start"]
            end = arguments["end"]
            button = _button_from_string(arguments.get("button", "left"))
            
            # Move to start, press button, move to end, release button
            mouse_controller.position = (start["x"], start["y"])
            mouse_controller.press(button)
            time.sleep(0.01)  # Small delay
            mouse_controller.position = (end["x"], end["y"])
            time.sleep(0.01)
            mouse_controller.release(button)
            
            state = computer_state.get_state()
            result = {"success": True, "action": "drag", "start": start, "end": end, "button": arguments.get("button", "left")}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "mouse_move":
            x = arguments["x"]
            y = arguments["y"]
            mouse_controller.position = (x, y)
            state = computer_state.get_state()
            result = {"success": True, "action": "mouse_move", "x": x, "y": y}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "type":
            text = arguments["text"]
            keyboard_controller.type(text)
            state = computer_state.get_state()
            result = {"success": True, "action": "type", "text": text}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "key_down":
            key_str = arguments["key"]
            key = _key_from_string(key_str)
            keyboard_controller.press(key)
            state = computer_state.get_state()
            result = {"success": True, "action": "key_down", "key": key_str}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "key_up":
            key_str = arguments["key"]
            key = _key_from_string(key_str)
            keyboard_controller.release(key)
            state = computer_state.get_state()
            result = {"success": True, "action": "key_up", "key": key_str}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "key_press":
            key_str = arguments["key"]
            key = _key_from_string(key_str)
            keyboard_controller.press(key)
            keyboard_controller.release(key)
            state = computer_state.get_state()
            result = {"success": True, "action": "key_press", "key": key_str}
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "screenshot":
            screenshot_data = _capture_screenshot()
            state = computer_state.get_state(include_screenshot=False)  # Don't double-capture
            result = {"success": True, "action": "screenshot"}
            result.update(screenshot_data)
            result.update(state)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "set_config":
            # Update configuration
            if "observe_screen" in arguments:
                computer_state.config["observe_screen"] = arguments["observe_screen"]
            
            if "observe_mouse_position" in arguments:
                computer_state.config["observe_mouse_position"] = arguments["observe_mouse_position"]
            
            if "observe_mouse_button_states" in arguments:
                computer_state.config["observe_mouse_button_states"] = arguments["observe_mouse_button_states"]
            
            if "observe_keyboard_key_states" in arguments:
                computer_state.config["observe_keyboard_key_states"] = arguments["observe_keyboard_key_states"]
            
            if "observe_focused_app" in arguments:
                computer_state.config["observe_focused_app"] = arguments["observe_focused_app"]
            
            if "observe_accessibility_tree" in arguments:
                computer_state.config["observe_accessibility_tree"] = arguments["observe_accessibility_tree"]
            
            result = {
                "success": True,
                "action": "set_config",
                "config": computer_state.config.copy()
            }
            return [TextContent(type="text", text=json.dumps(result))]
        
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    
    except Exception as e:
        error_msg = {"error": str(e), "tool": name, "arguments": arguments}
        return [TextContent(type="text", text=json.dumps(error_msg))]


async def main():
    """Main entry point."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
