"""Accessibility tree actions."""

from computer_mcp.core.platform import (
    IS_DARWIN,
    IS_LINUX,
    IS_LINUX_ACCESSIBILITY_MODULES_SUPPORTED,
    IS_WINDOWS,
)

import subprocess
from typing import Any

if IS_WINDOWS:
    import psutil

    def get_accessibility_tree() -> dict[str, Any]:
        """Get Windows accessibility tree.
        
        Returns:
            Dictionary with accessibility tree data or error
        """
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

elif IS_DARWIN:
    def get_accessibility_tree() -> dict[str, Any]:
        """Get macOS accessibility tree using AppleScript.
        
        Returns:
            Dictionary with accessibility tree data or error
        """
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
                timeout=3,
                check=False
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

elif IS_LINUX:
    def get_accessibility_tree() -> dict[str, Any]:
        """Get Linux accessibility tree using AT-SPI.
        
        Returns:
            Dictionary with accessibility tree data or error
        """
        if IS_LINUX_ACCESSIBILITY_MODULES_SUPPORTED:
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
                        except:  # noqa: E722
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
                        except:  # noqa: E722
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
            except Exception as e:
                return {"error": f"Linux AT-SPI error: {str(e)}"}
        else:
            # Fallback to xdotool for basic window info
            try:
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    check=False
                )
                if result.returncode == 0:
                    return {
                        "tree": {
                            "name": result.stdout.strip(),
                            "note": "Simplified tree - install python3-gi and gir1.2-atspi-2.0 for full accessibility tree"
                        }
                    }
            except:  # noqa: E722
                pass
            return {"error": "python-gi/AT-SPI not installed", "note": "Install python3-gi and gir1.2-atspi-2.0 for Linux accessibility tree support"}

else:
    def get_accessibility_tree() -> dict[str, Any]:
        """Get accessibility tree (unsupported platform).
        
        Returns:
            Dictionary with error message
        """
        import platform
        return {"error": f"Unsupported platform: {platform.system()}"}

