"""Computer state tracking and management."""

from typing import Any, Optional

from pynput import keyboard, mouse
from pynput.keyboard import Controller as KeyboardController, Key, KeyCode
from pynput.mouse import Button, Controller as MouseController

from computer_mcp.core.screenshot import capture_screenshot


class ComputerState:
    """Manages computer state tracking."""
    
    def __init__(self):
        self.config = {
            "observe_screen": True,  # Default true
            "observe_mouse_position": False,
            "observe_mouse_button_states": False,
            "observe_keyboard_key_states": False,
            "observe_focused_app": False,
            "observe_accessibility_tree": False,
        }
        self.mouse_position = (0, 0)
        self.mouse_buttons = set()
        self.keyboard_keys = set()
        self.mouse_listener: Optional[mouse.Listener] = None
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()
        
    def start_mouse_listener(self):
        """Start mouse state tracking."""
        if self.mouse_listener is None and (self.config["observe_mouse_position"] or self.config["observe_mouse_button_states"]):
            self.mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self.mouse_listener.start()
    
    def stop_mouse_listener(self):
        """Stop mouse state tracking."""
        if self.mouse_listener is not None:
            self.mouse_listener.stop()
            self.mouse_listener = None
    
    def start_keyboard_listener(self):
        """Start keyboard state tracking."""
        if self.keyboard_listener is None and self.config["observe_keyboard_key_states"]:
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.keyboard_listener.start()
    
    def stop_keyboard_listener(self):
        """Stop keyboard state tracking."""
        if self.keyboard_listener is not None:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
    def _on_mouse_move(self, x: int, y: int):
        if self.config["observe_mouse_position"]:
            self.mouse_position = (x, y)
    
    def _on_mouse_click(self, x: int, y: int, button: Button, pressed: bool):
        if self.config["observe_mouse_position"]:
            self.mouse_position = (x, y)
        if self.config["observe_mouse_button_states"]:
            if pressed:
                self.mouse_buttons.add(button)
            else:
                self.mouse_buttons.discard(button)
    
    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int):  # noqa: ARG002
        if self.config["observe_mouse_position"]:
            self.mouse_position = (x, y)
    
    def _on_key_press(self, key):
        self.keyboard_keys.add(key)
    
    def _on_key_release(self, key):
        self.keyboard_keys.discard(key)
    
    def get_state(self, include_screenshot: bool = True) -> dict[str, Any]:
        """Get current state based on configuration."""
        state = {}
        
        # Screenshot (default true)
        if include_screenshot and self.config["observe_screen"]:
            try:
                state["screenshot"] = capture_screenshot()
            except Exception as e:
                state["screenshot"] = {"error": str(e)}
        
        # Mouse position
        if self.config["observe_mouse_position"]:
            current_pos = self.mouse_controller.position
            state["mouse_position"] = {"x": int(current_pos[0]), "y": int(current_pos[1])}
        
        # Mouse button states
        if self.config["observe_mouse_button_states"]:
            state["mouse_button_states"] = [str(btn) for btn in self.mouse_buttons]
        
        # Keyboard key states
        if self.config["observe_keyboard_key_states"]:
            state["keyboard_key_states"] = [self._format_key(key) for key in self.keyboard_keys]
        
        # Focused app
        if self.config["observe_focused_app"]:
            from platforms import get_focused_app as get_focused_app_impl
            state["focused_app"] = get_focused_app_impl()
        
        # Accessibility tree
        if self.config["observe_accessibility_tree"]:
            from platforms import get_accessibility_tree as get_accessibility_tree_impl
            state["accessibility_tree"] = get_accessibility_tree_impl()
        
        return state
    
    def _format_key(self, key) -> str:
        """Format key for display."""
        if isinstance(key, Key):
            return key.name if hasattr(key, 'name') else str(key)
        elif isinstance(key, KeyCode):
            return key.char if key.char else f"<{key.vk}>"
        return str(key)

