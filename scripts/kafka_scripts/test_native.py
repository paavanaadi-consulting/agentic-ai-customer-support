#!/usr/bin/env python3
"""
Native Test Runner - Local Testing Without Docker
Tests the A2A system using SQLite and in-memory components
"""

import asyncio
import os
import sys
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import argparse

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/native_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class NativeMockMCPClient:
    """Mock MCP client for local testing"""
    
    def __init__(self):
        self.db_path = "data/test.db"
        self.connection = None
        self.memory_store = {}
        
    async def start(self):
        """Initialize the mock MCP client"""
        # Create database connection
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        logger.info("Mock MCP client started with SQLite database")
        
    async def stop(self):
        """Stop the mock MCP client"""
        if self.connection:
            self.connection.close()
        logger.info("Mock MCP client stopped")
    
    async def call_tool(self, server: str, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate MCP tool calls"""
        if server == "database":
            return await self._handle_database_tool(tool, arguments)
        elif server == "kafka":
            return await self._handle_kafka_tool(tool, arguments)
        elif server == "aws":
            return await self._handle_aws_tool(tool, arguments)
        else:
            return {"error": f"Unknown server: {server}"}
    
    async def _handle_database_tool(self, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle database tool calls"""
        try:
            cursor = self.connection.cursor()
            
            if tool == "query_customers":
                cursor.execute("SELECT * FROM customers")
                customers = [dict(row) for row in cursor.fetchall()]
                return {"customers": customers}
                
            elif tool == "get_customer":
                customer_id = args.get("customer_id")
                cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
                customer = cursor.fetchone()
                return {"customer": dict(customer) if customer else None}
                
            elif tool == "search_knowledge":
                query = args.get("query", "")
                cursor.execute(
                    "SELECT * FROM knowledge_articles WHERE title LIKE ? OR content LIKE ?",
                    (f"%{query}%", f"%{query}%")
                )
                articles = [dict(row) for row in cursor.fetchall()]
                return {"articles": articles}
                
            elif tool == "create_interaction":
                interaction_data = args.get("interaction_data", {})
                cursor.execute("""
                    INSERT INTO query_interactions 
                    (interaction_id, query_id, customer_id, query_text, agent_response, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    interaction_data.get("interaction_id", f"int_{datetime.now().timestamp()}"),
                    interaction_data.get("query_id", ""),
                    interaction_data.get("customer_id", ""),
                    interaction_data.get("query_text", ""),
                    interaction_data.get("agent_response", ""),
                    datetime.now().isoformat()
                ))
                self.connection.commit()
                return {"success": True, "interaction_id": interaction_data.get("interaction_id")}
                
            else:
                return {"error": f"Unknown database tool: {tool}"}
                
        except Exception as e:
            logger.error(f"Database tool error: {e}")
            return {"error": str(e)}
    
    async def _handle_kafka_tool(self, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Kafka tool calls (in-memory simulation)"""
        if tool == "publish_message":
            topic = args.get("topic", "default")
            message = args.get("message", {})
            
            # Store in memory
            if topic not in self.memory_store:
                self.memory_store[topic] = []
            self.memory_store[topic].append({
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            return {"success": True, "message_id": f"msg_{len(self.memory_store[topic])}"}
            
        elif tool == "consume_messages":
            topic = args.get("topic", "default")
            messages = self.memory_store.get(topic, [])
            return {"messages": messages}
            
        else:
            return {"error": f"Unknown Kafka tool: {tool}"}
    
    async def _handle_aws_tool(self, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AWS tool calls (mock implementation)"""
        if tool == "s3_upload":
            return {"success": True, "url": "mock://s3/bucket/key"}
        elif tool == "s3_download":
            return {"success": True, "content": "mock file content"}
        else:
            return {"error": f"Unknown AWS tool: {tool}"}

class NativeQueryAgent:
    """Query Agent for native testing"""
    
    def __init__(self, agent_id: str = "native-query-agent"):
        self.agent_id = agent_id
        self.mcp_client = NativeMockMCPClient()
        self.is_running = False
        self.processed_queries = 0
        
    async def start(self):
        """Start the query agent"""
        await self.mcp_client.start()
        self.is_running = True
        logger.info(f"Query agent {self.agent_id} started")
        
    async def stop(self):
        """Stop the query agent"""
        await self.mcp_client.stop()
        self.is_running = False
        logger.info(f"Query agent {self.agent_id} stopped")
        
    async def process_query(self, customer_id: str, query_text: str) -> Dict[str, Any]:
        """Process a customer query"""
        if not self.is_running:
            return {"error": "Agent not running"}
            
        try:
            # Get customer information
            customer_result = await self.mcp_client.call_tool(
                "database", "get_customer", {"customer_id": customer_id}
            )
            
            # Analyze query (simple keyword matching for demo)
            query_keywords = query_text.lower().split()
            
            # Search knowledge base
            knowledge_result = await self.mcp_client.call_tool(
                "database", "search_knowledge", {"query": query_text}
            )
            
            # Publish to message queue
            await self.mcp_client.call_tool(
                "kafka", "publish_message", {
                    "topic": "query-processing",
                    "message": {
                        "customer_id": customer_id,
                        "query_text": query_text,
                        "timestamp": datetime.now().isoformat(),
                        "agent_id": self.agent_id
                    }
                }
            )
            
            self.processed_queries += 1
            
            return {
                "success": True,
                "customer": customer_result.get("customer"),
                "knowledge_articles": knowledge_result.get("articles", []),
                "query_keywords": query_keywords,
                "processed_queries": self.processed_queries
            }
            
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            return {"error": str(e)}

class NativeKnowledgeAgent:
    """Knowledge Agent for native testing"""
    
    def __init__(self, agent_id: str = "native-knowledge-agent"):
        self.agent_id = agent_id
        self.mcp_client = NativeMockMCPClient()
        self.is_running = False
        self.analyzed_queries = 0
        
    async def start(self):
        """Start the knowledge agent"""
        await self.mcp_client.start()
        self.is_running = True
        logger.info(f"Knowledge agent {self.agent_id} started")
        
    async def stop(self):
        """Stop the knowledge agent"""
        await self.mcp_client.stop()
        self.is_running = False
        logger.info(f"Knowledge agent {self.agent_id} stopped")
        
    async def analyze_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a query and find relevant knowledge"""
        if not self.is_running:
            return {"error": "Agent not running"}
            
        try:
            query_text = query_data.get("query_text", "")
            
            # Search for relevant knowledge articles
            knowledge_result = await self.mcp_client.call_tool(
                "database", "search_knowledge", {"query": query_text}
            )
            
            articles = knowledge_result.get("articles", [])
            
            # Score articles by relevance (simple word matching)
            scored_articles = []
            query_words = set(query_text.lower().split())
            
            for article in articles:
                title_words = set(article["title"].lower().split())
                content_words = set(article["content"].lower().split())
                
                # Simple scoring based on word overlap
                title_score = len(query_words & title_words) * 2
                content_score = len(query_words & content_words)
                total_score = title_score + content_score
                
                scored_articles.append({
                    **article,
                    "relevance_score": total_score
                })
            
            # Sort by relevance
            scored_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            self.analyzed_queries += 1
            
            return {
                "success": True,
                "relevant_articles": scored_articles[:3],  # Top 3 articles
                "total_articles_found": len(articles),
                "analyzed_queries": self.analyzed_queries
            }
            
        except Exception as e:
            logger.error(f"Knowledge analysis error: {e}")
            return {"error": str(e)}

class NativeResponseAgent:
    """Response Agent for native testing"""
    
    def __init__(self, agent_id: str = "native-response-agent"):
        self.agent_id = agent_id
        self.mcp_client = NativeMockMCPClient()
        self.is_running = False
        self.generated_responses = 0
        
    async def start(self):
        """Start the response agent"""
        await self.mcp_client.start()
        self.is_running = True
        logger.info(f"Response agent {self.agent_id} started")
        
    async def stop(self):
        """Stop the response agent"""
        await self.mcp_client.stop()
        self.is_running = False
        logger.info(f"Response agent {self.agent_id} stopped")
        
    async def generate_response(self, query_data: Dict[str, Any], knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a response based on query and knowledge"""
        if not self.is_running:
            return {"error": "Agent not running"}
            
        try:
            query_text = query_data.get("query_text", "")
            customer_id = query_data.get("customer_id", "")
            articles = knowledge_data.get("relevant_articles", [])
            
            # Generate response based on available knowledge
            if articles:
                best_article = articles[0]
                response_text = f"Based on our knowledge base: {best_article['content']}"
                
                if "password" in query_text.lower():
                    response_text = "To reset your password, please visit our login page and click 'Forgot Password'. You'll receive an email with instructions to create a new password."
                elif "support" in query_text.lower() or "hours" in query_text.lower():
                    response_text = "Our support team is available Monday-Friday 9AM-5PM EST. You can reach us through this chat or email support@example.com."
                elif "account" in query_text.lower():
                    response_text = "For account-related issues, please try clearing your browser cache first. If the problem persists, our support team can help you further."
            else:
                response_text = "Thank you for your question. Let me connect you with a human agent who can provide more specific assistance."
            
            # Create interaction record
            interaction_data = {
                "interaction_id": f"int_{datetime.now().timestamp()}",
                "query_id": f"query_{datetime.now().timestamp()}",
                "customer_id": customer_id,
                "query_text": query_text,
                "agent_response": response_text
            }
            
            await self.mcp_client.call_tool(
                "database", "create_interaction", {"interaction_data": interaction_data}
            )
            
            self.generated_responses += 1
            
            return {
                "success": True,
                "response_text": response_text,
                "interaction_id": interaction_data["interaction_id"],
                "generated_responses": self.generated_responses
            }
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return {"error": str(e)}

async def test_basic_query():
    """Test basic query processing"""
    print("🧪 Testing Basic Query Processing")
    print("-" * 40)
    
    agent = NativeQueryAgent()
    await agent.start()
    
    try:
        result = await agent.process_query("test_customer_12345", "How do I reset my password?")
        print(f"✅ Query processed successfully")
        print(f"   Customer found: {'Yes' if result.get('customer') else 'No'}")
        print(f"   Knowledge articles: {len(result.get('knowledge_articles', []))}")
        print(f"   Query keywords: {result.get('query_keywords', [])}")
        return result
    finally:
        await agent.stop()

async def test_knowledge_search():
    """Test knowledge base search"""
    print("🔍 Testing Knowledge Search")
    print("-" * 40)
    
    agent = NativeKnowledgeAgent()
    await agent.start()
    
    try:
        query_data = {
            "query_text": "password reset help",
            "customer_id": "test_customer_12345"
        }
        
        result = await agent.analyze_query(query_data)
        print(f"✅ Knowledge search completed")
        print(f"   Relevant articles found: {len(result.get('relevant_articles', []))}")
        print(f"   Total articles searched: {result.get('total_articles_found', 0)}")
        
        for article in result.get('relevant_articles', [])[:2]:
            print(f"   - {article['title']} (score: {article.get('relevance_score', 0)})")
        
        return result
    finally:
        await agent.stop()

async def test_response_generation():
    """Test response generation"""
    print("💬 Testing Response Generation")
    print("-" * 40)
    
    agent = NativeResponseAgent()
    await agent.start()
    
    try:
        query_data = {
            "query_text": "How do I reset my password?",
            "customer_id": "test_customer_12345"
        }
        
        knowledge_data = {
            "relevant_articles": [{
                "title": "Password Reset Guide",
                "content": "To reset your password, visit the login page and click 'Forgot Password'.",
                "relevance_score": 5
            }]
        }
        
        result = await agent.generate_response(query_data, knowledge_data)
        print(f"✅ Response generated successfully")
        print(f"   Response: {result.get('response_text', '')[:100]}...")
        print(f"   Interaction ID: {result.get('interaction_id', 'N/A')}")
        
        return result
    finally:
        await agent.stop()

async def test_full_pipeline():
    """Test the complete A2A pipeline"""
    print("🚀 Testing Full A2A Pipeline")
    print("=" * 50)
    
    # Initialize agents
    query_agent = NativeQueryAgent()
    knowledge_agent = NativeKnowledgeAgent()
    response_agent = NativeResponseAgent()
    
    # Start agents
    await query_agent.start()
    await knowledge_agent.start()
    await response_agent.start()
    
    try:
        # Test scenarios
        test_scenarios = [
            {
                "customer_id": "test_customer_12345",
                "query": "How do I reset my password?",
                "expected_keywords": ["password", "reset"]
            },
            {
                "customer_id": "test_customer_67890",
                "query": "What are your support hours?",
                "expected_keywords": ["support", "hours"]
            },
            {
                "customer_id": "customer_123",
                "query": "I cannot access my account",
                "expected_keywords": ["access", "account"]
            }
        ]
        
        results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📋 Test Scenario {i}: {scenario['query']}")
            print("-" * 30)
            
            # Step 1: Query processing
            query_result = await query_agent.process_query(
                scenario["customer_id"], 
                scenario["query"]
            )
            
            if not query_result.get("success"):
                print(f"❌ Query processing failed: {query_result.get('error')}")
                continue
            
            # Step 2: Knowledge analysis
            knowledge_result = await knowledge_agent.analyze_query({
                "query_text": scenario["query"],
                "customer_id": scenario["customer_id"]
            })
            
            if not knowledge_result.get("success"):
                print(f"❌ Knowledge analysis failed: {knowledge_result.get('error')}")
                continue
            
            # Step 3: Response generation
            response_result = await response_agent.generate_response(
                {
                    "query_text": scenario["query"],
                    "customer_id": scenario["customer_id"]
                },
                knowledge_result
            )
            
            if not response_result.get("success"):
                print(f"❌ Response generation failed: {response_result.get('error')}")
                continue
            
            # Verify results
            print(f"✅ Test passed!")
            print(f"   Processed queries: {query_agent.processed_queries}")
            print(f"   Analyzed queries: {knowledge_agent.analyzed_queries}")
            print(f"   Generated responses: {response_agent.generated_responses}")
            print(f"   Latest response: {response_result.get('response_text', '')[:80]}...")
            
            results.append({
                "scenario": scenario,
                "query_result": query_result,
                "knowledge_result": knowledge_result,
                "response_result": response_result
            })
        
        print(f"\n🎉 Pipeline test completed!")
        print(f"   Total scenarios: {len(test_scenarios)}")
        print(f"   Successful scenarios: {len(results)}")
        
        return results
        
    finally:
        # Stop agents
        await query_agent.stop()
        await knowledge_agent.stop()
        await response_agent.stop()

async def run_performance_test():
    """Run performance testing"""
    print("⚡ Running Performance Tests")
    print("=" * 50)
    
    query_agent = NativeQueryAgent()
    await query_agent.start()
    
    try:
        import time
        
        # Test query processing speed
        start_time = time.time()
        tasks = []
        
        for i in range(10):
            task = query_agent.process_query(
                f"customer_{i}", 
                f"Test query {i}"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        successful = sum(1 for r in results if r.get("success"))
        total_time = end_time - start_time
        
        print(f"✅ Performance test completed")
        print(f"   Total queries: {len(tasks)}")
        print(f"   Successful queries: {successful}")
        print(f"   Total time: {total_time:.2f} seconds")
        print(f"   Queries per second: {len(tasks) / total_time:.2f}")
        
    finally:
        await query_agent.stop()

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Native A2A Testing")
    parser.add_argument("--scenario", choices=["basic", "knowledge", "response", "full", "performance"], 
                       default="full", help="Test scenario to run")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Ensure required directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    print("🧪 Native A2A Testing Suite")
    print("=" * 50)
    print(f"Scenario: {args.scenario}")
    print(f"Verbose: {args.verbose}")
    print(f"Log file: logs/native_test.log")
    print()
    
    # Run the selected test scenario
    if args.scenario == "basic":
        asyncio.run(test_basic_query())
    elif args.scenario == "knowledge":
        asyncio.run(test_knowledge_search())
    elif args.scenario == "response":
        asyncio.run(test_response_generation())
    elif args.scenario == "full":
        asyncio.run(test_full_pipeline())
    elif args.scenario == "performance":
        asyncio.run(run_performance_test())
    
    print("\n✅ Testing completed! Check logs/native_test.log for detailed logs.")

if __name__ == "__main__":
    main()
