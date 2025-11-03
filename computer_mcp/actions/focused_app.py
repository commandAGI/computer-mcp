"""Focused application detection actions."""

from computer_mcp.core.platform import IS_DARWIN, IS_LINUX, IS_WINDOWS

import subprocess
from typing import Any

if IS_WINDOWS:
    import psutil

    def get_focused_app() -> dict[str, Any]:
        """Get current focused application on Windows.
        
        Returns:
            Dictionary with app name, pid, and title, or error
        """
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

elif IS_DARWIN:
    def get_focused_app() -> dict[str, Any]:
        """Get current focused application on macOS.
        
        Returns:
            Dictionary with app name and title, or error
        """
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

elif IS_LINUX:
    def get_focused_app() -> dict[str, Any]:
        """Get current focused application on Linux.
        
        Returns:
            Dictionary with app title, or error
        """
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
    def get_focused_app() -> dict[str, Any]:
        """Get current focused application (unsupported platform).
        
        Returns:
            Dictionary with error message
        """
        import platform
        return {"error": f"Unsupported platform: {platform.system()}"}

