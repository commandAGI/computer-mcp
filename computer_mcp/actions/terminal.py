"""Terminal management actions."""

import asyncio
import atexit
import signal
from typing import Any, Optional

from computer_mcp.core.utils import key_from_string


# Global terminal registry: PID -> Terminal
_terminals: dict[int, "Terminal"] = {}


class Terminal:
    """Represents a managed terminal process."""
    
    def __init__(self, pid: int, process: asyncio.subprocess.Process):
        self.pid = pid
        self.process = process
        self.stdout_buffer = asyncio.Queue()
        self.stderr_buffer = asyncio.Queue()
        self._stdout_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._closed = False
        
        # Start background tasks to read stdout/stderr
        self._stdout_task = asyncio.create_task(self._read_stream(process.stdout, self.stdout_buffer))
        self._stderr_task = asyncio.create_task(self._read_stream(process.stderr, self.stderr_buffer))
    
    async def _read_stream(self, stream: Optional[asyncio.StreamReader], buffer: asyncio.Queue):
        """Background task to continuously read from a stream."""
        if stream is None:
            return
        
        try:
            while not self._closed:
                try:
                    # Read available data (non-blocking with timeout)
                    data = await asyncio.wait_for(stream.read(4096), timeout=0.1)
                    if not data:
                        break  # EOF
                    # Decode and enqueue each character
                    try:
                        text = data.decode('utf-8', errors='replace')
                        for char in text:
                            await buffer.put(char)
                    except Exception:
                        pass
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break
        except Exception:
            pass
    
    async def send_text(self, text: str) -> dict[str, Any]:
        """Send text string to terminal stdin."""
        if self._closed or self.process.stdin is None:
            return {"error": "Terminal is closed or stdin not available"}
        
        try:
            self.process.stdin.write(text.encode('utf-8'))
            await self.process.stdin.drain()
            return {"success": True, "action": "send_text", "pid": self.pid, "text_length": len(text)}
        except Exception as e:
            return {"error": f"Failed to send text: {str(e)}", "pid": self.pid}
    
    async def send_key(self, key: str, event: str) -> dict[str, Any]:
        """Send key event (down/up) to terminal.
        
        Args:
            key: Key string (same format as keyboard tools, e.g., 'a', 'ctrl', 'enter')
            event: 'down' or 'up'
        """
        if self._closed or self.process.stdin is None:
            return {"error": "Terminal is closed or stdin not available"}
        
        try:
            # Convert key string to terminal input
            # For special keys, send VT sequences or raw bytes
            key_obj = key_from_string(key)
            
            # Map special keys to terminal sequences
            if hasattr(key_obj, 'name') or isinstance(key_obj, str):
                # Special key - send VT sequence or raw control code
                sequence = _key_to_terminal_sequence(key, event)
                if sequence:
                    self.process.stdin.write(sequence.encode('utf-8') if isinstance(sequence, str) else sequence)
                    await self.process.stdin.drain()
                    return {"success": True, "action": "send_key", "pid": self.pid, "key": key, "event": event}
            
            # Regular character
            if event == "down":
                # For character keys on 'down', we typically want to send the character
                if isinstance(key_obj, type) and hasattr(key_obj, 'char') and key_obj.char:
                    self.process.stdin.write(key_obj.char.encode('utf-8'))
                    await self.process.stdin.drain()
                    return {"success": True, "action": "send_key", "pid": self.pid, "key": key, "event": event}
                elif len(key) == 1:
                    self.process.stdin.write(key.encode('utf-8'))
                    await self.process.stdin.drain()
                    return {"success": True, "action": "send_key", "pid": self.pid, "key": key, "event": event}
            
            # For 'up' events or non-character keys, we might not send anything
            # (terminal input typically doesn't track key up events)
            return {"success": True, "action": "send_key", "pid": self.pid, "key": key, "event": event, "note": "Key up events not typically sent to terminals"}
        
        except Exception as e:
            return {"error": f"Failed to send key: {str(e)}", "pid": self.pid}
    
    async def read_output(self, as_chars: bool = True, count: Optional[int] = None) -> dict[str, Any]:
        """Read output from terminal.
        
        Args:
            as_chars: If True, return array of characters; if False, return text string
            count: Maximum number of characters/bytes to read (None = all available)
        
        Returns:
            Dictionary with 'chars' (if as_chars) or 'text' (if not as_chars) and 'pid'
        """
        if self._closed:
            return {"error": "Terminal is closed", "pid": self.pid}
        
        try:
            if as_chars:
                # Read characters into array
                chars = []
                while True:
                    try:
                        char = await asyncio.wait_for(self.stdout_buffer.get(), timeout=0.01)
                        chars.append(char)
                        if count is not None and len(chars) >= count:
                            break
                    except asyncio.TimeoutError:
                        break
                    
                    # Also check stderr
                    try:
                        char = await asyncio.wait_for(self.stderr_buffer.get(), timeout=0.01)
                        chars.append(char)
                        if count is not None and len(chars) >= count:
                            break
                    except asyncio.TimeoutError:
                        break
                
                return {"success": True, "action": "read_output", "pid": self.pid, "chars": chars}
            else:
                # Read as text string
                text_parts = []
                
                # Read from stdout
                while True:
                    try:
                        char = await asyncio.wait_for(self.stdout_buffer.get(), timeout=0.01)
                        text_parts.append(char)
                        if count is not None and len(text_parts) >= count:
                            break
                    except asyncio.TimeoutError:
                        break
                
                # Read from stderr
                while True:
                    try:
                        char = await asyncio.wait_for(self.stderr_buffer.get(), timeout=0.01)
                        text_parts.append(char)
                        if count is not None and len(text_parts) >= count:
                            break
                    except asyncio.TimeoutError:
                        break
                
                text = ''.join(text_parts)
                return {"success": True, "action": "read_output", "pid": self.pid, "text": text}
        
        except Exception as e:
            return {"error": f"Failed to read output: {str(e)}", "pid": self.pid}
    
    def close(self):
        """Close/kill the terminal process."""
        if self._closed:
            return
        
        self._closed = True
        
        # Cancel background tasks
        if self._stdout_task and not self._stdout_task.done():
            self._stdout_task.cancel()
        if self._stderr_task and not self._stderr_task.done():
            self._stderr_task.cancel()
        
        # Close streams properly
        try:
            if self.process.stdin:
                self.process.stdin.close()
        except Exception:
            pass
        
        try:
            if self.process.stdout:
                self.process.stdout.close()
        except Exception:
            pass
        
        try:
            if self.process.stderr:
                self.process.stderr.close()
        except Exception:
            pass
        
        # Kill process
        try:
            if self.process.returncode is None:
                self.process.kill()
                # Wait briefly for process to terminate
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create a task to wait for process
                        asyncio.create_task(self.process.wait())
                    else:
                        asyncio.run(self.process.wait())
                except Exception:
                    pass
        except Exception:
            pass
        
        # Remove from registry
        _terminals.pop(self.pid, None)
    
    def get_status(self) -> dict[str, Any]:
        """Get terminal status information."""
        return {
            "pid": self.pid,
            "returncode": self.process.returncode,
            "running": self.process.returncode is None,
            "closed": self._closed
        }


