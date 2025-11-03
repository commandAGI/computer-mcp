"""Platform detection and feature flags."""

import platform
import shutil

# Platform detection flags
IS_WINDOWS = platform.system() == "Windows"
IS_DARWIN = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Feature availability flags
IS_LINUX_ACCESSIBILITY_MODULES_SUPPORTED = False
if IS_LINUX:
    try:
        import gi  # pyright: ignore[reportMissingImports]
        gi.require_version('Atspi', '2.0')
        from gi.repository import Atspi  # noqa: F401
        IS_LINUX_ACCESSIBILITY_MODULES_SUPPORTED = True
    except (ImportError, ValueError):
        pass


def get_default_terminal_command() -> list[str]:
    """Get default terminal command for the current platform.
    
    Returns:
        List of command arguments (executable path and args)
        
    Platform defaults:
        - Windows: pwsh (PowerShell 7+) or powershell/cmd
        - Linux/macOS: /bin/bash or /bin/sh
    """
    if IS_WINDOWS:
        # Try PowerShell 7+ (pwsh) first
        if shutil.which("pwsh"):
            return ["pwsh"]
        # Fallback to Windows PowerShell
        if shutil.which("powershell"):
            return ["powershell"]
        # Last resort: cmd
        return ["cmd"]
    elif IS_LINUX or IS_DARWIN:
        # Try bash first
        if shutil.which("/bin/bash"):
            return ["/bin/bash"]
        # Fallback to sh
        return ["/bin/sh"]
    else:
        # Unknown platform, try common shells
        for shell in ["/bin/bash", "/bin/sh", "sh", "bash"]:
            if shutil.which(shell):
                return [shell]
        # Last resort
        return ["sh"]

