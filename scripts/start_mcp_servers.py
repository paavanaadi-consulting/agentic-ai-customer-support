#!/usr/bin/env python3
"""
MCP Server Manager - Start and manage MCP servers
"""
import asyncio
import os
import sys
import signal
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/mcp_servers.log')
    ]
)
logger = logging.getLogger(__name__)

# Import MCP servers
from mcp.postgres_mcp_wrapper import PostgresMCPWrapper
from mcp.kafka_mcp_wrapper import KafkaMCPWrapper, ExternalKafkaMCPConfig
from mcp.aws_mcp_wrapper import AWSMCPWrapper, ExternalMCPConfig
from data_sources.rdbms_connector import RDBMSConnector


class MCPServerManager:
    """Manages multiple MCP servers"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.servers = {}
        self.running = False
        self.config = self._load_config(config_path)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or environment"""
        if config_path and os.path.exists(config_path):
            import json
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration from environment
        return {
            "database": {
                "enabled": os.getenv("MCP_DATABASE_ENABLED", "true").lower() == "true",
                "port": int(os.getenv("MCP_DATABASE_PORT", "8001")),
                "host": os.getenv("MCP_DATABASE_HOST", "localhost"),
                "database_url": os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/customer_support")
            },
            "kafka": {
                "enabled": os.getenv("MCP_KAFKA_ENABLED", "true").lower() == "true",
                "port": int(os.getenv("MCP_KAFKA_PORT", "8002")),
                "host": os.getenv("MCP_KAFKA_HOST", "localhost"),
                "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            },
            "aws": {
                "enabled": os.getenv("MCP_AWS_ENABLED", "true").lower() == "true",
                "port": int(os.getenv("MCP_AWS_PORT", "8003")),
                "host": os.getenv("MCP_AWS_HOST", "localhost"),
                "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            }
        }
    
    async def start_database_server(self) -> bool:
        """Start the database MCP server"""
        if not self.config["database"]["enabled"]:
            logger.info("Database MCP server disabled")
            return True
        
        try:
            logger.info("Starting Database MCP server...")
            
            # Create database connector
            db_connector = RDBMSConnector()
            await db_connector.connect()
            
            # Create and start wrapper
            server = PostgresMCPWrapper()
            await server.initialize()
            
            self.servers["database"] = server
            logger.info(f"Database MCP wrapper started on port {self.config['database']['port']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Database MCP server: {e}")
            return False
    
    async def start_kafka_server(self) -> bool:
        """Start the Kafka MCP server"""
        if not self.config["kafka"]["enabled"]:
            logger.info("Kafka MCP server disabled")
            return True
        
        try:
            logger.info("Starting Kafka MCP server...")
            
            kafka_config = ExternalKafkaMCPConfig(
                bootstrap_servers=self.config["kafka"]["bootstrap_servers"],
                topic_name=self.config["kafka"].get("topic_name", "default-topic"),
                group_id=self.config["kafka"].get("group_id", "mcp-group")
            )
            server = KafkaMCPWrapper(kafka_config)
            await server.start()
            
            self.servers["kafka"] = server
            logger.info(f"Kafka MCP server started on port {self.config['kafka']['port']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Kafka MCP server: {e}")
            return False
    
    async def start_aws_server(self) -> bool:
        """Start the AWS MCP server"""
        if not self.config["aws"]["enabled"]:
            logger.info("AWS MCP server disabled")
            return True
        
        try:
            logger.info("Starting AWS MCP server...")
            
            aws_config = ExternalMCPConfig(
                aws_profile=self.config["aws"].get("profile", "default"),
                aws_region=self.config["aws"]["region"]
            )
            server = AWSMCPWrapper(aws_config)
            await server.initialize()
            
            self.servers["aws"] = server
            logger.info(f"AWS MCP wrapper started on port {self.config['aws']['port']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start AWS MCP server: {e}")
            return False
    
    async def start_all_servers(self) -> bool:
        """Start all enabled MCP servers"""
        logger.info("Starting all MCP servers...")
        
        success_count = 0
        total_servers = 0
        
        # Start database server
        if self.config["database"]["enabled"]:
            total_servers += 1
            if await self.start_database_server():
                success_count += 1
        
        # Start Kafka server
        if self.config["kafka"]["enabled"]:
            total_servers += 1
            if await self.start_kafka_server():
                success_count += 1
        
        # Start AWS server
        if self.config["aws"]["enabled"]:
            total_servers += 1
            if await self.start_aws_server():
                success_count += 1
        
        if success_count == total_servers:
            logger.info(f"All {total_servers} MCP servers started successfully")
            self.running = True
            return True
        else:
            logger.error(f"Only {success_count}/{total_servers} MCP servers started successfully")
            return False
    
    async def stop_all_servers(self):
        """Stop all running MCP servers"""
        logger.info("Stopping all MCP servers...")
        
        for server_name, server in self.servers.items():
            try:
                if hasattr(server, 'stop'):
                    await server.stop()
                server.running = False
                logger.info(f"{server_name} MCP server stopped")
            except Exception as e:
                logger.error(f"Error stopping {server_name} MCP server: {e}")
        
        self.servers.clear()
        self.running = False
        logger.info("All MCP servers stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def run_forever(self):
        """Run servers until shutdown signal"""
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            await self.stop_all_servers()
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all servers"""
        status = {
            "running": self.running,
            "servers": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for server_name, server in self.servers.items():
            status["servers"][server_name] = {
                "running": getattr(server, 'running', False),
                "server_id": getattr(server, 'server_id', 'unknown'),
                "name": getattr(server, 'name', 'unknown')
            }
        
        return status


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server Manager")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--server", choices=["database", "kafka", "aws"], 
                       help="Start only specific server")
    parser.add_argument("--status", action="store_true", 
                       help="Show server status and exit")
    
    args = parser.parse_args()
    
    # Create server manager
    manager = MCPServerManager(args.config)
    
    if args.status:
        status = manager.get_server_status()
        print(f"MCP Server Status: {status}")
        return
    
    try:
        if args.server:
            # Start specific server
            if args.server == "database":
                success = await manager.start_database_server()
            elif args.server == "kafka":
                success = await manager.start_kafka_server()
            elif args.server == "aws":
                success = await manager.start_aws_server()
            
            if success:
                logger.info(f"{args.server} MCP server started, running forever...")
                manager.running = True
                await manager.run_forever()
            else:
                logger.error(f"Failed to start {args.server} MCP server")
                sys.exit(1)
        else:
            # Start all servers
            success = await manager.start_all_servers()
            if success:
                logger.info("All MCP servers started, running forever...")
                await manager.run_forever()
            else:
                logger.error("Failed to start all MCP servers")
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the server manager
    asyncio.run(main())
