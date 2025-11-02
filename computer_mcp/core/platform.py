"""Platform detection and feature flags."""

import platform

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

