#!/usr/bin/env python3
"""
Quick network discovery tool for ZedLink servers
"""

import socket
import threading
import time
from typing import List, Tuple

def scan_for_zedlink_servers(timeout: float = 2.0) -> List[Tuple[str, int]]:
    """Scan local network for ZedLink servers"""
    found_servers = []
    
    # Get local IP range
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    ip_parts = local_ip.split('.')
    base_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
    
    print(f"🔍 Scanning {base_ip}.1-254 for ZedLink servers...")
    
    def check_host(ip: str):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, 9876))
            if result == 0:
                found_servers.append((ip, 9876))
                print(f"✅ Found ZedLink server at {ip}:9876")
            sock.close()
        except:
            pass
    
    # Start threads to check IPs in parallel
    threads = []
    for i in range(1, 255):
        ip = f"{base_ip}.{i}"
        if ip != local_ip:  # Skip our own IP
            thread = threading.Thread(target=check_host, args=(ip,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    return found_servers

def test_specific_ip(ip: str, port: int = 9876) -> bool:
    """Test connection to a specific IP"""
    try:
        print(f"🔗 Testing connection to {ip}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Connection successful to {ip}:{port}")
            return True
        else:
            print(f"❌ Connection failed to {ip}:{port}")
            return False
    except Exception as e:
        print(f"❌ Error testing {ip}:{port}: {e}")
        return False

if __name__ == "__main__":
    print("🌐 ZedLink Network Discovery")
    print("=" * 40)
    
    # Get current network info
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"📍 Your PC: {hostname} ({local_ip})")
    
    # Scan for servers
    servers = scan_for_zedlink_servers()
    
    if servers:
        print(f"\n🎯 Found {len(servers)} ZedLink server(s):")
        for ip, port in servers:
            print(f"   • {ip}:{port}")
            
        print(f"\n💡 Update your config with:")
        print(f"   server_host: '{servers[0][0]}'")
        print(f"   server_port: {servers[0][1]}")
    else:
        print("\n❌ No ZedLink servers found on local network")
        print("💡 Make sure the server is running and accessible")
        
        # Test the default IP anyway
        print(f"\n🔍 Testing default IP 192.168.1.100...")
        test_specific_ip("192.168.1.100")
        
        # Test the provided Linux Mint IP
        print(f"\n🔍 Testing Linux Mint IP 10.0.0.229...")
        test_specific_ip("10.0.0.229")
