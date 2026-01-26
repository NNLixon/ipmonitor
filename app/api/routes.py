"""
API Routes Module
Defines all REST API endpoints
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from loguru import logger
import time
import ipaddress

from ..models import (
    Host, HostCreate, HostUpdate, HostResponse,
    SystemStatus, Stats, ConfigUpdate, ErrorResponse,
    GroupCreate, GroupUpdate, GroupResponse,
    SubnetScanRequest,
    BulkEnableRequest, BulkDeleteRequest, BulkGroupRequest,
    Notification, NotificationType,
    OTPValidationRequest, OTPValidationResponse  # ADDED IMPORT
)

from ..config import settings
from ..monitor.state_manager import StateManager
from ..monitor.ping_service import PingService
from ..monitor.notification_service import NotificationService
from ..utils.network_scanner import NetworkScanner


# Create router
router = APIRouter(prefix="/api", tags=["api"])

# Global instances (will be set by main app)
state_manager: StateManager = None
ping_service: PingService = None
notification_service: NotificationService = None
monitor_task = None
notifier_task = None
start_time = None


def set_services(sm: StateManager, ps: PingService, ns: NotificationService):
    """Set service instances"""
    global state_manager, ping_service, notification_service
    state_manager = sm
    ping_service = ps
    notification_service = ns


def set_monitor_task(task):
    """Set monitor task reference"""
    global monitor_task
    monitor_task = task


def set_notifier_task(task):
    """Set notifier task reference"""
    global notifier_task
    notifier_task = task


def set_start_time(ts):
    """Set application start time"""
    global start_time
    start_time = ts


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": int(time.time())}


@router.get("/status", response_model=SystemStatus)
async def get_status():
    """Get overall system status"""
    try:
        stats_data = await state_manager.get_statistics()
        
        is_running = (
            monitor_task is not None and
            not monitor_task.done()
        )
        
        uptime = None
        if start_time and is_running:
            uptime = int(time.time() - start_time)
        
        stats = Stats(**stats_data)
        
        return SystemStatus(
            is_running=is_running,
            stats=stats,
            uptime=uptime,
            recent_logs=[]
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/groups", response_model=List[GroupResponse])
async def get_groups():
    """Get all groups with host counts"""
    try:
        groups = await state_manager.load_groups()
        hosts = await state_manager.load_hosts()
        
        result = []
        for group_id, group in groups.items():
            # Count hosts in this group
            host_count = sum(1 for host in hosts if host.group_id == group_id)
            
            result.append(GroupResponse(
                id=group_id,
                name=group["name"],
                description=group.get("description"),
                color=group.get("color", "#3B82F6"),
                icon=group.get("icon", "🔵"),
                host_count=host_count,
                created_at=group["created_at"]
            ))
        
        # Sort by name
        result.sort(key=lambda x: x.name.lower())
        return result
        
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/groups", status_code=status.HTTP_201_CREATED)
async def create_group(group_data: GroupCreate):
    """Create a new group"""
    try:
        group_dict = group_data.model_dump()
        group_id = await state_manager.add_group(group_dict)
        
        return {
            "success": True, 
            "message": f"Group '{group_data.name}' created",
            "group_id": group_id
        }
            
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/groups/{group_id}")
async def update_group(group_id: int, group_data: GroupUpdate):
    """Update an existing group"""
    try:
        updates = group_data.model_dump(exclude_unset=True)
        
        if await state_manager.update_group(group_id, **updates):
            return {"success": True, "message": f"Group {group_id} updated"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group with ID {group_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/groups/{group_id}")
async def delete_group(group_id: int):
    """Delete a group"""
    try:
        groups = await state_manager.load_groups()
        group = groups.get(group_id)
        
        if await state_manager.delete_group(group_id):
            # Send notification if group existed
            if group:
                notification = Notification(
                    type=NotificationType.INFO,
                    ip="0.0.0.0",
                    name=f"Group Deleted: {group.get('name', f'Group {group_id}')}",
                    timestamp=int(time.time()),
                    extra=f"Group ID: {group_id}"
                )
                notification_service.queue_notification(notification)
            
            return {"success": True, "message": f"Group {group_id} deleted"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group with ID {group_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/hosts", response_model=List[HostResponse])
async def get_hosts(
    status_filter: Optional[str] = None,
    group_filter: Optional[int] = None,
    search: Optional[str] = None
):
    """Get all hosts with their current status"""
    try:
        hosts = await state_manager.load_hosts()
        states = await state_manager.load_states()
        groups = await state_manager.load_groups()
        
        result = []
        for host in hosts:
            state = states.get(host.ip)
            
            if state:
                last_check = state.get_last_check_str()
                downtime = state.get_downtime_minutes()
                fail_count = state.fail_count
                host_status = state.status
            else:
                last_check = "Never"
                downtime = 0
                fail_count = 0
                host_status = "UNKNOWN"
            
            # Get group info
            group_name = None
            group_color = None
            if host.group_id and host.group_id in groups:
                group = groups[host.group_id]
                group_name = group.get("name")
                group_color = group.get("color")
            
            # Apply filters
            if status_filter and status_filter.upper() != host_status:
                continue
                
            if group_filter and host.group_id != group_filter:
                continue
                
            if search and search.lower() not in host.name.lower() and search not in host.ip:
                continue
            
            result.append(HostResponse(
                id=hash(host.ip) & 0xFFFFFFFF,
                ip=host.ip,
                name=host.name,
                status=host_status,
                lastCheck=last_check,
                downtime=downtime,
                failCount=fail_count,
                enabled=host.enabled,
                tags=host.tags,
                group_id=host.group_id,
                group_name=group_name,
                group_color=group_color,
                mac_address=host.mac_address,
                vendor_info=host.vendor_info
            ))
        
        # Sort by status (UP first), then by name
        status_order = {"UP": 0, "CHECKING": 1, "UNKNOWN": 2, "DOWN": 3}
        result.sort(key=lambda x: (status_order.get(x.status.upper(), 4), x.name.lower()))
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting hosts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/hosts", status_code=status.HTTP_201_CREATED)
async def create_host(host_data: HostCreate):
    """Create a new host"""
    try:
        # Check if it's a subnet
        if '/' in host_data.ip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use /api/subnet/scan endpoint for subnet scanning"
            )
        
        host = Host(**host_data.model_dump())
        
        # Validate group exists if specified
        if host.group_id:
            groups = await state_manager.load_groups()
            if host.group_id not in groups:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Group with ID {host.group_id} does not exist"
                )
        
        if await state_manager.add_host(host):
            # Send notification for new host
            notification = Notification(
                type=NotificationType.NEW_IP,
                ip=host.ip,
                name=host.name,
                timestamp=int(time.time()),
                extra=f"Added manually. Group: {host.group_id}" if host.group_id else "Added manually"
            )
            notification_service.queue_notification(notification)
            
            logger.info(f"Added new host: {host.name} ({host.ip})")
            
            return {"success": True, "message": f"Host {host.name} added"}
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Host with IP {host.ip} already exists"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating host: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/hosts/{ip}")
async def update_host(ip: str, host_data: HostUpdate):
    """Update an existing host"""
    try:
        # Get current host info
        current_host = await state_manager.get_host(ip)
        if not current_host:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Host with IP {ip} not found"
            )
        
        updates = host_data.model_dump(exclude_unset=True)
        
        # Validate group exists if specified
        if 'group_id' in updates and updates['group_id'] is not None:
            groups = await state_manager.load_groups()
            if updates['group_id'] not in groups:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Group with ID {updates['group_id']} does not exist"
                )
        
        if await state_manager.update_host(ip, **updates):
            # Send notification for host update
            notification_extra = []
            if 'name' in updates and updates['name'] != current_host.name:
                notification_extra.append(f"Renamed: {current_host.name} → {updates['name']}")
            if 'enabled' in updates:
                status_text = "Enabled" if updates['enabled'] else "Disabled"
                notification_extra.append(f"Status: {status_text}")
            if 'group_id' in updates:
                if updates['group_id']:
                    groups = await state_manager.load_groups()
                    group_name = groups.get(updates['group_id'], {}).get('name', f'Group {updates["group_id"]}')
                    notification_extra.append(f"Group: {group_name}")
                else:
                    notification_extra.append("Group: Removed")
            
            if notification_extra:
                notification = Notification(
                    type=NotificationType.INFO,
                    ip=ip,
                    name=f"Host Updated: {updates.get('name', current_host.name)}",
                    timestamp=int(time.time()),
                    extra=" | ".join(notification_extra)
                )
                notification_service.queue_notification(notification)
            
            return {"success": True, "message": f"Host {ip} updated"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update host"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating host: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/hosts/{ip}")
async def delete_host(ip: str):
    """Delete a host"""
    try:
        # Get host info before deleting
        host = await state_manager.get_host(ip)
        if not host:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Host with IP {ip} not found"
            )
        
        if await state_manager.delete_host(ip):
            # Also delete state
            await state_manager.delete_state(ip)
            
            # Send notification for host deletion
            notification = Notification(
                type=NotificationType.INFO,
                ip=ip,
                name=f"Host Deleted: {host.name}",
                timestamp=int(time.time()),
                extra=f"IP: {ip} | Was {'enabled' if host.enabled else 'disabled'}"
            )
            notification_service.queue_notification(notification)
            
            logger.info(f"Deleted host: {host.name} ({ip})")
            
            return {"success": True, "message": f"Host {ip} deleted"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete host"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting host: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/hosts/bulk/enable")
async def bulk_enable_hosts(request: BulkEnableRequest):
    """Bulk enable/disable hosts"""
    try:
        success_count = 0
        fail_count = 0
        affected_hosts = []
        
        for ip in request.ips:
            host = await state_manager.get_host(ip)
            if host:
                # Update the host
                if await state_manager.update_host(ip, enabled=request.enabled):
                    success_count += 1
                    affected_hosts.append(host.name)
                    
                    # If disabling, also update the state to prevent false notifications
                    if not request.enabled:
                        state = await state_manager.get_state(ip)
                        if state:
                            state.status = "UNKNOWN"
                            state.fail_count = 0
                            await state_manager.update_state(ip, state)
                else:
                    fail_count += 1
            else:
                fail_count += 1
        
        message = f"Updated {success_count} host(s)"
        if fail_count > 0:
            message += f", failed to update {fail_count} host(s)"
        
        # Send notification for bulk operation
        if success_count > 0:
            status_text = "Enabled" if request.enabled else "Disabled"
            notification = Notification(
                type=NotificationType.INFO,
                ip="0.0.0.0",
                name=f"Bulk Operation: {status_text} {success_count} Host(s)",
                timestamp=int(time.time()),
                extra=f"Affected hosts: {', '.join(affected_hosts[:5])}" + 
                      (f" and {len(affected_hosts) - 5} more..." if len(affected_hosts) > 5 else "")
            )
            notification_service.queue_notification(notification)
        
        return {
            "success": True,
            "message": message,
            "updated": success_count,
            "failed": fail_count
        }
        
    except Exception as e:
        logger.error(f"Error in bulk enable: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/hosts/bulk/delete")
async def bulk_delete_hosts(request: BulkDeleteRequest):
    """Bulk delete hosts"""
    try:
        success_count = 0
        fail_count = 0
        deleted_hosts = []
        
        for ip in request.ips:
            host = await state_manager.get_host(ip)
            if host:
                # Delete host
                if await state_manager.delete_host(ip):
                    # Delete state
                    await state_manager.delete_state(ip)
                    success_count += 1
                    deleted_hosts.append(host.name)
                else:
                    fail_count += 1
            else:
                fail_count += 1
        
        message = f"Deleted {success_count} host(s)"
        if fail_count > 0:
            message += f", failed to delete {fail_count} host(s)"
        
        # Send notification for bulk deletion
        if success_count > 0:
            notification = Notification(
                type=NotificationType.INFO,
                ip="0.0.0.0",
                name=f"Bulk Deletion: Removed {success_count} Host(s)",
                timestamp=int(time.time()),
                extra=f"Deleted: {', '.join(deleted_hosts[:5])}" + 
                      (f" and {len(deleted_hosts) - 5} more..." if len(deleted_hosts) > 5 else "")
            )
            notification_service.queue_notification(notification)
        
        return {
            "success": True,
            "message": message,
            "deleted": success_count,
            "failed": fail_count
        }
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/hosts/bulk/group")
async def bulk_update_group(request: BulkGroupRequest):
    """Bulk update host groups"""
    try:
        # Validate group exists if specified
        group_name = None
        if request.group_id:
            groups = await state_manager.load_groups()
            if request.group_id not in groups:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Group with ID {request.group_id} does not exist"
                )
            group_name = groups.get(request.group_id, {}).get('name', f'Group {request.group_id}')
        
        success_count = 0
        fail_count = 0
        moved_hosts = []
        
        for ip in request.ips:
            host = await state_manager.get_host(ip)
            if host:
                # Update the host's group
                if await state_manager.update_host(ip, group_id=request.group_id):
                    success_count += 1
                    moved_hosts.append(host.name)
                else:
                    fail_count += 1
            else:
                fail_count += 1
        
        if request.group_id:
            message = f"Moved {success_count} host(s) to {group_name}"
        else:
            message = f"Removed group from {success_count} host(s)"
            
        if fail_count > 0:
            message += f", failed to update {fail_count} host(s)"
        
        # Send notification for bulk group update
        if success_count > 0:
            action = f"Moved to {group_name}" if request.group_id else "Removed from groups"
            notification = Notification(
                type=NotificationType.INFO,
                ip="0.0.0.0",
                name=f"Bulk Group Update: {action}",
                timestamp=int(time.time()),
                extra=f"Affected: {', '.join(moved_hosts[:5])}" + 
                      (f" and {len(moved_hosts) - 5} more..." if len(moved_hosts) > 5 else "")
            )
            notification_service.queue_notification(notification)
        
        return {
            "success": True,
            "message": message,
            "updated": success_count,
            "failed": fail_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk group update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/subnet/scan")
async def scan_subnet(scan_request: SubnetScanRequest, background_tasks: BackgroundTasks):
    """Scan a subnet and add all discovered hosts"""
    try:
        # Parse subnet
        try:
            network = ipaddress.ip_network(scan_request.subnet, strict=False)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subnet format: {e}"
            )
        
        # Create group for the subnet if not specified
        group_id = None
        if not scan_request.group_name:
            group_name = f"Subnet {scan_request.subnet}"
        else:
            group_name = scan_request.group_name
        
        # Check if group already exists
        groups = await state_manager.load_groups()
        existing_group = next((gid for gid, g in groups.items() if g["name"] == group_name), None)
        
        if existing_group:
            group_id = existing_group
        else:
            # Create new group
            group_id = await state_manager.add_group({
                "name": group_name,
                "description": f"Auto-generated from subnet {scan_request.subnet}",
                "color": scan_request.group_color,
                "icon": scan_request.group_icon
            })
            
            # Send notification for new group creation
            notification = Notification(
                type=NotificationType.INFO,
                ip="0.0.0.0",
                name=f"New Group Created: {group_name}",
                timestamp=int(time.time()),
                extra=f"For subnet: {scan_request.subnet}"
            )
            notification_service.queue_notification(notification)
        
        # Send start notification
        notification = Notification(
            type=NotificationType.INFO,
            ip="0.0.0.0",
            name="Subnet Scan Started",
            timestamp=int(time.time()),
            extra=f"Scanning {scan_request.subnet} | Total IPs: {network.num_addresses - 2 if network.prefixlen < 31 else network.num_addresses}"
        )
        notification_service.queue_notification(notification)
        
        # Scan subnet in background
        background_tasks.add_task(
            _perform_subnet_scan,
            scan_request.subnet,
            group_id,
            scan_request.scan_mac,
            group_name
        )
        
        return {
            "success": True,
            "message": f"Started scanning subnet {scan_request.subnet}",
            "subnet": scan_request.subnet,
            "group_id": group_id,
            "group_name": group_name,
            "total_ips": network.num_addresses - 2 if network.prefixlen < 31 else network.num_addresses
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning subnet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def _perform_subnet_scan(subnet: str, group_id: int, scan_mac: bool, group_name: str):
    """Background task to perform subnet scanning"""
    try:
        logger.info(f"Starting subnet scan: {subnet}")
        
        # Get existing hosts to avoid duplicates
        existing_hosts = await state_manager.load_hosts()
        existing_ips = {host.ip for host in existing_hosts}
        
        # Parse subnet IPs
        ips = NetworkScanner.parse_subnet(subnet)
        logger.info(f"Found {len(ips)} IPs in subnet {subnet}")
        
        added_count = 0
        skipped_count = 0
        
        for ip in ips:
            try:
                # Skip if already exists
                if ip in existing_ips:
                    skipped_count += 1
                    continue
                
                # Get MAC address if requested
                mac_address = None
                vendor_info = None
                
                if scan_mac:
                    mac_address, vendor_info = await NetworkScanner.get_mac_address(ip)
                
                # Generate host name
                name = NetworkScanner.generate_host_name(ip, mac_address, vendor_info)
                
                # Create host
                host = Host(
                    ip=ip,
                    name=name,
                    enabled=True,
                    tags=[f"subnet-{subnet.replace('/', '-')}"],
                    group_id=group_id,
                    mac_address=mac_address,
                    vendor_info=vendor_info
                )
                
                # Add host
                if await state_manager.add_host(host):
                    added_count += 1
                    logger.info(f"Added host: {name} ({ip})")
                    
                    # Send notification for new host
                    notification_service.queue_notification(
                        Notification(
                            type=NotificationType.NEW_IP,
                            ip=ip,
                            name=name,
                            timestamp=int(time.time()),
                            extra=f"Auto-detected from subnet {subnet} | Group: {group_name}"
                        )
                    )
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing IP {ip}: {e}")
                continue
        
        logger.info(f"Subnet scan complete: {added_count} added, {skipped_count} skipped")
        
        # Send summary notification
        if added_count > 0:
            notification_service.queue_notification(
                Notification(
                    type=NotificationType.INFO,
                    ip="0.0.0.0",
                    name="Subnet Scan Complete",
                    timestamp=int(time.time()),
                    extra=f"Added {added_count} hosts from subnet {subnet} to group '{group_name}'"
                )
            )
        else:
            notification_service.queue_notification(
                Notification(
                    type=NotificationType.INFO,
                    ip="0.0.0.0",
                    name="Subnet Scan Complete",
                    timestamp=int(time.time()),
                    extra=f"No new hosts found in subnet {subnet}"
                )
            )
        
    except Exception as e:
        logger.error(f"Error in subnet scan: {e}")
        notification_service.queue_notification(
            Notification(
                type=NotificationType.ERROR,
                ip="0.0.0.0",
                name="Subnet Scan Failed",
                timestamp=int(time.time()),
                extra=f"Subnet: {subnet} | Error: {str(e)}"
            )
        )


@router.get("/subnet/preview/{subnet}")
async def preview_subnet(subnet: str):
    """Preview IPs in a subnet without scanning"""
    try:
        ips = NetworkScanner.parse_subnet(subnet)
        
        return {
            "success": True,
            "subnet": subnet,
            "total_ips": len(ips),
            "ips": ips[:50],  # Return first 50 IPs for preview
            "note": f"Showing first 50 of {len(ips)} IPs" if len(ips) > 50 else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid subnet: {e}"
        )


@router.get("/config")
async def get_config():
    """Get current configuration"""
    try:
        return {
            "webhook_url": settings.discord_webhook_url,
            "ping_interval": settings.ping_interval,
            "max_retries": settings.max_retries,
            "ping_timeout": settings.ping_timeout,
            "concurrent_pings": settings.concurrent_pings,
            "check_interval": settings.check_interval,
            "batch_interval": settings.batch_interval,
            "max_batch_size": settings.max_batch_size
        }
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/config")
async def update_config(config_data: ConfigUpdate):
    """Update configuration"""
    try:
        old_webhook = settings.discord_webhook_url
        updates = config_data.model_dump(exclude_unset=True)
        
        # Update settings in memory and save to file
        settings.update(**updates)
        
        # If webhook URL changed, update notification service
        if 'discord_webhook_url' in updates:
            notification_service.webhook_url = updates['discord_webhook_url']
            
            # Send notification about webhook change
            if old_webhook and not updates['discord_webhook_url']:
                # Webhook removed
                notification = Notification(
                    type=NotificationType.INFO,
                    ip="0.0.0.0",
                    name="Discord Webhook Removed",
                    timestamp=int(time.time()),
                    extra="Notifications disabled"
                )
                # Note: This won't be sent since webhook is removed
                logger.info("Discord webhook removed. Notifications disabled.")
            elif not old_webhook and updates['discord_webhook_url']:
                # Webhook added
                notification = Notification(
                    type=NotificationType.INFO,
                    ip="0.0.0.0",
                    name="Discord Webhook Added",
                    timestamp=int(time.time()),
                    extra="Notifications enabled"
                )
                notification_service.queue_notification(notification)
            elif old_webhook and updates['discord_webhook_url'] and old_webhook != updates['discord_webhook_url']:
                # Webhook changed
                notification = Notification(
                    type=NotificationType.INFO,
                    ip="0.0.0.0",
                    name="Discord Webhook Updated",
                    timestamp=int(time.time()),
                    extra="Webhook URL changed"
                )
                notification_service.queue_notification(notification)
            
            # Validate new webhook if it exists
            if updates['discord_webhook_url']:
                await notification_service.validate_webhook()
        
        # Send notification for other config changes
        if any(key in updates for key in ['ping_interval', 'max_retries', 'batch_interval', 'max_batch_size']):
            changes = []
            for key in ['ping_interval', 'max_retries', 'batch_interval', 'max_batch_size']:
                if key in updates:
                    changes.append(f"{key.replace('_', ' ').title()}: {updates[key]}")
            
            if changes:
                notification = Notification(
                    type=NotificationType.INFO,
                    ip="0.0.0.0",
                    name="Configuration Updated",
                    timestamp=int(time.time()),
                    extra=" | ".join(changes)
                )
                notification_service.queue_notification(notification)
        
        return {"success": True, "message": "Configuration updated"}
        
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/config/reload")
async def reload_config():
    """Reload configuration from file"""
    try:
        # Reload settings from file
        settings.reload()
        
        # Update notification service
        notification_service.reload_config()
        
        # Validate webhook if set
        if settings.discord_webhook_url:
            await notification_service.validate_webhook()
        
        # Send notification
        notification = Notification(
            type=NotificationType.INFO,
            ip="0.0.0.0",
            name="Configuration Reloaded",
            timestamp=int(time.time()),
            extra="Settings reloaded from file"
        )
        notification_service.queue_notification(notification)
        
        return {"success": True, "message": "Configuration reloaded"}
        
    except Exception as e:
        logger.error(f"Error reloading config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ADDED: OTP Validation Endpoints
@router.post("/webhook/validate", response_model=OTPValidationResponse)
async def validate_webhook_start():
    """Start webhook validation by sending OTP"""
    try:
        # Get webhook URL from settings or request body
        webhook_url = settings.discord_webhook_url
        
        if not webhook_url:
            return OTPValidationResponse(
                success=False,
                message="No webhook URL configured. Please set a webhook URL first."
            )
        
        success, message, otp = await notification_service.validate_webhook_with_otp(webhook_url)
        
        if success:
            return OTPValidationResponse(
                success=True,
                message=message,
                expires_in=600  # 10 minutes
            )
        else:
            return OTPValidationResponse(
                success=False,
                message=message
            )
            
    except Exception as e:
        logger.error(f"Error starting webhook validation: {e}")
        return OTPValidationResponse(
            success=False,
            message=f"Error: {str(e)}"
        )


@router.post("/webhook/verify", response_model=OTPValidationResponse)
async def verify_webhook_otp(otp_request: OTPValidationRequest):
    """Verify OTP for webhook validation"""
    try:
        webhook_url = settings.discord_webhook_url
        
        if not webhook_url:
            return OTPValidationResponse(
                success=False,
                message="No webhook URL configured"
            )
        
        success, message = await notification_service.verify_otp(webhook_url, otp_request.otp)
        
        return OTPValidationResponse(
            success=success,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        return OTPValidationResponse(
            success=False,
            message=f"Error: {str(e)}"
        )


@router.post("/monitor/start")
async def start_monitoring():
    """Start the monitoring process"""
    global monitor_task, notifier_task, start_time
    
    try:
        if monitor_task and not monitor_task.done():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monitor is already running"
            )
        
        # Import asyncio to create tasks
        import asyncio
        
        # Reset stop events
        ping_service.reset()
        notification_service.reset()
        
        # Get host count
        hosts = await state_manager.load_hosts()
        logger.info(f"Starting monitoring for {len(hosts)} hosts")
        
        # Send startup notification
        await notification_service.send_startup_notification(len(hosts))
        
        # Define callback functions
        async def get_hosts():
            return await state_manager.load_hosts()
        
        async def get_states():
            return await state_manager.load_states()
        
        async def save_states(states):
            await state_manager.save_states(states)
        
        async def handle_notifications(notifications):
            notification_service.queue_notifications(notifications)
        
        # Start monitoring tasks
        monitor_task = asyncio.create_task(
            ping_service.continuous_monitor(
                get_hosts,
                get_states,
                save_states,
                handle_notifications
            )
        )
        
        notifier_task = asyncio.create_task(
            notification_service.continuous_sender()
        )
        
        start_time = time.time()
        
        logger.info("✓ Monitoring started from dashboard")
        
        return {"success": True, "message": "Monitor started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting monitor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/monitor/stop")
async def stop_monitoring():
    """Stop the monitoring process"""
    global monitor_task, notifier_task
    
    try:
        if not monitor_task or monitor_task.done():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monitor is not running"
            )
        
        # Get host count for notification
        hosts = await state_manager.load_hosts()
        host_count = len(hosts)
        
        # Stop services
        ping_service.stop()
        notification_service.stop()
        
        # Cancel tasks
        if monitor_task and not monitor_task.done():
            monitor_task.cancel()
        
        if notifier_task and notifier_task and not notifier_task.done():
            notifier_task.cancel()
        
        # Send shutdown notification
        await notification_service.send_shutdown_notification()
        
        logger.info(f"✓ Monitoring stopped. Was monitoring {host_count} hosts.")
        
        return {"success": True, "message": "Monitor stopped"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping monitor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries"""
    try:
        log_file = settings.log_dir / "monitor.log"
        
        if not log_file.exists():
            return []
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
            
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
