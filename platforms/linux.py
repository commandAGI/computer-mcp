"""Linux-specific implementations."""

import subprocess
from typing import Any


def get_focused_app() -> dict[str, Any]:
    """Get current focused application on Linux."""
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


def get_accessibility_tree() -> dict[str, Any]:
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
        except:
            pass
        return {"error": "python-gi/AT-SPI not installed", "note": "Install python3-gi and gir1.2-atspi-2.0 for Linux accessibility tree support"}
    except Exception as e:
        return {"error": f"Linux AT-SPI error: {str(e)}"}

