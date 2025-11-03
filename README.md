# Computer MCP

A cross-platform computer automation and control library supporting multiple interfaces:
- **MCP Server** (stdio + HTTP/SSE modes)
- **HTTP REST API** (with OpenAPI spec)
- **CLI** (command execution and server management)
- **Programmatic Module** (stateless Python functions)

Provides tools for mouse/keyboard automation, screenshot capture, window management, virtual desktops, and comprehensive state tracking including accessibility tree support.

## Features

- **Mouse Control**: Click, double-click, triple-click, button down/up, drag operations
- **Keyboard Control**: Type text, key down/up/press
- **Screenshot Capture**: Fast cross-platform screenshot using `mss`, returns images as base64 or PNG
- **Window Management**: List, switch, move, resize, minimize, maximize, snap windows
- **Virtual Desktops**: List, switch, and move windows between virtual desktops
- **State Tracking**: Configurable tracking of mouse position/buttons, keyboard keys, focused app, and accessibility tree
- **Accessibility Tree**: Full platform-specific implementation for Windows, macOS, and Linux/Ubuntu

## Installation

```bash
# Install core dependencies
pip install -e .

# Optional: Install API/HTTP dependencies
pip install -e ".[api]"    # For HTTP REST API server
pip install -e ".[http]"   # For MCP HTTP/SSE mode
pip install -e ".[dev]"    # All optional dependencies

# Platform-specific optional dependencies (for enhanced features)
pip install -e ".[windows]"   # Windows: pywin32 for accessibility tree
pip install -e ".[macos]"      # macOS: pyobjc for native accessibility (AppleScript fallback available)
pip install -e ".[linux]"      # Linux: PyGObject for AT-SPI (requires: sudo apt install python3-gi gir1.2-atspi-2.0)
```

## Usage

### 1. As MCP Server (stdio mode)

The default mode for MCP clients like Cursor or Claude Desktop.

