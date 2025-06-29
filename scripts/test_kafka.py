#!/usr/bin/env python3
"""
Kafka Testing Script - Comprehensive testing for local Kafka setup
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("⚠️  kafka-python not installed. Install with: pip install kafka-python")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/kafka_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class KafkaTestSuite:
    """Comprehensive Kafka testing suite"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumer = None
        self.test_results = {}
        
    def setup_producer(self) -> bool:
        """Set up Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                batch_size=16384,
                linger_ms=10,
                buffer_memory=33554432
            )
            logger.info("✅ Kafka producer setup successful")
            return True
        except Exception as e:
            logger.error(f"❌ Kafka producer setup failed: {e}")
            return False
    
    def setup_consumer(self, topics: List[str], group_id: str = "test-group") -> bool:
        """Set up Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                consumer_timeout_ms=5000
            )
            logger.info(f"✅ Kafka consumer setup successful for topics: {topics}")
            return True
        except Exception as e:
            logger.error(f"❌ Kafka consumer setup failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test basic Kafka connection"""
        logger.info("🔌 Testing Kafka connection...")
        
        try:
            from kafka.admin import KafkaAdminClient
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='test_client'
            )
            
            # Get cluster metadata
            metadata = admin_client.describe_cluster()
            logger.info(f"✅ Connected to Kafka cluster: {metadata}")
            
            admin_client.close()
            self.test_results['connection'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            self.test_results['connection'] = False
            return False
    
    def test_topic_operations(self) -> bool:
        """Test topic creation and management"""
        logger.info("📋 Testing topic operations...")
        
        try:
            from kafka.admin import KafkaAdminClient, NewTopic
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='test_admin'
            )
            
            # Create test topic
            test_topic = f"test-topic-{int(time.time())}"
            topic_config = NewTopic(
                name=test_topic,
                num_partitions=3,
                replication_factor=1
            )
            
            # Create topic
            admin_client.create_topics([topic_config])
            logger.info(f"✅ Created test topic: {test_topic}")
            
            # List topics
            topics = admin_client.list_topics()
            if test_topic in topics:
                logger.info(f"✅ Topic verification successful: {test_topic}")
            else:
                logger.error(f"❌ Topic not found after creation: {test_topic}")
                return False
            
            # Delete test topic
            admin_client.delete_topics([test_topic])
            logger.info(f"✅ Deleted test topic: {test_topic}")
            
            admin_client.close()
            self.test_results['topic_operations'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Topic operations test failed: {e}")
            self.test_results['topic_operations'] = False
            return False
    
    def test_producer_consumer(self) -> bool:
        """Test message production and consumption"""
        logger.info("📤📥 Testing producer-consumer functionality...")
        
        try:
            test_topic = f"test-messages-{int(time.time())}"
            
            # Create test topic first
            from kafka.admin import KafkaAdminClient, NewTopic
            admin_client = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            topic_config = NewTopic(name=test_topic, num_partitions=1, replication_factor=1)
            admin_client.create_topics([topic_config])
            time.sleep(2)  # Wait for topic to be created
            
            # Setup producer
            if not self.setup_producer():
                return False
            
            # Setup consumer
            if not self.setup_consumer([test_topic], "test-producer-consumer"):
                return False
            
            # Test messages
            test_messages = [
                {"id": 1, "message": "Hello Kafka!", "timestamp": datetime.now().isoformat()},
                {"id": 2, "message": "Test message 2", "timestamp": datetime.now().isoformat()},
                {"id": 3, "message": "Final test message", "timestamp": datetime.now().isoformat()}
            ]
            
            # Send messages
            sent_count = 0
            for msg in test_messages:
                try:
                    future = self.producer.send(test_topic, value=msg, key=str(msg["id"]))
                    future.get(timeout=10)  # Wait for confirmation
                    sent_count += 1
                    logger.info(f"✅ Sent message {msg['id']}: {msg['message']}")
                except Exception as e:
                    logger.error(f"❌ Failed to send message {msg['id']}: {e}")
            
            # Flush producer
            self.producer.flush()
            
            # Consume messages
            received_messages = []
            start_time = time.time()
            
            for message in self.consumer:
                received_messages.append(message.value)
                logger.info(f"✅ Received message: {message.value}")
                
                if len(received_messages) >= len(test_messages):
                    break
                    
                if time.time() - start_time > 30:  # 30 second timeout
                    logger.error("❌ Timeout waiting for messages")
                    break
            
            # Verify results
            if len(received_messages) == len(test_messages):
                logger.info(f"✅ All messages received successfully ({len(received_messages)}/{len(test_messages)})")
                self.test_results['producer_consumer'] = True
                success = True
            else:
                logger.error(f"❌ Message count mismatch: sent {len(test_messages)}, received {len(received_messages)}")
                self.test_results['producer_consumer'] = False
                success = False
            
            # Cleanup
            self.producer.close()
            self.consumer.close()
            admin_client.delete_topics([test_topic])
            admin_client.close()
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Producer-consumer test failed: {e}")
            self.test_results['producer_consumer'] = False
            return False
    
    def test_performance(self, num_messages: int = 1000) -> bool:
        """Test Kafka performance"""
        logger.info(f"⚡ Testing Kafka performance with {num_messages} messages...")
        
        try:
            test_topic = f"perf-test-{int(time.time())}"
            
            # Create test topic
            from kafka.admin import KafkaAdminClient, NewTopic
            admin_client = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            topic_config = NewTopic(name=test_topic, num_partitions=3, replication_factor=1)
            admin_client.create_topics([topic_config])
            time.sleep(2)
            
            # Setup producer
            if not self.setup_producer():
                return False
            
            # Performance test - sending messages
            start_time = time.time()
            sent_count = 0
            
            for i in range(num_messages):
                message = {
                    "id": i,
                    "data": f"Performance test message {i}",
                    "timestamp": datetime.now().isoformat()
                }
                
                try:
                    self.producer.send(test_topic, value=message, key=str(i))
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send message {i}: {e}")
            
            # Flush all messages
            self.producer.flush()
            send_time = time.time() - start_time
            
            # Calculate throughput
            messages_per_second = sent_count / send_time if send_time > 0 else 0
            
            logger.info(f"✅ Performance test completed:")
            logger.info(f"   Messages sent: {sent_count}/{num_messages}")
            logger.info(f"   Time taken: {send_time:.2f} seconds")
            logger.info(f"   Throughput: {messages_per_second:.2f} messages/second")
            
            # Cleanup
            self.producer.close()
            admin_client.delete_topics([test_topic])
            admin_client.close()
            
            self.test_results['performance'] = {
                'messages_sent': sent_count,
                'time_taken': send_time,
                'throughput': messages_per_second
            }
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            self.test_results['performance'] = False
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling scenarios"""
        logger.info("🚨 Testing error handling...")
        
        try:
            # Test with invalid topic name
            invalid_producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            # Try to send to non-existent topic (should auto-create)
            invalid_topic = "non-existent-topic-test"
            message = {"test": "error handling"}
            
            try:
                future = invalid_producer.send(invalid_topic, value=message)
                future.get(timeout=10)
                logger.info("✅ Auto-topic creation works")
            except Exception as e:
                logger.info(f"✅ Expected error handled: {e}")
            
            invalid_producer.close()
            
            # Test connection to wrong port
            try:
                wrong_producer = KafkaProducer(
                    bootstrap_servers="localhost:9999",  # Wrong port
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    request_timeout_ms=5000
                )
                wrong_producer.send("test", value={"test": "should fail"})
                wrong_producer.flush()
                logger.error("❌ Expected connection error did not occur")
                return False
            except Exception as e:
                logger.info(f"✅ Connection error handled correctly: {type(e).__name__}")
                
            self.test_results['error_handling'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.test_results['error_handling'] = False
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Kafka tests"""
        logger.info("🚀 Starting comprehensive Kafka test suite...")
        
        tests = [
            ("Connection Test", self.test_connection),
            ("Topic Operations", self.test_topic_operations),
            ("Producer-Consumer", self.test_producer_consumer),
            ("Performance Test", lambda: self.test_performance(100)),  # Reduced for speed
            ("Error Handling", self.test_error_handling)
        ]
        
        results = {}
        passed = 0
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Running {test_name} ---")
            try:
                success = test_func()
                results[test_name] = success
                if success:
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
                results[test_name] = False
        
        # Summary
        total_tests = len(tests)
        logger.info(f"\n🎯 Test Summary:")
        logger.info(f"   Total tests: {total_tests}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {total_tests - passed}")
        logger.info(f"   Success rate: {(passed/total_tests)*100:.1f}%")
        
        return {
            'summary': {
                'total': total_tests,
                'passed': passed,
                'failed': total_tests - passed,
                'success_rate': (passed/total_tests)*100
            },
            'detailed_results': results,
            'test_results': self.test_results
        }

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kafka Testing Suite")
    parser.add_argument("--bootstrap-servers", default="localhost:9092", 
                       help="Kafka bootstrap servers")
    parser.add_argument("--test", choices=["connection", "topics", "producer", "performance", "errors", "all"],
                       default="all", help="Test to run")
    parser.add_argument("--messages", type=int, default=1000,
                       help="Number of messages for performance test")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if kafka-python is available
    if not KAFKA_AVAILABLE:
        print("❌ kafka-python is required for testing")
        print("Install with: pip install kafka-python")
        return 1
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Initialize test suite
    test_suite = KafkaTestSuite(args.bootstrap_servers)
    
    logger.info("🧪 Kafka Testing Suite")
    logger.info("=" * 50)
    logger.info(f"Bootstrap servers: {args.bootstrap_servers}")
    logger.info(f"Test selection: {args.test}")
    
    # Run selected tests
    if args.test == "all":
        results = test_suite.run_all_tests()
    else:
        # Run individual test
        test_map = {
            "connection": test_suite.test_connection,
            "topics": test_suite.test_topic_operations,
            "producer": test_suite.test_producer_consumer,
            "performance": lambda: test_suite.test_performance(args.messages),
            "errors": test_suite.test_error_handling
        }
        
        if args.test in test_map:
            success = test_map[args.test]()
            results = {"individual_test": {args.test: success}}
        else:
            logger.error(f"Unknown test: {args.test}")
            return 1
    
    # Save results to file
    results_file = f"logs/kafka_test_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📊 Test results saved to: {results_file}")
    
    # Return appropriate exit code
    if isinstance(results, dict) and 'summary' in results:
        return 0 if results['summary']['failed'] == 0 else 1
    else:
        return 0

if __name__ == "__main__":
    exit(main())
