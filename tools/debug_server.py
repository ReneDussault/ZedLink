#!/usr/bin/env python3
"""
Debug script to test the full server integration
Run this on your Linux Mint machine after updating the server files
"""

import sys
import json
import time
from server.mouse_controller import MouseController
from server.network_server import ZedLinkServer

def test_message_processing():
    """Test if the server processes mouse messages correctly"""
    print("🔧 Testing server message processing...")
    
    # Create components
    mouse_controller = MouseController()
    server = ZedLinkServer(mouse_controller=mouse_controller)
    
    print(f"✅ MouseController: {mouse_controller}")
    print(f"✅ ZedLinkServer: {server}")
    print(f"✅ Server has mouse_controller: {hasattr(server, 'mouse_controller')}")
    print(f"✅ Server mouse_controller is: {server.mouse_controller}")
    
    # Test message processing
    test_messages = [
        {"type": "handshake", "version": "1.0"},
        {"type": "mouse_move", "x": 0.5, "y": 0.5},
        {"type": "mouse_move", "x": 0.2, "y": 0.3},
        {"type": "mouse_move", "x": 0.8, "y": 0.7},
        {"type": "mouse_click", "button": "left", "pressed": True},
        {"type": "mouse_click", "button": "left", "pressed": False},
    ]
    
    print("\n🖱️  Testing message processing (watch your mouse)...")
    
    for i, message in enumerate(test_messages):
        print(f"   {i+1}. Processing: {message}")
        try:
            json_message = json.dumps(message)
            server._process_message(json_message)
            time.sleep(1)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    print("\n✅ Message processing test completed!")
    return True

def check_server_files():
    """Check if server files have the correct integration"""
    print("\n🔍 Checking server file integration...")
    
    # Check network_server.py
    try:
        with open('server/network_server.py', 'r') as f:
            content = f.read()
            
        checks = [
            ("mouse_controller parameter", "mouse_controller=None" in content or "mouse_controller:" in content),
            ("mouse_controller assignment", "self.mouse_controller = mouse_controller" in content),
            ("mouse move call", "self.mouse_controller.move_to(" in content),
            ("mouse click call", "self.mouse_controller.click(" in content),
        ]
        
        print("   network_server.py:")
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"     {status} {check_name}")
            
        if not all(passed for _, passed in checks):
            print("\n❌ Server files need updates!")
            return False
            
    except Exception as e:
        print(f"   ❌ Error reading network_server.py: {e}")
        return False
    
    # Check server.py
    try:
        with open('server/server.py', 'r') as f:
            content = f.read()
            
        has_integration = "mouse_controller=mouse_controller" in content
        print(f"   server.py:")
        print(f"     {'✅' if has_integration else '❌'} MouseController integration")
        
        if not has_integration:
            print("\n❌ server.py needs updates!")
            return False
            
    except Exception as e:
        print(f"   ❌ Error reading server.py: {e}")
        return False
    
    print("\n✅ All server files have correct integration!")
    return True

if __name__ == "__main__":
    print("🔧 ZedLink Server Integration Debug Tool")
    print("==========================================")
    
    # Check if files are updated
    if not check_server_files():
        print("\n📋 Action needed:")
        print("   1. Update server files with mouse controller integration")
        print("   2. Restart the server")
        print("   3. Run this test again")
        sys.exit(1)
    
    # Test message processing
    if test_message_processing():
        print("\n🎉 Server integration is working!")
        print("   The server should now respond to network messages")
        print("   Try connecting from your Windows client")
    else:
        print("\n❌ Server integration has issues")
        print("   Check the error messages above")
