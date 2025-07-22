#!/usr/bin/env python3
"""
ZedLink Cross-Platform Compatibility Test
Tests that our code works on Windows, macOS, and Linux.
"""

import sys
import os
import platform
import socket

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

def test_python_version():
    """Test Python version compatibility"""
    print(f"🐍 Python Version: {sys.version}")
    major, minor = sys.version_info[:2]
    
    if major >= 3 and minor >= 8:
        print("✅ Python version compatible (3.8+)")
        return True
    else:
        print("❌ Python version too old (need 3.8+)")
        return False

def test_os_compatibility():
    """Test OS-specific features"""
    print(f"💻 Operating System: {platform.system()} {platform.release()}")
    print(f"🏗️  Architecture: {platform.machine()}")
    
    os_name = platform.system().lower()
    
    if os_name in ['windows', 'linux', 'darwin']:
        print(f"✅ OS '{platform.system()}' is supported")
        return True
    else:
        print(f"⚠️  OS '{platform.system()}' is untested but may work")
        return True

def test_pynput_import():
    """Test pynput availability"""
    try:
        from pynput import mouse, keyboard
        print("✅ pynput imported successfully")
        
        # Test mouse controller creation
        controller = mouse.Controller()
        pos = controller.position
        print(f"✅ Mouse controller works (current pos: {pos})")
        
        return True
    except ImportError as e:
        print(f"❌ pynput import failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️  pynput available but error: {e}")
        return False

def test_networking():
    """Test basic networking functionality"""
    try:
        # Test socket creation
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Test binding to localhost
        test_socket.bind(('127.0.0.1', 0))  # 0 = any available port
        port = test_socket.getsockname()[1]
        
        test_socket.close()
        print(f"✅ TCP socket binding works (tested port {port})")
        return True
    except Exception as e:
        print(f"❌ Socket error: {e}")
        return False

def test_signal_handling():
    """Test signal handling compatibility"""
    try:
        import signal
        
        # Test if SIGINT is available (should be on all platforms)
        if hasattr(signal, 'SIGINT'):
            print("✅ SIGINT signal available")
            
            # Test signal handler registration
            def dummy_handler(sig, frame):
                pass
            
            signal.signal(signal.SIGINT, dummy_handler)
            print("✅ Signal handler registration works")
            return True
        else:
            print("❌ SIGINT not available")
            return False
    except Exception as e:
        print(f"❌ Signal handling error: {e}")
        return False

def test_protocol_import():
    """Test our protocol module"""
    try:
        from shared.protocol import Protocol, MessageType
        
        # Test message creation
        msg = Protocol.create_mouse_move(0.5, 0.5)
        encoded = Protocol.encode_message(msg)
        decoded = Protocol.decode_message(encoded.strip())
        
        print("✅ Protocol module works")
        return True
    except Exception as e:
        print(f"❌ Protocol error: {e}")
        return False

def main():
    """Run all compatibility tests"""
    print("🧪 ZedLink Cross-Platform Compatibility Test")
    print("=" * 50)
    
    tests = [
        ("Python Version", test_python_version),
        ("Operating System", test_os_compatibility),
        ("pynput Library", test_pynput_import),
        ("Network Sockets", test_networking),
        ("Signal Handling", test_signal_handling),
        ("Protocol Module", test_protocol_import),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! ZedLink should work on this platform.")
    elif passed >= total - 1:
        print("⚠️  Minor issues detected but should still work.")
    else:
        print("❌ Significant compatibility issues detected.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
