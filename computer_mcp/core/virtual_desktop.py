"""Windows Virtual Desktop API wrapper using VirtualDesktopAccessor.dll.

This module uses VirtualDesktopAccessor.dll from:
https://github.com/Ciantic/VirtualDesktopAccessor

The DLL is distributed with this package under the MIT License.
See: https://github.com/Ciantic/VirtualDesktopAccessor/blob/rust/LICENSE.txt
"""

import ctypes
from pathlib import Path
from typing import Optional

def _find_dll_path() -> Optional[Path]:
    """Find the VirtualDesktopAccessor.dll path, checking multiple locations."""
    # Try development path (when running from source at project root)
    dev_path = Path(__file__).parent.parent.parent / "resources" / "VirtualDesktopAccessor.dll"
    if dev_path.exists():
        return dev_path
    
    # Try development path (when running from source with DLL in package)
    dev_pkg_path = Path(__file__).parent.parent / "resources" / "VirtualDesktopAccessor.dll"
    if dev_pkg_path.exists():
        return dev_pkg_path
    
    # Try using importlib.resources (preferred for installed packages)
    try:
        import importlib.resources as pkg_resources
        # Access the DLL from package_data
        try:
            with pkg_resources.path("computer_mcp.resources", "VirtualDesktopAccessor.dll") as dll_path:
                if dll_path.exists():
                    return Path(dll_path)
        except (ModuleNotFoundError, FileNotFoundError):
            # Fallback: try to find it relative to package
            with pkg_resources.path("computer_mcp", "__init__.py") as pkg_init:
                pkg_root = pkg_init.parent
                dll_in_pkg = pkg_root / "resources" / "VirtualDesktopAccessor.dll"
                if dll_in_pkg.exists():
                    return dll_in_pkg
    except (ImportError, Exception):
        pass
    
    # Fallback: try installed package path (same directory as module)
    installed_path = Path(__file__).parent / "VirtualDesktopAccessor.dll"
    if installed_path.exists():
        return installed_path
    
    return None

# Path to the DLL - resolved at runtime
_DLL_PATH = _find_dll_path()

# Load the DLL
_vda_dll: Optional[ctypes.CDLL] = None
_dll_available = False

try:
    if _DLL_PATH.exists():
        # Try WinDLL first (stdcall) as Windows DLLs typically use this
        try:
            _vda_dll = ctypes.WinDLL(str(_DLL_PATH))
        except OSError:
            # Fall back to CDLL (cdecl) if WinDLL fails
            _vda_dll = ctypes.CDLL(str(_DLL_PATH))
        _dll_available = True
        
        # Define function signatures
        # fn GetCurrentDesktopNumber() -> i32
        _vda_dll.GetCurrentDesktopNumber.argtypes = []
        _vda_dll.GetCurrentDesktopNumber.restype = ctypes.c_int32
        
        # fn GetDesktopCount() -> i32
        _vda_dll.GetDesktopCount.argtypes = []
        _vda_dll.GetDesktopCount.restype = ctypes.c_int32
        
        # fn GoToDesktopNumber(desktop_number: i32) -> i32
        _vda_dll.GoToDesktopNumber.argtypes = [ctypes.c_int32]
        _vda_dll.GoToDesktopNumber.restype = ctypes.c_int32
        
        # fn MoveWindowToDesktopNumber(hwnd: HWND, desktop_number: i32) -> i32
        _vda_dll.MoveWindowToDesktopNumber.argtypes = [ctypes.c_void_p, ctypes.c_int32]
        _vda_dll.MoveWindowToDesktopNumber.restype = ctypes.c_int32
        
        # fn GetWindowDesktopNumber(hwnd: HWND) -> i32
        _vda_dll.GetWindowDesktopNumber.argtypes = [ctypes.c_void_p]
        _vda_dll.GetWindowDesktopNumber.restype = ctypes.c_int32
        
        # fn IsWindowOnCurrentVirtualDesktop(hwnd: HWND) -> i32
        _vda_dll.IsWindowOnCurrentVirtualDesktop.argtypes = [ctypes.c_void_p]
        _vda_dll.IsWindowOnCurrentVirtualDesktop.restype = ctypes.c_int32
        
except (OSError, AttributeError) as e:
    _dll_available = False
    _vda_dll = None


def is_available() -> bool:
    """Check if VirtualDesktopAccessor.dll is available."""
    return _dll_available


def get_current_desktop_number() -> Optional[int]:
    """Get the current virtual desktop number (0-indexed). Returns None on error."""
    if not _dll_available or not _vda_dll:
        return None
    try:
        result = _vda_dll.GetCurrentDesktopNumber()
        return result if result >= 0 else None
    except Exception:
        return None


def get_desktop_count() -> Optional[int]:
    """Get the total number of virtual desktops. Returns None on error."""
    if not _dll_available or not _vda_dll:
        return None
    try:
        result = _vda_dll.GetDesktopCount()
        return result if result > 0 else None
    except Exception:
        return None


def go_to_desktop_number(desktop_number: int) -> bool:
    """Switch to the specified virtual desktop (0-indexed). Returns True on success."""
    if not _dll_available or not _vda_dll:
        return False
    try:
        result = _vda_dll.GoToDesktopNumber(desktop_number)
        # Returns 1 on success, -1 on error (testing shows it returns 1 when successful)
        return result != -1
    except Exception as e:
        # Log the exception for debugging
        import sys
        print(f"Error calling GoToDesktopNumber: {e}", file=sys.stderr)
        return False


def move_window_to_desktop_number(hwnd: int, desktop_number: int) -> bool:
    """Move a window to the specified virtual desktop. Returns True on success."""
    if not _dll_available or not _vda_dll:
        return False
    try:
        result = _vda_dll.MoveWindowToDesktopNumber(ctypes.c_void_p(hwnd), desktop_number)
        # Returns non-negative on success, -1 on error
        return result != -1
    except Exception:
        return False


def get_window_desktop_number(hwnd: int) -> Optional[int]:
    """Get the virtual desktop number for a window (0-indexed). Returns None on error."""
    if not _dll_available or not _vda_dll:
        return None
    try:
        result = _vda_dll.GetWindowDesktopNumber(ctypes.c_void_p(hwnd))
        return result if result >= 0 else None
    except Exception:
        return None


def is_window_on_current_desktop(hwnd: int) -> Optional[bool]:
    """Check if a window is on the current virtual desktop. Returns None on error."""
    if not _dll_available or not _vda_dll:
        return None
    try:
        result = _vda_dll.IsWindowOnCurrentVirtualDesktop(ctypes.c_void_p(hwnd))
        return result == 1  # Returns 1 if on current desktop, 0 otherwise
    except Exception:
        return None