def _key_to_terminal_sequence(key: str, event: str) -> Optional[bytes | str]:
    """Convert key string to terminal input sequence (VT sequences or control codes).
    
    Args:
        key: Key string
        event: 'down' or 'up' (up events typically not sent)
    
    Returns:
        Bytes or string to send to terminal, or None if not handled
    """
    if event == "up":
        return None  # Terminal input typically doesn't handle key up
    
    key_lower = key.lower().strip()
    
    # Special key mappings to VT sequences or control codes
    key_map = {
        "enter": "\r",
        "return": "\r",
        "tab": "\t",
        "esc": "\x1b",
        "escape": "\x1b",
        "backspace": "\x7f",  # or \b
        "delete": "\x1b[3~",
        "up": "\x1b[A",
        "down": "\x1b[B",
        "right": "\x1b[C",
        "left": "\x1b[D",
        "home": "\x1b[H",
        "end": "\x1b[F",
        "pageup": "\x1b[5~",
        "pagedown": "\x1b[6~",
        "ctrl+c": "\x03",
        "ctrl+z": "\x1a",
        "ctrl+d": "\x04",  # EOF
    }
    
    if key_lower in key_map:
        return key_map[key_lower]
    
    # Handle ctrl+key combinations
    if key_lower.startswith("ctrl+") or key_lower.startswith("control+"):
        base_key = key_lower.split("+", 1)[1]
        # Control characters (0x00-0x1F) are typically mapped to Ctrl+letter
        if len(base_key) == 1:
            char_code = ord(base_key.lower()) - ord('a') + 1
            if 1 <= char_code <= 26:
                return bytes([char_code])
    
    return None


async def spawn_terminal(
    command: Optional[list[str]] = None,
    shell: bool = False
) -> dict[str, Any]:
    """Spawn a new terminal process.
    
    Args:
        command: Command to execute (list of args). If None, uses platform default.
        shell: Whether to run in shell mode
    
    Returns:
        Dictionary with 'pid' and terminal info
    """
    try:
        from computer_mcp.core.platform import get_default_terminal_command
        
        if command is None:
            command = get_default_terminal_command()
        
        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=shell
        )
        
        pid = process.pid
        terminal = Terminal(pid, process)
        _terminals[pid] = terminal
        
        return {
            "success": True,
            "action": "spawn_terminal",
            "pid": pid,
            "command": command
        }
    
    except Exception as e:
        return {"error": f"Failed to spawn terminal: {str(e)}"}


def list_terminals() -> dict[str, Any]:
    """List all active terminals."""
    terminals_list = []
    for pid, terminal in _terminals.items():
        terminals_list.append(terminal.get_status())
    
    return {
        "success": True,
        "action": "list_terminals",
        "terminals": terminals_list,
        "count": len(terminals_list)
    }


def get_terminal(pid: int) -> Optional[Terminal]:
    """Get terminal by PID."""
    return _terminals.get(pid)


def close_terminal(pid: int) -> dict[str, Any]:
    """Close/kill a terminal by PID."""
    terminal = _terminals.get(pid)
    if terminal is None:
        return {"error": f"Terminal with PID {pid} not found"}
    
    terminal.close()
    return {"success": True, "action": "close_terminal", "pid": pid}


def close_all_terminals():
    """Close all active terminals (cleanup on shutdown)."""
    terminals_to_close = list(_terminals.values())
    for terminal in terminals_to_close:
        terminal.close()


# Register cleanup handlers
atexit.register(close_all_terminals)

def _signal_handler(signum, frame):  # noqa: ARG001
    """Handle shutdown signals."""
    close_all_terminals()

signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)

