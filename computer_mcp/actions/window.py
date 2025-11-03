"""Window management actions."""

from computer_mcp.core.platform import IS_DARWIN, IS_LINUX, IS_WINDOWS

import subprocess
from typing import Any
from io import BytesIO

if IS_WINDOWS:
    import psutil
    import ctypes
    from ctypes import wintypes

    # DWM constants
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    _dwmapi = ctypes.windll.dwmapi

    class RECT(ctypes.Structure):
        _fields_ = [
            ('left', ctypes.c_long),
            ('top', ctypes.c_long),
            ('right', ctypes.c_long),
            ('bottom', ctypes.c_long)
        ]

    def _is_valid_window(hwnd: int) -> bool:
        """Check if window is valid and visible."""
        try:
            import win32gui
            if not win32gui.IsWindowVisible(hwnd):
                return False
            if win32gui.GetParent(hwnd) != 0:
                return False  # Skip child windows
            return True
        except Exception:
            return False

    def _get_window_data(hwnd: int) -> dict[str, Any] | None:
        """Get window data for a given handle."""
        try:
            import win32gui
            import win32process
            import win32con
            
            if not _is_valid_window(hwnd):
                return None
            
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return None  # Skip windows without titles
            
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(pid)
                process_name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "Unknown"
            
            rect = win32gui.GetWindowRect(hwnd)
            bounds = {
                "x": rect[0],
                "y": rect[1],
                "width": rect[2] - rect[0],
                "height": rect[3] - rect[1]
            }
            
            # Determine window state
            placement = win32gui.GetWindowPlacement(hwnd)
            if placement[1] == win32con.SW_SHOWMINIMIZED:
                state = "minimized"
            elif placement[1] == win32con.SW_SHOWMAXIMIZED:
                state = "maximized"
            else:
                state = "normal"
            
            return {
                "hwnd": hwnd,
                "title": title,
                "process": process_name,
                "pid": pid,
                "bounds": bounds,
                "state": state
            }
        except Exception:
            return None

    def _find_window_by_title(title_pattern: str) -> int | None:
        """Find window handle by title pattern."""
        import win32gui
        
        def enum_callback(hwnd, windows):
            if _is_valid_window(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if title_pattern.lower() in window_title.lower():
                    windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(enum_callback, windows)
        return windows[0] if windows else None

    def _set_dpi_aware_win():
        """Ensure coordinates match physical pixels on high-DPI displays."""
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    def _check_exit_fullscreen_win(hwnd: int):
        """Restore if window is maximized so it can be resized/moved."""
        try:
            import win32gui
            import win32con
            import time
            placement = win32gui.GetWindowPlacement(hwnd)
            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.05)
        except Exception:
            pass

    def _get_work_area_for_window(hwnd: int) -> tuple[int, int, int, int]:
        """Get work area (excluding taskbar) for the monitor containing the window."""
        try:
            import win32api
            import win32con
            monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
            mi = win32api.GetMonitorInfo(monitor)
            work = mi['Work']
            return work
        except Exception:
            try:
                import win32api
                import win32con
                width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                return (0, 0, width, height - 40)
            except Exception:
                return (0, 0, 1920, 1040)

    def _get_visible_frame_win(hwnd: int) -> tuple[int, int, int, int]:
        """Get visible frame bounds (excluding drop shadow) using DWM."""
        try:
            import win32gui
            rect = RECT()
            hr = _dwmapi.DwmGetWindowAttribute(
                wintypes.HWND(hwnd),
                ctypes.c_uint(DWMWA_EXTENDED_FRAME_BOUNDS),
                ctypes.byref(rect),
                ctypes.sizeof(rect),
            )
            if hr == 0:  # S_OK
                return (rect.left, rect.top, rect.right, rect.bottom)
        except Exception:
            pass
        try:
            import win32gui
            rect = win32gui.GetWindowRect(hwnd)
            return rect
        except Exception:
            return (0, 0, 1920, 1080)

    def _apply_window_bounds_win(hwnd: int, target_ltrb: tuple[int, int, int, int]):
        """Move/resize window so the visible frame aligns with the target rectangle."""
        try:
            import win32gui
            import win32con
            import time
            
            L, T, R, B = target_ltrb
            W = max(1, R - L)
            H = max(1, B - T)
            
            placement = win32gui.GetWindowPlacement(hwnd)
            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.05)
            
            win32gui.SetWindowPos(
                hwnd, 0, L, T, W, H,
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW
            )
            
            time.sleep(0.02)
            
            visL, visT, visR, visB = _get_visible_frame_win(hwnd)
            outL, outT, outR, outB = win32gui.GetWindowRect(hwnd)
            
            inset_left = visL - outL
            inset_top = visT - outT
            inset_right = outR - visR
            inset_bottom = outB - visB
            
            corrL = L - inset_left
            corrT = T - inset_top
            corrW = W + inset_left + inset_right
            corrH = H + inset_top + inset_bottom
            
            corrL = int(round(corrL))
            corrT = int(round(corrT))
            corrW = max(1, int(round(corrW)))
            corrH = max(1, int(round(corrH)))
            
            win32gui.SetWindowPos(
                hwnd, 0, corrL, corrT, corrW, corrH,
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW
            )
        except Exception:
            try:
                import win32gui
                import win32con
                import time
                placement = win32gui.GetWindowPlacement(hwnd)
                if placement[1] == win32con.SW_SHOWMAXIMIZED:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    time.sleep(0.05)
                
                L, T, R, B = target_ltrb
                W = max(1, R - L)
                H = max(1, B - T)
                win32gui.SetWindowPos(
                    hwnd, 0, L, T, W, H,
                    win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
                )
            except Exception:
                pass

    def list_windows() -> dict[str, Any]:
        """List all visible windows."""
        try:
            import win32gui
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        windows = []
        def enum_callback(hwnd, window_list):
            window_data = _get_window_data(hwnd)
            if window_data:
                window_list.append(window_data)
            return True
        
        win32gui.EnumWindows(enum_callback, windows)
        
        return {"success": True, "action": "list_windows", "windows": windows, "count": len(windows)}

    def switch_to_window(hwnd: int | None = None, title: str | None = None) -> dict[str, Any]:
        """Switch focus to a window by handle or title pattern."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        if hwnd is None:
            if title:
                hwnd = _find_window_by_title(title)
                if not hwnd:
                    return {"error": f"Window with title pattern '{title}' not found"}
            else:
                return {"error": "Either 'hwnd' or 'title' parameter is required"}
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "switch_to_window", "window": window_data}
        except Exception as e:
            return {"error": f"Failed to switch to window: {str(e)}"}

    def move_window(hwnd: int, x: int, y: int, width: int | None = None, height: int | None = None) -> dict[str, Any]:
        """Move and/or resize a window."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            flags = win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            if width is None or height is None:
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
            
            win32gui.SetWindowPos(hwnd, 0, x, y, width, height, flags)
            
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "move_window", "window": window_data}
        except Exception as e:
            return {"error": f"Failed to move window: {str(e)}"}

    def resize_window(hwnd: int, width: int, height: int) -> dict[str, Any]:
        """Resize a window."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            rect = win32gui.GetWindowRect(hwnd)
            x = rect[0]
            y = rect[1]
            
            flags = win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE
            win32gui.SetWindowPos(hwnd, 0, x, y, width, height, flags)
            
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "resize_window", "window": window_data}
        except Exception as e:
            return {"error": f"Failed to resize window: {str(e)}"}

    def minimize_window(hwnd: int) -> dict[str, Any]:
        """Minimize a window."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "minimize_window", "window": window_data}
        except Exception as e:
            return {"error": f"Failed to minimize window: {str(e)}"}

    def maximize_window(hwnd: int) -> dict[str, Any]:
        """Maximize a window."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "maximize_window", "window": window_data}
        except Exception as e:
            return {"error": f"Failed to maximize window: {str(e)}"}

    def restore_window(hwnd: int) -> dict[str, Any]:
        """Restore a minimized or maximized window."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "restore_window", "window": window_data}
        except Exception as e:
            return {"error": f"Failed to restore window: {str(e)}"}

    def set_window_topmost(hwnd: int, topmost: bool = True) -> dict[str, Any]:
        """Set or remove a window's always-on-top property."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            hwnd_insert_after = win32con.HWND_TOPMOST if topmost else win32con.HWND_NOTOPMOST
            flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            win32gui.SetWindowPos(hwnd, hwnd_insert_after, 0, 0, 0, 0, flags)
            
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "set_window_topmost", "topmost": topmost, "window": window_data}
        except Exception as e:
            return {"error": f"Failed to set window topmost: {str(e)}"}

    def get_window_info(hwnd: int) -> dict[str, Any]:
        """Get detailed information about a window."""
        try:
            import win32gui
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        window_data = _get_window_data(hwnd)
        if not window_data:
            return {"error": "Invalid window handle or window not accessible"}
        
        return {"success": True, "action": "get_window_info", "window": window_data}

    def close_window(hwnd: int) -> dict[str, Any]:
        """Close a window."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return {"success": True, "action": "close_window", "hwnd": hwnd}
        except Exception as e:
            return {"error": f"Failed to close window: {str(e)}"}

    def snap_window_left(hwnd: int) -> dict[str, Any]:
        """Snap window to fill left half of screen."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            left, top, right, bottom = _get_work_area_for_window(hwnd)
            work_width = right - left
            
            target_left = left
            target_top = top
            target_right = left + (work_width // 2)
            target_bottom = bottom
            
            _apply_window_bounds_win(hwnd, (target_left, target_top, target_right, target_bottom))
            
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "snap_window_left", "window": window_data}
        except Exception as e:
            return {"error": f"Failed to snap window left: {str(e)}"}

    def snap_window_right(hwnd: int) -> dict[str, Any]:
        """Snap window to fill right half of screen."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            left, top, right, bottom = _get_work_area_for_window(hwnd)
            work_width = right - left
            
            target_left = left + (work_width // 2)
            target_top = top
            target_right = right
            target_bottom = bottom
            
            _apply_window_bounds_win(hwnd, (target_left, target_top, target_right, target_bottom))
            
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "snap_window_right", "window": window_data}
        except Exception as e:
            return {"error": f"Failed to snap window right: {str(e)}"}

    def snap_window_top(hwnd: int) -> dict[str, Any]:
        """Snap window to fill top half of screen."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            left, top, right, bottom = _get_work_area_for_window(hwnd)
            work_height = bottom - top
            
            target_left = left
            target_top = top
            target_right = right
            target_bottom = top + (work_height // 2)
            
            _apply_window_bounds_win(hwnd, (target_left, target_top, target_right, target_bottom))
            
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "snap_window_top", "window": window_data}
        except Exception as e:
            return {"error": f"Failed to snap window top: {str(e)}"}

    def snap_window_bottom(hwnd: int) -> dict[str, Any]:
        """Snap window to fill bottom half of screen."""
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            left, top, right, bottom = _get_work_area_for_window(hwnd)
            work_height = bottom - top
            
            target_left = left
            target_top = top + (work_height // 2)
            target_right = right
            target_bottom = bottom
            
            _apply_window_bounds_win(hwnd, (target_left, target_top, target_right, target_bottom))
            
            window_data = _get_window_data(hwnd)
            return {"success": True, "action": "snap_window_bottom", "window": window_data}
        except Exception as e:
            return {"error": f"Failed to snap window bottom: {str(e)}"}

    def screenshot_window(hwnd: int) -> dict[str, Any]:
        """Capture screenshot of a specific window."""
        try:
            import win32gui
            import win32ui
            import win32con
            from PIL import Image
            import base64
            from io import BytesIO
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window screenshot support"}
        
        try:
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)
            
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
            
            bmp_info = bitmap.GetInfo()
            bmp_str = bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                "RGB",
                (bmp_info["bmWidth"], bmp_info["bmHeight"]),
                bmp_str,
                "raw",
                "BGRX",
                0,
                1
            )
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
            
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            return {
                "success": True,
                "action": "screenshot_window",
                "hwnd": hwnd,
                "format": "base64_png",
                "data": img_base64,
                "width": width,
                "height": height
            }
        except Exception as e:
            return {"error": f"Failed to screenshot window: {str(e)}"}

    def list_virtual_desktops() -> dict[str, Any]:
        """List all virtual desktops with their IDs and names."""
        try:
            from computer_mcp.core.virtual_desktop import (
                is_available,
                get_desktop_count,
                get_current_desktop_number
            )
            
            if not is_available():
                return {
                    "success": True,
                    "action": "list_virtual_desktops",
                    "desktops": [{"id": 0, "name": "Desktop 1", "is_current": True}],
                    "note": "VirtualDesktopAccessor.dll not available. Basic single desktop returned."
                }
            
            count = get_desktop_count()
            current = get_current_desktop_number()
            
            if count is None:
                return {
                    "success": True,
                    "action": "list_virtual_desktops",
                    "desktops": [{"id": 0, "name": "Desktop 1", "is_current": True}],
                    "note": "Failed to get desktop count. Basic single desktop returned."
                }
            
            desktops = []
            for i in range(count):
                desktops.append({
                    "id": i,
                    "name": f"Desktop {i + 1}",
                    "is_current": i == current if current is not None else False
                })
            
            return {
                "success": True,
                "action": "list_virtual_desktops",
                "desktops": desktops
            }
        except Exception as e:
            return {"error": f"Failed to list virtual desktops: {str(e)}"}

    def switch_virtual_desktop(desktop_id: int | None = None, name: str | None = None) -> dict[str, Any]:
        """Switch to a virtual desktop by ID or name."""
        try:
            from computer_mcp.core.virtual_desktop import (
                is_available,
                go_to_desktop_number,
                get_desktop_count
            )
            
            if desktop_id is None and name is None:
                return {"error": "Either 'desktop_id' or 'name' parameter is required"}
            
            if name and desktop_id is None:
                try:
                    desktop_id = int(name.split()[-1]) - 1
                except (ValueError, IndexError):
                    return {"error": f"Could not parse desktop ID from name: {name}"}
            
            if not is_available():
                return {
                    "error": "Virtual desktop switching requires VirtualDesktopAccessor.dll",
                    "note": "VirtualDesktopAccessor.dll not found. Please ensure it's available in the resources directory."
                }
            
            count = get_desktop_count()
            if count is not None and desktop_id >= count:
                return {
                    "error": f"Desktop number {desktop_id} is out of range. Available desktops: 0-{count - 1}"
                }
            
            success = go_to_desktop_number(desktop_id)
            
            if success:
                return {"success": True, "action": "switch_virtual_desktop", "desktop_id": desktop_id}
            else:
                return {
                    "error": f"Failed to switch to desktop {desktop_id}",
                    "note": "The desktop number may be invalid or the operation failed."
                }
        except Exception as e:
            return {"error": f"Failed to switch virtual desktop: {str(e)}"}

    def move_window_to_virtual_desktop(hwnd: int, desktop_id: int) -> dict[str, Any]:
        """Move a window to a different virtual desktop."""
        try:
            from computer_mcp.core.virtual_desktop import (
                is_available,
                move_window_to_desktop_number,
                get_desktop_count
            )
            
            if not is_available():
                return {
                    "error": "Virtual desktop window moving requires VirtualDesktopAccessor.dll",
                    "note": "VirtualDesktopAccessor.dll not found. Please ensure it's available in the resources directory."
                }
            
            count = get_desktop_count()
            if count is not None and desktop_id >= count:
                return {
                    "error": f"Desktop number {desktop_id} is out of range. Available desktops: 0-{count - 1}"
                }
            
            if not isinstance(hwnd, int):
                try:
                    hwnd = int(hwnd)
                except (ValueError, TypeError):
                    return {"error": f"Invalid window handle: {hwnd}"}
            
            success = move_window_to_desktop_number(hwnd, desktop_id)
            
            if success:
                return {
                    "success": True,
                    "action": "move_window_to_virtual_desktop",
                    "hwnd": hwnd,
                    "desktop_id": desktop_id
                }
            else:
                return {
                    "error": f"Failed to move window {hwnd} to desktop {desktop_id}",
                    "note": "The window handle may be invalid or the desktop number may be out of range."
                }
        except Exception as e:
            return {"error": f"Failed to move window to virtual desktop: {str(e)}"}

elif IS_DARWIN:
    # macOS implementations
    def list_windows() -> dict[str, Any]:
        """List all visible windows (macOS - not yet implemented)."""
        return {"error": "Window management not yet implemented for macOS"}
    
    def switch_to_window(hwnd: int | None = None, title: str | None = None) -> dict[str, Any]:
        """Switch focus to a window (macOS - not yet implemented)."""
        return {"error": "Window management not yet implemented for macOS"}
    
    def move_window(hwnd: int, x: int, y: int, width: int | None = None, height: int | None = None) -> dict[str, Any]:
        """Move and/or resize a window (macOS - not yet implemented)."""
        return {"error": "Window management not yet implemented for macOS"}
    
    def resize_window(hwnd: int, width: int, height: int) -> dict[str, Any]:
        """Resize a window (macOS - not yet implemented)."""
        return {"error": "Window management not yet implemented for macOS"}
    
    def minimize_window(hwnd: int) -> dict[str, Any]:
        """Minimize a window (macOS - not yet implemented)."""
        return {"error": "Window management not yet implemented for macOS"}
    
    def maximize_window(hwnd: int) -> dict[str, Any]:
        """Maximize a window (macOS - not yet implemented)."""
        return {"error": "Window management not yet implemented for macOS"}
    
    def restore_window(hwnd: int) -> dict[str, Any]:
        """Restore a window (macOS - not yet implemented)."""
        return {"error": "Window management not yet implemented for macOS"}
    
    def set_window_topmost(hwnd: int, topmost: bool = True) -> dict[str, Any]:
        """Set window topmost (macOS - not yet implemented)."""
        return {"error": "Window management not yet implemented for macOS"}
    
    def get_window_info(hwnd: int) -> dict[str, Any]:
        """Get window info (macOS - not yet implemented)."""
        return {"error": "Window management not yet implemented for macOS"}
    
    def close_window(hwnd: int) -> dict[str, Any]:
        """Close a window."""
        window_id = hwnd
        script = f'''
        tell application "System Events"
            try
                set targetWindow to window id {window_id} of application process whose frontmost is true
                tell targetWindow
                    click button 1
                end tell
                return "success"
            on error
                return "error"
            end try
        end tell
        '''
        
        try:
            result_osascript = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2,
                check=False
            )
            if result_osascript.returncode == 0:
                return {"success": True, "action": "close_window", "window_id": window_id}
            else:
                return {"error": "Failed to close window"}
        except Exception as e:
            return {"error": f"Failed to close window: {str(e)}"}
    
    def snap_window_left(hwnd: int) -> dict[str, Any]:
        """Snap window to fill left half of screen."""
        window_id = hwnd
        script = f'''
        tell application "System Events"
            tell application process whose frontmost is true
                set screenWidth to screen width
                set screenHeight to screen height
                set visibleTop to 25
                set visibleHeight to screenHeight - visibleTop
                set dockHeight to 60
                set visibleHeight to visibleHeight - dockHeight
                set bounds of window id {window_id} to {{0, visibleTop, (screenWidth / 2), visibleTop + visibleHeight}}
            end tell
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=2)
            return {"success": True, "action": "snap_window_left", "window_id": window_id}
        except Exception as e:
            return {"error": f"Failed to snap window left: {str(e)}"}
    
    def snap_window_right(hwnd: int) -> dict[str, Any]:
        """Snap window to fill right half of screen."""
        window_id = hwnd
        script = f'''
        tell application "System Events"
            tell application process whose frontmost is true
                set screenWidth to screen width
                set screenHeight to screen height
                set visibleTop to 25
                set visibleHeight to screenHeight - visibleTop
                set dockHeight to 60
                set visibleHeight to visibleHeight - dockHeight
                set bounds of window id {window_id} to {{(screenWidth / 2), visibleTop, screenWidth, visibleTop + visibleHeight}}
            end tell
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=2)
            return {"success": True, "action": "snap_window_right", "window_id": window_id}
        except Exception as e:
            return {"error": f"Failed to snap window right: {str(e)}"}
    
    def snap_window_top(hwnd: int) -> dict[str, Any]:
        """Snap window to fill top half of screen."""
        window_id = hwnd
        script = f'''
        tell application "System Events"
            tell application process whose frontmost is true
                set screenWidth to screen width
                set screenHeight to screen height
                set visibleTop to 25
                set visibleHeight to screenHeight - visibleTop
                set dockHeight to 60
                set visibleHeight to visibleHeight - dockHeight
                set bounds of window id {window_id} to {{0, visibleTop, screenWidth, visibleTop + (visibleHeight / 2)}}
            end tell
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=2)
            return {"success": True, "action": "snap_window_top", "window_id": window_id}
        except Exception as e:
            return {"error": f"Failed to snap window top: {str(e)}"}
    
    def snap_window_bottom(hwnd: int) -> dict[str, Any]:
        """Snap window to fill bottom half of screen."""
        window_id = hwnd
        script = f'''
        tell application "System Events"
            tell application process whose frontmost is true
                set screenWidth to screen width
                set screenHeight to screen height
                set visibleTop to 25
                set visibleHeight to screenHeight - visibleTop
                set dockHeight to 60
                set visibleHeight to visibleHeight - dockHeight
                set midPoint to visibleTop + (visibleHeight / 2)
                set bounds of window id {window_id} to {{0, midPoint, screenWidth, visibleTop + visibleHeight}}
            end tell
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=2)
            return {"success": True, "action": "snap_window_bottom", "window_id": window_id}
        except Exception as e:
            return {"error": f"Failed to snap window bottom: {str(e)}"}
    
    def screenshot_window(hwnd: int) -> dict[str, Any]:
        """Capture screenshot of a specific window."""
        window_id = hwnd
        try:
            script_bounds = f'''
            tell application "System Events"
                tell application process whose frontmost is true
                    set winBounds to bounds of window id {window_id}
                    return winBounds
                end tell
            end tell
            '''
            
            result_bounds = subprocess.run(
                ["osascript", "-e", script_bounds],
                capture_output=True,
                text=True,
                timeout=2,
                check=False
            )
            
            if result_bounds.returncode != 0:
                return {"error": "Failed to get window bounds"}
            
            bounds_str = result_bounds.stdout.strip()
            bounds = [int(x.strip()) for x in bounds_str.replace("{", "").replace("}", "").split(",")]
            x, y, right, bottom = bounds
            width = right - x
            height = bottom - y
            
            import tempfile
            import base64
            from PIL import Image
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            
            result_capture = subprocess.run(
                ["screencapture", "-R", f"{x},{y},{width},{height}", tmp_path],
                timeout=5,
                check=False
            )
            
            if result_capture.returncode == 0:
                img = Image.open(tmp_path)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                img_bytes = buffer.getvalue()
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                
                return {
                    "success": True,
                    "action": "screenshot_window",
                    "window_id": window_id,
                    "format": "base64_png",
                    "data": img_base64,
                    "width": width,
                    "height": height
                }
            else:
                return {"error": "Failed to capture window screenshot"}
        except Exception as e:
            return {"error": f"Failed to screenshot window: {str(e)}"}
    
    def list_virtual_desktops() -> dict[str, Any]:
        """List all virtual desktops (macOS Spaces - limited)."""
        return {
            "success": True,
            "action": "list_virtual_desktops",
            "desktops": [{"id": 0, "name": "Space 1", "is_current": True}],
            "note": "macOS Spaces enumeration is limited via AppleScript. Multiple Spaces may exist but are not easily enumerated."
        }
    
    def switch_virtual_desktop(desktop_id: int | None = None, name: str | None = None) -> dict[str, Any]:
        """Switch to a virtual desktop (macOS Spaces - limited)."""
        return {
            "success": True,
            "action": "switch_virtual_desktop",
            "desktop_id": desktop_id or 0,
            "note": "macOS Spaces switching via script is limited. Use Control+Left/Right manually or Mission Control API."
        }
    
    def move_window_to_virtual_desktop(hwnd: int, desktop_id: int) -> dict[str, Any]:
        """Move a window to a different virtual desktop (macOS Spaces - limited)."""
        return {
            "success": True,
            "action": "move_window_to_virtual_desktop",
            "window_id": hwnd,
            "desktop_id": desktop_id,
            "note": "macOS Spaces window moving requires Mission Control API which is not easily accessible via AppleScript."
        }

elif IS_LINUX:
    # Linux implementations
    def list_windows() -> dict[str, Any]:
        """List all visible windows (Linux - not yet implemented)."""
        return {"error": "Window management not yet implemented for Linux"}
    
    def switch_to_window(hwnd: int | None = None, title: str | None = None) -> dict[str, Any]:
        """Switch focus to a window (Linux - not yet implemented)."""
        return {"error": "Window management not yet implemented for Linux"}
    
    def move_window(hwnd: int, x: int, y: int, width: int | None = None, height: int | None = None) -> dict[str, Any]:
        """Move and/or resize a window (Linux - not yet implemented)."""
        return {"error": "Window management not yet implemented for Linux"}
    
    def resize_window(hwnd: int, width: int, height: int) -> dict[str, Any]:
        """Resize a window (Linux - not yet implemented)."""
        return {"error": "Window management not yet implemented for Linux"}
    
    def minimize_window(hwnd: int) -> dict[str, Any]:
        """Minimize a window (Linux - not yet implemented)."""
        return {"error": "Window management not yet implemented for Linux"}
    
    def maximize_window(hwnd: int) -> dict[str, Any]:
        """Maximize a window (Linux - not yet implemented)."""
        return {"error": "Window management not yet implemented for Linux"}
    
    def restore_window(hwnd: int) -> dict[str, Any]:
        """Restore a window (Linux - not yet implemented)."""
        return {"error": "Window management not yet implemented for Linux"}
    
    def set_window_topmost(hwnd: int, topmost: bool = True) -> dict[str, Any]:
        """Set window topmost (Linux - not yet implemented)."""
        return {"error": "Window management not yet implemented for Linux"}
    
    def get_window_info(hwnd: int) -> dict[str, Any]:
        """Get window info."""
        window_id = hwnd
        try:
            result_xdotool = subprocess.run(
                ["xdotool", "getwindowgeometry", str(window_id)],
                capture_output=True,
                text=True,
                timeout=1,
                check=False
            )
            
            if result_xdotool.returncode == 0:
                return {"success": True, "action": "get_window_info", "window_id": window_id, "info": result_xdotool.stdout}
            else:
                return {"error": "Failed to get window info"}
        except FileNotFoundError:
            return {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to get window info: {str(e)}"}
    
    def close_window(hwnd: int) -> dict[str, Any]:
        """Close a window."""
        window_id = hwnd
        try:
            subprocess.run(["xdotool", "windowclose", str(window_id)], timeout=2, check=False)
            return {"success": True, "action": "close_window", "window_id": window_id}
        except FileNotFoundError:
            return {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to close window: {str(e)}"}
    
    def snap_window_left(hwnd: int) -> dict[str, Any]:
        """Snap window to fill left half of screen."""
        window_id = hwnd
        try:
            result_screen = subprocess.run(
                ["xdotool", "getdisplaygeometry"],
                capture_output=True,
                text=True,
                timeout=1,
                check=False
            )
            
            if result_screen.returncode == 0:
                width, height = map(int, result_screen.stdout.strip().split())
                half_width = width // 2
                
                subprocess.run(["xdotool", "windowmove", str(window_id), "0", "0"], timeout=2, check=False)
                subprocess.run(["xdotool", "windowsize", str(window_id), str(half_width), str(height)], timeout=2, check=False)
                
                return {"success": True, "action": "snap_window_left", "window_id": window_id}
            else:
                return {"error": "Failed to get screen dimensions"}
        except FileNotFoundError:
            return {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to snap window left: {str(e)}"}
    
    def snap_window_right(hwnd: int) -> dict[str, Any]:
        """Snap window to fill right half of screen."""
        window_id = hwnd
        try:
            result_screen = subprocess.run(
                ["xdotool", "getdisplaygeometry"],
                capture_output=True,
                text=True,
                timeout=1,
                check=False
            )
            
            if result_screen.returncode == 0:
                width, height = map(int, result_screen.stdout.strip().split())
                half_width = width // 2
                x_pos = half_width
                
                subprocess.run(["xdotool", "windowmove", str(window_id), str(x_pos), "0"], timeout=2, check=False)
                subprocess.run(["xdotool", "windowsize", str(window_id), str(half_width), str(height)], timeout=2, check=False)
                
                return {"success": True, "action": "snap_window_right", "window_id": window_id}
            else:
                return {"error": "Failed to get screen dimensions"}
        except FileNotFoundError:
            return {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to snap window right: {str(e)}"}
    
    def snap_window_top(hwnd: int) -> dict[str, Any]:
        """Snap window to fill top half of screen."""
        window_id = hwnd
        try:
            result_screen = subprocess.run(
                ["xdotool", "getdisplaygeometry"],
                capture_output=True,
                text=True,
                timeout=1,
                check=False
            )
            
            if result_screen.returncode == 0:
                width, height = map(int, result_screen.stdout.strip().split())
                half_height = height // 2
                
                subprocess.run(["xdotool", "windowmove", str(window_id), "0", "0"], timeout=2, check=False)
                subprocess.run(["xdotool", "windowsize", str(window_id), str(width), str(half_height)], timeout=2, check=False)
                
                return {"success": True, "action": "snap_window_top", "window_id": window_id}
            else:
                return {"error": "Failed to get screen dimensions"}
        except FileNotFoundError:
            return {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to snap window top: {str(e)}"}
    
    def snap_window_bottom(hwnd: int) -> dict[str, Any]:
        """Snap window to fill bottom half of screen."""
        window_id = hwnd
        try:
            result_screen = subprocess.run(
                ["xdotool", "getdisplaygeometry"],
                capture_output=True,
                text=True,
                timeout=1,
                check=False
            )
            
            if result_screen.returncode == 0:
                width, height = map(int, result_screen.stdout.strip().split())
                half_height = height // 2
                y_pos = half_height
                
                subprocess.run(["xdotool", "windowmove", str(window_id), "0", str(y_pos)], timeout=2, check=False)
                subprocess.run(["xdotool", "windowsize", str(window_id), str(width), str(half_height)], timeout=2, check=False)
                
                return {"success": True, "action": "snap_window_bottom", "window_id": window_id}
            else:
                return {"error": "Failed to get screen dimensions"}
        except FileNotFoundError:
            return {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to snap window bottom: {str(e)}"}
    
    def screenshot_window(hwnd: int) -> dict[str, Any]:
        """Capture screenshot of a specific window."""
        window_id = hwnd
        try:
            import base64
            from PIL import Image
            import tempfile
            
            result_geom = subprocess.run(
                ["xdotool", "getwindowgeometry", str(window_id)],
                capture_output=True,
                text=True,
                timeout=1,
                check=False
            )
            
            if result_geom.returncode != 0:
                return {"error": "Failed to get window geometry"}
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            
            result_capture = subprocess.run(
                ["import", "-window", str(window_id), tmp_path],
                timeout=5,
                check=False
            )
            
            if result_capture.returncode != 0:
                xwd_path = tmp_path.replace(".png", ".xwd")
                result_xwd = subprocess.run(
                    ["xwd", "-id", str(window_id), "-out", xwd_path],
                    timeout=5,
                    check=False
                )
                
                if result_xwd.returncode == 0:
                    subprocess.run(["convert", xwd_path, tmp_path], timeout=5, check=False)
            
            try:
                img = Image.open(tmp_path)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                img_bytes = buffer.getvalue()
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                
                return {
                    "success": True,
                    "action": "screenshot_window",
                    "window_id": window_id,
                    "format": "base64_png",
                    "data": img_base64,
                    "width": img.width,
                    "height": img.height
                }
            except Exception:
                return {"error": "Failed to process window screenshot. Install ImageMagick (import) or xwd+imagemagick (convert)"}
        except FileNotFoundError:
            return {"error": "Window screenshot tools not available", "note": "Install ImageMagick: sudo apt install imagemagick"}
        except Exception as e:
            return {"error": f"Failed to screenshot window: {str(e)}"}
    
    def list_virtual_desktops() -> dict[str, Any]:
        """List all virtual desktops (Linux workspaces)."""
        try:
            result_wmctrl = subprocess.run(
                ["wmctrl", "-d"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False
            )
            
            if result_wmctrl.returncode == 0:
                desktops = []
                lines = result_wmctrl.stdout.strip().split("\n")
                for i, line in enumerate(lines):
                    is_current = "*" in line.split()[1] if len(line.split()) > 1 else False
                    desktops.append({
                        "id": i,
                        "name": f"Desktop {i + 1}",
                        "is_current": is_current
                    })
                
                return {"success": True, "action": "list_virtual_desktops", "desktops": desktops}
            else:
                result_xdotool = subprocess.run(
                    ["xdotool", "get_num_desktops"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    check=False
                )
                
                if result_xdotool.returncode == 0:
                    count = int(result_xdotool.stdout.strip())
                    current = int(subprocess.run(["xdotool", "get_desktop"], capture_output=True, text=True).stdout.strip())
                    desktops = [{"id": i, "name": f"Desktop {i + 1}", "is_current": (i == current)} for i in range(count)]
                    return {"success": True, "action": "list_virtual_desktops", "desktops": desktops}
                else:
                    return {"error": "Virtual desktop enumeration requires wmctrl or xdotool", "note": "Install: sudo apt install wmctrl or sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to list virtual desktops: {str(e)}"}
    
    def switch_virtual_desktop(desktop_id: int | None = None, name: str | None = None) -> dict[str, Any]:
        """Switch to a virtual desktop (Linux workspaces)."""
        if desktop_id is None and name is None:
            return {"error": "Either 'desktop_id' or 'name' parameter is required"}
        
        if name and desktop_id is None:
            try:
                desktop_id = int(name.split()[-1]) - 1
            except (ValueError, IndexError):
                return {"error": f"Could not parse desktop ID from name: {name}"}
        
        try:
            result_wmctrl = subprocess.run(
                ["wmctrl", "-s", str(desktop_id)],
                timeout=2,
                check=False
            )
            
            if result_wmctrl.returncode == 0:
                return {"success": True, "action": "switch_virtual_desktop", "desktop_id": desktop_id}
            
            result_xdotool = subprocess.run(
                ["xdotool", "set_desktop", str(desktop_id)],
                timeout=2,
                check=False
            )
            
            if result_xdotool.returncode == 0:
                return {"success": True, "action": "switch_virtual_desktop", "desktop_id": desktop_id}
            else:
                return {"error": "Virtual desktop switching requires wmctrl or xdotool", "note": "Install: sudo apt install wmctrl or sudo apt install xdotool"}
        except FileNotFoundError:
            return {"error": "Virtual desktop switching requires wmctrl or xdotool", "note": "Install: sudo apt install wmctrl or sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to switch virtual desktop: {str(e)}"}
    
    def move_window_to_virtual_desktop(hwnd: int, desktop_id: int) -> dict[str, Any]:
        """Move a window to a different virtual desktop (Linux workspaces)."""
        window_id = hwnd
        try:
            result_wmctrl = subprocess.run(
                ["wmctrl", "-i", "-r", str(window_id), "-t", str(desktop_id)],
                timeout=2,
                check=False
            )
            
            if result_wmctrl.returncode == 0:
                return {"success": True, "action": "move_window_to_virtual_desktop", "window_id": window_id, "desktop_id": desktop_id}
            else:
                return {"error": "Moving windows to virtual desktops requires wmctrl", "note": "Install: sudo apt install wmctrl"}
        except FileNotFoundError:
            return {"error": "Moving windows to virtual desktops requires wmctrl", "note": "Install: sudo apt install wmctrl"}
        except Exception as e:
            return {"error": f"Failed to move window to virtual desktop: {str(e)}"}

else:
    import platform
    _platform_error = f"Unsupported platform: {platform.system()}"
    
    def list_windows() -> dict[str, Any]:
        return {"error": _platform_error}
    
    def switch_to_window(hwnd: int | None = None, title: str | None = None) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def move_window(hwnd: int, x: int, y: int, width: int | None = None, height: int | None = None) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def resize_window(hwnd: int, width: int, height: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def minimize_window(hwnd: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def maximize_window(hwnd: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def restore_window(hwnd: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def set_window_topmost(hwnd: int, topmost: bool = True) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def get_window_info(hwnd: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def close_window(hwnd: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def snap_window_left(hwnd: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def snap_window_right(hwnd: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def snap_window_top(hwnd: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def snap_window_bottom(hwnd: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def screenshot_window(hwnd: int) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def list_virtual_desktops() -> dict[str, Any]:
        return {"error": _platform_error}
    
    def switch_virtual_desktop(desktop_id: int | None = None, name: str | None = None) -> dict[str, Any]:
        return {"error": _platform_error}
    
    def move_window_to_virtual_desktop(hwnd: int, desktop_id: int) -> dict[str, Any]:
        return {"error": _platform_error}

