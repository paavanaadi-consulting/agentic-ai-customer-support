#!/usr/bin/env python3
"""
Enhanced health check script for all services
"""

import asyncio
import aiohttp
import psycopg2
import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import CONFIG
from src.utils.logger import setup_logger

logger = setup_logger("HealthCheck")

class HealthChecker:
    """Comprehensive health checker for all services"""
    
    def __init__(self):
        self.results = {}
        self.verbose = False
        
    async def check_database(self) -> Tuple[bool, str]:
        """Check PostgreSQL database connectivity"""
        try:
            conn = psycopg2.connect(
                host=CONFIG['database']['host'],
                port=CONFIG['database']['port'],
                database=CONFIG['database']['name'],
                user=CONFIG['database']['user'],
                password=CONFIG['database']['password']
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return True, f"PostgreSQL connected, version: {version[:50]}"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"
    
    async def check_http_service(self, name: str, url: str, timeout: int = 5) -> Tuple[bool, str]:
        """Check HTTP service health"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()
                        return True, f"{name} responding (status: {response.status})"
                    else:
                        return False, f"{name} returned status: {response.status}"
        except asyncio.TimeoutError:
            return False, f"{name} timeout after {timeout}s"
        except Exception as e:
            return False, f"{name} error: {str(e)}"
    
    async def check_kafka(self) -> Tuple[bool, str]:
        """Check Kafka connectivity"""
        try:
            from kafka import KafkaProducer, KafkaConsumer
            from kafka.errors import NoBrokersAvailable
            
            # Test producer
            producer = KafkaProducer(
                bootstrap_servers=CONFIG['kafka']['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=5000
            )
            
            # Send test message
            future = producer.send('health-check', {'test': 'message', 'timestamp': time.time()})
            producer.flush(timeout=5)
            producer.close()
            
            return True, "Kafka producer/consumer working"
            
        except NoBrokersAvailable:
            return False, "Kafka brokers not available"
        except Exception as e:
            return False, f"Kafka error: {str(e)}"
    
    async def check_qdrant(self) -> Tuple[bool, str]:
        """Check Qdrant vector database"""
        try:
            from qdrant_client import QdrantClient
            
            client = QdrantClient(
                url=CONFIG['vector_db']['url'],
                timeout=5
            )
            
            # Test connection
            collections = client.get_collections()
            count = len(collections.collections) if collections else 0
            
            return True, f"Qdrant connected, {count} collections"
            
        except Exception as e:
            return False, f"Qdrant error: {str(e)}"
    
    async def check_mcp_servers(self) -> Dict[str, Tuple[bool, str]]:
        """Check all MCP servers"""
        mcp_services = {
            "PostgreSQL MCP": "http://localhost:8001/health",
            "Kafka MCP": "http://localhost:8002/health",
            "AWS Lambda MCP": "http://localhost:8766/health",
            "AWS Messaging MCP": "http://localhost:8767/health",
            "AWS MQ MCP": "http://localhost:8768/health"
        }
        
        results = {}
        for name, url in mcp_services.items():
            try:
                results[name] = await self.check_http_service(name, url, timeout=3)
            except Exception as e:
                results[name] = (False, f"Check failed: {str(e)}")
        
        return results
    
    async def check_api_endpoints(self) -> Dict[str, Tuple[bool, str]]:
        """Check main API endpoints"""
        base_url = "http://localhost:8000"
        endpoints = {
            "Health": f"{base_url}/health",
            "API Info": f"{base_url}/api/v1/info",
            "Documentation": f"{base_url}/docs",
            "Metrics": f"{base_url}/metrics"
        }
        
        results = {}
        for name, url in endpoints.items():
            try:
                results[name] = await self.check_http_service(name, url)
            except Exception as e:
                results[name] = (False, f"Check failed: {str(e)}")
        
        return results
    
    async def run_comprehensive_check(self, verbose: bool = False) -> Dict[str, any]:
        """Run all health checks"""
        self.verbose = verbose
        
        print("🏥 Running comprehensive health checks...")
        print("=" * 60)
        
        # Core infrastructure
        print("\n📊 Core Infrastructure:")
        
        # Database
        db_ok, db_msg = await self.check_database()
        self._print_result("PostgreSQL Database", db_ok, db_msg)
        
        # Kafka
        kafka_ok, kafka_msg = await self.check_kafka()
        self._print_result("Apache Kafka", kafka_ok, kafka_msg)
        
        # Qdrant
        qdrant_ok, qdrant_msg = await self.check_qdrant()
        self._print_result("Qdrant Vector DB", qdrant_ok, qdrant_msg)
        
        # MCP Servers
        print("\n🔌 MCP Servers:")
        mcp_results = await self.check_mcp_servers()
        for name, (ok, msg) in mcp_results.items():
            self._print_result(name, ok, msg)
        
        # API Services
        print("\n🌐 API Services:")
        api_results = await self.check_api_endpoints()
        for name, (ok, msg) in api_results.items():
            self._print_result(name, ok, msg)
        
        # Summary
        print("\n" + "=" * 60)
        
        total_checks = 3 + len(mcp_results) + len(api_results)
        passed_checks = (
            sum([db_ok, kafka_ok, qdrant_ok]) +
            sum([ok for ok, _ in mcp_results.values()]) +
            sum([ok for ok, _ in api_results.values()])
        )
        
        print(f"📋 Summary: {passed_checks}/{total_checks} checks passed")
        
        if passed_checks == total_checks:
            print("✅ All systems operational!")
            return {"status": "healthy", "passed": passed_checks, "total": total_checks}
        else:
            print("⚠️  Some systems need attention")
            return {"status": "degraded", "passed": passed_checks, "total": total_checks}
    
    def _print_result(self, service: str, ok: bool, message: str):
        """Print formatted result"""
        status = "✅" if ok else "❌"
        print(f"  {status} {service:<20} - {message}")
        
        if self.verbose and not ok:
            print(f"    💡 Troubleshooting: Check service logs and configuration")

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Health check for Agentic AI Customer Support')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--service', choices=['database', 'kafka', 'qdrant', 'mcp', 'api'], 
                       help='Check specific service only')
    parser.add_argument('--format', choices=['text', 'json'], default='text', 
                       help='Output format')
    
    args = parser.parse_args()
    
    checker = HealthChecker()
    
    if args.service:
        # Check specific service
        if args.service == 'database':
            ok, msg = await checker.check_database()
        elif args.service == 'kafka':
            ok, msg = await checker.check_kafka()
        elif args.service == 'qdrant':
            ok, msg = await checker.check_qdrant()
        elif args.service == 'mcp':
            results = await checker.check_mcp_servers()
            if args.format == 'json':
                print(json.dumps(results, indent=2))
            else:
                for name, (ok, msg) in results.items():
                    checker._print_result(name, ok, msg)
            return
        elif args.service == 'api':
            results = await checker.check_api_endpoints()
            if args.format == 'json':
                print(json.dumps(results, indent=2))
            else:
                for name, (ok, msg) in results.items():
                    checker._print_result(name, ok, msg)
            return
        
        if args.format == 'json':
            print(json.dumps({"service": args.service, "healthy": ok, "message": msg}))
        else:
            checker._print_result(args.service.title(), ok, msg)
    else:
        # Run comprehensive check
        result = await checker.run_comprehensive_check(verbose=args.verbose)
        
        if args.format == 'json':
            print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result["status"] == "healthy" else 1)

if __name__ == "__main__":
    asyncio.run(main())
