#!/usr/bin/env python3
"""
Main Application Entry Point
Starts FastAPI web server with integrated monitoring
"""

import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from loguru import logger
import time
import sys
from pathlib import Path

from app.config import settings
from app.monitor.ping_service import PingService
from app.monitor.state_manager import StateManager
from app.monitor.notification_service import NotificationService
from app.api import routes
from app.api.websocket import websocket_endpoint, manager


# Global service instances
state_manager = StateManager()
ping_service = PingService()
notification_service = NotificationService()

# Task references
monitor_task = None
notifier_task = None
start_time = None


def setup_logging():
    """Configure logging"""
    logger.remove()  # Remove default handler
    
    # Console logging
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # File logging
    log_file = settings.log_dir / "monitor.log"
    logger.add(
        log_file,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )


async def start_monitoring():
    """Start monitoring services"""
    global monitor_task, notifier_task, start_time
    
    logger.info("=" * 60)
    logger.info("Starting IP Monitor Services")
    logger.info("=" * 60)
    
    # Initialize notification service
    await notification_service.initialize()
    
    # Only validate webhook if it exists
    if settings.discord_webhook_url:
        await notification_service.validate_webhook()
    
    # Get host count
    hosts = await state_manager.load_hosts()
    logger.info(f"Loaded {len(hosts)} hosts")
    
    # Only send startup notification if webhook is configured
    if settings.discord_webhook_url:
        await notification_service.send_startup_notification(len(hosts))
    else:
        logger.info("Discord webhook not configured. Notifications disabled.")
    
    # Define callback functions
    async def get_hosts():
        return await state_manager.load_hosts()
    
    async def get_states():
        return await state_manager.load_states()
    
    async def save_states(states):
        await state_manager.save_states(states)
        # Broadcast update to WebSocket clients
        hosts = await get_hosts()
        hosts_data = []
        for host in hosts:
            state = states.get(host.ip)
            if state:
                hosts_data.append({
                    "ip": host.ip,
                    "name": host.name,
                    "status": state.status,
                    "lastCheck": state.get_last_check_str(),
                    "downtime": state.get_downtime_minutes()
                })
        await manager.broadcast_host_update(hosts_data)
    
    async def handle_notifications(notifications):
        # Only queue notifications if webhook is configured
        if settings.discord_webhook_url:
            notification_service.queue_notifications(notifications)
        elif notifications:
            logger.debug(f"Notifications skipped (no webhook): {len(notifications)}")
    
    # Start monitoring loop
    monitor_task = asyncio.create_task(
        ping_service.continuous_monitor(
            get_hosts,
            get_states,
            save_states,
            handle_notifications
        )
    )
    
    # Start notification sender loop only if webhook is configured
    if settings.discord_webhook_url:
        notifier_task = asyncio.create_task(
            notification_service.continuous_sender()
        )
    else:
        logger.info("Notification sender loop not started (no webhook configured)")
        notifier_task = None
    
    start_time = time.time()
    
    # Set task references in routes module
    routes.set_monitor_task(monitor_task)
    routes.set_notifier_task(notifier_task)
    routes.set_start_time(start_time)
    
    logger.info("✓ Monitoring services started")
    logger.info(f"✓ Ping interval: {settings.ping_interval}s")
    logger.info(f"✓ Max retries: {settings.max_retries}")
    logger.info(f"✓ Concurrent pings: {settings.concurrent_pings}")
    logger.info(f"✓ Discord notifications: {'Enabled' if settings.discord_webhook_url else 'Disabled'}")
    logger.info("=" * 60)


async def stop_monitoring():
    """Stop monitoring services"""
    global monitor_task, notifier_task
    
    logger.info("Stopping monitoring services...")
    
    # Stop services
    ping_service.stop()
    notification_service.stop()
    
    # Cancel tasks
    if monitor_task and not monitor_task.done():
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
    
    if notifier_task and notifier_task and not notifier_task.done():
        notifier_task.cancel()
        try:
            await notifier_task
        except asyncio.CancelledError:
            pass
    
    # Close notification service
    await notification_service.close()
    
    logger.info("✓ Monitoring services stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    setup_logging()
    logger.info("Starting IP Monitor Dashboard")
    
    # Set service instances in routes
    routes.set_services(state_manager, ping_service, notification_service)
    
    # Start monitoring
    await start_monitoring()
    
    yield
    
    # Shutdown
    logger.info("Shutting down IP Monitor Dashboard")
    await stop_monitoring()


# Create FastAPI app
app = FastAPI(
    title="IP Monitor Dashboard",
    description="Asynchronous IP monitoring system with real-time dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(routes.router)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_route(websocket):
    await websocket_endpoint(websocket)

# Mount static files
static_dir = Path(__file__).parent / "app" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Serve index.html at root
@app.get("/")
async def read_root():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "IP Monitor Dashboard - API is running"}


def main():
    """Main entry point"""
    logger.info(f"Dashboard URL: http://{settings.host}:{settings.port}")
    logger.info(f"API URL: http://{settings.host}:{settings.port}/api")
    logger.info(f"WebSocket URL: ws://{settings.host}:{settings.port}/ws")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
