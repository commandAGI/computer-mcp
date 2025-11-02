# Computer MCP Server

A cross-platform Model Context Protocol (MCP) server for computer automation and control. Provides tools for mouse/keyboard automation, screenshot capture (included by default in all responses), and comprehensive state tracking including accessibility tree support.

## Features

- **Mouse Control**: Click, double-click, triple-click, button down/up, drag operations
- **Keyboard Control**: Type text, key down/up/press
- **Screenshot Capture**: Fast cross-platform screenshot using `mss`, returns images as MCP ImageContent (included by default)
- **State Tracking**: Configurable tracking of mouse position/buttons, keyboard keys, focused app, and accessibility tree
- **Accessibility Tree**: Full platform-specific implementation for Windows, macOS, and Linux/Ubuntu
- **Zero Config**: Screenshots included by default - no need to call screenshot tool separately

## Installation

```bash
# Install core dependencies
pip install -e .

# Platform-specific optional dependencies (for enhanced features)
pip install -e ".[windows]"   # Windows: pywin32 for accessibility tree
pip install -e ".[macos]"      # macOS: pyobjc for native accessibility (AppleScript fallback available)
pip install -e ".[linux]"      # Linux: PyGObject for AT-SPI (requires: sudo apt install python3-gi gir1.2-atspi-2.0)
```

## Usage

### As MCP Server

Configure this server in your MCP client (e.g., Cursor, Claude Desktop):

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

### Available Tools

#### Mouse Tools

- `click(button='left'|'middle'|'right')` - Click at current cursor position
- `double_click(button='left'|'middle'|'right')` - Double-click at current cursor position
- `triple_click(button='left'|'middle'|'right')` - Triple-click at current cursor position
- `button_down(button='left'|'middle'|'right')` - Press and hold a mouse button
- `button_up(button='left'|'middle'|'right')` - Release a mouse button
- `drag(start={x, y}, end={x, y}, button='left')` - Drag from start to end position
- `mouse_move(x, y)` - Move cursor to specified coordinates

#### Keyboard Tools

- `type(text)` - Type text string
- `key_down(key)` - Press and hold a key
- `key_up(key)` - Release a key
- `key_press(key)` - Press and release a key (convenience)

#### Screenshot

- `screenshot()` - Explicitly capture screenshot (but screenshots are included by default in all responses)

#### Configuration

- `set_config(...)` - Configure observation options:
  - `observe_screen` (bool, default: `true`): Include screenshots in all responses
  - `observe_mouse_position` (bool, default: `false`): Track and include mouse position
  - `observe_mouse_button_states` (bool, default: `false`): Track and include mouse button states
  - `observe_keyboard_key_states` (bool, default: `false`): Track and include keyboard key states
  - `observe_focused_app` (bool, default: `false`): Include focused application information
  - `observe_accessibility_tree` (bool, default: `false`): Include accessibility tree

### Example Tool Calls

```python
# Click at current cursor position (screenshot included automatically)
click(button="left")

# Drag operation
drag(start={"x": 100, "y": 200}, end={"x": 300, "y": 400}, button="left")

# Type text
type(text="Hello World")

# Move mouse then click
mouse_move(x=500, y=500)
click(button="right")

# Enable full observation
set_config(
    observe_screen=True,              # Default true
    observe_mouse_position=True,
    observe_mouse_button_states=True,
    observe_keyboard_key_states=True,
    observe_focused_app=True,
    observe_accessibility_tree=True
)

# Now all tool responses include comprehensive state
click(button="left")  # Includes: screenshot, mouse position, button states, keyboard states, focused app, accessibility tree
```

### Key Names

Special keys can be specified as strings:
- `"ctrl"`, `"alt"`, `"shift"`, `"cmd"` (or `"win"` on Windows)
- `"space"`, `"enter"`, `"tab"`, `"esc"`, `"backspace"`
- Arrow keys: `"up"`, `"down"`, `"left"`, `"right"`
- Function keys: `"f1"` through `"f12"`
- Regular characters: `"a"`, `"b"`, etc.

## Platform Support

### Windows
- **Full Support**: All mouse/keyboard operations work
- **Focused App**: Requires `pywin32` (install with `pip install -e ".[windows]"`)
- **Accessibility Tree**: Uses Windows UI Automation API (requires `pywin32`)

### macOS
- **Full Support**: All mouse/keyboard operations work
- **Focused App**: Uses AppleScript (no dependencies)
- **Accessibility Tree**: 
  - Native: Uses AXUIElement via `pyobjc` (install with `pip install -e ".[macos]"`)
  - Fallback: Uses AppleScript (works without dependencies, limited tree depth)

### Linux/Ubuntu
- **Full Support**: All mouse/keyboard operations work
- **Focused App**: Uses `xdotool` (install: `sudo apt install xdotool`)
- **Accessibility Tree**: 
  - Native: Uses AT-SPI via PyGObject (install: `sudo apt install python3-gi gir1.2-atspi-2.0`, then `pip install -e ".[linux]"`)
  - Fallback: Basic window info via `xdotool`

## Configuration Schema

The `set_config` tool accepts the following options:

```json
{
  "observe_screen": true,                // Include screenshots (default: true)
  "observe_mouse_position": false,       // Track mouse position
  "observe_mouse_button_states": false,  // Track mouse button states
  "observe_keyboard_key_states": false,  // Track keyboard key states
  "observe_focused_app": false,          // Include focused app info
  "observe_accessibility_tree": false    // Include accessibility tree
}
```

## Response Format

By default (with `observe_screen: true`), all tool responses include a screenshot as MCP `ImageContent`, which displays as an actual image in MCP clients:

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

**Note:** Screenshots are returned as `ImageContent` objects that display as actual images in MCP clients. The base64 image data is only included in the `ImageContent`, not in the JSON metadata.

## Architecture

- Uses `pynput` for cross-platform mouse/keyboard control and state tracking
- Uses `mss` for fast screenshot capture
- Uses `mcp` Python SDK for MCP server implementation
- State listeners start/stop dynamically based on configuration to minimize overhead
- Screenshots captured on-demand but included automatically in all responses (when enabled)

## Accessibility Tree Details

### Windows
- Uses **Windows UI Automation API** via `win32com`
- Provides full control tree with names, types, bounds, and children
- Focuses on the currently focused window
- Limited to 50 children per element and max depth of 5 levels to prevent huge responses

### macOS
- **Native**: Uses **AXUIElement** API via `pyobjc` for full accessibility tree
- **Fallback**: Uses **AppleScript** with System Events for basic UI element enumeration
- AppleScript fallback works without dependencies but has limited depth

### Linux/Ubuntu
- Uses **AT-SPI** (Assistive Technology Service Provider Interface) via PyGObject
- Provides desktop-wide accessibility tree
- Requires system packages: `python3-gi` and `gir1.2-atspi-2.0`

## Notes

- Screenshots are **included by default** in all tool responses (when `observe_screen: true`)
- Mouse tools operate at the **current cursor position** unless you explicitly move the mouse first
- State tracking listeners are automatically started/stopped based on configuration
- Accessibility tree implementations may vary in depth and detail across platforms
- Some platform-specific features require optional dependencies or system packages

## License

MIT
