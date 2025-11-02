"""macOS-specific implementations."""

import subprocess
from typing import Any


def get_focused_app() -> dict[str, Any]:
    """Get current focused application on macOS."""
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


def get_accessibility_tree() -> dict[str, Any]:
    """Get macOS accessibility tree using AppleScript."""
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

