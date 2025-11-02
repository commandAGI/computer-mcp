"""Windows-specific implementations."""

from typing import Any

import psutil


def get_focused_app() -> dict[str, Any]:
    """Get current focused application on Windows."""
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


def get_accessibility_tree() -> dict[str, Any]:
    """Get Windows accessibility tree."""
    try:
        import win32gui
        import win32process
    except ImportError:
        return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows accessibility tree support"}
    
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