**Configuration** (e.g., `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "computer-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\Jacob\\Code\\computer-mcp",
        "run",
        "computer-mcp"
      ]
    }
  }
}
```

Or using `uvx`:

```json
{
  "mcpServers": {
    "computer-mcp": {
      "command": "uvx",
      "args": ["computer-mcp"]
    }
  }
}
```

**Note**: `uvx` automatically installs and runs the package if not already installed. Make sure you have [uv](https://github.com/astral-sh/uv) installed.

### 2. As MCP Server (HTTP/SSE mode)

For remote access via HTTP/SSE:

```bash
python -m computer_mcp serve mcp --http --host 127.0.0.1 --port 8000
```

This starts the MCP server with:
- SSE endpoint: `http://127.0.0.1:8000/sse`
- Tool call endpoint: `http://127.0.0.1:8000/mcp`

### 3. As HTTP REST API Server

Start the FastAPI server with automatic OpenAPI documentation:

```bash
python -m computer_mcp serve api --host 127.0.0.1 --port 8000
```

Or using the CLI:

```bash
computer-mcp serve api --port 8000
```

Then access:
- **API Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

**Example API calls**:

```bash
# Click mouse
curl -X POST http://localhost:8000/mouse/click -H "Content-Type: application/json" -d '{"button": "left"}'

# Type text
curl -X POST http://localhost:8000/keyboard/type -H "Content-Type: application/json" -d '{"text": "Hello World"}'

# Get screenshot as PNG
curl http://localhost:8000/screenshot/image -o screenshot.png

# List windows
curl http://localhost:8000/windows

# Switch to window
curl -X POST http://localhost:8000/windows/switch -H "Content-Type: application/json" -d '{"hwnd": 123456}'
```

### 4. As CLI Tool

Execute commands directly from the command line:

```bash
# Mouse commands
computer-mcp mouse click --button right
computer-mcp mouse double-click
computer-mcp mouse move --x 500 --y 300

# Keyboard commands
computer-mcp keyboard type "Hello World"
computer-mcp keyboard key-press ctrl

# Window commands
computer-mcp window list
computer-mcp window switch --hwnd 123456
computer-mcp window snap-left --hwnd 123456
computer-mcp window close --hwnd 123456

# Screenshot
computer-mcp screenshot --save screenshot.png

# Start servers
computer-mcp serve api --port 8000
computer-mcp serve mcp --http --port 8001

# JSON output
computer-mcp mouse click --json
```

### 5. As Python Module

Import and use stateless functions directly in your code:

```python
from computer_mcp import (
    click, double_click, move_mouse, drag,
    type_text, key_press, key_down, key_up,
    get_screenshot,
    list_windows, switch_to_window, close_window,
    snap_window_left, snap_window_right,
)

# Mouse operations
click("left")
double_click("right")
move_mouse(500, 300)
drag({"x": 100, "y": 200}, {"x": 300, "y": 400})

# Keyboard operations
type_text("Hello World")
key_press("ctrl")
key_down("shift")
key_up("shift")

# Screenshot
screenshot_data = get_screenshot()
print(f"Screenshot: {screenshot_data['width']}x{screenshot_data['height']}")

# Window management
windows = list_windows()
for window in windows.get("windows", []):
    print(f"{window['title']} (hwnd: {window['hwnd']})")

# Switch to a window by title
switch_to_window(title="Notepad")

# Snap window to left half
snap_window_left(hwnd=123456)
```

## Available Tools/Endpoints

### Mouse Operations

- `click(button='left'|'middle'|'right')` - Click at current cursor position
- `double_click(button='left'|'middle'|'right')` - Double-click at current cursor position
- `triple_click(button='left'|'middle'|'right')` - Triple-click at current cursor position
- `button_down(button='left'|'middle'|'right')` - Press and hold a mouse button
- `button_up(button='left'|'middle'|'right')` - Release a mouse button
- `drag(start={x, y}, end={x, y}, button='left')` - Drag from start to end position
- `mouse_move(x, y)` - Move cursor to specified coordinates

**REST API**: `POST /mouse/click`, `POST /mouse/drag`, `POST /mouse/move`, etc.

### Keyboard Operations

- `type(text)` - Type text string
- `key_down(key)` - Press and hold a key
- `key_up(key)` - Release a key
- `key_press(key)` - Press and release a key (convenience)

**REST API**: `POST /keyboard/type`, `POST /keyboard/key-press`, etc.

### Screenshot

- `screenshot()` / `get_screenshot()` - Capture screenshot (included by default in MCP responses)

**REST API**: 
- `GET /screenshot` - Returns JSON with base64 data
- `GET /screenshot/image` - Returns PNG image

### Window Management

- `list_windows()` - List all visible windows
- `switch_to_window(hwnd=<int>|title=<str>)` - Switch focus to a window
- `move_window(hwnd, x, y, width?, height?)` - Move and/or resize window
- `resize_window(hwnd, width, height)` - Resize window
- `minimize_window(hwnd)` - Minimize window
- `maximize_window(hwnd)` - Maximize window
- `restore_window(hwnd)` - Restore window
- `set_window_topmost(hwnd, topmost=true)` - Set window always-on-top
- `get_window_info(hwnd)` - Get detailed window information
- `close_window(hwnd)` - Close window
- `snap_window_left(hwnd)` - Snap to left half
- `snap_window_right(hwnd)` - Snap to right half
- `snap_window_top(hwnd)` - Snap to top half
- `snap_window_bottom(hwnd)` - Snap to bottom half
- `screenshot_window(hwnd)` - Capture screenshot of specific window

**REST API**: 
- `GET /windows` - List windows
- `POST /windows/switch` - Switch by handle
- `POST /windows/switch-by-title` - Switch by title
- `GET /windows/{hwnd}` - Get window info
- `DELETE /windows/{hwnd}` - Close window
- `POST /windows/{hwnd}/snap-left` - Snap left, etc.

### Virtual Desktops

- `list_virtual_desktops()` - List all virtual desktops
- `switch_virtual_desktop(desktop_id=<int>|name=<str>)` - Switch to virtual desktop
- `move_window_to_virtual_desktop(hwnd, desktop_id)` - Move window to desktop

**REST API**: 
- `GET /virtual-desktops` - List desktops
- `POST /virtual-desktops/switch` - Switch desktop
- `POST /windows/{hwnd}/move-to-desktop` - Move window

### Configuration

- `set_config(...)` - Configure observation options:
  - `observe_screen` (bool, default: `true`): Include screenshots in all responses
  - `observe_mouse_position` (bool, default: `false`): Track and include mouse position
  - `observe_mouse_button_states` (bool, default: `false`): Track and include mouse button states
  - `observe_keyboard_key_states` (bool, default: `false`): Track and include keyboard key states
  - `observe_focused_app` (bool, default: `false`): Include focused application information
  - `observe_accessibility_tree` (bool, default: `false`): Include accessibility tree

**REST API**: `POST /config` - Update configuration

## Key Names

Special keys can be specified as strings:
- `"ctrl"`, `"alt"`, `"shift"`, `"cmd"` (or `"win"` on Windows)
- `"space"`, `"enter"`, `"tab"`, `"esc"`, `"backspace"`
- Arrow keys: `"up"`, `"down"`, `"left"`, `"right"`
- Function keys: `"f1"` through `"f12"`
- Regular characters: `"a"`, `"b"`, etc.

## Platform Support

### Windows
- **Full Support**: All mouse/keyboard operations work
- **Window Management**: Full support via `pywin32` (included in `[windows]` extras)
- **Virtual Desktops**: Full support via `VirtualDesktopAccessor.dll`
- **Focused App**: Requires `pywin32` (install with `pip install -e ".[windows]"`)
- **Accessibility Tree**: Uses Windows UI Automation API (requires `pywin32`)

### macOS
- **Full Support**: All mouse/keyboard operations work
- **Window Management**: Limited support via AppleScript (some operations not yet implemented)
- **Virtual Desktops**: Limited support (Spaces enumeration/switching via Mission Control API)
- **Focused App**: Uses AppleScript (no dependencies)
- **Accessibility Tree**: 
  - Native: Uses AXUIElement via `pyobjc` (install with `pip install -e ".[macos]"`)
  - Fallback: Uses AppleScript (works without dependencies, limited tree depth)

### Linux/Ubuntu
- **Full Support**: All mouse/keyboard operations work
- **Window Management**: Full support via `xdotool` (install: `sudo apt install xdotool`)
- **Virtual Desktops**: Full support via `wmctrl` or `xdotool` (install: `sudo apt install wmctrl`)
- **Focused App**: Uses `xdotool` (install: `sudo apt install xdotool`)
- **Accessibility Tree**: 
  - Native: Uses AT-SPI via PyGObject (install: `sudo apt install python3-gi gir1.2-atspi-2.0`, then `pip install -e ".[linux]"`)
  - Fallback: Basic window info via `xdotool`

## Architecture

The codebase is organized into clear layers:

```
computer_mcp/
├── __init__.py          # Module API (stateless functions)
├── __main__.py          # CLI entry point
├── cli.py               # CLI implementation
├── mcp.py               # MCP server (stdio + HTTP/SSE)
├── api.py               # HTTP REST API server
├── actions/             # Business logic (pure functions)
│   ├── mouse.py
│   ├── keyboard.py
│   ├── window.py
│   ├── screenshot.py
│   ├── config.py
│   ├── focused_app.py
│   └── accessibility_tree.py
├── core/                # Core utilities
│   ├── state.py
│   ├── platform.py
│   ├── screenshot.py
│   ├── response.py
│   └── utils.py
└── resources/           # Platform-specific resources
```

**Key Design Principles:**
- **Actions layer**: Pure business logic functions, no interface dependencies
- **Interface adapters**: MCP, API, CLI wrap the actions layer
- **Stateless module API**: Clean functions for direct Python usage
- **State management**: Optional, configurable per interface

## Response Format

### MCP Server Response

By default (with `observe_screen: true`), all tool responses include a screenshot as MCP `ImageContent`:

**Response Structure:**
- `ImageContent` (type: "image"): Contains the screenshot as base64-encoded PNG with mimeType "image/png"
- `TextContent` (type: "text"): Contains JSON with action results and screenshot metadata:

```json
{
  "success": true,
  "action": "click",
  "button": "left",
  "screenshot": {
    "format": "base64_png",
    "width": 1920,
    "height": 1080
  }
}
```

With full observation enabled, the TextContent includes additional state:

```json
{
  "success": true,
  "action": "click",
  "button": "left",
  "screenshot": {
    "format": "base64_png",
    "width": 1920,
    "height": 1080
  },
  "mouse_position": {"x": 500, "y": 300},
  "mouse_button_states": ["Button.left"],
  "keyboard_key_states": ["ctrl"],
  "focused_app": {
    "name": "Code",
    "pid": 12345,
    "title": "main.py - computer-mcp"
  },
  "accessibility_tree": {
    "tree": {
      "name": "Application",
      "control_type": "...",
      "bounds": {"x": 0, "y": 0, "width": 1920, "height": 1080},
      "children": [...]
    }
  }
}
```

### HTTP REST API Response

Returns JSON directly:

```json
{
  "success": true,
  "action": "click",
  "button": "left"
}
```

Screenshots are returned as base64-encoded strings in JSON, or use the `/screenshot/image` endpoint for raw PNG.

### CLI Output

Default: Human-readable success/error messages
With `--json`: JSON output matching API format

### Module API Response

Returns plain Python dictionaries:

```python
result = click("left")
# result = {"success": True, "action": "click", "button": "left"}
```

## Notes

- Screenshots are **included by default** in MCP tool responses (when `observe_screen: true`)
- Mouse tools operate at the **current cursor position** unless you explicitly move the mouse first
- State tracking listeners are automatically started/stopped based on configuration
- Accessibility tree implementations may vary in depth and detail across platforms
- Some platform-specific features require optional dependencies or system packages
- Window management features vary by platform (Windows has full support, macOS/Linux have partial support)

## License

MIT
