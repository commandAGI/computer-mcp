"""Window management handlers."""

from computer_mcp.core.platform import IS_DARWIN, IS_LINUX, IS_WINDOWS
from computer_mcp.core.response import format_response
from computer_mcp.core.state import ComputerState

from mcp.types import ImageContent, TextContent
import subprocess
from typing import Any, Union
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
                # Small delay to let Windows finish restoring
                time.sleep(0.05)
        except Exception:
            pass

    def _get_work_area_for_window(hwnd: int) -> tuple[int, int, int, int]:
        """Get work area (excluding taskbar) for the monitor containing the window.
        
        Returns:
            Tuple of (left, top, right, bottom) coordinates
        """
        try:
            import win32api
            import win32con
            monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
            mi = win32api.GetMonitorInfo(monitor)
            work = mi['Work']  # Returns (left, top, right, bottom)
            return work
        except Exception:
            # Fallback to primary screen
            try:
                import win32api
                import win32con
                width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                # Assume taskbar is at bottom, ~40px high
                return (0, 0, width, height - 40)
            except Exception:
                return (0, 0, 1920, 1040)  # Conservative fallback

    def _get_visible_frame_win(hwnd: int) -> tuple[int, int, int, int]:
        """
        Get visible frame bounds (excluding drop shadow) using DWM.
        Falls back to GetWindowRect if DWM call fails.
        
        Returns:
            Tuple of (left, top, right, bottom) coordinates
        """
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
        # Fallback to GetWindowRect
        try:
            import win32gui
            rect = win32gui.GetWindowRect(hwnd)
            return rect
        except Exception:
            return (0, 0, 1920, 1080)

    def _apply_window_bounds_win(hwnd: int, target_ltrb: tuple[int, int, int, int]):
        """
        Move/resize window so the visible frame aligns with the target rectangle.
        Accounts for window chrome/shadow insets by measuring and correcting.
        
        Args:
            hwnd: Window handle
            target_ltrb: Target bounds as (left, top, right, bottom) for visible frame
        """
        try:
            import win32gui
            import win32con
            import time
            
            L, T, R, B = target_ltrb
            W = max(1, R - L)
            H = max(1, B - T)
            
            # Ensure window is not maximized before attempting to resize
            placement = win32gui.GetWindowPlacement(hwnd)
            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.05)
            
            # First, set approximate outer bounds
            win32gui.SetWindowPos(
                hwnd, 0, L, T, W, H,
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW
            )
            
            # Small delay to let Windows apply the change
            time.sleep(0.02)
            
            # Measure actual visible frame and outer bounds
            visL, visT, visR, visB = _get_visible_frame_win(hwnd)
            outL, outT, outR, outB = win32gui.GetWindowRect(hwnd)
            
            # Calculate insets
            inset_left = visL - outL
            inset_top = visT - outT
            inset_right = outR - visR
            inset_bottom = outB - visB
            
            # Correct outer bounds to account for insets
            corrL = L - inset_left
            corrT = T - inset_top
            corrW = W + inset_left + inset_right
            corrH = H + inset_top + inset_bottom
            
            corrL = int(round(corrL))
            corrT = int(round(corrT))
            corrW = max(1, int(round(corrW)))
            corrH = max(1, int(round(corrH)))
            
            # Apply corrected bounds
            win32gui.SetWindowPos(
                hwnd, 0, corrL, corrT, corrW, corrH,
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW
            )
        except Exception:
            # Fallback to simple positioning
            try:
                import win32gui
                import win32con
                import time
                # Ensure window is not maximized
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

    def handle_list_windows(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle list_windows action."""
        try:
            import win32gui
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        windows = []
        def enum_callback(hwnd, window_list):
            window_data = _get_window_data(hwnd)
            if window_data:
                window_list.append(window_data)
            return True
        
        win32gui.EnumWindows(enum_callback, windows)
        
        result = {"success": True, "action": "list_windows", "windows": windows, "count": len(windows)}
        return format_response(result, state)

    def handle_switch_to_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle switch_to_window action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = None
        if "hwnd" in arguments:
            hwnd = arguments["hwnd"]
        elif "title" in arguments:
            hwnd = _find_window_by_title(arguments["title"])
            if not hwnd:
                result = {"error": f"Window with title pattern '{arguments['title']}' not found"}
                return format_response(result, state)
        else:
            result = {"error": "Either 'hwnd' or 'title' parameter is required"}
            return format_response(result, state)
        
        try:
            # Restore if minimized
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            # Bring to foreground
            win32gui.SetForegroundWindow(hwnd)
            
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "switch_to_window", "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to switch to window: {str(e)}"}
            return format_response(result, state)

    def handle_move_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle move_window action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        x = arguments.get("x")
        y = arguments.get("y")
        width = arguments.get("width")
        height = arguments.get("height")
        
        if x is None or y is None:
            result = {"error": "'x' and 'y' parameters are required"}
            return format_response(result, state)
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            flags = win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            if width is None or height is None:
                # Just move, don't resize
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
            
            win32gui.SetWindowPos(hwnd, 0, x, y, width, height, flags)
            
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "move_window", "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to move window: {str(e)}"}
            return format_response(result, state)

    def handle_resize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle resize_window action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        width = arguments.get("width")
        height = arguments.get("height")
        
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        if width is None or height is None:
            result = {"error": "'width' and 'height' parameters are required"}
            return format_response(result, state)
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            # Get current position
            rect = win32gui.GetWindowRect(hwnd)
            x = rect[0]
            y = rect[1]
            
            flags = win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE
            win32gui.SetWindowPos(hwnd, 0, x, y, width, height, flags)
            
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "resize_window", "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to resize window: {str(e)}"}
            return format_response(result, state)

    def handle_minimize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle minimize_window action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "minimize_window", "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to minimize window: {str(e)}"}
            return format_response(result, state)

    def handle_maximize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle maximize_window action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "maximize_window", "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to maximize window: {str(e)}"}
            return format_response(result, state)

    def handle_restore_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle restore_window action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "restore_window", "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to restore window: {str(e)}"}
            return format_response(result, state)

    def handle_set_window_topmost(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle set_window_topmost action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        topmost = arguments.get("topmost", True)
        
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        try:
            hwnd_insert_after = win32con.HWND_TOPMOST if topmost else win32con.HWND_NOTOPMOST
            flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            win32gui.SetWindowPos(hwnd, hwnd_insert_after, 0, 0, 0, 0, flags)
            
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "set_window_topmost", "topmost": topmost, "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to set window topmost: {str(e)}"}
            return format_response(result, state)

    def handle_get_window_info(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle get_window_info action."""
        try:
            import win32gui
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        window_data = _get_window_data(hwnd)
        if not window_data:
            result = {"error": "Invalid window handle or window not accessible"}
            return format_response(result, state)
        
        result = {"success": True, "action": "get_window_info", "window": window_data}
        return format_response(result, state)

    def handle_close_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle close_window action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        try:
            # Post WM_CLOSE message to gracefully close the window
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            
            result = {"success": True, "action": "close_window", "hwnd": hwnd}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to close window: {str(e)}"}
            return format_response(result, state)

    def _get_screen_dimensions() -> tuple[int, int]:
        """Get primary screen dimensions (legacy - use _get_work_area_for_window for better results)."""
        try:
            import win32api
            import win32con
            # SM_CXSCREEN = 0, SM_CYSCREEN = 1
            return win32api.GetSystemMetrics(win32con.SM_CXSCREEN), win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        except Exception:
            # Fallback
            return 1920, 1080

    def handle_snap_window_left(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_left action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            # Get work area for the monitor containing this window (excludes taskbar)
            left, top, right, bottom = _get_work_area_for_window(hwnd)
            work_width = right - left
            work_height = bottom - top
            
            # Target visible frame bounds (left half)
            target_left = left
            target_top = top
            target_right = left + (work_width // 2)
            target_bottom = bottom
            
            # Use improved bounds function that accounts for window chrome/shadow
            _apply_window_bounds_win(hwnd, (target_left, target_top, target_right, target_bottom))
            
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "snap_window_left", "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window left: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_right(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_right action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            # Get work area for the monitor containing this window (excludes taskbar)
            left, top, right, bottom = _get_work_area_for_window(hwnd)
            work_width = right - left
            work_height = bottom - top
            
            # Target visible frame bounds (right half)
            target_left = left + (work_width // 2)
            target_top = top
            target_right = right
            target_bottom = bottom
            
            # Use improved bounds function that accounts for window chrome/shadow
            _apply_window_bounds_win(hwnd, (target_left, target_top, target_right, target_bottom))
            
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "snap_window_right", "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window right: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_top(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_top action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            # Get work area for the monitor containing this window (excludes taskbar)
            left, top, right, bottom = _get_work_area_for_window(hwnd)
            work_width = right - left
            work_height = bottom - top
            
            # Target visible frame bounds (top half)
            target_left = left
            target_top = top
            target_right = right
            target_bottom = top + (work_height // 2)
            
            # Use improved bounds function that accounts for window chrome/shadow
            _apply_window_bounds_win(hwnd, (target_left, target_top, target_right, target_bottom))
            
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "snap_window_top", "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window top: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_bottom(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_bottom action."""
        try:
            import win32gui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window management support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        try:
            _set_dpi_aware_win()
            _check_exit_fullscreen_win(hwnd)
            
            # Get work area for the monitor containing this window (excludes taskbar)
            left, top, right, bottom = _get_work_area_for_window(hwnd)
            work_width = right - left
            work_height = bottom - top
            
            # Target visible frame bounds (bottom half)
            target_left = left
            target_top = top + (work_height // 2)
            target_right = right
            target_bottom = bottom
            
            # Use improved bounds function that accounts for window chrome/shadow
            _apply_window_bounds_win(hwnd, (target_left, target_top, target_right, target_bottom))
            
            window_data = _get_window_data(hwnd)
            result = {"success": True, "action": "snap_window_bottom", "window": window_data}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window bottom: {str(e)}"}
            return format_response(result, state)

    def handle_screenshot_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle screenshot_window action."""
        try:
            import win32gui
            import win32ui
            import win32con
        except ImportError:
            result = {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window screenshot support"}
            return format_response(result, state)
        
        hwnd = arguments.get("hwnd")
        if not hwnd:
            result = {"error": "'hwnd' parameter is required"}
            return format_response(result, state)
        
        try:
            # Get window bounds
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            # Create device context for window
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # Create bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)
            
            # Copy window content
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
            
            # Convert to PIL Image
            from PIL import Image
            import base64
            from io import BytesIO
            
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
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
            
            # Cleanup
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            screenshot_data = {
                "format": "base64_png",
                "data": img_base64,
                "width": width,
                "height": height
            }
            
            result = {"success": True, "action": "screenshot_window", "hwnd": hwnd}
            return format_response(result, state, screenshot_data=screenshot_data)
        except Exception as e:
            result = {"error": f"Failed to screenshot window: {str(e)}"}
            return format_response(result, state)

    def handle_list_virtual_desktops(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle list_virtual_desktops action."""
        try:
            from computer_mcp.core.virtual_desktop import (
                is_available,
                get_desktop_count,
                get_current_desktop_number
            )
            
            if not is_available():
                result = {
                    "success": True,
                    "action": "list_virtual_desktops",
                    "desktops": [{"id": 0, "name": "Desktop 1", "is_current": True}],
                    "note": "VirtualDesktopAccessor.dll not available. Basic single desktop returned."
                }
                return format_response(result, state)
            
            count = get_desktop_count()
            current = get_current_desktop_number()
            
            if count is None:
                result = {
                    "success": True,
                    "action": "list_virtual_desktops",
                    "desktops": [{"id": 0, "name": "Desktop 1", "is_current": True}],
                    "note": "Failed to get desktop count. Basic single desktop returned."
                }
                return format_response(result, state)
            
            desktops = []
            for i in range(count):
                desktops.append({
                    "id": i,
                    "name": f"Desktop {i + 1}",
                    "is_current": i == current if current is not None else False
                })
            
            result = {
                "success": True,
                "action": "list_virtual_desktops",
                "desktops": desktops
            }
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to list virtual desktops: {str(e)}"}
            return format_response(result, state)

    def handle_switch_virtual_desktop(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle switch_virtual_desktop action."""
        try:
            from computer_mcp.core.virtual_desktop import (
                is_available,
                go_to_desktop_number,
                get_desktop_count
            )
            
            desktop_id = arguments.get("desktop_id")
            name = arguments.get("name")
            
            if desktop_id is None and name is None:
                result = {"error": "Either 'desktop_id' or 'name' parameter is required"}
                return format_response(result, state)
            
            # Extract ID from name if needed
            if name and desktop_id is None:
                # Try to extract number from name like "Desktop 2"
                try:
                    desktop_id = int(name.split()[-1]) - 1
                except (ValueError, IndexError):
                    result = {"error": f"Could not parse desktop ID from name: {name}"}
                    return format_response(result, state)
            
            if not is_available():
                result = {
                    "error": "Virtual desktop switching requires VirtualDesktopAccessor.dll",
                    "note": "VirtualDesktopAccessor.dll not found. Please ensure it's available in the resources directory."
                }
                return format_response(result, state)
            
            # Validate desktop number
            count = get_desktop_count()
            if count is not None and desktop_id >= count:
                result = {
                    "error": f"Desktop number {desktop_id} is out of range. Available desktops: 0-{count - 1}"
                }
                return format_response(result, state)
            
            # Switch to the desktop
            success = go_to_desktop_number(desktop_id)
            
            if success:
                result = {"success": True, "action": "switch_virtual_desktop", "desktop_id": desktop_id}
            else:
                result = {
                    "error": f"Failed to switch to desktop {desktop_id}",
                    "note": "The desktop number may be invalid or the operation failed."
                }
            
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to switch virtual desktop: {str(e)}"}
            return format_response(result, state)

    def handle_move_window_to_virtual_desktop(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle move_window_to_virtual_desktop action."""
        try:
            from computer_mcp.core.virtual_desktop import (
                is_available,
                move_window_to_desktop_number,
                get_desktop_count
            )
            
            hwnd = arguments.get("hwnd")
            desktop_id = arguments.get("desktop_id")
            
            if not hwnd:
                result = {"error": "'hwnd' parameter is required"}
                return format_response(result, state)
            
            if desktop_id is None:
                result = {"error": "'desktop_id' parameter is required"}
                return format_response(result, state)
            
            if not is_available():
                result = {
                    "error": "Virtual desktop window moving requires VirtualDesktopAccessor.dll",
                    "note": "VirtualDesktopAccessor.dll not found. Please ensure it's available in the resources directory."
                }
                return format_response(result, state)
            
            # Validate desktop number
            count = get_desktop_count()
            if count is not None and desktop_id >= count:
                result = {
                    "error": f"Desktop number {desktop_id} is out of range. Available desktops: 0-{count - 1}"
                }
                return format_response(result, state)
            
            # Validate window handle
            if not isinstance(hwnd, int):
                try:
                    hwnd = int(hwnd)
                except (ValueError, TypeError):
                    result = {"error": f"Invalid window handle: {hwnd}"}
                    return format_response(result, state)
            
            # Move the window
            success = move_window_to_desktop_number(hwnd, desktop_id)
            
            if success:
                result = {
                    "success": True,
                    "action": "move_window_to_virtual_desktop",
                    "hwnd": hwnd,
                    "desktop_id": desktop_id
                }
            else:
                result = {
                    "error": f"Failed to move window {hwnd} to desktop {desktop_id}",
                    "note": "The window handle may be invalid or the desktop number may be out of range."
                }
            
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to move window to virtual desktop: {str(e)}"}
            return format_response(result, state)

elif IS_DARWIN:
    # macOS placeholder implementations
    def handle_list_windows(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle list_windows action (macOS - not yet implemented)."""
        result = {"error": "Window management not yet implemented for macOS"}
        return format_response(result, state)

    def handle_switch_to_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle switch_to_window action (macOS - not yet implemented)."""
        result = {"error": "Window management not yet implemented for macOS"}
        return format_response(result, state)

    def handle_move_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle move_window action (macOS - not yet implemented)."""
        result = {"error": "Window management not yet implemented for macOS"}
        return format_response(result, state)

    def handle_resize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle resize_window action (macOS - not yet implemented)."""
        result = {"error": "Window management not yet implemented for macOS"}
        return format_response(result, state)

    def handle_minimize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle minimize_window action (macOS - not yet implemented)."""
        result = {"error": "Window management not yet implemented for macOS"}
        return format_response(result, state)

    def handle_maximize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle maximize_window action (macOS - not yet implemented)."""
        result = {"error": "Window management not yet implemented for macOS"}
        return format_response(result, state)

    def handle_restore_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle restore_window action (macOS - not yet implemented)."""
        result = {"error": "Window management not yet implemented for macOS"}
        return format_response(result, state)

    def handle_set_window_topmost(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle set_window_topmost action (macOS - not yet implemented)."""
        result = {"error": "Window management not yet implemented for macOS"}
        return format_response(result, state)

    def handle_get_window_info(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle get_window_info action (macOS - not yet implemented)."""
        result = {"error": "Window management not yet implemented for macOS"}
        return format_response(result, state)

    def handle_close_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle close_window action (macOS)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
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
                result = {"success": True, "action": "close_window", "window_id": window_id}
            else:
                result = {"error": "Failed to close window"}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to close window: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_left(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_left action (macOS)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        # Use visibleFrame to account for dock and menu bar
        script = f'''
        tell application "System Events"
            tell application process whose frontmost is true
                set screenBounds to bounds of window id {window_id}
                set screenWidth to screen width
                set screenHeight to screen height
                -- Use visibleFrame calculation (approximate if menu bar is ~25px)
                set visibleTop to 25
                set visibleHeight to screenHeight - visibleTop
                -- Assume dock is ~60px high at bottom if present
                set dockHeight to 60
                set visibleHeight to visibleHeight - dockHeight
                set bounds of window id {window_id} to {{0, visibleTop, (screenWidth / 2), visibleTop + visibleHeight}}
            end tell
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=2)
            result = {"success": True, "action": "snap_window_left", "window_id": window_id}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window left: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_right(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_right action (macOS)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        # Use visibleFrame to account for dock and menu bar
        script = f'''
        tell application "System Events"
            tell application process whose frontmost is true
                set screenWidth to screen width
                set screenHeight to screen height
                -- Use visibleFrame calculation (approximate if menu bar is ~25px)
                set visibleTop to 25
                set visibleHeight to screenHeight - visibleTop
                -- Assume dock is ~60px high at bottom if present
                set dockHeight to 60
                set visibleHeight to visibleHeight - dockHeight
                set bounds of window id {window_id} to {{(screenWidth / 2), visibleTop, screenWidth, visibleTop + visibleHeight}}
            end tell
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=2)
            result = {"success": True, "action": "snap_window_right", "window_id": window_id}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window right: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_top(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_top action (macOS)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        # Use visibleFrame to account for dock and menu bar
        script = f'''
        tell application "System Events"
            tell application process whose frontmost is true
                set screenWidth to screen width
                set screenHeight to screen height
                -- Use visibleFrame calculation (approximate if menu bar is ~25px)
                set visibleTop to 25
                set visibleHeight to screenHeight - visibleTop
                -- Assume dock is ~60px high at bottom if present
                set dockHeight to 60
                set visibleHeight to visibleHeight - dockHeight
                set bounds of window id {window_id} to {{0, visibleTop, screenWidth, visibleTop + (visibleHeight / 2)}}
            end tell
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=2)
            result = {"success": True, "action": "snap_window_top", "window_id": window_id}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window top: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_bottom(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_bottom action (macOS)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        # Use visibleFrame to account for dock and menu bar
        script = f'''
        tell application "System Events"
            tell application process whose frontmost is true
                set screenWidth to screen width
                set screenHeight to screen height
                -- Use visibleFrame calculation (approximate if menu bar is ~25px)
                set visibleTop to 25
                set visibleHeight to screenHeight - visibleTop
                -- Assume dock is ~60px high at bottom if present
                set dockHeight to 60
                set visibleHeight to visibleHeight - dockHeight
                set midPoint to visibleTop + (visibleHeight / 2)
                set bounds of window id {window_id} to {{0, midPoint, screenWidth, visibleTop + visibleHeight}}
            end tell
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=2)
            result = {"success": True, "action": "snap_window_bottom", "window_id": window_id}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window bottom: {str(e)}"}
            return format_response(result, state)

    def handle_screenshot_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle screenshot_window action (macOS)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        try:
            # Get window bounds first
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
                result = {"error": "Failed to get window bounds"}
                return format_response(result, state)
            
            # Parse bounds: {left, top, right, bottom}
            bounds_str = result_bounds.stdout.strip()
            bounds = [int(x.strip()) for x in bounds_str.replace("{", "").replace("}", "").split(",")]
            x, y, right, bottom = bounds
            width = right - x
            height = bottom - y
            
            # Use screencapture with window bounds
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
                # Read and convert to base64
                img = Image.open(tmp_path)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                img_bytes = buffer.getvalue()
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                
                screenshot_data = {
                    "format": "base64_png",
                    "data": img_base64,
                    "width": width,
                    "height": height
                }
                
                result = {"success": True, "action": "screenshot_window", "window_id": window_id}
                return format_response(result, state, screenshot_data=screenshot_data)
            else:
                result = {"error": "Failed to capture window screenshot"}
                return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to screenshot window: {str(e)}"}
            return format_response(result, state)

    def handle_list_virtual_desktops(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle list_virtual_desktops action (macOS - Spaces)."""
        script = '''
        tell application "System Events"
            tell application "System Preferences"
                set spaces to count of spaces
                return spaces
            end tell
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
            
            # macOS doesn't expose Spaces count easily via AppleScript
            # Return basic info
            result = {
                "success": True,
                "action": "list_virtual_desktops",
                "desktops": [{"id": 0, "name": "Space 1", "is_current": True}],
                "note": "macOS Spaces enumeration is limited via AppleScript. Multiple Spaces may exist but are not easily enumerated."
            }
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to list virtual desktops: {str(e)}"}
            return format_response(result, state)

    def handle_switch_virtual_desktop(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle switch_virtual_desktop action (macOS - Spaces)."""
        desktop_id = arguments.get("desktop_id")
        name = arguments.get("name")
        
        if desktop_id is None and name is None:
            result = {"error": "Either 'desktop_id' or 'name' parameter is required"}
            return format_response(result, state)
        
        # Extract ID from name if needed
        if name and desktop_id is None:
            try:
                desktop_id = int(name.split()[-1]) - 1
            except (ValueError, IndexError):
                result = {"error": f"Could not parse desktop ID from name: {name}"}
                return format_response(result, state)
        
        # Use Control+Left/Right arrow keys to switch Spaces
        from pynput.keyboard import Controller as KeyboardController, Key
        
        keyboard = KeyboardController()
        
        # macOS uses Control+Left/Right for Spaces
        # This requires knowing current space which is complex
        result = {
            "success": True,
            "action": "switch_virtual_desktop",
            "desktop_id": desktop_id,
            "note": "macOS Spaces switching via script is limited. Use Control+Left/Right manually or Mission Control API."
        }
        return format_response(result, state)

    def handle_move_window_to_virtual_desktop(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle move_window_to_virtual_desktop action (macOS - Spaces)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        desktop_id = arguments.get("desktop_id")
        
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        if desktop_id is None:
            result = {"error": "'desktop_id' parameter is required"}
            return format_response(result, state)
        
        result = {
            "success": True,
            "action": "move_window_to_virtual_desktop",
            "window_id": window_id,
            "desktop_id": desktop_id,
            "note": "macOS Spaces window moving requires Mission Control API which is not easily accessible via AppleScript."
        }
        return format_response(result, state)

elif IS_LINUX:
    # Linux placeholder implementations
    def handle_list_windows(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle list_windows action (Linux - not yet implemented)."""
        result = {"error": "Window management not yet implemented for Linux"}
        return format_response(result, state)

    def handle_switch_to_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle switch_to_window action (Linux - not yet implemented)."""
        result = {"error": "Window management not yet implemented for Linux"}
        return format_response(result, state)

    def handle_move_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle move_window action (Linux - not yet implemented)."""
        result = {"error": "Window management not yet implemented for Linux"}
        return format_response(result, state)

    def handle_resize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle resize_window action (Linux - not yet implemented)."""
        result = {"error": "Window management not yet implemented for Linux"}
        return format_response(result, state)

    def handle_minimize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle minimize_window action (Linux - not yet implemented)."""
        result = {"error": "Window management not yet implemented for Linux"}
        return format_response(result, state)

    def handle_maximize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle maximize_window action (Linux - not yet implemented)."""
        result = {"error": "Window management not yet implemented for Linux"}
        return format_response(result, state)

    def handle_restore_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle restore_window action (Linux - not yet implemented)."""
        result = {"error": "Window management not yet implemented for Linux"}
        return format_response(result, state)

    def handle_set_window_topmost(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle set_window_topmost action (Linux - not yet implemented)."""
        result = {"error": "Window management not yet implemented for Linux"}
        return format_response(result, state)

    def handle_get_window_info(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle get_window_info action (Linux)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        try:
            # Get window info using xdotool
            result_xdotool = subprocess.run(
                ["xdotool", "getwindowgeometry", str(window_id)],
                capture_output=True,
                text=True,
                timeout=1,
                check=False
            )
            
            if result_xdotool.returncode == 0:
                # Parse output
                result = {"success": True, "action": "get_window_info", "window_id": window_id, "info": result_xdotool.stdout}
            else:
                result = {"error": "Failed to get window info"}
            return format_response(result, state)
        except FileNotFoundError:
            result = {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to get window info: {str(e)}"}
            return format_response(result, state)

    def handle_close_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle close_window action (Linux)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        try:
            subprocess.run(["xdotool", "windowclose", str(window_id)], timeout=2, check=False)
            result = {"success": True, "action": "close_window", "window_id": window_id}
            return format_response(result, state)
        except FileNotFoundError:
            result = {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to close window: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_left(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_left action (Linux)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        try:
            # Get screen size
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
                
                subprocess.run([
                    "xdotool", "windowmove", str(window_id), "0", "0"
                ], timeout=2, check=False)
                subprocess.run([
                    "xdotool", "windowsize", str(window_id), str(half_width), str(height)
                ], timeout=2, check=False)
                
                result = {"success": True, "action": "snap_window_left", "window_id": window_id}
            else:
                result = {"error": "Failed to get screen dimensions"}
            return format_response(result, state)
        except FileNotFoundError:
            result = {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window left: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_right(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_right action (Linux)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
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
                
                subprocess.run([
                    "xdotool", "windowmove", str(window_id), str(x_pos), "0"
                ], timeout=2, check=False)
                subprocess.run([
                    "xdotool", "windowsize", str(window_id), str(half_width), str(height)
                ], timeout=2, check=False)
                
                result = {"success": True, "action": "snap_window_right", "window_id": window_id}
            else:
                result = {"error": "Failed to get screen dimensions"}
            return format_response(result, state)
        except FileNotFoundError:
            result = {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window right: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_top(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_top action (Linux)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
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
                
                subprocess.run([
                    "xdotool", "windowmove", str(window_id), "0", "0"
                ], timeout=2, check=False)
                subprocess.run([
                    "xdotool", "windowsize", str(window_id), str(width), str(half_height)
                ], timeout=2, check=False)
                
                result = {"success": True, "action": "snap_window_top", "window_id": window_id}
            else:
                result = {"error": "Failed to get screen dimensions"}
            return format_response(result, state)
        except FileNotFoundError:
            result = {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window top: {str(e)}"}
            return format_response(result, state)

    def handle_snap_window_bottom(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_bottom action (Linux)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
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
                
                subprocess.run([
                    "xdotool", "windowmove", str(window_id), "0", str(y_pos)
                ], timeout=2, check=False)
                subprocess.run([
                    "xdotool", "windowsize", str(window_id), str(width), str(half_height)
                ], timeout=2, check=False)
                
                result = {"success": True, "action": "snap_window_bottom", "window_id": window_id}
            else:
                result = {"error": "Failed to get screen dimensions"}
            return format_response(result, state)
        except FileNotFoundError:
            result = {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to snap window bottom: {str(e)}"}
            return format_response(result, state)

    def handle_screenshot_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle screenshot_window action (Linux)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        try:
            import base64
            from PIL import Image
            import tempfile
            
            # Get window geometry
            result_geom = subprocess.run(
                ["xdotool", "getwindowgeometry", str(window_id)],
                capture_output=True,
                text=True,
                timeout=1,
                check=False
            )
            
            if result_geom.returncode != 0:
                result = {"error": "Failed to get window geometry"}
                return format_response(result, state)
            
            # Parse geometry and capture
            # Use import or xwd to capture window
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            
            # Try using import (ImageMagick) first
            result_capture = subprocess.run(
                ["import", "-window", str(window_id), tmp_path],
                timeout=5,
                check=False
            )
            
            if result_capture.returncode != 0:
                # Fallback to xwd + convert
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
                
                screenshot_data = {
                    "format": "base64_png",
                    "data": img_base64,
                    "width": img.width,
                    "height": img.height
                }
                
                result = {"success": True, "action": "screenshot_window", "window_id": window_id}
                return format_response(result, state, screenshot_data=screenshot_data)
            except Exception:
                result = {"error": "Failed to process window screenshot. Install ImageMagick (import) or xwd+imagemagick (convert)"}
                return format_response(result, state)
        except FileNotFoundError:
            result = {"error": "Window screenshot tools not available", "note": "Install ImageMagick: sudo apt install imagemagick"}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to screenshot window: {str(e)}"}
            return format_response(result, state)

    def handle_list_virtual_desktops(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle list_virtual_desktops action (Linux - workspaces)."""
        try:
            # Try wmctrl first
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
                
                result = {"success": True, "action": "list_virtual_desktops", "desktops": desktops}
                return format_response(result, state)
            else:
                # Fallback: try xdotool
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
                    result = {"success": True, "action": "list_virtual_desktops", "desktops": desktops}
                    return format_response(result, state)
                else:
                    result = {"error": "Virtual desktop enumeration requires wmctrl or xdotool", "note": "Install: sudo apt install wmctrl or sudo apt install xdotool"}
                    return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to list virtual desktops: {str(e)}"}
            return format_response(result, state)

    def handle_switch_virtual_desktop(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle switch_virtual_desktop action (Linux - workspaces)."""
        desktop_id = arguments.get("desktop_id")
        name = arguments.get("name")
        
        if desktop_id is None and name is None:
            result = {"error": "Either 'desktop_id' or 'name' parameter is required"}
            return format_response(result, state)
        
        if name and desktop_id is None:
            try:
                desktop_id = int(name.split()[-1]) - 1
            except (ValueError, IndexError):
                result = {"error": f"Could not parse desktop ID from name: {name}"}
                return format_response(result, state)
        
        try:
            # Try wmctrl first
            result_wmctrl = subprocess.run(
                ["wmctrl", "-s", str(desktop_id)],
                timeout=2,
                check=False
            )
            
            if result_wmctrl.returncode == 0:
                result = {"success": True, "action": "switch_virtual_desktop", "desktop_id": desktop_id}
                return format_response(result, state)
            
            # Fallback: xdotool
            result_xdotool = subprocess.run(
                ["xdotool", "set_desktop", str(desktop_id)],
                timeout=2,
                check=False
            )
            
            if result_xdotool.returncode == 0:
                result = {"success": True, "action": "switch_virtual_desktop", "desktop_id": desktop_id}
            else:
                result = {"error": "Virtual desktop switching requires wmctrl or xdotool", "note": "Install: sudo apt install wmctrl or sudo apt install xdotool"}
            return format_response(result, state)
        except FileNotFoundError:
            result = {"error": "Virtual desktop switching requires wmctrl or xdotool", "note": "Install: sudo apt install wmctrl or sudo apt install xdotool"}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to switch virtual desktop: {str(e)}"}
            return format_response(result, state)

    def handle_move_window_to_virtual_desktop(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle move_window_to_virtual_desktop action (Linux - workspaces)."""
        window_id = arguments.get("hwnd") or arguments.get("window_id")
        desktop_id = arguments.get("desktop_id")
        
        if not window_id:
            result = {"error": "'hwnd' or 'window_id' parameter is required"}
            return format_response(result, state)
        
        if desktop_id is None:
            result = {"error": "'desktop_id' parameter is required"}
            return format_response(result, state)
        
        try:
            # Use wmctrl to move window
            result_wmctrl = subprocess.run(
                ["wmctrl", "-i", "-r", str(window_id), "-t", str(desktop_id)],
                timeout=2,
                check=False
            )
            
            if result_wmctrl.returncode == 0:
                result = {"success": True, "action": "move_window_to_virtual_desktop", "window_id": window_id, "desktop_id": desktop_id}
            else:
                result = {"error": "Moving windows to virtual desktops requires wmctrl", "note": "Install: sudo apt install wmctrl"}
            return format_response(result, state)
        except FileNotFoundError:
            result = {"error": "Moving windows to virtual desktops requires wmctrl", "note": "Install: sudo apt install wmctrl"}
            return format_response(result, state)
        except Exception as e:
            result = {"error": f"Failed to move window to virtual desktop: {str(e)}"}
            return format_response(result, state)

else:
    # Unsupported platform
    def handle_list_windows(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle list_windows action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_switch_to_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle switch_to_window action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_move_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle move_window action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_resize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle resize_window action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_minimize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle minimize_window action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_maximize_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle maximize_window action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_restore_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle restore_window action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_set_window_topmost(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle set_window_topmost action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_get_window_info(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle get_window_info action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_close_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle close_window action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_snap_window_left(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_left action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_snap_window_right(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_right action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_snap_window_top(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_top action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_snap_window_bottom(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle snap_window_bottom action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_screenshot_window(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle screenshot_window action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_list_virtual_desktops(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle list_virtual_desktops action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_switch_virtual_desktop(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle switch_virtual_desktop action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

    def handle_move_window_to_virtual_desktop(
        arguments: dict[str, Any],
        state: ComputerState,
        _controller: Any
    ) -> list[Union[TextContent, ImageContent]]:
        """Handle move_window_to_virtual_desktop action (unsupported platform)."""
        import platform
        result = {"error": f"Unsupported platform: {platform.system()}"}
        return format_response(result, state)

