"""
Network Scanner Module
Handles subnet scanning and MAC address detection
"""

import asyncio
import ipaddress
import re
from typing import List, Dict, Tuple, Optional
from loguru import logger


class NetworkScanner:
    """Network scanner for subnet detection and MAC address lookup"""
    
    @staticmethod
    def parse_subnet(subnet_str: str) -> List[str]:
        """
        Parse a subnet CIDR notation and return all IP addresses
        
        Args:
            subnet_str: Subnet in CIDR notation (e.g., 192.168.1.0/24)
            
        Returns:
            List of IP addresses in the subnet
        """
        try:
            network = ipaddress.ip_network(subnet_str, strict=False)
            # Exclude network and broadcast addresses for /31 and /32 subnets
            if network.prefixlen >= 31:
                return [str(ip) for ip in network.hosts()]
            else:
                return [str(ip) for ip in network.hosts() if ip not in [network.network_address, network.broadcast_address]]
        except ValueError as e:
            logger.error(f"Invalid subnet format {subnet_str}: {e}")
            return []
    
    @staticmethod
    async def get_mac_address(ip: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get MAC address and vendor info for an IP using nmap
        
        Args:
            ip: IP address to scan
            
        Returns:
            Tuple of (mac_address, vendor_info)
        """
        try:
            process = await asyncio.create_subprocess_exec(
                'sudo', 'nmap', '-sn', ip,
                stdout=asyncio.PIPE,
                stderr=asyncio.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=10
            )
            
            if process.returncode != 0:
                logger.error(f"Nmap error for {ip}: {stderr.decode().strip()}")
                return None, None
            
            output = stdout.decode()
            
            # Parse MAC address
            mac_pattern = r'MAC Address: ([0-9A-F:]{17}) \((.*?)\)'
            mac_match = re.search(mac_pattern, output, re.IGNORECASE)
            
            if mac_match:
                mac_address = mac_match.group(1).upper()
                vendor_info = mac_match.group(2).strip()
                return mac_address, vendor_info
            
            # Alternative pattern
            alt_pattern = r'([0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2})'
            alt_match = re.search(alt_pattern, output, re.IGNORECASE)
            
            if alt_match:
                mac_address = alt_match.group(1).upper()
                return mac_address, "Unknown"
            
            return None, None
            
        except asyncio.TimeoutError:
            logger.warning(f"Nmap timeout for {ip}")
            return None, None
        except Exception as e:
            logger.error(f"Error getting MAC for {ip}: {e}")
            return None, None
    
    @staticmethod
    async def scan_subnet(subnet_str: str) -> List[Dict]:
        """
        Scan a subnet and return active hosts with MAC addresses
        
        Args:
            subnet_str: Subnet in CIDR notation
            
        Returns:
            List of dicts with ip, mac_address, and vendor_info
        """
        ips = NetworkScanner.parse_subnet(subnet_str)
        if not ips:
            return []
        
        logger.info(f"Scanning subnet {subnet_str} with {len(ips)} IPs...")
        
        # First, do a quick ping scan to find active hosts
        active_hosts = []
        ping_tasks = []
        
        async def check_host(ip: str) -> Tuple[str, bool]:
            try:
                process = await asyncio.create_subprocess_exec(
                    'ping', '-c', '1', '-W', '1', ip,
                    stdout=asyncio.DEVNULL,
                    stderr=asyncio.DEVNULL
                )
                await asyncio.wait_for(process.wait(), timeout=2)
                return ip, process.returncode == 0
            except:
                return ip, False
        
        # Check all IPs concurrently
        for ip in ips:
            ping_tasks.append(check_host(ip))
        
        ping_results = await asyncio.gather(*ping_tasks)
        
        # Get MAC addresses for active hosts
        active_ips = [ip for ip, is_up in ping_results if is_up]
        
        logger.info(f"Found {len(active_ips)} active hosts in {subnet_str}")
        
        # Get MAC addresses for active hosts
        mac_tasks = [NetworkScanner.get_mac_address(ip) for ip in active_ips]
        mac_results = await asyncio.gather(*mac_tasks)
        
        # Combine results
        for ip, (mac, vendor) in zip(active_ips, mac_results):
            if mac:  # Only include hosts with detectable MAC
                active_hosts.append({
                    'ip': ip,
                    'mac_address': mac,
                    'vendor_info': vendor or "Unknown",
                    'status': 'active'
                })
        
        return active_hosts
    
    @staticmethod
    def generate_host_name(ip: str, mac: Optional[str] = None, vendor: Optional[str] = None) -> str:
        """
        Generate a host name based on IP, MAC, and vendor info
        
        Args:
            ip: IP address
            mac: MAC address
            vendor: Vendor information
            
        Returns:
            Generated host name
        """
        # Extract last octet of IP
        last_octet = ip.split('.')[-1]
        
        if vendor and vendor != "Unknown":
            # Use vendor name and last octet
            vendor_short = vendor.split()[0]  # Take first word of vendor
            return f"{vendor_short}-{last_octet}"
        elif mac:
            # Use last 4 chars of MAC
            mac_short = mac.replace(':', '')[-4:].upper()
            return f"Host-{last_octet}-{mac_short}"
        else:
            return f"Host-{last_octet}"
