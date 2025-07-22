#!/usr/bin/env python3
"""
ZedLink Client - Main Entry Point
Controls remote PC mouse from this machine via edge triggers and hotkeys.
"""

import sys
import os
import time

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from network_client import ZedLinkClient

def test_basic_connection():
    """Test basic client-server communication"""
    print("🔗 Testing connection to ZedLink Server...")
    
    client = ZedLinkClient()
    
    # Try to connect
    if client.connect():
        print("✅ Connected successfully!")
        
        # Send a test mouse movement
        print("📍 Sending test mouse movement...")
        client.send_mouse_move(0.5, 0.5)  # Center of screen
        
        time.sleep(1)
        
        print("🔌 Disconnecting...")
        client.disconnect()
        print("✅ Test complete!")
    else:
        print("❌ Connection failed!")
        print("💡 Make sure the server is running first")

def main():
    """Main entry point for ZedLink Client"""
    print("🖱️  ZedLink Client starting...")
    print("📡 Basic networking architecture ready!")
    
    # For now, just test the connection
    test_basic_connection()
    
    print("\n🚧 Phase 2: Basic networking implemented!")
    print("📋 Next: Edge detection and hotkey systems")

if __name__ == "__main__":
    main()
