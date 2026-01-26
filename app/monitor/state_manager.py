"""
State Manager Module
Handles persistence of hosts and monitoring states
"""

import json
import asyncio
import time
from typing import Dict, List, Optional
from pathlib import Path
from loguru import logger
from ..config import settings
from ..models import Host, HostState
import aiofiles


class StateManager:
    """Manages persistent storage of hosts and states"""
    
    def __init__(self):
        self.hosts_file = settings.hosts_file
        self.states_file = settings.states_file
        self._lock = asyncio.Lock()
        self._ensure_files()
    
    def _ensure_files(self):
        """Ensure data files exist"""
        self.hosts_file.parent.mkdir(parents=True, exist_ok=True)
        self.states_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.hosts_file.exists():
            self._write_json_sync(self.hosts_file, [])
        
        if not self.states_file.exists():
            self._write_json_sync(self.states_file, {})
    
    def _write_json_sync(self, file_path: Path, data):
        """Synchronously write JSON (for initialization)"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def load_groups(self) -> Dict[int, dict]:
        """Load groups from file"""
        groups_file = self.hosts_file.parent / "groups.json"
        
        if not groups_file.exists():
            return {}
        
        async with self._lock:
            try:
                async with aiofiles.open(groups_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    return {int(gid): group for gid, group in data.items()}
            except Exception as e:
                logger.error(f"Error loading groups: {e}")
                return {}

    async def save_groups(self, groups: Dict[int, dict]):
        """Save groups to file"""
        groups_file = self.hosts_file.parent / "groups.json"
        
        async with self._lock:
            try:
                async with aiofiles.open(groups_file, 'w') as f:
                    await f.write(json.dumps(groups, indent=2))
                logger.debug(f"Saved {len(groups)} groups")
            except Exception as e:
                logger.error(f"Error saving groups: {e}")

    async def add_group(self, group_data: dict) -> int:
        """Add a new group"""
        groups = await self.load_groups()
        
        # Generate new ID
        new_id = max(groups.keys(), default=0) + 1
        groups[new_id] = {
            **group_data,
            "id": new_id,
            "created_at": int(time.time())
        }
        
        await self.save_groups(groups)
        logger.info(f"Added group: {group_data['name']} (ID: {new_id})")
        return new_id

    async def update_group(self, group_id: int, **kwargs) -> bool:
        """Update an existing group"""
        groups = await self.load_groups()
        
        if group_id not in groups:
            logger.warning(f"Group with ID {group_id} not found")
            return False
        
        # Update fields
        for key, value in kwargs.items():
            if value is not None:
                groups[group_id][key] = value
        
        await self.save_groups(groups)
        logger.info(f"Updated group ID {group_id}")
        return True

    async def delete_group(self, group_id: int) -> bool:
        """Delete a group"""
        groups = await self.load_groups()
        
        if group_id not in groups:
            logger.warning(f"Group with ID {group_id} not found")
            return False
        
        # Remove group
        del groups[group_id]
        await self.save_groups(groups)
        
        # Remove group from hosts
        hosts = await self.load_hosts()
        updated = False
        for host in hosts:
            if host.group_id == group_id:
                host.group_id = None
                updated = True
        
        if updated:
            await self.save_hosts(hosts)
        
        logger.info(f"Deleted group ID {group_id}")
        return True

    async def get_group(self, group_id: int) -> Optional[dict]:
        """Get a specific group by ID"""
        groups = await self.load_groups()
        return groups.get(group_id)

    async def get_hosts_by_group(self, group_id: Optional[int] = None) -> List[Host]:
        """Get hosts filtered by group"""
        hosts = await self.load_hosts()
        
        if group_id is None:
            return hosts
        
        return [host for host in hosts if host.group_id == group_id]

    # Update load_hosts to ensure all fields exist
    async def load_hosts(self) -> List[Host]:
        """Load hosts from file"""
        async with self._lock:
            try:
                async with aiofiles.open(self.hosts_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    
                    # Ensure all fields exist
                    for host_data in data:
                        if "group_id" not in host_data:
                            host_data["group_id"] = None
                        if "mac_address" not in host_data:
                            host_data["mac_address"] = None
                        if "vendor_info" not in host_data:
                            host_data["vendor_info"] = None
                    
                    hosts = [Host(**item) for item in data]
                    logger.debug(f"Loaded {len(hosts)} hosts")
                    return hosts
            except FileNotFoundError:
                logger.warning("Hosts file not found, returning empty list")
                return []
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding hosts file: {e}")
                return []
            except Exception as e:
                logger.error(f"Error loading hosts: {e}")
                return []

    # Update save_hosts to include all fields
    async def save_hosts(self, hosts: List[Host]):
        """Save hosts to file"""
        async with self._lock:
            try:
                data = [host.model_dump() for host in hosts]
                async with aiofiles.open(self.hosts_file, 'w') as f:
                    await f.write(json.dumps(data, indent=2))
                logger.debug(f"Saved {len(hosts)} hosts")
            except Exception as e:
                logger.error(f"Error saving hosts: {e}")
    
    async def add_host(self, host: Host) -> bool:
        """Add a new host"""
        hosts = await self.load_hosts()
        
        # Check for duplicate IP
        if any(h.ip == host.ip for h in hosts):
            logger.warning(f"Host with IP {host.ip} already exists")
            return False
        
        hosts.append(host)
        await self.save_hosts(hosts)
        logger.info(f"Added host: {host.name} ({host.ip})")
        return True
    
    async def update_host(self, ip: str, **kwargs) -> bool:
        """Update an existing host"""
        hosts = await self.load_hosts()
        
        for i, host in enumerate(hosts):
            if host.ip == ip:
                # Update fields
                for key, value in kwargs.items():
                    if hasattr(host, key) and value is not None:
                        setattr(host, key, value)
                
                hosts[i] = host
                await self.save_hosts(hosts)
                logger.info(f"Updated host: {host.name} ({host.ip})")
                return True
        
        logger.warning(f"Host with IP {ip} not found")
        return False
    
    async def delete_host(self, ip: str) -> bool:
        """Delete a host"""
        hosts = await self.load_hosts()
        original_count = len(hosts)
        
        hosts = [h for h in hosts if h.ip != ip]
        
        if len(hosts) < original_count:
            await self.save_hosts(hosts)
            logger.info(f"Deleted host with IP: {ip}")
            return True
        
        logger.warning(f"Host with IP {ip} not found")
        return False
    
    async def get_host(self, ip: str) -> Host | None:
        """Get a specific host by IP"""
        hosts = await self.load_hosts()
        for host in hosts:
            if host.ip == ip:
                return host
        return None
    
    async def load_states(self) -> Dict[str, HostState]:
        """Load states from file"""
        async with self._lock:
            try:
                async with aiofiles.open(self.states_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    states = {
                        ip: HostState(**state_data)
                        for ip, state_data in data.items()
                    }
                    logger.debug(f"Loaded {len(states)} states")
                    return states
            except FileNotFoundError:
                logger.warning("States file not found, returning empty dict")
                return {}
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding states file: {e}")
                return {}
            except Exception as e:
                logger.error(f"Error loading states: {e}")
                return {}
    
    async def save_states(self, states: Dict[str, HostState]):
        """Save states to file"""
        async with self._lock:
            try:
                data = {
                    ip: state.model_dump()
                    for ip, state in states.items()
                }
                async with aiofiles.open(self.states_file, 'w') as f:
                    await f.write(json.dumps(data, indent=2))
                logger.debug(f"Saved {len(states)} states")
            except Exception as e:
                logger.error(f"Error saving states: {e}")
    
    async def get_state(self, ip: str) -> HostState | None:
        """Get state for a specific IP"""
        states = await self.load_states()
        return states.get(ip)
    
    async def update_state(self, ip: str, state: HostState):
        """Update state for a specific IP"""
        states = await self.load_states()
        states[ip] = state
        await self.save_states(states)
    
    async def delete_state(self, ip: str):
        """Delete state for a specific IP"""
        states = await self.load_states()
        if ip in states:
            del states[ip]
            await self.save_states(states)
            logger.info(f"Deleted state for IP: {ip}")
    
    async def cleanup_orphaned_states(self):
        """Remove states for hosts that no longer exist"""
        hosts = await self.load_hosts()
        states = await self.load_states()
        
        host_ips = {h.ip for h in hosts}
        state_ips = set(states.keys())
        
        orphaned = state_ips - host_ips
        
        if orphaned:
            for ip in orphaned:
                del states[ip]
            await self.save_states(states)
            logger.info(f"Cleaned up {len(orphaned)} orphaned states")
    
    async def get_statistics(self) -> Dict:
        """Get current statistics"""
        hosts = await self.load_hosts()
        states = await self.load_states()
        
        total = len(hosts)
        enabled = len([h for h in hosts if h.enabled])
        disabled = total - enabled
        
        up = 0
        down = 0
        checking = 0
        
        for host in hosts:
            if not host.enabled:
                continue
            
            state = states.get(host.ip)
            if state:
                if state.status == "UP":
                    up += 1
                elif state.status == "DOWN":
                    down += 1
                elif state.status == "CHECKING":
                    checking += 1
        
        return {
            "total": total,
            "enabled": enabled,
            "disabled": disabled,
            "up": up,
            "down": down,
            "checking": checking
        }
