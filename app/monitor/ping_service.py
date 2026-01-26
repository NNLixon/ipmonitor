"""
Async Ping Service Module
Handles asynchronous ping operations
"""

import asyncio
from typing import Dict, List, Tuple
from loguru import logger
from ..config import settings
from ..models import Host, HostState, HostStatus, Notification, NotificationType
import time


class PingService:
    """Asynchronous ping service"""
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.concurrent_pings)
        self.notification_queue: List[Notification] = []
        self._stop_event = asyncio.Event()
    
    async def ping(self, ip: str) -> bool:
        """
        Ping a single IP address asynchronously
        
        Args:
            ip: IP address to ping
            
        Returns:
            bool: True if ping successful, False otherwise
        """
        async with self.semaphore:
            try:
                process = await asyncio.create_subprocess_exec(
                    'ping', '-c', '1', '-W', str(settings.ping_timeout), ip,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                
                await asyncio.wait_for(
                    process.wait(),
                    timeout=settings.ping_timeout + 1
                )
                
                return process.returncode == 0
                
            except asyncio.TimeoutError:
                logger.debug(f"Ping timeout for {ip}")
                return False
            except Exception as e:
                logger.error(f"Ping error for {ip}: {e}")
                return False
    
    async def ping_batch(self, hosts: List[Host]) -> Dict[str, bool]:
        """
        Ping multiple hosts concurrently
        
        Args:
            hosts: List of hosts to ping
            
        Returns:
            Dict mapping IP to ping success status
        """
        if not hosts:
            return {}
        
        # Filter enabled hosts only
        enabled_hosts = [h for h in hosts if h.enabled]
        
        logger.info(f"Pinging {len(enabled_hosts)} hosts...")
        
        # Create ping tasks
        tasks = [self._ping_with_ip(host.ip) for host in enabled_hosts]
        
        # Execute all pings concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build results dictionary
        ping_results = {}
        for host, result in zip(enabled_hosts, results):
            if isinstance(result, Exception):
                logger.error(f"Ping exception for {host.ip}: {result}")
                ping_results[host.ip] = False
            else:
                ping_results[host.ip] = result
        
        up_count = sum(1 for v in ping_results.values() if v)
        logger.info(f"Ping results: {up_count}/{len(ping_results)} hosts up")
        
        return ping_results
    
    async def _ping_with_ip(self, ip: str) -> bool:
        """Helper to ping and return result with IP"""
        return await self.ping(ip)
    
    def update_state(
        self,
        host: Host,
        state: HostState,
        ping_success: bool
    ) -> Tuple[HostState, List[Notification]]:
        """
        Update host state based on ping result
        Only sends notifications on state changes (UP->DOWN or DOWN->UP)
        
        Args:
            host: Host object
            state: Current host state
            ping_success: Whether ping was successful
            
        Returns:
            Tuple of (updated_state, notifications)
        """
        current_time = int(time.time())
        notifications = []
        
        # Update basic info
        state.last_check = current_time
        state.name = host.name  # Keep name in sync
        
        # Store previous status before update
        previous_status = state.status
        
        if ping_success:
            # Ping successful
            if state.status == HostStatus.DOWN:
                # STATE CHANGE: DOWN -> UP (Recovery!)
                downtime_minutes = state.get_downtime_minutes()
                
                logger.info(
                    f"✓ RECOVERED: {state.name} ({state.ip}) - "
                    f"Downtime: {downtime_minutes}m"
                )
                
                # Add to total downtime
                if state.fail_time:
                    state.total_downtime += (current_time - state.fail_time)
                
                # Create recovery notification (ONLY ONCE on state change)
                notifications.append(Notification(
                    type=NotificationType.RECOVERED,
                    ip=state.ip,
                    name=state.name,
                    timestamp=current_time,
                    extra=str(downtime_minutes)
                ))
                
                # Update state
                state.status = HostStatus.UP
                state.fail_count = 0
                state.fail_time = None
                state.last_up = current_time
                
            elif state.fail_count > 0:
                # Was failing but recovered before threshold
                # No state change, no notification needed
                state.fail_count = 0
                if state.status != HostStatus.UP:
                    state.status = HostStatus.UP
                    state.last_up = current_time
            # else: Already UP, stay UP, no notification
        
        else:
            # Ping failed
            state.fail_count += 1
            
            # Only send notification when crossing threshold from UP to DOWN
            # Or if already DOWN and we just detected another failure (but don't spam)
            if state.fail_count >= settings.max_retries:
                if state.status == HostStatus.UP:
                    # STATE CHANGE: UP -> DOWN (Failure!)
                    logger.warning(
                        f"✗ FAILED: {state.name} ({state.ip}) - "
                        f"After {settings.max_retries} attempts"
                    )
                    
                    # Create failure notification (ONLY ONCE on state change)
                    notifications.append(Notification(
                        type=NotificationType.FAILED,
                        ip=state.ip,
                        name=state.name,
                        timestamp=current_time,
                        extra=f"Failed after {state.fail_count} attempts"
                    ))
                    
                    # Update state
                    state.status = HostStatus.DOWN
                    state.fail_time = current_time
                elif state.status == HostStatus.DOWN and previous_status == HostStatus.UP:
                    # Already marked as DOWN from previous check, no repeated notification
                    pass
                elif state.status == HostStatus.UNKNOWN:
                    # UNKNOWN host that has now failed max_retries times
                    logger.warning(
                        f"✗ FAILED (from UNKNOWN): {state.name} ({state.ip}) - "
                        f"After {settings.max_retries} attempts"
                    )
                    
                    # Create failure notification for UNKNOWN->DOWN transition
                    notifications.append(Notification(
                        type=NotificationType.FAILED,
                        ip=state.ip,
                        name=state.name,
                        timestamp=current_time,
                        extra=f"Failed after {state.fail_count} attempts (initial detection)"
                    ))
                    
                    # Update state
                    state.status = HostStatus.DOWN
                    state.fail_time = current_time
        
        return state, notifications
    
    async def monitor_cycle(
        self,
        hosts: List[Host],
        states: Dict[str, HostState]
    ) -> Tuple[Dict[str, HostState], List[Notification]]:
        """
        Perform one complete monitoring cycle
        
        Args:
            hosts: List of hosts to monitor
            states: Current states dictionary
            
        Returns:
            Tuple of (updated_states, notifications)
        """
        # Ping all hosts
        ping_results = await self.ping_batch(hosts)
        
        # Update states
        all_notifications = []
        updated_states = {}
        
        for host in hosts:
            if not host.enabled:
                # Keep disabled hosts in states but don't update
                if host.ip in states:
                    updated_states[host.ip] = states[host.ip]
                continue
            
            # Get or create state
            if host.ip in states:
                state = states[host.ip]
            else:
                # NEW HOST: Initialize with UNKNOWN status
                state = HostState(ip=host.ip, name=host.name, status=HostStatus.UNKNOWN)
                logger.info(f"New host added to monitoring: {host.name} ({host.ip})")
            
            # Get ping result
            ping_success = ping_results.get(host.ip, False)
            
            # For new hosts (UNKNOWN status), set initial status based on first ping
            if state.status == HostStatus.UNKNOWN:
                if ping_success:
                    state.status = HostStatus.UP
                    state.last_up = int(time.time())
                    logger.info(f"Initial status for {host.name} ({host.ip}): UP")
                    # Send new host notification
                    all_notifications.append(Notification(
                        type=NotificationType.NEW_IP,
                        ip=host.ip,
                        name=host.name,
                        timestamp=int(time.time()),
                        extra="Initial detection"
                    ))
                else:
                    # First ping failed, increment fail_count and check if we should mark as DOWN
                    state.fail_count += 1
                    state.last_check = int(time.time())
                    
                    # Check if we've already failed max_retries times
                    if state.fail_count >= settings.max_retries:
                        logger.warning(
                            f"✗ FAILED (from UNKNOWN): {host.name} ({host.ip}) - "
                            f"After {state.fail_count} attempts"
                        )
                        
                        # Create failure notification
                        all_notifications.append(Notification(
                            type=NotificationType.FAILED,
                            ip=host.ip,
                            name=host.name,
                            timestamp=int(time.time()),
                            extra=f"Failed after {state.fail_count} attempts (initial detection)"
                        ))
                        
                        state.status = HostStatus.DOWN
                        state.fail_time = int(time.time())
                    else:
                        logger.info(f"Initial ping failed for {host.name} ({host.ip}), count: {state.fail_count}/{settings.max_retries}")
                
                updated_states[host.ip] = state
                continue
            
            # Update state for existing hosts
            updated_state, notifications = self.update_state(
                host, state, ping_success
            )
            
            updated_states[host.ip] = updated_state
            all_notifications.extend(notifications)
        
        # Queue notifications
        self.notification_queue.extend(all_notifications)
        
        return updated_states, all_notifications
    
    def get_queued_notifications(self) -> List[Notification]:
        """Get and clear notification queue"""
        notifications = self.notification_queue.copy()
        self.notification_queue.clear()
        return notifications
    
    async def continuous_monitor(
        self,
        hosts_getter,
        states_getter,
        states_setter,
        notification_callback
    ):
        """
        Continuous monitoring loop
        
        Args:
            hosts_getter: Async function to get current hosts
            states_getter: Async function to get current states
            states_setter: Async function to save states
            notification_callback: Async function to handle notifications
        """
        logger.info("Starting continuous monitoring loop")
        
        while not self._stop_event.is_set():
            try:
                # Get current hosts and states
                hosts = await hosts_getter()
                states = await states_getter()
                
                # Perform monitoring cycle
                updated_states, notifications = await self.monitor_cycle(
                    hosts, states
                )
                
                # Save updated states
                await states_setter(updated_states)
                
                # Handle notifications
                if notifications:
                    await notification_callback(notifications)
                
                # Wait for next cycle
                await asyncio.sleep(settings.ping_interval)
                
            except asyncio.CancelledError:
                logger.info("Monitor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retry
        
        logger.info("Monitoring loop stopped")
    
    def stop(self):
        """Stop the monitoring loop"""
        self._stop_event.set()
    
    def reset(self):
        """Reset the stop event (for restarting)"""
        self._stop_event.clear()
