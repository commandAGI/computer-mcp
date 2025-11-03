"""Configuration actions."""

from typing import Any


def set_config(
    observe_screen: bool | None = None,
    observe_mouse_position: bool | None = None,
    observe_mouse_button_states: bool | None = None,
    observe_keyboard_key_states: bool | None = None,
    observe_focused_app: bool | None = None,
    observe_accessibility_tree: bool | None = None,
    config_dict: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Update configuration settings.
    
    Args:
        observe_screen: Include screenshots in responses
        observe_mouse_position: Track and include mouse position
        observe_mouse_button_states: Track and include mouse button states
        observe_keyboard_key_states: Track and include keyboard key states
        observe_focused_app: Include focused application information
        observe_accessibility_tree: Include accessibility tree
        config_dict: Optional dictionary to update config from
    
    Returns:
        Dictionary with updated configuration
    """
    config = {
        "observe_screen": observe_screen,
        "observe_mouse_position": observe_mouse_position,
        "observe_mouse_button_states": observe_mouse_button_states,
        "observe_keyboard_key_states": observe_keyboard_key_states,
        "observe_focused_app": observe_focused_app,
        "observe_accessibility_tree": observe_accessibility_tree,
    }
    
    # Remove None values
    config = {k: v for k, v in config.items() if v is not None}
    
    # Merge with config_dict if provided
    if config_dict:
        config.update(config_dict)
    
    return {
        "success": True,
        "action": "set_config",
        "config": config
    }

