"""HTTP REST API server for computer control."""

import base64
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from computer_mcp.actions import (
    accessibility_tree as accessibility_tree_actions,
    config as config_actions,
    focused_app as focused_app_actions,
    keyboard as keyboard_actions,
    mouse as mouse_actions,
    screenshot as screenshot_actions,
    window as window_actions,
)
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController

# Initialize controllers
mouse_controller = MouseController()
keyboard_controller = KeyboardController()

app = FastAPI(
    title="Computer Control API",
    description="REST API for cross-platform computer automation and control",
    version="0.0.3",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Request models
class ClickRequest(BaseModel):
    button: str = "left"


class MouseMoveRequest(BaseModel):
    x: int
    y: int


class DragRequest(BaseModel):
    start: dict[str, int]
    end: dict[str, int]
    button: str = "left"


class TypeRequest(BaseModel):
    text: str


class KeyRequest(BaseModel):
    key: str


class ConfigRequest(BaseModel):
    observe_screen: Optional[bool] = None
    observe_mouse_position: Optional[bool] = None
    observe_mouse_button_states: Optional[bool] = None
    observe_keyboard_key_states: Optional[bool] = None
    observe_focused_app: Optional[bool] = None
    observe_accessibility_tree: Optional[bool] = None


class WindowRequest(BaseModel):
    hwnd: int


class WindowTitleRequest(BaseModel):
    title: str


class MoveWindowRequest(BaseModel):
    hwnd: int
    x: int
    y: int
    width: Optional[int] = None
    height: Optional[int] = None


class ResizeWindowRequest(BaseModel):
    hwnd: int
    width: int
    height: int


class SetWindowTopmostRequest(BaseModel):
    hwnd: int
    topmost: bool = True


class VirtualDesktopRequest(BaseModel):
    desktop_id: Optional[int] = None
    name: Optional[str] = None


class MoveWindowToDesktopRequest(BaseModel):
    hwnd: int
    desktop_id: int


# Mouse endpoints
@app.post("/mouse/click")
async def mouse_click(request: ClickRequest) -> dict[str, Any]:
    """Perform a mouse click."""
    result = mouse_actions.click(button=request.button, controller=mouse_controller)
    return result


@app.post("/mouse/double-click")
async def mouse_double_click(request: ClickRequest) -> dict[str, Any]:
    """Perform a double mouse click."""
    result = mouse_actions.double_click(button=request.button, controller=mouse_controller)
    return result


@app.post("/mouse/triple-click")
async def mouse_triple_click(request: ClickRequest) -> dict[str, Any]:
    """Perform a triple mouse click."""
    result = mouse_actions.triple_click(button=request.button, controller=mouse_controller)
    return result


@app.post("/mouse/button-down")
async def mouse_button_down(request: ClickRequest) -> dict[str, Any]:
    """Press and hold a mouse button."""
    result = mouse_actions.button_down(button=request.button, controller=mouse_controller)
    return result


@app.post("/mouse/button-up")
async def mouse_button_up(request: ClickRequest) -> dict[str, Any]:
    """Release a mouse button."""
    result = mouse_actions.button_up(button=request.button, controller=mouse_controller)
    return result


@app.post("/mouse/drag")
async def mouse_drag(request: DragRequest) -> dict[str, Any]:
    """Drag mouse from start to end position."""
    result = mouse_actions.drag(
        start=request.start,
        end=request.end,
        button=request.button,
        controller=mouse_controller
    )
    return result


@app.post("/mouse/move")
async def mouse_move(request: MouseMoveRequest) -> dict[str, Any]:
    """Move the mouse cursor to specified coordinates."""
    result = mouse_actions.move_mouse(
        x=request.x,
        y=request.y,
        controller=mouse_controller
    )
    return result


# Keyboard endpoints
@app.post("/keyboard/type")
async def keyboard_type(request: TypeRequest) -> dict[str, Any]:
    """Type the specified text."""
    result = keyboard_actions.type_text(text=request.text, controller=keyboard_controller)
    return result


@app.post("/keyboard/key-down")
async def keyboard_key_down(request: KeyRequest) -> dict[str, Any]:
    """Press and hold a key."""
    result = keyboard_actions.key_down(key=request.key, controller=keyboard_controller)
    return result


@app.post("/keyboard/key-up")
async def keyboard_key_up(request: KeyRequest) -> dict[str, Any]:
    """Release a key."""
    result = keyboard_actions.key_up(key=request.key, controller=keyboard_controller)
    return result


@app.post("/keyboard/key-press")
async def keyboard_key_press(request: KeyRequest) -> dict[str, Any]:
    """Press and release a key."""
    result = keyboard_actions.key_press(key=request.key, controller=keyboard_controller)
    return result


# Screenshot endpoints
@app.get("/screenshot")
async def get_screenshot() -> dict[str, Any]:
    """Capture a screenshot of the display."""
    result = screenshot_actions.get_screenshot()
    return result


@app.get("/screenshot/image")
async def get_screenshot_image():
    """Get screenshot as PNG image."""
    result = screenshot_actions.get_screenshot()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    if "data" not in result:
        raise HTTPException(status_code=500, detail="No screenshot data available")
    
    image_data = base64.b64decode(result["data"])
    from fastapi.responses import Response
    return Response(content=image_data, media_type="image/png")


# Window management endpoints
@app.get("/windows")
async def list_windows() -> dict[str, Any]:
    """List all visible windows."""
    result = window_actions.list_windows()
    return result


@app.post("/windows/switch")
async def switch_to_window(request: WindowRequest) -> dict[str, Any]:
    """Switch focus to a window by handle."""
    result = window_actions.switch_to_window(hwnd=request.hwnd)
    return result


@app.post("/windows/switch-by-title")
async def switch_to_window_by_title(request: WindowTitleRequest) -> dict[str, Any]:
    """Switch focus to a window by title pattern."""
    result = window_actions.switch_to_window(title=request.title)
    return result


@app.post("/windows/move")
async def move_window(request: MoveWindowRequest) -> dict[str, Any]:
    """Move and/or resize a window."""
    result = window_actions.move_window(
        hwnd=request.hwnd,
        x=request.x,
        y=request.y,
        width=request.width,
        height=request.height
    )
    return result


@app.post("/windows/resize")
async def resize_window(request: ResizeWindowRequest) -> dict[str, Any]:
    """Resize a window."""
    result = window_actions.resize_window(
        hwnd=request.hwnd,
        width=request.width,
        height=request.height
    )
    return result


@app.post("/windows/minimize")
async def minimize_window(request: WindowRequest) -> dict[str, Any]:
    """Minimize a window."""
    result = window_actions.minimize_window(hwnd=request.hwnd)
    return result


@app.post("/windows/maximize")
async def maximize_window(request: WindowRequest) -> dict[str, Any]:
    """Maximize a window."""
    result = window_actions.maximize_window(hwnd=request.hwnd)
    return result


@app.post("/windows/restore")
async def restore_window(request: WindowRequest) -> dict[str, Any]:
    """Restore a window."""
    result = window_actions.restore_window(hwnd=request.hwnd)
    return result


@app.post("/windows/set-topmost")
async def set_window_topmost(request: SetWindowTopmostRequest) -> dict[str, Any]:
    """Set or remove a window's always-on-top property."""
    result = window_actions.set_window_topmost(
        hwnd=request.hwnd,
        topmost=request.topmost
    )
    return result


@app.get("/windows/{hwnd}")
async def get_window_info(hwnd: int) -> dict[str, Any]:
    """Get detailed information about a window."""
    result = window_actions.get_window_info(hwnd=hwnd)
    return result


@app.delete("/windows/{hwnd}")
async def close_window(hwnd: int) -> dict[str, Any]:
    """Close a window."""
    result = window_actions.close_window(hwnd=hwnd)
    return result


@app.post("/windows/{hwnd}/snap-left")
async def snap_window_left(hwnd: int) -> dict[str, Any]:
    """Snap window to fill left half of screen."""
    result = window_actions.snap_window_left(hwnd=hwnd)
    return result


@app.post("/windows/{hwnd}/snap-right")
async def snap_window_right(hwnd: int) -> dict[str, Any]:
    """Snap window to fill right half of screen."""
    result = window_actions.snap_window_right(hwnd=hwnd)
    return result


@app.post("/windows/{hwnd}/snap-top")
async def snap_window_top(hwnd: int) -> dict[str, Any]:
    """Snap window to fill top half of screen."""
    result = window_actions.snap_window_top(hwnd=hwnd)
    return result


@app.post("/windows/{hwnd}/snap-bottom")
async def snap_window_bottom(hwnd: int) -> dict[str, Any]:
    """Snap window to fill bottom half of screen."""
    result = window_actions.snap_window_bottom(hwnd=hwnd)
    return result


@app.get("/windows/{hwnd}/screenshot")
async def screenshot_window(hwnd: int) -> dict[str, Any]:
    """Capture screenshot of a specific window."""
    result = window_actions.screenshot_window(hwnd=hwnd)
    return result


# Virtual desktop endpoints
@app.get("/virtual-desktops")
async def list_virtual_desktops() -> dict[str, Any]:
    """List all virtual desktops."""
    result = window_actions.list_virtual_desktops()
    return result


@app.post("/virtual-desktops/switch")
async def switch_virtual_desktop(request: VirtualDesktopRequest) -> dict[str, Any]:
    """Switch to a virtual desktop."""
    result = window_actions.switch_virtual_desktop(
        desktop_id=request.desktop_id,
        name=request.name
    )
    return result


@app.post("/windows/{hwnd}/move-to-desktop")
async def move_window_to_virtual_desktop(
    hwnd: int,
    request: MoveWindowToDesktopRequest
) -> dict[str, Any]:
    """Move a window to a different virtual desktop."""
    result = window_actions.move_window_to_virtual_desktop(
        hwnd=hwnd,
        desktop_id=request.desktop_id
    )
    return result


# Config endpoints
@app.post("/config")
async def set_config(request: ConfigRequest) -> dict[str, Any]:
    """Configure observation options."""
    result = config_actions.set_config(
        observe_screen=request.observe_screen,
        observe_mouse_position=request.observe_mouse_position,
        observe_mouse_button_states=request.observe_mouse_button_states,
        observe_keyboard_key_states=request.observe_keyboard_key_states,
        observe_focused_app=request.observe_focused_app,
        observe_accessibility_tree=request.observe_accessibility_tree,
    )
    return result


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Computer Control API",
        "version": "0.0.3",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

