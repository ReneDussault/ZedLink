#!/usr/bin/env python3
"""
ZedLink Server - Remote Mouse Controller
Receives mouse commands from client and controls local mouse pointer.
"""

import sys
import os
import signal
import platform

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from network_server import ZedLinkServer
from mouse_controller import MouseController

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully (cross-platform)"""
    print("\n🛑 Shutting down ZedLink Server...")
    # Don't call sys.exit here, let the main loop handle cleanup
    if hasattr(signal_handler, 'server'):
        signal_handler.server.stop()
    sys.exit(0)

def setup_signal_handlers():
    """Set up signal handlers in a cross-platform way"""
    try:
        signal.signal(signal.SIGINT, signal_handler)
        
        # On Unix-like systems, also handle SIGTERM
        if platform.system() != 'Windows':
            signal.signal(signal.SIGTERM, signal_handler)
        
        print("✅ Signal handlers configured")
    except Exception as e:
        print(f"⚠️  Signal handler setup failed: {e}")
        print("   Manual shutdown with Ctrl+C may be needed")

def main():
    """Main entry point for ZedLink Server"""
    print("🖱️  ZedLink Server starting...")
    print(f"� Platform: {platform.system()} {platform.release()}")
    print("�📡 Basic networking architecture ready!")
    
    # Set up signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Initialize components
    mouse_controller = MouseController()
    server = ZedLinkServer(mouse_controller=mouse_controller)
    
    # Store server reference for signal handler
    signal_handler.server = server
    
    print(f"🚀 Server listening on port 9876")
    print("💡 Ready for client connections!")
    print("   Press Ctrl+C to stop")
    
    try:
        # Start the server (this will block)
        server.start()
    except KeyboardInterrupt:
        pass  # Don't print here, signal handler already did
    finally:
        server.stop()

if __name__ == "__main__":
    main()
