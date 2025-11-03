"""CLI implementation for computer control commands and server management."""

import argparse
import asyncio
import json
import sys
from typing import Any

from computer_mcp.actions import (
    keyboard as keyboard_actions,
    mouse as mouse_actions,
    screenshot as screenshot_actions,
    window as window_actions,
)
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController

# Initialize controllers
mouse_controller = MouseController()
keyboard_controller = KeyboardController()


def print_result(result: dict[str, Any], as_json: bool = False):
    """Print action result."""
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            print(f"✅ {result.get('action', 'Action')} completed successfully")
            if "text" in result:
                print(f"   Typed: {result['text']}")
            if "button" in result:
                print(f"   Button: {result['button']")
            if "window" in result:
                print(f"   Window: {result['window'].get('title', 'Unknown')}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            if "note" in result:
                print(f"   Note: {result['note']}")


def handle_mouse_command(args: argparse.Namespace):
    """Handle mouse commands."""
    if args.command == "click":
        result = mouse_actions.click(button=args.button, controller=mouse_controller)
        print_result(result, args.json)
    elif args.command == "double-click":
        result = mouse_actions.double_click(button=args.button, controller=mouse_controller)
        print_result(result, args.json)
    elif args.command == "triple-click":
        result = mouse_actions.triple_click(button=args.button, controller=mouse_controller)
        print_result(result, args.json)
    elif args.command == "move":
        result = mouse_actions.move_mouse(x=args.x, y=args.y, controller=mouse_controller)
        print_result(result, args.json)
    else:
        print(f"Unknown mouse command: {args.command}", file=sys.stderr)
        sys.exit(1)


def handle_keyboard_command(args: argparse.Namespace):
    """Handle keyboard commands."""
    if args.command == "type":
        result = keyboard_actions.type_text(text=args.text, controller=keyboard_controller)
        print_result(result, args.json)
    elif args.command == "key-press":
        result = keyboard_actions.key_press(key=args.key, controller=keyboard_controller)
        print_result(result, args.json)
    elif args.command == "key-down":
        result = keyboard_actions.key_down(key=args.key, controller=keyboard_controller)
        print_result(result, args.json)
    elif args.command == "key-up":
        result = keyboard_actions.key_up(key=args.key, controller=keyboard_controller)
        print_result(result, args.json)
    else:
        print(f"Unknown keyboard command: {args.command}", file=sys.stderr)
        sys.exit(1)


def handle_window_command(args: argparse.Namespace):
    """Handle window commands."""
    if args.command == "list":
        result = window_actions.list_windows()
        print_result(result, args.json)
    elif args.command == "switch":
        result = window_actions.switch_to_window(
            hwnd=args.hwnd,
            title=args.title
        )
        print_result(result, args.json)
    elif args.command == "close":
        if not args.hwnd:
            print("Error: --hwnd is required for close command", file=sys.stderr)
            sys.exit(1)
        result = window_actions.close_window(hwnd=args.hwnd)
        print_result(result, args.json)
    elif args.command == "snap-left":
        if not args.hwnd:
            print("Error: --hwnd is required for snap-left command", file=sys.stderr)
            sys.exit(1)
        result = window_actions.snap_window_left(hwnd=args.hwnd)
        print_result(result, args.json)
    elif args.command == "snap-right":
        if not args.hwnd:
            print("Error: --hwnd is required for snap-right command", file=sys.stderr)
            sys.exit(1)
        result = window_actions.snap_window_right(hwnd=args.hwnd)
        print_result(result, args.json)
    else:
        print(f"Unknown window command: {args.command}", file=sys.stderr)
        sys.exit(1)


def handle_screenshot_command(args: argparse.Namespace):
    """Handle screenshot command."""
    result = screenshot_actions.get_screenshot()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("success") or "data" in result:
            print("✅ Screenshot captured")
            print(f"   Format: {result.get('format', 'unknown')}")
            print(f"   Dimensions: {result.get('width')}x{result.get('height')}")
            if args.save:
                # Save screenshot to file
                import base64
                from pathlib import Path
                if "data" in result:
                    image_data = base64.b64decode(result["data"])
                    output_path = Path(args.save)
                    output_path.write_bytes(image_data)
                    print(f"   Saved to: {output_path}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")


async def handle_serve_command(args: argparse.Namespace):
    """Handle serve command (start API or MCP server)."""
    if args.type == "api":
        # Start HTTP API server
        try:
            from computer_mcp.api import app
            import uvicorn
            print(f"Starting HTTP API server on http://{args.host}:{args.port}")
            print(f"API docs available at http://{args.host}:{args.port}/docs")
            await uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("Error: fastapi and uvicorn are required for API server", file=sys.stderr)
            print("Install with: pip install fastapi uvicorn", file=sys.stderr)
            sys.exit(1)
    elif args.type == "mcp":
        # Start MCP server
        from computer_mcp.mcp import run_stdio, run_http
        if args.http:
            print(f"Starting MCP server in HTTP/SSE mode on http://{args.host}:{args.port}")
            await run_http(host=args.host, port=args.port)
        else:
            print("Starting MCP server in stdio mode")
            await run_stdio()
    else:
        print(f"Unknown server type: {args.type}", file=sys.stderr)
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="computer-mcp",
        description="Computer control CLI and server manager"
    )
    
    subparsers = parser.add_subparsers(dest="mode", help="Mode of operation")
    
    # Mouse subparser
    mouse_parser = subparsers.add_parser("mouse", help="Mouse commands")
    mouse_subparsers = mouse_parser.add_subparsers(dest="command", help="Mouse command")
    
    click_parser = mouse_subparsers.add_parser("click", help="Click mouse button")
    click_parser.add_argument("--button", choices=["left", "right", "middle"], default="left")
    click_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    double_click_parser = mouse_subparsers.add_parser("double-click", help="Double click mouse button")
    double_click_parser.add_argument("--button", choices=["left", "right", "middle"], default="left")
    double_click_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    triple_click_parser = mouse_subparsers.add_parser("triple-click", help="Triple click mouse button")
    triple_click_parser.add_argument("--button", choices=["left", "right", "middle"], default="left")
    triple_click_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    move_parser = mouse_subparsers.add_parser("move", help="Move mouse cursor")
    move_parser.add_argument("--x", type=int, required=True, help="X coordinate")
    move_parser.add_argument("--y", type=int, required=True, help="Y coordinate")
    move_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Keyboard subparser
    keyboard_parser = subparsers.add_parser("keyboard", help="Keyboard commands")
    keyboard_subparsers = keyboard_parser.add_subparsers(dest="command", help="Keyboard command")
    
    type_parser = keyboard_subparsers.add_parser("type", help="Type text")
    type_parser.add_argument("text", help="Text to type")
    type_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    key_press_parser = keyboard_subparsers.add_parser("key-press", help="Press and release a key")
    key_press_parser.add_argument("key", help="Key to press (e.g., 'ctrl', 'a', 'space')")
    key_press_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    key_down_parser = keyboard_subparsers.add_parser("key-down", help="Press and hold a key")
    key_down_parser.add_argument("key", help="Key to press")
    key_down_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    key_up_parser = keyboard_subparsers.add_parser("key-up", help="Release a key")
    key_up_parser.add_argument("key", help="Key to release")
    key_up_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Window subparser
    window_parser = subparsers.add_parser("window", help="Window management commands")
    window_subparsers = window_parser.add_subparsers(dest="command", help="Window command")
    
    list_parser = window_subparsers.add_parser("list", help="List all windows")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    switch_parser = window_subparsers.add_parser("switch", help="Switch to a window")
    switch_parser.add_argument("--hwnd", type=int, help="Window handle")
    switch_parser.add_argument("--title", help="Window title pattern")
    switch_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    close_parser = window_subparsers.add_parser("close", help="Close a window")
    close_parser.add_argument("--hwnd", type=int, required=True, help="Window handle")
    close_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    snap_left_parser = window_subparsers.add_parser("snap-left", help="Snap window left")
    snap_left_parser.add_argument("--hwnd", type=int, required=True, help="Window handle")
    snap_left_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    snap_right_parser = window_subparsers.add_parser("snap-right", help="Snap window right")
    snap_right_parser.add_argument("--hwnd", type=int, required=True, help="Window handle")
    snap_right_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Screenshot subparser
    screenshot_parser = subparsers.add_parser("screenshot", help="Screenshot commands")
    screenshot_parser.add_argument("--json", action="store_true", help="Output as JSON")
    screenshot_parser.add_argument("--save", help="Save screenshot to file")
    
    # Serve subparser
    serve_parser = subparsers.add_parser("serve", help="Start a server")
    serve_parser.add_argument("type", choices=["api", "mcp"], help="Server type")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    serve_parser.add_argument("--http", action="store_true", help="Use HTTP mode (MCP only)")
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.mode == "mouse":
            handle_mouse_command(args)
        elif args.mode == "keyboard":
            handle_keyboard_command(args)
        elif args.mode == "window":
            handle_window_command(args)
        elif args.mode == "screenshot":
            handle_screenshot_command(args)
        elif args.mode == "serve":
            asyncio.run(handle_serve_command(args))
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

