"""
Auto-discovery system for ZedLink
Automatically detects local IP addresses and discovers ZedLink servers on the network.
"""

import socket
import subprocess
import platform
import json
import threading
import time
from typing import List, Dict, Optional, Tuple
import logging


class NetworkDiscovery:
    """Auto-discovery system for ZedLink networking"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system = platform.system().lower()
        
    def get_local_ip_addresses(self) -> List[str]:
        """Get all local IP addresses for this machine"""
        ips = []
        
        try:
            # Method 1: Use socket to connect to external IP (doesn't actually connect)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                primary_ip = s.getsockname()[0]
                if primary_ip not in ips:
                    ips.append(primary_ip)
        except Exception:
            pass
        
        try:
            # Method 2: Get hostname IP
            hostname_ip = socket.gethostbyname(socket.gethostname())
            if hostname_ip not in ips and not hostname_ip.startswith("127."):
                ips.append(hostname_ip)
        except Exception:
            pass
        
        try:
            # Method 3: Platform-specific commands
            if self.system == "linux" or self.system == "darwin":
                # Use hostname -I on Linux/macOS
                result = subprocess.run(["hostname", "-I"], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for ip in result.stdout.strip().split():
                        if ip not in ips and not ip.startswith("127."):
                            ips.append(ip)
            
            elif self.system == "windows":
                # Use ipconfig on Windows
                result = subprocess.run(["ipconfig"], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "IPv4 Address" in line:
                            ip = line.split(":")[-1].strip()
                            if ip not in ips and not ip.startswith("127."):
                                ips.append(ip)
        except Exception as e:
            self.logger.debug(f"Platform-specific IP detection failed: {e}")
        
        # Filter out invalid IPs
        valid_ips = []
        for ip in ips:
            try:
                socket.inet_aton(ip)  # Validate IP format
                if not ip.startswith("127.") and not ip.startswith("169.254."):
                    valid_ips.append(ip)
            except:
                pass
        
        self.logger.info(f"Detected local IPs: {valid_ips}")
        return valid_ips
    
    def get_network_ranges(self, local_ips: List[str]) -> List[str]:
        """Get network ranges to scan based on local IPs"""
        ranges = []
        
        for ip in local_ips:
            parts = ip.split('.')
            if len(parts) == 4:
                network_base = f"{parts[0]}.{parts[1]}.{parts[2]}"
                if network_base not in ranges:
                    ranges.append(network_base)
        
        return ranges
    
    def scan_for_zedlink_servers(self, timeout: float = 1.0) -> List[Tuple[str, int]]:
        """Scan all local networks for ZedLink servers"""
        found_servers = []
        local_ips = self.get_local_ip_addresses()
        
        if not local_ips:
            self.logger.warning("No local IPs detected")
            return []
        
        network_ranges = self.get_network_ranges(local_ips)
        
        print(f"🔍 Scanning networks: {network_ranges}")
        print(f"📍 Your IPs: {local_ips}")
        
        def check_host(ip: str, port: int = 9876):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    found_servers.append((ip, port))
                    print(f"✅ Found ZedLink server at {ip}:{port}")
                sock.close()
            except:
                pass
        
        # Start threads to check IPs in parallel
        threads = []
        for network_base in network_ranges:
            for i in range(1, 255):
                ip = f"{network_base}.{i}"
                if ip not in local_ips:  # Skip our own IPs
                    thread = threading.Thread(target=check_host, args=(ip,))
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
                    
                    # Limit concurrent threads to avoid overwhelming
                    if len(threads) >= 50:
                        for t in threads:
                            t.join()
                        threads = []
        
        # Wait for remaining threads
        for thread in threads:
            thread.join()
        
        return found_servers
    
    def auto_configure_client(self, config_manager) -> bool:
        """Automatically configure client with discovered server"""
        print("🔍 Auto-discovering ZedLink servers...")
        
        servers = self.scan_for_zedlink_servers()
        
        if servers:
            best_server = servers[0]  # Use first found server
            ip, port = best_server
            
            print(f"✅ Auto-configuring with server: {ip}:{port}")
            
            # Update configuration
            success = config_manager.update_config(
                server_host=ip,
                server_port=port
            )
            
            if success:
                print(f"✅ Configuration updated successfully!")
                return True
            else:
                print(f"❌ Failed to update configuration")
                return False
        else:
            print("❌ No ZedLink servers found on network")
            print("💡 Make sure the server is running and accessible")
            return False
    
    def broadcast_server_presence(self, port: int = 9876) -> bool:
        """Broadcast server presence for auto-discovery (future feature)"""
        # This could send UDP broadcasts to announce server presence
        # For now, we rely on port scanning
        return True  # Placeholder


def auto_discover_and_configure():
    """Standalone function to auto-discover and configure"""
    # Import here to avoid circular imports
    import sys
    import os
    
    # Add paths for imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    client_dir = os.path.join(os.path.dirname(current_dir), 'client')
    sys.path.append(client_dir)
    
    try:
        from client.config import get_config_manager
        
        discovery = NetworkDiscovery()
        config_manager = get_config_manager()
        
        # Show current config
        current_config = config_manager.load_config()
        print(f"📋 Current server config: {current_config.server_host}:{current_config.server_port}")
        
        # Try auto-discovery
        success = discovery.auto_configure_client(config_manager)
        
        if success:
            # Show updated config
            updated_config = config_manager.load_config()
            print(f"📋 Updated server config: {updated_config.server_host}:{updated_config.server_port}")
        
        return success
        
    except ImportError as e:
        print(f"❌ Could not import config module: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🌐 ZedLink Auto-Discovery")
    print("=" * 40)
    
    discovery = NetworkDiscovery()
    
    # Test 1: Get local IPs
    print("🔍 Detecting local IP addresses...")
    local_ips = discovery.get_local_ip_addresses()
    print(f"📍 Local IPs: {local_ips}")
    
    # Test 2: Scan for servers
    print(f"\n🔍 Scanning for ZedLink servers...")
    servers = discovery.scan_for_zedlink_servers()
    
    if servers:
        print(f"\n🎯 Found {len(servers)} server(s):")
        for ip, port in servers:
            print(f"   • {ip}:{port}")
    else:
        print(f"\n❌ No servers found")
    
    # Test 3: Auto-configure if possible
    print(f"\n🔧 Testing auto-configuration...")
    success = auto_discover_and_configure()
    
    if success:
        print("✅ Auto-discovery and configuration successful!")
    else:
        print("❌ Auto-discovery failed - manual configuration required")
